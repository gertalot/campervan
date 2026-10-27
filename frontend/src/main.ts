import * as api from './api';
import { createController } from './controller';
import { setupSidebarResize } from './sidebar';
import { setupVisibility, createVisibilityButton, updateVisibilityButton } from './visibility';
import { createCadViewer } from './viewer';
import { setupMannequinControls } from './mannequin-controls';
import { setupMaterials } from './materials';
import { PlanningClient } from './planning-api';
import { setupPlanner } from './planner';
import { setupTabs, showTab, onTab } from './tabs';
import { setupCutting } from './cutting';
import { isStaticSite, readSnapshotPart } from './site-runtime';
import './style.css';

function element<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) throw new Error(`Missing element: ${id}`);
  return found as T;
}
const form = element<HTMLFormElement>('parameters');
const fields = element('fields');
const liveControls = element('live-controls');
const inputs = new Map<string, HTMLInputElement | HTMLSelectElement>();
const tableGroups: Record<number, string> = { 0: 'Bench mount', 2: 'Stowed' };
const tableEyes = new Map<number, HTMLButtonElement>();
function refreshTableEyes() {
  const selected = Number(inputs.get('table_mount')?.value ?? 0);
  for (const [index, button] of tableEyes) {
    updateVisibilityButton(button, tableGroups[index], selected === index ? 'shown' : 'hidden');
  }
}
const status = element('status');
const error = element('error');
if (isStaticSite) {
  form.querySelector<HTMLElement>('.actions')!.hidden = true;
  const badge = document.createElement('span');
  badge.className = 'snapshot-label';
  badge.textContent = 'Read-only snapshot';
  badge.title = 'Explore the model and saved layouts. Edit dimensions, materials and the plan in the local application.';
  status.before(badge);
  void readSnapshotPart<string>('exported_at').then(date => {
    badge.textContent = `Snapshot · ${new Date(date).toLocaleDateString()}`;
  }).catch(message => { error.textContent = String(message); error.hidden = false; });
}
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
const cutting = setupCutting(element('cuts-panel'), path => {
  showTab('cad');
  if (path.startsWith('Laptop table / ')) {
    void controller.savePosition('table_mount', 0);
  }
  if (!viewer.focusPiece(path)) {
    error.textContent = 'This piece is not in the displayed CAD model yet.'; error.hidden = false;
  }
});
viewer.setPieceLink({ has: cutting.hasPart, show: path => { void cutting.showPart(path); } });
const cabinetSideControl = element('cabinet-side-control');
const cabinetSideInputs = [...cabinetSideControl.querySelectorAll<HTMLInputElement>('input[name="cabinet-side"]')];
function setCabinetSide(side: string) {
  const right = side === 'right';
  for (const input of cabinetSideInputs) input.checked = input.value === (right ? 'right' : 'left');
  localStorage.setItem('campervan.cabinet-side', right ? 'right' : 'left');
  viewer.setMirrored(right);
  cutting.setMirrored(right);
}
for (const input of cabinetSideInputs) input.addEventListener('change', () => {
  if (input.checked) setCabinetSide(input.value);
});
setCabinetSide(localStorage.getItem('campervan.cabinet-side')
  ?? (localStorage.getItem('campervan.mirror-layout') === 'true' ? 'right' : 'left'));
localStorage.removeItem('campervan.mirror-layout');
void planning.read();
setupSidebarResize(element('sidebar-resizer'), element('sidebar'));

const controller = createController(api, {
  setMetadata(metadata) {
    visibility.resetGroups();
    fields.replaceChildren();
    liveControls.replaceChildren(cabinetSideControl);
    inputs.clear();
    tableEyes.clear();
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
          const tableIndex = groupPath[0] === 'Laptop table' && depth === 1
            ? Number(Object.entries(tableGroups).find(([, name]) => name === title)?.[0] ?? -1) : -1;
          if (tableIndex >= 0) {
            const eye = createVisibilityButton(title, () => {
              const current = Number(inputs.get('table_mount')?.value ?? 0);
              void controller.savePosition('table_mount', current === tableIndex ? (tableIndex === 0 ? 2 : 0) : tableIndex);
            });
            tableEyes.set(tableIndex, eye);
            heading.append(eye);
          } else if (cadVisibility && !(groupPath[0] === 'Cabinet' && groupPath[1] === 'Doors' && depth >= 2)) {
            visibility.addGroup(heading, `/Campervan/${groupPath.slice(0, depth + 1).join('/')}`, title);
          }
          group.append(heading);
          parent.append(group);
          groups.set(path, group);
        }
        parent = group;
      }
      return parent;
    }
    for (const [name, field] of Object.entries(metadata)) {
      const topLevelControl = field.control === 'position'
        && (name === 'table_fold_open_percent' || !['Stored gear', 'Laptop table', 'Cabinet'].includes(field.group[0]));
      const parent = groupFor(topLevelControl ? [] : field.group, topLevelControl ? liveControls : fields);
      const row = document.createElement('div');
      row.className = 'parameter-row';
      const label = document.createElement('label');
      label.htmlFor = name;
      label.textContent = field.title;
      const input = field.options ? document.createElement('select') : document.createElement('input');
      input.id = name;
      input.name = name;
      if (input instanceof HTMLInputElement) {
        input.type = field.control === 'position' ? 'range' : 'number';
        input.step = field.control === 'position' ? (field.unit === '%' ? '0.1' : '1') : 'any';
        input.autocomplete = 'off';
        input.placeholder = String(field.default);
      } else {
        for (const option of field.options!) input.add(new Option(option.label, String(option.value)));
        row.classList.add('choice-row');
      }
      if (field.material && input instanceof HTMLInputElement) {
        input.readOnly = true;
        input.addEventListener('click', () => materials.show(field.material));
        label.title = isStaticSite ? 'View stock details in Bill of materials' : 'Edit stock dimensions in Bill of materials';
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
      if (input instanceof HTMLInputElement) {
        if (minimum !== undefined) input.min = String(minimum);
        if (maximum !== undefined) input.max = String(maximum);
      }
      const tooltip = [field.description, `Default: ${field.default} ${field.unit}.`,
        bounds.length ? `${bounds.join(', ')} ${field.unit}.` : ''].filter(Boolean).join(' ');
      label.title = `${field.title}. ${tooltip}`;
      input.title = label.title;
      if (field.control === 'position') {
        input.dataset.livePosition = 'true';
        if (field.options) {
          row.classList.add('choice-row');
          row.append(label, input);
        } else {
          row.classList.add('position-row');
          const value = document.createElement('output');
          value.htmlFor = name;
          value.id = `${name}-value`;
          row.append(label, value, input);
        }
        input.addEventListener('input', () => viewer.previewPositions({ [name]: Number(input.value) }));
        input.addEventListener('change', () => { void viewer.savePositions(); });
      } else {
        if (isStaticSite) {
          if (input instanceof HTMLInputElement) input.readOnly = true;
          else input.disabled = true;
        }
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
    const stored = groupFor(['Laptop table', 'Stowed'], fields);
    const hint = document.createElement('p');
    hint.id = 'table-stowed-summary';
    hint.className = 'dimension-hint';
    stored.append(hint);
    // Reattach the same live controls after metadata refreshes, preserving pose and listeners.
    fields.append(seatedMannequin);
  },
  setConstraints(metadata, errors, adjustments, parameters) {
    for (const [name, input] of inputs) {
      if (!(input instanceof HTMLInputElement) || metadata[name].control === 'position') continue;
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
    viewer.setLayoutWidth(parameters.cargo_width_mm);
    const stack = 2 * parameters.table_ply_thickness_mm;
    element('table-stowed-summary').textContent = `Folded top with upright and arm stored underneath. `
      + `Approx. ${stack + 77}mm thick including the ${stack}mm bamboo stack. `
      + 'Preview location is adjustable; final storage location and actual handle clearance remain unconfirmed.';
    for (const [name, input] of inputs) {
      if (dirty && !reset && !(input instanceof HTMLInputElement && input.readOnly)) continue;
      input.value = String(parameters[name]);
      const output = document.getElementById(`${name}-value`);
      if (output) output.textContent = input.value;
    }
    refreshTableEyes();
    if (reset) dirty = false;
  },
  setViewerUrl: url => viewer.connect(url),
  setPosition(name, percent) {
    const input = inputs.get(name);
    if (input) input.value = String(percent);
    const output = document.getElementById(`${name}-value`);
    if (output) output.textContent = String(percent);
    viewer.setPosition(name, percent);
    if (name === 'table_mount') refreshTableEyes();
  },
  setStatus(model) {
    materials.onStatus(model);
    cutting.onStatus(model);
    const labels = {
      idle: 'Loading model…',
      regenerating: 'Regenerating…',
      ready: 'Ready',
      failed: 'Model update failed',
    };
    const previous = model.published_revision !== null && model.published_revision !== model.requested_revision;
    status.textContent = labels[model.state] + (previous ? ' · Previous model' : '');
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
viewer.setMotionController(controller);
onTab(tab => { if (tab !== 'cad') viewer.cancelDrag(); });

const draftValues = () => Object.fromEntries([...inputs].map(([name, input]) => [name, input.value]));
let previewTimer: number;
form.addEventListener('input', event => {
  if (isStaticSite) return;
  const target = event.target as HTMLElement;
  if (target.dataset.livePosition === 'true') return;
  dirty = true;
  window.clearTimeout(previewTimer);
  previewTimer = window.setTimeout(() => { void controller.preview(draftValues()); }, 180);
});
form.addEventListener('submit', event => {
  event.preventDefault();
  if (isStaticSite) return;
  window.clearTimeout(previewTimer);
  void controller.apply(draftValues());
});
element('regenerate').addEventListener('click', () => { void controller.regenerate(); });
window.addEventListener('pagehide', () => controller.stop());
window.addEventListener('pageshow', event => { if (event.persisted) void controller.start(); });
void controller.start();
