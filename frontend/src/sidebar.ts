/** Resize the sidebar without interfering with the viewer iframe. */
export function setupSidebarResize(handle: HTMLElement, sidebar: HTMLElement) {
  const storageKey = 'campervan.sidebar.width';
  const minimum = 220;
  let dragOffset = 0;
  const maximum = () => Math.max(minimum, Math.min(520, window.innerWidth - 160));

  function setWidth(width: number) {
    const value = Math.round(Math.max(minimum, Math.min(maximum(), width)));
    document.documentElement.style.setProperty('--sidebar-width', `${value}px`);
    handle.setAttribute('aria-valuemin', String(minimum));
    handle.setAttribute('aria-valuemax', String(maximum()));
    handle.setAttribute('aria-valuenow', String(value));
  }

  function saveWidth() {
    localStorage.setItem(storageKey, String(sidebar.getBoundingClientRect().width));
  }

  const saved = Number(localStorage.getItem(storageKey));
  setWidth(Number.isFinite(saved) && saved > 0 ? saved : 280);
  handle.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    event.preventDefault();
    dragOffset = sidebar.getBoundingClientRect().width - event.clientX;
    handle.setPointerCapture(event.pointerId);
    handle.focus();
    document.body.classList.add('resizing-sidebar');
  });
  handle.addEventListener('pointermove', event => {
    if (handle.hasPointerCapture(event.pointerId)) setWidth(event.clientX + dragOffset);
  });
  handle.addEventListener('lostpointercapture', () => {
    document.body.classList.remove('resizing-sidebar');
    saveWidth();
  });
  handle.addEventListener('keydown', event => {
    const width = sidebar.getBoundingClientRect().width;
    const step = event.shiftKey ? 40 : 10;
    const values: Record<string, number> = {
      ArrowLeft: width - step, ArrowRight: width + step, Home: minimum, End: maximum(),
    };
    if (!(event.key in values)) return;
    event.preventDefault();
    setWidth(values[event.key]);
    saveWidth();
  });
  window.addEventListener('resize', () => setWidth(sidebar.getBoundingClientRect().width));
}
