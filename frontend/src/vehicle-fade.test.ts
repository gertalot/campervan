import { expect, it } from 'vitest';
import { MeshBasicMaterial, Quaternion, Vector3 } from 'three';
import { createVehicleFade } from './vehicle-fade';

function panel(opacity = 0.32) {
  return {
    front: { material: new MeshBasicMaterial({ opacity, transparent: true, depthWrite: false }) },
    back: { material: new MeshBasicMaterial({ opacity, transparent: true, depthWrite: false }) },
    edges: { material: new MeshBasicMaterial({ transparent: true, depthWrite: false }) },
    setTransparent() {},
  };
}

it('keeps the far wall and rear corner opaque while fading the near side, from either side', () => {
  const left = panel(), right = panel(), leftCorner = panel(), rightCorner = panel();
  const fade = createVehicleFade();
  const prefix = '/Campervan/Vehicle references/';
  fade.attach({
    [`${prefix}Side walls/Left wall/Side panel`]: left,
    [`${prefix}Side walls/Right wall/Side panel`]: right,
    [`${prefix}Rear corners/Left rear corner`]: leftCorner,
    [`${prefix}Rear corners/Right rear corner`]: rightCorner,
  });
  for (const side of [-1, 1]) {
    // Looking from behind and to one side used to fade both rear corners.
    const direction = new Vector3(side, -1, 0.5).normalize();
    fade.update(new Quaternion().setFromUnitVectors(new Vector3(0, 0, 1), direction).toArray());
    const far = side === 1 ? [left, leftCorner] : [right, rightCorner];
    const near = side === 1 ? [right, rightCorner] : [left, leftCorner];
    for (const group of far) {
      for (const mesh of [group.front, group.back]) {
        expect(mesh.material.opacity).toBe(1);
        expect(mesh.material.depthWrite).toBe(true);
      }
    }
    for (const group of near) {
      expect(group.front.material.opacity).toBeCloseTo(0.05);
      expect(group.front.material.depthWrite).toBe(false);
    }
  }
});

it('preserves far-side glass transparency and restores original materials when disabled', () => {
  const wall = panel(), glass = panel(0.12);
  const fade = createVehicleFade();
  const prefix = '/Campervan/Vehicle references/Side walls/Left wall/';
  fade.attach({ [`${prefix}Side panel`]: wall, [`${prefix}Rear window/Window glass`]: glass });
  fade.update(new Quaternion().setFromUnitVectors(new Vector3(0, 0, 1), new Vector3(1, 0, 0)).toArray());
  expect(wall.front.material.opacity).toBe(1);
  expect(glass.front.material.opacity).toBe(0.12);
  expect(glass.front.material.depthWrite).toBe(false);
  fade.restore();
  expect(wall.front.material.opacity).toBe(0.32);
  expect(wall.front.material.depthWrite).toBe(false);
  expect(glass.front.material.opacity).toBe(0.12);
});

it('fades both cab seats only when viewed from the front', () => {
  const driver = panel(), passenger = panel(), support = panel();
  const fade = createVehicleFade();
  const prefix = '/Campervan/Vehicle references/Cab/Seats/';
  fade.attach({
    [`${prefix}Driver seat/Integrated backrest and headrest`]: driver,
    [`${prefix}Passenger seat/Cushion`]: passenger,
    [`${prefix}Driver seat/Seat supports/Left support`]: support,
  });
  for (const [direction, opacity] of [
    [new Vector3(0, 1, 0), 0.25],
    [new Vector3(0, -1, 0), 1],
    [new Vector3(-1, 0, 0), 1],
    [new Vector3(1, 0, 0), 1],
    [new Vector3(0, 0, 1), 1],
  ] as const) {
    fade.update(new Quaternion().setFromUnitVectors(new Vector3(0, 0, 1), direction).toArray());
    for (const seat of [driver, passenger, support]) {
      expect(seat.front.material.opacity).toBeCloseTo(opacity);
      expect(seat.back.material.opacity).toBeCloseTo(opacity);
    }
  }
});
