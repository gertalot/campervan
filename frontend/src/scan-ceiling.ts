import { BufferGeometry, Color, DoubleSide, Float32BufferAttribute, MathUtils, Mesh, MeshStandardMaterial } from 'three';
import ceiling from '../../data/scan-reference/ceiling-outline.json';
import { scanFaceDirections } from './vehicle-fade';
import type { ScanPaintPanel } from './scan-panels';

// Median sRGB colour of the timber in the registered scan.
export const ceilingColour = new Color('#aa9457');

export function scanCeiling(referenceKey: string) {
  if (referenceKey !== ceiling.referenceKey) return;
  const half = ceiling.halfPerimeterMm;
  const centreX = half[0][0];
  const centreY = (half[0][1] + half[half.length - 1][1]) / 2;
  const rim = half.concat(half.slice(1, -1).reverse().map(([x, y, z]) => [2 * centreX - x, y, z]));

  // Each station gives Y, the centre height, and the drop 600 mm either side of the centre.
  const stations = ceiling.crownStationsMm;
  function height(x: number, y: number) {
    const end = stations.findIndex(station => station[0] >= y);
    const b = stations[end < 0 ? stations.length - 1 : end];
    const a = end > 0 ? stations[end - 1] : b;
    const t = b === a ? 0 : (y - a[0]) / (b[0] - a[0]);
    return MathUtils.lerp(a[1], b[1], t) - MathUtils.lerp(a[2], b[2], t) * ((x - centreX) / 600) ** 2;
  }

  const positions = [centreX, centreY, height(centreX, centreY)];
  const triangles: number[] = [];
  // Closely spaced rings resolve the shallow arch all the way out to the reviewed perimeter.
  const rings = Math.ceil(Math.max(...rim.map(([x, y]) => Math.hypot(x - centreX, y - centreY))) / 40);
  for (let ring = 1; ring <= rings; ring++) {
    const start = positions.length / 3;
    for (const [i, [edgeX, edgeY, edgeZ]] of rim.entries()) {
      const t = ring / rings;
      const x = MathUtils.lerp(centreX, edgeX, t), y = MathUtils.lerp(centreY, edgeY, t);
      positions.push(x, y, ring === rings ? edgeZ : height(x, y));
      const a = start + i, b = start + (i + 1) % rim.length;
      if (ring === 1) triangles.push(0, a, b);
      // Mirror the diagonals as well as the vertices across the centreline.
      else if (i < half.length - 1) triangles.push(a - rim.length, a, b, a - rim.length, b, b - rim.length);
      else triangles.push(a - rim.length, a, b - rim.length, a, b, b - rim.length);
    }
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  geometry.setIndex(triangles);
  geometry.computeVertexNormals();
  const material = new MeshStandardMaterial({ color: ceilingColour, roughness: 0.9, side: DoubleSide });
  material.forceSinglePass = true;
  const face = new Mesh(geometry, material);
  face.name = 'Timber ceiling';
  face.raycast = () => {};
  const directions = [scanFaceDirections[5]];
  const panel: ScanPaintPanel = { face, directions, target: 'Scan ceiling/Timber ceiling' };
  return { panel, rim };
}
