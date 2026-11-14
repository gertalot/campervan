import { request } from './api';

export type SectionPlane = 'XZ' | 'YZ';
export type SectionPoint = [number, number]; // XZ: distance from centreline/Z; YZ: Y/Z, in millimetres
export interface OutlineSegment {
  kind: 'line' | 'cubic';
  end: SectionPoint;
  control1?: SectionPoint | null;
  control2?: SectionPoint | null;
}
export interface AuthoredSection {
  id: string;
  label: string;
  plane: SectionPlane;
  y_mm: number | null;
  x_mm: number | null;
  scan_key: string;
  centre_x_mm: number;
  start: SectionPoint | null;
  floor_z_mm: number | null;
  ceiling_z_mm: number | null;
  segments: OutlineSegment[];
  mirror_x: boolean;
  opposite_start: SectionPoint | null;
  opposite_segments: OutlineSegment[] | null;
  state: 'draft' | 'recorded';
  notes: string;
}
export interface SectionDocument {
  version: 1;
  revision: number;
  sections: AuthoredSection[];
}

export const readCrossSections = () => request<SectionDocument>('cross-sections');
export const recordCrossSection = (id: string, revision: number) =>
  request<SectionDocument>(`cross-sections/${encodeURIComponent(id)}/record`, 'POST', { revision });
