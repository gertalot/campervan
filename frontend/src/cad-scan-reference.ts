/** A scan is a display reference, independent of CAD geometry, selection and furniture mirroring. */
import { Matrix4, type Object3D } from 'three';
import { createScanPanels, type ScanDisplay } from './scan-panels';
import { disposeObject, layerUrl, loadObject } from './scan-assets';
import { readScanResults, type ScanResult } from './scan-library-api';
import { isStaticSite } from './site-runtime';
import { setupCrossSections, type CrossSectionViewer } from './cad-cross-sections';

interface ReferenceViewer extends CrossSectionViewer {
  setScanReference(scan?: ScanDisplay, vehicleOpacity?: number, scanOpacity?: number): void;
}

export function setupCadScanReference(container: HTMLElement, viewer: ReferenceViewer) {
  container.hidden = false;
  container.insertAdjacentHTML('beforeend', `
    <label class="reference-toggle"><input type="checkbox" data-visible /> Show scan reference with Vehicle</label>
    <label class="reference-result">Reconstruction<select data-result></select></label>
    <button type="button" data-refresh>Refresh references</button>
    <label class="reference-opacity">Scan opacity <output data-opacity-value></output>
      <input type="range" min="0" max="100" step="5" data-opacity />
    </label>
    <label class="reference-opacity">Vehicle opacity <output data-vehicle-opacity-value></output>
      <input type="range" min="0" max="100" step="5" data-vehicle-opacity />
    </label>
    <p role="status" aria-live="polite" data-status></p>`);
  const find = <T extends HTMLElement>(selector: string) => container.querySelector<T>(selector)!;
  const visible = find<HTMLInputElement>('[data-visible]');
  const select = find<HTMLSelectElement>('[data-result]');
  const opacity = find<HTMLInputElement>('[data-opacity]');
  const output = find<HTMLOutputElement>('[data-opacity-value]');
  const vehicleOpacity = find<HTMLInputElement>('[data-vehicle-opacity]');
  const vehicleOutput = find<HTMLOutputElement>('[data-vehicle-opacity-value]');
  const status = find<HTMLParagraphElement>('[data-status]');
  const sections = isStaticSite ? undefined : setupCrossSections(container, viewer);
  const key = 'campervan.cad.scan-reference';
  const saved = JSON.parse(localStorage.getItem(key) ?? '{}');
  visible.checked = saved.visible ?? true;
  opacity.value = String(saved.opacity ?? (isStaticSite ? 100 : 45));
  vehicleOpacity.value = String(saved.vehicleOpacity ?? (isStaticSite ? 0 : 35));
  let scans: ScanResult[] = [], root: Object3D | undefined, generation = 0;
  let scanDisplay: ReturnType<typeof createScanPanels> | undefined;
  const selected = () => scans.find(scan => scan.key === select.value);

  function save() {
    localStorage.setItem(key, JSON.stringify({ result: select.value, visible: visible.checked,
      opacity: Number(opacity.value), vehicleOpacity: Number(vehicleOpacity.value) }));
  }
  function display() {
    output.value = `${opacity.value}%`;
    opacity.setAttribute('aria-valuetext', `${opacity.value} percent`);
    viewer.setScanReference(visible.checked ? scanDisplay : undefined, Number(vehicleOpacity.value) / 100,
      Number(opacity.value) / 100);
    vehicleOutput.value = `${vehicleOpacity.value}%`;
    vehicleOpacity.setAttribute('aria-valuetext', `${vehicleOpacity.value} percent`);
  }
  function position() {
    const scan = selected();
    if (!scan || !root) return;
    const translation = scan.cad_reference!.translation_mm;
    const rotation = scan.cad_reference!.rotation;
    const orientation = rotation ? new Matrix4().fromArray([
      ...rotation[0], 0, ...rotation[1], 0, ...rotation[2], 0, 0, 0, 0, 1,
    ]).transpose() : new Matrix4();
    const transform = new Matrix4().makeTranslation(translation[0], translation[1], translation[2])
      .multiply(new Matrix4().makeScale(1000, 1000, 1000))
      .multiply(orientation)
      .multiply(new Matrix4().fromArray(scan.alignment!.matrix!.flat()).transpose());
    root.matrix.copy(transform).decompose(root.position, root.quaternion, root.scale);
    root.updateMatrixWorld(true);
    scanDisplay = createScanPanels(root, scan.key);
    display();
    void sections?.setReference(scan, root);
  }
  function clearReference() {
    viewer.setScanReference(undefined);
    void sections?.setReference(undefined, undefined);
    scanDisplay?.dispose();
    scanDisplay = undefined;
    if (root) { disposeObject(root); root = undefined; }
  }
  async function load() {
    const token = ++generation;
    clearReference();
    const scan = selected();
    if (!scan) return;
    const layer = scan.layers?.find(layer => layer.id === 'mesh')
      ?? scan.layers?.find(layer => layer.kind === 'mesh');
    if (!layer) { status.textContent = 'This reconstruction has no reference mesh.'; return; }
    status.textContent = 'Loading reference mesh…';
    try {
      const loaded = await loadObject(layerUrl(scan, layer), layer.kind);
      if (token !== generation) { disposeObject(loaded); return; }
      loaded.name = 'Scan reference';
      root = loaded;
      position();
      status.textContent = 'Aligned to CAD · reference only';
    } catch (error) {
      if (token === generation) status.textContent = `Reference failed: ${String(error)}`;
    }
  }
  visible.onchange = () => { display(); save(); };
  opacity.oninput = () => { display(); save(); };
  vehicleOpacity.oninput = () => { display(); save(); };
  select.onchange = () => { save(); void load(); };
  display();
  const refresh = find<HTMLButtonElement>('[data-refresh]');
  async function refreshReferences() {
    const previous = select.value || saved.result;
    refresh.disabled = true; refresh.textContent = 'Refreshing…';
    select.disabled = true;
    status.textContent = 'Loading available references…';
    try {
      const results = await readScanResults();
      scans = results.filter(scan => !scan.archived && scan.units === 'm' && scan.alignment?.status === 'aligned'
        && scan.alignment.matrix && scan.cad_reference);
      select.replaceChildren(...scans.map(scan => new Option(scan.display_name, scan.key)));
      if (scans.some(scan => scan.key === previous)) select.value = previous;
      if (!scans.length) {
        generation++;
        clearReference();
        status.textContent = 'No CAD-registered scan available.'; return;
      }
      await load();
    } catch (error) { status.textContent = `Could not list references: ${String(error)}`; }
    finally {
      refresh.disabled = false; refresh.textContent = 'Refresh references';
      select.disabled = !scans.length;
    }
  }
  refresh.onclick = () => { void refreshReferences(); };
  void refreshReferences();
  return { setCentreline: sections?.setCentreline };
}
