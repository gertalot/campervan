export const categories: Record<string, string[]> = {
  vehicle: ['/Campervan/Vehicle references'],
  wheelArches: ['/Campervan/Vehicle references/Wheel arches'],
  woodenFloor: ['/Campervan/Finished floor plywood'],
  cabinet: ['/Campervan/Cabinet'],
  topCabinet: ['/Campervan/Cabinet/Upper module'],
  bottomCabinet: ['/Campervan/Cabinet/Lower module'],
  cabinetShelves: ['/Campervan/Cabinet/Lower module/Shelves', '/Campervan/Cabinet/Upper module/Shelves'],
  cabinetDoors: ['/Campervan/Cabinet/Lower module/Doors', '/Campervan/Cabinet/Upper module/Doors'],
  cabinetSkin: ['/Campervan/Cabinet/Lower module/Skin', '/Campervan/Cabinet/Upper module/Skin'],
  cabinetFrames: ['/Campervan/Cabinet/Lower module/Frames', '/Campervan/Cabinet/Upper module/Frames'],
  storedGear: ['/Campervan/Stored gear'],
  longBench: ['/Campervan/Long bench', '/Campervan/Laptop table/Fixed mount'],
  table: ['/Campervan/Laptop table/Bench mount', '/Campervan/Laptop table/Stowed'],
  crossBench: ['/Campervan/Cross bench'],
  cushions: ['/Campervan/Long bench/Cushions', '/Campervan/Cross bench/Cushions'],
  slats: [
    '/Campervan/Long bench/Hinged lid/Fixed slats',
    '/Campervan/Long bench/Hinged lid/Sliding bed/Sliding assembly/Moving slats',
    '/Campervan/Cross bench/Fixed frame/Fixed slats',
  ],
};

interface VisibilityViewer {
  setVisibility(rules: Record<string, boolean>): void;
  setExcludedComponents(paths: string[]): void;
  getVisibility(paths: string[]): 'shown' | 'hidden' | 'mixed';
}

export function updateVisibilityButton(button: HTMLButtonElement, title: string, state: 'shown' | 'hidden' | 'mixed') {
  button.dataset.visibility = state;
  button.setAttribute('aria-pressed', state === 'mixed' ? 'mixed' : String(state === 'shown'));
  button.setAttribute('aria-label', `${title} visibility`);
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

export function setupVisibility(
  container: HTMLElement, viewer: VisibilityViewer,
  mannequin: { eye: HTMLButtonElement; setBedVisible(enabled: boolean): void },
) {
  const groups = new Map<HTMLButtonElement, { paths: string[]; title: string }>();
  const key = 'campervan.visibility.paths';
  const bedKey = 'campervan.visibility.bedCouch';
  const bedRoots = [...categories.longBench, ...categories.crossBench];
  let bedVisible = localStorage.getItem(bedKey) !== 'false';
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
  rules[categories.longBench[1]] ??= rules[categories.longBench[0]] ?? true;
  if (localStorage.getItem(key)) localStorage.setItem(key, JSON.stringify(rules));
  if (!localStorage.getItem(key)) {
    for (const [name, paths] of Object.entries(categories)) {
      for (const path of paths) rules[path] = localStorage.getItem(`campervan.visibility.${name}`) !== 'false';
    }
  }

  const rows = [...container.querySelectorAll<HTMLElement>('li[data-category]')].map(row => {
    const name = row.dataset.category!;
    const label = row.querySelector<HTMLElement>(':scope > label, :scope > details > summary')!;
    const title = label.textContent!.trim();
    const paths = categories[name] ?? [];
    const eye = name === 'mannequin' ? mannequin.eye : createVisibilityButton(title, () => {
      if (name === 'bedCouch') {
        bedVisible = !bedVisible;
        localStorage.setItem(bedKey, String(bedVisible));
        apply();
      } else {
        change(paths, !paths.every(path => rules[path] !== false));
      }
    });
    eye.id = `visibility-${name}`;
    if (label instanceof HTMLLabelElement) label.htmlFor = eye.id;
    row.prepend(eye);
    return { name, title, paths, eye };
  });

  function refresh() {
    const hidden = Object.keys(rules).filter(path => !rules[path]);
    for (const { name, title, paths, eye } of rows) {
      if (name === 'bedCouch') {
        updateVisibilityButton(eye, title, bedVisible ? 'shown' : 'hidden');
        continue;
      }
      const maskedByBed = !bedVisible && (name === 'mannequin' || paths.every(path =>
        bedRoots.some(root => path === root || path.startsWith(`${root}/`))));
      const masked = maskedByBed || (paths.length > 0 && paths.every(path =>
        hidden.some(root => path.startsWith(`${root}/`))));
      eye.toggleAttribute('data-masked', masked);
      if (masked) eye.setAttribute('aria-description', 'Hidden by a parent group.');
      else eye.removeAttribute('aria-description');
      if (name === 'mannequin') continue;
      const enabled = paths.filter(path => rules[path] !== false).length;
      updateVisibilityButton(eye, title, enabled === paths.length ? 'shown' : enabled ? 'mixed' : 'hidden');
      eye.disabled = paths.every(path => excludedRoots.some(root => path === root || path.startsWith(`${root}/`)));
    }
    for (const [button, { paths, title }] of groups) {
      updateVisibilityButton(button, title, viewer.getVisibility(paths));
      button.disabled = paths.every(path => excludedRoots.some(root => path === root || path.startsWith(`${root}/`)));
    }
  }

  function apply() {
    const effective = { ...rules };
    if (!bedVisible) for (const root of bedRoots) effective[root] = false;
    mannequin.setBedVisible(bedVisible);
    viewer.setVisibility(effective);
    viewer.setExcludedComponents(excludedRoots);
    refresh();
  }

  function change(paths: string[], visible: boolean) {
    for (const path of paths) rules[path] = visible;
    localStorage.setItem(key, JSON.stringify(rules));
    apply();
  }

  apply();
  return {
    setBuildInclusion(included: { table: boolean }) {
      excludedRoots = [
        ...(!included.table ? ['/Campervan/Laptop table'] : []),
      ];
      viewer.setExcludedComponents(excludedRoots);
      refresh();
    },
    restore: apply,
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
