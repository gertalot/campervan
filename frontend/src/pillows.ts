import { BufferGeometry, Float32BufferAttribute, IntType, Uint32BufferAttribute,
  Box3, Matrix4, Quaternion, Vector3, type Mesh, type Object3D } from 'three';
import asset from '../../src/campervan/cad/pillow_mesh.json';

/** Poly Haven cloth mesh inside the CAD pillow's existing pose/visibility group. */
export function createPillows() {
  const meshes: { mesh: Mesh; supportsHead: boolean; original: Float32Array; lift?: Object3D }[] = [];
  const placements: { root: Object3D; day: Vector3; night: Vector3; rotation: Quaternion; lift?: Object3D }[] = [];
  let backrest: Object3D | undefined;
  return {
    attach(groups: Record<string, unknown>) {
      meshes.length = 0;
      placements.length = 0;
      backrest = groups['/Campervan/Long bench/Cushions/Wall backrest/Foam/Core'] as Object3D | undefined;
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
          const bed = bounds(cross);
          // Recover the closed seat reference even when geometry arrives with
          // storage already open. The Foam assembly contains only the lift delta.
          long.updateWorldMatrix(true, true);
          const parent = long.parent!;
          const unlift = parent.matrixWorld.clone().multiply(long.matrix.clone().invert())
            .multiply(parent.matrixWorld.clone().invert());
          const seatMesh = (groups['/Campervan/Long bench/Cushions/Long seat/Foam/Core'] as
            Object3D & { front: Mesh }).front;
          seatMesh.geometry.computeBoundingBox();
          const seat = seatMesh.geometry.boundingBox!.clone()
            .applyMatrix4(inverse.clone().multiply(unlift).multiply(seatMesh.matrixWorld));
          const rear = path.includes('/Rear pillow/');
          const rotation = new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), rear ? Math.PI / 4 : 0)
            .multiply(new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), rear ? -Math.PI / 4 : Math.PI / 4));
          const points: Vector3[] = [];
          for (let i = 0; i < asset.positions.length; i += 3) {
            points.push(new Vector3(-asset.positions[i] * 600,
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
            bed.max.y - 200, bed.max.z + 100), rotation, lift: rear ? long : undefined });
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
        const lift = path.includes('/Rear pillow/') ? long : undefined;
        meshes.push({ mesh, supportsHead: path.includes("/Front pillow/"), original: new Float32Array(vertices), lift });
        if (cad.back) meshes.push({ mesh: cad.back, supportsHead: path.includes("/Front pillow/"),
          original: new Float32Array(vertices), lift });
      }
    },
    supportHead(head: Box3 | null, front = true) {
      for (const { mesh, supportsHead, original } of meshes) {
        if (supportsHead !== front) continue;
        const positions = mesh.geometry.getAttribute('position');
        mesh.updateWorldMatrix(true, false);
        const inverse = mesh.matrixWorld.clone().invert();
        const center = head?.getCenter(new Vector3());
        for (let i = 0; i < positions.count; i++) {
          const point = new Vector3(original[i * 3], original[i * 3 + 1], original[i * 3 + 2]);
          if (head && center && point.z > 0) {
            point.applyMatrix4(mesh.matrixWorld);
            const radius = Math.hypot((point.x - center.x) / 120, (point.y - center.y) / 145);
            const weight = Math.max(0, Math.min(1, (1.5 - radius) / .65));
            point.z -= Math.max(0, point.z - head.min.z) * weight;
            point.applyMatrix4(inverse);
          }
          positions.setXYZ(i, point.x, point.y, point.z);
        }
        positions.needsUpdate = true;
        mesh.geometry.computeVertexNormals();
        mesh.geometry.computeBoundingBox();
        mesh.geometry.computeBoundingSphere();
      }
    },
    pose(percent: number, lidPercent = 0) {
      const compression = Math.max(0, Math.min(1, (percent - 40) / 40));
      for (const { root, day, night, rotation, lift } of placements) {
        root.position.copy(day).lerp(night, compression);
        root.quaternion.copy(rotation).slerp(new Quaternion(), compression);
        root.scale.set(1, 1, 1);
        root.updateMatrix();
        if (lift && lidPercent > 0) {
          const parent = lift.parent!;
          parent.updateMatrix(); lift.updateMatrix();
          const delta = parent.matrix.clone().multiply(lift.matrix).multiply(parent.matrix.clone().invert());
          root.matrix.premultiply(delta).decompose(root.position, root.quaternion, root.scale);
          const up = new Vector3(0, 0, 1).transformDirection(parent.matrix.clone().multiply(lift.matrix));
          root.position.addScaledVector(up, -3 * lidPercent / 100);
        }
        root.updateMatrixWorld(true);
      }
      for (const { mesh } of meshes) {
        mesh.scale.x = 600;
        mesh.updateMatrixWorld(true);
      }
      this.supportHead(null, false);
    },
    squash(bedPercent = 0) {
      if (bedPercent > 0) return;
      // Small, direct cloth flattening against orange. There is no simulation.
      const orange = (backrest as (Object3D & { front?: Mesh }) | undefined)?.front;
      if (orange) orange.updateWorldMatrix(true, false);
      const orangeBounds = orange ? new Box3().setFromObject(orange) : null;
      const normal = orange ? new Vector3(0, 0, 1).transformDirection(orange.matrixWorld) : new Vector3();
      const plane = new Vector3();
      if (orange) {
        orange.geometry.computeBoundingBox();
        orange.geometry.boundingBox!.getCenter(plane);
        plane.z = orange.geometry.boundingBox!.max.z;
        plane.applyMatrix4(orange.matrixWorld);
      }
      for (const { mesh, supportsHead, original, lift } of meshes) {
        if (supportsHead) continue;
        const positions = mesh.geometry.getAttribute('position');
        const pillowBounds = new Box3().setFromObject(mesh);
        const contact = orangeBounds && lift
          && pillowBounds.max.y > orangeBounds.min.y && pillowBounds.min.y < orangeBounds.max.y
          && pillowBounds.max.z > orangeBounds.min.z && pillowBounds.min.z < orangeBounds.max.z;
        const direction = new Vector3();
        if (contact) {
          const up = new Vector3(0, 0, 1).transformDirection(lift.matrixWorld);
          const dot = normal.dot(up);
          direction.copy(normal).addScaledVector(up, -dot).divideScalar(1 - dot * dot);
        }
        const point = new Vector3();
        let penetration = 0;
        if (contact) for (let i = 0; i < positions.count; i++) {
          point.fromArray(original, i * 3).applyMatrix4(mesh.matrixWorld);
          penetration = Math.max(penetration, 0.5 - point.sub(plane).dot(normal));
        }
        const shift = Math.max(0, penetration - 15);
        const inverse = mesh.matrixWorld.clone().invert();
        for (let i = 0; i < positions.count; i++) {
          point.fromArray(original, i * 3);
          if (contact) {
            point.applyMatrix4(mesh.matrixWorld).addScaledVector(direction, shift);
            const distance = point.clone().sub(plane).dot(normal);
            point.addScaledVector(direction, Math.max(0, 0.5 - distance)).applyMatrix4(inverse);
          }
          positions.setXYZ(i, point.x, point.y, point.z);
        }
        positions.needsUpdate = true;
        mesh.geometry.computeVertexNormals();
        mesh.geometry.computeBoundingBox(); mesh.geometry.computeBoundingSphere();
      }
    },
  };
}
