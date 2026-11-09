import { readScanJob, type ProcessingJob } from './scan-import-api';

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
    subscribe(id: string, listener: (job: ProcessingJob) => void) {
      const entry = entries.get(id); if (!entry) throw new Error('Publish the job before subscribing.');
      entry.listeners.add(listener); listener(entry.job); return () => entry.listeners.delete(listener);
    } };
}
export function createJobView(retry: () => void) {
  const element = document.createElement('section'); element.className = 'scan-job-status';
  const status = document.createElement('p'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  // No value means indeterminate progress, not an invented completion percentage.
  // https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/progress
  const progress = document.createElement('progress'); progress.hidden = true;
  progress.setAttribute('aria-label', 'Scan processing progress');
  const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Show processing log';
  const log = document.createElement('pre'); details.append(summary, log);
  const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Retry'; button.onclick = retry;
  element.append(status, progress, button, details);
  return { element,
    pending(message: string) { status.textContent = message; progress.hidden = false; progress.setAttribute('aria-label', message);
      element.setAttribute('aria-busy', 'true'); button.hidden = true; details.hidden = true; },
    update(job: ProcessingJob) { status.textContent = `${job.name} · ${job.stage}${job.error ? ` · ${job.error}` : ''}`;
    const working = job.state === 'processing' && !job.error;
    progress.hidden = !working; progress.setAttribute('aria-label', `${job.name} progress`);
    element.setAttribute('aria-busy', String(working)); details.hidden = false;
    log.textContent = job.log_tail ?? ''; button.hidden = !job.error && job.state !== 'failed' && job.state !== 'interrupted'; } };
}

export const jobStatus = createJobStatus();
