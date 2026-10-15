import * as api from './api';
import { createController } from './controller';
import './style.css';

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) throw new Error(`Missing element: ${id}`);
  return found as T;
}
const form = element<HTMLFormElement>('parameters');
const input = element<HTMLInputElement>('size');
const iframe = element<HTMLIFrameElement>('viewer');
const status = element('status');
const error = element('error');
let dirty = false;

const controller = createController(api, {
  setMetadata(metadata) {
    element('size-label').textContent = metadata.title;
    element('unit').textContent = metadata.unit;
    input.placeholder = String(metadata.default);
    const bounds: string[] = [];
    if (metadata.exclusiveMinimum !== undefined) bounds.push(`greater than ${metadata.exclusiveMinimum}`);
    else if (metadata.minimum !== undefined) bounds.push(`at least ${metadata.minimum}`);
    if (metadata.exclusiveMaximum !== undefined) bounds.push(`less than ${metadata.exclusiveMaximum}`);
    else if (metadata.maximum !== undefined) bounds.push(`at most ${metadata.maximum}`);
    element('bounds').textContent = `${bounds.join(', ')} ${metadata.unit}. Default: ${metadata.default} ${metadata.unit}.`;
    const minimum = metadata.minimum ?? metadata.exclusiveMinimum;
    const maximum = metadata.maximum ?? metadata.exclusiveMaximum;
    if (minimum !== undefined) input.min = String(minimum);
    else input.removeAttribute('min');
    if (maximum !== undefined) input.max = String(maximum);
    else input.removeAttribute('max');
  },
  setParameters(parameters, reset) {
    if (reset || !dirty) {
      input.value = String(parameters.size_mm);
      dirty = false;
    }
  },
  setViewerUrl(url) {
    // The node lives for the page lifetime. Status and errors never rerender it.
    if (iframe.getAttribute('src') !== url) iframe.src = url;
  },
  setStatus(model) {
    const published = model.published_revision === null ? 'No model published yet.'
      : `Displayed revision ${model.published_revision}.`;
    const labels = {
      idle: 'Ready to regenerate.',
      regenerating: `Regenerating revision ${model.requested_revision}…`,
      ready: `Revision ${model.requested_revision} ready.`,
      failed: `Revision ${model.requested_revision} failed.`,
    };
    status.textContent = `${labels[model.state]} ${published}`;
  },
  setError(message) {
    error.textContent = message;
    error.hidden = message === null;
  },
}, {
  setTimeout: (callback, delay) => window.setTimeout(callback, delay),
  clearTimeout: handle => window.clearTimeout(handle as number),
});

input.addEventListener('input', () => { dirty = true; });
form.addEventListener('submit', event => {
  event.preventDefault();
  void controller.apply(input.value);
});
element('regenerate').addEventListener('click', () => { void controller.regenerate(); });
window.addEventListener('pagehide', () => controller.stop());
window.addEventListener('pageshow', event => { if (event.persisted) void controller.start(); });
void controller.start();
