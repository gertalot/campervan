import { assembly, blankDimensions, blankSize, el, fittingEdges, fittingMargins, fittingNote, fullName,
  materialName, mm, partColour, partName, pieceKey, sawSteps, templateFit, templateInstruction } from './cutting-types';
import type { Group, Part, Placement, Point, Result, Sheet } from './cutting-types';

const ns = 'http://www.w3.org/2000/svg';
const pathData = (points: Point[]) => points.length ? `M${points.map(p => p.join(',')).join('L')}Z` : '';
const rectangle = (p: Part): Point[] => [[0, 0], [p.length, 0], [p.length, p.width], [0, p.width]];
const mirrorUpdates = new WeakMap<SVGSVGElement, (mirrored: boolean) => void>();
let previewId = 0;
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
    const [blankLength, blankWidth] = blankSize(part), fitted = templateFit(part), margins = fittingMargins(part);
    const description = `${fullName(part)}, ${batch.length} pieces, cut blank ${blankDimensions(part)} mm${fitted ? ', template fit' : ''}`;
    card.setAttribute('aria-label', description);
    card.onclick = () => select(part.path);
    const svg = document.createElementNS(ns, 'svg');
    const margin = Math.max(fitted ? 40 : 2, blankLength * (fitted ? 0.06 : 0.025));
    svg.setAttribute('viewBox', `${-margin} ${-margin} ${blankLength + margin * 2} ${blankWidth + margin * 2}`);
    svg.setAttribute('aria-hidden', 'true');
    const g = node('g');
    const fittingLabels: { element: SVGElement; x: number; y: number }[] = [];
    if (fitted) {
      const id = `fitting-preview-${++previewId}`, defs = node('defs');
      const pattern = node('pattern', { id, width: 10, height: 10, patternUnits: 'userSpaceOnUse' });
      pattern.append(node('path', { d: 'M0,10L10,0', stroke: '#a78449', 'stroke-width': 1.5 }));
      defs.append(pattern); svg.append(defs);
      g.append(node('rect', { width: blankLength, height: blankWidth, fill: `url(#${id})`, stroke: '#323c47',
        'stroke-width': 1.5, 'vector-effect': 'non-scaling-stroke' }));
      const edgeLines = {
        left: [0, 0, 0, blankWidth], right: [blankLength, 0, blankLength, blankWidth],
        top: [0, 0, blankLength, 0], bottom: [0, blankWidth, blankLength, blankWidth],
      };
      const positions = {
        left: [margin * -0.5, blankWidth / 2], right: [blankLength + margin * 0.5, blankWidth / 2],
        top: [blankLength / 2, margin * -0.5], bottom: [blankLength / 2, blankWidth + margin * 0.5],
      };
      for (const edge of fittingEdges) {
        const [x1, y1, x2, y2] = edgeLines[edge];
        if (margins[edge] === 0) g.append(node('line', { x1, y1, x2, y2, stroke: '#1f6487', 'stroke-width': 2.5,
          'vector-effect': 'non-scaling-stroke' }));
        const [x, y] = positions[edge];
        const label = node('text', { x, y, 'text-anchor': 'middle', 'dominant-baseline': 'middle',
          'font-family': 'system-ui,sans-serif', 'font-size': Math.max(10, blankLength * 0.022), fill: '#24485d' },
        `${edge[0].toUpperCase()}: ${margins[edge] ? `+${mm(margins[edge])}` : 'datum'}`);
        label.append(node('title', {}, `${edge}${part.fitting_edges?.[edge] ? ` · ${part.fitting_edges[edge]}` : ''}`));
        fittingLabels.push({ element: label, x, y });
      }
    }
    g.append(node('path', { d: [part.outline.length ? part.outline : rectangle(part), ...part.holes].map(pathData).join(' '),
      fill: partColour(part), 'fill-rule': 'evenodd', stroke: '#323c47', 'stroke-width': 1,
      transform: fitted ? `translate(${margins.left} ${margins.top})` : '',
      ...(fitted ? { 'stroke-dasharray': '6 4' } : {}),
      'vector-effect': 'non-scaling-stroke' }));
    svg.append(g, ...fittingLabels.map(label => label.element)); card.append(svg);
    mirrorUpdates.set(svg, enabled => {
      const reflected = enabled && mirrorsPart(part);
      g.setAttribute('transform', reflected ? `translate(${blankLength} 0) scale(-1 1)` : '');
      for (const label of fittingLabels) label.element.setAttribute('x', String(reflected ? blankLength - label.x : label.x));
      card.setAttribute('aria-label', `${description}${mirrorsPart(part) ? `, ${cabinetSideLabel(enabled).toLowerCase()}` : ''}`);
    });
    updateDrawingMirror(svg, mirrored);
    const caption = batch.length > 1 && part.material === 'ledges' ? `${mm(part.length)} mm timber pieces`
      : batch.length > 1 && part.material === 'slats' ? 'Bed slats'
      : batch.length > 1 ? partName(part).replace(/\s*\d+\s*/g, ' ').trim() : partName(part);
    const name = el('strong', caption);
    if (batch.length > 1) name.append(el('span', ` × ${batch.length}`));
    card.append(name, el('span', `${fitted ? 'Cut blank: ' : ''}${blankDimensions(part)} mm`),
      el('small', group.kind === 'timber' ? materialName(group) : `${mm(part.thickness)} mm ${isPly(group) ? 'plywood' : 'sheet'}`));
    if (fitted) card.append(el('small', `CAD reference: ${mm(part.length)} × ${mm(part.width)} mm`),
      el('small', 'Template fit · dashed CAD reference · blue datum edges'));
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
  const fittedParts = sheet.parts.map(placement => result.parts.find(p => p.path === placement.path)!)
    .filter(templateFit);
  const hasFitting = fittedParts.length > 0;
  const legendHeight = hasFitting ? font * (3 + fittedParts.length * 1.6) : 0;
  const geometry: SVGElement[] = [], labels: { node: SVGElement; x: number; y: number; vertical: boolean }[] = [];
  svg.setAttribute('viewBox', `${-padding} ${-padding} ${length + padding * 2} ${width + padding * 2 + legendHeight}`);
  svg.setAttribute('xmlns', ns); svg.setAttribute('role', 'group');
  const description = `${materialName(group)}, ${group.kind === 'timber' ? 'length' : 'sheet'} ${index + 1}, ${length} by ${width} mm`;
  svg.setAttribute('aria-label', description);
  const title = node('title', {}, `${materialName(group)} · Sheet ${index + 1} · ${mm(length)} × ${mm(width)} mm`);
  svg.append(title);
  svg.classList.add('cut-sheet-svg');
  svg.dataset.physicalWidth = String(length + padding * 2); svg.dataset.physicalHeight = String(width + padding * 2 + legendHeight);
  const trim = result.options.trim, trimY = group.kind === 'timber' ? 0 : trim;
  const patternId = `trim-${group.key}-${index}`;
  const defs = node('defs'), pattern = node('pattern', { id: patternId, width: 10, height: 10, patternUnits: 'userSpaceOnUse' });
  pattern.append(node('path', { d: 'M0,10L10,0', stroke: '#bd5f3c', 'stroke-width': 2 })); defs.append(pattern); svg.append(defs);
  const fittingPatternId = `fitting-${group.key}-${index}`;
  const fittingPattern = node('pattern', { id: fittingPatternId, width: 14, height: 14, patternUnits: 'userSpaceOnUse' });
  fittingPattern.append(node('rect', { width: 14, height: 14, fill: '#fff8e4' }),
    node('path', { d: 'M0,14L14,0', stroke: '#b19862', 'stroke-width': 1.5 })); defs.append(fittingPattern);
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
    g.append(node('title', {}, `Largest rectangular offcut · ${mm(offcut.length)} × ${mm(offcut.width)} mm`));
    const vertical = offcut.width > offcut.length;
    const x = offcut.x + offcut.length / 2, y = offcut.y + offcut.width / 2;
    if (Math.min(offcut.length, offcut.width) > font * 2 && Math.max(offcut.length, offcut.width) > font * 15) {
      const text = node('text', { x, y, 'text-anchor': 'middle', 'dominant-baseline': 'middle',
        'font-family': 'system-ui,sans-serif', 'font-size': font, fill: '#425737',
        transform: vertical ? `rotate(-90 ${x} ${y})` : '' },
      `Largest offcut · ${mm(offcut.length)} × ${mm(offcut.width)} mm`);
      labels.push({ node: text, x, y, vertical }); g.append(text);
    }
    svg.append(g);
  }
  for (const placement of sheet.parts) {
    const part = result.parts.find(p => p.path === placement.path)!;
    const fitted = templateFit(part);
    const g = node('g'); interactive(g, part, select);
    g.append(node('title', {}, `${fullName(part)} · Cut blank ${blankDimensions(part)} × ${mm(part.thickness)} mm${fitted
      ? ` · CAD reference ${mm(part.length)} × ${mm(part.width)} mm · ${fittingNote(part)} · ${templateInstruction}` : ''}`));
    if (placement.blank) {
      const [x, y, w, h] = placement.blank;
      const blank = node('rect', { x, y, width: w, height: h, fill: fitted ? `url(#${fittingPatternId})` : '#fffdf6',
        stroke: fitted ? '#35404a' : '#8a8e90', 'stroke-width': fitted ? 2 : 1.5,
        ...(fitted ? {} : { 'stroke-dasharray': '7 5' }) });
      geometry.push(blank); g.append(blank);
      if (fitted) {
        const margins = fittingMargins(part), [bl, bw] = blankSize(part);
        const localEdges = {
          left: [0, 0, 0, bw], right: [bl, 0, bl, bw], top: [0, 0, bl, 0], bottom: [0, bw, bl, bw],
        };
        const angle = placement.angle * Math.PI / 180;
        const rotatedCorners = [[0, 0], [bl, 0], [bl, bw], [0, bw]].map(([cx, cy]) =>
          [cx * Math.cos(angle) - cy * Math.sin(angle), cx * Math.sin(angle) + cy * Math.cos(angle)]);
        const dx = x - Math.min(...rotatedCorners.map(p => p[0])), dy = y - Math.min(...rotatedCorners.map(p => p[1]));
        const transformed = (px: number, py: number) => [px * Math.cos(angle) - py * Math.sin(angle) + dx,
          px * Math.sin(angle) + py * Math.cos(angle) + dy];
        for (const edge of fittingEdges) if (margins[edge] === 0) {
          const [lx1, ly1, lx2, ly2] = localEdges[edge], [x1, y1] = transformed(lx1, ly1), [x2, y2] = transformed(lx2, ly2);
          const datum = node('line', { x1, y1, x2, y2, stroke: '#1f6487', 'stroke-width': 3 });
          datum.append(node('title', {}, `${edge} datum edge · no added allowance`)); geometry.push(datum); g.append(datum);
        }
      }
    }
    const outline = node('path', { d: [placement.outline, ...placement.holes].map(pathData).join(' '),
      fill: partColour(part), 'fill-rule': 'evenodd', stroke: '#35404a', 'stroke-width': 2,
      ...(fitted ? { 'stroke-dasharray': '10 6' } : {}) });
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
    const label = `${fitted ? `${part.id} · Template fit · ` : ''}${narrow < font * 1.6 ? partName(part) : `${assembly(part)} · ${partName(part)}`}`;
    const maxChars = Math.max(8, Math.floor(long / (font * 0.56)) - 2);
    text.textContent = label.length > maxChars ? label.slice(0, maxChars - 1) + '…' : label;
    if (narrow < font) text.setAttribute('font-size', String(Math.max(10, narrow * 0.8)));
    g.append(text); svg.append(g);
  }
  const cutLines = node('g', { class: 'cut-saw-lines', 'pointer-events': 'none' });
  const cutBadges = node('g');
  const badgePositions: Point[] = [];
  for (const [i, step] of sawSteps(sheet, result, group.kind).entries()) {
    const { cut } = step;
    const [x1, y1, x2, y2] = cut;
    const colour = step.kind === 'reference' ? '#006b70' : '#a32916';
    for (const [stroke, strokeWidth] of [['#fffdf5', 4.5], [colour, 1.8]] as const) {
      const line = node('line', { x1, y1, x2, y2, stroke, 'stroke-width': strokeWidth,
        'vector-effect': 'non-scaling-stroke', ...(stroke === colour ? { 'stroke-dasharray': '8 4' } : {}) });
      geometry.push(line); cutLines.append(line);
    }
    const candidates: Point[] = [0.5, 0.25, 0.75, 0.12, 0.88].map(t => [x1 + (x2 - x1) * t, y1 + (y2 - y1) * t]);
    const clearance = ([x, y]: Point) => Math.min(...badgePositions.map(([bx, by]) => Math.hypot(x - bx, y - by)));
    const position = candidates.find(p => clearance(p) > font * 2)
      ?? candidates.reduce((best, p) => clearance(p) > clearance(best) ? p : best);
    badgePositions.push(position);
    const [x, y] = position;
    const badge = node('circle', { cx: x, cy: y, r: font * 0.8, fill: colour, stroke: '#fffdf5', 'stroke-width': 5 });
    geometry.push(badge); cutBadges.append(badge);
    const label = node('text', { x, y, fill: '#fff', 'font-size': font * 1.1, 'text-anchor': 'middle',
      'dominant-baseline': 'central', 'font-family': 'system-ui,sans-serif', 'font-weight': 700 }, String(i + 1));
    labels.push({ node: label, x, y, vertical: false }); cutBadges.append(label);
  }
  // Paint every badge above every cut, including lines processed later in the sequence.
  cutLines.append(cutBadges);
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
  if (hasFitting) {
    for (const [i, line] of [
      'Template fit: solid outline = cut blank; dashed outline = CAD reference only.',
      'Hatched material stays until templating; blue edges = unchanged datum edges.',
      'Leave vehicle contours and notches uncut until fitted from a physical template.',
    ].entries()) svg.append(node('text', { x: 0, y: width + font * (2.4 + i * 0.7),
      fill: '#414b57', 'font-size': font * 0.65, 'font-family': 'system-ui,sans-serif' }, line));
    for (const [i, part] of fittedParts.entries()) {
      const y = width + font * (4.7 + i * 1.6);
      svg.append(node('text', { x: 0, y, fill: '#29333f', 'font-size': font * 0.7,
        'font-family': 'system-ui,sans-serif' },
      `${part.id} · ${fullName(part)} · Cut blank: ${blankDimensions(part)} mm · CAD reference: ${mm(part.length)} × ${mm(part.width)} mm`));
      svg.append(node('text', { x: 0, y: y + font * 0.7, fill: '#414b57', 'font-size': font * 0.65,
        'font-family': 'system-ui,sans-serif' }, `Fitting allowance: ${fittingNote(part)}`));
    }
  }
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
