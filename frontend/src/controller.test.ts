import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createController, type View } from './controller';
import { ApiError, getParameters, getStatus, putParameters, regenerate, type Api, type ModelStatus,
  type ParameterResponse } from './api';

const parameters = (session = 'first', size = 73): ParameterResponse => ({
  session_id: session, parameters: { size_mm: size }, viewer_url: 'http://127.0.0.1:3939',
  schema: { properties: { size_mm: { title: 'Edge length', default: 73, exclusiveMinimum: 2, maximum: 250, unit: 'mm' } } },
});
const status = (session = 'first', revision = 0, state: ModelStatus['state'] = 'idle'): ModelStatus => ({
  session_id: session, requested_revision: revision, published_revision: state === 'ready' ? revision : null,
  state, error: null,
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function setup() {
  const api = {
    getParameters: vi.fn<Api['getParameters']>().mockResolvedValue(parameters()),
    getStatus: vi.fn<Api['getStatus']>().mockResolvedValue(status()),
    putParameters: vi.fn<Api['putParameters']>().mockResolvedValue({ session_id: 'first', requested_revision: 2 }),
    regenerate: vi.fn<Api['regenerate']>().mockResolvedValue({ session_id: 'first', requested_revision: 1 }),
  };
  const view = {
    setMetadata: vi.fn<View['setMetadata']>(), setParameters: vi.fn<View['setParameters']>(),
    setViewerUrl: vi.fn<View['setViewerUrl']>(), setStatus: vi.fn<View['setStatus']>(),
    setError: vi.fn<View['setError']>(),
  };
  const controller = createController(api, view, {
    setTimeout: (callback, delay) => setTimeout(callback, delay),
    clearTimeout: (handle) => clearTimeout(handle as ReturnType<typeof setTimeout>),
  });
  return { api, view, controller };
}
beforeEach(() => vi.useFakeTimers());
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

describe('parameter and request behavior', () => {
  it('loads schema metadata, accepted parameters and viewer before initial regeneration', async () => {
    const { api, view, controller } = setup();
    api.regenerate.mockImplementation(async () => {
      expect(view.setViewerUrl).toHaveBeenCalledWith('http://127.0.0.1:3939');
      return { session_id: 'first', requested_revision: 1 };
    });
    await controller.start();
    expect(view.setMetadata).toHaveBeenCalledWith(parameters().schema.properties.size_mm);
    expect(view.setParameters).toHaveBeenCalledWith({ size_mm: 73 }, true);
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ state: 'regenerating', requested_revision: 1 }));
  });

  it('Apply sends exactly one numeric PUT; Regenerate explicitly sends POST', async () => {
    const { api, controller } = setup();
    await controller.start();
    api.regenerate.mockClear();
    await controller.apply('125.5');
    expect(api.putParameters).toHaveBeenCalledExactlyOnceWith({ size_mm: 125.5 });
    expect(api.regenerate).not.toHaveBeenCalled();
    await controller.regenerate();
    expect(api.regenerate).toHaveBeenCalledTimes(1);
  });

  it.each(['', ' ', '2', '0', '-4', '251', 'NaN', 'Infinity', 'abc'])('rejects invalid input %j using schema bounds', async raw => {
    const { api, view, controller } = setup();
    await controller.start();
    api.regenerate.mockClear();
    await controller.apply(raw);
    expect(api.putParameters).not.toHaveBeenCalled();
    expect(api.regenerate).not.toHaveBeenCalled();
    expect(view.setError).toHaveBeenLastCalledWith(expect.stringMatching(/Edge length/));
  });

  it('allows the inclusive maximum and shows backend field diagnostics', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    api.putParameters.mockRejectedValue(new ApiError(422, 'size_mm: must be a valid number'));
    await controller.apply('250');
    expect(api.putParameters).toHaveBeenCalledWith({ size_mm: 250 });
    expect(view.setError).toHaveBeenLastCalledWith('size_mm: must be a valid number');
  });

  it('keeps invalid input feedback visible across ordinary polls', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    api.getStatus.mockResolvedValue(status('first', 1, 'ready'));
    await controller.apply('');
    await vi.advanceTimersByTimeAsync(500);
    expect(view.setError).toHaveBeenLastCalledWith(expect.stringMatching(/Edge length/));
  });

  it('keeps controls accepting newer edits while a mutation is pending and ignores older status', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    const earlier = deferred<{session_id: string; requested_revision: number}>();
    api.putParameters.mockReturnValueOnce(earlier.promise)
      .mockResolvedValueOnce({ session_id: 'first', requested_revision: 3 });
    const first = controller.apply('90');
    await controller.apply('95');
    earlier.resolve({ session_id: 'first', requested_revision: 2 });
    await first;
    api.getStatus.mockResolvedValue(status('first', 1, 'ready'));
    await vi.advanceTimersByTimeAsync(500);
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ requested_revision: 3 }));
    expect(api.putParameters).toHaveBeenCalledTimes(2);
  });
});

describe('polling and recovery', () => {
  it('polls sequentially every 500ms while active and every 2000ms when idle', async () => {
    const { api, controller } = setup();
    await controller.start();
    const pending = deferred<ModelStatus>();
    api.getStatus.mockReturnValueOnce(pending.promise);
    await vi.advanceTimersByTimeAsync(500);
    expect(api.getStatus).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(5000);
    expect(api.getStatus).toHaveBeenCalledTimes(2);
    pending.resolve(status('first', 1, 'ready'));
    await vi.advanceTimersByTimeAsync(0);
    await vi.advanceTimersByTimeAsync(1999);
    expect(api.getStatus).toHaveBeenCalledTimes(2);
    api.getStatus.mockResolvedValue(status('first', 1, 'ready'));
    await vi.advanceTimersByTimeAsync(1);
    expect(api.getStatus).toHaveBeenCalledTimes(3);
    controller.stop();
    await vi.advanceTimersByTimeAsync(5000);
    expect(api.getStatus).toHaveBeenCalledTimes(3);
  });

  it('ordinary polls leave edited input alone by never resetting parameters', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    api.getStatus.mockResolvedValue(status('first', 1, 'ready'));
    await vi.advanceTimersByTimeAsync(6500);
    expect(view.setParameters).toHaveBeenCalledTimes(1);
  });

  it('shows publication failure without replacing the viewer and retries explicitly', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    api.getStatus.mockResolvedValue({ ...status('first', 1, 'failed'), error: { stage: 'publication', message: 'Viewer absent' } });
    await vi.advanceTimersByTimeAsync(500);
    expect(view.setError).toHaveBeenLastCalledWith('Publication failed: Viewer absent');
    expect(view.setViewerUrl).toHaveBeenCalledTimes(1);
    await controller.regenerate();
    expect(api.regenerate).toHaveBeenCalledTimes(2);
  });

  it('recovers a same-session outage by refreshing metadata without another automatic request', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    api.getStatus.mockRejectedValueOnce(new TypeError('offline'));
    await vi.advanceTimersByTimeAsync(500);
    expect(view.setError).toHaveBeenLastCalledWith(expect.stringMatching(/API unavailable/));
    api.getStatus.mockResolvedValue(status('first', 1, 'ready'));
    await vi.advanceTimersByTimeAsync(2000);
    expect(api.getParameters).toHaveBeenCalledTimes(2);
    expect(view.setParameters).toHaveBeenLastCalledWith({ size_mm: 73 }, false);
    expect(api.regenerate).toHaveBeenCalledTimes(1);
    expect(view.setViewerUrl).toHaveBeenCalledTimes(1);
    expect(view.setError).toHaveBeenLastCalledWith(null);
  });

  it('resets accepted parameters and revisions once per new session', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    api.putParameters.mockResolvedValue({ session_id: 'first', requested_revision: 50 });
    await controller.apply('150');
    api.getParameters.mockResolvedValue(parameters('second', 73));
    api.getStatus.mockResolvedValue(status('second'));
    api.regenerate.mockResolvedValue({ session_id: 'second', requested_revision: 1 });
    await vi.advanceTimersByTimeAsync(500);
    expect(view.setParameters).toHaveBeenLastCalledWith({ size_mm: 73 }, true);
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second', requested_revision: 1 }));
    api.getStatus.mockResolvedValue(status('second', 1, 'ready'));
    await vi.advanceTimersByTimeAsync(4500);
    expect(api.regenerate).toHaveBeenCalledTimes(2);
    expect(view.setViewerUrl).toHaveBeenCalledTimes(1);
  });

  it('follows an already outstanding new-session request', async () => {
    const { api, controller } = setup();
    api.getStatus.mockResolvedValue(status('first', 4, 'regenerating'));
    await controller.start();
    expect(api.regenerate).not.toHaveBeenCalled();
  });

  it('follows an Apply accepted while the initialization status response is in flight', async () => {
    const { api, controller } = setup();
    const initialStatus = deferred<ModelStatus>();
    api.getStatus.mockReturnValueOnce(initialStatus.promise);
    const initial = controller.start();
    await vi.advanceTimersByTimeAsync(0);
    await controller.apply('80');
    initialStatus.resolve(status());
    await initial;
    expect(api.regenerate).not.toHaveBeenCalled();
  });

  it('does not repeat a failed initialization mutation on idle polls', async () => {
    const { api, view, controller } = setup();
    api.regenerate.mockRejectedValue(new Error('request failed'));
    await controller.start();
    expect(view.setError).toHaveBeenLastCalledWith(expect.stringMatching(/request failed/));
    await vi.advanceTimersByTimeAsync(6000);
    expect(api.regenerate).toHaveBeenCalledTimes(1);
    api.regenerate.mockResolvedValue({ session_id: 'first', requested_revision: 1 });
    await controller.regenerate();
    expect(api.regenerate).toHaveBeenCalledTimes(2);
  });

  it('refreshes before acting on a mutation from a new session and rejects an obsolete poll', async () => {
    const { api, view, controller } = setup();
    await controller.start();
    const oldPoll = deferred<ModelStatus>();
    api.getStatus.mockReturnValueOnce(oldPoll.promise);
    await vi.advanceTimersByTimeAsync(500);
    api.getParameters.mockResolvedValue(parameters('second'));
    api.getStatus.mockResolvedValue(status('second', 1, 'regenerating'));
    api.putParameters.mockResolvedValue({ session_id: 'second', requested_revision: 1 });
    await controller.apply('80');
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second' }));
    oldPoll.resolve(status('first', 99, 'ready'));
    await vi.advanceTimersByTimeAsync(0);
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second' }));
    expect(api.regenerate).toHaveBeenCalledTimes(1);
  });

  it('discards an obsolete initialization after stop and restart', async () => {
    const { api, view, controller } = setup();
    const oldMetadata = deferred<ParameterResponse>();
    api.getParameters.mockReturnValueOnce(oldMetadata.promise);
    const first = controller.start();
    controller.stop();
    api.getParameters.mockResolvedValue(parameters('second'));
    api.getStatus.mockResolvedValue(status('second', 1, 'regenerating'));
    await controller.start();
    oldMetadata.resolve(parameters('first'));
    await first;
    expect(view.setParameters).toHaveBeenCalledTimes(1);
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second' }));
  });

  it('invalidates an in-flight initialization when a mutation discovers recovery', async () => {
    const { api, view, controller } = setup();
    const oldStatus = deferred<ModelStatus>();
    api.getStatus.mockReturnValueOnce(oldStatus.promise);
    const initial = controller.start();
    await vi.advanceTimersByTimeAsync(0);
    api.putParameters.mockResolvedValue({ session_id: 'second', requested_revision: 1 });
    api.getParameters.mockResolvedValue(parameters('second'));
    api.getStatus.mockResolvedValue(status('second', 1, 'regenerating'));
    await controller.apply('80');
    oldStatus.resolve(status('first', 99, 'ready'));
    await initial;
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second' }));
    expect(api.regenerate).not.toHaveBeenCalled();
  });

  it('reinitializes if the automatic regeneration response belongs to a newer session', async () => {
    const { api, view, controller } = setup();
    api.regenerate.mockImplementation(async () => {
      api.getParameters.mockResolvedValue(parameters('second'));
      api.getStatus.mockResolvedValue(status('second', 1, 'regenerating'));
      return { session_id: 'second', requested_revision: 1 };
    });
    await controller.start();
    expect(view.setParameters).toHaveBeenLastCalledWith({ size_mm: 73 }, true);
    expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second' }));
    expect(api.regenerate).toHaveBeenCalledTimes(1);
  });
});

describe('HTTP boundary', () => {
  it('uses the four versioned routes and sends numeric JSON only for Apply', async () => {
    const requests: { url: string; method: string; body?: BodyInit | null; contentType: string | null }[] = [];
    vi.stubGlobal('fetch', async (url: string, options: RequestInit) => {
      requests.push({ url, method: options.method!, body: options.body,
        contentType: new Headers(options.headers).get('Content-Type') });
      const result = url.endsWith('/status') ? status()
        : options.method === 'GET' ? parameters() : { session_id: 'first', requested_revision: 1 };
      return new Response(JSON.stringify(result), { status: options.method === 'GET' ? 200 : 202 });
    });
    expect(await getParameters()).toEqual(parameters());
    expect(await getStatus()).toEqual(status());
    expect(await putParameters({ size_mm: 150 })).toEqual({ session_id: 'first', requested_revision: 1 });
    await regenerate();
    expect(requests).toEqual([
      { url: '/api/v1/parameters', method: 'GET', body: undefined, contentType: null },
      { url: '/api/v1/model/status', method: 'GET', body: undefined, contentType: null },
      { url: '/api/v1/parameters', method: 'PUT', body: '{"size_mm":150}', contentType: 'application/json' },
      { url: '/api/v1/model/regenerate', method: 'POST', body: undefined, contentType: null },
    ]);
  });

  it('retains field-level 422 diagnostics and handles non-JSON failures', async () => {
    vi.stubGlobal('fetch', async () => new Response(JSON.stringify({ detail: [
      { loc: ['body', 'size_mm'], msg: 'Input should be greater than 0' },
    ] }), { status: 422 }));
    await expect(putParameters({ size_mm: 0 })).rejects.toMatchObject({
      status: 422, message: 'size_mm: Input should be greater than 0',
    });
    vi.stubGlobal('fetch', async () => new Response('Bad gateway', { status: 502 }));
    await expect(getStatus()).rejects.toMatchObject({ status: 502, message: 'API request failed (502)' });
  });
});
