/** Our host for the installed OCP renderer. No second viewer or playback timeline. */
import { createViewCube } from './view-cube';
import { loadMannequin, type MannequinPose } from './mannequin';
import { createSeatCushion } from './seat-cushion';
import { Box3, type Object3D, type Scene } from 'three';

type Axis = 'x' | 'y' | 'z';
interface Track {
  path: string; axis: Axis; kind?: 'rotation' | 'translation';
  travel?: number; keyframes?: [number, number][];
}
interface Motion { position: number; tracks: Track[] }
interface Vector { x: number; y: number; z: number }
interface CameraState {
  position: number[]; quaternion: number[]; target: number[]; zoom: number; ortho: boolean; viewHeight?: number;
}
interface SceneGroup { position: Vector; rotation: Vector; updateMatrixWorld(force: boolean): void }
interface CameraQuaternion {
  toArray(): number[];
  clone(): CameraQuaternion;
  angleTo(other: CameraQuaternion): number;
  slerp(other: CameraQuaternion, fraction: number): CameraQuaternion;
}
interface CameraVector {
  set(x: number, y: number, z: number): CameraVector;
  clone(): CameraVector;
  applyQuaternion(quaternion: CameraQuaternion): CameraVector;
  toArray(): number[];
}
interface CameraPose {
  position: CameraVector;
  up: { set(x: number, y: number, z: number): void };
  quaternion: CameraQuaternion;
  lookAt(x: number, y: number, z: number): void;
  clone(): CameraPose;
}
interface CadViewer {
  ready: boolean;
  rendered: {
    scene: Scene;
    nestedGroup: { groups: Record<string, SceneGroup> };
    orientationMarker: { setVisible(value: boolean): void };
    camera: { camera: CameraPose & { top: number; bottom: number } };
  };
  getStates(): Record<string, number[]>;
  setStates(states: Record<string, number[]>): void;
  getCameraPosition(): number[];
  getCameraQuaternion(): number[];
  getCameraTarget(): number[];
  getCameraZoom(): number;
  getOrtho(): boolean;
  setCameraLocationSettings(position: number[], quaternion: number[], target: number[], zoom: number | null, notify: boolean): void;
  update(change: boolean, controls: boolean): void;
}

export function createCadViewer(container: HTMLElement, onModel: () => void, onError: (message: string) => void,
  onMannequinStatus: (message: string) => void = () => {},
  onMannequinFit: (pose: Pick<MannequinPose, 'x' | 'y' | 'z' | 'facing' | 'hip' | 'knee'>) => void = () => {}) {
  let viewer: CadViewer | undefined;
  let cube: ReturnType<typeof createViewCube> | undefined;
  let socket: WebSocket | undefined;
  let motions: Record<string, Motion> = {};
  const positions: Record<string, number> = {};
  const bases = new Map<string, Vector>();
  const cameraKey = 'campervan.camera';
  let rendering = false;
  let cameraAnimation: number | null = null;
  let mannequin: Awaited<ReturnType<typeof loadMannequin>> | undefined;
  let mannequinLoading: Promise<void> | undefined;
  let mannequinPose: MannequinPose;
  let seatCushion: ReturnType<typeof createSeatCushion> | undefined;

  function showMannequin() {
    if (!mannequin || !viewer?.ready) return;
    const groups = viewer.rendered.nestedGroup.groups;
    const seat = groups['/Campervan/Long bench/Cushions/Long seat/Foam'] as unknown as Object3D;
    const back = groups['/Campervan/Long bench/Cushions/Wall backrest/Foam'] as unknown as Object3D;
    if (!seat || !back) return;
    seatCushion ??= createSeatCushion(seat);
    const bed = positions.bed_extension_percent ?? motions.bed_extension_percent?.position ?? 0;
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
    viewer.update(true, false);
  }

  function cancelCameraAnimation() {
    if (cameraAnimation !== null) cancelAnimationFrame(cameraAnimation);
    cameraAnimation = null;
  }
  container.addEventListener('pointerdown', cancelCameraAnimation, { capture: true });
  container.addEventListener('wheel', cancelCameraAnimation, { capture: true, passive: true });
  container.addEventListener('keydown', cancelCameraAnimation, { capture: true });

  function cameraState(): CameraState | null {
    return viewer?.ready ? {
      position: viewer.getCameraPosition(), quaternion: viewer.getCameraQuaternion(),
      target: viewer.getCameraTarget(), zoom: viewer.getCameraZoom(), ortho: viewer.getOrtho(),
      viewHeight: viewer.getOrtho()
        ? (viewer.rendered.camera.camera.top - viewer.rendered.camera.camera.bottom) / viewer.getCameraZoom()
        : undefined,
    } : null;
  }

  function saveCamera() {
    if (rendering) return;
    const camera = cameraState();
    if (camera) localStorage.setItem(cameraKey, JSON.stringify(camera));
  }
  window.addEventListener('pagehide', saveCamera);

  function setDirection(direction: [number, number, number], animate = true) {
    cancelCameraAnimation();
    const state = cameraState();
    if (!state || !viewer) return;
    const distance = Math.hypot(...state.position.map((value, i) => value - state.target[i]));
    const size = Math.hypot(...direction);
    const position = direction.map((value, i) => state.target[i] + value * distance / size);
    const pose = viewer.rendered.camera.camera.clone();
    const startRotation = pose.quaternion.clone();
    pose.position.set(position[0], position[1], position[2]);
    // Upright side/corner views; stable plan orientations at the two poles.
    if (direction[0] === 0 && direction[1] === 0) pose.up.set(0, direction[2] > 0 ? 1 : -1, 0);
    else pose.up.set(0, 0, 1);
    pose.lookAt(state.target[0], state.target[1], state.target[2]);
    const duration = animate ? startRotation.angleTo(pose.quaternion) / Math.PI * 500 : 0;
    if (duration < 1) {
      viewer.setCameraLocationSettings(position, pose.quaternion.toArray(), state.target, state.ortho ? state.zoom : null, true);
      saveCamera();
      return;
    }
    const started = performance.now();
    const tick = (now: number) => {
      if (!viewer?.ready) { cameraAnimation = null; return; }
      const fraction = Math.min((now - started) / duration, 1);
      // Three.js supplies shortest-path spherical interpolation: 360 degrees per second.
      const rotation = startRotation.clone().slerp(pose.quaternion, fraction);
      const offset = pose.position.clone().set(0, 0, distance).applyQuaternion(rotation).toArray();
      const nextPosition = offset.map((value, i) => state.target[i] + value);
      viewer.setCameraLocationSettings(nextPosition, rotation.toArray(), state.target, state.ortho ? state.zoom : null, fraction === 1);
      if (fraction < 1) cameraAnimation = requestAnimationFrame(tick);
      else { cameraAnimation = null; saveCamera(); }
    };
    cameraAnimation = requestAnimationFrame(tick);
  }

  function orbitCube(dx: number, dy: number) {
    const state = cameraState();
    if (!state) return;
    const [x, y, z] = state.position.map((value, i) => value - state.target[i]);
    const azimuth = Math.atan2(y, x) - dx * 0.012;
    const elevation = Math.max(-Math.PI / 2 + 0.01, Math.min(Math.PI / 2 - 0.01,
      Math.atan2(z, Math.hypot(x, y)) + dy * 0.012));
    setDirection([Math.cos(azimuth) * Math.cos(elevation), Math.sin(azimuth) * Math.cos(elevation), Math.sin(elevation)], false);
  }

  function move() {
    if (!viewer?.ready) return;
    for (const [name, motion] of Object.entries(motions)) {
      const percent = positions[name] ?? motion.position;
      const fraction = (percent - motion.position) / 100;
      for (const track of motion.tracks) {
        const group = viewer.rendered.nestedGroup.groups[track.path];
        const base = bases.get(`${track.path}:${track.kind ?? 'translation'}`);
        if (!group || !base) continue;
        const transform = track.kind === 'rotation' ? group.rotation : group.position;
        const units = track.kind === 'rotation' ? Math.PI / 180 : 1;
        if (track.keyframes) {
          const points = track.keyframes;
          const endIndex = points.findIndex(([position], index) => index > 0 && position >= percent);
          const [start, a] = points[endIndex - 1];
          const [end, b] = points[endIndex];
          transform[track.axis] = (a + (b - a) * (percent - start) / (end - start)) * units;
        } else {
          transform[track.axis] = base[track.axis] + fraction * track.travel! * units;
        }
        group.updateMatrixWorld(true);
      }
    }
    showMannequin();
    viewer.update(true, true);
  }

  return {
    async connect(url: string) {
      const css = document.createElement('link');
      css.rel = 'stylesheet';
      css.href = '/viewer-assets/css/three-cad-viewer.css';
      const styles = new Promise<void>((resolve, reject) => {
        css.onload = () => resolve();
        css.onerror = () => reject(new Error('Could not load CAD viewer styles.'));
      });
      document.head.append(css);
      // Serve JS and CSS from the locked Python package, keeping both halves compatible.
      const rendererUrl = '/viewer-assets/js/three-cad-viewer.esm.js';
      const coreUrl = '/viewer-assets/js/ocp-viewer-core/index.js';
      const [library, core] = await Promise.all([
        import(/* @vite-ignore */ rendererUrl), import(/* @vite-ignore */ coreUrl), styles,
      ]);
      // createPage accepts the Viewer constructor; capture its instance while reusing
      // OCP's geometry loading and measurement messages.
      class HostedViewer extends library.Viewer {
        constructor(...args: any[]) {
          super(...args);
          viewer = this as unknown as CadViewer;
          const update = this.update.bind(this);
          this.update = (...updateArgs: any[]) => {
            update(...updateArgs);
            if (this.ready) cube?.update(this.getCameraQuaternion());
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
      function trimToolbar() {
        // createPage clears the host when it creates the first display.
        cube ??= createViewCube(container, setDirection, orbitCube);
        for (const child of container.querySelectorAll<HTMLElement>('.tcv_cad_toolbar > *')) {
          const button = child.querySelector('input[class*="tcv_button_"]');
          if (button && [...allowed].some(name => button.classList.contains(`tcv_button_${name}`))) {
            child.dataset.campervanControl = 'true';
          }
        }
        viewer?.rendered.orientationMarker.setVisible(true);
        if (viewer?.ready) cube?.update(viewer.getCameraQuaternion());
      }
      const endpoint = new URL(url);
      endpoint.protocol = endpoint.protocol === 'https:' ? 'wss:' : 'ws:';
      endpoint.pathname = '/';
      socket = new WebSocket(endpoint);
      socket.onmessage = event => {
        try {
          const message = JSON.parse(event.data);
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
              mannequin?.root.removeFromParent();
              seatCushion?.dispose();
              seatCushion = undefined;
            }
            try { page.handleMessage(message); }
            finally { rendering = false; }
            if (message.type === 'data') {
              motions = {};
              bases.clear();
              trimToolbar();
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
              showMannequin();
            }
          }
        } catch (error) { onError(error instanceof Error ? error.message : String(error)); }
      };
      new ResizeObserver(() => { if (viewer?.ready) page.resize(); }).observe(container);
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
    setPosition(name: string, percent: number) { positions[name] = percent; move(); },
    setMannequinPose(pose: MannequinPose) {
      mannequinPose = { ...pose };
      if (mannequin) showMannequin();
      else if (pose.visible) mannequinLoading ??= loadMannequin().then(model => {
        mannequin = model;
        showMannequin();
      }).catch(error => onError(`Mannequin: ${error instanceof Error ? error.message : String(error)}`));
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
      if (!viewer?.ready) return;
      const states: Record<string, number[]> = {};
      const hidden = Object.keys(rules).filter(path => !rules[path]);
      for (const [path, state] of Object.entries(viewer.getStates())) {
        // Every containing assembly and content filter must permit visibility.
        const visible = !hidden.some(prefix => path === prefix || path.startsWith(`${prefix}/`));
        states[path] = state.map(value => value === 3 ? 3 : Number(visible));
      }
      viewer.setStates(states);
    },
  };
}
