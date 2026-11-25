import type { ScanPaintPanel } from './scan-panels';
import { BufferGeometry, DoubleSide, Float32BufferAttribute, Mesh, MeshBasicMaterial, Path, Vector2 } from 'three';
import profile from '../../data/scan-reference/window-outlines.json';
import trimPanels from '../../data/scan-reference/trim-panel-outlines.json';
import { scanFaceDirections, type FadePanel } from './vehicle-fade';

/** CAD millimetres. Each corner gives its projected intersection and the tangent lengths on its two edges. */
function sampledOutline(corners: number[][], mirrorAt?: number) {
  const vertices = corners.map(([u, z]) => new Vector2(u, z));
  const path = new Path();
  // The hatch stores the two left corners. Trace from sill centre to header centre, then reflect.
  if (mirrorAt !== undefined) path.moveTo(mirrorAt, vertices[0].y);
  for (const [i, [, , incoming, outgoing]] of corners.entries()) {
    const vertex = vertices[i];
    function tangent(offset: number, distance: number) {
      const j = i + offset;
      const neighbour = mirrorAt !== undefined && (j < 0 || j >= vertices.length)
        ? new Vector2(mirrorAt, vertex.y) : vertices[(j + vertices.length) % vertices.length];
      return neighbour.clone().sub(vertex).setLength(distance).add(vertex);
    }
    const start = tangent(-1, incoming), end = tangent(1, outgoing);
    if (i === 0 && mirrorAt === undefined) path.moveTo(start.x, start.y);
    else path.lineTo(start.x, start.y);
    // Cubic approximation of a quarter ellipse, tangent to both straight edges.
    const handle = 4 * (Math.SQRT2 - 1) / 3;
    const c1 = start.clone().lerp(vertex, handle), c2 = end.clone().lerp(vertex, handle);
    path.bezierCurveTo(c1.x, c1.y, c2.x, c2.y, end.x, end.y);
  }
  if (mirrorAt === undefined) path.closePath();
  else path.lineTo(mirrorAt, vertices[vertices.length - 1].y);
  const points = path.getSpacedPoints(Math.ceil(path.getLength() / 5));
  return mirrorAt === undefined ? points.slice(0, -1)
    : points.concat(points.slice(1, -1).reverse().map(p => new Vector2(2 * mirrorAt - p.x, p.y)));
}

interface ScanOutline {
  name: string;
  direction: number;
  centre: number[];
  rim: number[][];
}

export interface ScanWindow extends ScanOutline {
  reveal: { jamb: number[][]; oppositeJamb?: number[][]; sill: number[][]; top: number[][] };
}

interface OutlineProfile {
  name: string;
  wall: string;
  corners: number[][];
  depth: number[];
}

function mirrorAcrossVan([x, y, z]: number[]) {
  return [2 * profile.centreXmm - x, y, z];
}

/** Project a rounded profile onto the scan. Side pairs share one profile and the same CAD centreline. */
function scanOutlines({ name, wall, corners, depth }: OutlineProfile, inwardOffset = 0): ScanOutline[] {
  const [offset, u0, z0, across, rise, bow, verticalBow = 0] = depth;
  function surfacePoint(u: number, z: number) {
    const du = (u - u0) / 100, dz = (z - z0) / 100;
    const d = offset + inwardOffset + across * du + rise * dz + bow * du * du + verticalBow * dz * dz;
    return wall === 'rear' ? [u, d, z] : [d, u, z];
  }
  const rim = sampledOutline(corners, wall === 'rear' ? profile.centreXmm : undefined);
  const centre = rim.reduce((sum, point) => sum.add(point), new Vector2()).divideScalar(rim.length);
  const middle = surfacePoint(centre.x, centre.y);
  const edge = rim.map(p => surfacePoint(p.x, p.y));
  if (wall === 'rear') return [{ name, direction: 2, centre: middle, rim: edge }];
  return [
    { name: 'Left ' + name, direction: 0, centre: middle, rim: edge },
    { name: 'Right ' + name, direction: 1, centre: mirrorAcrossVan(middle), rim: edge.map(mirrorAcrossVan) },
  ];
}

export function scanWindows(referenceKey: string): ScanWindow[] {
  if (referenceKey !== profile.referenceKey) return [];
  return profile.windows.flatMap(window => scanOutlines(window).map(outline => ({ ...outline, reveal: window.reveal })));
}

export function scanTrimPanels(referenceKey: string): ScanPaintPanel[] {
  if (referenceKey !== profile.referenceKey) return [];
  return trimPanels.flatMap(panel => scanOutlines(panel, panel.surfaceOffsetMm)).map(profile => {
    const { name, direction } = profile;
    const directions = [scanFaceDirections[direction]];
    const geometry = panelGeometry(profile);
    geometry.computeVertexNormals();
    const face = new Mesh(geometry, new MeshBasicMaterial({ side: DoubleSide, colorWrite: false, depthWrite: false }));
    face.material.forceSinglePass = true;
    face.name = name;
    face.renderOrder = 1;
    face.raycast = () => {}; // Only the paint bucket picks this surface.
    return { target: 'Scan trim/' + name, face, directions, finishOpacity: 1 };
  });
}

function panelGeometry({ centre, rim }: ScanOutline) {
  const vertices = [centre, ...rim];
  const triangles: number[] = [];
  for (let i = 1; i < vertices.length; i++) {
    const next = i === vertices.length - 1 ? 1 : i + 1;
    triangles.push(0, i, next);
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(vertices.flat(), 3));
  geometry.setIndex(triangles);
  return geometry;
}

export function scanWindowPane(window: ScanWindow): FadePanel {
  const glass = new MeshBasicMaterial({ color: '#739ead', opacity: 0.2, transparent: true,
    side: DoubleSide, depthWrite: false });
  glass.forceSinglePass = true;
  const pane = new Mesh(panelGeometry(window), glass);
  pane.name = window.name + ' pane';
  pane.userData.campervanOverlay = true;
  pane.raycast = () => {};
  return { face: pane, directions: [scanFaceDirections[window.direction]], overlayOpacity: glass.opacity };
}
