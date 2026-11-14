/** Exact scan cuts and independently authored, explicitly recorded vehicle sections. */
import { Group, Matrix4, Mesh, Vector3, type Object3D } from 'three';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { disposeObject, layerUrl, loadObject } from './scan-assets';
import type { ScanResult } from './scan-library-api';
import { ScanSectionIndex, type SectionMesh } from './scan-section-geometry';
import { type AuthoredSection, type OutlineSegment, type SectionPlane, type SectionPoint } from './cross-section-api';
import { createSectionControls, sectionStations } from './cross-section-controls';

export interface CrossSectionViewer { setCrossSections(root: Object3D): void }

function pathPoints(start: SectionPoint, segments: OutlineSegment[]): SectionPoint[] {
  const points: SectionPoint[] = [start];
  function cubic(a: SectionPoint, b: SectionPoint, c: SectionPoint, d: SectionPoint, depth = 0) {
    const dx = d[0] - a[0], dz = d[1] - a[1], length2 = dx * dx + dz * dz;
    const distance = (p: SectionPoint) => {
      const t = length2 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / length2)) : 0;
      return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz);
    };
    if (depth === 12 || Math.max(distance(b), distance(c)) <= 0.25) { points.push(d); return; }
    const mid = (p: SectionPoint, q: SectionPoint): SectionPoint => [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
    const ab = mid(a, b), bc = mid(b, c), cd = mid(c, d), abc = mid(ab, bc), bcd = mid(bc, cd);
    const centre = mid(abc, bcd);
    cubic(a, ab, abc, centre, depth + 1); cubic(centre, bcd, cd, d, depth + 1);
  }
  for (const segment of segments) {
    if (segment.kind === 'cubic') cubic(points[points.length - 1], segment.control1!, segment.control2!, segment.end);
    else points.push(segment.end);
  }
  return points;
}

function outlinePositions(section: AuthoredSection, station: number): Float32Array {
  const positions: number[] = [];
  if (section.plane === 'YZ') {
    const opposite = Math.abs(station - section.x_mm!) > 0.001;
    const points = pathPoints(opposite ? section.opposite_start ?? section.start! : section.start!,
      opposite ? section.opposite_segments ?? section.segments : section.segments);
    for (let i = 1; i < points.length; i++) {
      for (const [y, z] of [points[i - 1], points[i]]) positions.push(station, y, z);
    }
  } else {
    for (const sign of [-1, 1]) {
      const points = pathPoints([0, section.floor_z_mm!],
        sign > 0 ? section.opposite_segments ?? section.segments : section.segments);
      for (let i = 1; i < points.length; i++) {
        for (const point of [points[i - 1], points[i]]) {
          positions.push(section.centre_x_mm + sign * point[0], section.y_mm!, point[1]);
        }
      }
    }
  }
  return new Float32Array(positions);
}

function line(positions: Float32Array, color: string, width: number, opacity: number, order: number) {
  const geometry = new LineSegmentsGeometry().setPositions(positions);
  const material = new LineMaterial({ color, linewidth: width, opacity, transparent: true,
    depthTest: false, depthWrite: false });
  const result = new LineSegments2(geometry, material);
  result.renderOrder = order;
  result.userData.campervanOverlay = true;
  result.raycast = () => {};
  return result;
}

function clear(group: Group) {
  for (const child of [...group.children]) { child.removeFromParent(); disposeObject(child); }
}

function indexedMeshes(source: Object3D, registration: Matrix4): SectionMesh[] {
  source.updateMatrixWorld(true);
  const meshes: SectionMesh[] = [], point = new Vector3();
  source.traverse(object => {
    if (!(object instanceof Mesh)) return;
    const attribute = object.geometry.getAttribute('position');
    if (!attribute) return;
    const transform = registration.clone().multiply(object.matrixWorld);
    const positions = new Float32Array(attribute.count * 3);
    for (let i = 0; i < attribute.count; i++) {
      point.fromBufferAttribute(attribute, i).applyMatrix4(transform);
      positions.set([point.x, point.y, point.z], i * 3);
    }
    const index = object.geometry.getIndex();
    const indices = index ? Uint32Array.from(index.array) : Uint32Array.from({ length: attribute.count }, (_, i) => i);
    meshes.push({ positions, indices });
  });
  return meshes;
}

export function setupCrossSections(container: HTMLElement, viewer: CrossSectionViewer) {
  const overlay = new Group();
  overlay.name = 'Cross sections'; overlay.userData.campervanOverlay = true;
  const layers = {
    XZ: { raw: new Group(), blue: new Group(), index: undefined as ScanSectionIndex | undefined },
    YZ: { raw: new Group(), blue: new Group(), index: undefined as ScanSectionIndex | undefined },
  };
  for (const layer of Object.values(layers)) overlay.add(layer.blue, layer.raw);
  viewer.setCrossSections(overlay);
  let frame = 0;
  const pending = new Set<SectionPlane>();
  function schedule(panel: { plane: SectionPlane }) {
    pending.add(panel.plane);
    if (!frame) frame = requestAnimationFrame(draw);
  }
  const controls = createSectionControls(container, schedule);
  function draw() {
    frame = 0;
    for (const panel of controls.panels) {
      if (!pending.has(panel.plane)) continue;
      const layer = layers[panel.plane];
      clear(layer.raw); clear(layer.blue);
      if (layer.index) {
        const segments = layer.index.section(panel.coordinate);
        if (segments.length) {
          const contour = line(segments, '#36ed76', 1.5, panel.rawOpacity, 9002);
          contour.visible = panel.rawOpacity > 0; layer.raw.add(contour);
        }
        controls.status(panel.plane, (segments.length / 6) + ' raw scan segments at '
          + (panel.plane === 'XZ' ? 'Y' : 'X') + ' = ' + panel.coordinate + ' mm. Gaps remain open.');
      }
      for (const section of controls.sections()) {
        if (section.plane !== panel.plane) continue;
        for (const station of sectionStations(section)) {
          const selected = section.id === panel.activeId && Math.abs(station - panel.coordinate) < 0.5;
          const outline = line(outlinePositions(section, station), '#368cff', selected ? 3 : 1.25,
            panel.blueOpacity * (selected ? 1 : 0.14), selected ? 9001 : 9000);
          outline.name = 'Blue section ' + section.id + ' at ' + station;
          outline.visible = panel.blueOpacity > 0; layer.blue.add(outline);
        }
      }
    }
    pending.clear(); viewer.setCrossSections(overlay);
  }
  let source: Object3D | undefined, sourceOwned = false, sourceKey = '', generation = 0;
  import.meta.hot?.dispose(() => {
    cancelAnimationFrame(frame); generation++;
    for (const layer of Object.values(layers)) { clear(layer.raw); clear(layer.blue); }
    overlay.removeFromParent();
    if (sourceOwned && source) disposeObject(source);
  });
  return {
    async setReference(scan: ScanResult | undefined, reference: Object3D | undefined) {
      const token = ++generation;
      for (const plane of ['XZ', 'YZ'] as const) {
        layers[plane].index = undefined; clear(layers[plane].raw); controls.setBounds(plane, undefined);
      }
      viewer.setCrossSections(overlay);
      if (!scan || !reference) {
        for (const plane of ['XZ', 'YZ'] as const) controls.status(plane, 'Choose a registered scan to inspect its sections.');
        return;
      }
      const registration = reference.matrix.clone();
      const full = scan.layers?.find(layer => layer.id === 'mesh-full');
      const nextKey = scan.key + ':' + (full?.asset ?? 'display');
      for (const plane of ['XZ', 'YZ'] as const) controls.status(plane, full
        ? 'Loading full-resolution scan for sections…' : 'Preparing displayed scan for sections…');
      try {
        if (!full || sourceKey !== nextKey || !source) {
          if (sourceOwned && source) disposeObject(source);
          source = undefined; sourceKey = '';
          const loaded = full ? await loadObject(layerUrl(scan, full), full.kind) : reference;
          if (token !== generation) { if (full) disposeObject(loaded); return; }
          source = loaded; sourceOwned = !!full; sourceKey = nextKey;
        }
        await new Promise<void>(resolve => requestAnimationFrame(() => resolve()));
        if (token !== generation) return;
        const meshes = indexedMeshes(source, sourceOwned ? registration : new Matrix4());
        // The two axis indexes retain the same transformed vertex/index buffers.
        layers.XZ.index = new ScanSectionIndex(meshes, 1);
        layers.YZ.index = new ScanSectionIndex(meshes, 0);
        for (const plane of ['XZ', 'YZ'] as const) {
          const index = layers[plane].index!;
          controls.setBounds(plane, [index.min, index.max]);
        }
      } catch (error) {
        if (token === generation) {
          for (const plane of ['XZ', 'YZ'] as const) {
            layers[plane].index = undefined;
            controls.status(plane, 'Could not section the scan: ' + String(error));
          }
        }
      }
    },
  };
}
