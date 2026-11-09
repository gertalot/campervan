import { request } from './api';

export interface DistanceMeasurement {
  tag_a: number; tag_b: number; distance_m: number; entered_text: string; source_run_id: string; sigma_m: number | null;
}
export interface MeasurementDocument {
  version: 1; tag_layout_id: string; revision: number; distances: DistanceMeasurement[];
  default_sigma_m?: number | null;
  excluded_pairs?: { tag_a: number; tag_b: number; reason: string }[];
}
export interface MeasurementResponse { configured: boolean; document: MeasurementDocument | null; layout_name?: string }
export const readMeasurements = (layout?: string | null) => request<MeasurementResponse>(
  `scans/measurements${layout ? `?tag_layout_id=${encodeURIComponent(layout)}` : ''}`,
);
export function saveMeasurement(document: MeasurementDocument, record: Omit<DistanceMeasurement, 'sigma_m'>) {
  const { tag_a, tag_b, ...values } = record;
  return request<MeasurementDocument>(`scans/measurements/${tag_a}/${tag_b}`, 'PUT', {
    ...values, revision: document.revision, tag_layout_id: document.tag_layout_id,
  });
}
export function removeMeasurement(document: MeasurementDocument, record: DistanceMeasurement) {
  return request<MeasurementDocument>(`scans/measurements/${record.tag_a}/${record.tag_b}`, 'DELETE', {
    revision: document.revision, tag_layout_id: document.tag_layout_id,
  });
}
export const configureMeasurements = (document: MeasurementDocument, default_sigma_m: number | null,
  pair_sigmas: Record<string, number | null> = {}, excluded_pairs = document.excluded_pairs ?? []) =>
  request<MeasurementDocument>('scans/measurements/settings', 'PUT', {
    revision: document.revision, tag_layout_id: document.tag_layout_id, default_sigma_m, pair_sigmas, excluded_pairs,
  });
