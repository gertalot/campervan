/** Picking, framing and persistent selection for links to physical cutting pieces. */
import { Box3, Mesh, Raycaster, Vector2, Vector3, type Camera, type Material, type Object3D } from 'three';
import { createPlanDropdown, type PlanMenuItem } from './plan-dropdown';
import { highlightPiece } from './viewer-highlight';

interface PickHit { info: { solidPath: string | null; path: string } }
export interface PieceViewer {
  ready: boolean;
  state: {
    get(name: string): unknown;
    subscribe(name: string, listener: () => void): () => void;
  };
  idPicker: {
    pickAt(x: number, y: number, options?: object): PickHit | null;
    setDirty(): void;
    edgeMaterial: Material | null;
    _renderPickBuffer(camera: Camera, target: unknown): void;
  } | null;
  rendered: {
    nestedGroup: { groups: Record<string, Object3D> };
    camera: { camera: Camera & { top: number; bottom: number; fov?: number } };
  };
  getStates(): Record<string, number[]>;
  setStates(states: Record<string, number[]>): void;
  getCameraPosition(): number[];
  getOrtho(): boolean;
  setCameraLocationSettings(position: number[], quaternion: number[], target: number[], zoom: number | null, notify: boolean): void;
  clearSelection(): void;
  removeLastBbox(): void;
  update(change: boolean, controls?: boolean): void;
}
export const hasActiveTool = (viewer: PieceViewer | undefined) => Boolean(viewer?.state.get('activeTool'));
type Link = { has(path: string): boolean; show(path: string): void };
const cutPath = (path: string) => path
  .replace('/Laptop table/Stowed/Facing/Packed tabletop/Offset tabletop/',
    '/Laptop table/Bench mount/Height adjustment/Arm orientation/Swivel arm/Tabletop rotation/Offset tabletop/')
  .replace(/^\/Campervan\//, '').split('/').join(' / ');
const cadPath = (path: string) => '/Campervan/' + path.split(' / ').join('/');

export function createViewerPieces(container: HTMLElement, getViewer: () => PieceViewer | undefined,
  cancelCamera: () => void, saveCamera: () => void) {
  const menu = createPlanDropdown();
  let link: Link | undefined;
  const selected = new Map<string, () => void>();
  let down: { x: number; y: number; camera: string } | undefined;
  let extraCommands = (): PlanMenuItem[] => [];
  const tools = document.createElement('span'); tools.className = 'cad-piece-controls';
  tools.dataset.campervanControl = 'true';
  function iconButton(command: PlanMenuItem, drawing: string) {
    const tooltip = document.createElement('span'); tooltip.className = 'tcv_tooltip';
    tooltip.dataset.tooltip = `${command.label} › ${command.shortcut}`;
    const frame = document.createElement('span'); frame.className = 'tcv_button_frame';
    const button = document.createElement('button'); button.type = 'button'; button.className = 'tcv_reset tcv_btn cad-piece-button';
    button.setAttribute('aria-label', command.label); button.title = `${command.label} · ${command.shortcut}`;
    if (command.ariaShortcut) button.setAttribute('aria-keyshortcuts', command.ariaShortcut);
    button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7"
      stroke-linecap="round" stroke-linejoin="round">${drawing}</svg>`;
    button.onclick = command.run; frame.append(button); tooltip.append(frame); tools.append(tooltip); return button;
  }
  const showButton = iconButton(commands()[0],
    '<rect x="3" y="3" width="14" height="18" rx="1.5"/><path d="M3 9h14M9 9v12M13 15h8m-3-3 3 3-3 3"/>');
  showButton.disabled = true;
  const clearButton = iconButton(commands()[1],
    '<rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="3 3"/><path d="m8 8 8 8m0-8-8 8"/>');
  const menuButton = iconButton({ label: 'Piece actions', group: 'piece', shortcut: 'Shift+F10',
    ariaShortcut: 'Shift+F10', run: () => openMenu() },
    '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>');
  menuButton.setAttribute('aria-haspopup', 'menu');
  menuButton.setAttribute('aria-expanded', 'false');
  const selectionHint = 'Click a piece to select or deselect it. Shift-click to add or remove individual pieces.';
  menuButton.title += '. ' + selectionHint;
  menuButton.parentElement!.parentElement!.dataset.tooltip = menuButton.title;
  container.setAttribute('aria-description', selectionHint);
  container.tabIndex = 0;

  function clear() {
    selectOnly(null);
    const viewer = getViewer();
    if (viewer?.ready) { viewer.clearSelection(); viewer.removeLastBbox(); viewer.update(true, false); }
  }
  function onlyPiece(): string | undefined {
    return selected.size === 1 ? selected.keys().next().value : undefined;
  }
  function navigate(path = onlyPiece()) {
    if (!hasActiveTool(getViewer()) && path && link?.has(cutPath(path))) link.show(cutPath(path));
  }
  function frame(box: Box3, direction?: Vector3) {
    const viewer = getViewer();
    if (!viewer?.ready || box.isEmpty()) return;
    const centre = box.getCenter(new Vector3());
    const camera = viewer.rendered.camera.camera.clone();
    if (direction) {
      camera.up.set(0, 0, 1);
      camera.position.copy(centre).add(direction);
      camera.lookAt(centre);
    }
    const inverse = camera.quaternion.clone().invert();
    const rect = container.getBoundingClientRect(), aspect = rect.width / rect.height;
    const tanY = Math.tan((viewer.rendered.camera.camera.fov ?? 50) * Math.PI / 360);
    let distance = 0, halfHeight = 0;
    for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) {
      for (const z of [box.min.z, box.max.z]) {
        const corner = new Vector3(x, y, z).sub(centre).applyQuaternion(inverse);
        const height = Math.max(Math.abs(corner.y), Math.abs(corner.x) / aspect);
        halfHeight = Math.max(halfHeight, height);
        distance = Math.max(distance, corner.z + height / tanY);
      }
    }
    const offset = new Vector3(0, 0, Math.max(1, distance) * 1.1).applyQuaternion(camera.quaternion);
    camera.position.copy(centre).add(offset);
    const zoom = viewer.getOrtho()
      ? (viewer.rendered.camera.camera.top - viewer.rendered.camera.camera.bottom) / Math.max(1, halfHeight * 2.2) : null;
    viewer.setCameraLocationSettings(camera.position.toArray(), camera.quaternion.toArray(), centre.toArray(), zoom, true);
    saveCamera();
  }
  function cargoBounds() {
    const viewer = getViewer()!;
    const box = new Box3();
    for (const name of ['Floor outline', 'Roof']) {
      const envelope = viewer.rendered.nestedGroup.groups[`/Campervan/Vehicle references/${name}`];
      envelope.updateWorldMatrix(true, true);
      box.union(new Box3().setFromObject(envelope));
    }
    return box;
  }
  function resetView() {
    const viewer = getViewer();
    if (!viewer?.ready || hasActiveTool(viewer)) return;
    cancelCamera();
    frame(cargoBounds());
  }
  function resetCommand(): PlanMenuItem {
    return { label: 'Reset view', group: 'camera', shortcut: 'R', ariaShortcut: 'R',
      enabled: Boolean(getViewer()?.ready) && !hasActiveTool(getViewer()), run: resetView };
  }
  function commands(target?: string): PlanMenuItem[] {
    const path = target ?? onlyPiece();
    return [
      { label: 'Show in cut list', group: 'piece', shortcut: 'Double-click',
        enabled: !hasActiveTool(getViewer()) && Boolean(path && link?.has(cutPath(path))), run: () => navigate(target) },
      { label: 'Clear selection', group: 'selection', shortcut: 'Esc', ariaShortcut: 'Escape',
        enabled: !hasActiveTool(getViewer()), run: () => { if (!hasActiveTool(getViewer())) clear(); } },
      { label: path && selected.has(path) ? 'Remove piece from selection' : 'Add piece to selection',
        group: 'selection', shortcut: 'Shift-click', enabled: Boolean(path), run: () => { if (path) toggle(path, true); } },
      resetCommand(),
      ...extraCommands(),
    ];
  }
  function openMenu(event?: MouseEvent) {
    if (hasActiveTool(getViewer())) return;
    menu.open({ label: 'Piece actions', items: commands(event ? pick(event) ?? undefined : onlyPiece()),
      trigger: event ? undefined : menuButton, x: event?.clientX, y: event?.clientY,
      returnFocus: () => container.focus({ preventScroll: true }) });
  }
  function canvasEvent(event: Event) { return event.target instanceof HTMLCanvasElement; }
  function pick(event: MouseEvent) {
    const viewer = getViewer();
    if (!viewer?.ready || hasActiveTool(viewer) || !viewer.idPicker) return null;
    const canvas = container.querySelector('canvas'); if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const hit = viewer.idPicker.pickAt(event.clientX - rect.left, event.clientY - rect.top);
    return hit ? hit.info.solidPath ?? hit.info.path.replace(/\/(faces|edges|vertices)\/[^/]+$/, '') : null;
  }
  function setSelection(paths: Set<string>) {
    if (paths.size === selected.size && [...paths].every(path => selected.has(path))) {
      updateControls();
      return;
    }
    const viewer = getViewer();
    for (const [path, remove] of selected) {
      if (paths.has(path)) continue;
      remove();
      selected.delete(path);
    }
    if (viewer?.ready) {
      for (const path of paths) {
        if (selected.has(path)) continue;
        const group = viewer.rendered.nestedGroup.groups[path];
        if (group) selected.set(path, highlight(viewer, group, path));
      }
      viewer.update(true, false);
    }
    updateControls();
  }
  function selectOnly(path: string | null) {
    setSelection(new Set(path ? [path] : []));
  }
  function toggle(path: string, additive: boolean) {
    const paths = new Set(selected.keys());
    if (!paths.delete(path)) {
      if (!additive) paths.clear();
      paths.add(path);
    }
    setSelection(paths);
  }
  function updateControls() {
    const measuring = hasActiveTool(getViewer());
    const path = onlyPiece();
    showButton.disabled = measuring || !path || !link?.has(cutPath(path));
    clearButton.disabled = menuButton.disabled = measuring;
    const label = !showButton.disabled ? `Show ${path!.split('/').at(-1)} in cut list › Double-click`
      : measuring ? 'Show in cut list › Finish measuring first'
      : 'Show in cut list › Select a wood piece, or double-click one';
    showButton.title = label; showButton.parentElement!.parentElement!.dataset.tooltip = label;
  }
  function highlight(viewer: PieceViewer, group: Object3D, path: string) {
    const previous = viewer.getStates()[path]?.slice();
    const shown = previous?.map(value => value === 3 ? 3 : 1);
    if (shown) viewer.setStates({ [path]: shown });
    const colour = getComputedStyle(container).getPropertyValue('--piece-selection-colour').trim();
    const removeOverlay = highlightPiece(group, colour);
    return () => {
      removeOverlay();
      if (previous && JSON.stringify(viewer.getStates()[path]) === JSON.stringify(shown)) {
        viewer.setStates({ [path]: previous });
      }
    };
  }
  container.addEventListener('pointerdown', event => {
    if (hasActiveTool(getViewer()) || !canvasEvent(event) || event.button !== 0) return;
    down = { x: event.clientX, y: event.clientY, camera: JSON.stringify(getViewer()?.getCameraPosition()) };
    container.focus({ preventScroll: true });
  }, true);
  container.addEventListener('click', event => {
    if (hasActiveTool(getViewer()) || !canvasEvent(event) || event.button !== 0 || !down) return;
    const start = down; down = undefined;
    if (Math.hypot(event.clientX - start.x, event.clientY - start.y) > 4
      || start.camera !== JSON.stringify(getViewer()?.getCameraPosition())) return;
    const path = pick(event);
    if (path) toggle(path, event.shiftKey);
    else if (!event.shiftKey) clear();
  });
  container.addEventListener('dblclick', event => {
    if (hasActiveTool(getViewer()) || !canvasEvent(event)) return;
    // Reserve all canvas double-clicks: the renderer otherwise uses modifiers to hide/isolate parts.
    event.preventDefault(); event.stopImmediatePropagation();
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const path = pick(event);
    if (path && link?.has(cutPath(path))) { selectOnly(path); navigate(path); }
  }, true);
  container.addEventListener('contextmenu', event => {
    if (hasActiveTool(getViewer()) || !canvasEvent(event)) return;
    event.preventDefault(); openMenu(event);
  }, true);
  container.addEventListener('keydown', event => {
    if (hasActiveTool(getViewer())) return;
    if ((event.target as HTMLElement).closest('input, textarea, select, [contenteditable=true]')) return;
    if (event.key === 'ContextMenu' || (event.key === 'F10' && event.shiftKey)) {
      event.preventDefault(); openMenu();
    }
  });
  container.addEventListener('keydown', event => {
    if (event.key.toLowerCase() !== 'r' || event.repeat || event.defaultPrevented
      || event.ctrlKey || event.metaKey || event.altKey || event.target !== container
      || container.closest('[inert]') || hasActiveTool(getViewer())) return;
    event.preventDefault(); event.stopImmediatePropagation(); resetCommand().run();
  }, true);
  document.addEventListener('keydown', event => {
    if (hasActiveTool(getViewer()) || event.key !== 'Escape' || event.defaultPrevented
      || container.closest('[inert]') || !selected.size) return;
    if ((event.target as Element).closest('[role="menu"]')) return;
    event.preventDefault(); clear();
  }, true);

  return {
    resetCommand,
    toolChanged() {
      down = undefined; menu.close();
      // Remove only our overlay: clear() would also reset the measurement endpoints.
      if (hasActiveTool(getViewer())) selectOnly(null);
      else updateControls();
    },
    setLink(value: Link) { link = value; },
    setCommands(value: () => PlanMenuItem[]) { extraCommands = value; },
    pickPoint(event: MouseEvent) {
      const path = pick(event), viewer = getViewer();
      const group = path && viewer?.rendered.nestedGroup.groups[path];
      const canvas = container.querySelector('canvas');
      if (!path || !viewer || !group || !canvas) return null;
      group.updateWorldMatrix(true, true);
      const rect = canvas.getBoundingClientRect();
      const ray = new Raycaster();
      ray.setFromCamera(new Vector2(2 * (event.clientX - rect.left) / rect.width - 1,
        1 - 2 * (event.clientY - rect.top) / rect.height), viewer.rendered.camera.camera);
      const solid = group as Object3D & { front?: Mesh; back?: Mesh };
      const meshes: Mesh[] = [];
      if (solid.front) meshes.push(solid.front);
      if (solid.back) meshes.push(solid.back);
      if (!meshes.length) group.traverse(object => {
        if (object instanceof Mesh && !object.userData.campervanOverlay) meshes.push(object);
      });
      const hits = ray.intersectObjects(meshes, false).filter(hit => !hit.object.userData.campervanOverlay);
      return hits.length ? { path, point: hits[0].point } : null;
    },
    orbitTarget(): number[] {
      const viewer = getViewer()!;
      const rect = container.querySelector('canvas')!.getBoundingClientRect();
      const hit = this.pickPoint(new MouseEvent('mousemove', {
        clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2,
      }));
      if (hit) return hit.point.toArray();
      const ray = new Raycaster();
      ray.setFromCamera(new Vector2(0, 0), viewer.rendered.camera.camera);
      const box = cargoBounds();
      const target = ray.ray.intersectBox(box, new Vector3());
      if (target && target.distanceToSquared(ray.ray.origin) >= 1) return target.toArray();
      return ray.ray.at(Math.max(1, box.getSize(new Vector3()).length() / 2), new Vector3()).toArray();
    },
    attach() { selectOnly(null); container.querySelector('.tcv_cad_toolbar')!.append(tools); },
    clear,
    focus(path: string) {
      const viewer = getViewer();
      if (hasActiveTool(viewer)) return false;
      const group = viewer?.ready ? viewer.rendered.nestedGroup.groups[cadPath(path)] : undefined;
      if (!viewer || !group) return false;
      clear(); cancelCamera(); selectOnly(cadPath(path));
      group.updateWorldMatrix(true, true);
      const box = new Box3().setFromObject(group), centre = box.getCenter(new Vector3()), size = box.getSize(new Vector3());
      const model = new Box3().setFromObject(viewer.rendered.nestedGroup.groups['/Campervan']);
      const middle = model.getCenter(new Vector3());
      const axis = size.x <= size.y && size.x <= size.z ? 'x' : size.y <= size.z ? 'y' : 'z';
      const direction = axis === 'x' ? new Vector3(centre.x < middle.x ? -1 : 1, -0.3, 0.25)
        : axis === 'y' ? new Vector3(0.25, centre.y < middle.y ? -1 : 1, 0.25) : new Vector3(0.15, -0.2, 1);
      direction.normalize();
      frame(box, direction);

      viewer.update(true, false);
      container.focus({ preventScroll: true }); return true;
    },
  };
}
