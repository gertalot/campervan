/** Pointer gestures for the existing constrained assembly motions. */
import {
  DoubleSide, EdgesGeometry, LineBasicMaterial, LineSegments, Mesh, MeshBasicMaterial, Raycaster, Vector2, Vector3,
  type Camera, type Object3D,
} from 'three';
import type { PlanMenuItem } from './plan-dropdown';
import { createTableDrag } from './table-drag';
import type { PieceViewer } from './viewer-pieces';

export interface Track {
  path: string; axis: 'x' | 'y' | 'z'; kind?: 'rotation' | 'translation'; travel?: number;
  keyframes?: [number, number][]; interpolation?: 'linear' | 'step';
}
export interface Motion { position: number; tracks: Track[] }
export interface DragSnapshot { positions: Record<string, number>; returnMountedTable: boolean }
export interface DragHost {
  viewer(): PieceViewer | undefined;
  motions(): Record<string, Motion>;
  pose(): Record<string, number>;
  pick(event: MouseEvent): { path: string; point: Vector3 } | null;
  preview(patch: Record<string, number>): Record<string, number>;
  save(): void;
  snapshot(): DragSnapshot;
  restore(snapshot: DragSnapshot): void;
}
type Patch = Record<string, number>;
type Target = {
  kind: 'linear' | 'hinge' | 'table'; path: string; label: string; group: Object3D;
  field?: string; track?: Track; point: Vector3;
};
type Solver = {
  solve(x: number, y: number, current: Patch): Patch | null;
  rebase(x: number, y: number, current: Patch): void;
  hint?: string;
  atLimit?: boolean;
};
type Gesture = {
  id: number; canvas: HTMLCanvasElement; target: Target; snapshot: DragSnapshot; solver: Solver;
  downX: number; downY: number; x: number; y: number; active: boolean; dirty: boolean;
  pending: Patch | null;
};
const TABLE_ARM = '/Campervan/Laptop table/Bench mount/Height adjustment/Arm orientation/Swivel arm';
const TABLE_TOP = `${TABLE_ARM}/Tabletop rotation`;
const TABLE_WOOD = `${TABLE_TOP}/Offset tabletop`;
const CYAN = '#29dbf0';
const clamp = (value: number) => Math.max(0, Math.min(100, value));
const under = (path: string, parent: string) => path === parent || path.startsWith(`${parent}/`);

function screen(point: Vector3, camera: Camera, rect: DOMRect) {
  const projected = point.clone().project(camera);
  return new Vector2(rect.left + (projected.x + 1) * rect.width / 2,
    rect.top + (1 - projected.y) * rect.height / 2);
}

function linearSolver(target: Target, camera: Camera, rect: DOMRect, x: number, y: number,
  pose: Patch): Solver {
  const field = target.field!, track = target.track!;
  const axis = new Vector3(); axis[track.axis] = 1;
  target.group.parent?.updateWorldMatrix(true, false);
  if (target.group.parent) axis.transformDirection(target.group.parent.matrixWorld);
  const frames = track.keyframes;
  const travel = track.travel ?? (frames ? frames[frames.length - 1][1] - frames[0][1] : 0);
  axis.multiplyScalar(Math.sign(travel) || 1);
  const length = Math.abs(travel), stage = field === 'bed_extension_percent' ? 40 : 100;
  const ray = new Raycaster();
  function distance(clientX: number, clientY: number) {
    ray.setFromCamera(new Vector2((clientX - rect.left) / rect.width * 2 - 1,
      1 - (clientY - rect.top) / rect.height * 2), camera);
    const parallel = ray.ray.direction.dot(axis), divisor = 1 - parallel * parallel;
    if (divisor < 0.01 || length < 0.001) return null;
    const offset = ray.ray.origin.clone().sub(target.point);
    return (offset.dot(axis) - parallel * offset.dot(ray.ray.direction)) / divisor;
  }
  let anchor = distance(x, y), value = pose[field];
  const solver: Solver = {
    solve(clientX, clientY) {
      const at = distance(clientX, clientY);
      if (at === null || anchor === null) {
        solver.hint = 'Rotate the view to see the direction of travel'; return null;
      }
      solver.hint = undefined;
      const raw = value + (at - anchor) / length * stage;
      solver.atLimit = raw < 0 || raw > 100;
      return { [field]: clamp(raw) };
    },
    rebase(clientX, clientY, current) { anchor = distance(clientX, clientY); value = current[field]; },
  };
  return solver;
}

function hingeSolver(target: Target, camera: Camera, rect: DOMRect, x: number, y: number,
  pose: Patch): Solver {
  const field = target.field!, track = target.track!, initial = pose[field];
  target.group.updateWorldMatrix(true, false);
  const pivot = target.group.getWorldPosition(new Vector3()), axis = new Vector3(); axis[track.axis] = 1;
  if (target.group.parent) axis.transformDirection(target.group.parent.matrixWorld);
  const radius = target.point.clone().sub(pivot), radians = (track.travel ?? 0) * Math.PI / 180 / 100;
  const projected = (value: number) => screen(radius.clone().applyAxisAngle(axis, (value - initial) * radians)
    .add(pivot), camera, rect);
  let anchor = projected(initial), pointer = new Vector2(x, y);
  const solver: Solver = {
    solve(clientX, clientY, current) {
      const wanted = anchor.clone().add(new Vector2(clientX, clientY).sub(pointer));
      let value = current[field];
      solver.atLimit = false;
      for (let step = 0; step < 8; step++) {
        const here = projected(value);
        const lower = Math.max(0, value - 0.5), upper = Math.min(100, value + 0.5);
        const tangent = projected(upper).sub(projected(lower)).divideScalar(upper - lower);
        if (tangent.lengthSq() < 0.04) {
          solver.hint = 'Rotate the view to see the hinge movement'; return null;
        }
        const delta = wanted.clone().sub(here).dot(tangent) / tangent.lengthSq();
        const raw = value + Math.max(-15, Math.min(15, delta));
        solver.atLimit ||= raw < 0 || raw > 100;
        const next = clamp(raw);
        if (Math.abs(next - value) < 0.01) break;
        value = next;
      }
      solver.hint = undefined; return { [field]: value };
    },
    rebase(clientX, clientY, current) {
      anchor = projected(current[field]); pointer = new Vector2(clientX, clientY);
    },
  };
  return solver;
}

export function createViewerDrag(container: HTMLElement, host: DragHost) {
  let gesture: Gesture | null = null, hover: Target | null = null, latestHover: PointerEvent | null = null;
  let frame = 0, attached = false, orbit = false, suppressClickUntil = 0;
  let removeOverlay: (() => void) | undefined;
  const hint = document.createElement('div'); hint.className = 'cad-drag-hint'; hint.hidden = true;
  hint.setAttribute('role', 'status'); hint.setAttribute('aria-live', 'polite');
  const tools = document.createElement('span'); tools.className = 'cad-piece-controls cad-drag-controls';
  tools.dataset.campervanControl = 'true';
  const tooltip = document.createElement('span'); tooltip.className = 'tcv_tooltip';
  const buttonFrame = document.createElement('span'); buttonFrame.className = 'tcv_button_frame';
  const orbitButton = document.createElement('button'); orbitButton.type = 'button';
  orbitButton.className = 'tcv_reset tcv_btn cad-piece-button';
  orbitButton.setAttribute('aria-keyshortcuts', 'O');
  orbitButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"'
    + ' stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
    + '<ellipse cx="12" cy="12" rx="9" ry="5" transform="rotate(-30 12 12)"/>'
    + '<path d="m18 3 3 3-4 1M7 21l-4-2 2-3"/><circle cx="12" cy="12" r="2"/></svg>';
  buttonFrame.append(orbitButton); tooltip.append(buttonFrame); tools.append(tooltip);
  function setOrbit(value: boolean) {
    cancel(); orbit = value; orbitButton.setAttribute('aria-pressed', String(orbit));
    orbitButton.classList.toggle('is-active', orbit);
    const label = `Orbit camera over movable parts · O · Alt-drag also orbits`;
    orbitButton.setAttribute('aria-label', 'Orbit camera over movable parts');
    orbitButton.title = label; tooltip.dataset.tooltip = label;
    container.classList.toggle('cad-orbit-override', orbit);
  }
  orbitButton.onclick = () => setOrbit(!orbit);
  setOrbit(false);

  function targetAt(event: MouseEvent): Target | null {
    const viewer = host.viewer(); if (!viewer?.ready) return null;
    const state = (viewer as PieceViewer & { state?: { get(name: string): unknown } }).state;
    if (state?.get('activeTool') || state?.get('animationMode') === 'explode') return null;
    const hit = host.pick(event); if (!hit) return null;
    const groups = viewer.rendered.nestedGroup.groups;
    if (under(hit.path, TABLE_WOOD) && /\/(Fixed|Folding) bamboo leaf(?:\/|$)/.test(hit.path)
      && host.pose().table_mount === 0 && groups[TABLE_ARM]) {
      return { kind: 'table', path: TABLE_ARM, label: 'Steer table', group: groups[TABLE_ARM], point: hit.point };
    }
    for (const [field, motion] of Object.entries(host.motions())) {
      const track = motion.tracks.find(item => under(hit.path, item.path)); if (!track) continue;
      const group = groups[track.path]; if (!group) continue;
      if (field === 'bed_extension_percent' && track.path.includes('/Long bench/Sliding bed/Sliding assembly')) {
        return { kind: 'linear', field, track, path: track.path, label: 'Convert bed', group, point: hit.point };
      }
      if (field === 'drawer_extension_percent' && track.path.endsWith('/Rear drawer/Tray')) {
        return { kind: 'linear', field, track, path: track.path, label: 'Extend drawer', group, point: hit.point };
      }
      if (track.kind === 'rotation' && track.path.includes('/Cabinet/Doors/')) {
        return { kind: 'hinge', field, track, path: track.path,
          label: `Open ${track.path.split('/').at(-1)}`, group, point: hit.point };
      }
    }
    return null;
  }

  function overlay(target: Target | null, active = false) {
    removeOverlay?.(); removeOverlay = undefined;
    if (!target) { if (host.viewer()?.ready) host.viewer()!.update(true, false); return; }
    const fronts = new Set<Mesh>(), fallback = new Set<Mesh>();
    target.group.traverse(object => {
      if (object.userData.campervanOverlay) return;
      const front = (object as Object3D & { front?: Mesh }).front;
      if (front && !front.userData.campervanOverlay) fronts.add(front);
      if (object instanceof Mesh) fallback.add(object);
    });
    const dispose: (() => void)[] = [];
    for (const source of fronts.size ? fronts : fallback) {
      if (!source.parent || source.userData.campervanOverlay) continue;
      const material = new MeshBasicMaterial({ color: CYAN, side: DoubleSide, transparent: true,
        opacity: active ? 0.42 : 0.13, depthTest: false, depthWrite: false, toneMapped: false });
      const surface = new Mesh(source.geometry, material);
      const edges = new EdgesGeometry(source.geometry, 35);
      const lineMaterial = new LineBasicMaterial({ color: CYAN, transparent: true,
        opacity: active ? 1 : 0.85, depthTest: false, depthWrite: false, toneMapped: false });
      const outline = new LineSegments(edges, lineMaterial);
      for (const object of [surface, outline]) {
        object.position.copy(source.position); object.quaternion.copy(source.quaternion); object.scale.copy(source.scale);
        object.userData.campervanOverlay = true; object.raycast = () => {};
        object.renderOrder = active ? 10003 : 10002; source.parent.add(object);
      }
      dispose.push(() => {
        surface.removeFromParent(); outline.removeFromParent(); material.dispose(); edges.dispose(); lineMaterial.dispose();
      });
    }
    removeOverlay = () => dispose.forEach(remove => remove());
    host.viewer()?.update(true, false);
  }

  function showHint(text: string, x: number, y: number) {
    hint.hidden = false;
    if (hint.textContent !== text) hint.textContent = text;
    const rect = container.getBoundingClientRect();
    hint.style.left = `${Math.max(12, Math.min(x - rect.left + 18, rect.width - hint.offsetWidth - 12))}px`;
    hint.style.top = `${Math.max(48, Math.min(y - rect.top + 20, rect.height - hint.offsetHeight - 48))}px`;
  }
  function clearHover() {
    hover = null; latestHover = null; overlay(null); hint.hidden = true;
    container.classList.remove('cad-can-drag', 'cad-is-dragging');
  }
  function describe(target: Target, pose: Patch) {
    if (target.kind === 'table') return `Arm ${Math.round(pose.table_arm_swivel_deg)}° · Top ${Math.round(pose.table_top_rotation_deg)}°`;
    const percent = pose[target.field!];
    if (target.field === 'bed_extension_percent') {
      const stage = percent < 40 ? 'Extend frame' : percent < 80 ? 'Position cushions' : 'Lower backrests';
      return `${stage} · ${Math.round(percent)}%`;
    }
    return `${target.label} · ${Math.round(percent)}%`;
  }
  function makeSolver(target: Target, event: PointerEvent): Solver | null {
    const viewer = host.viewer(); if (!viewer) return null;
    const camera = viewer.rendered.camera.camera;
    const rect = (event.target as HTMLCanvasElement).getBoundingClientRect(), pose = host.pose();
    if (target.kind === 'linear') return linearSolver(target, camera, rect, event.clientX, event.clientY, pose);
    if (target.kind === 'hinge') return hingeSolver(target, camera, rect, event.clientX, event.clientY, pose);
    const groups = viewer.rendered.nestedGroup.groups, top = groups[TABLE_TOP], wood = groups[TABLE_WOOD];
    if (!top || !wood) return null;
    wood.updateWorldMatrix(true, false);
    const local = wood.worldToLocal(target.point.clone());
    let table = createTableDrag(target.group, top, wood, target.point, pose, camera, rect);
    let shift = screen(target.point, camera, rect).sub(new Vector2(event.clientX, event.clientY));
    const solver: Solver = {
      solve(x, y, current) {
        const patch = table.solve(x + shift.x, y + shift.y, current);
        solver.hint = patch ? undefined : 'Rotate the view to look down onto the table'; return patch;
      },
      rebase(x, y, current) {
        wood.updateWorldMatrix(true, false);
        const point = wood.localToWorld(local.clone());
        table = createTableDrag(target.group, top, wood, point, current, camera, rect);
        shift = screen(point, camera, rect).sub(new Vector2(x, y));
      },
    };
    return solver;
  }

  function requestFrame() { if (!frame) frame = requestAnimationFrame(update); }
  function update() {
    frame = 0;
    const current = gesture;
    if (current?.active) {
      if (current.dirty) {
        current.pending = current.solver.solve(current.x, current.y, host.pose()); current.dirty = false;
      }
      if (current.pending) {
        const pose = host.preview(current.pending);
        showHint(`${describe(current.target, pose)} · Esc cancels`, current.x, current.y);
        if (current.solver.atLimit) current.solver.rebase(current.x, current.y, pose);
        current.pending = null;
      } else if (current.solver.hint) showHint(current.solver.hint, current.x, current.y);
      return;
    }
    if (current || !latestHover) return;
    const event = latestHover; latestHover = null;
    const target = orbit || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ? null : targetAt(event);
    if (target?.path !== hover?.path) { hover = target; overlay(target); }
    container.classList.toggle('cad-can-drag', Boolean(target));
    if (target) showHint(`${target.label} · Drag · Alt-drag orbits`, event.clientX, event.clientY);
    else hint.hidden = true;
  }

  function releasePointer(current: Gesture) {
    if (current.canvas.hasPointerCapture(current.id)) current.canvas.releasePointerCapture(current.id);
  }
  function cancel() {
    const current = gesture; gesture = null;
    if (frame) { cancelAnimationFrame(frame); frame = 0; }
    if (current) {
      if (current.active) { host.restore(current.snapshot); suppressClickUntil = performance.now() + 350; }
      releasePointer(current);
    }
    clearHover();
  }
  function finish(event: PointerEvent) {
    const current = gesture; if (!current || current.id !== event.pointerId || (event.buttons & 1) !== 0) return;
    gesture = null;
    if (frame) { cancelAnimationFrame(frame); frame = 0; }
    if (current.active) {
      // Release ends the gesture at the last accepted position; queued moves are discarded.
      suppressClickUntil = performance.now() + 350; host.save();
      event.preventDefault(); event.stopImmediatePropagation();
    }
    releasePointer(current); clearHover();
  }
  function pointerDown(event: PointerEvent) {
    if (!(event.target instanceof HTMLCanvasElement) || event.button !== 0 || !event.isPrimary
      || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || orbit || gesture) return;
    const target = targetAt(event); if (!target) return;
    const solver = makeSolver(target, event); if (!solver) return;
    gesture = { id: event.pointerId, canvas: event.target, target, snapshot: host.snapshot(), solver,
      downX: event.clientX, downY: event.clientY, x: event.clientX, y: event.clientY,
      active: false, dirty: false, pending: null };
    // Keep the piece selector's same-element capture listener, while reserving the canvas gesture.
    event.stopPropagation();
    container.focus({ preventScroll: true }); event.target.setPointerCapture(event.pointerId);
  }
  function pointerMove(event: PointerEvent) {
    const current = gesture;
    if (!current) {
      if (event.target instanceof HTMLCanvasElement && !event.buttons) { latestHover = event; requestFrame(); }
      return;
    }
    if (event.pointerId !== current.id) return;
    if (!(event.buttons & 1)) { finish(event); return; }
    event.preventDefault(); event.stopImmediatePropagation();
    current.x = event.clientX; current.y = event.clientY;
    if (!current.active && Math.hypot(current.x - current.downX, current.y - current.downY) > 4) {
      current.active = true; hover = null; overlay(current.target, true);
      container.classList.add('cad-is-dragging');
    }
    if (current.active) { current.dirty = true; requestFrame(); }
  }
  function commands(): PlanMenuItem[] {
    return [
      { label: 'Orbit camera over movable parts', group: 'camera', shortcut: 'O / Alt-drag', ariaShortcut: 'O',
        checked: orbit, run: () => setOrbit(!orbit) },
      { label: 'Cancel dragging', group: 'motion', shortcut: 'Esc', ariaShortcut: 'Escape',
        enabled: Boolean(gesture?.active), run: cancel },
    ];
  }
  return {
    attach() {
      cancel();
      container.querySelector('.tcv_cad_toolbar')?.append(tools); container.append(hint);
      if (attached) return; attached = true;
      container.addEventListener('pointerdown', pointerDown, true);
      container.addEventListener('pointermove', pointerMove, true);
      window.addEventListener('pointerup', finish, true);
      container.addEventListener('pointercancel', event => { if (gesture?.id === event.pointerId) cancel(); }, true);
      container.addEventListener('lostpointercapture', event => { if (gesture?.id === event.pointerId) cancel(); }, true);
      container.addEventListener('pointerleave', () => { if (!gesture) clearHover(); });
      for (const type of ['click', 'dblclick'] as const) window.addEventListener(type, event => {
        if (event.target instanceof HTMLCanvasElement && container.contains(event.target)
          && performance.now() < suppressClickUntil) {
          event.preventDefault(); event.stopImmediatePropagation();
        }
      }, true);
      // Window capture runs before the persistent piece-selection Escape handler.
      window.addEventListener('keydown', event => {
        if (event.key === 'Escape' && gesture) {
          event.preventDefault(); event.stopImmediatePropagation(); cancel();
        }
      }, true);
      container.addEventListener('keydown', event => {
        if (event.ctrlKey || event.metaKey || event.altKey || event.key.toLowerCase() !== 'o'
          || (event.target as HTMLElement).closest('input,textarea,select,[contenteditable="true"]')) return;
        event.preventDefault(); event.stopPropagation(); setOrbit(!orbit);
      });
      window.addEventListener('blur', cancel); window.addEventListener('pagehide', cancel);
      document.addEventListener('visibilitychange', () => { if (document.hidden) cancel(); });
    },
    cancel,
    commands,
  };
}
