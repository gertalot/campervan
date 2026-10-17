import {
  Bone, Box3, BufferGeometry, DoubleSide, Group, Mesh, MeshStandardMaterial, Quaternion, Scene, SkinnedMesh, Vector3,
} from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createSpine } from './spine-rig';

export interface MannequinPose {
  visible: boolean;
  x: number; y: number; z: number; facing: number; compression: number;
  lean: number; curvature: number; headTilt: number; hip: number; knee: number; shoulder: number; elbow: number;
  autoLegs: boolean; fitSeat: boolean;
}
export const seatedPose: MannequinPose = {
  visible: true, x: 1153, y: 700, z: 560, facing: 270, compression: 30,
  lean: 20, curvature: 35, headTilt: 15, hip: 82, knee: 82, shoulder: 10, elbow: 80, autoLegs: true, fitSeat: true,
};
interface RigPose {
  visible: boolean; x: number; y: number; z: number; facing: number;
  lean: number; curvature: number; headTilt: number; hip: number; knee: number; shoulder: number; elbow: number;
}
const radians = (degrees: number) => degrees * Math.PI / 180;
const direction = (angle: number) => new Vector3(0, -Math.cos(radians(angle)), Math.sin(radians(angle)));

/** GLB rest space is metres, Y-up, facing +Z. CAD space is millimetres, Z-up. */
export function createMannequin(body: Group) {
  const root = new Group();
  root.name = 'Mannequin';
  const bones = new Map<string, Bone>();
  const meshes: SkinnedMesh[] = [];
  body.updateMatrixWorld(true);
  body.traverse(object => {
    if (object instanceof Bone) bones.set(object.name, object);
    if (object instanceof SkinnedMesh) meshes.push(object);
  });
  const bone = (name: string) => {
    const found = bones.get(name);
    if (!found) throw new Error(`Mannequin is missing bone ${name}`);
    return found;
  };
  function aim(name: string, child: string, target: Vector3) {
    const joint = bone(name);
    const origin = joint.getWorldPosition(new Vector3());
    const current = bone(child).getWorldPosition(new Vector3()).sub(origin).normalize();
    const rotation = new Quaternion().setFromUnitVectors(current, target.clone().normalize());
    const world = joint.getWorldQuaternion(new Quaternion()).premultiply(rotation);
    const parent = joint.parent!.getWorldQuaternion(new Quaternion());
    joint.quaternion.copy(parent.invert().multiply(world));
    joint.updateMatrixWorld(true);
  }
  function pitch(name: string, degrees: number) {
    const joint = bone(name);
    const rotation = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), radians(degrees));
    const world = joint.getWorldQuaternion(new Quaternion()).premultiply(rotation);
    joint.quaternion.copy(joint.parent!.getWorldQuaternion(new Quaternion()).invert().multiply(world));
    joint.updateMatrixWorld(true);
  }
  const footDirections = new Map(['l', 'r'].map(side => {
    const direction = bone(`ball_${side}`).getWorldPosition(new Vector3())
      .sub(bone(`foot_${side}`).getWorldPosition(new Vector3()));
    direction.x = 0;
    return [side, direction];
  }));

  // Straighten the limbs before measuring, retaining the spine and neck's anatomical rest curves.
  for (const side of ['l', 'r']) {
    aim(`thigh_${side}`, `calf_${side}`, direction(0));
    aim(`calf_${side}`, `foot_${side}`, direction(0));
    // Ankle-to-toe bones slope downward in a flat foot; a horizontal bone tips the toes upward.
    aim(`foot_${side}`, `ball_${side}`, footDirections.get(side)!);
    aim(`upperarm_${side}`, `lowerarm_${side}`, direction(0));
    aim(`lowerarm_${side}`, `hand_${side}`, direction(0));
  }
  let sole = Infinity, crotch = Infinity, crown = -Infinity;
  for (const mesh of meshes) {
    const positions = mesh.geometry.attributes.position;
    const posed = positions.clone();
    const inverse = mesh.matrixWorld.clone().invert();
    const point = new Vector3();
    for (let i = 0; i < positions.count; i++) {
      mesh.getVertexPosition(i, point).applyMatrix4(mesh.matrixWorld);
      sole = Math.min(sole, point.y);
      crown = Math.max(crown, point.y);
      // The lowest midline vertex is the crotch, not the higher hip joint.
      if (Math.abs(point.x) < 0.005) crotch = Math.min(crotch, point.y);
      point.applyMatrix4(inverse);
      posed.setXYZ(i, point.x, point.y, point.z);
    }
    mesh.geometry.setAttribute('position', posed);
  }
  const kneeHeight = bone('calf_l').getWorldPosition(new Vector3()).y;
  const hipHeight = bone('thigh_l').getWorldPosition(new Vector3()).y;
  function proportion(point: Vector3) {
    point.x *= 1780 / (crown - sole);
    point.z *= 1780 / (crown - sole);
    // Gert: sole-to-knee pivot 500mm, hip-to-knee 400mm, inseam 800mm, total height 1780mm.
    const levels = [[sole, 0], [kneeHeight, 500], [crotch, 800], [hipHeight, 900], [crown, 1780]];
    const end = Math.max(1, levels.findIndex(([height]) => height >= point.y));
    const [a, low] = levels[end - 1], [b, high] = levels[end];
    point.y = low + (point.y - a) * (high - low) / (b - a);
    return point;
  }
  const joints = new Map([...bones.values()].map(joint => [joint, proportion(joint.getWorldPosition(new Vector3()))]));
  for (const mesh of meshes) {
    const positions = mesh.geometry.attributes.position;
    const inverse = mesh.matrixWorld.clone().invert();
    const point = new Vector3();
    for (let i = 0; i < positions.count; i++) {
      point.fromBufferAttribute(positions, i).applyMatrix4(mesh.matrixWorld);
      proportion(point).applyMatrix4(inverse);
      positions.setXYZ(i, point.x, point.y, point.z);
    }
    positions.needsUpdate = true;
    mesh.geometry.computeVertexNormals();
    // Poses change the bounds; avoid rest-pose frustum culling.
    mesh.frustumCulled = false;
  }
  // Traverse parent-first so every joint retains its orientation while its position is resized.
  body.traverse(object => {
    if (!(object instanceof Bone)) return;
    object.position.copy(object.parent!.worldToLocal(joints.get(object)!.clone()));
    object.updateMatrixWorld(true);
  });
  const spine = createSpine(body, bones, meshes);
  for (const mesh of meshes) {
    mesh.skeleton.calculateInverses();
    mesh.bind(mesh.skeleton, mesh.matrixWorld);
  }
  const rest = new Map([...bones.values()].map(joint => [joint, joint.quaternion.clone()]));
  const pelvis = bone('pelvis').getWorldPosition(new Vector3());
  for (const side of ['l', 'r']) {
    footDirections.set(side, bone(`ball_${side}`).getWorldPosition(new Vector3())
      .sub(bone(`foot_${side}`).getWorldPosition(new Vector3())));
  }

  // Keep only contact vertices for quick seated fitting (no triangle collision engine).
  const contacts = meshes.map(mesh => {
    const groups: Record<string, number[]> = { pelvis: [], feet: [], legs: [] };
    const indices = mesh.geometry.attributes.skinIndex, weights = mesh.geometry.attributes.skinWeight;
    for (let i = 0; i < indices.count; i++) {
      let dominant = 0;
      for (let j = 1; j < 4; j++) if (weights.getComponent(i, j) > weights.getComponent(i, dominant)) dominant = j;
      const name = mesh.skeleton.bones[indices.getComponent(i, dominant)].name;
      if (name === 'pelvis') groups.pelvis.push(i);
      if (/^(foot|ball)_/.test(name)) groups.feet.push(i);
      if (/^(calf|foot|ball)_/.test(name)) groups.legs.push(i);
    }
    return { mesh, groups };
  });
  function contactBounds(group: string) {
    const bounds = new Box3();
    for (const { mesh, groups } of contacts) for (const index of groups[group]) {
      bounds.expandByPoint(mesh.getVertexPosition(index, new Vector3()).applyMatrix4(mesh.matrixWorld));
    }
    return bounds;
  }
  let resourcesAdopted = false;
  const mannequin = {
    root,
    attach(scene: Scene) {
      if (!resourcesAdopted) {
        // OCP bundles its own Three.js. Allocate render resources through that copy:
        // its renderer caches geometry/materials by numeric IDs, which must not collide.
        let sample: Mesh<BufferGeometry, MeshStandardMaterial> | undefined;
        scene.traverse(object => {
          const candidate = object as Mesh<BufferGeometry, MeshStandardMaterial>;
          if (!sample && candidate.isMesh && candidate.material?.isMeshStandardMaterial) sample = candidate;
        });
        if (!sample) throw new Error('CAD scene has no surface material for the mannequin.');
        const Geometry = sample.geometry.constructor as typeof BufferGeometry;
        const Material = sample.material.constructor as typeof MeshStandardMaterial;
        for (const mesh of meshes) {
          mesh.geometry = new Geometry().copy(mesh.geometry);
          mesh.material = new Material({ color: 0x808080, roughness: 0.85, metalness: 0, side: DoubleSide });
        }
        resourcesAdopted = true;
      }
      scene.add(root);
    },
    setPose(pose: RigPose) {
      // Pose in the asset's untransformed world, then place the whole person in CAD space.
      body.removeFromParent();
      body.position.set(0, 0, 0);
      for (const [joint, rotation] of rest) joint.quaternion.copy(rotation);
      body.updateMatrixWorld(true);
      const shoulderPitch = spine.pose(pose.lean, pose.curvature);
      // Share gaze compensation across the cervical joints instead of cranking the skull against the neck.
      const gaze = pose.headTilt - shoulderPitch;
      pitch('neck_01', gaze * 0.6);
      pitch('head', gaze * 0.4);
      for (const side of ['l', 'r']) {
        aim(`thigh_${side}`, `calf_${side}`, direction(pose.hip));
        aim(`calf_${side}`, `foot_${side}`, direction(pose.hip - pose.knee));
        aim(`foot_${side}`, `ball_${side}`, footDirections.get(side)!);
        aim(`upperarm_${side}`, `lowerarm_${side}`, direction(pose.shoulder));
        aim(`lowerarm_${side}`, `hand_${side}`, direction(pose.shoulder + pose.elbow));
      }
      body.position.copy(pelvis).negate();
      root.add(body);
      root.rotation.set(Math.PI / 2, 0, radians(180 - pose.facing), 'ZYX');
      root.position.set(pose.x, pose.y, pose.z);
      root.visible = pose.visible;
      root.updateMatrixWorld(true);
      for (const mesh of meshes) mesh.skeleton.update();
    },
    seat(pose: MannequinPose, cushion: Box3, backrestFront: number) {
      const compression = Math.min(pose.compression, (cushion.max.z - cushion.min.z) * 0.5);
      const rig: RigPose = { ...pose, z: 0, hip: 90, knee: 90 };
      if (pose.fitSeat) { rig.x = cushion.min.x + 260; rig.facing = 270; }
      mannequin.setPose(rig);
      rig.z = pose.fitSeat ? cushion.max.z - compression - contactBounds('pelvis').min.z : pose.z;
      const hipOffset = bone('thigh_l').getWorldPosition(new Vector3()).z;
      let kneeTarget = 500;
      for (let i = 0; pose.autoLegs && i < 3; i++) {
        const drop = (rig.z + hipOffset - kneeTarget) / 400;
        if (Math.abs(drop) >= 1) throw new Error('This seat height is out of reach for the measured leg lengths.');
        rig.hip = rig.knee = Math.acos(drop) * 180 / Math.PI;
        mannequin.setPose(rig);
        kneeTarget -= contactBounds('feet').min.z;
      }
      if (!pose.autoLegs) {
        rig.hip = pose.hip;
        rig.knee = pose.knee;
        mannequin.setPose(rig);
        // Keep the joint angles the user chose; floor contact changes the hip height.
        rig.z -= contactBounds('feet').min.z;
        mannequin.setPose(rig);
      }
      // Calves must sit in front of the hard bench, and the back must clear the upright cushion.
      const calfClearance = contactBounds('legs').max.x - (cushion.min.x - 10);
      const bodyBounds = new Box3().setFromObject(root, true);
      const backClearance = bodyBounds.max.x - (backrestFront - 5);
      if (pose.fitSeat) rig.x -= Math.max(0, calfClearance, backClearance);
      const halfWidth = (bodyBounds.max.y - bodyBounds.min.y) / 2;
      if (pose.fitSeat) rig.y = Math.max(cushion.min.y + halfWidth + 110, Math.min(cushion.max.y - halfWidth - 10, pose.y));
      mannequin.setPose(rig);
      return {
        feet: contactBounds('feet'), legs: contactBounds('legs'), bounds: new Box3().setFromObject(root, true),
        pose: rig, hip: rig.hip, knee: rig.knee, compression: cushion.max.z - contactBounds('pelvis').min.z,
      };
    },
  };
  return mannequin;
}

export async function loadMannequin() {
  const asset = await new GLTFLoader().loadAsync('/models/mannequin.glb');
  return createMannequin(asset.scene);
}
