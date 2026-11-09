import { readScanJob, type ProcessingJob } from './scan-import-api';

/** One keyed polling owner can serve multiple views of the same processing job. */
export function createJobStatus() {
  const entries = new Map<string, { job: ProcessingJob; listeners: Set<(job: ProcessingJob) => void>; timer?: ReturnType<typeof setTimeout> }>();
  function publish(job: ProcessingJob) {
    let entry = entries.get(job.id);
    if (!entry) { entry = { job, listeners: new Set() }; entries.set(job.id, entry); }
    entry.job = job; entry.listeners.forEach(listener => listener(job));
    if (entry.timer) clearTimeout(entry.timer);
    entry.timer = job.state === 'processing' ? setTimeout(() => { void refresh(job.id); }, 2000) : undefined;
  }
  async function refresh(id: string) {
    try { publish(await readScanJob(id)); }
    catch (reason) { const entry = entries.get(id); if (entry) { entry.timer = undefined;
      entry.listeners.forEach(listener => listener({ ...entry.job, error: `Status unavailable: ${String(reason)}` })); } }
  }
  return { publish, refresh,
    subscribe(id: string, listener: (job: ProcessingJob) => void) {
      const entry = entries.get(id); if (!entry) throw new Error('Publish the job before subscribing.');
      entry.listeners.add(listener); listener(entry.job); return () => entry.listeners.delete(listener);
    } };
}
export function createJobView(retry: () => void) {
  const element = document.createElement('section');
  const status = document.createElement('p'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Show processing log';
  const log = document.createElement('pre'); details.append(summary, log);
  const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Retry'; button.onclick = retry;
  element.append(status, button, details);
  return { element, update(job: ProcessingJob) { status.textContent = `${job.name} · ${job.stage}${job.error ? ` · ${job.error}` : ''}`;
    log.textContent = job.log_tail ?? ''; button.hidden = !job.error && job.state !== 'failed' && job.state !== 'interrupted'; } };
}

export const jobStatus = createJobStatus();
