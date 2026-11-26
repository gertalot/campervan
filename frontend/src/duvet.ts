import {
  BufferGeometry, Float32BufferAttribute, MathUtils, Mesh, MeshStandardMaterial, type Box3, type Object3D,
} from 'three';
import { forEachSkinVertex } from './mannequin';

// Two cloth faces meet at the sewn hem. Both use the same drape.
const columns = 81, rows = 109, faceSize = columns * rows;
const bell = (distance: number) => Math.exp(-distance * distance);

export function createDuvet(cabinet: Box3) {
  const geometry = new BufferGeometry();
  const positions = new Float32BufferAttribute(new Float32Array(faceSize * 2 * 3), 3);
  geometry.setAttribute('position', positions);
  const colors = new Float32BufferAttribute(new Float32Array(faceSize * 2 * 3), 3);
  geometry.setAttribute('color', colors);
  const uv = new Float32BufferAttribute(new Float32Array(faceSize * 2 * 2), 2);
  geometry.setAttribute('uv', uv);
  const indices: number[] = [];
  function quad(a: number, b: number, c: number, d: number) { indices.push(a, b, c, a, c, d); }
  for (let row = 0; row < rows - 1; row++) {
    for (let col = 0; col < columns - 1; col++) {
      const a = row * columns + col, b = a + 1, d = a + columns, c = d + 1;
      quad(a, b, c, d);
      quad(a + faceSize, d + faceSize, c + faceSize, b + faceSize);
      if (col === 0) quad(a, d, d + faceSize, a + faceSize);
      if (col === columns - 2) quad(c, b, b + faceSize, c + faceSize);
      if (row === 0) quad(b, a, a + faceSize, b + faceSize);
      if (row === rows - 2) quad(d, c, c + faceSize, d + faceSize);
    }
  }
  geometry.setIndex(indices);
  const material = new MeshStandardMaterial({ color: 0xcac1b2, roughness: 1, vertexColors: true });
  const mesh = new Mesh(geometry, material);
  mesh.name = 'Duvet';
  mesh.visible = false;

  function fit(mattress: Box3, pillowEdge: number, sleepers: Object3D[]) {
    const left = mattress.min.x + 9, foot = mattress.min.y + 8;
    const width = mattress.max.x - left, length = pillowEdge - 22 - foot;
    if (width <= 0 || length <= 0) return false;
    const dy = length / (rows - 1);
    // Pull the hem inside the mattress beside the cabinet. Only the free section hangs down.
    function aisleAt(y: number) {
      const away = Math.max(y - cabinet.max.y, cabinet.min.y - y, 0);
      return MathUtils.smoothstep(away, 0, 120);
    }
    const right = (free: number) => mattress.max.x - 24 + 49 * free;
    const support = new Float32Array(faceSize).fill(-64);
    for (const sleeper of sleepers) {
      forEachSkinVertex(sleeper, point => {
        const height = point.z - mattress.max.z;
        if (height <= 0) return;
        const x = (point.x - left) / (right(aisleAt(point.y)) - left) * (columns - 1);
        const y = (point.y - foot) / dy;
        // Support the entire cell containing the skin vertex, including its upper face.
        for (let row = Math.max(0, Math.floor(y)); row <= Math.min(rows - 1, Math.ceil(y)); row++) {
          for (let col = Math.max(0, Math.floor(x)); col <= Math.min(columns - 1, Math.ceil(x)); col++) {
            const i = row * columns + col;
            support[i] = Math.max(support[i], height + 8);
          }
        }
      });
    }
    if (sleepers.length) {
      // Limit the slope away from each contact. Cloth bridges small gaps between limbs.
      const across = width / (columns - 1) * 0.82, along = dy * 0.82;
      const diagonal = Math.hypot(across, along);
      for (const step of [1, -1]) {
        for (let k = 0; k < faceSize; k++) {
          const i = step === 1 ? k : faceSize - 1 - k;
          const col = i % columns, prevRow = i - step * columns;
          const hasPrev = step === 1 ? col > 0 : col < columns - 1;
          if (hasPrev) support[i] = Math.max(support[i], support[i - step] - across);
          if (prevRow < 0 || prevRow >= faceSize) continue;
          support[i] = Math.max(support[i], support[prevRow] - along);
          if (col > 0) support[i] = Math.max(support[i], support[prevRow - 1] - diagonal);
          if (col + 1 < columns) support[i] = Math.max(support[i], support[prevRow + 1] - diagonal);
        }
      }
      // Soften ridges between samples, retaining the minimum clearance over the skin.
      const raised = support.slice();
      for (let i = columns + 1; i < faceSize - columns - 1; i++) {
        if (i % columns === 0 || i % columns === columns - 1) continue;
        const average = (raised[i - 1] + raised[i + 1] + raised[i - columns] + raised[i + columns]) / 4;
        support[i] = Math.max(raised[i] - 3, average);
      }
    }

    for (let row = 0; row < rows; row++) {
      const v = row / (rows - 1), y = foot + v * length, free = aisleAt(y);
      for (let col = 0; col < columns; col++) {
        const u = col / (columns - 1), x = left + u * (right(free) - left);
        const edge = Math.min(u * width, (1 - u) * width, v * length, (1 - v) * length);
        const fullness = 1 - Math.exp(-edge / 44);
        const hem = bell((edge - 14) / 7);
        const sway = Math.sin(5 * v + 2 * u);
        // Loose cover fabric crests on one side of a fold and settles into the other.
        const footFold = (u - 0.12 - 0.46 * v - 0.05 * sway) / 0.085;
        const sideFold = (v - 0.32 - 0.42 * u - 0.055 * Math.sin(6 * u)) / 0.07;
        const folds = (31 * bell(footFold) - 15 * bell(footFold + 1.35)) * bell((v - 0.18) / 0.35)
          + (26 * bell(sideFold) - 13 * bell(sideFold - 1.4)) * bell((u - 0.84) / 0.33);
        const headDistance = (1 - v) * length;
        const cuff = (9 + 13 * bell((u - 0.36) / 0.3)) * bell((headDistance - 85 - 26 * sway) / 36);
        const filling = 49 + 14 * bell((u - 0.56) / 0.38) * bell((v - 0.44) / 0.46);
        const loft = 4 + fullness * (filling + folds + cuff) - 2 * hem;
        const drop = free * 48 * MathUtils.smoothstep(x - mattress.max.x, 0, 25);
        const i = row * columns + col;
        const base = mattress.max.z + Math.max(support[i], -drop);
        const z = base + loft;
        const shade = 1 - 0.12 * hem;
        // The print follows the cloth grid as the sleeper and hem change the drape.
        uv.setXY(i, u * width, v * length);
        uv.setXY(i + faceSize, u * width, v * length);
        colors.setXYZ(i, shade, shade, shade);
        colors.setXYZ(i + faceSize, shade, shade, shade);
        const hemY = y + v ** 5 * (5 * Math.sin(7 * u) + 3 * Math.sin(15 * u));
        const cornerInset = 14 * bell(Math.min(v, 1 - v) * length / 25);
        const hemX = x + ((1 - u) ** 12 - u ** 12) * (cornerInset + 2 * Math.sin(v * 21));
        positions.setXYZ(i, hemX, hemY, z);
        positions.setXYZ(i + faceSize, hemX, hemY, base + 1);
      }
    }
    positions.needsUpdate = true;
    colors.needsUpdate = true;
    uv.needsUpdate = true;
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();
    return true;
  }
  return { mesh, fit, dispose() { mesh.removeFromParent(); geometry.dispose(); material.dispose(); } };
}
