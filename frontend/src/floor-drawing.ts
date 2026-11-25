import { floorPattern as pattern, floorPatternTile, floorPieces, floorRoot, floorRotation } from './floor-pattern';
import type { Group, Part, Point } from './cutting-types';
import './floor-drawing.css';

const { width: pitch, height: rise, stripe: band, brown, cream } = pattern;
const run = pitch / 2;
const margin = 50; // Extra plywood beyond each finished edge, in millimetres.
const angle = Math.atan2(rise, run);
const degrees = Math.round(angle * 180 / Math.PI);
const normalWidth = (band * Math.cos(angle)).toFixed(1);

function dimension(x1: number, y1: number, x2: number, y2: number, label: string, shift = -10) {
  const length = Math.hypot(x2 - x1, y2 - y1);
  const rotation = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
  return `<g class="dimension" transform="translate(${x1} ${y1}) rotate(${rotation})">
    <path d="M0 0H${length} M0 0l8 -3v6z M${length} 0l-8 -3v6z"/>
    <text x="${length / 2}" y="${shift}">${label}</text></g>`;
}

function repeatDrawing() {
  const span = rise + band;
  const square = 0.10 * run;
  const angleRadius = 0.22 * run;
  const diagonal = angleRadius / Math.sqrt(2);
  const x = run / 3, y = rise - x;
  const nx = band * Math.sin(angle) * Math.cos(angle), ny = band * Math.cos(angle) ** 2;
  return `<svg viewBox="-76 -99 ${pitch+144} ${span+140}" role="img" aria-label="One chevron repeat with tape dimensions in millimetres">
    <defs>${floorPatternTile('detail-tile')}</defs>
    <g transform="translate(0 ${span}) scale(1 -1)">
      <rect width="${pitch}" height="${span}" fill="url(#detail-tile)"/>
    </g>
    <g class="extension"><path d="M0 -76V-5 M${run} -42V0 M${pitch} -76V-5
      M-56 ${rise}H0 M-56 ${span}H0 M${run} 0H${pitch+42} M${pitch} ${rise}h42"/></g>
    ${dimension(0, -69, pitch, -69, String(pitch))}
    ${dimension(0, -32, run, -32, String(run))}
    ${dimension(pitch+34, 0, pitch+34, rise, String(rise))}
    ${dimension(-39, rise, -39, span, String(band))}
    ${dimension(x, y, x+nx, y+ny, normalWidth)}
    <g class="angle-mark">
      <path d="M0 ${rise}h${angleRadius+18} M${angleRadius} ${rise}a${angleRadius} ${angleRadius} 0 0 0 ${diagonal-angleRadius} ${-diagonal}"/>
      <text x="${angleRadius+18}" y="${rise-16}">${degrees}°</text>
      <path d="M${run-square} ${square}l${square} ${square}l${square} ${-square}"/>
      <text x="${run}" y="${square*2+24}">${180-2*degrees}°</text>
    </g>
  </svg>`;
}

function planDrawing(bench: Part, aisle: Part) {
  const width = bench.width + aisle.width, length = bench.length;
  // The cut list stores [length along the van, width across the sheet] in millimetres.
  function outline(points: Point[], offset: number) {
    return 'M' + points.map(([y, x]) => `${offset+x},${y}`).join('L') + 'Z';
  }
  const cuts = [outline(bench.outline, 0), outline(aisle.outline, bench.width),
    ...aisle.holes.map(hole => outline(hole, bench.width))].join(' ');
  return `<svg viewBox="-175 -150 ${width+350} ${length+340}" role="img"
    aria-label="Rectangular plywood blank with the finished floor outline, sheet joint and fuel-pump hatch. Cab at the top.">
    <defs>${floorPatternTile('floor-tile')}<path id="floor-cuts" d="${cuts}"/></defs>
    <g transform="translate(0 ${length}) scale(1 -1)">
      <rect x="${-margin}" y="${-margin}" width="${width+2*margin}" height="${length+2*margin}"
        fill="url(#floor-tile)" stroke="#463d37" stroke-width="4"/>
      <g fill="none" stroke-linejoin="round">
        <use href="#floor-cuts" stroke="white" stroke-width="10"/>
        <use href="#floor-cuts" stroke="#075368" stroke-width="5"/>
      </g>
    </g>
    <g class="tape-points"></g>
    <g class="plan-label"><text x="${width/2}" y="-75">CAB</text>
      <text x="${width/2}" y="${length+125}">REAR</text></g>
  </svg>`;
}

export function setupFloorDrawing(panel: HTMLElement) {
  panel.innerHTML = `<article class="floor-sheet">
    <h2>Floor pattern</h2>
    <div class="floor-figures">
      <figure><h3>Plywood before cutting</h3><div id="drawing-floor-rotation"></div>
        <div data-floor-plan><p>Loading floor outlines…</p></div>
        <figcaption data-floor-size></figcaption></figure>
      <div><figure><h3>One repeat <small>mm · pattern axes</small></h3>${repeatDrawing()}
        <figcaption>Each tape edge lies at ${degrees}° to the pattern axis. Each point turns ${180-2*degrees}°.
        Each stripe measures ${band} mm along the pattern axis and ${normalWidth} mm perpendicular to its edge.</figcaption></figure>
        <h3>Mark one brown stripe</h3>
        <p>Stand at the rear and face the cab. Measure from the left and rear edges of the rectangular blank.</p>
        <table><caption>Distances from the blank edges (mm)</caption>
          <thead><tr><th scope="col">Point</th><th scope="col">From left</th><th scope="col">From rear</th></tr></thead>
          <tbody></tbody></table>
        <p>Join A–B–C for one edge. Join D–E–F for the other. Place the tape on the cream side.</p>
        <p data-repeat></p>
        <p class="floor-colours"><span style="--paint:${cream}">Warm cream · ${cream}</span>
          <span style="--paint:${brown}">Dark brown · ${brown}</span></p>
      </div>
    </div>
  </article>`;
  let width = 0, length = 0, rotation = 0;
  const plan = panel.querySelector<HTMLElement>('[data-floor-plan]')!;
  const repeatNote = panel.querySelector<HTMLElement>('[data-repeat]')!;
  const table = panel.querySelector('tbody')!;
  function setRotation(value: number) {
    rotation = value;
    const tile = plan.querySelector('#floor-tile');
    if (!tile) return;
    const matrix = floorRotation(rotation, width, length);
    tile.setAttribute('patternTransform', `${matrix} scale(${pattern.stripe})`);
    // Keep one whole repeat near the centre so all six marks remain on the blank.
    const startX = Math.round((width / 2 - run) / pitch) * pitch;
    const startY = Math.round((length / 2 - (rise + band) / 2) / rise) * rise;
    const mm = (n: number) => Number(n.toFixed(1));
    const points = Array.from('ABCDEF', (label, i) => {
      const column = i % 3;
      const x = startX + column * run;
      const y = startY + (column === 1 ? rise : 0) + (i >= 3 ? band : 0);
      return { label, point: matrix.transformPoint({ x, y }) };
    });
    plan.querySelector('.tape-points')!.innerHTML = points.map(({ label, point }) =>
      `<g transform="translate(${point.x} ${length - point.y})">
        <circle r="7"/><text x="17" y="-12">${label}</text></g>`).join('');
    table.innerHTML = points.map(({ label, point }) =>
      `<tr><th scope="row">${label}</th><td>${mm(point.x + margin)}</td><td>${mm(point.y + margin)}</td></tr>`).join('');
    function shift(x: number, y: number) {
      const dx = mm(x), dy = mm(y);
      return [dx && `${Math.abs(dx)} mm ${dx > 0 ? 'right' : 'left'}`,
        dy && `${Math.abs(dy)} mm towards the ${dy > 0 ? 'cab' : 'rear'}`].filter(Boolean).join(' and ');
    }
    repeatNote.textContent = `To extend this stripe, shift all six marks ${shift(matrix.a * pitch, matrix.b * pitch)}.
      For the next stripe, shift them ${shift(matrix.c * rise, matrix.d * rise)}.
      Reverse these directions to reach the opposite edges of the blank.`;
  }
  function setGroups(groups: Group[]) {
    const parts = groups.flatMap(group => group.parts);
    const find = (name: string) => parts.find(part => part.path === floorRoot + ' / ' + name.replaceAll('/', ' / '));
    const bench = find(floorPieces.bench), aisle = find(floorPieces.aisle);
    if (!bench || !aisle) {
      plan.textContent = 'Floor outlines are unavailable in this cut list.';
      panel.querySelector('[data-floor-size]')!.textContent = '';
      table.replaceChildren();
      repeatNote.textContent = '';
      return;
    }
    width = bench.width + aisle.width;
    length = bench.length;
    plan.innerHTML = planDrawing(bench, aisle);
    panel.querySelector('[data-floor-size]')!.textContent =
      `Blank: ${width + 2*margin} mm wide × ${bench.length + 2*margin} mm long. Allow ${margin} mm on each edge.
      The blue lines show the finished floor, the sheet joint and the hatch.`;
    setRotation(rotation);
  }
  return { setGroups, setRotation };
}
