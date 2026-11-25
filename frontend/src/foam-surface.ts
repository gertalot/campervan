import {
  BoxGeometry, IntType, Uint32BufferAttribute, Vector3,
  type BufferGeometry, type Color, type Mesh, type MeshStandardMaterial, type Object3D, type Texture,
} from 'three';

/** Rounded display mesh; each draw deforms its cached rest shape once. */
export function createFoamSkin(group: Object3D, velvet: Texture) {
  const cad = group as Object3D & { front: Mesh<BufferGeometry, MeshStandardMaterial>; originalColor: Color;
    edges?: Object3D & { geometry: BufferGeometry } };
  const mesh = cad.front;
  const material = mesh.material;
  const originalMap = material.map, originalColor = cad.originalColor.clone();
  const originalRoughness = material.roughness, originalMetalness = material.metalness;
  material.map = velvet;
  material.color.set(0xffffff);
  cad.originalColor.copy(material.color); // OCP restores this colour after selection.
  material.metalness = 0;
  material.roughness = 0.85;
  material.needsUpdate = true;
  const geometry = mesh.geometry;
  const original = geometry.clone();
  original.computeBoundingBox();
  const localBounds = original.boundingBox!.clone();
  const size = localBounds.getSize(new Vector3());
  const centre = localBounds.getCenter(new Vector3());
  const radius = Math.min(5, size.x / 4, size.y / 4, size.z / 4);
  const skin = new BoxGeometry(size.x, size.y, size.z,
    Math.ceil(size.x / 25), Math.ceil(size.y / 25), Math.ceil(size.z / 10))
    .translate(centre.x, centre.y, centre.z);
  const positions = skin.getAttribute('position');
  const faceNormals = skin.getAttribute('normal');
  const uv = skin.getAttribute('uv');
  const sourceIds = original.getAttribute('componentId');
  const sourceNormals = original.getAttribute('normal');
  const componentIds = sourceIds ? new Uint32Array(positions.count) : null;
  const seamIndices = new Uint32Array(positions.count);
  const seams = new Map<string, number>();
  const point = new Vector3(), inner = new Vector3();
  const innerMin = localBounds.min.clone().addScalar(radius);
  const innerMax = localBounds.max.clone().addScalar(-radius);

  for (let i = 0; i < positions.count; i++) {
    // Measure each sewn face in millimetres so any fabric follows the foam through deformation.
    const uLength = faceNormals.getX(i) ? size.z : size.x;
    const vLength = faceNormals.getY(i) ? size.z : size.y;
    uv.setXY(i, uv.getX(i) * uLength, uv.getY(i) * vLength);
    // Assign the original CAD face before rounding changes its normal.
    if (componentIds && sourceNormals) {
      for (let j = 0; j < sourceIds.count; j++) {
        if (faceNormals.getX(i) * sourceNormals.getX(j)
          + faceNormals.getY(i) * sourceNormals.getY(j)
          + faceNormals.getZ(i) * sourceNormals.getZ(j) > 0.99) {
          componentIds[i] = sourceIds.getX(j);
          break;
        }
      }
    }
    point.fromBufferAttribute(positions, i);
    inner.copy(point).clamp(innerMin, innerMax);
    point.sub(inner).normalize().multiplyScalar(radius).add(inner);
    positions.setXYZ(i, point.x, point.y, point.z);
    const key = `${point.x.toFixed(5)},${point.y.toFixed(5)},${point.z.toFixed(5)}`;
    let seam = seams.get(key);
    if (seam === undefined) { seam = seams.size; seams.set(key, seam); }
    seamIndices[i] = seam;
  }
  if (componentIds) {
    const attribute = new Uint32BufferAttribute(componentIds, 1);
    attribute.gpuType = IntType;
    skin.setAttribute('componentId', attribute);
  }
  const normalSums = new Float64Array(seams.size * 3);
  const edgeRange = cad.edges ? { ...cad.edges.geometry.drawRange } : null;
  let displayed = false;

  function bounds() {
    mesh.updateWorldMatrix(true, false);
    return localBounds.clone().applyMatrix4(mesh.matrixWorld);
  }

  function draw(deform: (point: Vector3) => void) {
    if (!displayed) {
      // Keep the geometry object and its OCP IDs/material ownership intact.
      geometry.dispose();
      geometry.copy(skin);
      cad.edges?.geometry.setDrawRange(0, 0);
      displayed = true;
    }
    const output = geometry.getAttribute('position');
    for (let i = 0; i < output.count; i++) {
      point.fromBufferAttribute(positions, i);
      deform(point);
      output.setXYZ(i, point.x, point.y, point.z);
    }
    output.needsUpdate = true;
    geometry.computeVertexNormals();
    const normals = geometry.getAttribute('normal');
    normalSums.fill(0);
    for (let i = 0; i < normals.count; i++) {
      const seam = seamIndices[i]! * 3;
      normalSums[seam] += normals.getX(i);
      normalSums[seam + 1] += normals.getY(i);
      normalSums[seam + 2] += normals.getZ(i);
    }
    for (let i = 0; i < normals.count; i++) {
      const seam = seamIndices[i]! * 3;
      point.set(normalSums[seam]!, normalSums[seam + 1]!, normalSums[seam + 2]!).normalize();
      normals.setXYZ(i, point.x, point.y, point.z);
    }
    normals.needsUpdate = true;
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();
  }

  return {
    mesh, localBounds, bounds, draw,
    dispose() {
      material.map = originalMap;
      material.color.copy(originalColor);
      cad.originalColor.copy(originalColor);
      material.roughness = originalRoughness;
      material.metalness = originalMetalness;
      material.needsUpdate = true;
      if (displayed) {
        geometry.dispose();
        geometry.copy(original);
        if (cad.edges && edgeRange) cad.edges.geometry.setDrawRange(edgeRange.start, edgeRange.count);
      }
      original.dispose();
      skin.dispose();
    },
  };
}
