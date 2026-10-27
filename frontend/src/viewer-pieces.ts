/** Picking, framing and persistent selection for links to physical cutting pieces. */
import { Box3, DoubleSide, Mesh, MeshBasicMaterial, Vector3, type Camera, type Object3D } from 'three';
import { createPlanDropdown, type PlanMenuItem } from './plan-dropdown';

interface PickHit { info: { solidPath: string | null; path: string } }
export interface PieceViewer {
  ready: boolean;
  idPicker: { pickAt(x: number, y: number, options?: object): PickHit | null; setDirty(): void } | null;
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
type Link = { has(path: string): boolean; show(path: string): void };
const cutPath = (path: string) => path
  .replace('/Laptop table/Stowed/Facing/Packed tabletop/Offset tabletop/',
    '/Laptop table/Bench mount/Height adjustment/Arm orientation/Swivel arm/Tabletop rotation/Offset tabletop/')
  .replace(/^\/Campervan\//, '').split('/').join(' / ');
const cadPath = (path: string) => '/Campervan/' + path.split(' / ').join('/');

export function createViewerPieces(container: HTMLElement, getViewer: () => PieceViewer | undefined,
  cancelCamera: () => void, saveCamera: () => void) {
  const menu = createPlanDropdown();
  let link: Link | undefined, selected: string | null = null;
  let removeHighlight: (() => void) | undefined;
  let down: { x: number; y: number; camera: string } | undefined;
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
  iconButton(commands()[1], '<rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="3 3"/><path d="m8 8 8 8m0-8-8 8"/>');
  container.tabIndex = 0;

  function clear() {
    select(null);
    const viewer = getViewer();
    if (viewer?.ready) { viewer.clearSelection(); viewer.removeLastBbox(); viewer.update(true, false); }
  }
  function navigate() {
    if (selected && link?.has(cutPath(selected))) link.show(cutPath(selected));
  }
  function commands(): PlanMenuItem[] {
    return [
      { label: 'Show in cut list', group: 'piece', shortcut: 'Double-click',
        enabled: Boolean(selected && link?.has(cutPath(selected))), run: navigate },
      { label: 'Clear selection', group: 'selection', shortcut: 'Esc', ariaShortcut: 'Escape', run: clear },
    ];
  }
  function openMenu(x?: number, y?: number) {
    const rect = showButton.getBoundingClientRect();
    menu.open({ label: 'Piece actions', items: commands(), x: x ?? rect.left, y: y ?? rect.bottom,
      returnFocus: () => container.focus({ preventScroll: true }) });
  }
  function canvasEvent(event: Event) { return event.target instanceof HTMLCanvasElement; }
  function pick(event: MouseEvent) {
    const viewer = getViewer();
    if (!viewer?.ready || !viewer.idPicker) return null;
    const canvas = container.querySelector('canvas'); if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const hit = viewer.idPicker.pickAt(event.clientX - rect.left, event.clientY - rect.top);
    return hit ? hit.info.solidPath ?? hit.info.path.replace(/\/(faces|edges|vertices)\/[^/]+$/, '') : null;
  }
  function select(path: string | null) {
    if (selected !== path) {
      removeHighlight?.(); selected = path;
      const viewer = getViewer();
      if (viewer?.ready) {
        const group = path ? viewer.rendered.nestedGroup.groups[path] : undefined;
        if (group && path) highlight(viewer, group, path);
        viewer.update(true, false);
      }
    }
    showButton.disabled = !path || !link?.has(cutPath(path));
    const label = !showButton.disabled ? `Show ${path!.split('/').at(-1)} in cut list › Double-click`
      : 'Show in cut list › Select a wood piece, or double-click one';
    showButton.title = label; showButton.parentElement!.parentElement!.dataset.tooltip = label;
  }
  function highlight(viewer: PieceViewer, group: Object3D, path: string) {
    const previous = viewer.getStates()[path]?.slice();
    const shown = previous?.map(value => value === 3 ? 3 : 1);
    if (shown) viewer.setStates({ [path]: shown });
    const overlays: Mesh[] = [];
    const front = (group as Object3D & { front?: Mesh }).front;
    const sources: Mesh[] = [];
    if (front) sources.push(front);
    else group.traverse(object => { if (object instanceof Mesh) sources.push(object); });
    const colour = getComputedStyle(container).getPropertyValue('--piece-selection-colour').trim();
    for (const source of sources) {
      const overlay = new Mesh(source.geometry, new MeshBasicMaterial({ color: colour, side: DoubleSide,
        transparent: true, opacity: 1, depthTest: false, depthWrite: false, toneMapped: false }));
      overlay.position.copy(source.position); overlay.quaternion.copy(source.quaternion); overlay.scale.copy(source.scale);
      overlay.layers.set(0); overlay.renderOrder = 10000; source.parent!.add(overlay); overlays.push(overlay);
    }
    removeHighlight = () => {
      for (const overlay of overlays) { overlay.removeFromParent(); (overlay.material as MeshBasicMaterial).dispose(); }
      if (previous && JSON.stringify(viewer.getStates()[path]) === JSON.stringify(shown)) {
        viewer.setStates({ [path]: previous });
      }
      removeHighlight = undefined;
    };
  }
  container.addEventListener('pointerdown', event => {
    if (!canvasEvent(event) || event.button !== 0) return;
    down = { x: event.clientX, y: event.clientY, camera: JSON.stringify(getViewer()?.getCameraPosition()) };
    container.focus({ preventScroll: true });
  }, true);
  container.addEventListener('click', event => {
    if (!canvasEvent(event) || event.button !== 0 || !down) return;
    const start = down; down = undefined;
    if (Math.hypot(event.clientX - start.x, event.clientY - start.y) > 4
      || start.camera !== JSON.stringify(getViewer()?.getCameraPosition())) return;
    const path = pick(event);
    if (path) select(path); else clear();
  });
  container.addEventListener('dblclick', event => {
    if (!canvasEvent(event) || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); event.stopImmediatePropagation();
    select(pick(event));
    if (selected) navigate(); else clear();
  }, true);
  container.addEventListener('contextmenu', event => {
    if (!canvasEvent(event)) return;
    event.preventDefault(); select(pick(event)); openMenu(event.clientX, event.clientY);
  });
  container.addEventListener('keydown', event => {
    if ((event.target as HTMLElement).closest('input, textarea, select, [contenteditable=true]')) return;
    if (event.key === 'ContextMenu' || (event.key === 'F10' && event.shiftKey)) {
      event.preventDefault(); openMenu();
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || event.defaultPrevented || container.closest('[inert]') || !selected) return;
    if ((event.target as Element).closest('[role="menu"]')) return;
    event.preventDefault(); clear();
  }, true);

  return {
    setLink(value: Link) { link = value; },
    attach() { select(null); container.querySelector('.tcv_cad_toolbar')!.append(tools); },
    clear,
    focus(path: string) {
      const viewer = getViewer();
      const group = viewer?.ready ? viewer.rendered.nestedGroup.groups[cadPath(path)] : undefined;
      if (!viewer || !group) return false;
      clear(); cancelCamera(); select(cadPath(path));
      group.updateWorldMatrix(true, true);
      const box = new Box3().setFromObject(group), centre = box.getCenter(new Vector3()), size = box.getSize(new Vector3());
      const model = new Box3().setFromObject(viewer.rendered.nestedGroup.groups['/Campervan']);
      const middle = model.getCenter(new Vector3());
      const axis = size.x <= size.y && size.x <= size.z ? 'x' : size.y <= size.z ? 'y' : 'z';
      const direction = axis === 'x' ? new Vector3(centre.x < middle.x ? -1 : 1, -0.3, 0.25)
        : axis === 'y' ? new Vector3(0.25, centre.y < middle.y ? -1 : 1, 0.25) : new Vector3(0.15, -0.2, 1);
      direction.normalize();
      const camera = viewer.rendered.camera.camera.clone(); camera.up.set(0, 0, 1);
      const rect = container.getBoundingClientRect();
      const diameter = Math.max(150, size.length()) * 1.35 / Math.min(1, rect.width / rect.height);
      const fov = viewer.rendered.camera.camera.fov ?? 50;
      const distance = viewer.getOrtho() ? diameter * 2 : diameter / (2 * Math.sin(fov * Math.PI / 360));
      camera.position.copy(centre).addScaledVector(direction, distance); camera.lookAt(centre);
      const zoom = viewer.getOrtho()
        ? (viewer.rendered.camera.camera.top - viewer.rendered.camera.camera.bottom) / diameter : null;
      viewer.setCameraLocationSettings(camera.position.toArray(), camera.quaternion.toArray(), centre.toArray(), zoom, true);
      saveCamera();

      viewer.update(true, false);
      container.focus({ preventScroll: true }); return true;
    },
  };
}
