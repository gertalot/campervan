import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { createController, type View } from './controller';
import type { Api, ModelStatus, ParameterResponse } from './api';

function setup(saved = new Map<string, string>()) {
  const parameters: ParameterResponse = {
    session_id: 'first', parameters: { cargo_width_mm: 1500, cargo_length_mm: 1860 },
    viewer_url: 'http://127.0.0.1:3939/viewer',
    schema: { properties: {
      cargo_width_mm: { title: 'Cargo width', default: 1500, exclusiveMinimum: 0, unit: 'mm', group: ['Vehicle references', 'Floor outline'] },
      cargo_length_mm: { title: 'Cargo length', default: 1860, exclusiveMinimum: 0, unit: 'mm', group: ['Vehicle references', 'Floor outline'] },
    } },
  };
  const status: ModelStatus = {
    session_id: 'first', requested_revision: 0, published_revision: null, state: 'idle', error: null,
  };
  const api = {
    getParameters: vi.fn<Api['getParameters']>().mockResolvedValue(parameters),
    getStatus: vi.fn<Api['getStatus']>().mockResolvedValue(status),
    putParameters: vi.fn<Api['putParameters']>().mockResolvedValue({ session_id: 'first', requested_revision: 2 }),
    regenerate: vi.fn<Api['regenerate']>().mockResolvedValue({ session_id: 'first', requested_revision: 1 }),
    setPosition: vi.fn<Api['setPosition']>().mockResolvedValue({ bed_extension_percent: 75 }),
  };
  const view: View = {
    setMetadata: vi.fn(), setParameters: vi.fn(), setViewerUrl: vi.fn(), setStatus: vi.fn(), setError: vi.fn(),
    setPosition: vi.fn(),
  };
  const controller = createController(api, view, {
    setTimeout: (callback, delay) => setTimeout(callback, delay),
    clearTimeout: handle => clearTimeout(handle as ReturnType<typeof setTimeout>),
  }, { getItem: key => saved.get(key) ?? null, setItem: (key, value) => { saved.set(key, value); } });
  return { api, view, controller, parameters, status };
}
beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

it('initializes the viewer and requests regeneration', async () => {
  const { api, view, controller, parameters } = setup();
  await controller.start();
  expect(view.setViewerUrl).toHaveBeenCalledWith(parameters.viewer_url);
  expect(view.setParameters).toHaveBeenCalledWith(parameters.parameters, true);
  expect(api.regenerate).toHaveBeenCalledTimes(1);
  controller.stop();
});

it('Apply submits numeric dimensions without an extra regeneration request', async () => {
  const { api, controller } = setup();
  await controller.start();
  api.regenerate.mockClear();
  await controller.apply({ cargo_width_mm: '1520', cargo_length_mm: '1900' });
  expect(api.putParameters).toHaveBeenCalledExactlyOnceWith({ cargo_width_mm: 1520, cargo_length_mm: 1900 });
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
  expect(view.setParameters).toHaveBeenLastCalledWith(parameters.parameters, true);
  expect(view.setStatus).toHaveBeenLastCalledWith(expect.objectContaining({ session_id: 'second' }));
  await vi.advanceTimersByTimeAsync(1000);
  expect(api.regenerate).toHaveBeenCalledTimes(2);
  expect(view.setViewerUrl).toHaveBeenCalledTimes(1);
  controller.stop();
});

it('moves the bed and drawer independently without regenerating, restoring both after a geometry update', async () => {
  const { api, view, controller, status } = setup();
  await controller.start();
  api.regenerate.mockClear();
  controller.previewPosition('bed_extension_percent', 75);
  controller.previewPosition('drawer_extension_percent', 40);
  expect(view.setPosition).toHaveBeenCalledWith('bed_extension_percent', 75);
  expect(view.setPosition).toHaveBeenLastCalledWith('drawer_extension_percent', 40);
  await controller.savePosition('drawer_extension_percent', 40);
  expect(api.setPosition).toHaveBeenCalledExactlyOnceWith('drawer_extension_percent', 40);
  expect(api.putParameters).not.toHaveBeenCalled();
  expect(api.regenerate).not.toHaveBeenCalled();
  vi.mocked(view.setPosition).mockClear();
  api.getStatus.mockResolvedValue({ ...status, requested_revision: 1, published_revision: 1, state: 'ready' });
  await vi.advanceTimersByTimeAsync(500);
  expect(view.setPosition).toHaveBeenCalledWith('bed_extension_percent', 75);
  expect(view.setPosition).toHaveBeenCalledWith('drawer_extension_percent', 40);
  controller.stop();
});

it('restores all sliders from browser storage and sends them to a restarted API before regenerating', async () => {
  const saved = new Map<string, string>();
  const first = setup(saved);
  for (const [name, value] of Object.entries({
    bed_extension_percent: 75, drawer_extension_percent: 40, cross_lid_open_percent: 60,
  })) first.controller.previewPosition(name, value);
  first.controller.stop();

  const { api, view, controller, parameters, status } = setup(saved);
  const positions = JSON.parse(saved.get('campervan.positions')!);
  for (const name of Object.keys(positions)) {
    parameters.parameters[name] = 0;
    parameters.schema.properties[name] = {
      title: name, default: 0, minimum: 0, maximum: 100, unit: '%', group: [], control: 'position',
    };
  }
  api.regenerate.mockImplementation(async () => {
    for (const [name, value] of Object.entries(positions)) {
      expect(api.setPosition).toHaveBeenCalledWith(name, value);
    }
    return { session_id: status.session_id, requested_revision: 1 };
  });
  await controller.start();
  expect(view.setParameters).toHaveBeenLastCalledWith({ ...parameters.parameters, ...positions }, true);
  for (const [name, value] of Object.entries(positions)) expect(view.setPosition).toHaveBeenCalledWith(name, value);

  api.setPosition.mockClear();
  parameters.session_id = status.session_id = 'restarted';
  await vi.advanceTimersByTimeAsync(500);
  expect(api.setPosition).toHaveBeenCalledTimes(3);
  expect(view.setParameters).toHaveBeenLastCalledWith({ ...parameters.parameters, ...positions }, true);
  expect(api.regenerate).toHaveBeenCalledTimes(2);
  controller.stop();
});
