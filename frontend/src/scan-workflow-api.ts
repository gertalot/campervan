import { request } from './api';
import type { ProcessingJob, TagLayout } from './scan-import-api';
import type { MeasurementDocument } from './scan-measurements-api';

export type Stage = 'review_capture' | 'measure' | 'check_accuracy' | 'update_reconstruction';
export type ArtifactKind = 'measurement_network' | 'measurement_plan' | 'placement_review' | 'context_review' | 'scan_correction';
export type WorkflowAction = 'review-placement' | 'plan-measurements' | 'check-measurements' | 'suggest-more' | 'preview-correction' | 'update-mesh';
export interface Pair { tag_a: number; tag_b: number }
export interface ProfileRef { profile_id: string; revision: number }
export interface Relationship { kind: string; region_ids: string[]; enabled: boolean; sigma: number | null; units: string | null; support: string[] }
export interface ProfileRevision { profile_id: string; revision: number; layout_id: string; context_text: string; target_classes: string[]; relationships: Relationship[]; tag_references: Record<string, unknown>[] }
export interface SourceBinding { source_run_id: string; profile_ref: ProfileRef; revision: number; regions: { id: string; label: string; support: { frame_id: string; asset: string; observed_xyz: [number, number, number] | null }[]; correction_revision: number }[]; masks: { frame_id: string; asset: string; revision: number }[]; relationships: Relationship[] }
export interface ChecklistBatch { id: string; kind: 'initial' | 'additional' | 'recheck'; ordered_pairs: Pair[]; current_pair: Pair | null; producing_artifact_id: string }
export interface Workflow { id: string; source_run_id: string; layout_id: string; group_id: string | null; profile_ref: ProfileRef | null; source_binding: SourceBinding | null; stage: Stage; target_mm: number; improvement_mm: number; candidate_sigmas: Record<string, number>; checklist_batches: ChecklistBatch[]; artifact_refs: Partial<Record<ArtifactKind, string>>; corrected_run_id: string | null; review_decisions: Record<string, unknown> }
export interface ArtifactStatus { status: 'current' | 'stale' | 'unavailable'; reasons: string[]; available_actions: string[] }
interface ArtifactBase { version: 1; id: string; algorithm_version: string; workflow_id: string; source_run_id: string; layout_id: string; measurement_revision: number; profile_ref: ProfileRef | null; fingerprints: Record<string, string>; assumptions: Record<string, unknown>; job_id: string }
export interface NetworkInformation {
  rigid_motion_rank: number; shape_dimension: number; rank: number; nullity: number;
  singular_values: number[]; rank_cutoff: number; nonzero_singular_ratio: number | null;
  condition_number: number | null; poorly_conditioned: boolean;
}
export interface NetworkTopology {
  status: 'rigid' | 'not_certified' | 'unknown'; vertices: number[]; edges: [number, number][];
  seed: number; package: 'pyrigi'; version: string | null; dimension: 3; algorithm: 'randomized';
  probability: number; qualification: string; error: string | null; elapsed_s: number;
}
export interface NetworkEllipsoid {
  tag_id: number; semi_axes_95_m: number[]; directions: number[][];
  longest_semi_axis_95_m: number; worst_direction: number[];
}
export interface NetworkResidual extends Pair {
  entered_m: number; fitted_m: number | null; residual_m: number | null; sigma_m: number | null;
  standardised_residual: number | null; weight: number | null;
}
export interface NetworkSettings {
  huber_k: number; rank_rtol: number; poor_condition_ratio: number; coincident_m: number;
  linear_solver: 'MULTIFRONTAL_QR';
  rigidity_algorithm: 'randomized'; rigidity_probability: number;
  covariance_convention: 'equal-weight-orthogonal-free-network';
}
export interface MeasurementNetwork {
  tag_ids: number[]; positions_m: number[][]; Q: number[][]; covariance_m2: number[][] | null;
  null_basis: number[][]; information: NetworkInformation;
  completeness: {
    status: 'complete' | 'incomplete'; active_tag_count: number; active_measurement_count: number;
    inactive_measurement_count: number;
    inactive_measurements: (MeasurementDocument['distances'][number] & { reason: string })[];
    unmeasured_tags: number[]; components: number[][]; remaining_motions: number;
    generic_rigidity: NetworkTopology; actual_geometry_rank: number; actual_geometry_singular_values_m: number[];
    adequate_3d_geometry: boolean; nonlinear_ambiguity: boolean; coincident_initial_pairs: [number, number][];
  };
  consistency: {
    status: 'unknown' | 'assessed'; residual_sign: 'fitted-entered'; residuals: NetworkResidual[];
    redundancy: number; can_check_errors: boolean; downweighted_pairs: number;
    rank_before_robust_weights: number; rank_after_robust_weights: number;
  };
  uncertainty: {
    status: 'unknown' | 'unbounded' | 'finite'; local_status: 'unknown' | 'unbounded' | 'finite';
    ellipsoids: NetworkEllipsoid[]; worst_tag: NetworkEllipsoid | null; local_worst_tag: NetworkEllipsoid | null;
    confidence: number; conversion: string; convention: string; nonlinear_ambiguity: boolean; qualification: string;
  };
  solver: {
    status: 'not_needed' | 'unavailable' | 'fitted'; iterations: number;
    initial_objective: number | null; final_objective: number | null;
    method: string; linear_solver: 'MULTIFRONTAL_QR'; loss: 'Huber'; huber_k: number; sigma_rule: string; gauge_anchors: number[];
    gauge_coordinates: string[]; display_rotation: number[][]; scan_information: false; damping_information: false;
  };
  settings: NetworkSettings; warnings: string[];
  runtime: { dependencies: Record<string, string | null>; dependency_import_s: number; fit_s: number; rigidity_s: number; total_s: number };
}
export type ArtifactEnvelope = { [K in ArtifactKind]: ArtifactBase & {
  kind: K; payload: K extends 'measurement_network' ? MeasurementNetwork : Record<string, unknown>
} }[ArtifactKind];
export interface WorkflowView { revision: number; workflow: Workflow; measurement: MeasurementDocument | null; source_available: boolean; profile: ProfileRevision | null; actions: Record<WorkflowAction, { available: boolean; reasons: string[] }>; artifacts: Partial<Record<ArtifactKind, ArtifactStatus>>; stages: Record<Stage, 'Not started' | 'In progress' | 'Complete' | 'Needs updating'>; jobs: ProcessingJob[] }
export interface WorkflowEdit { revision: number; stage?: Stage; target_mm?: number; improvement_mm?: number; candidate_sigmas?: Record<string, number>; checklist_batches?: ChecklistBatch[]; review_decisions?: Record<string, unknown>; profile?: ProfileRevision; profile_ref?: ProfileRef | null; source_binding?: SourceBinding }
const base = 'scans/workflows';
export const createWorkflow = (source_run_id: string, layout_id: string) => request<WorkflowView>(base, 'POST', { source_run_id, layout_id });
export const readWorkflow = (id: string) => request<WorkflowView>(`${base}/${encodeURIComponent(id)}`);
export const editWorkflow = (id: string, edit: WorkflowEdit) => request<WorkflowView>(`${base}/${encodeURIComponent(id)}`, 'PATCH', edit);
export const runWorkflowAction = (id: string, action: WorkflowAction, revision: number, measurement_revision: number) => request<{ id: string }>(`${base}/${encodeURIComponent(id)}/actions/${action}`, 'POST', { revision, measurement_revision });
export const readWorkflowArtifact = (id: string, artifact: string) => request<{ artifact: ArtifactEnvelope; status: ArtifactStatus }>(`${base}/${encodeURIComponent(id)}/artifacts/${encodeURIComponent(artifact)}`);
export const reviseTagLayout = (id: string, body: { name: string; tag_family: '36h11'; tag_size_mm: number; revision: number; unchanged: number[]; moved: number[]; removed: number[]; added: number[] }) => request<TagLayout>(`scans/layouts/${encodeURIComponent(id)}/revise`, 'POST', body);
