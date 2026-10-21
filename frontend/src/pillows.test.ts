import { expect, it } from 'vitest';
import { Box3, BoxGeometry, Group, Mesh, MeshBasicMaterial, Vector3 } from 'three';
import { createPillows } from './pillows';

it('uses cloth geometry and changes from 680mm to the measured 500mm fluffed width', () => {
  const group = new Group() as Group & { front: Mesh; back: Mesh };
  const old = new BoxGeometry(680, 400, 200).translate(-340, 200, 100);
  group.front = new Mesh(old, new MeshBasicMaterial());
  group.back = new Mesh(old, new MeshBasicMaterial());
  group.add(group.front, group.back);
  const pillows = createPillows();
  pillows.attach({ '/Campervan/Cross bench/Cushions/Front pillow/Pillow': group });
  expect(group.front.geometry.getAttribute('position').count).toBeGreaterThan(1000);
  for (const [percent, width] of [[0, 680], [100, 500]]) {
    pillows.pose(percent);
    const bounds = new Box3().setFromObject(group);
    expect(bounds.getCenter(new Vector3()).toArray()).toEqual([-340, 200, 100]);
    const size = bounds.getSize(new Vector3());
    expect(size.x).toBeCloseTo(width);
    expect(size.y).toBeCloseTo(400);
    expect(size.z).toBeCloseTo(200);
  }
});
