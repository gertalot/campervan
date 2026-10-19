import { Quaternion, Vector3, type Material, type Object3D } from 'three';

type Direction = [number, number, number];
interface CadGroup extends Object3D {
  front?: { material: Material };
  back?: { material: Material };
  edges?: { material: Material };
  setTransparent(flag: boolean): void;
  transparent: boolean;
}

const left: Direction = [-1, 0, 0], right: Direction = [1, 0, 0];
const rear: Direction = [0, -1, 0], roof: Direction = [0, 0, 1], floor: Direction = [0, 0, -1];

function directions(path: string): Direction[] {
  const prefix = '/Campervan/Vehicle references/';
  if (!path.startsWith(prefix)) return [];
  const part = path.slice(prefix.length);
  if (part.startsWith('Rear corners/')) return [part.includes('Left') ? left : right, rear];
  if (part.startsWith('Roof/Side rails/')) return [part.includes('Left') ? left : right, roof];
  if (part.startsWith('Roof/Rear header')) return [roof, rear];
  if (part.startsWith('Roof/') || part.startsWith('Cab/Headliner')) return [roof];
  if (part.startsWith('Body floor/') || part.startsWith('Cab/Floor') || part === 'Floor outline') return [floor];
  if (part.startsWith('Rear opening/')) return [rear];
  if (['Side walls/', 'Sliding doors/', 'Wheel arches/'].some(prefix => part.startsWith(prefix))) {
    return [part.includes('Left') ? left : right];
  }
  return [];
}

/** Fade vehicle sides, without touching visibility, geometry, or furniture materials. */
export function createVehicleFade() {
  type Entry = { group: CadGroup; directions: Direction[]; maxOpacity: number; materials: {
    material: Material; edge: boolean; opacity: number; transparent: boolean; depthWrite: boolean;
  }[] };
  let entries: Entry[] = [];
  const towardCamera = new Vector3();
  const rotation = new Quaternion();

  function restore() {
    for (const { group, materials } of entries) {
      for (const { material, opacity, transparent, depthWrite } of materials) {
        material.opacity = opacity;
        material.transparent = transparent;
        material.depthWrite = depthWrite;
        material.needsUpdate = true;
      }
      // Respect the OCP transparency toolbar's current setting, including changes while fading.
      group.setTransparent(group.transparent);
    }
  }

  return {
    attach(groups: Record<string, unknown>) {
      entries = [];
      for (const [path, object] of Object.entries(groups)) {
        const normals = directions(path);
        if (!normals.length) continue;
        const group = object as CadGroup;
        const materials: Entry['materials'] = [];
        for (const [mesh, edge] of [[group.front, false], [group.back, false], [group.edges, true]] as const) {
          if (!mesh) continue;
          const { material } = mesh;
          materials.push({ material, edge, opacity: material.opacity,
            transparent: material.transparent, depthWrite: material.depthWrite });
        }
        if (materials.length) entries.push({ group, directions: normals, materials,
          maxOpacity: path.endsWith('/Window glass') ? group.front?.material.opacity ?? 0.12 : 0.7 });
      }
    },
    clear() { entries = []; },
    restore,
    update(quaternion: number[]) {
      // Camera local +Z points toward the observer in both orthographic and perspective views.
      towardCamera.set(0, 0, 1).applyQuaternion(rotation.fromArray(quaternion));
      for (const entry of entries) {
        const facing = Math.max(...entry.directions.map(([x, y, z]) =>
          x * towardCamera.x + y * towardCamera.y + z * towardCamera.z));
        const t = Math.max(0, Math.min(1, (facing + 0.35) / 0.7));
        const near = t * t * (3 - 2 * t);
        for (const { material, edge } of entry.materials) {
          if (!material.transparent) { material.transparent = true; material.needsUpdate = true; }
          material.depthWrite = false;
          material.opacity = edge ? 0.5 - 0.48 * near : entry.maxOpacity * (1 - near * 0.65 / 0.7);
        }
      }
    },
  };
}
