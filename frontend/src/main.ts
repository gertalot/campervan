import * as api from './api';
import { createController } from './controller';
import { setupSidebarResize } from './sidebar';
import { setupVisibility } from './visibility';
import { createCadViewer } from './viewer';
import { setupMannequinControls } from './mannequin-controls';
import { setupMaterials } from './materials';
import { PlanningClient } from './planning-api';
import { setupPlanner } from './planner';
import { setupTabs } from './tabs';
import './style.css';

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) throw new Error(`Missing element: ${id}`);
  return found as T;
}
const form = element<HTMLFormElement>('parameters');
const fields = element('fields');
const liveControls = element('live-controls');
const inputs = new Map<string, HTMLInputElement>();
const status = element('status');
const error = element('error');
const viewer = createCadViewer(element('viewer'), () => visibility.restore(), message => {
  error.textContent = message;
  error.hidden = false;
}, message => {
  for (const mode of ['seated', 'lying', 'lying-second']) element(`mannequin-${mode}-status`).textContent = message;
}, pose => mannequinControls.fitted(pose));
const visibility = setupVisibility(element('visibility'), viewer);
const seeInside = element<HTMLInputElement>('see-inside');
seeInside.checked = localStorage.getItem('campervan.see-inside') !== 'false';
viewer.setSeeInside(seeInside.checked);
seeInside.addEventListener('change', () => {
  localStorage.setItem('campervan.see-inside', String(seeInside.checked));
  viewer.setSeeInside(seeInside.checked);
});
const seatedMannequin = element<HTMLDetailsElement>('mannequin');
const mannequinControls = setupMannequinControls(
  seatedMannequin, element<HTMLInputElement>('mannequin-visible'), pose => viewer.setMannequinPose(pose),
);
let dirty = false;
const planning = new PlanningClient();
setupTabs();
setupPlanner(element('plan-panel'), planning);
const materials = setupMaterials(planning);
void planning.read();
setupSidebarResize(element('sidebar-resizer'), element('sidebar'));

const controller = createController(api, {
  setMetadata(metadata) {
    visibility.resetGroups();
    fields.replaceChildren();
    liveControls.replaceChildren();
    inputs.clear();
    const groups = new Map<string, HTMLDetailsElement>();
    function groupFor(groupPath: string[], parent: HTMLElement, cadVisibility = true): HTMLElement {
      for (let depth = 0; depth < groupPath.length; depth++) {
        const title = groupPath[depth];
        const path = JSON.stringify(groupPath.slice(0, depth + 1));
        let group = groups.get(path);
        if (!group) {
          group = document.createElement('details');
          group.dataset.group = path;
          const storageKey = `campervan.parameter-group.${path}.collapsed`;
          const oldTitles: Record<string, string> = {
            'Vehicle references': 'Vehicle', 'Fixed frame': 'Plywood',
            'Internal drawer-support frame': 'Drawer support', 'Sliding assembly': 'Bed', 'Angle brackets': 'Bed brackets',
          };
          const previousKey = `campervan.parameter-group.${oldTitles[title] ?? title}.collapsed`;
          group.open = (localStorage.getItem(storageKey) ?? localStorage.getItem(previousKey)) !== 'true';
          group.addEventListener('toggle', event => {
            localStorage.setItem(storageKey, String(!(event.currentTarget as HTMLDetailsElement).open));
          });
          const heading = document.createElement('summary');
          heading.textContent = title;
          if (cadVisibility) visibility.addGroup(heading, `/Campervan/${groupPath.slice(0, depth + 1).join('/')}`, title);
          group.append(heading);
          parent.append(group);
          groups.set(path, group);
        }
        parent = group;
      }
      return parent;
    }
    for (const [name, field] of Object.entries(metadata)) {
      const topLevelControl = field.control === 'position' && field.group[0] !== 'Stored gear';
      const parent = groupFor(topLevelControl ? [] : field.group, topLevelControl ? liveControls : fields);
      const row = document.createElement('div');
      row.className = 'parameter-row';
      const label = document.createElement('label');
      label.htmlFor = name;
      label.textContent = field.title;
      const input = document.createElement('input');
      input.id = name;
      input.name = name;
      input.type = field.control === 'position' ? 'range' : 'number';
      input.step = field.control === 'position' ? (field.unit === '%' ? '0.1' : '1') : 'any';
      input.autocomplete = 'off';
      input.placeholder = String(field.default);
      if (field.material) {
        input.readOnly = true;
        input.addEventListener('click', () => materials.show(field.material));
        label.title = 'Edit stock dimensions in Bill of materials';
        const link = document.createElement('button');
        link.type = 'button'; link.className = 'material-link'; link.textContent = field.title;
        link.addEventListener('click', () => materials.show(field.material));
        label.replaceChildren(link);
      }
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
      if (field.control === 'position') {
        row.classList.add('position-row');
        const value = document.createElement('output');
        value.htmlFor = name;
        value.id = `${name}-value`;
        row.append(label, value, input);
        input.addEventListener('input', () => controller.previewPosition(name, input.valueAsNumber));
        input.addEventListener('change', () => { void controller.savePosition(name, input.valueAsNumber); });
      } else {
        const hint = document.createElement('small');
        hint.id = `${name}-constraint`;
        hint.className = 'parameter-constraint';
        hint.hidden = true;
        input.setAttribute('aria-describedby', hint.id);
        row.append(label, input, hint);
      }
      parent.append(row);
      inputs.set(name, input);
    }
    // Reattach the same live controls after metadata refreshes, preserving pose and listeners.
    fields.append(seatedMannequin);
  },
  setConstraints(metadata, errors, adjustments, parameters) {
    for (const [name, input] of inputs) {
      if (input.type === 'range') continue;
      const field = metadata[name];
      const minimum = field.minimum ?? field.exclusiveMinimum;
      const maximum = field.maximum ?? field.exclusiveMaximum;
      input.min = minimum === undefined ? '' : String(minimum);
      input.max = maximum === undefined ? '' : String(maximum);
      if (field.reason) {
        input.title = `${field.title}. ${field.reason}`;
        if (input.labels?.[0]) input.labels[0].title = input.title;
      }
      input.setCustomValidity(errors[name] ?? '');
      input.setAttribute('aria-invalid', String(Boolean(errors[name])));
      if (adjustments[name]) input.value = String(parameters[name]);
      const hint = element(`${name}-constraint`);
      hint.textContent = errors[name] ?? adjustments[name] ?? field.reason ?? '';
      hint.hidden = !hint.textContent;
      hint.classList.toggle('invalid', Boolean(errors[name]));
    }
    form.querySelector<HTMLButtonElement>('button[type="submit"]')!.disabled = Object.keys(errors).length > 0;
  },
  setParameters(parameters, reset) {
    for (const [name, input] of inputs) {
      if (dirty && !reset && !input.readOnly) continue;
      input.value = String(parameters[name]);
      const output = document.getElementById(`${name}-value`);
      if (output) output.textContent = input.value;
    }
    if (reset) dirty = false;
  },
  setViewerUrl: url => viewer.connect(url),
  setPosition(name, percent) {
    const input = inputs.get(name);
    if (input) input.value = String(percent);
    const output = document.getElementById(`${name}-value`);
    if (output) output.textContent = String(percent);
    viewer.setPosition(name, percent);
  },
  setStatus(model) {
    materials.onStatus(model);
    const labels = {
      idle: 'Ready',
      regenerating: 'Regenerating…',
      ready: 'Ready',
      failed: 'Regeneration failed',
    };
    status.textContent = labels[model.state];
    status.dataset.state = model.state;
  },
  setError(message) {
    error.textContent = message;
    error.hidden = message === null;
  },
}, {
  setTimeout: (callback, delay) => window.setTimeout(callback, delay),
  clearTimeout: handle => window.clearTimeout(handle as number),
}, window.localStorage);

const draftValues = () => Object.fromEntries([...inputs].map(([name, input]) => [name, input.value]));
let previewTimer: number;
form.addEventListener('input', event => {
  if ((event.target as HTMLInputElement).type === 'range') return;
  dirty = true;
  window.clearTimeout(previewTimer);
  previewTimer = window.setTimeout(() => { void controller.preview(draftValues()); }, 180);
});
form.addEventListener('submit', event => {
  event.preventDefault();
  window.clearTimeout(previewTimer);
  void controller.apply(draftValues());
});
element('regenerate').addEventListener('click', () => { void controller.regenerate(); });
window.addEventListener('pagehide', () => controller.stop());
window.addEventListener('pageshow', event => { if (event.persisted) void controller.start(); });
void controller.start();
