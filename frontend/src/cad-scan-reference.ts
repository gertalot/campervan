/** A scan is a display reference, independent of CAD geometry, selection and furniture mirroring. */
import { Matrix4, Mesh, Points, type Object3D } from 'three';
import { disposeObject, layerUrl, loadObject } from './scan-assets';
import { readScanResults, type ScanResult } from './scan-library-api';
import { isStaticSite } from './site-runtime';

interface ReferenceViewer {
  setScanReference(root: Object3D | undefined): void;
  setVehicleComparisonOpacity(opacity: number | null): void;
}

export function setupCadScanReference(container: HTMLElement, viewer: ReferenceViewer) {
  if (isStaticSite) return;
  container.hidden = false;
  container.insertAdjacentHTML('beforeend', `
    <label class="reference-toggle"><input type="checkbox" data-visible /> Show scan reference</label>
    <label class="reference-result">Reconstruction<select data-result></select></label>
    <button type="button" data-refresh>Refresh references</button>
    <label class="reference-opacity">Scan opacity <output data-opacity-value></output>
      <input type="range" min="0" max="100" step="5" data-opacity />
    </label>
    <label class="reference-opacity">Vehicle opacity <output data-vehicle-opacity-value></output>
      <input type="range" min="0" max="100" step="5" data-vehicle-opacity />
    </label>
    <p>Light pink is vehicle CAD. See inside fades nearby vehicle surfaces and hides the outside-facing backs
      of scan surfaces. Both opacity sliders still apply. Furniture and visibility switches keep their usual behaviour.</p>
    <details><summary>Reference position</summary>
      <p>Offsets in CAD millimetres. X across, Y forwards, Z up. Reset restores the saved registration.</p>
      <div class="reference-offsets">
        <label>X<input type="number" step="1" required data-offset="0" /></label>
        <label>Y<input type="number" step="1" required data-offset="1" /></label>
        <label>Z<input type="number" step="1" required data-offset="2" /></label>
      </div>
      <button type="button" data-reset>Reset position</button>
    </details>
    <p role="status" aria-live="polite" data-status></p>`);
  const find = <T extends HTMLElement>(selector: string) => container.querySelector<T>(selector)!;
  const visible = find<HTMLInputElement>('[data-visible]');
  const select = find<HTMLSelectElement>('[data-result]');
  const opacity = find<HTMLInputElement>('[data-opacity]');
  const output = find<HTMLOutputElement>('[data-opacity-value]');
  const vehicleOpacity = find<HTMLInputElement>('[data-vehicle-opacity]');
  const vehicleOutput = find<HTMLOutputElement>('[data-vehicle-opacity-value]');
  const status = find<HTMLParagraphElement>('[data-status]');
  const offsets = [...container.querySelectorAll<HTMLInputElement>('[data-offset]')];
  const key = 'campervan.cad.scan-reference';
  const saved = JSON.parse(localStorage.getItem(key) ?? '{}');
  visible.checked = saved.visible ?? true;
  opacity.value = String(saved.opacity ?? 45);
  vehicleOpacity.value = String(saved.vehicleOpacity ?? 35);
  const translations: Record<string, number[]> = saved.translations ?? {};
  let scans: ScanResult[] = [], root: Object3D | undefined, generation = 0;
  const selected = () => scans.find(scan => scan.key === select.value);

  function save() {
    localStorage.setItem(key, JSON.stringify({ result: select.value, visible: visible.checked,
      opacity: Number(opacity.value), vehicleOpacity: Number(vehicleOpacity.value), translations }));
  }
  function display() {
    output.value = `${opacity.value}%`;
    opacity.setAttribute('aria-valuetext', `${opacity.value} percent`);
    if (root) {
      root.visible = visible.checked;
      root.traverse(object => {
        if (!(object instanceof Mesh || object instanceof Points)) return;
        for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
          material.opacity = Number(opacity.value) / 100;
          material.transparent = material.opacity < 1;
          material.depthWrite = !material.transparent;
          material.needsUpdate = true;
        }
      });
    }
    viewer.setScanReference(root);
    vehicleOutput.value = `${vehicleOpacity.value}%`;
    vehicleOpacity.setAttribute('aria-valuetext', `${vehicleOpacity.value} percent`);
    viewer.setVehicleComparisonOpacity(visible.checked && root ? Number(vehicleOpacity.value) / 100 : null);
  }
  function position() {
    const scan = selected();
    if (!scan || !root) return;
    const translation = translations[scan.key] ?? scan.cad_reference!.translation_mm;
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
    display();
  }
  async function load() {
    const token = ++generation;
    viewer.setScanReference(undefined);
    viewer.setVehicleComparisonOpacity(null);
    if (root) { disposeObject(root); root = undefined; }
    const scan = selected();
    if (!scan) return;
    const translation = translations[scan.key] ?? scan.cad_reference!.translation_mm;
    offsets.forEach((input, i) => { input.value = String(translation[i]); });
    const layer = scan.layers?.find(layer => layer.id === 'mesh')
      ?? scan.layers?.find(layer => layer.kind === 'mesh');
    if (!layer) { status.textContent = 'This reconstruction has no reference mesh.'; return; }
    status.textContent = 'Loading reference mesh…';
    try {
      const loaded = await loadObject(layerUrl(scan, layer), layer.kind);
      if (token !== generation) { disposeObject(loaded); return; }
      loaded.name = 'Scan reference';
      loaded.traverse(object => { object.userData.campervanOverlay = true; object.raycast = () => {}; });
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
  for (const input of offsets) input.onchange = () => {
    if (offsets.some(field => field.value.trim() === '' || !field.validity.valid || !Number.isFinite(field.valueAsNumber))) {
      input.reportValidity(); return;
    }
    translations[select.value] = offsets.map(field => field.valueAsNumber);
    position(); save();
  };
  find<HTMLButtonElement>('[data-reset]').onclick = () => {
    const scan = selected(); if (!scan) return;
    delete translations[scan.key];
    offsets.forEach((input, i) => { input.value = String(scan.cad_reference!.translation_mm[i]); });
    position(); save();
  };
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
        generation++; viewer.setScanReference(undefined); viewer.setVehicleComparisonOpacity(null);
        if (root) { disposeObject(root); root = undefined; }
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
}
