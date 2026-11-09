import { request } from './api';
import type { ScanTag } from './scan-tags';
import type { DistanceMeasurement, MeasurementDocument } from './scan-measurements-api';
import type { ProcessingJob } from './scan-import-api';
export interface AnalysisResult {
  run_id: string; tag_layout_id: string; measurement_revision: number; tags: ScanTag[];
  movements: { id: number; before: number[]; after: number[]; distance_m: number }[];
  residuals: (DistanceMeasurement & { scan_m: number; fitted_m: number; residual_m: number; weight: number; standardised_residual: number })[];
  dimensions: { tag_a: number; tag_b: number; before_95_m: number; after_95_m: number }[];
  diagnostics: { note: string; nodes: number; original_factors: number; excluded_nonlocalised_links: number };
}
export interface SuggestedPair {
  tag_a: number; tag_b: number; target_a: number; target_b: number; gain_m: number; before_95_m: number; after_95_m: number;
  clearance: 'unknown' | 'obstructed' | 'no_obstruction_detected'; clearance_reason: string;
  overlaps_with: number[][]; manual?: boolean; hit?: number[];
}
export interface AnalysisStatus {
  id: string; job: ProcessingJob; result: AnalysisResult | null; stale: boolean; solution_revision: number;
  diagnostic: { message: string; note: string; pairs: { tag_a: number; tag_b: number }[] } | null;
  acceptance: { active: boolean; source_run_id: string; result_run_id: string; job_id: string } | null;
  accepted_job: ProcessingJob | null; suggestions_job: ProcessingJob | null;
  suggestions: { rows: SuggestedPair[]; threshold_mm: number; note: string;
    remeasure: (DistanceMeasurement & { standardised_residual: number })[] } | null;
}
export const analyseMeasurements = (run_id: string, doc: MeasurementDocument) => request<{id: string}>('scans/analyses', 'POST', {
  run_id, tag_layout_id: doc.tag_layout_id, revision: doc.revision,
});
export const readAnalysis = (id: string) => request<AnalysisStatus>(`scans/analyses/${id}`);
export const applyAnalysis = (id: string, solution_revision: number) => request<ProcessingJob>(`scans/analyses/${id}/apply`, 'POST', { solution_revision });
export const revertAnalysis = (id: string, solution_revision: number) => request<{result_key: string}>(`scans/analyses/${id}/revert`, 'POST', { solution_revision });
export const suggestMeasurements = (id: string, threshold_mm: number) => request<{id: string}>(`scans/analyses/${id}/suggestions`, 'POST', { threshold_mm });
