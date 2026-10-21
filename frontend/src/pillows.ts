import { BufferGeometry, Float32BufferAttribute, IntType, Uint32BufferAttribute,
  Box3, Matrix4, Quaternion, Vector3, type Mesh, type Object3D } from 'three';
import asset from '../../src/campervan/cad/pillow_mesh.json';

/** Poly Haven cloth mesh inside the CAD pillow's existing pose/visibility group. */
export function createPillows() {
  const meshes: { mesh: Mesh; dayWidth: number }[] = [];
  const placements: { root: Object3D; day: Vector3; night: Vector3; rotation: Quaternion }[] = [];
  return {
    attach(groups: Record<string, unknown>) {
      meshes.length = 0;
      placements.length = 0;
      for (const [path, value] of Object.entries(groups)) {
        if (!path.endsWith('/Pillow')) continue;
        const cad = value as Object3D & { front: Mesh; back?: Mesh; edges?: Object3D & { geometry: BufferGeometry } };
        const root = cad.parent;
        const frame = root?.parent;
        const cross = groups['/Campervan/Cross bench/Cushions/Cross seat/Foam'] as Object3D | undefined;
        const long = groups['/Campervan/Long bench/Cushions/Long seat/Foam'] as Object3D | undefined;
        if (root && frame && cross && long) {
          frame.updateWorldMatrix(true, false);
          const inverse = frame.matrixWorld.clone().invert();
          const bounds = (object: Object3D) => new Box3().setFromObject(object).applyMatrix4(inverse);
          const bed = bounds(cross), seat = bounds(long);
          const rear = path.includes('/Rear pillow/');
          const rotation = new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), rear ? Math.PI / 4 : 0)
            .multiply(new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), rear ? -Math.PI / 4 : Math.PI / 4));
          const points: Vector3[] = [];
          for (let i = 0; i < asset.positions.length; i += 3) {
            points.push(new Vector3(-asset.positions[i] * (rear ? 500 : 680),
              asset.positions[i + 1] * 400, asset.positions[i + 2] * 200).applyQuaternion(rotation));
          }
          const cloth = new Box3().setFromPoints(points);
          const day = new Vector3(rear ? -2 * (seat.max.z - seat.min.z) - cloth.max.x : -340,
            rear ? seat.min.y - cloth.min.y : bed.max.y - cloth.max.y, bed.max.z - cloth.min.z);
          const cab = groups['/Campervan/Vehicle references/Cab/Seats/Driver seat/Integrated backrest and headrest'] as Object3D | undefined;
          if (!rear && cab) {
            // Contact the rendered seat triangles at the pillow's height, rather than the cross-bench edge.
            const front = (cab as Object3D & { front?: Mesh }).front;
            if (front) {
              front.updateWorldMatrix(true, false);
              const transform = new Matrix4().multiplyMatrices(inverse, front.matrixWorld);
              const positions = front.geometry.getAttribute('position');
              let contact = Infinity;
              for (let i = 0; i < positions.count; i++) {
                const v = new Vector3().fromBufferAttribute(positions, i).applyMatrix4(transform);
                if (v.z >= day.z + cloth.min.z && v.z <= day.z + cloth.max.z)
                  contact = Math.min(contact, v.y);
              }
              if (Number.isFinite(contact)) day.y = contact - cloth.max.y;
            }
          }
          // Owner adjustments to the folded layout, relative to the fitted pose.
          day.y += rear ? -150 : -60;
          day.x += rear ? 150 : -50;
          if (rear) rotation.premultiply(
            new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), -Math.PI / 12),
          );
          const middle = (bed.min.x + bed.max.x) / 2;
          placements.push({ root, day, night: new Vector3(middle + (rear ? 250 : -250),
            bed.max.y - 200, bed.max.z + 100), rotation });
          cad.position.set(0, 0, 0);
          cad.rotation.set(0, 0, 0);
        }
        const mesh = cad.front;
        if (!mesh) continue;
        mesh.geometry.computeBoundingBox();
        const centre = mesh.geometry.boundingBox!.getCenter(new Vector3());
        // OCP keeps a box's corner-based geometry and its separate placement.
        // Preserve that native centre when replacing it with a centred cloth mesh.
        if (root && frame && cross && long) {
          mesh.position.set(0, 0, 0);
          if (cad.back) cad.back.position.set(0, 0, 0);
        } else {
          mesh.position.add(centre);
          if (cad.back) cad.back.position.add(centre);
        }
        const geometry = new BufferGeometry();
        // Geometry is mirrored with the rest of the interior; reverse triangle winding too.
        const vertices = asset.positions.map((value, i) => value * [-1, 400, 200][i % 3]);
        const indices = [...asset.indices];
        for (let i = 0; i < indices.length; i += 3) [indices[i + 1], indices[i + 2]] = [indices[i + 2], indices[i + 1]];
        geometry.setAttribute('position', new Float32BufferAttribute(vertices, 3));
        geometry.setIndex(indices);
        geometry.computeVertexNormals();
        const ids = new Uint32BufferAttribute(new Uint32Array(vertices.length / 3), 1);
        ids.gpuType = IntType;
        geometry.setAttribute('componentId', ids);
        mesh.geometry.dispose();
        mesh.geometry.copy(geometry);
        if (cad.back && cad.back.geometry !== mesh.geometry) {
          cad.back.geometry.dispose();
          cad.back.geometry.copy(geometry);
        }
        geometry.dispose();
        // Remove the CAD envelope's hard edges, including after visibility changes.
        if (cad.edges) {
          cad.edges.geometry.dispose();
          cad.edges.geometry = new BufferGeometry();
        }
        meshes.push({ mesh, dayWidth: path.includes("/Rear pillow/") ? 500 : 680 });
        if (cad.back) meshes.push({ mesh: cad.back, dayWidth: path.includes("/Rear pillow/") ? 500 : 680 });
      }
    },
    pose(percent: number) {
      const compression = Math.max(0, Math.min(1, (percent - 40) / 40));
      for (const { root, day, night, rotation } of placements) {
        root.position.copy(day).lerp(night, compression);
        root.quaternion.copy(rotation).slerp(new Quaternion(), compression);
        root.updateMatrixWorld(true);
      }
      for (const { mesh, dayWidth } of meshes) {
        mesh.scale.x = dayWidth + (500 - dayWidth) * compression;
        mesh.updateMatrixWorld(true);
      }
    },
  };
}
