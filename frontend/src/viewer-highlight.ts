/** Shared surface tint and edge outline for selection and direct manipulation. */
import {
  DoubleSide, EdgesGeometry, LineBasicMaterial, LineSegments, Mesh, MeshBasicMaterial, type Object3D,
} from 'three';

export function highlightPiece(group: Object3D, colour: string, active = true) {
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
    const material = new MeshBasicMaterial({ color: colour, side: DoubleSide, transparent: true,
      opacity: active ? 0.42 : 0.13, depthTest: false, depthWrite: false, toneMapped: false });
    const surface = new Mesh(source.geometry, material);
    const edges = new EdgesGeometry(source.geometry, 35);
    const lineMaterial = new LineBasicMaterial({ color: colour, transparent: true,
      opacity: active ? 1 : 0.85, depthTest: false, depthWrite: false, toneMapped: false });
    const outline = new LineSegments(edges, lineMaterial);
    for (const object of [surface, outline]) {
      object.position.copy(source.position); object.quaternion.copy(source.quaternion); object.scale.copy(source.scale);
      object.userData.campervanOverlay = true; object.raycast = () => {};
      object.renderOrder = active ? 10003 : 10002; source.parent.add(object);
    }
    dispose.push(() => {
      surface.removeFromParent(); outline.removeFromParent(); material.dispose(); edges.dispose(); lineMaterial.dispose();
    });
  }
  return () => dispose.forEach(remove => remove());
}
