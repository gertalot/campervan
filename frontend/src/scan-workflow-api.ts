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
export type ArtifactEnvelope = { [K in ArtifactKind]: ArtifactBase & { kind: K; payload: Record<string, unknown> } }[ArtifactKind];
export interface WorkflowView { revision: number; workflow: Workflow; measurement: MeasurementDocument | null; source_available: boolean; profile: ProfileRevision | null; actions: Record<WorkflowAction, { available: boolean; reasons: string[] }>; artifacts: Partial<Record<ArtifactKind, ArtifactStatus>>; stages: Record<Stage, 'Not started' | 'In progress' | 'Complete' | 'Needs updating'>; jobs: ProcessingJob[] }
export interface WorkflowEdit { revision: number; stage?: Stage; target_mm?: number; improvement_mm?: number; candidate_sigmas?: Record<string, number>; checklist_batches?: ChecklistBatch[]; review_decisions?: Record<string, unknown>; profile?: ProfileRevision; profile_ref?: ProfileRef | null; source_binding?: SourceBinding }
const base = 'scans/workflows';
export const createWorkflow = (source_run_id: string, layout_id: string) => request<WorkflowView>(base, 'POST', { source_run_id, layout_id });
export const readWorkflow = (id: string) => request<WorkflowView>(`${base}/${encodeURIComponent(id)}`);
export const editWorkflow = (id: string, edit: WorkflowEdit) => request<WorkflowView>(`${base}/${encodeURIComponent(id)}`, 'PATCH', edit);
export const runWorkflowAction = (id: string, action: WorkflowAction, revision: number, measurement_revision: number) => request<{ id: string }>(`${base}/${encodeURIComponent(id)}/actions/${action}`, 'POST', { revision, measurement_revision });
export const readWorkflowArtifact = (id: string, artifact: string) => request<{ artifact: ArtifactEnvelope; status: ArtifactStatus }>(`${base}/${encodeURIComponent(id)}/artifacts/${encodeURIComponent(artifact)}`);
export const reviseTagLayout = (id: string, body: { name: string; tag_family: '36h11'; tag_size_mm: number; revision: number; unchanged: number[]; moved: number[]; removed: number[]; added: number[] }) => request<TagLayout>(`scans/layouts/${encodeURIComponent(id)}/revise`, 'POST', body);
