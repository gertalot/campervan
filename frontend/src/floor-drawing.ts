import { chevronAspect, defaultFloorPattern, floorPattern as pattern, floorPatternTile, floorPatternTransform,
  floorPieces, floorRoot, type FloorPatternSettings } from './floor-pattern';
import type { Group, Part, Point } from './cutting-types';
import './floor-drawing.css';

const { height: rise, stripe: band, brown, cream } = pattern;
const guideOffset = 500; // From the centre of the finished floor, in millimetres.
const mm = (value: number) => Number(value.toFixed(1));

function dimension(x1: number, y1: number, x2: number, y2: number, label: string, shift = -10) {
  const length = Math.hypot(x2 - x1, y2 - y1);
  const rotation = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
  return `<g class="dimension" transform="translate(${x1} ${y1}) rotate(${rotation})">
    <path d="M0 0H${length} M0 0l8 -3v6z M${length} 0l-8 -3v6z"/>
    <text x="${length / 2}" y="${shift}">${label}</text></g>`;
}

function repeatDrawing({ stripe, angle }: FloorPatternSettings) {
  const aspect = chevronAspect(angle);
  const pitch = pattern.width * aspect, run = pitch / 2;
  const legDegrees = (180 - angle) / 2, leg = legDegrees * Math.PI / 180;
  const size = (value: number) => String(mm(value * stripe / band));
  const span = rise + band;
  const angleRadius = 0.22 * Math.min(run, rise);
  const arcX = angleRadius * Math.cos(leg), arcY = angleRadius * Math.sin(leg);
  const x = run / 3, y = rise - x * rise / run;
  const perpendicular = band * Math.cos(leg);
  const nx = perpendicular * Math.sin(leg), ny = perpendicular * Math.cos(leg);
  return `<svg viewBox="-76 -99 ${pitch+144} ${span+140}" role="img" aria-label="One chevron repeat with tape dimensions in millimetres">
    <defs>${floorPatternTile('detail-tile', aspect)}</defs>
    <g transform="translate(0 ${span}) scale(1 -1)">
      <rect width="${pitch}" height="${span}" fill="url(#detail-tile)"/>
    </g>
    <g class="extension"><path d="M0 -76V-5 M${run} -42V0 M${pitch} -76V-5
      M-56 ${rise}H0 M-56 ${span}H0 M${run} 0H${pitch+42} M${pitch} ${rise}h42"/></g>
    ${dimension(0, -69, pitch, -69, size(pitch))}
    ${dimension(0, -32, run, -32, size(run))}
    ${dimension(pitch+34, 0, pitch+34, rise, size(rise))}
    ${dimension(-39, rise, -39, span, size(band))}
    ${dimension(x, y, x+nx, y+ny, size(perpendicular))}
    <g class="angle-mark">
      <path d="M0 ${rise}h${angleRadius+18} M${angleRadius} ${rise}a${angleRadius} ${angleRadius} 0 0 0 ${arcX-angleRadius} ${-arcY}"/>
      <text x="${angleRadius+18}" y="${rise-16}">${legDegrees}°</text>
      <path d="M${run-arcX} ${arcY}a${angleRadius} ${angleRadius} 0 0 0 ${2*arcX} 0"/>
      <text x="${run}" y="${angleRadius+22}">${angle}°</text>
    </g>
  </svg>`;
}

function planDrawing(bench: Part, aisle: Part) {
  const width = bench.width + aisle.width, length = bench.length;
  // The cut list stores [length along the van, width across the sheet] in millimetres.
  function outline(points: Point[], offset: number) {
    return 'M' + points.map(([y, x]) => `${offset+x},${y}`).join('L') + 'Z';
  }
  const floor = outline(bench.outline, 0) + outline(aisle.outline, bench.width);
  const hatch = aisle.holes.map(hole => outline(hole, bench.width)).join(' ');
  return `<svg viewBox="-32 -76 ${width + 64} ${length + 152}" role="img"
    aria-label="Cut floor with the cab at the top. Four teal guides show the marks for both tape directions.">
    <defs>${floorPatternTile('floor-tile')}<path id="floor-shape" d="${floor}"/>
      <clipPath id="floor-clip"><use href="#floor-shape"/></clipPath></defs>
    <g transform="translate(0 ${length}) scale(1 -1)">
      <use href="#floor-shape" fill="url(#floor-tile)" class="floor-cut"/>
      <path d="${hatch}" fill="none" class="floor-cut"/>
      <g clip-path="url(#floor-clip)"><g class="floor-guides"></g></g>
    </g>
    <g class="plan-label"><text x="${width/2}" y="-18">CAB</text>
      <text x="${width/2}" y="${length + 58}">REAR</text></g>
  </svg>`;
}

function line(x: number, y: number, endX: number, endY: number) {
  return `M${x},${y}L${endX},${endY}`;
}

function markingGuides(matrix: DOMMatrix, width: number, length: number) {
  const cx = width / 2, cy = length / 2;
  // Select a brown peak near the centre. Its two boundaries are one artwork unit apart.
  const centre = matrix.inverse().transformPoint({ x: cx, y: cy });
  const halfRepeat = pattern.width / (2 * band), row = rise / band;
  const peakX = (2 * Math.round((centre.x / halfRepeat - 1) / 2) + 1) * halfRepeat;
  const peakY = row * Math.round((centre.y - 0.5) / row);
  const peak = matrix.transformPoint({ x: peakX, y: peakY });
  const other = matrix.transformPoint({ x: peakX, y: peakY + 1 });
  let datums = '', ticks = '', extensions = '', tape = '', crossings = '', rows = '';
  const pitches = { longitudinal: 0, transverse: 0 };

  // Choose the pairing with the larger minimum crossing angle across both legs.
  const risingAcross = Math.min(Math.abs(matrix.a + matrix.c), Math.abs(matrix.b - matrix.d))
    >= Math.min(Math.abs(matrix.a - matrix.c), Math.abs(matrix.b + matrix.d));
  for (const sign of [1, -1]) {
    const dx = matrix.a + sign * matrix.c, dy = matrix.b + sign * matrix.d;
    const longitudinal = sign === 1 ? risingAcross : !risingAcross;
    const slope = longitudinal ? dy / dx : dx / dy;
    const atGuide = (fixed: number, point: DOMPoint) => longitudinal
      ? point.y + (fixed - point.x) * slope
      : point.x + (fixed - point.y) * slope;
    const fixedCentre = longitudinal ? cx : cy;
    const alongCentre = longitudinal ? cy : cx;
    const extent = longitudinal ? length : width;
    const guideLine = (fixed: number, along: number, endFixed: number, endAlong: number) => longitudinal
      ? line(fixed, along, endFixed, endAlong) : line(along, fixed, endAlong, endFixed);
    const far = longitudinal ? width : length;
    for (const edge of [peak, other]) {
      extensions += guideLine(0, atGuide(0, edge), far, atGuide(far, edge));
      tape += line(edge.x, edge.y, edge.x - sign * dx * halfRepeat, edge.y - sign * dy * halfRepeat);
    }
    const spacing = Math.abs(atGuide(fixedCentre, other) - atGuide(fixedCentre, peak));
    pitches[longitudinal ? 'longitudinal' : 'transverse'] = spacing;
    for (const offset of [-guideOffset, guideOffset]) {
      const fixed = fixedCentre + offset;
      datums += guideLine(fixed, 0, fixed, extent);
      const first = atGuide(fixed, peak), second = atGuide(fixed, other);
      for (let i = Math.ceil(-first / spacing); first + i * spacing <= extent; i++) {
        const along = first + i * spacing;
        ticks += guideLine(fixed - 9, along, fixed + 9, along);
      }
      for (const along of [first, second]) {
        crossings += `<circle cx="${longitudinal ? fixed : along}" cy="${longitudinal ? along : fixed}" r="8"/>`;
      }
      const name = longitudinal ? (offset < 0 ? 'Left' : 'Right') : (offset < 0 ? 'Rear' : 'Cab');
      const start = alongCentre - guideOffset;
      rows += `<tr><th scope="row">${name}</th><td>${mm(first - start)}</td><td>${mm(second - start)}</td></tr>`;
    }
  }
  return { pitches, rows, svg: `<path class="guide-extensions" d="${extensions}"/>
    <path class="guide-datums" d="${datums}${ticks}"/><path class="guide-tape" d="${tape}"/>${crossings}` };
}

export function setupFloorDrawing(panel: HTMLElement) {
  panel.innerHTML = `<article class="floor-sheet">
    <h2>Floor pattern</h2>
    <div class="floor-figures">
      <figure><h3>Cut floor</h3><div id="drawing-floor-rotation"></div><div id="drawing-floor-stripe"></div>
        <div id="drawing-floor-angle"></div>
        <div data-floor-plan><p>Loading floor outlines…</p></div>
        <figcaption data-guide-spacing></figcaption></figure>
      <div><figure><h3>One repeat <small>mm · pattern axes</small></h3><div data-repeat></div>
        <figcaption data-stripe-size></figcaption></figure>
        <section data-marking hidden><h3>Place the masking tape</h3>
          <p>Draw each guide 500 mm from the floor centre. The guides in each pair are 1,000 mm apart.</p>
          <p>Use the table to mark the two edges of the brown stripe. The circles show these marks.</p>
          <table><caption>Distance along each guide (mm)</caption>
            <thead><tr><th scope="col">Guide</th><th scope="col">Edge 1</th><th scope="col">Edge 2</th></tr></thead>
            <tbody></tbody></table>
          <p>On the left and right guides, measure from the rear guide towards the cab.
            On the rear and cab guides, measure from the left guide towards the right. For a negative value, measure back.</p>
          <p>Join matching edge numbers on each pair of guides. The thin magenta lines extend the tape edges.
            Follow the thick magenta lines to each turn. Place tape on the cream side.</p></section>
        <p class="floor-colours"><span style="--paint:${cream}">Warm cream · ${cream}</span>
          <span style="--paint:${brown}">Dark brown · ${brown}</span></p>
      </div>
    </div>
  </article>`;
  let width = 0, length = 0, settings = defaultFloorPattern;
  const plan = panel.querySelector<HTMLElement>('[data-floor-plan]')!;
  const spacingNote = panel.querySelector<HTMLElement>('[data-guide-spacing]')!;
  const marking = panel.querySelector<HTMLElement>('[data-marking]')!;
  function setPattern(value: FloorPatternSettings) {
    settings = value;
    panel.querySelector('[data-repeat]')!.innerHTML = repeatDrawing(settings);
    panel.querySelector('[data-stripe-size]')!.textContent =
      `Each stripe measures ${settings.stripe} mm along the pattern axis and ${mm(settings.stripe * Math.sin(settings.angle * Math.PI / 360))} mm square across its edges.`;
    const tile = plan.querySelector('#floor-tile');
    if (!tile) return;
    const matrix = floorPatternTransform(settings, width, length);
    tile.setAttribute('patternTransform', matrix.toString());
    const guides = markingGuides(matrix, width, length);
    plan.querySelector('.floor-guides')!.innerHTML = guides.svg;
    panel.querySelector('tbody')!.innerHTML = guides.rows;
    const along = mm(guides.pitches.longitudinal), across = mm(guides.pitches.transverse);
    spacingNote.innerHTML = (along === across ? `Mark every <strong>${along} mm</strong> on all four guides.`
      : `Fore–aft guides: mark every <strong>${along} mm</strong>. Transverse guides: mark every <strong>${across} mm</strong>.`)
      + ' Two intervals reach the same edge of the next brown stripe.';
  }
  function setGroups(groups: Group[]) {
    const parts = groups.flatMap(group => group.parts);
    const find = (name: string) => parts.find(part => part.path === floorRoot + ' / ' + name);
    const bench = find(floorPieces.bench), aisle = find(floorPieces.aisle);
    marking.hidden = !bench || !aisle;
    if (!bench || !aisle) {
      plan.textContent = 'Floor outlines are unavailable in this cut list.';
      spacingNote.textContent = '';
      return;
    }
    width = bench.width + aisle.width;
    length = bench.length;
    plan.innerHTML = planDrawing(bench, aisle);
    setPattern(settings);
  }
  return { setGroups, setPattern };
}
