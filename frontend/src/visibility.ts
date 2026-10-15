import type { ModelStatus } from './api';

const categories: Record<string, string[]> = {
  vehicle: ['/Campervan/Vehicle references/'],
  slats: [
    '/Campervan/Long bench/Sliding bed/Fixed slats/',
    '/Campervan/Long bench/Sliding bed/Sliding assembly/Moving slats/',
  ],
};

export function setupVisibility(container: HTMLElement, iframe: HTMLIFrameElement) {
  const inputs = [...container.querySelectorAll<HTMLInputElement>('input')];
  let paths: string[] = [];
  let publication = '';

  function apply(controls = inputs) {
    const states: Record<string, number[]> = {};
    for (const input of controls) {
      for (const path of paths) {
        if (categories[input.name].some(prefix => path.startsWith(prefix))) {
          states[path] = input.checked ? [1, 1] : [0, 0];
        }
      }
    }
    if (Object.keys(states).length) {
      iframe.contentWindow?.postMessage({ type: 'ui', config: { states } }, new URL(iframe.src).origin);
    }
  }

  for (const input of inputs) {
    const key = `campervan.visibility.${input.name}`;
    input.checked = localStorage.getItem(key) !== 'false';
    input.addEventListener('change', () => {
      localStorage.setItem(key, String(input.checked));
      apply([input]);
    });
  }

  return (model: ModelStatus) => {
    if (model.published_revision === null) return;
    const next = `${model.session_id}:${model.published_revision}`;
    if (next === publication) return;
    publication = next;
    paths = model.model_paths;
    apply();
  };
}
