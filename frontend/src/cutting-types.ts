export type Mode = 'straight' | 'nesting';
export type Grain = 'length' | 'width' | 'free';
export type Point = [number, number];
export interface Stock { name: string; length: number; width: number; copies: number; offcut: boolean }
export interface StockOptions { confirmed: boolean; orientations: Record<string, Grain>; stock: Stock[] }
export interface Settings { algorithm: Mode; kerf: number; trim: number; grain: Grain }
export interface Options extends StockOptions { kerf: number; trim: number; grain: Grain }
export interface Part {
  id: string; path: string; material: string; length: number; width: number; thickness: number;
  outline: Point[]; holes: Point[][]; profile_note: string; profile_axes: string;
}
export interface Group {
  key: string; name: string; kind: 'sheet' | 'timber'; thickness: number; parts: Part[]; stock: Stock[]; stock_sourced: boolean;
}
export interface Placement {
  id: string; path: string; outline: Point[]; holes: Point[][]; angle: number; blank?: number[];
}
export interface Sheet { stock: Stock; parts: Placement[]; cuts: number[][]; remnants: number[][] }
export interface Result {
  mode: Mode; source: string; created: string; options: Options; name: string; parts: Part[]; sheets: Sheet[];
  unplaced: string[]; stock_area: number; blank_area: number; profile_area: number;
  full_stock_count: number; offcut_count: number; estimated_cost: number | null; optimal?: boolean; objective?: string;
  stock_count_optimal?: boolean; optimises_offcuts?: boolean;
  best_offcut?: { sheet: number; x: number; y: number; length: number; width: number;
    area: number; perimeter_area_ratio: number } | null;
  profile_allowance: number;
}
export interface Data {
  groups: Group[]; sources: Record<string, string>; current: boolean;
  jobs: Record<string, { state: 'running' | 'complete' | 'stopped' | 'failed'; source: string; error: string | null }>;
  state: { settings: Settings; options: Record<string, StockOptions>; results: Record<string, Result> };
}
export const mm = (n: number) => Number(n.toFixed(2)).toLocaleString('en-NZ');
export function assembly(part: Pick<Part, 'path'>): string {
  return part.path === 'Finished floor plywood' ? 'Floor'
    : part.path.includes('Rear drawer /') ? 'Drawer' : part.path.split(' / ')[0];
}
export const partName = (part: Pick<Part, 'path'>) => part.path.split(' / ').at(-1)!;
export const fullName = (part: Pick<Part, 'path'>) => `${assembly(part)} · ${partName(part)}`;
export const pieceKey = (part: Part) => JSON.stringify([assembly(part),
  ['ledges', 'slats'].includes(part.material) ? '' : partName(part).replace(/\d+/g, '#'),
  part.material, part.length, part.width, part.thickness, part.outline, part.holes]);
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
