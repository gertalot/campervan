/** A clickable orientation cube; projection uses the CAD camera's quaternion. */
type Point = [number, number, number];
const faces: { name: string; normal: Point; u: Point; v: Point }[] = [
  { name: 'RIGHT', normal: [1, 0, 0], u: [0, 1, 0], v: [0, 0, 1] },
  { name: 'LEFT', normal: [-1, 0, 0], u: [0, -1, 0], v: [0, 0, 1] },
  { name: 'FRONT', normal: [0, 1, 0], u: [-1, 0, 0], v: [0, 0, 1] },
  { name: 'REAR', normal: [0, -1, 0], u: [1, 0, 0], v: [0, 0, 1] },
  { name: 'TOP', normal: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0] },
  { name: 'BOTTOM', normal: [0, 0, -1], u: [1, 0, 0], v: [0, -1, 0] },
];
const dot = (a: Point, b: Point) => a.reduce((sum, n, i) => sum + n * b[i], 0);
const viewName = (direction: Point) => faces.filter(face => dot(face.normal, direction) > 0)
  .map(face => face.name.toLowerCase()).join(' ') + ' view';

function svgElement<K extends keyof SVGElementTagNameMap>(name: K) {
  return document.createElementNS('http://www.w3.org/2000/svg', name);
}

export function createViewCube(
  container: HTMLElement, select: (direction: Point) => void, orbit: (dx: number, dy: number) => void,
) {
  const svg = svgElement('svg');
  svg.classList.add('view-cube');
  svg.setAttribute('viewBox', '0 0 112 112');
  svg.setAttribute('role', 'group');
  svg.setAttribute('aria-label', 'View cube: select a face, edge or corner; drag to orbit');
  svg.style.display = 'none';
  container.append(svg);
  let dragged = false;
  let pointer: { id: number; x: number; y: number; startX: number; startY: number } | null = null;
  svg.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    event.stopPropagation();
    dragged = false;
    pointer = { id: event.pointerId, x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY };
  });
  svg.addEventListener('pointermove', event => {
    if (!pointer || pointer.id !== event.pointerId) return;
    if (!dragged && Math.hypot(event.clientX - pointer.startX, event.clientY - pointer.startY) < 4) return;
    dragged = true;
    svg.setPointerCapture(event.pointerId);
    orbit(event.clientX - pointer.x, event.clientY - pointer.y);
    pointer.x = event.clientX;
    pointer.y = event.clientY;
    event.preventDefault();
  });
  svg.addEventListener('pointerup', () => { pointer = null; });
  svg.addEventListener('pointercancel', () => { pointer = null; dragged = true; });
  svg.addEventListener('pointerleave', () => { if (!dragged) pointer = null; });

  const segments = [-1, -0.55, 0.55, 1];
  const targets = new Map<string, SVGPolygonElement[]>();
  const nodes = faces.map(face => {
    const group = svgElement('g');
    const outline = svgElement('polygon');
    outline.classList.add('view-cube-face');
    group.append(outline);
    const point = (u: number, v: number): Point => face.normal.map((n, i) => n + u * face.u[i] + v * face.v[i]) as Point;
    const tiles = [];
    for (let row = 0; row < 3; row++) {
      for (let col = 0; col < 3; col++) {
        const direction = point(col - 1, row - 1);
        const tile = svgElement('polygon');
        const title = svgElement('title');
        title.textContent = viewName(direction);
        tile.append(title);
        tile.classList.add('view-cube-target');
        if (row !== 1 && col !== 1) tile.classList.add('view-cube-corner');
        const key = direction.join(',');
        targets.set(key, [...(targets.get(key) ?? []), tile]);
        const highlight = (active: boolean) => targets.get(key)?.forEach(target =>
          target.classList.toggle('is-highlighted', active));
        tile.addEventListener('pointerenter', () => highlight(true));
        tile.addEventListener('pointerleave', () => highlight(false));
        tile.addEventListener('focus', () => highlight(true));
        tile.addEventListener('blur', () => highlight(false));
        tile.setAttribute('role', 'button');
        tile.setAttribute('tabindex', '0');
        tile.setAttribute('aria-label', title.textContent);
        tile.addEventListener('click', event => {
          event.stopPropagation();
          if (!dragged) select(direction);
        });
        tile.addEventListener('keydown', event => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            select(direction);
          }
        });
        group.append(tile);
        tiles.push({ tile, points: [point(segments[col], segments[row]), point(segments[col + 1], segments[row]),
          point(segments[col + 1], segments[row + 1]), point(segments[col], segments[row + 1])] });
      }
    }
    const label = svgElement('text');
    label.textContent = face.name;
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('dominant-baseline', 'central');
    group.append(label);
    svg.append(group);
    return { face, group, outline, label, tiles, corners: [point(-1, -1), point(1, -1), point(1, 1), point(-1, 1)] };
  });
  let previous: number[] = [];
  return {
    update(quaternion: number[]) {
      if (quaternion.every((value, i) => value === previous[i])) return;
      previous = [...quaternion];
      svg.style.display = '';
      const [x, y, z, w] = quaternion;
      // World-space camera right, up and backward axes (columns of its rotation matrix).
      const right: Point = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)];
      const up: Point = [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)];
      const back: Point = [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)];
      const project = (point: Point) => `${56 + 28 * dot(point, right)},${56 - 28 * dot(point, up)}`;
      for (const { face, group, outline, label, tiles, corners } of nodes) {
        const facing = dot(face.normal, back);
        group.style.display = facing > 0.001 ? '' : 'none';
        if (facing <= 0.001) continue;
        outline.setAttribute('points', corners.map(project).join(' '));
        outline.style.fill = `hsl(215 12% ${28 + facing * 14}%)`;
        const [cx, cy] = project(face.normal).split(',');
        label.setAttribute('x', cx);
        label.setAttribute('y', cy);
        label.style.display = facing > 0.25 ? '' : 'none';
        for (const { tile, points } of tiles) tile.setAttribute('points', points.map(project).join(' '));
      }
    },
  };
}
