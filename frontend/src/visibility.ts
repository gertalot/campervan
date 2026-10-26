const categories: Record<string, string[]> = {
  vehicle: ['/Campervan/Vehicle references'],
  wheelArches: ['/Campervan/Vehicle references/Wheel arches'],
  woodenFloor: ['/Campervan/Finished floor plywood'],
  cabinet: ['/Campervan/Cabinet'],
  cabinetShelves: ['/Campervan/Cabinet/Shelves'],
  cabinetBacking: ['/Campervan/Cabinet/Back lining'],
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
  const groups = new Map<HTMLButtonElement, { path: string; title: string }>();
  const key = 'campervan.visibility.paths';
  const independentRoots = categories.wheelArches;
  const rules: Record<string, boolean> = {
    '/Campervan/Vehicle references/Floor outline': false,
    '/Campervan/Vehicle references/Rear opening/Clear opening': false,
    ...JSON.parse(localStorage.getItem(key) ?? '{}'),
  };
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
    for (const [button, { path, title }] of groups) {
      updateVisibilityButton(button, title, viewer.getVisibility([path]));
    }
  }

  function change(paths: string[], visible: boolean) {
    for (const path of paths) {
      for (const existing of Object.keys(rules)) {
        const independent = independentRoots.some(root => root.startsWith(`${path}/`)
          && (existing === root || existing.startsWith(`${root}/`)));
        if (existing.startsWith(`${path}/`) && !independentPaths.has(existing) && !independent) delete rules[existing];
      }
      rules[path] = visible;
    }
    localStorage.setItem(key, JSON.stringify(rules));
    viewer.setVisibility(rules, independentRoots);
    refresh();
  }

  for (const input of inputs) {
    input.addEventListener('change', () => change(categories[input.name], input.checked));
  }

  return {
    restore() {
      viewer.setVisibility(rules, independentRoots);
      refresh();
    },
    resetGroups() { groups.clear(); },
    addGroup(heading: HTMLElement, path: string, title: string) {
      const button = createVisibilityButton(title, () => {
        change([path], rules[path] === false);
      });
      groups.set(button, { path, title });
      heading.append(button);
      refresh();
    },
  };
}
