import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';

export function screenLine(positions: Float32Array, color: string, width: number, opacity: number, order: number,
  depthTest = false) {
  const geometry = new LineSegmentsGeometry().setPositions(positions);
  const material = new LineMaterial({ color, linewidth: width, opacity, transparent: true,
    depthTest, depthWrite: false });
  const result = new LineSegments2(geometry, material);
  result.renderOrder = order;
  result.userData.campervanOverlay = true;
  result.raycast = () => {};
  return result;
}
