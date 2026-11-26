/// <reference types="vite/client" />
/** Our host for the installed OCP renderer. No second viewer or playback timeline. */
import { createViewerCamera, type CameraState, type CameraViewer } from './viewer-camera';
import { loadMannequin, seatedPose, lyingPose, secondLyingPose, type MannequinPose } from './mannequin';
import { createDuvet } from './duvet';
import { categories } from './visibility';
import { createPillows } from './pillows';
import { createCushionFoam } from './cushion-foam';
import { defaultFloorPattern, type FloorPatternSettings } from './floor-pattern';
import { applyFloorFinish } from './floor-finish';
import { createVehicleFade } from './vehicle-fade';
import { paintHitDistance, type ScanDisplay } from './scan-panels';
import { createViewerPieces, hasActiveTool, type PieceViewer } from './viewer-pieces';
import { createViewerDrag, type DragSnapshot } from './viewer-drag';
import { createViewerHuman, type HumanViewer } from './viewer-human';
import { createViewerPaint } from './viewer-paint';
import { createLayoutMirror } from './layout-mirror';
import { Box3, type Object3D, type Scene } from 'three';
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
interface CadViewer extends HumanViewer {
  display: {
    shapeFilterDropDownMenu: { setValue(value: string): void };
  };
  rendered: HumanViewer['rendered'] & {
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
  let visibilityRules: Record<string, boolean> = {};
  let unsubscribeTool: (() => void) | undefined;
  let socket: WebSocket | undefined;
  let cadActive = false;
  let pendingFocus: string | undefined;
  let motions: Record<string, Motion> = {};
  const positions: Record<string, number> = {};
  const bases = new Map<string, Vector>();
  const pendingMotions = new Set<string>();
  let mannequinPending = false;
  let motionFrame: number | null = null;
  let motionController: MotionController | undefined;
  const cameraKey = 'campervan.camera';
  let rendering = false;
  const cameraNavigation = createViewerCamera(container, () => viewer, cameraKey, () => rendering || human.isActive());
  const { cameraState, saveCamera, cancelCameraAnimation } = cameraNavigation;
  const mannequins: Partial<Record<MannequinPose['mode'], Awaited<ReturnType<typeof loadMannequin>>>> = {};
  let mannequinLoading: Promise<void> | undefined;
  const mannequinPoses = { seated: { ...seatedPose }, lying: { ...lyingPose }, 'lying-second': { ...secondLyingPose } };
  let seatCushion: ReturnType<typeof createCushionFoam> | undefined;
  const vehicleFade = createVehicleFade();
  const layoutMirror = createLayoutMirror();
  let floorSettings = defaultFloorPattern;
  let updateFloorFinish: ReturnType<typeof applyFloorFinish>;
  let scanDisplay: ScanDisplay | undefined;
  let scanVehicleOpacity: number | null = null;
  let crossSections: Object3D | undefined;
  const human = createViewerHuman(container, () => viewer,
    () => { paint.cancel(); cancelCameraAnimation(); drag.cancel(); }, saveCamera, () => pieces.orbitTarget());
  const pieces = createViewerPieces(container, () => viewer as unknown as PieceViewer | undefined,
    () => { cancelCameraAnimation(); human.cancel(); drag.cancel(); }, saveCamera, () => paint.isActive());
  const drag = createViewerDrag(container, {
    viewer: () => viewer as unknown as PieceViewer | undefined,
    motions: () => motions,
    pose: () => motionController?.snapshotPositions().positions ?? { ...positions },
    pick: pieces.pickPoint,
    painting: () => paint.isActive(),
    preview: previewPose,
    save: () => { void saveAcceptedPositions(); },
    snapshot: () => motionController?.snapshotPositions() ?? { positions: { ...positions } },
    restore: snapshot => motionController?.restorePositions(snapshot),
  });
  const paint = createViewerPaint(container, {
    pick(event, sample = false) {
      const scan = scanDisplay?.root.visible ? scanDisplay : undefined;
      const cloth = duvet?.mesh;
      if (!scan && !cloth?.visible) {
        if (sample) return pieces.pickPoint(event);
        const path = pieces.pickPath(event);
        return path ? { path } : null;
      }
      const opacity = scan ? scanVehicleOpacity ?? 1 : 1;
      return pieces.pickPoint(event, (ray, cad) => {
        let nearest = cad;
        if (cloth?.visible) {
          const hit = ray.intersectObject(cloth, false)[0];
          if (hit && hit.distance < paintHitDistance(ray, cad, opacity)) {
            nearest = { path: cloth.name, point: hit.point, hit };
          }
        }
        return scan ? scan.pickPaint(ray, nearest, opacity, sample) : nearest;
      });
    },
    modeChanged(active) {
      if (active) { cancelCameraAnimation(); human.cancel(); }
      drag.toolChanged();
      pieces.toolChanged();
    },
    redraw() { if (viewer?.ready) viewer.update(true, false); },
    error: onError,
  });
  pieces.setCommands(() => [...human.commands(), ...drag.commands(), ...paint.commands()]);

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
  let duvet: ReturnType<typeof createDuvet> | undefined;
  let duvetFitted = false;
  function updateDuvetVisibility() {
    if (!duvet) return;
    const visible = duvetFitted && categories.cushions.every(path =>
      !Object.entries(visibilityRules).some(([root, shown]) => !shown && (path === root || path.startsWith(`${root}/`))));
    if (duvet.mesh.visible && !visible) paint.clearPointer();
    duvet.mesh.visible = visible;
  }

  let pillows = createPillows();
  if (import.meta.hot) import.meta.hot.accept('./pillows', module => {
    if (!module || !viewer?.ready) return;
    pillows = module.createPillows();
    layoutMirror.inOriginalCoordinates(() => {
      pillows.attach(viewer!.rendered.nestedGroup.groups);
      const lid = positions.bed_lid_open_percent ?? motions.bed_lid_open_percent?.position ?? 0;
      const bed = positions.bed_extension_percent ?? motions.bed_extension_percent?.position ?? 0;
      pillows.pose(bed, lid);
      pillows.squash(bed);
    });
    viewer.update(true, true);
  });
  let seeInside = false;

  function updateScanVisibility() {
    const vehicleVisible = visibilityRules['/Campervan/Vehicle references'] !== false;
    if (scanDisplay) scanDisplay.root.visible = vehicleVisible;
    vehicleFade.setComparisonOpacity(scanDisplay && vehicleVisible ? scanVehicleOpacity : null);
  }

  function showMannequin(render = true) {
    if (!viewer?.ready) return;
    layoutMirror.inOriginalCoordinates(() => {
      const lid = positions.bed_lid_open_percent ?? motions.bed_lid_open_percent?.position ?? 0;
      const bed = positions.bed_extension_percent ?? motions.bed_extension_percent?.position ?? 0;
      pillows.pose(bed, lid);
      duvetFitted = false;
      fitMannequin();
      updateDuvetVisibility();
      pillows.squash(bed);
      for (const model of Object.values(mannequins)) layoutMirror.add(model.root);
    });
    if (render) viewer.update(true, false);
  }

  function renderFoam() {
    if (!viewer?.ready) return;
    (viewer as unknown as PieceViewer).idPicker?.setDirty();
    viewer.update(true, false);
  }

  function fitMannequin() {
    if (!viewer?.ready) return;
    const bed = positions.bed_extension_percent ?? motions.bed_extension_percent?.position ?? 0;
    for (const model of Object.values(mannequins)) model.root.visible = false;
    const groups = viewer.rendered.nestedGroup.groups;
    const seat = groups['/Campervan/Long bench/Cushions/Long seat/Foam/Core'] as unknown as Object3D;
    const back = groups['/Campervan/Long bench/Cushions/Wall backrest/Foam/Core'] as unknown as Object3D;
    const crossSeat = groups['/Campervan/Cross bench/Cushions/Cross seat/Foam/Core'] as unknown as Object3D;
    if (!seat || !back || !crossSeat) return;
    seatCushion ??= createCushionFoam(seat, back, crossSeat, renderFoam,
      operation => layoutMirror.inOriginalCoordinates(operation));
    if ((positions.bed_lid_open_percent ?? motions.bed_lid_open_percent?.position ?? 0) > 0) {
      seatCushion.deform(null, positions.bed_lid_open_percent ?? motions.bed_lid_open_percent?.position ?? 0);
      pillows.supportHead(null); pillows.supportHead(null, false);
      onMannequinStatus('Close the storage lid to show the seated preview.');
      return;
    }
    pillows.supportHead(null);
    pillows.supportHead(null, false);
    if (bed === 100) {
      seatCushion.deform(null);
      const mattress = seatCushion.mattressBounds();
      const sleepers: Object3D[] = [];
      let pillowEdge = mattress.max.y;
      let feetOutside = false;
      for (const id of ['lying', 'lying-second'] as const) {
        const model = mannequins[id];
        const pose = mannequinPoses[id];
        const first = id === 'lying';
        const path = first ? '/Campervan/Cross bench/Cushions/Front pillow/Pillow'
          : '/Campervan/Long bench/Cushions/Rear pillow/Pillow';
        const pillow = groups[path] as unknown as Object3D;
        if (!pillow) continue;
        const bounds = new Box3().setFromObject(pillow);
        pillowEdge = Math.min(pillowEdge, bounds.min.y);
        if (!model || !pose.visible) continue;
        const fitted = model.lie(pose, mattress, bounds);
        model.attach(viewer.rendered.scene);
        sleepers.push(model.root);
        pillows.supportHead(fitted.head, first);
        feetOutside ||= fitted.feet.min.y < mattress.min.y;
      }
      duvetFitted = duvet?.fit(mattress, pillowEdge, sleepers) ?? false;
      onMannequinStatus(feetOutside ? 'Feet extend beyond the mattress.' : '');
      return;
    }
    const mannequin = mannequins.seated;
    if (!mannequin) { seatCushion.deform(null); return; }
    const mannequinPose = mannequinPoses.seated;
    const visible = mannequinPose.visible && bed === 0;
    const floor = groups['/Campervan/Finished floor plywood'] as unknown as Object3D;
    if (!floor) return;
    const floorZ = new Box3().setFromObject(floor).max.z;
    const fitted = mannequin.seat({ ...mannequinPose, visible }, seatCushion.bounds(),
      new Box3().setFromObject(back).min.x, floorZ);
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
      const path = `/Campervan/Laptop table/${name}`;
      const group = viewer.rendered.nestedGroup.groups[path];
      const hidden = Object.entries(visibilityRules).some(([root, visible]) =>
        !visible && (path === root || path.startsWith(`${root}/`)));
      const excluded = excludedComponents.some(root => path === root || path.startsWith(`${root}/`));
      if (group) group.visible = selected === value && !hidden && !excluded;
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
    const lidChanged = !changed || changed.has('bed_lid_open_percent');
    const foamChanged = bedChanged || lidChanged || mannequinChanged;
    if (!changed || changed.has('table_mount')) showTables();
    if (foamChanged) showMannequin(false);
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
      void paint.load();
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
          const nativeHover = this.pickingController.hoverPreselectActive.bind(this.pickingController);
          this.pickingController.hoverPreselectActive = () => hasActiveTool(this as unknown as PieceViewer) && nativeHover();
          this.reset = () => pieces.resetCommand().run();
          this.display.resize = () => pieces.resetCommand().run();
          unsubscribeTool?.();
          unsubscribeTool = (this as unknown as PieceViewer).state.subscribe('activeTool', () => {
            const measuring = hasActiveTool(this as unknown as PieceViewer);
            this.pickingController.clearHover();
            paint.toolChanged(measuring);
            drag.toolChanged(); pieces.toolChanged(); human.toolChanged(measuring);
            if (measuring) this.display.shapeFilterDropDownMenu.setValue('All');
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
          if (cadActive && socket?.readyState === WebSocket.OPEN) socket.send(`U:${JSON.stringify({ command, text: message })}`);
        },
      });
      const allowed = new Set(['perspective', 'transparent', 'blackedges', 'reset', 'distance']);
      if (isStaticSite) allowed.delete('distance');
      function trimToolbar() {
        // createPage clears the host when it creates the first display.
        cameraNavigation.attachCube();
        for (const child of container.querySelectorAll<HTMLElement>('.tcv_cad_toolbar > *')) {
          const button = child.querySelector('input[class*="tcv_button_"]');
          if (button && [...allowed].some(name => button.classList.contains(`tcv_button_${name}`))) {
            child.dataset.campervanControl = 'true';
            if (button.classList.contains('tcv_button_reset')) {
              const action = pieces.resetCommand();
              button.setAttribute('aria-label', action.label);
              button.setAttribute('aria-keyshortcuts', action.ariaShortcut!);
              button.setAttribute('title', `${action.label} · ${action.shortcut}`);
              (button as HTMLInputElement).onclick = action.run;
            }
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
          if (message.type === 'data') human.cancel();
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
            scanDisplay?.root.removeFromParent();
            crossSections?.removeFromParent();
            drag.cancel();
            pieces.clear();
            paint.detach();
            vehicleFade.clear();
            layoutMirror.clear();
            duvet?.dispose();
            duvet = undefined;
            duvetFitted = false;
            Object.values(mannequins).forEach(model => model.root.removeFromParent());
            seatCushion?.dispose();
            seatCushion = undefined;
          }
          try { page.handleMessage(message); }
          finally { rendering = false; }
          if (message.type === 'data') {
            updateFloorFinish = applyFloorFinish(viewer!.rendered.nestedGroup.groups);
            updateFloorFinish?.(floorSettings);
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
            const frame = viewer!.rendered.nestedGroup.groups['/Campervan/Cabinet/Lower module/Frames'];
            const cabinetBounds = new Box3();
            if (frame) cabinetBounds.setFromObject(frame as unknown as Object3D);
            duvet = createDuvet(cabinetBounds);
            viewer!.rendered.scene.add(duvet.mesh);
            layoutMirror.add(duvet.mesh);
            layoutMirror.attach(viewer!.rendered.nestedGroup.groups);
            if (scanDisplay) viewer!.rendered.scene.add(scanDisplay.root);
            if (crossSections) viewer!.rendered.scene.add(crossSections);
            motions = {};
            bases.clear();
            trimToolbar();
            pieces.attach();
            drag.attach();
            human.attach();
            page.resize();
            if (camera && viewer?.ready) {
              const projection = viewer.rendered.camera.camera;
              // Perspective zoom is already encoded by position. Orthographic zoom depends on the new frustum.
              const zoom = camera.ortho
                ? camera.viewHeight ? (projection.top - projection.bottom) / camera.viewHeight : camera.zoom
                : null;
              viewer.setCameraLocationSettings(camera.position, camera.quaternion, camera.target, zoom, false);
            }
            cameraNavigation.applyFieldOfView();
            saveCamera();
            onModel();
            if (pendingFocus) {
              if (!pieces.focus(pendingFocus)) onError('This piece is not in the displayed CAD model yet.');
              pendingFocus = undefined;
            }
            showTables();
            showMannequin();
            paint.attach(viewer!.rendered.nestedGroup.groups, message.stockTextures ?? {}, duvet.mesh);
            viewer!.update(true, false);
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
        socket!.onopen = () => { if (cadActive) socket!.send('L:{}'); resolve(); };
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
    setCadActive(active: boolean) {
      if (active === cadActive) return;
      cadActive = active;
      if (socket?.readyState === WebSocket.OPEN) socket.send(active ? 'L:{}' : 'X:{}');
      if (!active) {
        pendingFocus = undefined;
        human.cancel(); drag.cancel(); paint.cancel();
      }
    },
    setMotionController(controller: MotionController) { motionController = controller; },
    getFieldOfView: cameraNavigation.getFieldOfView,
    setFloorPattern(settings: FloorPatternSettings) {
      floorSettings = settings;
      updateFloorFinish?.(settings);
      viewer?.update(true, false);
    },
    setFieldOfView(degrees: number) {
      cameraNavigation.setFieldOfView(degrees);
      viewer?.update(true, false);
    },
    setScanReference(scan?: ScanDisplay, vehicleOpacity?: number, scanOpacity = 1) {
      paint.clearPointer();
      if (scanDisplay !== scan) {
        scanDisplay?.root.removeFromParent();
        scanDisplay = scan;
        paint.setScanPaintPanels(scan?.paintPanels ?? []);
        if (scanDisplay && viewer?.ready) viewer.rendered.scene.add(scanDisplay.root);
      }
      vehicleFade.setScanPanels(scan?.panels ?? [], scanOpacity);
      scanVehicleOpacity = vehicleOpacity ?? null;
      updateScanVisibility();
      viewer?.update(true, false);
    },
    setCrossSections(root: Object3D) {
      if (crossSections !== root) crossSections?.removeFromParent();
      crossSections = root;
      if (viewer?.ready && root.parent !== viewer.rendered.scene) viewer.rendered.scene.add(root);
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
    setPieceLink: pieces.setLink,
    focusPiece(path: string) {
      if (viewer?.ready) return pieces.focus(path);
      pendingFocus = path;
      return true;
    },
    setSeeInside(enabled: boolean) {
      seeInside = enabled;
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
    setVisibility(rules: Record<string, boolean>) {
      visibilityRules = { ...rules };
      updateDuvetVisibility();
      updateScanVisibility();
      if (!viewer?.ready) return;
      const states: Record<string, number[]> = {};
      const hidden = Object.keys(rules).filter(path => !rules[path]);
      for (const [path, state] of Object.entries(viewer.getStates())) {
        const visible = !hidden.some(root => path === root || path.startsWith(`${root}/`));
        states[path] = state.map(value => value === 3 ? 3 : Number(visible));
      }
      viewer.setStates(states);
      showTables();
      viewer.update(true, true);
    },
  };
}
