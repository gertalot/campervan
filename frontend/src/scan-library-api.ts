import { request } from './api';
import type { ScanTag } from './scan-tags';
import type { CapturePurpose } from './scan-import-api';

export interface ScanLayer { id: string; label: string; asset: string; kind: 'cloud' | 'mesh' | 'obj' }
export interface TagAlignmentDefinition {
  version: 1; target_frame: string; description?: string; origin_tag: number; up_normal_tags: number[];
  x_direction: { from_tag: number; to_tag: number }; y_direction: { from_tag: number; to_tag: number };
}
export interface ScanResult {
  key: string; id?: string; name: string; bytes: number; display_name: string;
  group_id: string | null; group_name: string | null; archived: boolean; is_default: boolean;
  layers?: ScanLayer[]; measured?: boolean; tag_layout_id?: string | null; tags?: ScanTag[]; tag_note?: string;
  alignment?: { status: string; matrix?: number[][]; target_frame?: string;
    definition?: TagAlignmentDefinition; reason?: string };
  cad_reference?: { translation_mm: [number, number, number]; rotation?: number[][]; description: string };
  created_at?: string | null; input_filenames?: string[]; pose_source?: string | null;
  settings?: { voxel_mm?: number; [key: string]: unknown }; frame_count?: number | null;
  geometry?: { triangles?: number; [key: string]: unknown };
  purpose?: CapturePurpose; units?: 'm' | 'arbitrary'; photo_error?: string | null;
  inputs?: { capture_id: string; kind: 'database' | 'photo'; filename: string; width?: number; height?: number }[];
  scale?: { status: 'metric' | 'unscaled'; factor?: number | null; source?: string | null;
    supporting_tag_ids?: number[]; reason?: string | null };
  photo_reconstruction?: {
    selected_image_count: number; registered_image_count: number; unregistered_image_ids: string[];
    component_summaries: unknown[]; selected_component_id: number | string | null;
    settings: Record<string, unknown>; versions: Record<string, unknown>; tag_support_asset: string;
  };
  source_run_id?: string | null; reference_run_id?: string | null;
}
export interface ScanEntryPreferences { display_name: string | null; group_id: string | null; archived: boolean }
export interface ScanLibraryDocument {
  version: 1; revision: number; default_key: string | null;
  groups: Record<string, string>; entries: Record<string, ScanEntryPreferences>;
  group_layouts?: Record<string, string>;
}
export const readScanResults = () => request<ScanResult[]>('scans');
export const readScanLibrary = () => request<ScanLibraryDocument>('scans/library');
export const saveScanLibrary = (candidate: ScanLibraryDocument) => request<ScanLibraryDocument>('scans/library', 'PUT', candidate);
export const deleteScanResult = (key: string, revision: number) =>
  request<ScanLibraryDocument>('scans/library/result', 'DELETE', { key, revision });
export const deleteCaptureGroup = (group_id: string, revision: number) =>
  request<ScanLibraryDocument>('scans/library/group', 'DELETE', { group_id, revision });
export const moveScanItem = (kind: 'result' | 'capture', key: string, group_id: string | null, revision: number) =>
  request<ScanLibraryDocument>('scans/library/move', 'POST', { kind, key, group_id, revision });
