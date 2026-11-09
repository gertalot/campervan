/** Group-level database import, explicit tag setup and progress over the existing reconstruction CLI. */
import { createTagLayout, processCaptures, readScanImports, uploadCapture,
  type ScanImports, type ProcessingJob } from './scan-import-api';
import { jobStatus, createJobView } from './scan-job-status';
import { createWorkflow } from './scan-workflow-api';
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
  dialog.innerHTML = `<header><h2 id="scan-import-title">Add capture databases</h2><button type="button" data-close>Close</button></header>
    <p data-group></p>
    <form>
      <fieldset><legend>Capture databases</legend>
        <label class="scan-import-drop">Choose .db files or drop them here
          <input type="file" multiple accept=".db" aria-label="Choose RTAB-Map capture databases" /></label>
        <div data-files></div>
      </fieldset>
      <fieldset><legend>Tags and reconstruction</legend>
        <label>Tag layout <select data-layout></select></label>
        <p>Reuse a layout only while every tag stays in the same position. New or moved tags need a new layout.</p>
        <div data-new-layout>
          <label>New layout name <input data-layout-name required maxlength="120" /></label>
          <label>Tag family <select data-family><option value="36h11">AprilTag 36h11</option></select></label>
          <label>Printed tag size <input data-tag-size type="number" min="0.1" step="any" value="80" required /> mm</label>
          <p>Measure the tag's black outer square, excluding the paper margin. A new layout starts with no distances or axis roles.</p>
        </div>
        <label>Result name <input data-name required maxlength="120" /></label>
        <label>Surface detail <select data-resolution><option value="5">5 mm</option><option value="10">10 mm</option></select></label>
        <label><input type="checkbox" data-photo /> Add photographic texture (slower)</label>
        <p>Builds a surface with colour texture. After processing, review the capture and use measured distances to preview corrections and update the mesh.</p>
      </fieldset>
      <button type="submit" data-process>Process captures</button>
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
  const resolution = get<HTMLSelectElement>('[data-resolution]'); const photo = get<HTMLInputElement>('[data-photo]');
  const error = get<HTMLParagraphElement>('[data-error]'); const progressPanel = get<HTMLElement>('[data-progress]');
  const stage = get<HTMLElement>('[data-stage]'); const meter = get<HTMLProgressElement>('progress');
  const view = get<HTMLButtonElement>('[data-view]');
  let data: ScanImports = { captures: [], layouts: [], jobs: [] };
  let group = ''; let queued: File[] = []; let selected = new Set<string>();
  let busy = false; let currentJob: ProcessingJob | undefined;
  const handoffs = new Map<string, number>();
  const jobs = jobStatus;
  const subscriptions = new Map<string, () => void>();
  const jobView = createJobView(() => { if (currentJob?.state === 'processing') void jobs.refresh(currentJob.id); else void start(); });
  progressPanel.append(jobView.element); jobView.element.hidden = true;
  const terminal = new Set<string>();
  const activities = new Set<{ group: string; name: string; node: HTMLElement }>();
  function fail(reason: unknown) { error.textContent = reason instanceof Error ? reason.message : String(reason); }
  function layoutChanged() {
    newLayout.hidden = !!layout.value;
    for (const input of newLayout.querySelectorAll<HTMLInputElement | HTMLSelectElement>('input,select')) input.disabled = !!layout.value;
  }
  layout.onchange = layoutChanged;
  function fileRows() {
    fileList.replaceChildren();
    for (const capture of data.captures.filter(item => item.group_id === group)) {
      const label = document.createElement('label'); const checkbox = document.createElement('input'); checkbox.type = 'checkbox';
      checkbox.checked = selected.has(capture.id); checkbox.disabled = busy;
      checkbox.onchange = () => { if (checkbox.checked) selected.add(capture.id); else selected.delete(capture.id); };
      label.append(checkbox, `${capture.filename} · ${capture.frames} frames · already imported`); fileList.append(label);
    }
    for (const file of queued) {
      const row = document.createElement('div'); row.className = 'scan-import-file';
      const label = document.createElement('span'); label.textContent = `${file.name} · ${(file.size / 1048576).toFixed(1)} MB`;
      const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove'; remove.disabled = busy;
      remove.setAttribute('aria-label', `Remove ${file.name} from this import`);
      remove.onclick = () => { queued = queued.filter(item => item !== file); fileRows(); }; row.append(label, remove); fileList.append(row);
    }
    if (!queued.length && !data.captures.some(item => item.group_id === group)) fileList.textContent = 'No databases selected.';
  }
  function addFiles(incoming: File[]) {
    if (busy) return;
    const invalid = incoming.find(file => !file.name.toLowerCase().endsWith('.db'));
    if (invalid) { fail(new Error(`${invalid.name} is not an RTAB-Map .db file.`)); return; }
    for (const file of incoming) {
      if (!queued.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) queued.push(file);
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
              await createWorkflow(updated.run_id, updated.layout_id);
              const token = handoffs.get(updated.id); const autoOpen = token !== undefined && dialog.open
                && currentJob?.id === updated.id && token === host.interactionGeneration() && host.canAutoOpen();
              if (autoOpen) dialog.close(); host.completed(updated.result_key, autoOpen);
            } catch (reason) { fail(reason); }
          })();
        }
      }));
    }
  }
  async function open(id: string, label: string, incoming: File[] = []) {
    if (busy) { if (!dialog.open) dialog.showModal(); return; }
    group = id; queued = []; error.textContent = ''; progressPanel.hidden = true;
    get<HTMLElement>('[data-group]').textContent = `Capture group: ${label}`;
    if (!dialog.open) dialog.showModal();
    setBusy(true);
    try {
      await refresh(); selected = new Set(data.captures.filter(item => item.group_id === id).map(item => item.id));
      layout.replaceChildren(new Option('Create new tag layout…', ''));
      for (const item of data.layouts) layout.add(new Option(`${item.name} · ${item.tag_size_mm} mm ${item.tag_family}`, item.id));
      layout.value = host.defaultLayout(id) ?? ''; if (layout.selectedIndex < 0) layout.selectedIndex = 0;
      layoutName.value = label; name.value = `${label} — reconstruction`; layoutChanged();
      setBusy(false); addFiles(incoming);
      const job = data.jobs.find(item => item.group_id === id);
      currentJob = job; if (job) { showJob(job); void jobs.refresh(job.id); }
      files.focus();
    } catch (reason) { setBusy(false); fail(reason); }
  }
  form.onsubmit = event => { event.preventDefault(); void start(); };
  async function start() {
    if (busy) return;
    if (data.jobs.some(job => job.state === 'processing')) { fail(new Error('A reconstruction is already running. Wait for it to finish.')); return; }
    if (!selected.size && !queued.length) { fail(new Error('Choose at least one capture database.')); return; }
    if (!name.value.trim() || (!layout.value && !layoutName.value.trim())) { fail(new Error('Enter a result and tag-layout name.')); return; }
    const resultName = name.value.trim(); const size = Number(tagSize.value);
    const settings = { voxel_mm: Number(resolution.value), sdf_trunc_mm: Number(resolution.value) * 5,
      texture_mode: photo.checked ? 'photo' : 'baked' };
    setBusy(true); error.textContent = ''; progressPanel.hidden = false; jobView.element.hidden = true; stage.hidden = false; meter.hidden = false; view.hidden = true;
    try {
      while (queued.length) {
        const file = queued[0]; stage.textContent = `Uploading ${file.name}…`; meter.max = 1; meter.value = 0;
        const imported = await uploadCapture(file, group, fraction => { meter.value = fraction; });
        if (!data.captures.some(item => item.id === imported.id)) data.captures.push(imported);
        selected.add(imported.id); queued.shift(); fileRows();
      }
      if (!layout.value) {
        const created = await createTagLayout(layoutName.value.trim(), size);
        data.layouts.push(created); layout.add(new Option(created.name, created.id)); layout.value = created.id; layoutChanged();
      }
      meter.removeAttribute('value'); stage.textContent = 'Starting reconstruction…';
      const job = await processCaptures({ group_id: group, capture_ids: [...selected], layout_id: layout.value,
        name: resultName, settings });
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
