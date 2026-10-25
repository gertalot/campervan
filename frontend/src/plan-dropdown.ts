import { el } from './purchase-grid';

export type PlanMenuItem = {
  label: string; group: string; run: () => void;
  shortcut?: string; ariaShortcut?: string; enabled?: boolean; checked?: boolean; danger?: boolean;
};
type DropdownRequest = {
  label: string; items: PlanMenuItem[]; trigger?: HTMLElement; x?: number; y?: number;
  initial?: 'first' | 'last'; className?: string; onClose?: () => void; returnFocus?: () => void;
};

/** The File menu and editor menus share the same popup, focus and dismissal behaviour. */
export function createPlanDropdown() {
  let popup: HTMLDivElement | null = null;
  let active: DropdownRequest | null = null;
  const close = (restoreFocus = false) => {
    if (!active) return;
    const previous = active; active = null;
    popup?.remove(); popup = null;
    previous.trigger?.setAttribute('aria-expanded', 'false'); previous.trigger?.removeAttribute('aria-controls');
    previous.onClose?.();
    if (restoreFocus) {
      if (previous.returnFocus) previous.returnFocus();
      else if (previous.trigger?.isConnected) previous.trigger.focus({ preventScroll: true });
    }
  };
  const outside = (event: PointerEvent) => {
    if (popup && !popup.contains(event.target as Node) && !active?.trigger?.contains(event.target as Node)) close();
  };
  const scroll = (event: Event) => { if (popup && !popup.contains(event.target as Node)) close(); };
  const dismiss = () => close();
  document.addEventListener('pointerdown', outside);
  document.addEventListener('scroll', scroll, true);
  window.addEventListener('resize', dismiss); window.addEventListener('blur', dismiss);

  const open = (request: DropdownRequest) => {
    if (active?.trigger === request.trigger && request.trigger) { close(true); return; }
    close(); active = request;
    popup = el('div'); popup.className = 'plan-context-menu' + (request.className ? ' ' + request.className : '');
    popup.id = 'plan-menu-' + crypto.randomUUID(); popup.setAttribute('role', 'menu');
    popup.setAttribute('aria-label', request.label);
    const buttons: HTMLButtonElement[] = [];
    let group: string | undefined; let typeahead = ''; let typedAt = 0;
    for (const item of request.items) {
      if (group !== undefined && item.group !== group) {
        const line = el('div'); line.setAttribute('role', 'separator'); line.className = 'menu-separator'; popup.append(line);
      }
      group = item.group;
      const button = el('button'); button.type = 'button'; button.tabIndex = -1;
      button.setAttribute('role', item.checked === undefined ? 'menuitem' : 'menuitemcheckbox');
      if (item.checked !== undefined) button.setAttribute('aria-checked', String(item.checked));
      button.setAttribute('aria-disabled', String(item.enabled === false));
      if (item.danger) button.classList.add('is-destructive');
      if (item.ariaShortcut) button.setAttribute('aria-keyshortcuts', item.ariaShortcut);
      button.append(el('span', item.checked ? '✓' : ''), el('span', item.label), el('kbd', item.shortcut ?? ''));
      button.onmousedown = event => event.preventDefault();
      button.onpointermove = () => button.focus({ preventScroll: true });
      button.onclick = () => { if (item.enabled !== false) { close(true); item.run(); } };
      popup.append(button); buttons.push(button);
    }
    popup.onkeydown = event => {
      const at = buttons.indexOf(document.activeElement as HTMLButtonElement);
      let next = -1;
      if (event.key === 'ArrowDown') next = (at + 1) % buttons.length;
      else if (event.key === 'ArrowUp') next = (at - 1 + buttons.length) % buttons.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = buttons.length - 1;
      else if (event.key === 'Escape') { event.preventDefault(); close(true); return; }
      else if (event.key === 'Tab') { close(true); return; }
      else if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); buttons[at]?.click(); return; }
      else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
        const letter = event.key.toLowerCase();
        typeahead = Date.now() - typedAt > 600 ? letter : typeahead + letter; typedAt = Date.now();
        const prefix = [...typeahead].every(char => char === letter) ? letter : typeahead;
        for (let step = 1; step <= buttons.length; step++) {
          const index = (at + step) % buttons.length;
          if (request.items[index].label.toLowerCase().startsWith(prefix)) { next = index; break; }
        }
      }
      if (next >= 0) { event.preventDefault(); buttons[next].focus(); }
    };
    popup.onfocusout = () => queueMicrotask(() => {
      if (popup && !popup.contains(document.activeElement) && document.activeElement !== active?.trigger) close();
    });
    document.body.append(popup);
    const rect = request.trigger?.getBoundingClientRect();
    const left = request.x ?? rect?.left ?? 8;
    let top = request.y ?? (rect ? rect.bottom + 4 : 8);
    if (rect && request.y === undefined && top + popup.offsetHeight > window.innerHeight - 8
        && rect.top > window.innerHeight - rect.bottom) top = rect.top - popup.offsetHeight - 4;
    popup.style.left = `${Math.max(8, Math.min(left, window.innerWidth - popup.offsetWidth - 8))}px`;
    popup.style.top = `${Math.max(8, Math.min(top, window.innerHeight - popup.offsetHeight - 8))}px`;
    request.trigger?.setAttribute('aria-expanded', 'true'); request.trigger?.setAttribute('aria-controls', popup.id);
    (request.initial === 'last' ? buttons.at(-1) : buttons[0])?.focus({ preventScroll: true });
  };
  return {
    open, close,
    isOpen: (trigger?: HTMLElement) => Boolean(active && trigger && active.trigger === trigger),
    destroy() {
      close(); document.removeEventListener('pointerdown', outside); document.removeEventListener('scroll', scroll, true);
      window.removeEventListener('resize', dismiss); window.removeEventListener('blur', dismiss);
    },
  };
}
