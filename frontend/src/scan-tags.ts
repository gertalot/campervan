/** Saved landmarks and measurements projected through the existing native camera. */
import { Matrix4, Vector3, type Camera } from 'three';
import type { DistanceMeasurement } from './scan-measurements-api';

export interface ScanTag { id: number; pose: number[][]; size_m: number | null; observations: number }
export interface MeasurementPreview { from: number; to?: number; pointer?: { x: number; y: number } }
interface ScreenPoint { x: number; y: number; z: number; onScreen?: boolean }

export function createScanTags(container: HTMLElement, camera: () => Camera | undefined) {
  const element = <K extends keyof SVGElementTagNameMap>(name: K) =>
    document.createElementNS('http://www.w3.org/2000/svg', name);
  const svg = element('svg');
  svg.classList.add('scan-tags');
  svg.setAttribute('role', 'group');
  svg.setAttribute('aria-label', 'Estimated AprilTag locations, shown through surfaces');
  const title = element('title');
  const lines = element('g');
  const tagsGroup = element('g');
  const analysisGroup = element('g'); const suggestionGroup = element('g');
  svg.append(title, lines, tagsGroup, analysisGroup, suggestionGroup);
  container.append(svg);
  let visible = true;
  let interactive = false;
  let selectTag: ((id: number) => void) | undefined;
  let selection: number[] = [];
  let records: DistanceMeasurement[] = [];
  let pending: MeasurementPreview | null = null;
  let referenceMatrix = new Matrix4();
  let analysis: { id: number; from: Vector3; to: Vector3; line: SVGLineElement; dot: SVGCircleElement; label: SVGTextElement }[] = [];
  let suggested: { from: number; to: number; hit?: number[] } | null = null;
  let markers: { id: number; node: SVGGElement; outline: SVGPolygonElement; label: SVGTextElement;
    circle: SVGCircleElement; centre: Vector3; corners: Vector3[]; point?: ScreenPoint }[] = [];
  let renderedLines: { from: number; to?: number; line: SVGLineElement; label?: SVGTextElement }[] = [];
  const inDepth = (p: ScreenPoint | undefined): p is ScreenPoint => !!p && p.z >= -1 && p.z <= 1;
  const inView = (p: ScreenPoint | undefined): p is ScreenPoint => inDepth(p) && p.onScreen !== false;

  function drawLines() {
    lines.replaceChildren(); renderedLines = [];
    for (const record of records) {
      if (!markers.some(m => m.id === record.tag_a) || !markers.some(m => m.id === record.tag_b)) continue;
      const line = element('line'); line.classList.add('scan-measure-line', 'is-saved');
      const label = element('text'); label.classList.add('scan-measure-label');
      label.textContent = `${record.tag_a} ↔ ${record.tag_b}: ${(record.distance_m * 1000).toFixed(1)} mm`;
      lines.append(line, label);
      renderedLines.push({ from: record.tag_a, to: record.tag_b, line, label });
    }
    if (pending) {
      const line = element('line');
      line.classList.add('scan-measure-line', pending.to === undefined ? 'is-pending' : 'is-editing');
      lines.append(line); renderedLines.push({ from: pending.from, to: pending.to, line });
    }
  }

  function update() {
    svg.style.display = (visible || interactive || analysis.length || suggested) && markers.length ? '' : 'none';
    if ((!visible && !interactive && !analysis.length && !suggested) || !markers.length) return;
    const projection = camera(); const canvas = container.querySelector('canvas');
    if (!projection || !canvas) return;
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
      const p = marker.point = project(marker.centre); const shown = inView(p);
      marker.node.style.display = shown ? '' : 'none';
      marker.node.setAttribute('tabindex', interactive && shown ? '0' : '-1');
      marker.node.setAttribute('role', interactive ? 'button' : 'group');
      if (interactive) marker.node.setAttribute('aria-pressed', String(selection.includes(marker.id)));
      else marker.node.removeAttribute('aria-pressed');
      marker.node.classList.toggle('is-selected', selection.includes(marker.id));
      marker.node.classList.toggle('is-measured', interactive && records.some(r => r.tag_a === marker.id || r.tag_b === marker.id));
      marker.label.setAttribute('x', String(p.x + 9)); marker.label.setAttribute('y', String(p.y - 9));
      marker.circle.setAttribute('cx', String(p.x)); marker.circle.setAttribute('cy', String(p.y));
      marker.outline.setAttribute('points', marker.corners.map(corner => {
        const point = project(corner); return `${point.x},${point.y}`;
      }).join(' '));
    }
    for (const segment of renderedLines) {
      const a = markers.find(m => m.id === segment.from)?.point;
      const b = segment.to === undefined
        ? pending?.pointer ? { x: pending.pointer.x - bounds.left, y: pending.pointer.y - bounds.top, z: 0 } : undefined
        : markers.find(m => m.id === segment.to)?.point;
      const shown = interactive && inDepth(a) && inDepth(b);
      segment.line.style.display = shown ? '' : 'none';
      if (segment.label) segment.label.style.display = shown ? '' : 'none';
      if (!shown) continue;
      segment.line.setAttribute('x1', String(a.x)); segment.line.setAttribute('y1', String(a.y));
      segment.line.setAttribute('x2', String(b.x)); segment.line.setAttribute('y2', String(b.y));
      segment.label?.setAttribute('x', String((a.x + b.x) / 2 + 6));
      segment.label?.setAttribute('y', String((a.y + b.y) / 2 - 8));
    }
    for (const segment of analysis) {
      const a = project(segment.from); const b = project(segment.to);
      const shown = inDepth(a) && inDepth(b);
      for (const node of [segment.line, segment.dot, segment.label]) node.style.display = shown ? '' : 'none';
      segment.line.setAttribute('x1', String(a.x)); segment.line.setAttribute('y1', String(a.y));
      segment.line.setAttribute('x2', String(b.x)); segment.line.setAttribute('y2', String(b.y));
      segment.dot.setAttribute('cx', String(b.x)); segment.dot.setAttribute('cy', String(b.y));
      segment.label.setAttribute('x', String(b.x+9)); segment.label.setAttribute('y', String(b.y+14));
    }
    suggestionGroup.replaceChildren();
    if (suggested) {
      const position = (id: number) => analysis.find(row => row.id === id)?.to ?? markers.find(row => row.id === id)?.centre;
      const from = position(suggested.from); const to = position(suggested.to);
      if (from && to) {
        const a = project(from); const b = project(to);
        if (inDepth(a) && inDepth(b)) {
          const line = element('line'); line.classList.add('scan-suggest-line');
          for (const [name, value] of Object.entries({ x1: a.x, y1: a.y, x2: b.x, y2: b.y })) line.setAttribute(name, String(value));
          suggestionGroup.append(line);
          if (suggested.hit) {
            const hit = project(new Vector3(...suggested.hit as [number, number, number]).applyMatrix4(referenceMatrix));
            const dot = element('circle'); dot.classList.add('scan-obstruction'); dot.setAttribute('r', '6');
            dot.setAttribute('cx', String(hit.x)); dot.setAttribute('cy', String(hit.y)); suggestionGroup.append(dot);
          }
        }
      }
    }
  }

  return {
    update,
    setAnalysis(movements: { id: number; before: number[]; after: number[]; distance_m: number }[]) {
      analysisGroup.replaceChildren();
      analysis = movements.map(movement => {
        const line = element('line'); line.classList.add('scan-analysis-line');
        const dot = element('circle'); dot.classList.add('scan-analysis-dot'); dot.setAttribute('r', '4');
        const label = element('text'); label.classList.add('scan-analysis-label');
        label.textContent = `Δ ${(movement.distance_m*1000).toFixed(1)} mm`;
        analysisGroup.append(line, dot, label);
        return { id: movement.id, from: new Vector3(...movement.before as [number, number, number]).applyMatrix4(referenceMatrix),
          to: new Vector3(...movement.after as [number, number, number]).applyMatrix4(referenceMatrix), line, dot, label };
      }); update();
    },
    setSuggestedPair(value: { from: number; to: number; hit?: number[] } | null) { suggested = value; update(); },
    setVisible(value: boolean) { visible = value; update(); },
    setInteractive(value: boolean, onSelect?: (id: number) => void) {
      interactive = value; selectTag = onSelect; update();
    },
    setSelection(ids: number[]) { selection = ids; update(); },
    setMeasurements(values: DistanceMeasurement[], preview: MeasurementPreview | null) {
      const rebuild = records !== values || pending?.from !== preview?.from || pending?.to !== preview?.to;
      records = values; pending = preview;
      if (rebuild) drawLines(); update();
    },
    pickTag(clientX: number, clientY: number): number | null {
      const bounds = container.getBoundingClientRect();
      const candidates = markers.filter(marker => {
        if (!inView(marker.point)) return false;
        if (Math.hypot(clientX - bounds.left - marker.point.x, clientY - bounds.top - marker.point.y) <= 12) return true;
        return [marker.outline, marker.label].some(node => {
          const rect = node.getBoundingClientRect();
          return clientX >= rect.left && clientX <= rect.right && clientY >= rect.top && clientY <= rect.bottom;
        });
      });
      candidates.sort((a, b) => Math.hypot(clientX - bounds.left - a.point!.x, clientY - bounds.top - a.point!.y)
        - Math.hypot(clientX - bounds.left - b.point!.x, clientY - bounds.top - b.point!.y));
      return candidates[0]?.id ?? null;
    },
    setTags(tags: ScanTag[], scanToReference?: number[][]) {
      referenceMatrix = scanToReference ? new Matrix4().fromArray(scanToReference.flat()).transpose() : new Matrix4();
      analysis = []; analysisGroup.replaceChildren(); suggested = null;
      tagsGroup.replaceChildren();
      title.textContent = tags.length
        ? tags.map(tag => `Tag ${tag.id}: ${tag.observations} observed frames`).join('; ') : 'No saved tag poses';
      markers = tags.map(tag => {
        const pose = scanToReference ? new Matrix4().fromArray(scanToReference.flat()).transpose() : new Matrix4();
        pose.multiply(new Matrix4().fromArray(tag.pose.flat()).transpose());
        const centre = new Vector3().applyMatrix4(pose); const half = (tag.size_m ?? 0) / 2;
        const corners = [[-half, -half], [half, -half], [half, half], [-half, half]]
          .map(([x, y]) => new Vector3(x, y, 0).applyMatrix4(pose));
        const node = element('g'); node.setAttribute('aria-label', `Tag ${tag.id}, ${tag.observations} observed frames`);
        node.onkeydown = event => {
          if (interactive && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault(); event.stopPropagation(); selectTag?.(tag.id);
          }
        };
        const outline = element('polygon'); const circle = element('circle'); circle.setAttribute('r', '4');
        const label = element('text'); label.textContent = `Tag ${tag.id}`;
        node.append(outline, circle, label); tagsGroup.append(node);
        return { id: tag.id, node, outline, label, circle, centre, corners };
      });
      drawLines(); update();
    },
  };
}
