/** Shared nonmodal shell; callers own content, actions and domain state, not dismissal behavior. */
export interface SidePanel {
  element: HTMLDialogElement; context: HTMLElement; actions: HTMLElement; status: HTMLElement; body: HTMLElement;
  closeButton: HTMLButtonElement;
  open(): void;
  close(options?: { focus?: HTMLElement; restoreFocus?: boolean }): void;
  readonly isOpen: boolean;
}
let active: SidePanel | undefined;
export function createSidePanel(options: {
  id: string; title: string; onClose?(): void;
}): SidePanel {
  const element = document.createElement('dialog'); element.id = options.id; element.className = 'side-panel';
  // Both panels dismiss through outside clicks, Escape or X without blocking the canvas.
  // https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog#closedby
  element.setAttribute('closedby', 'any');
  element.setAttribute('aria-labelledby', `${options.id}-title`);
  const header = document.createElement('div'); header.className = 'side-panel-header';
  const title = document.createElement('h2'); title.id = `${options.id}-title`; title.textContent = options.title;
  const closeButton = document.createElement('button'); closeButton.type = 'button'; closeButton.className = 'side-panel-close';
  const closeName = `Close ${options.title.replace(/^Manage /, '').toLowerCase()}`;
  closeButton.setAttribute('aria-label', closeName); closeButton.title = closeName;
  closeButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>';
  header.append(title, closeButton);
  const context = document.createElement('div'); context.className = 'side-panel-context';
  const actions = document.createElement('div'); actions.className = 'side-panel-actions';
  const status = document.createElement('div'); status.className = 'side-panel-status';
  status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const body = document.createElement('div'); body.className = 'side-panel-body';
  element.append(header, context, actions, status, body); document.body.append(element);
  let returnFocus: HTMLElement | null = null;
  let closingFocus: HTMLElement | null | undefined;
  const panel: SidePanel = {
    element, context, actions, status, body, closeButton,
    get isOpen() { return element.open; },
    open() {
      if (element.open) return;
      active?.close({ restoreFocus: false });
      returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      closingFocus = undefined; active = panel;
      element.show();
    },
    close(settings = {}) {
      if (!element.open) return;
      closingFocus = settings.restoreFocus === false ? null : settings.focus ?? returnFocus;
      element.close();
    },
  };
  closeButton.onclick = () => panel.close();
  element.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !event.defaultPrevented && !event.isComposing) {
      event.preventDefault(); event.stopPropagation(); panel.close();
    }
  });
  element.addEventListener('close', () => {
    if (active === panel) active = undefined;
    options.onClose?.();
    (closingFocus === undefined ? returnFocus : closingFocus)?.focus({ preventScroll: true });
    closingFocus = undefined;
  });
  return panel;
}
