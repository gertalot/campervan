import type { Api, FieldMetadata, ModelStatus, ParameterResponse, Parameters } from './api';

export interface View {
  setMetadata(metadata: Record<string, FieldMetadata>): void;
  setParameters(parameters: Parameters, reset: boolean): void;
  setViewerUrl(url: string): Promise<void> | void;
  setStatus(status: ModelStatus): void;
  setError(message: string | null): void;
  setPosition(name: string, percent: number): void;
  setConstraints(metadata: Record<string, FieldMetadata>, errors: Record<string, string>,
    adjustments: Record<string, string>, parameters: Parameters): void;
}
export interface Clock {
  setTimeout(callback: () => void, delay: number): unknown;
  clearTimeout(handle: unknown): void;
}

export function createController(api: Api, view: View, clock: Clock, storage: Pick<Storage, 'getItem' | 'setItem'>) {
  let running = false;
  let polling = false;
  let timer: unknown;
  let session: string | null = null;
  let metadata: Record<string, FieldMetadata> | null = null;
  let current: ModelStatus | null = null;
  let inputError: string | null = null;
  let previewRevision = 0;
  const positionKey = 'campervan.positions';
  let positions: Parameters = JSON.parse(storage.getItem(positionKey) ?? '{}');
  delete positions.cross_bed_extension_percent;

  function setPosition(name: string, percent: number) {
    positions[name] = percent;
    storage.setItem(positionKey, JSON.stringify(positions));
    view.setPosition(name, percent);
  }

  function show(status: ModelStatus) {
    if (current && status.requested_revision < current.requested_revision) return;
    if (status.published_revision !== null && status.published_revision !== current?.published_revision) {
      for (const [name, value] of Object.entries(positions)) view.setPosition(name, value);
    }
    current = status;
    view.setStatus(status);
    const previous = status.published_revision !== null && status.published_revision !== status.requested_revision;
    view.setError(inputError ?? (status.error
      ? `Model update failed: ${status.error.message}${previous ? ' Showing the previous model.' : ''}` : null));
  }
  function schedule(delay = current?.state === 'regenerating' ? 500 : 2000) {
    clock.clearTimeout(timer);
    if (running && !polling) timer = clock.setTimeout(() => { void poll(); }, delay);
  }
  function showError(error: unknown) {
    view.setError(error instanceof Error ? error.message : String(error));
  }
  async function request(operation: () => Promise<ModelStatus>) {
    if (!running) return false;
    try {
      const accepted = await operation();
      if (!running) return false;
      inputError = null;
      if (accepted.session_id !== session) {
        // The next poll reloads parameters before displaying this session's revisions.
        session = null;
      } else {
        show(accepted);
      }
      schedule();
      return true;
    } catch (error) { showError(error); schedule(2000); return false; }
  }
  async function preview(raw: Record<string, string>): Promise<ParameterResponse | null> {
    const revision = ++previewRevision;
    if (!metadata) { view.setError('Parameters are unavailable.'); return null; }
    const parameters: Parameters = {};
    for (const [name, field] of Object.entries(metadata)) {
      const text = raw[name] ?? '';
      const value = Number(text);
      if (!text.trim() || !Number.isFinite(value)) {
        inputError = `${field.title}: enter a number.`;
        view.setConstraints(metadata, { [name]: inputError }, {}, parameters);
        view.setError(inputError);
        return null;
      }
      parameters[name] = value;
    }
    try {
      const data = await api.previewParameters(parameters);
      if (revision !== previewRevision || !running) return null;
      metadata = data.schema.properties;
      const errors = data.errors ?? {};
      inputError = Object.values(errors)[0] ?? null;
      view.setConstraints(metadata, errors, data.adjustments ?? {}, data.parameters);
      view.setError(inputError);
      return inputError ? null : data;
    } catch (error) {
      if (revision === previewRevision) {
        inputError = error instanceof Error ? error.message : String(error);
        view.setConstraints(metadata, { _form: inputError }, {}, parameters);
        view.setError(inputError);
      }
      return null;
    }
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
        if (!metadata) await view.setViewerUrl(data.viewer_url);
        metadata = data.schema.properties;
        current = null;
        inputError = null;
        view.setMetadata(metadata);
        positions = Object.fromEntries(Object.entries(data.parameters)
          .filter(([name]) => metadata![name]?.control === 'position')
          .map(([name, value]) => [name, positions[name] ?? value]));
        storage.setItem(positionKey, JSON.stringify(positions));
        for (const [name, value] of Object.entries(positions)) view.setPosition(name, value);
        view.setParameters({ ...data.parameters, ...positions }, true);
        await Promise.all(Object.entries(positions)
          .filter(([name, value]) => data.parameters[name] !== value)
          .map(([name, value]) => api.setPosition(name, value)));
        session = data.session_id;
        status = await api.loadModel();
        if (!running || status.session_id !== session) return;
        show(status);
        const draft = Object.fromEntries(Object.entries({ ...data.parameters, ...positions })
          .map(([name, value]) => [name, String(value)]));
        await preview(draft);
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
    async apply(raw: Record<string, string>) {
      const data = await preview(raw);
      if (data && await request(() => api.putParameters(data.parameters))) view.setParameters(data.parameters, true);
    },
    preview,
    async regenerate() {
      await request(() => api.regenerate());
      try { view.setParameters({ ...(await api.getParameters()).parameters, ...positions }, false); }
      catch (error) { showError(error); }
    },
    previewPosition: setPosition,
    async savePosition(name: string, percent: number) {
      setPosition(name, percent);
      try { await api.setPosition(name, percent); }
      catch (error) { showError(error); }
    },
    stop() { running = false; clock.clearTimeout(timer); },
  };
}
