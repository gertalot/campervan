import { assembly, el, fullName, materialName, mm, partColour, partName, pieceKey } from './cutting-types';
import type { Group, Part, Placement, Point, Result, Sheet } from './cutting-types';

const ns = 'http://www.w3.org/2000/svg';
const pathData = (points: Point[]) => points.length ? `M${points.map(p => p.join(',')).join('L')}Z` : '';
const rectangle = (p: Part): Point[] => [[0, 0], [p.length, 0], [p.length, p.width], [0, p.width]];
const mirrorUpdates = new WeakMap<SVGSVGElement, (mirrored: boolean) => void>();
export const mirrorsPart = (part: Pick<Part, 'path'>) =>
  ['Long bench', 'Cross bench', 'Cabinet', 'Drawer', 'Laptop table', 'Stored gear'].includes(assembly(part));
export const mirrorsSheet = (sheet: Sheet) => sheet.parts.some(mirrorsPart);
export const cabinetSideLabel = (mirrored: boolean) => `Cabinet on ${mirrored ? 'right' : 'left'}`;

/** Reflect the complete sheet, preserving nested clearances, blanks and offcuts. */
export function drawingCut(cut: number[], sheet: Sheet, mirrored: boolean) {
  const [x1, y1, x2, y2] = cut;
  return mirrored && mirrorsSheet(sheet)
    ? [sheet.stock.length - x2, y1, sheet.stock.length - x1, y2] : cut;
}
export function updateDrawingMirror(svg: SVGSVGElement, mirrored: boolean) {
  mirrorUpdates.get(svg)?.(mirrored);
}
function node(tag: string, attrs: Record<string, string | number> = {}, text = '') {
  const n = document.createElementNS(ns, tag);
  for (const [key, value] of Object.entries(attrs)) n.setAttribute(key, String(value));
  if (text) n.textContent = text;
  return n;
}
function interactive(svg: SVGElement, part: Pick<Part, 'path'>, select: (path: string) => void) {
  svg.dataset.part = part.path; svg.setAttribute('tabindex', '0'); svg.setAttribute('role', 'button');
  svg.setAttribute('aria-label', fullName(part));
  svg.addEventListener('click', () => select(part.path));
  svg.addEventListener('keydown', event => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(part.path); }
  });
}

/** Named, flat CAD pieces. Identical pieces share a drawing and a visible quantity. */
export function pieceGallery(parts: Part[], groups: Group[], select: (path: string) => void, mirrored = false) {
  const gallery = el('div'); gallery.className = 'cut-piece-gallery';
  const batches = new Map<string, Part[]>();
  for (const part of parts) {
    const key = pieceKey(part);
    batches.set(key, [...(batches.get(key) ?? []), part]);
  }
  for (const batch of batches.values()) {
    const part = batch[0], group = groups.find(g => g.parts.some(p => p.path === part.path))!;
    const card = el('button'); card.type = 'button'; card.className = 'cut-piece-card'; card.dataset.part = part.path;
    card.dataset.partPaths = JSON.stringify(batch.map(piece => piece.path));
    const description = `${fullName(part)}, ${batch.length} pieces, ${mm(part.length)} by ${mm(part.width)} mm`;
    card.setAttribute('aria-label', description);
    card.onclick = () => select(part.path);
    const svg = document.createElementNS(ns, 'svg');
    const margin = Math.max(2, part.length * 0.025);
    svg.setAttribute('viewBox', `${-margin} ${-margin} ${part.length + margin * 2} ${part.width + margin * 2}`);
    svg.setAttribute('aria-hidden', 'true');
    const g = node('g');
    g.append(node('path', { d: [part.outline.length ? part.outline : rectangle(part), ...part.holes].map(pathData).join(' '),
      fill: partColour(part), 'fill-rule': 'evenodd', stroke: '#323c47', 'stroke-width': 1,
      'vector-effect': 'non-scaling-stroke' }));
    svg.append(g); card.append(svg);
    mirrorUpdates.set(svg, enabled => {
      const reflected = enabled && mirrorsPart(part);
      g.setAttribute('transform', reflected ? `translate(${part.length} 0) scale(-1 1)` : '');
      card.setAttribute('aria-label', `${description}${mirrorsPart(part) ? `, ${cabinetSideLabel(enabled).toLowerCase()}` : ''}`);
    });
    updateDrawingMirror(svg, mirrored);
    const caption = batch.length > 1 && part.material === 'ledges' ? `${mm(part.length)} mm timber pieces`
      : batch.length > 1 && part.material === 'slats' ? 'Bed slats'
      : batch.length > 1 ? partName(part).replace(/\s*\d+\s*/g, ' ').trim() : partName(part);
    const name = el('strong', caption);
    if (batch.length > 1) name.append(el('span', ` × ${batch.length}`));
    card.append(name, el('span', `${mm(part.length)} × ${mm(part.width)} mm`),
      el('small', group.kind === 'timber' ? materialName(group) : `${mm(part.thickness)} mm ${isPly(group) ? 'plywood' : 'sheet'}`));
    card.title = batch.map(p => fullName(p)).join('\n'); gallery.append(card);
  }
  return gallery;
}
const isPly = (g: Group) => /plywood/i.test(g.name);

function inside(p: Point, polygon: Point[]) {
  let hit = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i], [xj, yj] = polygon[j];
    if ((yi > p[1]) !== (yj > p[1]) && p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}
/** Put labels on the wood, including frames whose centre is an empty opening. */
function labelPoint(part: Placement): Point {
  const xs = part.outline.map(p => p[0]), ys = part.outline.map(p => p[1]);
  const left = Math.min(...xs), right = Math.max(...xs), top = Math.min(...ys), bottom = Math.max(...ys);
  const centre: Point = [(left + right) / 2, (top + bottom) / 2];
  const contains = (p: Point) => inside(p, part.outline) && !part.holes.some(h => inside(p, h));
  if (contains(centre)) return centre;
  for (let step = 1; step <= 20; step++) {
    for (const p of [[centre[0], top + (bottom - top) * step / 40],
      [left + (right - left) * step / 40, centre[1]]] as Point[]) if (contains(p)) return p;
  }
  return part.outline[0];
}

export function sheetDrawing(sheet: Sheet, group: Group, result: Result, index: number,
                             select: (path: string) => void, mirrored = false) {
  const svg = document.createElementNS(ns, 'svg');
  const { length, width } = sheet.stock;
  const font = Math.max(18, length / 75), padding = font * 1.9;
  const geometry: SVGElement[] = [], labels: { node: SVGElement; x: number; y: number; vertical: boolean }[] = [];
  svg.setAttribute('viewBox', `${-padding} ${-padding} ${length + padding * 2} ${width + padding * 2}`);
  svg.setAttribute('xmlns', ns); svg.setAttribute('role', 'group');
  const description = `${materialName(group)}, ${group.kind === 'timber' ? 'length' : 'sheet'} ${index + 1}, ${length} by ${width} mm`;
  svg.setAttribute('aria-label', description);
  const title = node('title', {}, `${materialName(group)} · Sheet ${index + 1} · ${mm(length)} × ${mm(width)} mm`);
  svg.append(title);
  svg.classList.add('cut-sheet-svg');
  svg.dataset.physicalWidth = String(length + padding * 2); svg.dataset.physicalHeight = String(width + padding * 2);
  const trim = result.options.trim, trimY = group.kind === 'timber' ? 0 : trim;
  const patternId = `trim-${group.key}-${index}`;
  const defs = node('defs'), pattern = node('pattern', { id: patternId, width: 10, height: 10, patternUnits: 'userSpaceOnUse' });
  pattern.append(node('path', { d: 'M0,10L10,0', stroke: '#bd5f3c', 'stroke-width': 2 })); defs.append(pattern); svg.append(defs);
  svg.append(node('rect', { width: length, height: width, fill: '#eeeae1', stroke: '#29313a', 'stroke-width': 3 }));
  if (trim) {
    for (const [x, y, w, h] of [[0, 0, length, trimY], [0, width - trimY, length, trimY],
      [0, 0, trim, width], [length - trim, 0, trim, width]]) {
      svg.append(node('rect', { x, y, width: w, height: h, fill: `url(#${patternId})` }));
    }
  }
  const offcut = result.best_offcut;
  if (offcut?.sheet === index) {
    const g = node('g', { 'pointer-events': 'none' });
    const offcutRect = node('rect', { x: offcut.x, y: offcut.y, width: offcut.length, height: offcut.width,
      fill: '#dae5d2', stroke: '#607954', 'stroke-width': 2, 'stroke-dasharray': '10 6' });
    geometry.push(offcutRect); g.append(offcutRect);
    g.append(node('title', {}, `Offcut · ${mm(offcut.length)} × ${mm(offcut.width)} mm`));
    const vertical = offcut.width > offcut.length;
    const x = offcut.x + offcut.length / 2, y = offcut.y + offcut.width / 2;
    if (Math.min(offcut.length, offcut.width) > font * 2 && Math.max(offcut.length, offcut.width) > font * 15) {
      const text = node('text', { x, y, 'text-anchor': 'middle', 'dominant-baseline': 'middle',
        'font-family': 'system-ui,sans-serif', 'font-size': font, fill: '#425737',
        transform: vertical ? `rotate(-90 ${x} ${y})` : '' },
      `Offcut · ${mm(offcut.length)} × ${mm(offcut.width)} mm`);
      labels.push({ node: text, x, y, vertical }); g.append(text);
    }
    svg.append(g);
  }
  for (const placement of sheet.parts) {
    const part = result.parts.find(p => p.path === placement.path)!;
    const g = node('g'); interactive(g, part, select);
    g.append(node('title', {}, `${fullName(part)} · ${mm(part.length)} × ${mm(part.width)} × ${mm(part.thickness)} mm`));
    if (placement.blank) {
      const [x, y, w, h] = placement.blank;
      const blank = node('rect', { x, y, width: w, height: h, fill: '#fffdf6', stroke: '#8a8e90',
        'stroke-width': 1.5, 'stroke-dasharray': '7 5' });
      geometry.push(blank); g.append(blank);
    }
    const outline = node('path', { d: [placement.outline, ...placement.holes].map(pathData).join(' '),
      fill: partColour(part), 'fill-rule': 'evenodd', stroke: '#35404a', 'stroke-width': 2 });
    geometry.push(outline); g.append(outline);
    const [x, y] = labelPoint(placement);
    const text = node('text', { x, y, fill: '#18212a', 'text-anchor': 'middle', 'dominant-baseline': 'middle',
      'font-family': 'system-ui,sans-serif', 'font-size': font, 'paint-order': 'stroke', stroke: '#fffdf5',
      'stroke-width': 4, 'stroke-linejoin': 'round', 'pointer-events': 'none' });
    const long = Math.max(part.length, part.width), narrow = Math.min(part.length, part.width);
    const placementXs = placement.outline.map(p => p[0]), placementYs = placement.outline.map(p => p[1]);
    const vertical = Math.max(...placementYs) - Math.min(...placementYs) > (Math.max(...placementXs) - Math.min(...placementXs)) * 2;
    if (vertical) text.setAttribute('transform', `rotate(-90 ${x} ${y})`);
    labels.push({ node: text, x, y, vertical });
    const label = narrow < font * 1.6 ? partName(part) : `${assembly(part)} · ${partName(part)}`;
    const maxChars = Math.max(8, Math.floor(long / (font * 0.56)) - 2);
    text.textContent = label.length > maxChars ? label.slice(0, maxChars - 1) + '…' : label;
    if (narrow < font) text.setAttribute('font-size', String(Math.max(10, narrow * 0.8)));
    g.append(text); svg.append(g);
  }
  // Saw lines are optional detail; outlines and names remain the main drawing.
  const cutLines = node('g', { class: 'cut-saw-lines', display: 'none', 'pointer-events': 'none' });
  for (const [i, cut] of sheet.cuts.entries()) {
    const [x1, y1, x2, y2] = cut;
    const line = node('line', { x1, y1, x2, y2, stroke: '#b23b24', 'stroke-width': Math.max(1, result.options.kerf), 'stroke-dasharray': '10 5' });
    geometry.push(line); cutLines.append(line);
    const label = node('text', { x: x1 + font / 2, y: y1 + font, fill: '#a32d17', 'font-size': font * 0.75 }, String(i + 1));
    labels.push({ node: label, x: x1 + font / 2, y: y1 + font, vertical: false }); cutLines.append(label);
  }
  svg.append(cutLines);
  svg.append(node('text', { x: length / 2, y: -font * 0.55, 'text-anchor': 'middle', fill: '#414b57',
    'font-size': font, 'font-family': 'system-ui,sans-serif' }, `${mm(length)} mm`));
  svg.append(node('text', { x: -font * 0.5, y: width / 2,
    transform: `rotate(-90 ${-font * 0.5} ${width / 2})`, 'text-anchor': 'middle', fill: '#414b57',
    'font-size': font, 'font-family': 'system-ui,sans-serif' }, `${mm(width)} mm`));
  const sideLabel = node('text', { x: length / 2, y: width + font * 1.3,
    'text-anchor': 'middle', fill: '#414b57', 'font-size': font * 0.75,
    'font-family': 'system-ui,sans-serif' });
  svg.append(sideLabel);
  mirrorUpdates.set(svg, enabled => {
    const reflected = enabled && mirrorsSheet(sheet);
    const transform = reflected ? `translate(${length} 0) scale(-1 1)` : '';
    for (const element of geometry) element.setAttribute('transform', transform);
    for (const label of labels) {
      const x = reflected ? length - label.x : label.x;
      label.node.setAttribute('x', String(x));
      label.node.setAttribute('transform', label.vertical ? `rotate(-90 ${x} ${label.y})` : '');
    }
    sideLabel.textContent = cabinetSideLabel(enabled);
    svg.setAttribute('aria-label', `${description}, ${cabinetSideLabel(enabled).toLowerCase()}`);
    title.textContent = `${materialName(group)} · Sheet ${index + 1} · ${mm(length)} × ${mm(width)} mm · ${cabinetSideLabel(enabled)}`;
  });
  updateDrawingMirror(svg, mirrored);
  return svg;
}
