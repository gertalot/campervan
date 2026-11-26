/** The paint bucket owns its gestures and applies saved finishes to each new CAD scene. */
import type { Intersection } from 'three';
import type { ScanPaintPanel } from './scan-panels';
import { request } from './api';
import { ariaShortcut, isMac, shortcutLabel } from './keyboard-shortcuts';
import { createPaintPicker, paintCommandLabel, paintShortcut } from './paint-picker';
import { createPaintSurface, type PaintFace } from './paint-surface';
import type { PaintSwatch } from './paint-swatch';
import { paintTarget } from './paint-target';
import type { PlanMenuItem } from './plan-dropdown';
import { isStaticSite } from './site-runtime';
import { highlightPiece } from './viewer-highlight';

interface PaintState {
  assignments: Record<string, PaintSwatch>; favourites: PaintSwatch[];
  can_undo: boolean; can_redo: boolean;
}
const historyActions = [
  { direction: 'undo', label: 'Undo paint', key: 'Mod-z' },
  { direction: 'redo', label: 'Redo paint', key: 'Mod-Shift-z' },
] as const;
interface PaintHost {
  pick(event: MouseEvent, sample?: boolean): { path: string; hit?: Intersection } | null;
  modeChanged(active: boolean): void;
  redraw(): void;
  error(message: string): void;
}

export function createViewerPaint(container: HTMLElement, host: PaintHost) {
  let state: PaintState | undefined;
  let surface: ReturnType<typeof createPaintSurface> | undefined;
  let paintPanels: ScanPaintPanel[] = [];
  let mode: 'paint' | 'sample' | null = null;
  let resumePaint = false, measuring = false;
  let hover: string | null = null;
  let outlines: (() => void)[] = [];
  let down: { x: number; y: number; id: number; moved: boolean } | undefined;
  let pointer: PointerEvent | undefined;
  let frame = 0;
  let writes = Promise.resolve();
  let pendingPaint = 0;
  let savedFavourites: PaintSwatch[] = [];

  const picker = createPaintPicker({
    onToggle: toggle,
    onSample() {
      if (!available() || mode === 'sample') return;
      resumePaint = mode === 'paint';
      setMode('sample');
    },
    historyCommands,
    used: () => surface?.used() ?? [],
    favourites: () => state?.favourites ?? [],
    onFavourites(favourites) {
      if (!state || isStaticSite) return;
      state.favourites = favourites;
      enqueue(async () => {
        try {
          await request('paint/favourites', 'PUT', { favourites });
          savedFavourites = favourites;
        } catch (error) {
          if (state?.favourites === favourites) state.favourites = savedFavourites;
          throw error;
        }
      });
    },
  });

  function enqueue(save: () => Promise<void>) {
    writes = writes.then(save).catch(error => host.error(`Could not save paint. ${String(error)}`));
  }
  function available() { return Boolean(surface && state && !measuring && !isStaticSite); }
  function updateControls() { picker.setDisabled(!available()); picker.updateHistory(); }
  function clearPointer() {
    down = undefined;
    pointer = undefined;
    cancelAnimationFrame(frame);
    frame = 0;
    preview(null);
  }
  function setMode(next: typeof mode) {
    if (next === mode) return;
    const wasActive = Boolean(mode);
    mode = next;
    picker.close();
    picker.setBucketActive(mode === 'paint');
    container.classList.toggle('cad-painting', Boolean(mode));
    clearPointer();
    if (wasActive !== Boolean(mode)) host.modeChanged(Boolean(mode));
    container.focus({ preventScroll: true });
  }
  function cancel() {
    picker.close();
    setMode(null);
  }
  function toggle() {
    if (available()) setMode(mode === 'paint' ? null : 'paint');
  }
  function finishSample(swatch?: PaintSwatch) {
    setMode(resumePaint ? 'paint' : null);
    picker.finishSample(swatch);
  }
  function preview(target: string | null) {
    if (hover === target) return;
    for (const remove of outlines) remove();
    hover = target;
    const members = target && surface ? surface.members(target) : [];
    outlines = members.map(member => highlightPiece(member, '#29dbf0', 'paint'));
    host.redraw();
  }
  function targetAt(event: MouseEvent) {
    const hit = host.pick(event);
    return hit ? surface?.targetFor(hit.path) ?? null : null;
  }
  function paint(target: string) {
    const swatch = { ...picker.swatch() };
    changePaint(() => request<PaintState>('paint/assignment', 'PUT', { target, swatch }));
  }
  function changePaint(save: () => Promise<PaintState>) {
    pendingPaint++;
    updateControls();
    enqueue(async () => {
      try {
        const saved = await save();
        state = { ...saved, favourites: state!.favourites };
        surface?.apply(state.assignments);
        host.redraw();
      } finally {
        pendingPaint--;
        updateControls();
      }
    });
  }
  function historyCommands(): PlanMenuItem[] {
    return historyActions.map(({ direction, label, key }) => ({
      label, group: 'paint', shortcut: shortcutLabel(key), ariaShortcut: ariaShortcut(key),
      enabled: available() && (pendingPaint > 0 || Boolean(direction === 'undo' ? state?.can_undo : state?.can_redo)),
      run() {
        if (!available()) return;
        container.focus({ preventScroll: true });
        clearPointer();
        changePaint(() => request<PaintState>('paint/history/' + direction, 'POST'));
      },
    }));
  }
  container.addEventListener('pointermove', event => {
    if (!mode) return;
    if (down && event.pointerId === down.id && Math.hypot(event.clientX - down.x, event.clientY - down.y) > 4) {
      down.moved = true;
    }
    if (!(event.target instanceof HTMLCanvasElement) || event.buttons || event.altKey) {
      pointer = undefined;
      preview(null);
      return;
    }
    pointer = event;
    if (!frame) frame = requestAnimationFrame(() => {
      frame = 0;
      if (mode === 'paint' && pointer) preview(targetAt(pointer));
    });
  }, true);
  container.addEventListener('pointerleave', clearPointer);
  container.addEventListener('pointercancel', clearPointer);
  container.addEventListener('pointerdown', event => {
    if (!mode || !(event.target instanceof HTMLCanvasElement)) return;
    container.focus({ preventScroll: true });
    clearPointer();
    if (event.isPrimary && event.button === 0 && !event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
      down = { x: event.clientX, y: event.clientY, id: event.pointerId, moved: false };
    }
  }, true);
  container.addEventListener('click', event => {
    if (!mode || !(event.target instanceof HTMLCanvasElement) || event.button !== 0) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const start = down;
    down = undefined;
    if (!start || start.moved || Math.hypot(event.clientX - start.x, event.clientY - start.y) > 4) return;
    if (mode === 'sample') {
      const picked = host.pick(event, true);
      const swatch = picked && surface?.sample(picked.path, picked.hit);
      if (swatch) finishSample(swatch);
      return;
    }
    const target = targetAt(event);
    preview(target);
    if (target) paint(target);
  }, true);
  container.addEventListener('keydown', event => {
    if (event.defaultPrevented || container.closest('[inert]')) return;
    if (event.key.toLowerCase() === 'z' && !event.altKey
      && (isMac() ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey)
      && (event.target === container || event.target instanceof HTMLCanvasElement
        || (event.target instanceof Element && event.target.closest('.cad-paint-controls')))) {
      const command = historyCommands()[event.shiftKey ? 1 : 0];
      if (!command.enabled) return;
      event.preventDefault(); event.stopImmediatePropagation(); command.run(); return;
    }
    if (event.repeat || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey
      || event.target !== container) return;
    if (event.key.toUpperCase() === paintShortcut && available()) toggle();
    else if (event.key === 'Escape' && mode === 'sample') finishSample();
    else if (event.key === 'Escape' && mode) cancel();
    else return;
    event.preventDefault(); event.stopImmediatePropagation();
  }, true);

  return {
    isActive: () => Boolean(mode),
    commands: (): PlanMenuItem[] => isStaticSite ? [] : [{
      label: paintCommandLabel, group: 'paint', shortcut: paintShortcut, ariaShortcut: paintShortcut,
      checked: mode === 'paint', enabled: available(), run: toggle,
    }, ...historyCommands()],
    cancel,
    clearPointer,
    async load() {
      try {
        state = await request<PaintState>('paint');
        savedFavourites = state.favourites;
        surface?.apply(state.assignments);
        host.redraw();
        updateControls();
      } catch (error) { host.error(`Could not load paint. ${String(error)}`); }
    },
    setScanPaintPanels(panels: ScanPaintPanel[]) {
      paintPanels = panels;
      surface?.setScanPaintPanels(panels);
      if (state) surface?.apply(state.assignments);
    },
    attach(groups: Record<string, unknown>, stockTextures: Record<string, string>, duvet: PaintFace) {
      surface = createPaintSurface(groups, paintTarget, host.redraw, stockTextures, duvet);
      surface.setScanPaintPanels(paintPanels);
      if (state) surface.apply(state.assignments);
      if (!isStaticSite) container.querySelector('.tcv_cad_toolbar')?.append(picker.element);
      updateControls();
    },
    detach() {
      clearPointer();
      surface?.dispose();
      surface = undefined;
      updateControls();
    },
    toolChanged(usingMeasurement: boolean) {
      measuring = usingMeasurement;
      if (measuring) cancel();
      updateControls();
    },
  };
}
