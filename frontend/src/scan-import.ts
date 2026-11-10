/** Shared capture selection and explicit preview/photographic processing. */
import { createTagLayout, processCaptures, readScanImports, uploadCapture,
  captureDescription, type CapturePurpose, type CaptureProcessing, type ScanImports, type ProcessingJob } from './scan-import-api';
import { jobStatus, createJobView } from './scan-job-status';
import type { TagAlignmentDefinition } from './scan-library-api';
interface Host {
  defaultLayout(group: string): string | undefined;
  changed(): Promise<void>;
  view(key: string): void;
  closed(group: string): void;
  interactionGeneration(): number;
  canAutoOpen(): boolean;
  completed(key: string, autoOpen: boolean): void;
}
export function createScanImport(host: Host) {
  const dialog = document.createElement('dialog'); dialog.className = 'scan-import-dialog';
  dialog.setAttribute('aria-labelledby', 'scan-import-title');
  dialog.innerHTML = `<header><h2 id="scan-import-title">Create from captures</h2><button type="button" data-close>Close</button></header>
    <p data-group></p>
    <form>
      <fieldset><legend>Processing purpose</legend>
        <label>Action <select data-purpose required>
          <option value="">Choose an action…</option>
          <option value="preview">Create quick preview…</option>
          <option value="photographic">Create detailed reconstruction…</option>
        </select></label>
        <details data-guidance><summary>Capture guidance</summary><p data-help></p></details>
      </fieldset>
      <fieldset><legend>Capture inputs</legend>
        <label class="scan-import-drop">Choose databases or JPEG, PNG and HEIC photos, or drop them here
          <input type="file" multiple accept=".db,.jpg,.jpeg,.png,.heic" aria-label="Choose capture databases or original photos" /></label>
        <p>Checked inputs are used for this run. Upload originals to keep them in this group independently of processing.</p>
        <div data-files></div>
        <p data-selection role="status"></p>
        <button type="button" data-upload>Upload queued captures</button>
      </fieldset>
      <fieldset><legend>Tags and reconstruction</legend>
        <label>Tag settings <select data-layout></select></label>
        <p>Positions are detected from this reconstruction’s selected captures. These settings hold the tag family and printed size.</p>
        <div data-new-layout>
          <label>New tag settings name <input data-layout-name required maxlength="120" /></label>
          <label>Tag family <select data-family><option value="36h11">AprilTag 36h11</option></select></label>
          <label>Printed tag size <input data-tag-size type="number" min="0.1" step="any" value="80" required /> mm</label>
          <p>Measure the tag's black outer square, excluding the paper margin. A new layout starts with no distances or axis roles.</p>
        </div>
        <label>Result name <input data-name required maxlength="120" /></label>
        <label data-preview-settings>Preview fusion resolution <select data-resolution><option value="5">5 mm</option><option value="10">10 mm</option></select></label>
        <p data-detailed-settings hidden>Photographic geometry uses native-resolution images, 4 threads, a 500,000-triangle display mesh and 4096 px texture.</p>
      </fieldset>
      <button type="submit" data-process>Create from captures</button>
      <p>Retry creates a new run from the checked inputs and settings shown above.</p>
    </form>
    <p role="alert" data-error></p>
    <section data-progress hidden><h3>Processing</h3><p role="status" aria-live="polite" data-stage></p>
      <progress aria-label="Capture processing progress"></progress>
      <button type="button" data-view hidden>Show result in viewer</button>
    </section>`;
  document.body.append(dialog);
  const get = <T extends HTMLElement>(selector: string) => dialog.querySelector<T>(selector)!;
  const form = get<HTMLFormElement>('form'); const files = get<HTMLInputElement>('input[type=file]');
  const fileList = get<HTMLDivElement>('[data-files]'); const layout = get<HTMLSelectElement>('[data-layout]');
  const layoutName = get<HTMLInputElement>('[data-layout-name]'); const tagSize = get<HTMLInputElement>('[data-tag-size]');
  const newLayout = get<HTMLDivElement>('[data-new-layout]'); const name = get<HTMLInputElement>('[data-name]');
  const resolution = get<HTMLSelectElement>('[data-resolution]');
  const purpose = get<HTMLSelectElement>('[data-purpose]');
  const upload = get<HTMLButtonElement>('[data-upload]');
  const error = get<HTMLParagraphElement>('[data-error]'); const progressPanel = get<HTMLElement>('[data-progress]');
  const stage = get<HTMLElement>('[data-stage]'); const meter = get<HTMLProgressElement>('progress');
  const view = get<HTMLButtonElement>('[data-view]');
  let data: ScanImports = { captures: [], layouts: [], jobs: [] };
  let group = ''; let queued: File[] = []; let selected = new Set<string>();
  let busy = false; let currentJob: ProcessingJob | undefined;
  let alignmentDefinition: TagAlignmentDefinition | undefined;
  let layoutSelectionRequired = false;
  const handoffs = new Map<string, number>();
  const jobs = jobStatus;
  const subscriptions = new Map<string, () => void>();
  const jobView = createJobView(() => {
    if (currentJob?.state === 'processing') void jobs.refresh(currentJob.id); else void start();
  }, 'Retry as a new run with inputs above');
  progressPanel.append(jobView.element); jobView.element.hidden = true;
  const terminal = new Set<string>();
  const activities = new Set<{ group: string; name: string; node: HTMLElement }>();
  function fail(reason: unknown) { error.textContent = reason instanceof Error ? reason.message : String(reason); }
  function layoutChanged() {
    newLayout.hidden = layoutSelectionRequired || !!layout.value;
    for (const input of newLayout.querySelectorAll<HTMLInputElement | HTMLSelectElement>('input,select')) input.disabled = newLayout.hidden;
  }
  layout.onchange = () => { layoutSelectionRequired = false; layout.required = false; layoutChanged(); };
  function fileRows() {
    fileList.replaceChildren();
    for (const capture of data.captures.filter(item => item.group_id === group)) {
      const label = document.createElement('label'); const checkbox = document.createElement('input'); checkbox.type = 'checkbox';
      checkbox.checked = selected.has(capture.id); checkbox.disabled = busy;
      checkbox.onchange = () => {
        if (checkbox.checked) selected.add(capture.id); else selected.delete(capture.id); selectionChanged();
      };
      label.append(checkbox, `${capture.filename} · ${captureDescription(capture)} · ${capture.id.slice(0, 8)}`);
      fileList.append(label);
    }
    for (const file of queued) {
      const row = document.createElement('div'); row.className = 'scan-import-file';
      const label = document.createElement('span');
      label.textContent = `${file.name} · ${file.name.toLowerCase().endsWith('.db') ? 'Database' : 'Original photo'} · ${(file.size / 1048576).toFixed(1)} MB · queued`;
      const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove'; remove.disabled = busy;
      remove.setAttribute('aria-label', `Remove ${file.name} from this import`);
      remove.onclick = () => { queued = queued.filter(item => item !== file); fileRows(); }; row.append(label, remove); fileList.append(row);
    }
    if (!queued.length && !data.captures.some(item => item.group_id === group)) fileList.textContent = 'No captures imported.';
    upload.disabled = busy || !queued.length; selectionChanged();
  }
  function selectedPhotos() {
    return data.captures.filter(item => selected.has(item.id) && item.kind === 'photo');
  }
  function selectionChanged() {
    const incompatible = purpose.value === 'preview' && (selectedPhotos().length
      || queued.some(file => !file.name.toLowerCase().endsWith('.db')));
    get<HTMLElement>('[data-selection]').textContent = incompatible
      ? 'Quick preview needs depth databases. Upload the photos, then uncheck them, or choose detailed reconstruction.'
      : `${selected.size} imported inputs checked${queued.length ? ` · ${queued.length} queued for upload and selection` : ''}.`;
  }
  function purposeChanged() {
    const preview = purpose.value === 'preview';
    get<HTMLElement>('[data-preview-settings]').hidden = !preview; resolution.disabled = !preview;
    get<HTMLElement>('[data-detailed-settings]').hidden = purpose.value !== 'photographic';
    get<HTMLElement>('#scan-import-title').textContent = preview ? 'Create quick preview'
      : purpose.value === 'photographic' ? 'Create detailed reconstruction' : 'Create from captures';
    get<HTMLButtonElement>('[data-process]').textContent = preview ? 'Create preview'
      : purpose.value === 'photographic' ? 'Reconstruct from photos' : 'Choose a processing action';
    get<HTMLElement>('[data-help]').textContent = preview
      ? 'Use RTAB-Map with LiDAR on and HD off initially. Inspect detected tags; capture missed tags closer with surrounding context. A coarse preview does not establish measurement accuracy.'
      : purpose.value === 'photographic'
        ? 'Use overlapping original iPhone Camera stills with stable lighting and translated viewpoints. Connect overview and detail passes. JPEG, PNG and HEIC originals retain their resolution and metadata; database photographs can be selected too. No preview is required.'
        : 'Choose quick preview for depth databases, or detailed reconstruction for original photos, database photographs or a selected mixture.';
    selectionChanged();
  }
  purpose.onchange = purposeChanged;
  function addFiles(incoming: File[]) {
    if (busy) return;
    const invalid = incoming.find(file => !/\.(db|jpe?g|png|heic)$/i.test(file.name));
    if (invalid) { fail(new Error(`${invalid.name} is not a supported .db, JPEG, PNG or HEIC capture.`)); return; }
    for (const file of incoming) {
      if (!queued.includes(file)) queued.push(file);
    }
    error.textContent = ''; fileRows();
  }
  files.onchange = () => { addFiles([...files.files ?? []]); files.value = ''; };
  const drop = get<HTMLElement>('.scan-import-drop');
  drop.ondragover = event => { event.preventDefault(); if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'; };
  drop.ondrop = event => { event.preventDefault(); addFiles([...event.dataTransfer?.files ?? []]); };
  get<HTMLButtonElement>('[data-close]').onclick = () => dialog.close();
  dialog.addEventListener('close', () => host.closed(group));
  function setBusy(value: boolean) {
    busy = value;
    for (const fieldset of form.querySelectorAll('fieldset')) fieldset.disabled = value;
    get<HTMLButtonElement>('[data-process]').disabled = value || data.jobs.some(job => job.state === 'processing'); fileRows();
  }
  function jobLabel(job: ProcessingJob) {
    return job.state === 'completed' ? job.result_key ? 'Ready to view' : 'Result no longer available'
      : job.state === 'processing' ? job.stage : job.state;
  }
  function showJob(job: ProcessingJob) {
    currentJob = job; progressPanel.hidden = false; jobView.element.hidden = false; jobView.update(job); stage.hidden = true; meter.removeAttribute('value'); meter.hidden = true;
    view.hidden = !job.result_key;
    view.textContent = job.state === 'completed' ? 'Show result in viewer' : 'Show available result in viewer';
    view.onclick = () => { if (job.result_key) { dialog.close(); host.view(job.result_key); } };
  }
  function paintActivities() {
    for (const activity of activities) {
      if (!activity.node.isConnected) { activities.delete(activity); continue; }
      activity.node.replaceChildren();
      const job = data.jobs.find(item => item.group_id === activity.group);
      if (!job) continue;
      const status = document.createElement('span');
      status.textContent = `${job.name} · ${jobLabel(job)}`;
      const action = document.createElement('button'); action.type = 'button'; action.textContent = 'Show processing progress…';
      action.onclick = () => { void open(activity.group, activity.name); };
      activity.node.append(status, action);
    }
  }
  async function refresh() {
    data = await readScanImports(); paintActivities();
    if (!busy) get<HTMLButtonElement>('[data-process]').disabled = data.jobs.some(job => job.state === 'processing');
    for (const job of data.jobs) {
      if (!subscriptions.has(job.id) && job.state !== 'processing' && !handoffs.has(job.id)) terminal.add(job.id);
      jobs.publish(job);
      if (!subscriptions.has(job.id)) subscriptions.set(job.id, jobs.subscribe(job.id, updated => {
        const index = data.jobs.findIndex(item => item.id === updated.id);
        if (index >= 0) data.jobs[index] = updated;
        if (currentJob?.id === updated.id) showJob(updated);
        paintActivities();
        if (!busy) get<HTMLButtonElement>('[data-process]').disabled = data.jobs.some(item => item.state === 'processing');
        if (updated.state !== 'processing' && !terminal.has(updated.id)) {
          terminal.add(updated.id);
          void (async () => { try { await host.changed();
              if (updated.state !== 'completed' || !updated.result_key) return;
              const token = handoffs.get(updated.id); const autoOpen = token !== undefined && dialog.open
                && currentJob?.id === updated.id && token === host.interactionGeneration() && host.canAutoOpen();
              if (autoOpen) dialog.close(); host.completed(updated.result_key, autoOpen);
            } catch (reason) { fail(reason); }
          })();
        }
      }));
    }
  }
  async function open(id: string, label: string, incoming: File[] = [], layoutId?: string, action?: CapturePurpose,
    definition?: TagAlignmentDefinition) {
    if (busy) { if (!dialog.open) dialog.showModal(); return; }
    alignmentDefinition = definition ? structuredClone(definition) : undefined;
    group = id; queued = []; purpose.value = action ?? ''; error.textContent = ''; progressPanel.hidden = true;
    get<HTMLElement>('[data-group]').textContent = `Capture group: ${label}`;
    if (!dialog.open) dialog.showModal();
    setBusy(true);
    try {
      await refresh(); selected = new Set(data.captures.filter(item => item.group_id === id).map(item => item.id));
      layout.replaceChildren(new Option('Create new tag settings…', ''));
      for (const item of data.layouts) layout.add(new Option(`${item.name} · ${item.tag_size_mm} mm ${item.tag_family}`, item.id));
      const chosenLayout = layoutId ?? host.defaultLayout(id) ?? '';
      layout.value = chosenLayout;
      const missingLayout = !!chosenLayout && layout.selectedIndex < 0;
      layoutSelectionRequired = missingLayout;
      if (missingLayout) {
        const missing = new Option('Choose tag settings…', '', true, true); missing.disabled = true;
        layout.prepend(missing); layout.required = true;
      } else layout.required = false;
      layoutName.value = label; name.value = `${label} — ${action === 'preview' ? 'preview' : 'reconstruction'}`;
      layoutChanged(); purposeChanged();
      setBusy(false); addFiles(incoming);
      if (missingLayout) fail(new Error('The selected result’s tag settings are unavailable. Choose settings before processing.'));
      const job = data.jobs.find(item => item.group_id === id);
      currentJob = job; if (job) { showJob(job); void jobs.refresh(job.id); }
      (action ? files : purpose).focus();
    } catch (reason) { setBusy(false); fail(reason); }
  }
  form.onsubmit = event => { event.preventDefault(); void start(); };
  async function uploadQueued() {
    while (queued.length) {
      const file = queued[0]; stage.textContent = `Uploading ${file.name}…`; meter.max = 1; meter.value = 0;
      const imported = await uploadCapture(file, group, fraction => { meter.value = fraction; });
      if (!data.captures.some(item => item.id === imported.id)) data.captures.push(imported);
      selected.add(imported.id); queued.shift(); fileRows();
    }
  }
  upload.onclick = async () => {
    if (busy || !queued.length) return;
    setBusy(true); error.textContent = ''; progressPanel.hidden = false; jobView.element.hidden = true;
    stage.hidden = false; meter.hidden = false; view.hidden = true;
    try { await uploadQueued(); stage.textContent = 'Captures uploaded. Choose the inputs and action to process.'; await host.changed(); }
    catch (reason) { fail(reason); }
    finally { meter.hidden = true; setBusy(false); }
  };
  async function start() {
    if (busy) return;
    if (!purpose.value) { fail(new Error('Choose quick preview or detailed reconstruction before processing.')); purpose.focus(); return; }
    if (layoutSelectionRequired) { fail(new Error('Choose tag settings before processing.')); return; }
    if (data.jobs.some(job => job.state === 'processing')) { fail(new Error('A reconstruction is already running. Wait for it to finish.')); return; }
    if (!selected.size && !queued.length) { fail(new Error('Choose at least one capture input.')); return; }
    if (purpose.value === 'preview' && (selectedPhotos().length
      || queued.some(file => !file.name.toLowerCase().endsWith('.db')))) {
      fail(new Error('Quick preview accepts depth databases only. Upload queued photos separately, then uncheck them, or choose detailed reconstruction.')); return;
    }
    if (!name.value.trim() || (!layout.value && !layoutName.value.trim())) { fail(new Error('Enter a result and tag-settings name.')); return; }
    const resultName = name.value.trim(); const size = Number(tagSize.value);
    const action: CapturePurpose = purpose.value === 'preview' ? 'preview' : 'photographic';
    const processing: CaptureProcessing = action === 'preview'
      ? { purpose: 'preview', settings: { voxel_mm: Number(resolution.value),
        sdf_trunc_mm: Number(resolution.value) * 5, texture_mode: 'baked' } }
      : { purpose: 'photographic', settings: { num_threads: 4, target_triangles: 500000, texture_size: 4096 } };
    setBusy(true); error.textContent = ''; progressPanel.hidden = false; jobView.element.hidden = true; stage.hidden = false; meter.hidden = false; view.hidden = true;
    try {
      await uploadQueued();
      if (!layout.value) {
        const created = await createTagLayout(layoutName.value.trim(), size);
        data.layouts.push(created); layout.add(new Option(created.name, created.id)); layout.value = created.id; layoutChanged();
      }
      meter.removeAttribute('value'); stage.textContent = 'Starting reconstruction…';
      const job = await processCaptures({ group_id: group, capture_ids: [...selected], layout_id: layout.value,
        name: resultName, ...processing,
        ...(alignmentDefinition ? { alignment_definition: alignmentDefinition } : {}) });
      handoffs.set(job.id, host.interactionGeneration());
      jobs.publish(job); showJob(job); await refresh(); await host.changed();
    } catch (reason) { fail(reason); meter.hidden = true; }
    finally { setBusy(false); }
  }
  return {
    open, refresh,
    captures: () => data.captures,
    activity(id: string, label: string) {
      const node = document.createElement('div'); node.className = 'scan-import-activity';
      activities.add({ group: id, name: label, node });
      queueMicrotask(paintActivities); return node;
    },
    drop(event: DragEvent, id: string, label: string) {
      event.preventDefault(); if (event.dataTransfer?.files.length) void open(id, label, [...event.dataTransfer.files]);
    },
  };
}
