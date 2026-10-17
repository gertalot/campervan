import { Bone, Quaternion, Skeleton, Vector3, type Group, type SkinnedMesh } from 'three';

/** A continuous sagittal bend sampled by skinning bones, starting at the sacrum. */
export function createSpine(body: Group, bones: Map<string, Bone>, meshes: SkinnedMesh[]) {
  const pelvis = bones.get('pelvis')!;
  const origin = pelvis.getWorldPosition(new Vector3());
  const pelvisRotation = pelvis.getWorldQuaternion(new Quaternion());
  const length = bones.get('neck_01')!.getWorldPosition(new Vector3()).y - origin.y;
  const axis = new Vector3(1, 0, 0);
  const samples = Array.from({ length: 13 }, (_, i) => {
    const joint = new Bone();
    joint.name = `back_${i}`;
    body.add(joint);
    joint.position.copy(body.worldToLocal(origin.clone().add(new Vector3(0, length * i / 12, 0))));
    joint.updateMatrixWorld(true);
    bones.set(joint.name, joint);
    return joint;
  });
  // Carry shoulders, arms, neck and head from the top of the curve, retaining their native joints.
  // The original coarse torso bones no longer deform the trunk.
  samples.at(-1)!.attach(bones.get('spine_03')!);
  body.updateMatrixWorld(true);
  for (const mesh of meshes) {
    const originalBones = mesh.skeleton.bones;
    const trunk = ['pelvis', 'spine_01', 'spine_02', 'spine_03'].map(name => originalBones.indexOf(bones.get(name)!));
    const indices = mesh.geometry.attributes.skinIndex;
    const weights = mesh.geometry.attributes.skinWeight;
    const positions = mesh.geometry.attributes.position;
    const point = new Vector3();
    for (let i = 0; i < positions.count; i++) {
      point.fromBufferAttribute(positions, i).applyMatrix4(mesh.matrixWorld);
      if (point.y <= origin.y) continue;
      const influence = new Map<number, number>();
      let trunkWeight = 0;
      for (let j = 0; j < 4; j++) {
        const index = indices.getComponent(i, j), weight = weights.getComponent(i, j);
        if (trunk.includes(index)) trunkWeight += weight;
        else influence.set(index, (influence.get(index) ?? 0) + weight);
      }
      if (!trunkWeight) continue;
      const level = Math.min(12, (point.y - origin.y) / length * 12);
      const lower = Math.floor(level), upper = Math.min(12, lower + 1);
      const fraction = level - lower;
      influence.set(originalBones.length + lower, trunkWeight * (1 - fraction));
      if (fraction) influence.set(originalBones.length + upper, trunkWeight * fraction);
      // Retain the source rig's limb/neck influences alongside the continuous torso weights.
      const strongest = [...influence].filter(([, weight]) => weight > 0).sort((a, b) => b[1] - a[1]).slice(0, 4);
      const total = strongest.reduce((sum, [, weight]) => sum + weight, 0);
      for (let j = 0; j < 4; j++) {
        indices.setComponent(i, j, strongest[j]?.[0] ?? 0);
        weights.setComponent(i, j, (strongest[j]?.[1] ?? 0) / total);
      }
    }
    indices.needsUpdate = true;
    weights.needsUpdate = true;
    mesh.skeleton = new Skeleton([...originalBones, ...samples]);
  }

  function orient(joint: Bone, world: Quaternion) {
    joint.quaternion.copy(joint.parent!.getWorldQuaternion(new Quaternion()).invert().multiply(world));
    joint.updateMatrixWorld(true);
  }
  return {
    pose(recline: number, curvature: number) {
      const bend = curvature * Math.PI / 180;
      // Recline is the mean torso angle. The pelvis and shoulders are tangent to the same arc.
      const start = (-recline - curvature / 2) * Math.PI / 180;
      orient(pelvis, new Quaternion().setFromAxisAngle(axis, start).multiply(pelvisRotation));
      for (const [i, joint] of samples.entries()) {
        const t = i / 12, angle = start + bend * t;
        const y = Math.abs(bend) < 1e-8 ? length * t * Math.cos(start)
          : length * (Math.sin(angle) - Math.sin(start)) / bend;
        const z = Math.abs(bend) < 1e-8 ? length * t * Math.sin(start)
          : length * (Math.cos(start) - Math.cos(angle)) / bend;
        joint.position.copy(joint.parent!.worldToLocal(origin.clone().add(new Vector3(0, y, z))));
        orient(joint, new Quaternion().setFromAxisAngle(axis, angle));
      }
      return -recline + curvature / 2;
    },
  };
}
