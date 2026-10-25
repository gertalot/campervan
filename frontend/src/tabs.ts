export type Tab = 'cad' | 'bom' | 'plan';
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
  for (const name of ['cad', 'bom', 'plan'] as const) {
    const panel = document.getElementById(`${name}-panel`)!;
    if (name === 'cad') { panel.style.visibility = tab === 'cad' ? '' : 'hidden'; panel.inert = tab !== 'cad'; }
    else panel.hidden = name !== tab;
    document.getElementById(`${name}-tab`)!.setAttribute('aria-pressed', String(name === tab));
  }
  document.getElementById('workspace')!.classList.toggle('show-bom', tab !== 'cad');
  if (history) {
    const path = tab === 'bom' && role ? `/bom/${encodeURIComponent(role)}` : `/${tab}`;
    if (path !== location.pathname) window.history.pushState(null, '', path);
  }
  listeners.forEach(fn => fn(tab, role));
}
export function setupTabs() {
  for (const tab of ['cad', 'bom', 'plan'] as const) document.getElementById(`${tab}-tab`)!.onclick = () => showTab(tab);
  const restore = () => {
    const match = location.pathname.match(/^\/(cad|bom|plan)(?:\/([^/]+))?\/?$/);
    showTab((match?.[1] as Tab) ?? 'cad', match?.[2] ? decodeURIComponent(match[2]) : undefined, false);
    if (location.pathname === '/') history.replaceState(null, '', '/cad');
  };
  window.addEventListener('popstate', restore); restore();
}
