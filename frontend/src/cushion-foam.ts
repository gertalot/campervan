import { Box3, RepeatWrapping, SRGBColorSpace, TextureLoader, Vector3, type Object3D } from 'three';
import { forEachSkinVertex } from './mannequin';
import { createFoamSkin } from './foam-surface';
import { shirazVelvet } from './paint-swatch';

/** Preserve the existing seated-preview dent; it is independent of lid fitting. */
function seatedDent(human: Object3D | null, seat: Box3) {
  if (!human?.visible) return () => 0;
  const step = 25, height = seat.max.z - seat.min.z;
  const columns = Math.ceil((seat.max.x - seat.min.x) / step) + 1;
  const rows = Math.ceil((seat.max.y - seat.min.y) / step) + 1;
  const dents = new Float32Array(columns * rows);
  forEachSkinVertex(human, point => {
    if (point.x < seat.min.x || point.x > seat.max.x || point.y < seat.min.y || point.y > seat.max.y
      || point.z >= seat.max.z || point.z < seat.max.z - height * 0.55) return;
    const depth = seat.max.z - point.z + 2;
    const x = (point.x - seat.min.x) / step, y = (point.y - seat.min.y) / step;
    for (let row = Math.max(0, Math.floor(y) - 3); row <= Math.min(rows - 1, Math.ceil(y) + 3); row++) {
      for (let column = Math.max(0, Math.floor(x) - 3);
        column <= Math.min(columns - 1, Math.ceil(x) + 3); column++) {
        const distance = Math.hypot(column - x, row - y) * step;
        const falloff = Math.max(0, Math.min(1, (75 - distance) / 40));
        const index = row * columns + column;
        dents[index] = Math.max(dents[index], Math.min(height * 0.55, depth * falloff));
      }
    }
  });
  return (point: Vector3) => {
    const x = Math.max(0, Math.min(columns - 1, (point.x - seat.min.x) / step));
    const y = Math.max(0, Math.min(rows - 1, (point.y - seat.min.y) / step));
    const left = Math.floor(x), right = Math.min(columns - 1, left + 1);
    const bottom = Math.floor(y), top = Math.min(rows - 1, bottom + 1);
    const mix = (a: number, b: number, t: number) => a + (b - a) * t;
    return mix(mix(dents[bottom * columns + left], dents[bottom * columns + right], x - left),
      mix(dents[top * columns + left], dents[top * columns + right], x - left), y - bottom);
  };
}

/** One direct geometry update per pose. No physics, gravity, inertia or settling. */
export function createCushionFoam(seat: Object3D, back: Object3D, crossSeat: Object3D,
  onChange: () => void, inCoordinates: (operation: () => void) => void) {
  const velvet = new TextureLoader().load(shirazVelvet.image, onChange);
  velvet.name = shirazVelvet.id;
  velvet.colorSpace = SRGBColorSpace;
  velvet.wrapS = velvet.wrapT = RepeatWrapping;
  velvet.repeat.set(1 / shirazVelvet.width, 1 / shirazVelvet.height);
  const blue = createFoamSkin(seat, velvet), orange = createFoamSkin(back, velvet);
  const cross = createFoamSkin(crossSeat, velvet);
  cross.draw(() => {});
  const size = blue.localBounds.getSize(new Vector3());

  function update(human: Object3D | null, lidPercent: number) {
    blue.mesh.updateWorldMatrix(true, false); orange.mesh.updateWorldMatrix(true, false);
    const blueWorld = blue.mesh.matrixWorld.clone(), blueInverse = blueWorld.clone().invert();
    const orangeWorld = orange.mesh.matrixWorld.clone(), orangeInverse = orangeWorld.clone().invert();
    // Display the manufactured foam width, including its intentional overlap with the rails.
    const nominal = blue.localBounds;
    const left = nominal.min.x, right = nominal.max.x;
    const squeeze = 3 * Math.max(0, Math.min(1, lidPercent / 100));
    const height = size.z - squeeze;
    const dent = seatedDent(human, blue.bounds());
    blue.draw(point => {
      const throughFoam = (point.z - nominal.min.z) / size.z;
      point.z = nominal.min.z + throughFoam * height;
      point.applyMatrix4(blueWorld);
      point.z -= dent(point) * throughFoam;
      point.applyMatrix4(blueInverse);
    });

    // Blue stays a firm planar slab. Orange remains upright, rises as a whole,
    // and has at most 3mm of extra compression at its lower contact edge.
    const origin = new Vector3(left, nominal.min.y, nominal.min.z + height).applyMatrix4(blueWorld);
    const normal = new Vector3(0, 0, 1).transformDirection(blueWorld);
    const planeHeight = (x: number, y: number) => origin.z
      - (normal.x * (x - origin.x) + normal.y * (y - origin.y)) / normal.z;
    const seatBounds = new Box3(new Vector3(left, nominal.min.y, nominal.min.z),
      new Vector3(right, nominal.max.y, nominal.min.z + height)).applyMatrix4(blueWorld);
    const foot = orange.bounds();
    const overlap = foot.max.x > seatBounds.min.x + 0.1 && foot.min.x < seatBounds.max.x - 0.1
      && foot.max.y > seatBounds.min.y && foot.min.y < seatBounds.max.y;
    const contact = lidPercent > 0 && overlap;
    const maximum = Math.max(...[foot.min.x, foot.max.x].flatMap(x =>
      [foot.min.y, foot.max.y].map(y => planeHeight(x, y))));
    const rise = contact ? Math.max(0, maximum + 0.5 - foot.min.z - squeeze) : 0;
    orange.draw(point => {
      if (!contact) return;
      point.applyMatrix4(orangeWorld);
      // Every orange vertex stays above the same separating plane. Its
      // triangles therefore stay above it too, including between vertices.
      point.z = Math.max(point.z + rise, planeHeight(point.x, point.y) + 0.5);
      point.applyMatrix4(orangeInverse);
    });
    onChange();
  }

  return {
    bounds: () => blue.bounds(),
    mattressBounds: () => blue.bounds().union(orange.bounds()).union(cross.bounds()),
    deform(human: Object3D | null, lidPercent = 0) { inCoordinates(() => update(human, lidPercent)); },
    dispose() { blue.dispose(); orange.dispose(); cross.dispose(); velvet.dispose(); },
  };
}
