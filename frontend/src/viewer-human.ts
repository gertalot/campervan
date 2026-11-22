/** First-person camera input, scoped to the focused CAD viewport. */
import { Quaternion, Vector3 } from 'three';
import type { CameraViewer } from './viewer-camera';
import type { PlanMenuItem } from './plan-dropdown';

export interface HumanViewer extends CameraViewer {
  rendered: CameraViewer['rendered'] & { controls: { controls: { enabled: boolean } } };
  setOrtho(value: boolean): void;
}

export function createViewerHuman(container: HTMLElement, current: () => HumanViewer | undefined,
  prepare: () => void, save: () => void, orbitTarget: () => number[]) {
  let active = false, frame = 0, lastTime = 0;
  let requesting = false;
  let previousControls = true;
  const keys = new Set<string>();
  const arrows = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
  const help = 'Mouse: look · ↑/↓: forward/back · ←/→: sideways · Shift+↑/↓: world Z · Esc: exit';
  const tools = document.createElement('span'); tools.className = 'cad-piece-controls cad-human-controls';
  tools.dataset.campervanControl = 'true';
  const tooltip = document.createElement('span'); tooltip.className = 'tcv_tooltip';
  const buttonFrame = document.createElement('span'); buttonFrame.className = 'tcv_button_frame';
  const button = document.createElement('button'); button.type = 'button';
  button.className = 'tcv_reset tcv_btn cad-piece-button';
  button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"'
    + ' stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
    + '<circle cx="12" cy="4" r="2.5"/><path d="M8 21v-7L5 10m11 11v-7l3-4M8 14V9h8v5M12 14v7"/></svg>';
  const hint = document.createElement('div'); hint.className = 'cad-human-hint'; hint.hidden = true;
  hint.id = 'cad-human-help'; hint.textContent = help; hint.setAttribute('role', 'status');
  button.setAttribute('aria-describedby', hint.id);
  buttonFrame.append(button); tooltip.append(buttonFrame); tools.append(tooltip);

  function stop() {
    keys.clear(); lastTime = 0;
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    if (active) save();
  }
  function setActive(value: boolean) {
    const viewer = current();
    if (!value) {
      requesting = false;
      if (document.pointerLockElement === container) document.exitPointerLock();
    }
    if (value === active || (value && (!viewer?.ready || button.disabled))) return;
    stop();
    if (value && viewer) {
      active = true;
      prepare();
      if (viewer.getOrtho()) {
        const position = viewer.getCameraPosition(), target = viewer.getCameraTarget();
        const rotation = viewer.getCameraQuaternion();
        viewer.setOrtho(false);
        // Native switching converts zoom into dolly distance; restore the original eye position.
        viewer.setCameraLocationSettings(position, rotation, target, null, false);
      }
      previousControls = viewer.rendered.controls.controls.enabled;
      viewer.rendered.controls.controls.enabled = false;
    } else if (viewer?.ready) {
      viewer.rendered.controls.controls.enabled = previousControls;
      // Keep the eye and viewing direction; only replace the distant look target.
      viewer.setCameraLocationSettings(viewer.getCameraPosition(), viewer.getCameraQuaternion(), orbitTarget(), null, false);
    }
    active = value;
    button.setAttribute('aria-pressed', String(active)); button.classList.toggle('is-active', active);
    container.classList.toggle('cad-human-view', active); hint.hidden = !active;
    if (active) container.focus({ preventScroll: true });
    save();
  }
  function lockFailed() {
    requesting = false;
    setActive(false);
    hint.textContent = 'Could not capture the mouse. Click Human view to try again.';
    hint.hidden = false;
  }
  function toggle() {
    if (active || requesting) { setActive(false); return; }
    if (!current()?.ready || button.disabled) return;
    requesting = true; hint.textContent = help;
    // Must run directly in the click/key gesture; lock acquisition is asynchronous.
    try {
      Promise.resolve(container.requestPointerLock()).catch(lockFailed);
    } catch { lockFailed(); }
  }
  document.addEventListener('pointerlockchange', () => {
    if (document.pointerLockElement === container) {
      if (requesting || active) { requesting = false; setActive(true); }
      else document.exitPointerLock();
    } else if (active) setActive(false);
  });
  document.addEventListener('pointerlockerror', () => { if (requesting) lockFailed(); });
  function command(): PlanMenuItem {
    return { label: 'Human view', group: 'camera', shortcut: 'H', ariaShortcut: 'H',
      checked: active, enabled: !button.disabled, run: toggle };
  }
  const action = command();
  button.setAttribute('aria-label', action.label); button.setAttribute('aria-keyshortcuts', action.ariaShortcut!);
  button.setAttribute('aria-pressed', 'false');
  button.title = `${action.label} · ${action.shortcut} · ${help}`; tooltip.dataset.tooltip = button.title;
  button.onclick = action.run;

  function focused() {
    return active && document.pointerLockElement === container && document.activeElement === container;
  }
  function forward(viewer: HumanViewer) {
    return new Vector3(0, 0, -1).applyQuaternion(new Quaternion().fromArray(viewer.getCameraQuaternion()));
  }
  function move(now: number) {
    frame = 0;
    const viewer = current();
    if (!focused() || !viewer?.ready) { stop(); return; }
    const dt = lastTime ? Math.min((now - lastTime) / 1000, 0.05) : 0;
    lastTime = now;
    const direction = new Vector3();
    const ahead = Number(keys.has('ArrowUp')) - Number(keys.has('ArrowDown'));
    const sideways = Number(keys.has('ArrowRight')) - Number(keys.has('ArrowLeft'));
    if (keys.has('Shift')) direction.z = ahead;
    else {
      const heading = forward(viewer);
      heading.z = 0;
      direction.addScaledVector(heading.normalize(), ahead);
    }
    direction.addScaledVector(new Vector3(1, 0, 0)
      .applyQuaternion(new Quaternion().fromArray(viewer.getCameraQuaternion())), sideways);
    if (direction.lengthSq() && dt) {
      const offset = direction.normalize().multiplyScalar(500 * dt);
      const position = new Vector3(...viewer.getCameraPosition()).add(offset);
      const target = new Vector3(...viewer.getCameraTarget()).add(offset);
      viewer.setCameraLocationSettings(position.toArray(), viewer.getCameraQuaternion(), target.toArray(), null, false);
    }
    if (arrows.some(key => keys.has(key))) frame = requestAnimationFrame(move);
    else lastTime = 0;
  }
  container.addEventListener('keydown', event => {
    if ((event.target as HTMLElement).closest('input,textarea,select,[contenteditable], [role="menu"]')
      || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key.toLowerCase() === 'h' && !event.repeat) {
      event.preventDefault(); event.stopImmediatePropagation(); command().run(); return;
    }
    if (!focused() || !arrows.includes(event.key)) return;
    event.preventDefault(); event.stopImmediatePropagation(); keys.add(event.key);
    if (event.shiftKey) keys.add('Shift'); else keys.delete('Shift');
    if (!frame) frame = requestAnimationFrame(move);
  }, true);
  window.addEventListener('keydown', event => {
    if (focused() && event.key === 'Shift') keys.add('Shift');
    if (active && event.key === 'Escape' && container.contains(event.target as Node)) {
      event.preventDefault(); event.stopImmediatePropagation(); setActive(false);
    }
  }, true);
  window.addEventListener('keyup', event => {
    keys.delete(event.key);
    if (active && arrows.includes(event.key) && !arrows.some(key => keys.has(key))) stop();
  });
  document.addEventListener('mousemove', event => {
    if (!focused()) return;
    event.stopImmediatePropagation();
    const viewer = current(); if (!viewer?.ready) return;
    const dx = event.movementX, dy = event.movementY;
    if (!dx && !dy) return;
    const direction = forward(viewer);
    const yaw = Math.atan2(direction.y, direction.x) - dx * 0.003;
    const pitch = Math.max(-Math.PI / 2 + 0.01, Math.min(Math.PI / 2 - 0.01,
      Math.asin(Math.max(-1, Math.min(1, direction.z))) - dy * 0.003));
    const position = new Vector3(...viewer.getCameraPosition());
    const distance = Math.max(1, position.distanceTo(new Vector3(...viewer.getCameraTarget())));
    const target = new Vector3(Math.cos(yaw) * Math.cos(pitch), Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch))
      .multiplyScalar(distance).add(position);
    viewer.setCameraLocationSettings(position.toArray(), viewer.getCameraQuaternion(), target.toArray(), null, false);
  }, true);
  // Locked mouse events target the viewport itself, rather than its canvas.
  for (const type of ['pointerdown', 'pointermove', 'click', 'dblclick', 'wheel', 'contextmenu'] as const) {
    container.addEventListener(type, event => {
      if (!active || document.pointerLockElement !== container) return;
      event.preventDefault(); event.stopImmediatePropagation();
    }, { capture: true, passive: false });
  }
  container.addEventListener('focusout', event => {
    if (active && event.relatedTarget !== container) setActive(false);
  });
  window.addEventListener('blur', () => setActive(false));
  document.addEventListener('visibilitychange', () => { if (document.hidden) setActive(false); });
  return {
    isActive: () => active,
    commands: () => [command()],
    cancel: () => setActive(false),
    toolChanged(measuring: boolean) { if (measuring) setActive(false); button.disabled = measuring; },
    attach() { container.querySelector('.tcv_cad_toolbar')?.append(tools); container.append(hint); },
  };
}
