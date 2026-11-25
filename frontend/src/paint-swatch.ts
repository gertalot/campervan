import wood from './assets/wood-table.webp';
import pine from './assets/pine-grain.webp';
import shiraz from './assets/landry-shiraz.webp';
import { floorPattern, floorPatternTile } from './floor-pattern';

export interface PaintSwatch { colour: string; opacity: number; texture: string }

export function samePaint(a: PaintSwatch, b: PaintSwatch) {
  return a.texture === b.texture && a.colour.toLowerCase() === b.colour.toLowerCase() && a.opacity === b.opacity;
}

const { width, height } = floorPattern;
const chevron = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
  <defs>${floorPatternTile('tile')}</defs><rect width="100%" height="100%" fill="url(#tile)"/></svg>`;

type PaintTexture = { id: string; label: string; defaultColour?: string } & (
  { image?: undefined } | { image: string; width: number; height: number }
);
// The ruler in the fabric photo gives the repeat size of the cropped tile.
export const shirazVelvet = { id: 'shiraz', label: 'Shiraz velvet', image: shiraz, width: 312, height: 312 };
export const paintTextures: readonly PaintTexture[] = [
  { id: 'solid', label: 'Solid colour' },
  // Wood Table 001, photographed by Dimitrios Savva and processed by Rico Cilliers.
  // https://polyhaven.com/a/wood_table_001 (CC0). The scanned tile spans 1.5 metres.
  { id: 'wood', label: 'Wood grain', image: wood, width: 1500, height: 1500 },
  // One board from Poly Haven's Coated Pine scan. The greyscale grain takes its colour from the selected stock.
  { id: 'pine', label: 'Dressed pine', image: pine, width: 740, height: 202, defaultColour: '#efd4b7' },
  shirazVelvet,
  { id: 'chevron', label: 'Floor chevron', image: 'data:image/svg+xml,' + encodeURIComponent(chevron), width, height },
];
