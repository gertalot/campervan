/** Exact XZ or YZ cuts through the registered scan, in CAD millimetres. */
export interface SectionMesh {
  positions: Float32Array;
  indices: Uint32Array;
}

interface Bucket {
  mesh: SectionMesh;
  triangles: number[];
}

const BIN_MM = 50;

export class ScanSectionIndex {
  readonly min: number;
  readonly max: number;
  private readonly bins = new Map<number, Bucket[]>();

  constructor(meshes: SectionMesh[], private readonly axis: 0 | 1 = 1) {
    let min = Infinity, max = -Infinity, faceCount = 0;
    for (const mesh of meshes) {
      const { positions, indices } = mesh;
      if (positions.length % 3 || indices.length % 3) {
        throw new Error('The scan has incomplete vertex or triangle data.');
      }
      for (const value of positions) {
        if (!Number.isFinite(value)) throw new Error('The scan contains non-finite coordinates.');
      }
      const meshBins = new Map<number, number[]>();
      for (let triangle = 0; triangle < indices.length; triangle += 3) {
        const a = indices[triangle] * 3, b = indices[triangle + 1] * 3, c = indices[triangle + 2] * 3;
        if (a + 2 >= positions.length || b + 2 >= positions.length || c + 2 >= positions.length) {
          throw new Error('A scan triangle references a missing vertex.');
        }
        if (a === b || b === c || c === a) continue;
        const abx = positions[b] - positions[a], aby = positions[b + 1] - positions[a + 1];
        const abz = positions[b + 2] - positions[a + 2];
        const acx = positions[c] - positions[a], acy = positions[c + 1] - positions[a + 1];
        const acz = positions[c + 2] - positions[a + 2];
        if (abx * acy === aby * acx && aby * acz === abz * acy && abz * acx === abx * acz) continue;
        const low = Math.min(positions[a + axis], positions[b + axis], positions[c + axis]);
        const high = Math.max(positions[a + axis], positions[b + axis], positions[c + axis]);
        const first = Math.floor(low / BIN_MM), last = Math.floor(high / BIN_MM);
        if (last - first > 10000 || !Number.isSafeInteger(first) || !Number.isSafeInteger(last)) {
          throw new Error('The scan coordinates are too large to section in millimetres. Check its registration.');
        }
        min = Math.min(min, low); max = Math.max(max, high); faceCount++;
        for (let bin = first; bin <= last; bin++) {
          const triangles = meshBins.get(bin);
          if (triangles) triangles.push(triangle);
          else meshBins.set(bin, [triangle]);
        }
      }
      for (const [bin, triangles] of meshBins) {
        const buckets = this.bins.get(bin);
        if (buckets) buckets.push({ mesh, triangles });
        else this.bins.set(bin, [{ mesh, triangles }]);
      }
    }
    if (!faceCount || !Number.isFinite(min) || !Number.isFinite(max)) {
      throw new Error('The scan has no valid triangle faces to section.');
    }
    this.min = min; this.max = max;
  }

  /** XYZ vertex pairs. Open contours and all disconnected fragments stay open. */
  section(position: number): Float32Array {
    if (!Number.isFinite(position)) throw new Error('The cross-section position must be a finite number.');
    if (position < this.min || position > this.max) return new Float32Array();
    const segments: number[] = [];
    const coordinates = new Float64Array(6);
    const axis = this.axis;
    for (const { mesh, triangles } of this.bins.get(Math.floor(position / BIN_MM)) ?? []) {
      const { positions, indices } = mesh;
      for (const triangle of triangles) {
        let hits = 0;
        for (let edge = 0; edge < 3; edge++) {
          const a = indices[triangle + edge] * 3;
          const b = indices[triangle + (edge + 1) % 3] * 3;
          const av = positions[a + axis], bv = positions[b + axis];
          // Half-open edges count a plane vertex once. Entirely coplanar faces
          // have no unique cut line and contribute no invented interior edges.
          if (!((av <= position && bv > position) || (bv <= position && av > position))) continue;
          const t = (position - av) / (bv - av);
          for (let coordinate = 0; coordinate < 3; coordinate++) {
            coordinates[hits * 3 + coordinate] = coordinate === axis
              ? position : positions[a + coordinate] + t * (positions[b + coordinate] - positions[a + coordinate]);
          }
          hits++;
        }
        if (hits === 2 && (coordinates[0] !== coordinates[3] || coordinates[1] !== coordinates[4]
          || coordinates[2] !== coordinates[5])) {
          segments.push(...coordinates);
        }
      }
    }
    return new Float32Array(segments);
  }
}
