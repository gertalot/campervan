// The physical set-out is the same on both floor sheets and the pump lid.
import proof from '../../docs/research/red-room-floor-proof.svg?raw';

const tile = new DOMParser().parseFromString(proof, 'image/svg+xml').querySelector('pattern')!;
const band = tile.querySelector('path')!;
const stripe = tile.patternTransform.baseVal.getItem(0).matrix.a;
export const floorPattern = {
  stripe,
  width: tile.width.baseVal.value * stripe,
  height: tile.height.baseVal.value * stripe,
  cream: tile.querySelector('rect')!.getAttribute('fill')!,
  brown: band.getAttribute('fill')!,
  bandPath: band.getAttribute('d')!,
};

export interface FloorPatternSettings { rotation: number; stripe: number; angle: number }
export const defaultFloorPattern: FloorPatternSettings = { rotation: 0, stripe, angle: 90 };

// Half the tip angle sets the horizontal run for one unit of rise.
export function chevronAspect(angle: number) {
  return angle === 90 ? 1 : Math.tan(angle * Math.PI / 360);
}

// Transform artwork units (one stripe each) to millimetres on the cut floor.
// Floor coordinates increase to the right and towards the cab. Positive control angles turn clockwise.
export function floorPatternTransform(settings: FloorPatternSettings, width: number, length: number) {
  return new DOMMatrix().translate(width / 2, length / 2).rotate(-settings.rotation)
    .translate(-width / 2, -length / 2).scale(settings.stripe * chevronAspect(settings.angle), settings.stripe);
}

export function floorPatternTile(id: string, aspect = 1) {
  const copy = tile.cloneNode(true) as SVGPatternElement;
  copy.id = id;
  copy.setAttribute('patternTransform', `scale(${stripe * aspect} ${stripe})`);
  return new XMLSerializer().serializeToString(copy);
}

export const floorRoot = 'Finished floor plywood';
export const floorPieces = {
  bench: 'Bench-side panel',
  aisle: 'Aisle panel',
  lid: 'Fuel pump hatch/Lift-out plywood lid',
};
