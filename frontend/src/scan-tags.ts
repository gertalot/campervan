/** Saved landmarks, measurements and one shared emphasis renderer in the existing native camera. */
import { Matrix4, Vector3, type Camera } from 'three';
import type { DistanceMeasurement } from './scan-measurements-api';

export interface ScanTag { id: number; pose: number[][]; size_m: number | null; observations: number }
export interface MeasurementPreview { from: number; to?: number; pointer?: { x: number; y: number } }
export interface ScanHighlight {
  tagIds: number[];
  connections?: { tag_a: number; tag_b: number }[];
  triangles?: number[][];
  vectors?: { id: number; before: number[]; after: number[]; distance_m: number; label?: string }[];
}
interface ScreenPoint { x: number; y: number; z: number; onScreen?: boolean }
interface OverlayLine { node: SVGGElement; line: SVGLineElement; halo: SVGLineElement }

export function createScanTags(container: HTMLElement, camera: () => Camera | undefined) {
  const element = <K extends keyof SVGElementTagNameMap>(name: K) => document.createElementNS('http://www.w3.org/2000/svg', name);
  const svg = element('svg'); svg.classList.add('scan-tags'); svg.setAttribute('role', 'group');
  svg.setAttribute('aria-label', 'Estimated AprilTag locations, shown through surfaces');
  const title = element('title'); const lines = element('g'); const tagsGroup = element('g');
  const emphasisGroup = element('g'); emphasisGroup.setAttribute('aria-label', 'Active tag highlight');
  const faceGroup = element('g');
  const shapeGroup = element('g'); const vectorGroup = element('g');
  emphasisGroup.append(faceGroup, shapeGroup, vectorGroup);
  svg.append(title, lines, emphasisGroup, tagsGroup); container.append(svg);
  let visible = true; let interactive = false;
  let selectTag: ((id: number) => void) | undefined;
  let selection: number[] = []; let highlight: ScanHighlight | null = null; let highlightKey: string | null = null;
  let activeTags = new Set<number>();
  let edges: { a: number; b: number; stroke: OverlayLine }[] = [];
  let faces: { ids: number[]; node: SVGPolygonElement }[] = [];
  let vectors: { from: Vector3; to: Vector3; stroke: OverlayLine; dot: SVGCircleElement; label: SVGTextElement }[] = [];
  let records: DistanceMeasurement[] = []; let pending: MeasurementPreview | null = null;
  let referenceMatrix = new Matrix4();
  let markers: { id: number; node: SVGGElement; outline: SVGPolygonElement; outlineHalo: SVGPolygonElement;
    label: SVGTextElement; circle: SVGCircleElement; ring: SVGCircleElement; ringHalo: SVGCircleElement;
    centre: Vector3; corners: Vector3[]; point?: ScreenPoint }[] = [];
  let renderedLines: { from: number; to?: number; stroke: OverlayLine; label?: SVGTextElement }[] = [];
  const inDepth = (p: ScreenPoint | undefined): p is ScreenPoint => !!p && p.z >= -1 && p.z <= 1;
  const inView = (p: ScreenPoint | undefined): p is ScreenPoint => inDepth(p) && p.onScreen !== false;

  function createLine(emphasized: boolean, extraClass?: string): OverlayLine {
    const node = element('g'); const halo = element('line'); const line = element('line');
    node.classList.add(emphasized ? 'scan-emphasis-line' : 'scan-saved-line');
    if (extraClass) node.classList.add(extraClass);
    halo.classList.add('scan-line-halo'); line.classList.add('scan-line-stroke'); node.append(halo, line);
    return { node, line, halo };
  }
  function placeLine(stroke: OverlayLine, a?: ScreenPoint, b?: ScreenPoint, show = true) {
    const shown = show && inDepth(a) && inDepth(b); stroke.node.style.display = shown ? '' : 'none';
    if (!shown) return;
    for (const line of [stroke.halo, stroke.line]) {
      line.setAttribute('x1', String(a.x)); line.setAttribute('y1', String(a.y));
      line.setAttribute('x2', String(b.x)); line.setAttribute('y2', String(b.y));
    }
  }
  function rebuildEmphasis() {
    const editing = interactive && selection.length > 0;
    activeTags = new Set(editing ? selection : highlight?.tagIds ?? []);
    shapeGroup.replaceChildren(); vectorGroup.replaceChildren(); faceGroup.replaceChildren(); edges = []; vectors = []; faces = [];
    const ids = [...activeTags];
    // Pending tape geometry is drawn by drawLines, through the same line renderer.
    if (!editing) {
      const connections = highlight?.connections ?? ids.flatMap((a, i) => ids.slice(i + 1).map(b => ({ tag_a: a, tag_b: b })));
      const seen = new Set<string>();
      for (const pair of connections) {
        const key = [pair.tag_a, pair.tag_b].sort((a, b) => a - b).join(':'); if (seen.has(key)) continue; seen.add(key);
        const stroke = createLine(true); shapeGroup.append(stroke.node); edges.push({ a: pair.tag_a, b: pair.tag_b, stroke });
      }
      for (const triangle of highlight?.triangles ?? (ids.length === 3 && highlight?.connections === undefined ? [ids] : [])) {
        const node = element('polygon'); node.classList.add('scan-highlight-face'); faceGroup.append(node); faces.push({ ids: triangle, node });
      }
    }
    for (const vector of editing ? [] : highlight?.vectors ?? []) {
      const stroke = createLine(true); const dot = element('circle'); dot.classList.add('scan-emphasis-dot'); dot.setAttribute('r', '5');
      const label = element('text'); label.classList.add('scan-emphasis-label');
      label.textContent = vector.label ?? `Δ ${(vector.distance_m * 1000).toFixed(1)} mm`;
      vectorGroup.append(stroke.node, dot, label);
      vectors.push({ from: new Vector3(...vector.before as [number, number, number]).applyMatrix4(referenceMatrix),
        to: new Vector3(...vector.after as [number, number, number]).applyMatrix4(referenceMatrix), stroke, dot, label });
    }
    update();
  }
  function drawLines() {
    lines.replaceChildren(); renderedLines = [];
    for (const record of records) {
      if (!markers.some(m => m.id === record.tag_a) || !markers.some(m => m.id === record.tag_b)) continue;
      const stroke = createLine(false); const label = element('text'); label.classList.add('scan-measure-label');
      label.textContent = `${record.tag_a} ↔ ${record.tag_b}: ${(record.distance_m * 1000).toFixed(1)} mm`;
      lines.append(stroke.node, label); renderedLines.push({ from: record.tag_a, to: record.tag_b, stroke, label });
    }
    if (pending) {
      const stroke = createLine(true, pending.to === undefined ? 'is-pending' : 'is-editing');
      lines.append(stroke.node); renderedLines.push({ from: pending.from, to: pending.to, stroke });
    }
  }
  function update() {
    const shown = !!(visible || interactive || activeTags.size);
    svg.style.display = shown && markers.length ? '' : 'none'; if (!shown || !markers.length) return;
    const projection = camera(); const canvas = container.querySelector('canvas'); if (!projection || !canvas) return;
    if (!svg.isConnected) container.append(svg);
    const viewport = canvas.getBoundingClientRect(); const bounds = container.getBoundingClientRect();
    svg.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
    const project = (point: Vector3): ScreenPoint => {
      const p = point.clone().project(projection);
      return { x: viewport.left - bounds.left + (p.x + 1) * viewport.width / 2,
        y: viewport.top - bounds.top + (1 - p.y) * viewport.height / 2, z: p.z,
        onScreen: p.x >= -1 && p.x <= 1 && p.y >= -1 && p.y <= 1 };
    };
    for (const marker of markers) {
      const p = marker.point = project(marker.centre); const shown = inView(p); const emphasized = activeTags.has(marker.id);
      marker.node.style.display = shown ? '' : 'none';
      marker.node.setAttribute('tabindex', interactive && shown ? '0' : '-1'); marker.node.setAttribute('role', interactive ? 'button' : 'group');
      const label = `${emphasized ? '▶ ' : ''}Tag ${marker.id}`;
      if (marker.label.textContent !== label) marker.label.textContent = label;
      marker.node.setAttribute('aria-label', `${emphasized ? 'Highlighted, ' : ''}Tag ${marker.id}`);
      if (interactive) marker.node.setAttribute('aria-pressed', String(selection.includes(marker.id))); else marker.node.removeAttribute('aria-pressed');
      marker.node.classList.toggle('is-highlighted', emphasized);
      marker.label.setAttribute('x', String(p.x + 15)); marker.label.setAttribute('y', String(p.y - 14));
      for (const circle of [marker.circle, marker.ring, marker.ringHalo]) {
        circle.setAttribute('cx', String(p.x)); circle.setAttribute('cy', String(p.y));
      }
      const corners = marker.corners.map(corner => { const point = project(corner); return `${point.x},${point.y}`; }).join(' ');
      marker.outline.setAttribute('points', corners); marker.outlineHalo.setAttribute('points', corners);
    }
    for (const segment of renderedLines) {
      const a = markers.find(m => m.id === segment.from)?.point;
      const b = segment.to === undefined ? pending?.pointer ? { x: pending.pointer.x - bounds.left, y: pending.pointer.y - bounds.top, z: 0 } : undefined
        : markers.find(m => m.id === segment.to)?.point;
      placeLine(segment.stroke, a, b, interactive);
      if (segment.label) {
        const shown = interactive && inDepth(a) && inDepth(b); segment.label.style.display = shown ? '' : 'none';
        if (shown) { segment.label.setAttribute('x', String((a.x + b.x) / 2 + 6)); segment.label.setAttribute('y', String((a.y + b.y) / 2 - 8)); }
      }
    }
    for (const edge of edges) placeLine(edge.stroke, markers.find(m => m.id === edge.a)?.point, markers.find(m => m.id === edge.b)?.point);
    for (const face of faces) {
      const triangle = face.ids.map(id => markers.find(m => m.id === id)?.point);
      const shown = triangle.length === 3 && triangle.every(inDepth); face.node.style.display = shown ? '' : 'none';
      if (shown) face.node.setAttribute('points', triangle.map(point => `${point!.x},${point!.y}`).join(' '));
    }
    for (const vector of vectors) {
      const a = project(vector.from); const b = project(vector.to); const shown = inDepth(a) && inDepth(b);
      placeLine(vector.stroke, a, b);
      vector.dot.style.display = vector.label.style.display = shown ? '' : 'none';
      vector.dot.setAttribute('cx', String(b.x)); vector.dot.setAttribute('cy', String(b.y));
      vector.label.setAttribute('x', String(b.x + 12)); vector.label.setAttribute('y', String(b.y + 16));
    }
  }
  return {
    update,
    setHighlight(value: ScanHighlight | null): boolean {
      const key = value ? JSON.stringify({ tags: [...new Set(value.tagIds)].sort((a, b) => a - b),
        connections: value.connections, triangles: value.triangles,
        vectors: value.vectors?.map(vector => [vector.id, vector.before, vector.after, vector.distance_m, vector.label]) ?? [] }) : null;
      highlight = key !== null && key !== highlightKey ? value : null;
      highlightKey = highlight ? key : null; rebuildEmphasis(); return highlight !== null;
    },
    setVisible(value: boolean) { visible = value; update(); },
    setInteractive(value: boolean, onSelect?: (id: number) => void) {
      const changed = interactive !== value; interactive = value; selectTag = onSelect;
      if (changed) rebuildEmphasis(); else update();
    },
    setSelection(ids: number[]) {
      if (ids.length === selection.length && ids.every((id, i) => selection[i] === id)) return;
      selection = [...ids]; rebuildEmphasis();
    },
    setMeasurements(values: DistanceMeasurement[], preview: MeasurementPreview | null) {
      const rebuild = records !== values || pending?.from !== preview?.from || pending?.to !== preview?.to;
      records = values; pending = preview; if (rebuild) drawLines(); update();
    },
    pickTag(clientX: number, clientY: number): number | null {
      const bounds = container.getBoundingClientRect();
      const candidates = markers.filter(marker => {
        if (!inView(marker.point)) return false;
        if (Math.hypot(clientX - bounds.left - marker.point.x, clientY - bounds.top - marker.point.y) <= 12) return true;
        return [marker.outline, marker.label].some(node => { const rect = node.getBoundingClientRect();
          return clientX >= rect.left && clientX <= rect.right && clientY >= rect.top && clientY <= rect.bottom; });
      });
      candidates.sort((a, b) => Math.hypot(clientX - bounds.left - a.point!.x, clientY - bounds.top - a.point!.y)
        - Math.hypot(clientX - bounds.left - b.point!.x, clientY - bounds.top - b.point!.y));
      return candidates[0]?.id ?? null;
    },
    setTags(tags: ScanTag[], scanToReference?: number[][]) {
      referenceMatrix = scanToReference ? new Matrix4().fromArray(scanToReference.flat()).transpose() : new Matrix4();
      highlight = null; highlightKey = null; tagsGroup.replaceChildren();
      title.textContent = tags.length ? tags.map(tag => `Tag ${tag.id}: ${tag.observations} observed frames`).join('; ') : 'No saved tag poses';
      markers = tags.map(tag => {
        const pose = new Matrix4().copy(referenceMatrix).multiply(new Matrix4().fromArray(tag.pose.flat()).transpose());
        const centre = new Vector3().applyMatrix4(pose); const half = (tag.size_m ?? 0) / 2;
        const corners = [[-half, -half], [half, -half], [half, half], [-half, half]].map(([x, y]) => new Vector3(x, y, 0).applyMatrix4(pose));
        const node = element('g'); node.classList.add('scan-tag-marker');
        node.onkeydown = event => { if (interactive && (event.key === 'Enter' || event.key === ' ')) {
          event.preventDefault(); event.stopPropagation(); selectTag?.(tag.id); } };
        const outlineHalo = element('polygon'); outlineHalo.classList.add('scan-tag-outline-halo');
        const outline = element('polygon'); outline.classList.add('scan-tag-outline');
        const circle = element('circle'); circle.classList.add('scan-tag-centre'); circle.setAttribute('r', '4');
        const ringHalo = element('circle'); ringHalo.classList.add('scan-tag-ring-halo'); ringHalo.setAttribute('r', '12');
        const ring = element('circle'); ring.classList.add('scan-tag-ring'); ring.setAttribute('r', '12');
        const label = element('text');
        node.append(outlineHalo, outline, circle, ringHalo, ring, label); tagsGroup.append(node);
        return { id: tag.id, node, outline, outlineHalo, circle, ring, ringHalo, label, centre, corners };
      }); drawLines(); rebuildEmphasis();
    },
  };
}
