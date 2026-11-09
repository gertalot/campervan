const categories: Record<string, string[]> = {
  vehicle: ['/Campervan/Vehicle references'],
  wheelArches: ['/Campervan/Vehicle references/Wheel arches'],
  woodenFloor: ['/Campervan/Finished floor plywood'],
  cabinet: ['/Campervan/Cabinet'],
  cabinetShelves: ['/Campervan/Cabinet/Lower module/Shelves', '/Campervan/Cabinet/Upper module/Shelves'],
  cabinetDoors: ['/Campervan/Cabinet/Lower module/Doors', '/Campervan/Cabinet/Upper module/Doors'],
  cabinetSkin: ['/Campervan/Cabinet/Lower module/Skin', '/Campervan/Cabinet/Upper module/Skin'],
  cabinetFrames: ['/Campervan/Cabinet/Lower module/Frames', '/Campervan/Cabinet/Upper module/Frames'],
  storedGear: ['/Campervan/Stored gear'],
  longBench: ['/Campervan/Long bench'],
  crossBench: ['/Campervan/Cross bench'],
  cushions: ['/Campervan/Long bench/Cushions', '/Campervan/Cross bench/Cushions'],
  slats: [
    '/Campervan/Long bench/Fixed frame/Fixed slats',
    '/Campervan/Long bench/Sliding bed/Sliding assembly/Moving slats',
    '/Campervan/Cross bench/Fixed frame/Fixed slats',
  ],
};

interface VisibilityViewer {
  setVisibility(rules: Record<string, boolean>, independentRoots: string[]): void;
  setExcludedComponents(paths: string[]): void;
  getVisibility(paths: string[]): 'shown' | 'hidden' | 'mixed';
}

export function updateVisibilityButton(button: HTMLButtonElement, title: string, state: 'shown' | 'hidden' | 'mixed') {
  button.dataset.visibility = state;
  button.setAttribute('aria-pressed', state === 'mixed' ? 'mixed' : String(state === 'shown'));
  button.setAttribute('aria-label', `${state === 'shown' ? 'Hide' : 'Show'} ${title}`);
  button.title = `${state === 'shown' ? 'Hide' : 'Show'} ${title}${state === 'mixed' ? ' (partly visible)' : ''}`;
}

export function createVisibilityButton(title: string, toggle: () => void) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'group-visibility';
  button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/><path class="eye-slash" d="m3 3 18 18"/></svg>';
  button.addEventListener('click', event => {
    event.preventDefault();
    event.stopPropagation();
    toggle();
  });
  updateVisibilityButton(button, title, 'shown');
  return button;
}

export function setupVisibility(container: HTMLElement, viewer: VisibilityViewer) {
  const inputs = [...container.querySelectorAll<HTMLInputElement>('input[name]')];
  const groups = new Map<HTMLButtonElement, { paths: string[]; title: string }>();
  const key = 'campervan.visibility.paths';
  const independentRoots = categories.wheelArches;
  let excludedRoots: string[] = [];
  const rules: Record<string, boolean> = {
    '/Campervan/Vehicle references/Floor outline': false,
    '/Campervan/Vehicle references/Rear opening/Clear opening': false,
    ...JSON.parse(localStorage.getItem(key) ?? '{}'),
  };
  // Carry existing component and category choices into the two carcass modules.
  const cabinetPrefix = '/Campervan/Cabinet/';
  for (const [path, visible] of Object.entries(rules)) {
    if (!path.startsWith(cabinetPrefix)) continue;
    const suffix = path.slice(cabinetPrefix.length);
    if (/^(Lower module|Upper module|Module fasteners)(\/|$)/.test(suffix)) continue;
    for (const module of ['Lower module', 'Upper module']) {
      rules[`${cabinetPrefix}${module}/${suffix}`] ??= visible;
    }
    delete rules[path];
  }
  for (const [path, visible] of Object.entries(rules)) {
    if (path.endsWith('/Back lining')) {
      rules[path.replace(/Back lining$/, 'Skin')] ??= visible;
      delete rules[path];
    }
  }
  if (localStorage.getItem(key)) localStorage.setItem(key, JSON.stringify(rules));
  // Assembly switches must retain independent content filters and reference-wire choices.
  const independentPaths = new Set([
    ...Object.values(categories).flat(),
    '/Campervan/Vehicle references/Floor outline',
    '/Campervan/Vehicle references/Rear opening/Clear opening',
  ]);
  if (!localStorage.getItem(key)) {
    for (const input of inputs) {
      for (const path of categories[input.name]) {
        rules[path] = localStorage.getItem(`campervan.visibility.${input.name}`) !== 'false';
      }
    }
  }

  function refresh() {
    for (const input of inputs) {
      // A checkbox represents its own switch, even when another switch masks its contents.
      const enabled = categories[input.name].map(path => rules[path] !== false);
      input.checked = enabled.every(Boolean);
      input.indeterminate = enabled.some(Boolean) && !input.checked;
    }
    for (const [button, { paths, title }] of groups) {
      updateVisibilityButton(button, title, viewer.getVisibility(paths));
      button.disabled = paths.every(path => excludedRoots.some(root => path === root || path.startsWith(`${root}/`)));
    }
  }

  function change(paths: string[], visible: boolean) {
    for (const path of paths) {
      for (const existing of Object.keys(rules)) {
        const independent = independentRoots.some(root => root.startsWith(`${path}/`)
          && (existing === root || existing.startsWith(`${root}/`)));
        const excluded = excludedRoots.some(root => existing === root || existing.startsWith(`${root}/`));
        if (existing.startsWith(`${path}/`) && !independentPaths.has(existing) && !independent && !excluded) {
          delete rules[existing];
        }
      }
      rules[path] = visible;
    }
    localStorage.setItem(key, JSON.stringify(rules));
    viewer.setVisibility(rules, independentRoots);
    viewer.setExcludedComponents(excludedRoots);
    refresh();
  }

  for (const input of inputs) {
    input.addEventListener('change', () => change(categories[input.name], input.checked));
  }

  return {
    setBuildInclusion(included: { drawer: boolean; table: boolean }) {
      excludedRoots = [
        ...(!included.drawer ? ['/Campervan/Long bench/Rear drawer'] : []),
        ...(!included.table ? ['/Campervan/Laptop table'] : []),
      ];
      viewer.setExcludedComponents(excludedRoots);
      refresh();
    },
    restore() {
      viewer.setVisibility(rules, independentRoots);
      viewer.setExcludedComponents(excludedRoots);
      refresh();
    },
    resetGroups() { groups.clear(); },
    addGroup(heading: HTMLElement, path: string, title: string) {
      const cabinetGroups: Record<string, string[]> = {
        Shelves: categories.cabinetShelves,
        Doors: categories.cabinetDoors,
        Skin: categories.cabinetSkin,
        Frames: categories.cabinetFrames,
        'Module joint': ['Lower module', 'Upper module'].map(module =>
          `/Campervan/Cabinet/${module}/Frames/Module joint`),
      };
      const suffix = path.startsWith(cabinetPrefix) ? path.slice(cabinetPrefix.length) : '';
      const paths = cabinetGroups[suffix] ?? [path];
      const button = createVisibilityButton(title, () => {
        change(paths, !paths.every(item => rules[item] !== false));
      });
      groups.set(button, { paths, title });
      heading.append(button);
      refresh();
    },
  };
}
