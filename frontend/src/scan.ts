/** Inspect loose clouds and completed RGB-D reconstruction runs in the installed CAD renderer. */
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { MTLLoader } from 'three/addons/loaders/MTLLoader.js';
import {
  Box3, LoadingManager, Matrix4, Mesh, MeshBasicMaterial, MeshStandardMaterial, PointLight, Points, PointsMaterial, Vector3,
  type AmbientLight, type DirectionalLight, type Material, type Object3D, type Texture, type MeshPhongMaterial, type Camera,
} from 'three';
import * as library from './renderer';
import { createViewerCamera, type CameraViewer, type CameraState } from './viewer-camera';
import { onTab } from './tabs';
import { assetUrl } from './site-runtime';
import { createScanTags } from './scan-tags';
import { createScanWorkflowPanel } from './scan-workflow-panel';
import { readScanResults, type ScanResult as Scan, type ScanLayer as Layer } from './scan-library-api';
import { createScanLibrary } from './scan-library';

interface ScanViewer extends CameraViewer {
  rendered: CameraViewer['rendered'] & {
    nestedGroup: { groups: Record<string, Object3D> };
    scene: Object3D;
    ambientLight: AmbientLight;
    directLight: DirectionalLight;
    orientationMarker: { setVisible(visible: boolean): void };
  };
  update(marker: boolean, notify: boolean): void;
}

function disposeObject(root: Object3D) {
  root.traverse(object => {
    if (!(object instanceof Mesh || object instanceof Points)) return;
    object.geometry.dispose();
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      for (const value of Object.values(material)) if ((value as Texture)?.isTexture) (value as Texture).dispose();
      material.dispose();
    }
  });
}

function availableLayers(scan: Scan): Layer[] {
  const available = scan.layers?.length ? scan.layers
    : [{ id: 'cloud', label: 'Cloud', asset: scan.name, kind: 'cloud' as const }];
  const surfaces = available.filter(layer => layer.kind === 'mesh');
  return [...available, ...surfaces.map(surface => ({ ...surface,
    id: surface.id === 'mesh-full' ? 'shaded-full' : 'shaded',
    label: surface.id === 'mesh-full' ? 'Shaded surface — full resolution' : 'Shaded surface — simplified',
  }))];
}

async function loadObject(url: string, kind: Layer['kind'], mode = ''): Promise<Object3D> {
  if (kind !== 'obj') {
    const geometry = await new PLYLoader().loadAsync(url);
    if (!geometry.getAttribute('position')?.count) { geometry.dispose(); throw new Error('The scan has no geometry.'); }
    if (kind === 'cloud') return new Points(geometry, new PointsMaterial({ size: 2, sizeAttenuation: false,
      color: '#ffffff', vertexColors: !!geometry.getAttribute('color') }));
    if (mode === 'shaded' || mode === 'shaded-full') {
      if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
      return new Mesh(geometry, new MeshStandardMaterial({ color: '#b8b8b8', roughness: 1, metalness: 0 }));
    }
    return new Mesh(geometry, new MeshBasicMaterial({ color: '#ffffff', vertexColors: !!geometry.getAttribute('color') }));
  }
  // Keep the native manager open while MTL, OBJ and their texture images are loaded.
  const manager = new LoadingManager();
  let assetError = '';
  const complete = new Promise<void>(resolve => { manager.onLoad = resolve; });
  manager.onError = failed => { assetError = `Could not load scan asset: ${failed}`; };
  manager.itemStart('scan');
  let root: Object3D | undefined;
  try {
    // OpenMVS writes Tr=1 for opaque surfaces; its convention is the inverse of standard MTL.
    const materialLoader = new MTLLoader(manager);
    materialLoader.setMaterialOptions({ invertTrProperty: mode === 'photo' });
    const materials = await materialLoader.loadAsync(url.replace(/\.obj$/, '.mtl'));
    materials.preload();
    root = await new OBJLoader(manager).setMaterials(materials).loadAsync(url);
    manager.itemEnd('scan');
    await complete;
    if (assetError) throw new Error(assetError);
    root.traverse(object => {
      if (!(object instanceof Mesh)) return;
      const unlit = (original: Material) => {
        const source = original as MeshPhongMaterial;
        const material = new MeshBasicMaterial({ color: source.color, map: source.map,
          opacity: source.opacity, transparent: source.transparent, vertexColors: !source.map && source.vertexColors });
        original.dispose();
        return material;
      };
      object.material = Array.isArray(object.material) ? object.material.map(unlit) : unlit(object.material);
    });
    return root;
  } catch (error) {
    if (root) disposeObject(root);
    throw error;
  }
}

export function setupScan(panel: HTMLElement) {
  panel.innerHTML = `
    <div class="scan-controls">
      <label>Result <select data-scan aria-label="Scan result"></select></label>
      <button type="button" data-manage>Manage scans…</button>
      <label>Layer <select data-layer aria-label="Scan display layer"></select></label>
      <label data-point-size>Point size <input type="range" min="1" max="6" step="0.5" value="2" />
        <output>2 px</output></label>
      <button type="button" data-refresh>Refresh scans</button>
      <span data-refresh-status role="status" aria-live="polite"></span>
      <label title="Estimated tag locations, shown through surfaces"><input type="checkbox" data-tags checked />
        <span data-tag-count>AprilTags</span></label>
      <p role="status" aria-live="polite">Select Scan to load the processed result.</p>
    </div>
    <div id="scan-viewer" aria-label="Interactive scan viewer"></div>`;
  const select = panel.querySelector<HTMLSelectElement>('[data-scan]')!;
  const layers = panel.querySelector<HTMLSelectElement>('[data-layer]')!;
  const size = panel.querySelector<HTMLInputElement>('input[type=range]')!;
  const output = panel.querySelector('output')!;
  const pointSize = panel.querySelector<HTMLElement>('[data-point-size]')!;
  const refresh = panel.querySelector<HTMLButtonElement>('[data-refresh]')!;
  const refreshStatus = panel.querySelector<HTMLElement>('[data-refresh-status]')!;
  const tags = panel.querySelector<HTMLInputElement>('[data-tags]')!;
  const tagCount = panel.querySelector<HTMLElement>('[data-tag-count]')!;
  const status = panel.querySelector('[role=status]')!;
  const container = panel.querySelector<HTMLElement>('#scan-viewer')!;
  let scans: Scan[] = [];
  let viewer: ScanViewer | undefined;
  let surfaceLight: PointLight | undefined;
  let lightDefaults: { ambient: AmbientLight; intensity: number; visible: boolean } | undefined;
  let material: PointsMaterial | undefined;
  let page: { handleMessage(message: unknown): void; resize(): void } | undefined;
  let loading = false;
  let initialized = false;
  let generation = 0;
  let interactionGeneration = 0;
  document.addEventListener('pointerdown', () => { interactionGeneration++; }, true);
  document.addEventListener('pointermove', event => { if (event.buttons) interactionGeneration++; }, true);
  document.addEventListener('wheel', () => { interactionGeneration++; }, true);
  document.addEventListener('keydown', () => { interactionGeneration++; }, true);
  document.addEventListener('input', () => { interactionGeneration++; }, true);
  const completion = document.createElement('div'); completion.setAttribute('role', 'status'); completion.setAttribute('aria-live', 'polite');
  panel.querySelector('.scan-controls')!.append(completion);
  let tagOverlay: ReturnType<typeof createScanTags> | undefined;
  let renderedScan: Scan | undefined;
  const workflow = createScanWorkflowPanel({
    capture: () => renderedScan, loading: () => loading,
    addCaptures: purpose => manager.addCaptures(renderedScan?.key ?? select.value, purpose),
  });
  const workflowTools = document.createElement('div'); workflowTools.className = 'scan-workflow-tools';
  workflowTools.dataset.campervanControl = 'true';
  const reviewButton = document.createElement('button'); reviewButton.type = 'button';
  reviewButton.textContent = 'Review capture…'; reviewButton.setAttribute('aria-haspopup', 'dialog');
  reviewButton.setAttribute('aria-controls', 'scan-workflow'); reviewButton.onclick = () => workflow.openReview();
  workflowTools.append(reviewButton);
  function refreshWorkflow() { workflow.refresh(); reviewButton.disabled = loading || !renderedScan; }
  function attachWorkflow() {
    (container.querySelector('.tcv_cad_toolbar') ?? panel.querySelector('.scan-controls'))?.append(workflowTools);
    refreshWorkflow();
  }
  const camera = createViewerCamera(container, () => viewer, 'campervan.scan.camera.reference', () => loading);
  attachWorkflow();
  const manager = createScanLibrary({ results: () => scans, currentKey: () => select.value,
    view: key => changeResult(key), changed: preserveSelection => refreshScans(preserveSelection), interactionGeneration: () => interactionGeneration,
    canAutoOpen: () => !panel.hidden,
    importCompleted(key, autoOpen) {
      const announce = (detail = 'Capture processing complete.') => { completion.replaceChildren(`${detail} `); const button = document.createElement('button');
        button.type = 'button'; button.textContent = 'Review capture'; button.onclick = () => { void review(false); }; completion.append(button); };
      const review = async (guard: boolean) => {
        if (!guard) {
          completion.replaceChildren(); await changeResult(key);
          if (renderedScan?.key === key) workflow.openReview();
          else announce('Could not display the completed capture.');
          return;
        }
        const token = interactionGeneration; const sceneToken = generation; const previousKey = select.value;
        const previousLayer = layers.value; const previousScan = renderedScan;
        const valid = () => token === interactionGeneration && sceneToken === generation && !panel.hidden
          && select.value === previousKey && layers.value === previousLayer && renderedScan === previousScan
          && scans.some(item => item.key === key && !item.archived);
        const scan = scans.find(item => item.key === key && !item.archived); if (!scan || !page || !valid()) { announce(); return; }
        const layer = preferredLayer(scan);
        let root: Object3D;
        try { root = await loadObject(layerUrl(scan, layer), layer.kind, layer.id); }
        catch (error) { announce(`Could not load the completed capture: ${error instanceof Error ? error.message : String(error)}.`); return; }
        if (!valid()) { disposeObject(root); announce(); return; }
        completion.replaceChildren(); await changeResult(key, { layer, root });
        if (token !== interactionGeneration || panel.hidden || renderedScan?.key !== key) announce();
        else workflow.openReview();
      };
      if (autoOpen && !panel.hidden) void review(true); else announce();
    } });
  panel.querySelector<HTMLButtonElement>('[data-manage]')!.onclick = () => { void manager.open(); };
  tags.onchange = () => { tagOverlay?.setVisible(tags.checked); };

  size.oninput = () => {
    output.value = `${size.value} px`;
    if (material) material.size = Number(size.value);
    viewer?.update(true, false);
  };

  function preferredLayer(scan: Scan): Layer {
    const available = availableLayers(scan);
    const previous = layers.value || sessionStorage.getItem('campervan.scan.layer') || '';
    return available.find(layer => layer.id === previous)
      ?? ['colour', 'mesh', 'photo', 'cloud'].map(id => available.find(layer => layer.id === id)).find(layer => !!layer)
      ?? available[0];
  }
  function layerUrl(scan: Scan, layer: Layer) {
    return scan.id
      ? `/api/v1/scans/runs/${encodeURIComponent(scan.id)}/assets/${layer.asset.split('/').map(encodeURIComponent).join('/')}`
      : `/api/v1/scans/${encodeURIComponent(scan.name)}`;
  }
  function layerOptions() {
    const scan = scans.find(item => item.key === select.value);
    const chosen = scan ? preferredLayer(scan) : undefined;
    layers.replaceChildren();
    if (!scan) { layers.disabled = true; return; }
    for (const layer of availableLayers(scan)) {
      layers.add(new Option(layer.label, layer.id));
    }
    if (chosen) layers.value = chosen.id;
    layers.disabled = layers.options.length < 2;
  }

  function updateSurfaceLight() {
    if (!surfaceLight || !viewer?.ready) return;
    const projection = viewer.rendered.camera.camera as unknown as Camera;
    const distance = Math.max(.1, projection.position.distanceTo(new Vector3().fromArray(viewer.getCameraTarget())));
    surfaceLight.position.set(distance * .2, distance * .15, 0)
      .applyQuaternion(projection.quaternion).add(projection.position);
    // Keep illumination near the orbit target steady while zooming; use normal inverse-square attenuation.
    surfaceLight.intensity = 3 * distance * distance;
  }

  function surfaceLighting(enabled: boolean) {
    surfaceLight?.removeFromParent(); surfaceLight = undefined;
    if (!viewer?.ready) return;
    const { ambientLight, directLight, scene } = viewer.rendered;
    if (!lightDefaults || lightDefaults.ambient !== ambientLight) {
      lightDefaults = { ambient: ambientLight, intensity: ambientLight.intensity, visible: directLight.visible };
    }
    ambientLight.intensity = enabled ? .6 : lightDefaults.intensity;
    directLight.visible = enabled ? false : lightDefaults.visible;
    if (enabled) {
      surfaceLight = new PointLight(0xffffff, 1); scene.add(surfaceLight); updateSurfaceLight();
    }
  }

  async function loadLayer(prepared?: { layer: Layer; root: Object3D }) {
    const scan = scans.find(item => item.key === select.value && !item.archived);
    if (!scan || !page) return;
    const layer = prepared?.layer ?? availableLayers(scan).find(item => item.id === layers.value) ?? preferredLayer(scan);
    sessionStorage.setItem('campervan.scan.result', scan.key);
    sessionStorage.setItem('campervan.scan.layer', layer.id);
    const token = ++generation;
    const aligned = scan.alignment?.status === 'aligned' && !!scan.alignment.matrix;
    let saved = camera.cameraState()
      ?? JSON.parse(localStorage.getItem('campervan.scan.camera.reference') ?? 'null') as CameraState | null;
    loading = true;
    refreshWorkflow();
    camera.cancelCameraAnimation();
    status.textContent = `Loading ${scan.display_name} · ${layer.label}…`;
    let root: Object3D | undefined;
    try {
      root = prepared ? prepared.root : await loadObject(layerUrl(scan, layer), layer.kind, layer.id);
      if (token !== generation) { disposeObject(root); return; }
      // Navigation during an asset load takes precedence over the earlier snapshot.
      saved = camera.cameraState() ?? saved;
      if (aligned) root.applyMatrix4(new Matrix4().fromArray(scan.alignment!.matrix!.flat()).transpose());
      const bounds = new Box3().setFromObject(root);
      if (bounds.isEmpty()) throw new Error('The scan contains no geometry.');
      const { min, max } = bounds;
      page.handleMessage({
        type: 'data', data: { shapes: { id: '/Scan', name: 'Scan',
          bb: { xmin: min.x, ymin: min.y, zmin: min.z, xmax: max.x, ymax: max.y, zmax: max.z },
          parts: [{ id: '/Scan/Cloud', name: layer.label, type: 'vertices', state: [0, 1],
            size: Number(size.value), color: '#ffffff', shape: { obj_vertices: [] } }],
        } },
        config: { theme: 'dark', tools: false, glass: false, control: 'orbit', up: 'Z',
          ...(saved ?? { ortho: false, zoom: 0.65 }), resetCamera: 'keep', axes: true, axes0: true,
          grid: [false, false, false] },
      });
      // Let the existing renderer own the bulk layer without registering millions of CAD components.
      const group = viewer!.rendered.nestedGroup.groups['/Scan/Cloud'];
      for (const child of [...group.children]) { disposeObject(child); group.remove(child); }
      group.add(root);
      surfaceLighting(layer.id === 'shaded' || layer.id === 'shaded-full');
      renderedScan = scan;
      refreshWorkflow();
      if (token !== generation) { root = undefined; return; }
      tagOverlay ??= createScanTags(container, () => viewer?.rendered.camera.camera as unknown as Camera);
      tagOverlay.setTags(scan.tags ?? [], aligned ? scan.alignment!.matrix : undefined);
      tagOverlay.setVisible(tags.checked);
      tags.disabled = !scan.tags?.length;
      tagCount.textContent = `AprilTags (${scan.tags?.length ?? 0})`;
      tags.parentElement!.title = `${scan.tag_note ?? 'No saved tag poses.'} Markers are shown through surfaces.`;
      material = root instanceof Points ? root.material as PointsMaterial : undefined;
      if (material) material.size = Number(size.value);
      pointSize.hidden = layer.kind !== 'cloud';
      camera.attachCube();
      viewer!.rendered.orientationMarker.setVisible(true);
      for (const child of container.querySelectorAll<HTMLElement>('.tcv_cad_toolbar > *')) {
        if (child.querySelector('.tcv_button_perspective, .tcv_button_reset, .tcv_button_resize')) {
          child.dataset.campervanControl = 'true';
        }
      }
      if (!panel.hidden) page.resize();
      if (saved) {
        const projection = viewer!.rendered.camera.camera;
        const zoom = saved.ortho
          ? saved.viewHeight ? (projection.top - projection.bottom) / saved.viewHeight : saved.zoom : null;
        viewer!.setCameraLocationSettings(saved.position, saved.quaternion, saved.target, zoom, false);
      }
      viewer!.update(true, false);
      const vertices = root instanceof Mesh || root instanceof Points ? root.geometry.getAttribute('position').count : null;
      const unitStatus = scan.units === 'arbitrary' ? 'arbitrary units · metric scale unavailable' : 'metres';
      status.textContent = `${vertices?.toLocaleString() ?? ''} ${layer.label} · ${unitStatus} · `
        + (aligned ? `${scan.alignment!.target_frame} axes · origin tag ${scan.alignment!.definition!.origin_tag}`
          : scan.alignment?.reason ?? 'unaligned scan coordinates')
        + (scan.pose_source === 'gtsam_measured_distances' ? ' · distance-adjusted'
          : scan.measured === false ? ' · unmeasured trial' : '');
      root = undefined; // The native renderer disposes the attached layer when it replaces the scene.
    } catch (error) {
      if (root) disposeObject(root);
      if (token === generation) status.textContent = error instanceof Error ? error.message : String(error);
    } finally {
      if (token === generation) { loading = false; camera.saveCamera(); attachWorkflow(); }
    }
  }

  function clearDisplayedResult() {
    ++generation; loading = false;
    sessionStorage.removeItem('campervan.scan.result'); sessionStorage.removeItem('campervan.scan.layer');
    const group = viewer?.rendered.nestedGroup.groups['/Scan/Cloud'];
    if (group) for (const child of [...group.children]) { disposeObject(child); group.remove(child); }
    material = undefined; renderedScan = undefined;
    surfaceLighting(false);
    tagOverlay?.setTags([]); tagCount.textContent = 'AprilTags (0)'; tags.disabled = true;
    pointSize.hidden = true; size.disabled = true; attachWorkflow();
    camera.cancelCameraAnimation(); viewer?.update(true, false);
    status.textContent = 'No active results — open Manage scans to restore one.';
  }

  async function changeResult(key: string, prepared?: { layer: Layer; root: Object3D }) {
    if (!scans.some(scan => scan.key === key && !scan.archived)) { if (prepared) disposeObject(prepared.root); return; }
    ++generation; select.value = key; layerOptions(); await loadLayer(prepared);
  }

  async function refreshScans(preserveSelection = false) {
    const previousKey = select.value;
    const preferredKey = previousKey || sessionStorage.getItem('campervan.scan.result');
    const discovered = await readScanResults();
    const retainedKey = select.value;
    scans = discovered;
    const active = scans.filter(scan => !scan.archived).sort((a, b) =>
      (a.group_name ?? 'Ungrouped').localeCompare(b.group_name ?? 'Ungrouped')
      || (a.group_id ?? '').localeCompare(b.group_id ?? '')
      || a.display_name.localeCompare(b.display_name) || a.key.localeCompare(b.key));
    const selected = active.find(scan => scan.key === preferredKey) ?? active.find(scan => scan.is_default) ?? active[0];
    const groups = new Set(active.map(scan => scan.group_id));
    select.replaceChildren();
    let group: HTMLOptGroupElement | undefined;
    let previousGroup: string | null | undefined;
    for (const scan of active) {
      const option = new Option(scan.display_name, scan.key);
      if (groups.size > 1) {
        if (!group || scan.group_id !== previousGroup) {
          group = document.createElement('optgroup'); group.label = scan.group_name ?? 'Ungrouped'; select.append(group);
          previousGroup = scan.group_id;
        }
        group.append(option);
      } else select.add(option);
    }
    if (preserveSelection) {
      if (active.some(scan => scan.key === retainedKey)) select.value = retainedKey; else select.selectedIndex = -1;
      select.disabled = !active.length; tags.disabled = !renderedScan?.tags?.length; size.disabled = !renderedScan;
      layerOptions();
      const updated = active.find(scan => scan.key === renderedScan?.key); if (updated) renderedScan = updated;
      return;
    }
    select.disabled = !selected; tags.disabled = !renderedScan?.tags?.length; size.disabled = !selected;
    if (selected) select.value = selected.key;
    layerOptions();
    if (!selected) clearDisplayedResult();
    else if (previousKey && selected.key !== previousKey) { clearDisplayedResult(); await loadLayer(); }
    else if (!previousKey && page) await loadLayer();
    else if (renderedScan?.key === selected.key) renderedScan = selected;
  }

  async function initialize() {
    status.textContent = 'Loading available scans…';
    try {
      await refreshScans();
      const css = document.createElement('link');
      css.rel = 'stylesheet'; css.href = assetUrl('viewer-assets/css/three-cad-viewer.css');
      const styles = new Promise<void>((resolve, reject) => {
        css.onload = () => resolve(); css.onerror = () => reject(new Error('Could not load scan viewer styles.'));
      });
      document.head.append(css);
      const url = assetUrl('viewer-assets/js/ocp-viewer-core/index.js');
      const [core] = await Promise.all([import(/* @vite-ignore */ url), styles]);
      class ScanRenderer extends library.Viewer {
        constructor(...args: any[]) {
          super(...args); viewer = this as unknown as ScanViewer;
          const update = this.update.bind(this);
          this.update = (...args: any[]) => { updateSurfaceLight(); update(...args); camera.updateCube(); tagOverlay?.update(); };
        }
      }
      page = core.createPage({
        Viewer: ScanRenderer, Display: library.Display, Timer: library.Timer,
        container, listen: false, theme: 'dark',
        getSize: () => ({ width: container.clientWidth + 20, height: container.clientHeight }),
        overrides: { display: { tools: false, glass: false, theme: 'dark' }, viewer: { tools: false } },
        send(command: string) { if (command === 'status') camera.saveCamera(); },
      });
      new ResizeObserver(() => { if (viewer?.ready && !panel.hidden) page!.resize(); }).observe(container);
      await loadLayer();
    } catch (error) { status.textContent = error instanceof Error ? error.message : String(error); }
  }

  select.onchange = () => changeResult(select.value);
  layers.onchange = () => { void loadLayer(); };
  refresh.onclick = () => {
    refresh.disabled = true;
    refresh.textContent = 'Refreshing…';
    refresh.setAttribute('aria-busy', 'true');
    refreshStatus.textContent = 'Refreshing scans…';
    void Promise.all([refreshScans(), manager.refresh()])
      .then(() => { refreshStatus.textContent = 'Scans refreshed.'; })
      .catch(error => { refreshStatus.textContent = `Refresh failed: ${String(error)}`; })
      .finally(() => {
        refresh.disabled = false; refresh.textContent = 'Refresh scans';
        refresh.removeAttribute('aria-busy'); refreshWorkflow();
      });
  };
  onTab(tab => {
    interactionGeneration++;
    if (tab !== 'scan') workflow.hide();
    if (tab !== 'scan') { camera.cancelCameraAnimation(); return; }
    if (!initialized) { initialized = true; void initialize(); }
    else if (viewer?.ready) page!.resize();
  });
}
