import { categories } from './visibility';

const bed = '/Campervan/Long bench';
const lid = `${bed}/Hinged lid`;
const table = '/Campervan/Laptop table';

// The slat roots come first because the cross-bench frame also contains its fixed slats.
const paintGroups: Record<string, string[]> = {
  Slats: categories.slats,
  Skins: categories.cabinetSkin,
  Shelves: categories.cabinetShelves,
  'Cabinet frame': categories.cabinetFrames,
  'Bench frame': [
    `${bed}/Storage box`,
    `${lid}/Slotted plywood lid`,
    `${lid}/Wall-side cushion rail`,
    `${lid}/Sliding bed/Sliding assembly/Moving front slat support/Moving support frame`,
    '/Campervan/Cross bench/Fixed frame',
    `${table}/Fixed mount/Bench mounting pad`,
  ],
};

const under = (path: string, root: string) => path === root || path.startsWith(`${root}/`);

export function paintTarget(path: string): string | null {
  if (!path.startsWith('/Campervan/') || path.endsWith('/')) return null;
  if (path.split('/').includes('Scan reference')) return null;
  if (categories.cabinetDoors.some(root => under(path, root))) {
    const part = path.slice(path.lastIndexOf('/') + 1);
    if (['Plywood door', 'Cabinet 3 fixed cover', 'Box 8 fixed front'].includes(part)) return 'Doors';
    if (part === 'Pine hinge backing strip' || part === 'Pine stay door pad') return path;
    return null;
  }
  if (categories.cushions.some(root => under(path, root))) {
    return path.endsWith('/Foam/Core') ? 'Cushions' : null;
  }
  if (under(path, categories.vehicle[0])) {
    if (/\/(Rear window|Window glass|Cushion|Integrated backrest and headrest)(?:\/|$)/.test(path)) return null;
    if (path.endsWith('/Floor outline') || path.endsWith('/Clear opening')) return null;
  }
  for (const [group, roots] of Object.entries(paintGroups)) {
    if (roots.some(root => under(path, root))) return group;
  }
  if (under(path, table)) {
    // Mounted and stowed versions share the same wood, hinge halves and detachable Lagun hardware.
    for (const part of ['/Offset tabletop/', '/Lagun hardware/']) {
      const offset = path.indexOf(part);
      if (offset >= 0) return table + path.slice(offset);
    }
  }
  return path;
}
