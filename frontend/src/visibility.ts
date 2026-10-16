const categories: Record<string, string[]> = {
  vehicle: ['/Campervan/Vehicle references'],
  cabinet: ['/Campervan/Cabinet'],
  cushions: ['/Campervan/Long bench/Cushions', '/Campervan/Cross bench/Cushions'],
  slats: [
    '/Campervan/Long bench/Fixed frame/Fixed slats',
    '/Campervan/Long bench/Sliding bed/Sliding assembly/Moving slats',
    '/Campervan/Cross bench/Fixed frame/Fixed slats',
    '/Campervan/Cross bench/Fixed frame/Fixed deck',
    '/Campervan/Cross bench/Sliding assembly/Moving slats',
    '/Campervan/Cross bench/Sliding assembly/Extension stops',
    '/Campervan/Cross bench/Storage lid',
  ],
};

interface VisibilityViewer {
  setVisibility(paths: string[], visible: boolean): void;
  getVisibility(paths: string[]): 'shown' | 'hidden' | 'mixed';
}

export function setupVisibility(container: HTMLElement, viewer: VisibilityViewer) {
  const inputs = [...container.querySelectorAll<HTMLInputElement>('input')];
  const groups = new Map<HTMLButtonElement, { path: string; title: string }>();
  const key = 'campervan.visibility.paths';
  const rules: Record<string, boolean> = JSON.parse(localStorage.getItem(key) ?? '{}');
  if (!localStorage.getItem(key)) {
    for (const input of inputs) {
      for (const path of categories[input.name]) {
        rules[path] = localStorage.getItem(`campervan.visibility.${input.name}`) !== 'false';
      }
    }
  }

  function refresh() {
    for (const input of inputs) {
      const state = viewer.getVisibility(categories[input.name]);
      input.checked = state === 'shown';
      input.indeterminate = state === 'mixed';
    }
    for (const [button, { path, title }] of groups) {
      const state = viewer.getVisibility([path]);
      button.dataset.visibility = state;
      button.setAttribute('aria-pressed', state === 'mixed' ? 'mixed' : String(state === 'shown'));
      button.setAttribute('aria-label', `${state === 'shown' ? 'Hide' : 'Show'} ${title}`);
      button.title = `${state === 'shown' ? 'Hide' : 'Show'} ${title}${state === 'mixed' ? ' (partly visible)' : ''}`;
    }
  }

  function change(paths: string[], visible: boolean) {
    for (const path of paths) {
      // A parent toggle replaces its children's overrides.
      for (const existing of Object.keys(rules)) if (existing.startsWith(`${path}/`)) delete rules[existing];
      rules[path] = visible;
    }
    localStorage.setItem(key, JSON.stringify(rules));
    viewer.setVisibility(paths, visible);
    refresh();
  }

  for (const input of inputs) {
    input.addEventListener('change', () => change(categories[input.name], input.checked));
  }

  return {
    restore() {
      // Apply parent choices before explicit child choices.
      for (const path of Object.keys(rules).sort((a, b) => a.split('/').length - b.split('/').length)) {
        viewer.setVisibility([path], rules[path]);
      }
      refresh();
    },
    resetGroups() { groups.clear(); },
    addGroup(heading: HTMLElement, path: string, title: string) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'group-visibility';
      button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/><path class="eye-slash" d="m3 3 18 18"/></svg>';
      groups.set(button, { path, title });
      button.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        change([path], viewer.getVisibility([path]) !== 'shown');
      });
      heading.append(button);
      refresh();
    },
  };
}
