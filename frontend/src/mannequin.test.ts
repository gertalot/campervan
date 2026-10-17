import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
import { Box3, Quaternion, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createMannequin, seatedPose } from './mannequin';

it('uses measured legs and seats the person with feet on the floor and calves clear of the bench', async () => {
  const bytes = readFileSync(new URL('../public/models/mannequin.glb', import.meta.url));
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const { scene } = await new GLTFLoader().parseAsync(buffer, '');
  const mannequin = createMannequin(scene);
  const seat = new Box3(new Vector3(893, 85, 400), new Vector3(1493, 1365, 500));
  for (const height of [450, 500]) {
    seat.min.z = height - 100;
    seat.max.z = height;
    const fit = mannequin.seat(seatedPose, seat, 1393);
    expect(fit.feet.min.z).toBeCloseTo(0, 1);
    expect(fit.legs.max.x).toBeLessThanOrEqual(seat.min.x - 9.9);
    const hip = scene.getObjectByName('thigh_l')!.getWorldPosition(new Vector3());
    const knee = scene.getObjectByName('calf_l')!.getWorldPosition(new Vector3());
    expect(hip.distanceTo(knee)).toBeCloseTo(400, 1);
    expect(knee.z).toBeCloseTo(500, 1);
    mannequin.root.removeFromParent();
    const restored = mannequin.seat(seatedPose, seat, 1393);
    expect(restored.bounds.min.distanceTo(fit.bounds.min)).toBeLessThan(0.001);
  }
  mannequin.seat({ ...seatedPose, lean: 0, curvature: 0, headTilt: 0 }, seat, 1393);
  const neck = scene.getObjectByName('neck_01')!;
  const neutralNeck = neck.quaternion.clone();
  const head = scene.getObjectByName('head')!;
  const neutralHead = head.getWorldQuaternion(new Quaternion());
  // The reported pose must not force a large neck counter-rotation to maintain a downward gaze.
  mannequin.seat({ ...seatedPose, lean: 35, curvature: 45, headTilt: 25 }, seat, 1393);
  expect(neck.quaternion.angleTo(neutralNeck) * 180 / Math.PI).toBeLessThan(30);
  expect(head.getWorldQuaternion(new Quaternion()).angleTo(neutralHead) * 180 / Math.PI).toBeCloseTo(25, 1);
  // The deformation begins at the sacrum and has no large angular step above the lower back.
  const curved = mannequin.seat({ ...seatedPose, lean: 20, curvature: 40 }, seat, 1393);
  const base = scene.getObjectByName('back_0')!.getWorldPosition(new Vector3());
  expect(base.distanceTo(scene.getObjectByName('pelvis')!.getWorldPosition(new Vector3()))).toBeLessThan(0.001);
  for (let i = 1; i <= 12; i++) {
    const a = scene.getObjectByName(`back_${i - 1}`)!.getWorldQuaternion(new Quaternion());
    const b = scene.getObjectByName(`back_${i}`)!.getWorldQuaternion(new Quaternion());
    expect(a.angleTo(b) * 180 / Math.PI).toBeLessThan(4);
  }
  expect(curved.feet.min.z).toBeCloseTo(0, 1);
});
