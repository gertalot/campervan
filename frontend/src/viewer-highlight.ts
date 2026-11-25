/** Shared surface tint and edge outline for selection and direct manipulation. */
import {
  DoubleSide, EdgesGeometry, LineBasicMaterial, LineSegments, Mesh, MeshBasicMaterial, type Object3D,
} from 'three';
import { screenLine } from './screen-line';

export function highlightPiece(group: Object3D, colour: string, mode: 'selection' | 'paint' = 'selection') {
  const paint = mode === 'paint';
  const fronts = new Set<Mesh>(), fallback = new Set<Mesh>();
  group.traverse(object => {
    if (object.userData.campervanOverlay) return;
    const front = (object as Object3D & { front?: Mesh }).front;
    if (front && !front.userData.campervanOverlay) fronts.add(front);
    if (object instanceof Mesh) fallback.add(object);
  });
  const dispose: (() => void)[] = [];
  for (const source of fronts.size ? fronts : fallback) {
    if (!source.parent || source.userData.campervanOverlay) continue;
    if (paint && (!source.visible || !(Array.isArray(source.material)
      ? source.material.some(material => material.visible) : source.material.visible))) continue;
    const material = new MeshBasicMaterial({ color: colour, side: DoubleSide, transparent: true,
      opacity: paint ? 0.12 : 0.42, depthTest: paint, depthWrite: false, toneMapped: false,
      polygonOffset: paint, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
    const surface = new Mesh(source.geometry, material);
    surface.renderOrder = paint ? 10001 : 10003;
    const edges = new EdgesGeometry(source.geometry, 35);
    const outline = paint
      ? screenLine(edges.getAttribute('position').array as Float32Array, colour, 1.5, 0.55, 10002)
      : new LineSegments(edges, new LineBasicMaterial({ color: colour, transparent: true,
        depthTest: false, depthWrite: false, toneMapped: false }));
    if (paint) {
      // Screen-space ribbons keep their winding when the van layout is mirrored.
      outline.material.side = DoubleSide;
      outline.material.forceSinglePass = true;
      outline.material.toneMapped = false;
      edges.dispose();
    } else outline.renderOrder = surface.renderOrder;
    for (const object of [surface, outline]) {
      object.position.copy(source.position); object.quaternion.copy(source.quaternion); object.scale.copy(source.scale);
      object.userData.campervanOverlay = true; object.raycast = () => {};
      source.parent.add(object);
    }
    dispose.push(() => {
      surface.removeFromParent(); outline.removeFromParent();
      material.dispose(); outline.geometry.dispose(); outline.material.dispose();
    });
  }
  return () => dispose.forEach(remove => remove());
}
