import { cancelScanJob, readScanJob, type ProcessingJob } from './scan-import-api';

/** One keyed polling owner can serve multiple views of the same processing job. */
export function createJobStatus() {
  const entries = new Map<string, { job: ProcessingJob; listeners: Set<(job: ProcessingJob) => void>;
    timer?: ReturnType<typeof setTimeout>; generation: number }>();
  function publish(job: ProcessingJob) {
    let entry = entries.get(job.id);
    if (!entry) { entry = { job, listeners: new Set(), generation: 0 }; entries.set(job.id, entry); }
    else if (entry.job.state !== 'processing' && job.state === 'processing') return;
    entry.generation++; entry.job = job; entry.listeners.forEach(listener => listener(job));
    if (entry.timer) clearTimeout(entry.timer);
    entry.timer = job.state === 'processing' ? setTimeout(() => { void refresh(job.id); }, 2000) : undefined;
  }
  async function refresh(id: string) {
    const entry = entries.get(id); if (!entry) return;
    if (entry.timer) clearTimeout(entry.timer); entry.timer = undefined;
    const generation = ++entry.generation;
    try { const job = await readScanJob(id); if (entry.generation === generation) publish(job); }
    catch (reason) { if (entry.generation === generation) { entry.timer = undefined;
      entry.listeners.forEach(listener => listener({ ...entry.job, error: `Status unavailable: ${String(reason)}` })); } }
  }
  return { publish, refresh,
    async cancel(id: string) { publish(await cancelScanJob(id)); },
    subscribe(id: string, listener: (job: ProcessingJob) => void) {
      const entry = entries.get(id); if (!entry) throw new Error('Publish the job before subscribing.');
      entry.listeners.add(listener); listener(entry.job); return () => entry.listeners.delete(listener);
    } };
}
export function createJobView(retry: () => void, retryLabel = 'Retry') {
  let current: ProcessingJob | null = null; let cancelling: string | null = null;
  const element = document.createElement('section'); element.className = 'scan-job-status';
  const status = document.createElement('p'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const error = document.createElement('p'); error.setAttribute('role', 'alert'); error.hidden = true;
  // No value means indeterminate progress, not an invented completion percentage.
  // https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/progress
  const progress = document.createElement('progress'); progress.hidden = true;
  progress.setAttribute('aria-label', 'Scan processing progress');
  const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Show processing log';
  const inputs = document.createElement('p');
  const settings = document.createElement('pre');
  const log = document.createElement('pre'); details.append(summary, inputs, settings, log);
  const button = document.createElement('button'); button.type = 'button'; button.textContent = retryLabel; button.onclick = retry;
  const cancel = document.createElement('button'); cancel.type = 'button'; cancel.textContent = 'Cancel'; cancel.hidden = true;
  cancel.onclick = () => { const job = current; if (!job || job.state !== 'processing' || cancelling) return;
    cancelling = job.id; cancel.disabled = true; cancel.textContent = 'Cancelling…';
    void jobStatus.cancel(job.id).catch(reason => {
      if (current?.id === job.id) status.textContent = `Could not cancel: ${String(reason)}`;
    }).finally(() => { cancelling = null; cancel.disabled = false; cancel.textContent = 'Cancel'; }); };
  element.append(status, error, progress, cancel, button, details);
  return { element,
    pending(message: string) { status.textContent = message; progress.hidden = false; progress.setAttribute('aria-label', message);
      current = null; cancel.hidden = true; error.hidden = true;
      element.setAttribute('aria-busy', 'true'); button.hidden = true; details.hidden = true; },
    update(job: ProcessingJob) { current = job;
    status.textContent = `${job.name} · ${job.stage}`;
    error.textContent = job.error ?? ''; error.hidden = !job.error;
    inputs.textContent = job.request
      ? `${job.request.purpose === 'preview' ? 'Quick preview' : 'Photographic reconstruction'} inputs: ${job.request.inputs.map(input => `${input.filename} (${input.kind}, ${input.capture_id})`).join(', ')}`
      : 'Recorded inputs and settings: Unknown';
    settings.textContent = job.request ? JSON.stringify(job.request.settings, null, 2) : '';
    const working = job.state === 'processing' && !job.error;
    progress.hidden = !working; progress.setAttribute('aria-label', `${job.name} progress`);
    if (working && job.progress_percent !== undefined) { progress.max = 100; progress.value = job.progress_percent; }
    else progress.removeAttribute('value');
    element.setAttribute('aria-busy', String(working)); details.hidden = false;
    cancel.hidden = job.state !== 'processing'; cancel.disabled = cancelling === job.id;
    cancel.textContent = cancelling === job.id ? 'Cancelling…' : 'Cancel';
    log.textContent = job.log_tail ?? ''; button.hidden = !job.error && job.state !== 'failed' && job.state !== 'interrupted'; } };
}

export const jobStatus = createJobStatus();
