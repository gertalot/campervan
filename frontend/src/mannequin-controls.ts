import { seatedPose, type MannequinPose } from './mannequin';

/** Browser-only pose controls: never send these through CAD regeneration. */
export function setupMannequinControls(
  container: HTMLDetailsElement,
  visible: HTMLInputElement,
  change: (pose: MannequinPose) => void,
) {
  const storageKey = 'campervan.mannequin.seated';
  const pose: MannequinPose = { ...seatedPose, ...JSON.parse(localStorage.getItem(storageKey) ?? '{}') };
  const inputs = new Map<keyof MannequinPose, HTMLInputElement>();
  const outputs = new Map<keyof MannequinPose, HTMLOutputElement>();
  container.open = localStorage.getItem(`${storageKey}.collapsed`) !== 'true';
  container.addEventListener('toggle', () => localStorage.setItem(`${storageKey}.collapsed`, String(!container.open)));
  const summary = document.createElement('summary');
  summary.textContent = 'Seated mannequin · 178cm';
  container.append(summary);
  visible.checked = pose.visible;
  function update() {
    visible.checked = pose.visible;
    for (const [name, input] of inputs) {
      input.value = String(pose[name]);
      const output = outputs.get(name);
      if (output) output.value = `${Math.round(Number(pose[name]))}${['x', 'y', 'z', 'compression'].includes(name) ? 'mm' : '°'}`;
    }
    localStorage.setItem(storageKey, JSON.stringify(pose));
    change(pose);
  }
  visible.addEventListener('change', () => { pose.visible = visible.checked; update(); });
  const presets = document.createElement('div');
  presets.className = 'mannequin-presets';
  for (const [label, angles] of Object.entries({
    'Sit on bench': seatedPose,
  })) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.addEventListener('click', () => { Object.assign(pose, angles, { visible: true }); update(); });
    presets.append(button);
  }
  container.append(presets);
  const hint = document.createElement('p');
  hint.className = 'dimension-hint';
  hint.textContent = 'Position at hip joint · mm. Feet stay on the floor; leg angles and hip height are linked.';
  container.append(hint);
  const status = document.createElement('p');
  status.id = 'mannequin-status';
  status.className = 'dimension-hint';
  status.setAttribute('role', 'status');
  container.append(status);
  const controls: [Exclude<keyof MannequinPose, 'visible' | 'autoLegs' | 'fitSeat'>, string, number, number, boolean][] = [
    ['x', 'Across (X)', 0, 1500, true],
    ['y', 'Along (Y)', 0, 2500, true],
    ['z', 'Hip height (Z)', 120, 900, true],
    ['facing', 'Facing', 0, 360, true],
    ['compression', 'Foam compression', 0, 50, true],
    ['lean', 'Back recline', -90, 150, true],
    ['curvature', 'Back curvature', 0, 90, true],
    ['headTilt', 'Head tilt down', 0, 60, true],
    ['hip', 'Hip bend', 0, 120, true],
    ['knee', 'Knee bend', 0, 140, true],
    ['shoulder', 'Arms forward', -30, 150, true],
    ['elbow', 'Elbows bent', 0, 140, true],
  ];
  for (const [name, labelText, min, max, slider] of controls) {
    const row = document.createElement('div');
    row.className = slider ? 'parameter-row position-row' : 'parameter-row';
    const label = document.createElement('label');
    label.textContent = labelText;
    label.htmlFor = `mannequin-${name}`;
    const input = document.createElement('input');
    input.id = label.htmlFor;
    input.type = slider ? 'range' : 'number';
    input.min = String(min);
    input.max = String(max);
    input.step = slider ? '1' : '5';
    row.append(label);
    if (slider) {
      const output = document.createElement('output');
      output.htmlFor = input.id;
      outputs.set(name, output);
      row.append(output);
    }
    row.append(input);
    inputs.set(name, input);
    input.addEventListener('input', () => {
      if (!Number.isFinite(input.valueAsNumber)) return;
      const previous = pose[name];
      pose[name] = Math.max(min, Math.min(max, input.valueAsNumber));
      if (['x', 'y', 'z', 'facing', 'hip', 'knee'].includes(name)) pose.fitSeat = false;
      if (name === 'hip' || name === 'knee') pose.autoLegs = false;
      if (name === 'z') pose.autoLegs = true;
      if (name === 'compression') {
        pose.z += previous - pose.compression;
        pose.autoLegs = true;
        pose.fitSeat = false;
      }
      update();
    });
    container.append(row);
  }
  update();
  return {
    fitted(values: Pick<MannequinPose, 'x' | 'y' | 'z' | 'facing' | 'hip' | 'knee'>) {
      Object.assign(pose, values);
      pose.fitSeat = false;
      for (const name of ['x', 'y', 'z', 'facing', 'hip', 'knee'] as const) {
        inputs.get(name)!.value = String(pose[name]);
        outputs.get(name)!.value = `${Math.round(pose[name])}${['x', 'y', 'z'].includes(name) ? 'mm' : '°'}`;
      }
      localStorage.setItem(storageKey, JSON.stringify(pose));
    },
  };
}
