import { createViewCube } from './view-cube';

export interface CameraState {
  position: number[]; quaternion: number[]; target: number[]; zoom: number; ortho: boolean; viewHeight?: number;
}
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
export interface CameraViewer {
  ready: boolean;
  rendered: { camera: { camera: CameraPose & { top: number; bottom: number } } };
  getCameraPosition(): number[];
  getCameraQuaternion(): number[];
  getCameraTarget(): number[];
  getCameraZoom(): number;
  getOrtho(): boolean;
  setCameraLocationSettings(position: number[], quaternion: number[], target: number[], zoom: number | null,
    notify: boolean): void;
}

/** Shared camera persistence and view cube for CAD and scan surfaces. */
export function createViewerCamera(container: HTMLElement, current: () => CameraViewer | undefined,
  cameraKey: string, isRendering: () => boolean = () => false) {
  let cameraAnimation: number | null = null;
  let cube: ReturnType<typeof createViewCube> | undefined;
  function cancelCameraAnimation() {
    if (cameraAnimation !== null) cancelAnimationFrame(cameraAnimation);
    cameraAnimation = null;
  }
  container.addEventListener('pointerdown', cancelCameraAnimation, { capture: true });
  container.addEventListener('wheel', cancelCameraAnimation, { capture: true, passive: true });
  container.addEventListener('keydown', cancelCameraAnimation, { capture: true });

  function cameraState(): CameraState | null {
    const viewer = current();
    return viewer?.ready ? {
      position: viewer.getCameraPosition(), quaternion: viewer.getCameraQuaternion(),
      target: viewer.getCameraTarget(), zoom: viewer.getCameraZoom(), ortho: viewer.getOrtho(),
      viewHeight: viewer.getOrtho()
        ? (viewer.rendered.camera.camera.top - viewer.rendered.camera.camera.bottom) / viewer.getCameraZoom()
        : undefined,
    } : null;
  }

  function saveCamera() {
    if (isRendering()) return;
    const camera = cameraState();
    if (camera) localStorage.setItem(cameraKey, JSON.stringify(camera));
  }
  window.addEventListener('pagehide', saveCamera);

  function setDirection(direction: [number, number, number], animate = true) {
    const viewer = current();
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

  return {
    cameraState, saveCamera, cancelCameraAnimation,
    attachCube() {
      cube ??= createViewCube(container, setDirection, orbitCube);
      this.updateCube();
    },
    updateCube() {
      const viewer = current();
      if (viewer?.ready) cube?.update(viewer.getCameraQuaternion());
    },
  };
}
