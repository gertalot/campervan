export type Tab = 'cad' | 'bom' | 'plan' | 'cuts';
const tabs = ['cad', 'bom', 'plan', 'cuts'] as const;
type Listener = (tab: Tab, role?: string) => void;
let current: Tab = 'cad';
let currentRole: string | undefined;
const listeners = new Set<Listener>();
export function onTab(listener: Listener) {
  listeners.add(listener); listener(current, currentRole);
  return () => { listeners.delete(listener); };
}
export function showTab(tab: Tab, role?: string, history = true) {
  current = tab; currentRole = role;
  for (const name of tabs) {
    const panel = document.getElementById(`${name}-panel`)!;
    if (name === 'cad') { panel.style.visibility = tab === 'cad' ? '' : 'hidden'; panel.inert = tab !== 'cad'; }
    else panel.hidden = name !== tab;
    document.getElementById(`${name}-tab`)!.setAttribute('aria-pressed', String(name === tab));
    document.getElementById(`${name}-tab`)!.setAttribute('aria-selected', String(name === tab));
    document.getElementById(`${name}-tab`)!.tabIndex = name === tab ? 0 : -1;
  }
  document.getElementById('workspace')!.classList.toggle('show-bom', tab !== 'cad');
  if (history) {
    const path = tab === 'bom' && role ? `/bom/${encodeURIComponent(role)}` : `/${tab}`;
    if (path !== location.pathname) window.history.pushState(null, '', path);
  }
  listeners.forEach(fn => fn(tab, role));
}
export function setupTabs() {
  const navigation = document.querySelector('nav[aria-label="Project views"]')!;
  navigation.setAttribute('role', 'tablist');
  for (const tab of tabs) {
    const button = document.getElementById(`${tab}-tab`)!;
    button.setAttribute('role', 'tab');
    button.onclick = () => showTab(tab);
    const panel = document.getElementById(`${tab}-panel`)!;
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', `${tab}-tab`);
    button.addEventListener('keydown', event => {
      let index = tabs.indexOf(tab);
      if (event.key === 'ArrowRight') index = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') index = (index + tabs.length - 1) % tabs.length;
      else if (event.key === 'Home') index = 0;
      else if (event.key === 'End') index = tabs.length - 1;
      else return;
      event.preventDefault(); showTab(tabs[index]); document.getElementById(`${tabs[index]}-tab`)!.focus();
    });
  }
  const restore = () => {
    const match = location.pathname.match(/^\/(cad|bom|plan|cuts)(?:\/([^/]+))?\/?$/);
    showTab((match?.[1] as Tab) ?? 'cad', match?.[2] ? decodeURIComponent(match[2]) : undefined, false);
    if (location.pathname === '/') history.replaceState(null, '', '/cad');
  };
  window.addEventListener('popstate', restore); restore();
}
