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

// Floor coordinates increase to the right and towards the cab. Positive control angles turn clockwise.
export function floorRotation(degrees: number, width: number, length: number) {
  return new DOMMatrix().translate(width / 2, length / 2).rotate(-degrees).translate(-width / 2, -length / 2);
}

export function floorPatternTile(id: string) {
  const copy = tile.cloneNode(true) as SVGPatternElement;
  copy.id = id;
  return new XMLSerializer().serializeToString(copy);
}

export const floorRoot = 'Finished floor plywood';
export const floorPieces = {
  bench: 'Bench-side panel',
  aisle: 'Aisle panel',
  lid: 'Fuel pump hatch/Lift-out plywood lid',
};
