import { Quaternion, Vector3, type BufferGeometry, type Color, type Material, type Mesh, type Object3D } from 'three';

type ColouredMaterial = Material & { color?: Color };

type Direction = [number, number, number];
interface CadGroup extends Object3D {
  front?: Mesh<BufferGeometry, Material>;
  back?: Mesh<BufferGeometry, Material>;
  edges?: { material: Material };
}

const left: Direction = [-1, 0, 0], right: Direction = [1, 0, 0];
const front: Direction = [0, 1, 0], rear: Direction = [0, -1, 0];
const roof: Direction = [0, 0, 1], floor: Direction = [0, 0, -1];

function setOpacity(material: Material, opacity: number, edge: boolean) {
  material.opacity = opacity;
  // Fully opaque panels belong in the depth-writing opaque pass.
  const transparent = opacity < 1;
  if (material.transparent !== transparent) {
    material.transparent = transparent;
    material.needsUpdate = true;
  }
  material.depthWrite = !edge && !transparent;
}

function directions(path: string): Direction[] {
  if (path === '/Campervan/Finished floor plywood') return [floor];
  const prefix = '/Campervan/Vehicle references/';
  if (!path.startsWith(prefix)) return [];
  const part = path.slice(prefix.length);
  if (part.startsWith('Cab/Seats/')) return [front];
  // These are side-wall returns. A rearward direction would also fade the far corner.
  if (part.startsWith('Rear corners/')) return [part.includes('Left') ? left : right];
  if (part.startsWith('Roof/Side rails/')) return [part.includes('Left') ? left : right, roof];
  if (part.startsWith('Roof/Rear header')) return [roof, rear];
  if (part.startsWith('Roof/') || part.startsWith('Cab/Headliner')) return [roof];
  if (part.startsWith('Body floor/') || part.startsWith('Cab/Floor') || part === 'Floor outline') return [floor];
  if (part.startsWith('Rear opening/')) return [rear];
  if (['Side walls/', 'Sliding doors/'].some(prefix => part.startsWith(prefix))) {
    return [part.includes('Left') ? left : right];
  }
  return [];
}

/** Fade vehicle sides, without touching visibility, geometry, or furniture materials. */
export function createVehicleFade() {
  type Entry = {
    group: CadGroup; directionFrame?: Object3D; skipPick: boolean; directions: Direction[];
    vehicle: boolean; maxOpacity: number; fadeAmount: number;
    materials: { material: ColouredMaterial; edge: boolean; originalColor?: Color }[];
  };
  let entries: Entry[] = [];
  let pickingVersion = 0;
  let comparisonOpacity: number | null = null;
  const towardCamera = new Vector3();
  const panelNormal = new Vector3();
  const camera = new Vector3(), fromPanel = new Vector3();
  const rotation = new Quaternion();
  function skipPicking(entry: Entry, skip: boolean) {
    if (entry.skipPick !== skip) { entry.skipPick = skip; pickingVersion++; }
  }

  function comparisonStyle(entry: Entry, near = 0): boolean {
    if (!entry.vehicle || comparisonOpacity === null) return false;
    skipPicking(entry, near > 0.5 || comparisonOpacity === 0 || entry.maxOpacity === 0);
    for (const { material, edge } of entry.materials) {
      setOpacity(material, edge ? Math.min(1, comparisonOpacity * 2) * (1 - 0.96 * near)
        : Math.min(entry.maxOpacity, comparisonOpacity) * (1 - near * entry.fadeAmount), edge);
    }
    return true;
  }

  function comparisonColors() {
    for (const entry of entries) {
      if (!entry.vehicle) continue;
      for (const { material, edge, originalColor } of entry.materials) {
        if (!material.color || !originalColor) continue;
        if (comparisonOpacity === null) material.color.copy(originalColor);
        else material.color.set(edge ? '#d980a4' : '#f4b9ce');
      }
    }
  }

  function setExteriorOpacity() {
    for (const entry of entries) {
      if (comparisonStyle(entry)) continue;
      const { materials, maxOpacity } = entry;
      skipPicking(entry, maxOpacity === 0);
      for (const { material, edge } of materials) {
        setOpacity(material, edge ? 1 : maxOpacity, edge);
      }
    }
  }

  return {
    attach(groups: Record<string, unknown>) {
      entries = [];
      const hatchPath = '/Campervan/Vehicle references/Rear opening/Rear hatch';
      const hatch = groups[hatchPath] as Object3D | undefined;
      for (const [path, object] of Object.entries(groups)) {
        const vehicle = path.startsWith('/Campervan/Vehicle references/');
        const opaque = path.startsWith('/Campervan/Vehicle references/Wheel arches/');
        const normals = directions(path);
        if (!normals.length && !vehicle) continue;
        const group = object as CadGroup;
        const materials: Entry['materials'] = [];
        for (const [mesh, edge] of [[group.front, false], [group.back, false], [group.edges, true]] as const) {
          if (!mesh) continue;
          const material = mesh.material as ColouredMaterial;
          materials.push({ material, edge, originalColor: material.color?.clone() });
        }
        const glass = path.endsWith('/Window glass');
        const rearGlass = glass && path.startsWith('/Campervan/Vehicle references/Rear opening/');
        if (materials.length) entries.push({ group, vehicle,
          directionFrame: path === hatchPath || path.startsWith(`${hatchPath}/`) ? hatch : undefined,
          skipPick: false, directions: normals, materials,
          fadeAmount: opaque ? 0 : path.startsWith('/Campervan/Vehicle references/Cab/Seats/') ? 0.75 : 0.95,
          maxOpacity: rearGlass ? 0 : glass ? 0.3 : 1 });
      }
      comparisonColors();
    },
    clear() { entries = []; pickingVersion++; },
    setComparisonOpacity(opacity: number | null) {
      const changed = (comparisonOpacity === null) !== (opacity === null);
      comparisonOpacity = opacity;
      if (changed) comparisonColors();
    },
    get pickingVersion() { return pickingVersion; },
    withPicking<T>(pick: () => T): T {
      const hidden = entries.filter(entry => entry.skipPick && entry.group.visible);
      for (const entry of hidden) entry.group.visible = false;
      try { return pick(); }
      finally { for (const entry of hidden) entry.group.visible = true; }
    },
    setExteriorOpacity,
    update(quaternion: number[], cameraPosition?: number[]) {
      // Orthographic rays are parallel. Perspective rays depend on the panel's
      // position: looking down does not put the observer above the ceiling.
      towardCamera.set(0, 0, 1).applyQuaternion(rotation.fromArray(quaternion));
      if (cameraPosition) camera.fromArray(cameraPosition);
      for (const entry of entries) {
        let direction = towardCamera;
        const face = entry.group.front ?? entry.group.back;
        if (cameraPosition && face) {
          if (!face.geometry.boundingBox) face.geometry.computeBoundingBox();
          face.geometry.boundingBox!.getCenter(fromPanel);
          face.localToWorld(fromPanel);
          fromPanel.subVectors(camera, fromPanel).normalize();
          direction = fromPanel;
        }
        const facing = entry.directions.length ? Math.max(...entry.directions.map(([x, y, z]) => {
          panelNormal.set(x, y, z);
          // The rear hatch's outward face turns upward with its hinge.
          if (entry.directionFrame) panelNormal.transformDirection(entry.directionFrame.matrixWorld);
          return panelNormal.dot(direction);
        })) : 0;
        // Keep far-facing and edge-on panels solid; fade only as their side turns toward us.
        const t = Math.max(0, Math.min(1, facing / 0.35));
        const near = t * t * (3 - 2 * t);
        if (comparisonStyle(entry, near)) continue;
        skipPicking(entry, near > 0.5 || entry.maxOpacity === 0);
        for (const { material, edge } of entry.materials) {
          setOpacity(material, edge ? 0.5 - 0.48 * near : entry.maxOpacity * (1 - near * entry.fadeAmount), edge);
        }
      }
    },
  };
}
