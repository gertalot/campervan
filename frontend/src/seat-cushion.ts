import {
  Box3, BoxGeometry, IntType, Uint32BufferAttribute, Vector3,
  type BufferGeometry, type Mesh, type Object3D, type SkinnedMesh,
} from 'three';

/** Visual foam compression only; the underlying CAD cushion retains its manufactured dimensions. */
export function createSeatCushion(group: Object3D) {
  const cad = group as Object3D & { front: Mesh; edges?: Object3D & { geometry: BufferGeometry } };
  const mesh = cad.front;
  const geometry = mesh.geometry;
  const original = geometry.clone();
  original.computeBoundingBox();
  const localBounds = original.boundingBox!.clone();
  const size = localBounds.getSize(new Vector3());
  const centre = localBounds.getCenter(new Vector3());
  const dense = new BoxGeometry(
    size.x, size.y, size.z, Math.ceil(size.x / 25), Math.ceil(size.y / 25), 4,
  ).translate(centre.x, centre.y, centre.z);

  // Keep OCP's face picking/highlighting IDs when subdividing its six planar faces.
  const sourceIds = original.getAttribute('componentId');
  if (sourceIds) {
    const ids = new Uint32Array(dense.getAttribute('position').count);
    const sourceNormals = original.getAttribute('normal');
    const normals = dense.getAttribute('normal');
    const normal = new Vector3();
    for (let i = 0; i < ids.length; i++) {
      normal.fromBufferAttribute(normals, i);
      for (let j = 0; j < sourceIds.count; j++) {
        if (normal.x * sourceNormals.getX(j) + normal.y * sourceNormals.getY(j)
          + normal.z * sourceNormals.getZ(j) > 0.99) {
          ids[i] = sourceIds.getX(j);
          break;
        }
      }
    }
    const attribute = new Uint32BufferAttribute(ids, 1);
    attribute.gpuType = IntType;
    dense.setAttribute('componentId', attribute);
  }

  const edgeRange = cad.edges ? { ...cad.edges.geometry.drawRange } : null;
  let compressed = false;
  function restore() {
    if (!compressed) return;
    // Retain OCP's geometry object/ID and materials; release replaced GPU buffers.
    geometry.dispose();
    geometry.copy(original);
    if (cad.edges && edgeRange) cad.edges.geometry.setDrawRange(edgeRange.start, edgeRange.count);
    compressed = false;
  }
  function bounds() {
    mesh.updateWorldMatrix(true, false);
    return localBounds.clone().applyMatrix4(mesh.matrixWorld);
  }

  return {
    bounds,
    deform(human: Object3D | null) {
      if (!human?.visible) { restore(); return; }
      const seat = bounds();
      const height = seat.max.z - seat.min.z;
      const maximumDent = height * 0.55;
      const step = 25;
      const columns = Math.ceil((seat.max.x - seat.min.x) / step) + 1;
      const rows = Math.ceil((seat.max.y - seat.min.y) / step) + 1;
      const dents = new Float32Array(columns * rows);
      const point = new Vector3();
      let contact = false;
      human.updateWorldMatrix(true, true);
      human.traverse(object => {
        const skin = object as SkinnedMesh;
        if (!skin.isSkinnedMesh) return;
        const positions = skin.geometry.getAttribute('position');
        for (let i = 0; i < positions.count; i++) {
          skin.getVertexPosition(i, point).applyMatrix4(skin.matrixWorld);
          if (point.x < seat.min.x || point.x > seat.max.x || point.y < seat.min.y || point.y > seat.max.y
            || point.z >= seat.max.z || point.z < seat.max.z - maximumDent) continue;
          contact = true;
          const depth = seat.max.z - point.z + 2;
          const x = (point.x - seat.min.x) / step;
          const y = (point.y - seat.min.y) / step;
          // A small flat contact patch, then a soft falloff into the surrounding foam.
          for (let row = Math.max(0, Math.floor(y) - 3); row <= Math.min(rows - 1, Math.ceil(y) + 3); row++) {
            for (let column = Math.max(0, Math.floor(x) - 3);
              column <= Math.min(columns - 1, Math.ceil(x) + 3); column++) {
              const distance = Math.hypot(column - x, row - y) * step;
              const falloff = Math.max(0, Math.min(1, (75 - distance) / 40));
              const offset = row * columns + column;
              dents[offset] = Math.max(dents[offset]!, Math.min(maximumDent, depth * falloff));
            }
          }
        }
      });
      if (!contact) { restore(); return; }
      if (!compressed) {
        geometry.dispose();
        geometry.copy(dense);
        // Suppress the undeformed CAD wire outline without changing the user's visibility state.
        cad.edges?.geometry.setDrawRange(0, 0);
        compressed = true;
      }
      const positions = geometry.getAttribute('position');
      const rest = dense.getAttribute('position');
      const inverse = mesh.matrixWorld.clone().invert();
      for (let i = 0; i < positions.count; i++) {
        point.fromBufferAttribute(rest, i).applyMatrix4(mesh.matrixWorld);
        const x = Math.max(0, Math.min(columns - 1, (point.x - seat.min.x) / step));
        const y = Math.max(0, Math.min(rows - 1, (point.y - seat.min.y) / step));
        const left = Math.floor(x), right = Math.min(columns - 1, left + 1);
        const bottom = Math.floor(y), top = Math.min(rows - 1, bottom + 1);
        const blend = (a: number, b: number, t: number) => a + (b - a) * t;
        const depth = blend(
          blend(dents[bottom * columns + left]!, dents[bottom * columns + right]!, x - left),
          blend(dents[top * columns + left]!, dents[top * columns + right]!, x - left), y - bottom,
        );
        // Keep the bottom on its plywood/slats while the upper side walls follow the top.
        point.z -= depth * (point.z - seat.min.z) / height;
        point.applyMatrix4(inverse);
        positions.setXYZ(i, point.x, point.y, point.z);
      }
      positions.needsUpdate = true;
      geometry.computeVertexNormals();
      geometry.computeBoundingBox();
      geometry.computeBoundingSphere();
    },
    dispose() { restore(); original.dispose(); dense.dispose(); },
  };
}
