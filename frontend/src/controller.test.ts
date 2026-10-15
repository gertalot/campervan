import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { createController, type View } from './controller';
import type { Api, ModelStatus, ParameterResponse } from './api';

function setup() {
  const parameters: ParameterResponse = {
    session_id: 'first', parameters: { size_mm: 100 }, viewer_url: 'http://127.0.0.1:3939/viewer',
    schema: { properties: { size_mm: {
      title: 'Cube size', default: 100, exclusiveMinimum: 0, maximum: 1000, unit: 'mm',
    } } },
  };
  const status: ModelStatus = {
    session_id: 'first', requested_revision: 0, published_revision: null, state: 'idle', error: null,
  };
  const api = {
    getParameters: vi.fn<Api['getParameters']>().mockResolvedValue(parameters),
    getStatus: vi.fn<Api['getStatus']>().mockResolvedValue(status),
    putParameters: vi.fn<Api['putParameters']>().mockResolvedValue({ session_id: 'first', requested_revision: 2 }),
    regenerate: vi.fn<Api['regenerate']>().mockResolvedValue({ session_id: 'first', requested_revision: 1 }),
  };
  const view: View = {
    setMetadata: vi.fn(), setParameters: vi.fn(), setViewerUrl: vi.fn(), setStatus: vi.fn(), setError: vi.fn(),
  };
  const controller = createController(api, view, {
    setTimeout: (callback, delay) => setTimeout(callback, delay),
    clearTimeout: handle => clearTimeout(handle as ReturnType<typeof setTimeout>),
  });
  return { api, view, controller, parameters, status };
}
beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

it('initializes the viewer and requests regeneration', async () => {
  const { api, view, controller, parameters } = setup();
  await controller.start();
  expect(view.setViewerUrl).toHaveBeenCalledWith(parameters.viewer_url);
  expect(view.setParameters).toHaveBeenCalledWith({ size_mm: 100 }, true);
  expect(api.regenerate).toHaveBeenCalledTimes(1);
  controller.stop();
});

it('Apply submits a numeric size without an extra regeneration request', async () => {
  const { api, controller } = setup();
  await controller.start();
  api.regenerate.mockClear();
  await controller.apply('150');
  expect(api.putParameters).toHaveBeenCalledExactlyOnceWith({ size_mm: 150 });
  expect(api.regenerate).not.toHaveBeenCalled();
  controller.stop();
});

it('refreshes parameters and regenerates once after an API session restart', async () => {
  const { api, view, controller, parameters, status } = setup();
  await controller.start();
  api.getParameters.mockResolvedValue({ ...parameters, session_id: 'second' });
  api.getStatus.mockResolvedValue({ ...status, session_id: 'second' });
  api.regenerate.mockResolvedValue({ session_id: 'second', requested_revision: 1 });
  await vi.advanceTimersByTimeAsync(500);
  expect(view.setParameters).toHaveBeenLastCalledWith({ size_mm: 100 }, true);
  expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second' }));
  await vi.advanceTimersByTimeAsync(1000);
  expect(api.regenerate).toHaveBeenCalledTimes(2);
  expect(view.setViewerUrl).toHaveBeenCalledTimes(1);
  controller.stop();
});
