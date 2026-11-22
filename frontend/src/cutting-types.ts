export type Mode = 'straight' | 'nesting';
export type Grain = 'length' | 'width' | 'free';
export type Point = [number, number];
export type FittingEdge = 'left' | 'right' | 'top' | 'bottom';
export type FittingMargins = Record<FittingEdge, number>;
export const fittingEdges: FittingEdge[] = ['left', 'right', 'top', 'bottom'];
export interface Stock { name: string; length: number; width: number; copies: number; offcut: boolean }
export interface StockOptions {
  confirmed: boolean; orientations: Record<string, Grain>; stock: Stock[];
  fitting_margins: Record<string, FittingMargins>;
}
export interface Settings { algorithm: Mode; kerf: number; trim: number; grain: Grain; fitting_allowance: number }
export interface Options extends StockOptions { kerf: number; trim: number; grain: Grain; fitting_allowance: number }
export interface Part {
  id: string; path: string; material: string; length: number; width: number; thickness: number;
  outline: Point[]; holes: Point[][]; profile_note: string; profile_axes: string;
  fitting_edges?: Partial<Record<FittingEdge, string>>;
  blank_length?: number; blank_width?: number; fitting_margins?: FittingMargins; template_fit?: boolean;
}
export interface Group {
  key: string; name: string; kind: 'sheet' | 'timber'; thickness: number; parts: Part[]; stock: Stock[]; stock_sourced: boolean;
}
export interface Placement {
  id: string; path: string; outline: Point[]; holes: Point[][]; angle: number; blank?: number[];
}
export interface Sheet {
  stock: Stock; parts: Placement[]; cuts: number[][]; remnants: number[][]; breakdown_cut_count?: number;
}
export interface Result {
  mode: Mode; source: string; created: string; options: Options; name: string; parts: Part[]; sheets: Sheet[];
  unplaced: string[]; stock_area: number; blank_area: number; profile_area: number;
  full_stock_count: number; offcut_count: number; estimated_cost: number | null; optimal?: boolean; objective?: string;
  stock_count_optimal?: boolean; optimises_offcuts?: boolean;
  best_offcut?: { sheet: number; x: number; y: number; length: number; width: number;
    area: number; perimeter_area_ratio: number } | null;
  profile_allowance: number;
}
export interface SawStep { cut: number[]; kind: 'reference' | 'trim' | 'breakdown' | 'part' }
/** Add reserved edge trims to the solver's blank-separating cuts, without moving any parts. */
export function sawSteps(sheet: Sheet, result: Result, kind: Group['kind']): SawStep[] {
  const native = sheet.cuts.map((cut, i): SawStep => ({ cut,
    kind: i < (sheet.breakdown_cut_count ?? 0) ? 'breakdown' : 'part' }));
  if (kind !== 'sheet' || result.mode !== 'straight' || !native.length) return native;
  const { trim, kerf } = result.options;
  const axis = sheet.stock.length >= sheet.stock.width ? 0 : 1;
  const long = axis === 0 ? sheet.stock.length : sheet.stock.width;
  const short = axis === 0 ? sheet.stock.width : sheet.stock.length;
  const line = (position: number, start: number, end: number, perpendicular = false) =>
    (axis === 0) !== perpendicular ? [position, start, position, end] : [start, position, end, position];
  const breakdown = native.filter(step => step.kind === 'breakdown');
  const steps: SawStep[] = trim > 0 ? [{ cut: line(trim, 0, short), kind: 'reference' }] : [];
  steps.push(...breakdown.map(step => ({ ...step, cut: line(step.cut[axis], 0, short) })));
  const blanks = sheet.parts.flatMap(part => part.blank ? [part.blank] : []);
  if (trim > 0 && blanks.some(blank => Math.abs(blank[axis] + blank[axis + 2] - (long - trim)) < 0.02)) {
    steps.push({ cut: line(long - trim, 0, short), kind: 'trim' });
  }
  const boundaries = breakdown.map(step => step.cut[axis]).sort((a, b) => a - b);
  const remaining = new Set(native.filter(step => step.kind !== 'breakdown'));
  let start = trim;
  for (const end of [...boundaries, long - trim]) {
    const sectionBlanks = blanks.filter(blank => blank[axis] >= start - 0.02
      && blank[axis] + blank[axis + 2] <= end + 0.02);
    if (trim > 0 && sectionBlanks.length) steps.push({ cut: line(trim, start, end, true), kind: 'reference' });
    for (const step of remaining) {
      if (Math.min(step.cut[axis], step.cut[axis + 2]) >= start - 0.02
        && Math.max(step.cut[axis], step.cut[axis + 2]) <= end + 0.02) {
        steps.push(step); remaining.delete(step);
      }
    }
    if (trim > 0 && sectionBlanks.some(blank =>
      Math.abs(blank[1 - axis] + blank[3 - axis] - (short - trim)) < 0.02)) {
      steps.push({ cut: line(short - trim, start, end, true), kind: 'trim' });
    }
    start = end + kerf;
  }
  steps.push(...remaining);
  return steps;
}
export interface Data {
  groups: Group[]; sources: Record<string, string>; current: boolean;
  jobs: Record<string, { state: 'running' | 'paused' | 'complete' | 'stopped' | 'failed'; source: string; error: string | null }>;
  state: { settings: Settings; options: Record<string, StockOptions>; results: Record<string, Result> };
}
export const mm = (n: number) => Number(n.toFixed(2)).toLocaleString('en-NZ');
export const fittingMargins = (part: Part): FittingMargins => part.fitting_margins
  ?? { left: 0, right: 0, top: 0, bottom: 0 };
export const blankSize = (part: Part): Point => [part.blank_length ?? part.length, part.blank_width ?? part.width];
export const templateFit = (part: Part) => Boolean(part.template_fit);
export const blankDimensions = (part: Part) => blankSize(part).map(mm).join(' × ');
export const fittingNote = (part: Part) => fittingEdges.filter(edge => fittingMargins(part)[edge] > 0)
  .map(edge => `${part.fitting_edges?.[edge] ? `${part.fitting_edges[edge]} / ` : ''}${edge}: +${mm(fittingMargins(part)[edge])}mm`).join('; ');
export const templateInstruction = 'Leave vehicle contours and notches uncut until fitted from a physical template.';
export function assembly(part: Pick<Part, 'path'>): string {
  return part.path === 'Finished floor plywood' || part.path.startsWith('Finished floor plywood / ') ? 'Floor'
    : part.path.includes('Rear drawer /') ? 'Drawer' : part.path.split(' / ')[0];
}
export const partName = (part: Pick<Part, 'path'>) => part.path.split(' / ').at(-1)!;
export const fullName = (part: Pick<Part, 'path'>) => `${assembly(part)} · ${partName(part)}`;
export const pieceKey = (part: Part) => JSON.stringify([assembly(part),
  ['ledges', 'slats'].includes(part.material) ? '' : partName(part).replace(/\d+/g, '#'),
  part.material, part.length, part.width, part.thickness, part.outline, part.holes,
  blankSize(part), fittingMargins(part), part.fitting_edges, part.template_fit]);
export const materialName = (group: Group) => group.kind === 'timber'
  ? `${mm(group.parts[0].width)} × ${mm(group.thickness)} mm timber`
  : `${mm(group.thickness)} mm ${group.name.replace(/\s*·\s*\d+(?:\.\d+)?\s*mm\s*$/i, '')}`;
export const isPlywood = (group: Group) => group.kind === 'sheet' && /plywood/i.test(group.name);
export const colours: Record<string, string> = {
  'Long bench': '#a8c8e7', 'Cross bench': '#afd0b0', Cabinet: '#edc88c', Drawer: '#c8b6df',
  'Laptop table': '#d9b394',
};
export const partColour = (part: Pick<Part, 'path'>) => colours[assembly(part)] ?? '#ccc4ac';
export const el = <K extends keyof HTMLElementTagNameMap>(tag: K, text = '') => {
  const node = document.createElement(tag); node.textContent = text; return node;
};
export const option = (value: string, text: string) => {
  const node = el('option', text); node.value = value; return node;
};
export function download(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const link = el('a'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export const csv = (rows: (string | number)[][]) => rows.map(row => row.map(value =>
  `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n');
