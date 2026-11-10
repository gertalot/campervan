import { ApiError, request } from './api';
import type { TagAlignmentDefinition } from './scan-library-api';
export type CapturePurpose = 'preview' | 'photographic';
export interface ImportedCapture {
  id: string; group_id: string; filename: string; bytes: number; frames: number;
  kind: 'database' | 'photo'; width?: number; height?: number;
}
export function captureDescription(capture: ImportedCapture) {
  return capture.kind === 'photo'
    ? `Original photo · ${capture.width && capture.height ? `${capture.width} × ${capture.height} px` : 'dimensions unknown'}`
    : `RTAB-Map database · ${capture.frames} frames`;
}
export interface PreviewSettings { voxel_mm: number; sdf_trunc_mm: number; texture_mode: 'baked' }
export interface PhotographicSettings { num_threads: number; target_triangles: number; texture_size: number }
interface CaptureRequest {
  group_id: string; capture_ids: string[]; layout_id: string; name: string;
  alignment_definition?: TagAlignmentDefinition;
}
export type CaptureProcessing = { purpose: 'preview'; settings: PreviewSettings }
  | { purpose: 'photographic'; settings: PhotographicSettings };
export type ProcessCaptures = CaptureRequest & CaptureProcessing;
export interface TagLayout { id: string; name: string; tag_family: string; tag_size_mm: number }
export interface ProcessingJob {
  id: string; run_id: string; group_id: string | null; name: string; layout_id: string;
  state: 'processing' | 'completed' | 'failed' | 'interrupted' | 'cancelled'; stage: string; error: string | null; log_tail?: string;
  result_key?: string;
  progress_percent?: number;
  request?: { purpose: CapturePurpose; settings: Record<string, unknown>;
    inputs: { capture_id: string; kind: 'database' | 'photo'; filename: string }[] };
}
export interface ScanImports { captures: ImportedCapture[]; layouts: TagLayout[]; jobs: ProcessingJob[] }
export const readScanImports = () => request<ScanImports>('scans/imports');
export const readScanJob = (id: string) => request<ProcessingJob>(`scans/process/${encodeURIComponent(id)}`);
export const cancelScanJob = (id: string) => request<ProcessingJob>(`scans/process/${encodeURIComponent(id)}/cancel`, 'POST');
export const createTagLayout = (name: string, tag_size_mm: number) =>
  request<TagLayout>('scans/layouts', 'POST', { name, tag_size_mm, tag_family: '36h11' });
export const processCaptures = (body: ProcessCaptures) => request<ProcessingJob>('scans/process', 'POST', body);
export function uploadCapture(file: File, group: string, progress: (fraction: number) => void): Promise<ImportedCapture> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/v1/scans/captures?${new URLSearchParams({ group_id: group, filename: file.name })}`);
    xhr.setRequestHeader('Content-Type', 'application/octet-stream');
    xhr.upload.onprogress = event => { if (event.lengthComputable) progress(event.loaded / event.total); };
    xhr.onerror = () => reject(new Error(`Could not upload ${file.name}. Check the local API connection.`));
    xhr.onload = () => {
      try {
        const response = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) resolve(response as ImportedCapture);
        else reject(new ApiError(xhr.status, typeof response.detail === 'string' ? response.detail : `Upload failed (${xhr.status}).`));
      } catch { reject(new Error(`Could not read the upload response (${xhr.status}).`)); }
    };
    xhr.send(file);
  });
}
