import { lyingPose, secondLyingPose, seatedPose, restoreMannequinPose, type MannequinPose } from './mannequin';

/** Browser-only pose controls: never send these through CAD regeneration. */
function setupPoseControls(
  container: HTMLDetailsElement,
  defaults: MannequinPose,
  change: (pose: MannequinPose) => void,
) {
  const storageKey = `campervan.mannequin.${defaults.mode}`;
  const saved = JSON.parse(localStorage.getItem(storageKey) ?? '{}');
  const pose = restoreMannequinPose(defaults, saved);
  const inputs = new Map<keyof MannequinPose, HTMLInputElement>();
  const outputs = new Map<keyof MannequinPose, HTMLOutputElement>();
  container.open = localStorage.getItem(`${storageKey}.collapsed`) !== 'true';
  container.addEventListener('toggle', () => localStorage.setItem(`${storageKey}.collapsed`, String(!container.open)));
  const summary = document.createElement('summary');
  summary.textContent = defaults.mode === 'seated' ? 'Seated mannequin' : defaults.mode === 'lying' ? 'Lying mannequin' : 'Second lying mannequin';
  container.append(summary);
  const unit = (name: keyof MannequinPose) => ['x', 'y', 'z', 'compression'].includes(name)
    || (defaults.mode !== 'seated' && ['shoulder', 'elbow'].includes(name)) ? 'mm' : '°';
  function update() {
      for (const [name, input] of inputs) {
      input.value = String(pose[name]);
      const output = outputs.get(name);
      if (output) output.value = `${Math.round(Number(pose[name]))}${unit(name)}`;
    }
    hint.textContent = pose.mode !== 'seated' ? 'Shown automatically at full bed extension. Position offsets are relative to its pillow.'
      : 'Position at hip joint · mm. Feet stay on the floor; leg angles and hip height are linked.';
    inputs.get('compression')!.closest('.parameter-row')!.querySelector('label')!.textContent =
      pose.mode !== 'seated' ? 'Pillow compression' : 'Foam compression';
    inputs.get('compression')!.max = pose.mode !== 'seated' ? '130' : '50';
    localStorage.setItem(storageKey, JSON.stringify({ ...pose, poseVersion: 2 }));
    change(pose);
  }
  const presets = document.createElement('div');
  presets.className = 'mannequin-presets';
  for (const [label, angles] of Object.entries({
    'Reset posture': defaults,
  })) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.addEventListener('click', () => { Object.assign(pose, angles); update(); });
    presets.append(button);
  }
  container.append(presets);
  const hint = document.createElement('p');
  hint.className = 'dimension-hint';
  hint.textContent = 'Position at hip joint · mm. Feet stay on the floor; leg angles and hip height are linked.';
  container.append(hint);
  const status = document.createElement('p');
  status.id = `mannequin-${defaults.mode}-status`;
  status.className = 'dimension-hint';
  status.setAttribute('role', 'status');
  container.append(status);
  const controls: [Exclude<keyof MannequinPose, 'visible' | 'autoLegs' | 'fitSeat' | 'mode'>, string, number, number, boolean][] = [
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
  if (defaults.mode !== 'seated') {
    controls.splice(0, controls.length,
      ['x', 'Across offset', -500, 500, true], ['y', 'Along offset', -500, 500, true],
      ['z', 'Height offset', -100, 300, true], ['facing', 'Body rotation', -90, 90, true],
      ['compression', 'Pillow compression', 0, 130, true], ['lean', 'Back lift', -20, 40, true],
      ['curvature', 'Back curvature', 0, 60, true], ['headTilt', 'Head tilt adjustment', -30, 30, true],
      ['hip', 'Hip bend', -15, 60, true], ['knee', 'Knee bend', 0, 90, true],
      ['shoulder', 'Hands along belly', -100, 100, true], ['elbow', 'Hand height offset', -150, 150, true]);
  }
  for (const [name, labelText, min, max, slider] of controls) {
    const row = document.createElement('div');
    row.className = slider ? 'parameter-row position-row' : 'parameter-row';
    const label = document.createElement('label');
    label.textContent = labelText;
    label.htmlFor = `mannequin-${defaults.mode}-${name}`;
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
      pose[name] = Math.max(min, Math.min(Number(input.max), input.valueAsNumber));
      if (['x', 'y', 'z', 'facing', 'hip', 'knee'].includes(name)) pose.fitSeat = false;
      if (name === 'hip' || name === 'knee') pose.autoLegs = false;
      if (name === 'z') pose.autoLegs = true;
      if (name === 'compression' && pose.mode === 'seated') {
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
      if (pose.mode !== 'seated') return;
      Object.assign(pose, values);
      pose.fitSeat = false;
      for (const name of ['x', 'y', 'z', 'facing', 'hip', 'knee'] as const) {
        inputs.get(name)!.value = String(pose[name]);
        outputs.get(name)!.value = `${Math.round(pose[name])}${['x', 'y', 'z'].includes(name) ? 'mm' : '°'}`;
      }
      localStorage.setItem(storageKey, JSON.stringify({ ...pose, poseVersion: 2 }));
    },
  };
}

/** Independent mannequins share only the visibility checkbox. */
export function setupMannequinControls(
  container: HTMLDetailsElement, visible: HTMLInputElement, change: (pose: MannequinPose) => void,
) {
  const summary = document.createElement('summary');
  summary.textContent = 'Mannequin';
  container.append(summary);
  const collapsedKey = 'campervan.parameter-group.["Mannequin"].collapsed';
  container.open = localStorage.getItem(collapsedKey) !== 'true';
  container.addEventListener('toggle', () => localStorage.setItem(collapsedKey, String(!container.open)));
  const saved = JSON.parse(localStorage.getItem('campervan.mannequin.seated') ?? '{}');
  visible.checked = localStorage.getItem('campervan.mannequin.visible') === null
    ? saved.visible !== false : localStorage.getItem('campervan.mannequin.visible') !== 'false';
  const poses = new Map<string, MannequinPose>();
  const groups = [seatedPose, lyingPose, secondLyingPose].map(defaults => {
    const group = document.createElement('details');
    group.className = 'parameter-group';
    container.append(group);
    return setupPoseControls(group, defaults, pose => {
      poses.set(pose.mode, pose);
      change({ ...pose, visible: visible.checked });
    });
  });
  visible.addEventListener('change', () => {
    localStorage.setItem('campervan.mannequin.visible', String(visible.checked));
    for (const pose of poses.values()) change({ ...pose, visible: visible.checked });
  });
  return { fitted: groups[0].fitted };
}
