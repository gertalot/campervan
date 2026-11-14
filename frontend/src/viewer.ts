/// <reference types="vite/client" />
/** Our host for the installed OCP renderer. No second viewer or playback timeline. */
import { createViewerCamera, type CameraState, type CameraViewer } from './viewer-camera';
import { loadMannequin, seatedPose, lyingPose, secondLyingPose, type MannequinPose } from './mannequin';
import { createPillows } from './pillows';
import { createSeatCushion } from './seat-cushion';
import { createVehicleFade } from './vehicle-fade';
import { createViewerPieces, hasActiveTool, type PieceViewer } from './viewer-pieces';
import { createViewerDrag, type DragSnapshot } from './viewer-drag';
import { createLayoutMirror } from './layout-mirror';
import { Box3, DoubleSide, FrontSide, Mesh, type Object3D, type Scene } from 'three';
import * as library from './renderer';
import { assetUrl, isStaticSite } from './site-runtime';

type Axis = 'x' | 'y' | 'z';
interface Track {
  path: string; axis: Axis; kind?: 'rotation' | 'translation';
  travel?: number; keyframes?: [number, number][]; interpolation?: 'linear' | 'step';
}
interface Motion { position: number; tracks: Track[] }
interface Vector { x: number; y: number; z: number }
interface SceneGroup { position: Vector; rotation: Vector; visible: boolean; updateMatrixWorld(force: boolean): void }
interface MotionController {
  snapshotPositions(): DragSnapshot;
  previewPositions(patch: Record<string, number>): void;
  restorePositions(snapshot: DragSnapshot): void;
  savePositions(patch?: Record<string, number>): Promise<void>;
}
interface CadViewer extends CameraViewer {
  display: {
    shapeFilterDropDownMenu: { setValue(value: string): void };
  };
  rendered: CameraViewer['rendered'] & {
    scene: Scene;
    nestedGroup: { groups: Record<string, SceneGroup> };
    orientationMarker: { setVisible(value: boolean): void };
  };
  getStates(): Record<string, number[]>;
  setStates(states: Record<string, number[]>): void;
  update(change: boolean, controls: boolean): void;
}

export function createCadViewer(container: HTMLElement, onModel: () => void, onError: (message: string) => void,
  onMannequinStatus: (message: string) => void = () => {},
  onMannequinFit: (pose: Pick<MannequinPose, 'x' | 'y' | 'z' | 'facing' | 'hip' | 'knee'>) => void = () => {}) {
  let viewer: CadViewer | undefined;
  let excludedComponents: string[] = [];
  let unsubscribeTool: (() => void) | undefined;
  let socket: WebSocket | undefined;
  let motions: Record<string, Motion> = {};
  const positions: Record<string, number> = {};
  const bases = new Map<string, Vector>();
  const pendingMotions = new Set<string>();
  let mannequinPending = false;
  let motionFrame: number | null = null;
  let motionController: MotionController | undefined;
  const cameraKey = 'campervan.camera';
  let rendering = false;
  const cameraNavigation = createViewerCamera(container, () => viewer, cameraKey, () => rendering);
  const { cameraState, saveCamera, cancelCameraAnimation } = cameraNavigation;
  const mannequins: Partial<Record<MannequinPose['mode'], Awaited<ReturnType<typeof loadMannequin>>>> = {};
  let mannequinLoading: Promise<void> | undefined;
  const mannequinPoses = { seated: { ...seatedPose }, lying: { ...lyingPose }, 'lying-second': { ...secondLyingPose } };
  let seatCushion: ReturnType<typeof createSeatCushion> | undefined;
  const vehicleFade = createVehicleFade();
  const layoutMirror = createLayoutMirror();
  let scanReference: Object3D | undefined;
  const pieces = createViewerPieces(container, () => viewer as unknown as PieceViewer | undefined,
    cancelCameraAnimation, saveCamera);
  const drag = createViewerDrag(container, {
    viewer: () => viewer as unknown as PieceViewer | undefined,
    motions: () => motions,
    pose: () => motionController?.snapshotPositions().positions ?? { ...positions },
    pick: pieces.pickPoint,
    preview: previewPose,
    save: () => { void saveAcceptedPositions(); },
    snapshot: () => motionController?.snapshotPositions() ?? { positions: { ...positions }, returnMountedTable: false },
    restore: snapshot => motionController?.restorePositions(snapshot),
  });
  pieces.setCommands(drag.commands);

  function previewPose(patch: Record<string, number>) {
    motionController?.previewPositions(patch);
    return motionController?.snapshotPositions().positions ?? { ...positions };
  }
  async function saveAcceptedPositions() {
    const pose = motionController?.snapshotPositions().positions;
    const normalised: Record<string, number> = {};
    for (const name of ['table_arm_swivel_deg', 'table_top_rotation_deg']) {
      if (pose && (pose[name] < 0 || pose[name] > 360)) normalised[name] = ((pose[name] % 360) + 360) % 360;
    }
    await motionController?.savePositions(normalised);
  }
  let pillows = createPillows();
  if (import.meta.hot) import.meta.hot.accept('./pillows', module => {
    if (!module || !viewer?.ready) return;
    pillows = module.createPillows();
    layoutMirror.inOriginalCoordinates(() => {
      pillows.attach(viewer!.rendered.nestedGroup.groups);
      pillows.pose(positions.bed_extension_percent ?? motions.bed_extension_percent?.position ?? 0);
    });
    viewer.update(true, true);
  });
  let seeInside = false;

  function updateScanSides() {
    // The reconstructed interior mesh is wound towards the cabin. Culling its backs
    // opens the near-side shell while keeping inward-facing floor and far-side faces.
    const side = seeInside ? FrontSide : DoubleSide;
    scanReference?.traverse(object => {
      if (!(object instanceof Mesh)) return;
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        if (material.side === side) continue;
        material.side = side;
        material.needsUpdate = true;
      }
    });
  }

  function showMannequin(render = true) {
    if (!viewer?.ready) return;
    layoutMirror.inOriginalCoordinates(() => {
      fitMannequin();
      for (const model of Object.values(mannequins)) layoutMirror.add(model.root);
    });
    if (render) viewer.update(true, false);
  }

  function fitMannequin() {
    if (!viewer?.ready) return;
    const bed = positions.bed_extension_percent ?? motions.bed_extension_percent?.position ?? 0;
    for (const model of Object.values(mannequins)) model.root.visible = false;
    const mode = bed === 100 ? 'lying' : 'seated';
    const mannequin = mannequins[mode];
    const mannequinPose = mannequinPoses[mode];
    if (!mannequin) return;
    const groups = viewer.rendered.nestedGroup.groups;
    const seat = groups['/Campervan/Long bench/Cushions/Long seat/Foam'] as unknown as Object3D;
    const back = groups['/Campervan/Long bench/Cushions/Wall backrest/Foam'] as unknown as Object3D;
    if (!seat || !back) return;
    seatCushion ??= createSeatCushion(seat);
    pillows.supportHead(null);
    pillows.supportHead(null, false);
    if (mannequinPose.mode === 'lying') {
      seatCushion.deform(null);
      const cross = groups['/Campervan/Cross bench/Cushions/Cross seat/Foam'] as unknown as Object3D;
      if (!cross) return;
      const mattress = seatCushion.bounds().union(new Box3().setFromObject(cross));
      let feetOutside = false;
      for (const id of ['lying', 'lying-second'] as const) {
        const model = mannequins[id];
        const pose = mannequinPoses[id];
        const first = id === 'lying';
        const path = first ? '/Campervan/Cross bench/Cushions/Front pillow/Pillow'
          : '/Campervan/Long bench/Cushions/Rear pillow/Pillow';
        const pillow = groups[path] as unknown as Object3D;
        if (!model || !pillow) continue;
        const fitted = model.lie({ ...pose, visible: pose.visible && bed === 100 },
          mattress, new Box3().setFromObject(pillow));
        model.attach(viewer.rendered.scene);
        if (model.root.visible) {
          pillows.supportHead(fitted.head, first);
          feetOutside ||= fitted.feet.min.y < mattress.min.y;
        }
      }
      onMannequinStatus(feetOutside ? 'Feet extend beyond the mattress.' : '');
      return;
    }
    const visible = mannequinPose.visible && bed === 0;
    const fitted = mannequin.seat({ ...mannequinPose, visible }, seatCushion.bounds(), new Box3().setFromObject(back).min.x);
    const { x, y, z, facing, hip, knee } = fitted.pose;
    Object.assign(mannequinPose, { x, y, z, facing, hip, knee });
    mannequinPose.fitSeat = false;
    onMannequinFit({ x, y, z, facing, hip, knee });
    mannequin.attach(viewer.rendered.scene);
    seatCushion.deform(visible ? mannequin.root : null);
    const cabinet = groups['/Campervan/Cabinet'] as unknown as Object3D;
    const cabinetBounds = cabinet ? new Box3().setFromObject(cabinet) : null;
    onMannequinStatus(bed > 0 ? 'Retract the bed to show the seated preview.'
      : cabinetBounds?.intersectsBox(fitted.feet) ? 'Feet overlap the cabinet: this layout needs more legroom.'
      : fitted.compression < -5 ? 'This leg pose lifts the hips off the seat.'
      : fitted.compression > (seatCushion.bounds().max.z - seatCushion.bounds().min.z) * 0.55
        ? 'This leg pose needs more compression than the cushion allows.' : '');
  }

  function showTables(pose: Record<string, number> = positions) {
    if (!viewer?.ready) return;
    const selected = pose.table_mount ?? motions.table_mount?.position ?? 0;
    for (const [name, value] of [['Bench mount', 0], ['Stowed', 2]] as const) {
      const group = viewer.rendered.nestedGroup.groups[`/Campervan/Laptop table/${name}`];
      if (group) group.visible = selected === value;
    }
    (viewer as unknown as PieceViewer).idPicker?.setDirty();
  }

  function scheduleMove(name?: string) {
    if (!viewer?.ready) return; // Latest values are replayed when geometry arrives.
    if (name) pendingMotions.add(name);
    else mannequinPending = true;
    if (motionFrame !== null) return;
    motionFrame = requestAnimationFrame(() => {
      motionFrame = null;
      const changed = new Set(pendingMotions);
      const mannequinChanged = mannequinPending;
      pendingMotions.clear();
      mannequinPending = false;
      move(changed, mannequinChanged);
    });
  }

  function move(changed?: ReadonlySet<string>, mannequinChanged = false) {
    if (!viewer?.ready) return;
    if (!changed) {
      // A new motion payload replays all latest values and replaces queued work.
      if (motionFrame !== null) cancelAnimationFrame(motionFrame);
      motionFrame = null;
      pendingMotions.clear();
      mannequinPending = false;
    }
    applyMotionTransforms(positions, changed);
    const bedChanged = !changed || changed.has('bed_extension_percent');
    if (bedChanged) pillows.pose(positions.bed_extension_percent ?? motions.bed_extension_percent?.position ?? 0);
    if (!changed || changed.has('table_mount')) showTables();
    if (bedChanged || mannequinChanged) showMannequin(false);
    (viewer as unknown as PieceViewer).idPicker?.setDirty();
    viewer.update(true, true);
  }

  function applyMotionTransforms(pose: Record<string, number>, changed?: ReadonlySet<string>) {
    if (!viewer?.ready) return;
    for (const [name, motion] of Object.entries(motions)) {
      if (changed && !changed.has(name)) continue;
      const percent = pose[name] ?? motion.position;
      const fraction = (percent - motion.position) / 100;
      for (const track of motion.tracks) {
        const group = viewer.rendered.nestedGroup.groups[track.path];
        const base = bases.get(`${track.path}:${track.kind ?? 'translation'}`);
        if (!group || !base) continue;
        const transform = track.kind === 'rotation' ? group.rotation : group.position;
        const units = track.kind === 'rotation' ? Math.PI / 180 : 1;
        if (track.keyframes) {
          const points = track.keyframes;
          if (track.interpolation === 'step') {
            let value = points[0][1];
            for (const [threshold, next] of points) {
              if (percent < threshold) break;
              value = next;
            }
            transform[track.axis] = value * units;
          } else {
            const endIndex = points.findIndex(([position], index) => index > 0 && position >= percent);
            const [start, a] = points[endIndex - 1];
            const [end, b] = points[endIndex];
            transform[track.axis] = (a + (b - a) * (percent - start) / (end - start)) * units;
          }
        } else {
          transform[track.axis] = base[track.axis] + fraction * track.travel! * units;
        }
        group.updateMatrixWorld(true);
      }
    }
  }

  return {
    async connect(url: string) {
      const css = document.createElement('link');
      css.rel = 'stylesheet';
      css.href = assetUrl('viewer-assets/css/three-cad-viewer.css');
      const styles = new Promise<void>((resolve, reject) => {
        css.onload = () => resolve();
        css.onerror = () => reject(new Error('Could not load CAD viewer styles.'));
      });
      document.head.append(css);
      // Serve JS and CSS from the locked Python package, keeping both halves compatible.
      const coreUrl = assetUrl('viewer-assets/js/ocp-viewer-core/index.js');
      const [core] = await Promise.all([import(/* @vite-ignore */ coreUrl), styles]);
      // createPage accepts the Viewer constructor; capture its instance while reusing
      // OCP's geometry loading and measurement messages.
      class HostedViewer extends library.Viewer {
        constructor(...args: any[]) {
          super(...args);
          viewer = this as unknown as CadViewer;
          unsubscribeTool?.();
          unsubscribeTool = (this as unknown as PieceViewer).state.subscribe('activeTool', () => {
            drag.toolChanged(); pieces.toolChanged();
            if (hasActiveTool(this as unknown as PieceViewer)) this.display.shapeFilterDropDownMenu.setValue('All');
          });
          const update = this.update.bind(this);
          this.update = (...updateArgs: any[]) => {
            if (this.ready) {
              if (seeInside) vehicleFade.update(this.getCameraQuaternion(),
                this.getOrtho() ? undefined : this.getCameraPosition());
              else vehicleFade.setExteriorOpacity();
            }
            update(...updateArgs);
            if (this.ready) cameraNavigation.updateCube();
          };
        }
      }
      const page = core.createPage({
        Viewer: HostedViewer, Display: library.Display, Timer: library.Timer,
        container, listen: false, theme: 'dark',
        getSize: () => ({ width: container.clientWidth + 20, height: container.clientHeight }),
        overrides: { display: { tools: false, glass: false, theme: 'dark' }, viewer: { tools: false } },
        send(command: string, message: unknown) {
          if (command === 'status') saveCamera();
          if (socket?.readyState === WebSocket.OPEN) socket.send(`U:${JSON.stringify({ command, text: message })}`);
        },
      });
      const allowed = new Set(['perspective', 'transparent', 'blackedges', 'reset', 'resize', 'distance']);
      if (isStaticSite) allowed.delete('distance');
      function trimToolbar() {
        // createPage clears the host when it creates the first display.
        cameraNavigation.attachCube();
        for (const child of container.querySelectorAll<HTMLElement>('.tcv_cad_toolbar > *')) {
          const button = child.querySelector('input[class*="tcv_button_"]');
          if (button && [...allowed].some(name => button.classList.contains(`tcv_button_${name}`))) {
            child.dataset.campervanControl = 'true';
          }
        }
        viewer?.rendered.orientationMarker.setVisible(true);
        if (viewer?.ready) cameraNavigation.updateCube();
      }
      function receive(message: any) {
        if (message.type === 'data') cancelCameraAnimation();
        if (message.type === 'campervan_motion') {
          motions = message.motions;
          for (const motion of Object.values(motions)) {
            for (const track of motion.tracks) {
              const group = viewer?.rendered.nestedGroup.groups[track.path];
              if (group) {
                const transform = track.kind === 'rotation' ? group.rotation : group.position;
                bases.set(`${track.path}:${track.kind ?? 'translation'}`, { x: transform.x, y: transform.y, z: transform.z });
              }
            }
          }
          move();
        } else {
          const camera: CameraState | null = message.type === 'data'
            ? cameraState() ?? JSON.parse(localStorage.getItem(cameraKey) ?? 'null') : null;
          if (message.config) {
            Object.assign(message.config, { tools: false, glass: false, control: 'orbit', up: 'Z' });
            if (message.type === 'data') {
              // Explicit camera values preserve the exact framing, including across a full page reload.
              Object.assign(message.config, camera ?? { zoom: 0.65 }, { resetCamera: 'keep' });
            }
          }
          rendering = true;
          // OCP disposes its old scene when replacing geometry; keep the independent human rig.
          if (message.type === 'data') {
            scanReference?.removeFromParent();
            drag.cancel();
            pieces.clear();
            vehicleFade.clear();
            layoutMirror.clear();
            Object.values(mannequins).forEach(model => model.root.removeFromParent());
            seatCushion?.dispose();
            seatCushion = undefined;
          }
          try { page.handleMessage(message); }
          finally { rendering = false; }
          if (message.type === 'data') {
            vehicleFade.attach(viewer!.rendered.nestedGroup.groups);
            const picker = (viewer as unknown as PieceViewer).idPicker;
            if (picker) {
              layoutMirror.attachPicker(picker);
              const pick = picker.pickAt.bind(picker);
              let pickingVersion = -1;
              picker.pickAt = (x, y, options) => {
                if (pickingVersion !== vehicleFade.pickingVersion) {
                  picker.setDirty(); pickingVersion = vehicleFade.pickingVersion;
                }
                return vehicleFade.withPicking(() => pick(x, y, options));
              };
            }
            pillows.attach(viewer!.rendered.nestedGroup.groups);
            pillows.pose(positions.bed_extension_percent ?? 0);
            layoutMirror.attach(viewer!.rendered.nestedGroup.groups);
            if (scanReference) viewer!.rendered.scene.add(scanReference);
            motions = {};
            bases.clear();
            trimToolbar();
            pieces.attach();
            drag.attach();
            page.resize();
            if (camera && viewer?.ready) {
              const projection = viewer.rendered.camera.camera;
              // Perspective zoom is already encoded by position. Orthographic zoom depends on the new frustum.
              const zoom = camera.ortho
                ? camera.viewHeight ? (projection.top - projection.bottom) / camera.viewHeight : camera.zoom
                : null;
              viewer.setCameraLocationSettings(camera.position, camera.quaternion, camera.target, zoom, false);
            }
            saveCamera();
            onModel();
            showTables();
            showMannequin();
          }
        }
      }
      new ResizeObserver(() => { if (viewer?.ready) page.resize(); }).observe(container);
      if (isStaticSite) {
        const response = await fetch(assetUrl('viewer-frames.json'));
        if (!response.ok) throw new Error(`Could not load the exported model (${response.status}).`);
        const messages = await response.json() as unknown[];
        for (const message of messages) receive(message);
        if (!viewer?.ready) throw new Error('The exported model did not load. Run make site again.');
        return;
      }
      const endpoint = new URL(url);
      endpoint.protocol = endpoint.protocol === 'https:' ? 'wss:' : 'ws:';
      endpoint.pathname = '/';
      socket = new WebSocket(endpoint);
      socket.onmessage = event => {
        try { receive(JSON.parse(event.data)); }
        catch (error) { onError(error instanceof Error ? error.message : String(error)); }
      };
      await new Promise<void>((resolve, reject) => {
        socket!.onopen = () => { socket!.send('L:{}'); resolve(); };
        socket!.onerror = () => {
          const error = new Error('CAD viewer connection failed. Check make viewer.');
          onError(error.message);
          reject(error);
        };
      });
      socket.onclose = () => onError('CAD viewer connection closed. Refresh after restarting make viewer.');
    },
    setPosition(name: string, percent: number) {
      if (positions[name] === percent) return;
      if (name === 'table_mount' && positions[name] !== percent) pieces.clear();
      positions[name] = percent;
      scheduleMove(name);
    },
    setMotionController(controller: MotionController) { motionController = controller; },
    setScanReference(root: Object3D | undefined) {
      scanReference?.removeFromParent();
      scanReference = root;
      updateScanSides();
      if (root && viewer?.ready) viewer.rendered.scene.add(root);
      viewer?.update(true, false);
    },
    setVehicleComparisonOpacity(opacity: number | null) {
      vehicleFade.setComparisonOpacity(opacity);
      viewer?.update(true, false);
    },
    setLayoutWidth(width: number) { layoutMirror.setWidth(width); },
    setMirrored(enabled: boolean) {
      drag.cancel();
      layoutMirror.setEnabled(enabled);
      (viewer as unknown as PieceViewer | undefined)?.idPicker?.setDirty();
      viewer?.update(true, false);
    },
    previewPositions: previewPose,
    savePositions: saveAcceptedPositions,
    cancelDrag: drag.cancel,
    setPieceLink: pieces.setLink,
    focusPiece: pieces.focus,
    setSeeInside(enabled: boolean) {
      seeInside = enabled;
      updateScanSides();
      viewer?.update(true, false);
    },
    setMannequinPose(pose: MannequinPose) {
      mannequinPoses[pose.mode] = { ...pose };
      if (mannequins.seated && mannequins.lying && mannequins['lying-second']) scheduleMove();
      else if (pose.visible) mannequinLoading ??= Promise.all([loadMannequin(), loadMannequin(), loadMannequin()]).then(([seated, lying, second]) => {
        mannequins.seated = seated;
        mannequins.lying = lying;
        mannequins['lying-second'] = second;
        scheduleMove();
      }).catch(error => onError(`Mannequin: ${error instanceof Error ? error.message : String(error)}`));
    },
    setExcludedComponents(paths: string[]) {
      const affected = new Set([...excludedComponents, ...paths]);
      excludedComponents = [...paths];
      if (!viewer?.ready) return;
      for (const path of affected) {
        const group = viewer.rendered.nestedGroup.groups[path];
        if (group) group.visible = !excludedComponents.includes(path);
      }
      (viewer as unknown as PieceViewer).idPicker?.setDirty();
      viewer.update(true, true);
    },
    getVisibility(paths: string[]): 'shown' | 'hidden' | 'mixed' {
      const states = viewer?.ready ? viewer.getStates() : {};
      const visible = Object.entries(states)
        .filter(([path]) => paths.some(root => path === root || path.startsWith(`${root}/`)))
        .map(([, state]) => state.some(value => value === 1));
      if (!visible.length || visible.every(Boolean)) return 'shown';
      return visible.some(Boolean) ? 'mixed' : 'hidden';
    },
    setVisibility(rules: Record<string, boolean>, independentRoots: string[] = []) {
      if (!viewer?.ready) return;
      const states: Record<string, number[]> = {};
      const hidden = Object.keys(rules).filter(path => !rules[path]);
      for (const [path, state] of Object.entries(viewer.getStates())) {
        // Independent references retain their own visibility when a containing
        // assembly is hidden. Their own switches and descendant filters still apply.
        const independent = independentRoots.find(root => path === root || path.startsWith(`${root}/`));
        const visible = !hidden.some(prefix => {
          if (independent?.startsWith(`${prefix}/`)) return false;
          return path === prefix || path.startsWith(`${prefix}/`);
        });
        states[path] = state.map(value => value === 3 ? 3 : Number(visible));
      }
      viewer.setStates(states);
      showTables();
      viewer.update(true, true);
    },
  };
}
