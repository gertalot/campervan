import { Box3, BufferGeometry, DoubleSide, Group, Line, Mesh, Points, Sphere, Vector3,
  type Intersection, type Material, type MeshBasicMaterial, type MeshStandardMaterial, type Object3D, type Raycaster } from 'three';
import { scanFaceDirections, type FadePanel } from './vehicle-fade';
import { scanTrimPanels, scanWindowPane, scanWindows } from './scan-outlines';
import type { PiecePoint } from './viewer-pieces';
import { repairScanMesh } from './scan-mesh-repair';
import { scanCeiling } from './scan-ceiling';

export interface ScanPaintPanel extends FadePanel {
  target: string;
  face: Mesh<BufferGeometry, MeshBasicMaterial | MeshStandardMaterial>;
}

export interface ScanDisplay {
  root: Group;
  panels: FadePanel[];
  paintPanels: ScanPaintPanel[];
  pickPaint(ray: Raycaster, cad: PiecePoint | null, vehicleOpacity: number, sample?: boolean): PiecePoint | null;
}

/** A translucent comparison body allows paint hits on surfaces behind it. */
export function paintHitDistance(ray: Raycaster, hit: PiecePoint | null, vehicleOpacity: number) {
  if (!hit || (vehicleOpacity < 0.5 && hit.path.startsWith('/Campervan/Vehicle references/'))) return Infinity;
  return ray.ray.origin.distanceTo(hit.point);
}

/** Give the registered scan display panels. Keep the source mesh for section measurements. */
export function createScanPanels(source: Object3D, referenceKey: string) {
  const root = new Group();
  root.name = source.name;
  const panels: FadePanel[] = [];
  const bounds = new Box3().setFromObject(source, true);
  const windows = scanWindows(referenceKey);
  const ceiling = source instanceof Mesh ? scanCeiling(referenceKey) : undefined;
  const repaired = source instanceof Mesh && (windows.length > 0 || ceiling)
    ? repairScanMesh(source, windows, ceiling?.rim) : undefined;
  const a = new Vector3(), b = new Vector3(), c = new Vector3(), centre = new Vector3();
  const low = new Vector3(), high = new Vector3(), nearest = new Vector3();
  const axes = ['x', 'y', 'z'] as const;

  function region(point: Vector3) {
    low.subVectors(point, bounds.min);
    high.subVectors(bounds.max, point);
    nearest.copy(low).min(high);
    let mask = 0;
    for (let axis = 0; axis < axes.length; axis++) {
      // The wall band narrows at each junction with an adjoining surface.
      const depth = Math.min(300, 180 + Math.min(nearest[axes[(axis + 1) % 3]], nearest[axes[(axis + 2) % 3]]));
      if (low[axes[axis]] < depth) mask |= 1 << (axis * 2);
      if (high[axes[axis]] < depth) mask |= 1 << (axis * 2 + 1);
    }
    return mask;
  }

  function add(face: FadePanel['face'], original: Object3D, mask: number) {
    face.matrix.copy(original.matrixWorld);
    face.matrixAutoUpdate = false;
    face.userData.campervanOverlay = true;
    face.raycast = () => {};
    root.add(face);
    panels.push({ face, directions: scanFaceDirections.filter((_, i) => mask & (1 << i)) });
  }

  source.traverse(object => {
    if (object instanceof Points || object instanceof Line) {
      add(object.clone(false), object, 0);
      return;
    }
    if (!(object instanceof Mesh)) return;
    const geometry: BufferGeometry = object === source && repaired ? repaired : object.geometry;
    const position = geometry.getAttribute('position'), index = geometry.getIndex();
    const materials: Material[] = Array.isArray(object.material) ? object.material : [object.material];
    const groups = Array.isArray(object.material) ? geometry.groups
      : [{ start: 0, count: index?.count ?? position.count, materialIndex: 0 }];
    for (const group of groups) {
      const regions = new Map<number, { indices: number[]; bounds: Box3 }>();
      for (let i = group.start; i < group.start + group.count; i += 3) {
        const ia = index ? index.getX(i) : i;
        const ib = index ? index.getX(i + 1) : i + 1;
        const ic = index ? index.getX(i + 2) : i + 2;
        a.fromBufferAttribute(position, ia);
        b.fromBufferAttribute(position, ib);
        c.fromBufferAttribute(position, ic);
        centre.copy(a).add(b).add(c).multiplyScalar(1 / 3).applyMatrix4(object.matrixWorld);
        const mask = region(centre);
        let part = regions.get(mask);
        if (!part) { part = { indices: [], bounds: new Box3() }; regions.set(mask, part); }
        part.indices.push(ia, ib, ic);
        part.bounds.expandByPoint(a).expandByPoint(b).expandByPoint(c);
      }
      for (const [mask, part] of regions) {
        const panel = new BufferGeometry();
        for (const [name, attribute] of Object.entries(geometry.attributes)) panel.setAttribute(name, attribute);
        panel.setIndex(part.indices);
        panel.boundingBox = part.bounds;
        panel.boundingSphere = part.bounds.getBoundingSphere(new Sphere());
        const material = materials[group.materialIndex ?? 0].clone();
        material.side = DoubleSide;
        material.forceSinglePass = true;
        add(new Mesh(panel, material), object, mask);
      }
    }
  });
  if (ceiling) {
    root.add(ceiling.panel.face);
    panels.push(ceiling.panel);
  }
  const scanFaces = panels.slice();
  const trim = scanTrimPanels(referenceKey);
  const panes = windows.map(scanWindowPane);
  for (const panel of [...panes, ...trim]) {
    root.add(panel.face);
    panels.push(panel);
  }
  const paintPanels = ceiling ? [...trim, ceiling.panel] : trim;
  const sampleFaces = [...scanFaces, ...panes];
  root.updateMatrixWorld(true);
  const worldBox = new Box3(), entry = new Vector3();
  const hits: Intersection[] = [];
  return {
    root, panels, paintPanels,
    pickPaint(ray: Raycaster, cad: PiecePoint | null, vehicleOpacity: number, sample = false) {
      if (!root.visible) return cad;
      let nearest = cad;
      let pickedFace: Mesh | undefined;
      let distance = paintHitDistance(ray, cad, vehicleOpacity);
      for (const panel of paintPanels) {
        if (!panel.face.visible || !panel.pickable || (sample && !panel.face.material.colorWrite)) continue;
        hits.length = 0;
        Mesh.prototype.raycast.call(panel.face, ray, hits);
        for (const hit of hits) {
          if (hit.distance < distance) {
            nearest = { path: panel.target, point: hit.point, hit };
            distance = hit.distance;
            pickedFace = panel.face;
          }
        }
      }
      if (!nearest && !sample) return null;
      const far = ray.far;
      ray.far = Math.min(far, sample ? distance : ray.ray.origin.distanceTo(nearest!.point));
      try {
        for (const panel of sample ? sampleFaces : scanFaces) {
          const { face } = panel;
          if (sample && !panel.pickable) continue;
          if (face === pickedFace) continue;
          const materials = Array.isArray(face.material) ? face.material : [face.material];
          // Translucent scan surfaces let the paint pointer reach parts behind them.
          if (!face.visible || !materials.some(material => material.visible && (sample ? material.opacity > 0 : material.opacity >= 0.5))) continue;
          // Partition bounds let us skip batches of scan triangles behind the candidate.
          // Screen-space lines and points need their native expanded bounds to match their drawn width.
          if (face instanceof Mesh && !('isLineSegments2' in face) && face.geometry.boundingBox) {
            worldBox.copy(face.geometry.boundingBox).applyMatrix4(face.matrixWorld);
            const start = ray.ray.origin;
            if (!worldBox.containsPoint(start) && (!ray.ray.intersectBox(worldBox, entry)
              || start.distanceToSquared(entry) > ray.far ** 2)) continue;
          }
          hits.length = 0;
          // Scan display objects disable picking. Only this occlusion query uses the native intersection method.
          const prototype: Object3D = Object.getPrototypeOf(face);
          prototype.raycast.call(face, ray, hits);
          for (const hit of hits) {
            if (hit.distance > ray.far) continue;
            if (!sample) return null;
            nearest = { path: face.name, point: hit.point, hit };
            ray.far = hit.distance;
          }
        }
        return nearest;
      } finally {
        ray.far = far;
      }
    },
    dispose() {
      repaired?.dispose();
      for (const { face } of panels) {
        if (face instanceof Mesh) {
          face.geometry.dispose();
          for (const material of Array.isArray(face.material) ? face.material : [face.material]) material.dispose();
        }
      }
    },
  };
}
