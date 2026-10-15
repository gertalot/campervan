import * as api from './api';
import { createController } from './controller';
import './style.css';

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) throw new Error(`Missing element: ${id}`);
  return found as T;
}
const form = element<HTMLFormElement>('parameters');
const fields = element('fields');
const inputs = new Map<string, HTMLInputElement>();
const iframe = element<HTMLIFrameElement>('viewer');
const status = element('status');
const error = element('error');
let dirty = false;

const controller = createController(api, {
  setMetadata(metadata) {
    fields.replaceChildren();
    inputs.clear();
    const groups = new Map<string, HTMLFieldSetElement>();
    for (const [name, field] of Object.entries(metadata)) {
      let group = groups.get(field.group);
      if (!group) {
        group = document.createElement('fieldset');
        const legend = document.createElement('legend');
        legend.textContent = field.group;
        group.append(legend);
        fields.append(group);
        groups.set(field.group, group);
      }
      const row = document.createElement('div');
      row.className = 'parameter-row';
      const label = document.createElement('label');
      label.htmlFor = name;
      label.textContent = field.title;
      const input = document.createElement('input');
      input.id = name;
      input.name = name;
      input.type = 'number';
      input.step = 'any';
      input.autocomplete = 'off';
      input.placeholder = String(field.default);
      const bounds: string[] = [];
      if (field.exclusiveMinimum !== undefined) bounds.push(`greater than ${field.exclusiveMinimum}`);
      else if (field.minimum !== undefined) bounds.push(`at least ${field.minimum}`);
      if (field.exclusiveMaximum !== undefined) bounds.push(`less than ${field.exclusiveMaximum}`);
      else if (field.maximum !== undefined) bounds.push(`at most ${field.maximum}`);
      const minimum = field.minimum ?? field.exclusiveMinimum;
      const maximum = field.maximum ?? field.exclusiveMaximum;
      if (minimum !== undefined) input.min = String(minimum);
      if (maximum !== undefined) input.max = String(maximum);
      const tooltip = [field.description, `Default: ${field.default} ${field.unit}.`,
        bounds.length ? `${bounds.join(', ')} ${field.unit}.` : ''].filter(Boolean).join(' ');
      label.title = `${field.title}. ${tooltip}`;
      input.title = label.title;
      row.append(label, input);
      group.append(row);
      inputs.set(name, input);
    }
  },
  setParameters(parameters, reset) {
    if (reset || !dirty) {
      for (const [name, input] of inputs) input.value = String(parameters[name]);
      dirty = false;
    }
  },
  setViewerUrl(url) {
    // The node lives for the page lifetime. Status and errors never rerender it.
    if (iframe.getAttribute('src') !== url) iframe.src = url;
  },
  setStatus(model) {
    const labels = {
      idle: 'Ready',
      regenerating: 'Regenerating…',
      ready: 'Ready',
      failed: 'Regeneration failed',
    };
    status.textContent = labels[model.state];
  },
  setError(message) {
    error.textContent = message;
    error.hidden = message === null;
  },
}, {
  setTimeout: (callback, delay) => window.setTimeout(callback, delay),
  clearTimeout: handle => window.clearTimeout(handle as number),
});

form.addEventListener('input', () => { dirty = true; });
form.addEventListener('submit', event => {
  event.preventDefault();
  void controller.apply(Object.fromEntries([...inputs].map(([name, input]) => [name, input.value])));
});
element('regenerate').addEventListener('click', () => { void controller.regenerate(); });
window.addEventListener('pagehide', () => controller.stop());
window.addEventListener('pageshow', event => { if (event.persisted) void controller.start(); });
void controller.start();
