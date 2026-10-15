import type { Api, ModelStatus, MutationResponse, Parameters, SizeMetadata } from './api';

export interface View {
  setMetadata(metadata: SizeMetadata): void;
  setParameters(parameters: Parameters, reset: boolean): void;
  setViewerUrl(url: string): void;
  setStatus(status: ModelStatus): void;
  setError(message: string | null): void;
}
export interface Clock {
  setTimeout(callback: () => void, delay: number): unknown;
  clearTimeout(handle: unknown): void;
}

export function createController(api: Api, view: View, clock: Clock) {
  let running = false;
  let polling = false;
  let timer: unknown;
  let session: string | null = null;
  let metadata: SizeMetadata | null = null;
  let current: ModelStatus | null = null;
  let inputError: string | null = null;

  function show(status: ModelStatus) {
    if (current && status.requested_revision < current.requested_revision) return;
    current = status;
    view.setStatus(status);
    view.setError(status.error ? `Regeneration failed: ${status.error.message}` : inputError);
  }
  function schedule(delay = current?.state === 'regenerating' ? 500 : 2000) {
    clock.clearTimeout(timer);
    if (running && !polling) timer = clock.setTimeout(() => { void poll(); }, delay);
  }
  function showError(error: unknown) {
    view.setError(error instanceof Error ? error.message : String(error));
  }
  async function request(operation: () => Promise<MutationResponse>) {
    if (!running) return;
    try {
      const accepted = await operation();
      if (!running) return;
      inputError = null;
      if (accepted.session_id !== session) {
        // The next poll reloads parameters before displaying this session's revisions.
        session = null;
      } else {
        show({ ...accepted, published_revision: current?.published_revision ?? null,
          state: 'regenerating', error: null });
      }
      schedule();
    } catch (error) { showError(error); schedule(2000); }
  }
  async function poll() {
    if (!running || polling) return;
    polling = true;
    let failed = false;
    try {
      let status = await api.getStatus();
      if (!running) return;
      if (status.session_id !== session) {
        const data = await api.getParameters();
        if (!running) return;
        if (!metadata) view.setViewerUrl(data.viewer_url);
        session = data.session_id;
        metadata = data.schema.properties.size_mm;
        current = null;
        inputError = null;
        view.setMetadata(metadata);
        view.setParameters(data.parameters, true);
        status = await api.getStatus();
        if (!running || status.session_id !== session) return;
        show(status);
        if (status.state !== 'regenerating') await request(() => api.regenerate());
      } else show(status);
    } catch (error) { failed = true; showError(error); }
    finally {
      polling = false;
      schedule(failed ? 2000 : undefined);
    }
  }
  return {
    async start() {
      if (running) return;
      running = true;
      await poll();
    },
    async apply(raw: string) {
      if (!metadata) { view.setError('Parameters are unavailable.'); return; }
      const value = Number(raw);
      const invalid = !raw.trim() || !Number.isFinite(value)
        || (metadata.minimum !== undefined && value < metadata.minimum)
        || (metadata.exclusiveMinimum !== undefined && value <= metadata.exclusiveMinimum)
        || (metadata.maximum !== undefined && value > metadata.maximum)
        || (metadata.exclusiveMaximum !== undefined && value >= metadata.exclusiveMaximum);
      if (invalid) {
        inputError = `${metadata.title}: enter a number within the displayed bounds.`;
        view.setError(inputError);
        return;
      }
      await request(() => api.putParameters({ size_mm: value }));
    },
    async regenerate() { await request(() => api.regenerate()); },
    stop() { running = false; clock.clearTimeout(timer); },
  };
}
