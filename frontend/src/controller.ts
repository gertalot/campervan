import { ApiError } from './api';
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
  let generation = 0;
  let timer: unknown;
  let pollingGeneration: number | null = null;
  let initialization: Promise<void> | null = null;
  let initializingSession: string | null = null;
  let session: string | null = null;
  let metadata: SizeMetadata | null = null;
  let current: ModelStatus | null = null;
  let unavailable = false;
  let viewerInitialized = false;
  let requestError: string | null = null;
  const sessions = new Set<string>();
  const initializedSessions = new Set<string>();
  const valid = (token: number) => running && token === generation;

  function renderStatus(next: ModelStatus) {
    // Only compare revisions after the session has been established by metadata.
    if (current && next.requested_revision < current.requested_revision) return;
    current = next;
    view.setStatus(next);
    const error = next.error;
    view.setError(error
      ? `${error.stage === 'publication' ? 'Publication' : 'Generation'} failed: ${error.message}`
      : requestError);
  }

  function fail(error: unknown) {
    requestError = error instanceof Error ? error.message : 'Request failed';
    if (!(error instanceof ApiError) || error.status >= 500) {
      unavailable = true;
      requestError = `API unavailable: ${requestError}. Retrying connection…`;
    }
    view.setError(requestError);
  }

  function schedule() {
    clock.clearTimeout(timer);
    if (!running || initialization || pollingGeneration === generation) return;
    timer = clock.setTimeout(() => { void poll(); },
      !unavailable && current?.state === 'regenerating' ? 500 : 2000);
  }

  async function accept(response: MutationResponse, token: number) {
    if (!valid(token)) return;
    if (response.session_id !== session) {
      if (!sessions.has(response.session_id)) await beginInitialization(response.session_id);
      return;
    }
    requestError = null;
    renderStatus({
      ...response, published_revision: current?.published_revision ?? null, state: 'regenerating', error: null,
    });
  }

  async function initialize(token: number) {
    // A restart between these two GETs needs a fresh matching pair before acting.
    while (valid(token)) {
      const data = await api.getParameters();
      if (!valid(token)) return;
      if (data.session_id !== session && sessions.has(data.session_id)) return;
      const changed = session !== data.session_id;
      session = data.session_id;
      sessions.add(session);
      if (changed) current = null;
      metadata = data.schema.properties.size_mm;
      view.setMetadata(metadata);
      view.setParameters(data.parameters, changed);
      if (!viewerInitialized) {
        view.setViewerUrl(data.viewer_url);
        viewerInitialized = true;
      }
      const state = await api.getStatus();
      if (!valid(token)) return;
      if (state.session_id !== session) {
        if (sessions.has(state.session_id)) return;
        continue;
      }
      unavailable = false;
      requestError = null;
      renderStatus(state);
      if (!initializedSessions.has(session)) {
        // Record the attempt before POST: failure must not cause an idle-poll POST loop.
        initializedSessions.add(session);
        if (current?.state !== 'regenerating') {
          const accepted = await api.regenerate();
          if (!valid(token)) return;
          if (accepted.session_id !== session) {
            if (sessions.has(accepted.session_id)) return;
            continue;
          }
          await accept(accepted, token);
        }
      }
      return;
    }
  }

  function beginInitialization(targetSession: string | null = null): Promise<void> {
    if (initialization && (!targetSession || targetSession === initializingSession)) return initialization;
    clock.clearTimeout(timer);
    const token = ++generation;
    initializingSession = targetSession;
    const operation = initialize(token).catch(error => {
      if (valid(token)) fail(error);
    }).finally(() => {
      if (valid(token)) {
        initialization = null;
        initializingSession = null;
        schedule();
      }
    });
    initialization = operation;
    return operation;
  }

  async function poll() {
    const token = generation;
    if (!valid(token)) return;
    if (unavailable) { await beginInitialization(); return; }
    pollingGeneration = token;
    try {
      const state = await api.getStatus();
      if (!valid(token)) return;
      if (state.session_id === session) renderStatus(state);
      else if (!sessions.has(state.session_id)) await beginInitialization(state.session_id);
    } catch (error) {
      if (valid(token)) fail(error);
    } finally {
      if (pollingGeneration === token) pollingGeneration = null;
      if (valid(token)) schedule();
    }
  }

  async function mutate(operation: () => Promise<MutationResponse>) {
    if (!running) return;
    const token = generation;
    try { await accept(await operation(), token); }
    catch (error) { if (valid(token)) fail(error); }
    finally { if (valid(token)) schedule(); }
  }

  return {
    async start() {
      if (running) { await initialization; return; }
      running = true;
      await beginInitialization();
    },
    async apply(raw: string) {
      if (!metadata) { view.setError('Parameters are unavailable. Reconnect before applying an edit.'); return; }
      const value = Number(raw);
      const invalid = !raw.trim() || !Number.isFinite(value)
        || (metadata.minimum !== undefined && value < metadata.minimum)
        || (metadata.exclusiveMinimum !== undefined && value <= metadata.exclusiveMinimum)
        || (metadata.maximum !== undefined && value > metadata.maximum)
        || (metadata.exclusiveMaximum !== undefined && value >= metadata.exclusiveMaximum);
      if (invalid) {
        requestError = `${metadata.title}: enter a finite number within the displayed bounds.`;
        view.setError(requestError);
        return;
      }
      await mutate(() => api.putParameters({ size_mm: value }));
    },
    async regenerate() {
      await mutate(() => api.regenerate());
    },
    stop() {
      running = false;
      generation++;
      initialization = null;
      clock.clearTimeout(timer);
    },
  };
}
