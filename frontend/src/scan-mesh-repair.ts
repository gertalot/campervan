import { BufferGeometry, Color, Float32BufferAttribute, Mesh, SRGBColorSpace, Vector3, Vector4 } from 'three';
import trim from '../../data/scan-reference/window-trim.json';
import ceilingTrim from '../../data/scan-reference/ceiling-trim.json';
import { ceilingColour } from './scan-ceiling';
import type { ScanWindow } from './scan-outlines';

const clampColor = (channel: number) => Math.max(0, Math.min(1, channel));

// Rows are 5 mm apart, measured outwards from the glass: inward depth (mm), then scan RGB (sRGB bytes).
function measuredSection(rows: number[][]) {
  const samples = rows.map(([depth, r, g, b]) => {
    const c = new Color().setRGB(r / 255, g / 255, b / 255, SRGBColorSpace);
    return new Vector4(depth, c.r, c.g, c.b);
  });
  return (distance: number) => {
    const station = Math.min(distance / 5, samples.length - 1);
    const i = Math.floor(station);
    return samples[i].clone().lerp(samples[Math.min(i + 1, samples.length - 1)], station - i);
  };
}

/** Replace the damaged faces in the display copy. The measured scan keeps its original geometry. */
export function repairScanMesh(source: Mesh, windows: ScanWindow[], ceilingRim?: number[][]): BufferGeometry {
  const geometry = source.geometry;
  const index = geometry.getIndex();
  const pos = geometry.getAttribute('position'), rgb = geometry.getAttribute('color');
  if (!index || pos.count !== trim.sourceVertexCount || index.count !== 3 * trim.sourceFaceCount || !rgb) {
    throw new Error('The display repair requires the original indexed colour scan.');
  }

  const removed = new Uint8Array(trim.sourceFaceCount);
  for (const [start, end] of trim.removedFaceRanges) removed.fill(1, start, end);
  if (ceilingRim) {
    for (const [start, end] of ceilingTrim.removedFaceRanges) removed.fill(1, start, end);
  }
  const indices: number[] = [];
  for (let i = 0; i < index.count; i += 3) {
    if (!removed[i / 3]) indices.push(index.getX(i), index.getX(i + 1), index.getX(i + 2));
  }
  const positions = Array.from(pos.array), colors = Array.from(rgb.array);
  const toLocal = source.matrixWorld.clone().invert();
  const wallEdges: Record<string, number[][]> = trim.wallEdges;
  for (const { name, rim, direction, reveal } of windows) {
    const edge = wallEdges[name];
    const wall = edge.map(([id]) => new Vector3().fromBufferAttribute(pos, id).applyMatrix4(source.matrixWorld));
    const glass = rim.map(p => new Vector3(...p));
    const u = direction === 2 ? 'x' : 'y';
    const depth = direction === 2 ? 'y' : 'x';
    const low = measuredSection(reveal.jamb);
    const high = reveal.oppositeJamb ? measuredSection(reveal.oppositeJamb) : low;
    const sill = measuredSection(reveal.sill), top = measuredSection(reveal.top);
    const profiles = glass.map((point, i) => {
      const tangent = glass[(i + 1) % rim.length].clone().sub(glass[(i + rim.length - 1) % rim.length]);
      const length = Math.hypot(tangent[u], tangent.z);
      const nu = -tangent.z / length, nz = tangent[u] / length;
      const jamb = nu < 0 ? low : high, rail = nz < 0 ? sill : top;
      return {
        widthTo: (end: Vector3) => Math.max(0, nu * (end[u] - point[u]) + nz * (end.z - point.z)),
        sample: (d: number) => jamb(d).lerp(rail(d), nz * nz),
      };
    });

    function vertex(point: Vector3, sample: Vector4) {
      const id = positions.length / 3;
      const local = point.clone().applyMatrix4(toLocal);
      positions.push(local.x, local.y, local.z);
      colors.push(clampColor(sample.y), clampColor(sample.z), clampColor(sample.w));
      return id;
    }
    const lip = glass.map((point, i) => vertex(point, profiles[i].sample(0)));
    const width = Math.max(...edge.map(([, fraction], i) =>
      profiles[Math.round(fraction * rim.length) % rim.length].widthTo(wall[i])));
    const layers = Math.max(2, Math.ceil(width / 5));
    function section(w: number, r: number): number[] {
      const end = edge[w][0], span = profiles[r].widthTo(wall[w]);
      const outer = profiles[r].sample(span);
      const column = [lip[r]];
      for (let level = 1; level < layers; level++) {
        const t = level / layers;
        const p = glass[r].clone().lerp(wall[w], t);
        const sample = profiles[r].sample(t * span);
        // Fit the measured curve between the exact glass and metal endpoints.
        p[depth] += (direction === 1 ? -1 : 1) * (sample.x - t * outer.x);
        // Local scan colour takes over at the outer seam. The measured section supplies the lip and sill shading.
        const blend = t ** 4;
        sample.y += blend * (rgb.getX(end) - outer.y);
        sample.z += blend * (rgb.getY(end) - outer.z);
        sample.w += blend * (rgb.getZ(end) - outer.w);
        column.push(vertex(p, sample));
      }
      column.push(end);
      return column;
    }

    const first = section(0, 0);
    let previous = first;
    function triangle(a: number, b: number, c: number) {
      if (a === b || b === c || a === c) return;
      if (direction === 0) indices.push(a, b, c);
      else indices.push(a, c, b);
    }
    function join(w: number, r: number) {
      const next = w === 0 && r === 0 ? first : section(w, r);
      for (let k = 0; k < layers; k++) {
        triangle(previous[k + 1], previous[k], next[k]);
        triangle(previous[k + 1], next[k], next[k + 1]);
      }
      previous = next;
    }
    let cursor = 0;
    function joinRim(w: number, end: number) {
      while (cursor < end) join(w, ++cursor % rim.length);
    }
    for (const [i, [, fraction]] of edge.entries()) {
      joinRim(i, Math.round(fraction * rim.length));
      join((i + 1) % edge.length, cursor % rim.length);
    }
    joinRim(0, rim.length);
  }
  if (ceilingRim) {
    // Join the surviving scan edge to the same outer ring used by the replacement timber.
    const first = positions.length / 3;
    for (const p of ceilingRim) {
      positions.push(...new Vector3(...p).applyMatrix4(toLocal).toArray());
      colors.push(ceilingColour.r, ceilingColour.g, ceilingColour.b);
    }
    const rimId = (i: number) => first + i % ceilingRim.length;
    const wall = ceilingTrim.surroundToRim;
    for (const [i, [vertex, station]] of wall.entries()) {
      const [next, nextStation] = wall[(i + 1) % wall.length];
      const end = i + 1 === wall.length ? ceilingRim.length : nextStation;
      indices.push(rimId(station), vertex, next);
      for (let j = station; j < end; j++) indices.push(rimId(j), next, rimId(j + 1));
    }
  }
  const result = new BufferGeometry();
  result.setAttribute('position', new Float32BufferAttribute(positions, 3));
  result.setAttribute('color', new Float32BufferAttribute(colors, 3));
  result.setIndex(indices);
  return result;
}
