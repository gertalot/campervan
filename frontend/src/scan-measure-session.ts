import { ApiError } from './api';
import { configureMeasurements, readMeasurements, removeMeasurement, saveMeasurement,
  type MeasurementDocument } from './scan-measurements-api';
import { editWorkflow, readWorkflow, type ChecklistBatch, type Pair, type WorkflowView } from './scan-workflow-api';

export function parseDistance(value: string): number {
  const match = value.trim().match(/^(\d+(?:\.\d*)?|\.\d+)\s*(mm|cm|m|in|ft)?$/i);
  if (!match) throw new Error('Enter a positive distance in mm, cm, m, in or ft (for example 841 mm).');
  const scale: Record<string, number> = { mm: 0.001, cm: 0.01, m: 1, in: 0.0254, ft: 0.3048 };
  const result = Number(match[1]) * scale[(match[2] ?? 'mm').toLowerCase()];
  if (!Number.isFinite(result) || result <= 0) throw new Error('Distance must be greater than zero.');
  return result;
}
export const pairKey = (pair: Pair) => `${Math.min(pair.tag_a, pair.tag_b)}:${Math.max(pair.tag_a, pair.tag_b)}`;
export interface Draft { text: string; saved: string; state: 'Saved' | 'Saving' | 'Not saved'; error: string }
export interface MeasurementSettings { default_sigma_m?: number | null; pair_sigmas?: Record<string, number | null>;
  excluded_pairs?: NonNullable<MeasurementDocument['excluded_pairs']> }
export function createMeasurementSession(initial: MeasurementDocument, source: () => string | undefined) {
  let document = initial;
  let workflow: WorkflowView | null = null;
  const drafts = new Map<string, Draft>();
  const precisionDrafts = new Map<string, string>();
  let settingsError = '';
  const pending = new Map<string, { text: string; promise: Promise<boolean> }>();
  const conflicts = new Map<string, number>();
  const listeners = new Set<() => void>();
  let queue: Promise<unknown> = Promise.resolve();
  const notify = () => listeners.forEach(listener => listener());
  const record = (pair: Pair) => document.distances.find(row => pairKey(row) === pairKey(pair));
  function draft(pair: Pair): Draft {
    const key = pairKey(pair); let value = drafts.get(key);
    if (!value) { const saved = record(pair)?.entered_text ?? ''; value = { text: saved, saved, state: 'Saved', error: '' }; drafts.set(key, value); }
    return value;
  }
  function setDraft(pair: Pair, text: string) {
    const value = draft(pair); value.text = text; value.error = '';
    value.state = pending.has(pairKey(pair)) ? 'Saving' : text === value.saved ? 'Saved' : 'Not saved'; notify();
  }
  function enqueue<T>(action: () => Promise<T>): Promise<T> {
    const result = queue.then(action); queue = result.catch(() => undefined); return result;
  }
  async function refresh() {
    const response = await readMeasurements(document.tag_layout_id);
    if (!response.document || response.document.tag_layout_id !== document.tag_layout_id) throw new Error('Measurement document is unavailable.');
    document = response.document;
    for (const [key, value] of drafts) {
      const saved = document.distances.find(row => pairKey(row) === key)?.entered_text ?? '';
      const clean = value.text === value.saved; value.saved = saved;
      if (clean) value.text = saved;
      if (!pending.has(key)) value.state = value.text === saved ? 'Saved' : 'Not saved';
    }
    notify();
  }
  function commit(pair: Pair): Promise<boolean> {
    const key = pairKey(pair); const value = draft(pair); const text = value.text;
    const existing = pending.get(key); if (existing?.text === text) return existing.promise;
    if (text === value.saved && !existing) { value.state = 'Saved'; value.error = ''; notify(); return Promise.resolve(true); }
    let distance: number;
    try { distance = parseDistance(text); } catch (reason) { value.state = 'Not saved'; value.error = (reason as Error).message; notify(); return Promise.resolve(false); }
    const sourceId = source();
    if (!sourceId) { value.state = 'Not saved'; value.error = 'Select a capture before saving.'; notify(); return Promise.resolve(false); }
    value.state = 'Saving'; value.error = ''; notify();
    const conflictVersion = conflicts.get(key) ?? 0;
    const promise: Promise<boolean> = enqueue(async () => {
      if ((conflicts.get(key) ?? 0) !== conflictVersion) {
        value.state = 'Not saved'; value.error = 'The document changed. Retry saving this value.';
        if (pending.get(key)?.promise === promise) pending.delete(key); notify(); return false;
      }
      try {
        document = await saveMeasurement(document, { tag_a: Math.min(pair.tag_a, pair.tag_b), tag_b: Math.max(pair.tag_a, pair.tag_b),
          distance_m: distance, entered_text: text.trim(), source_run_id: sourceId });
        value.saved = text.trim(); if (value.text === text) value.text = value.saved;
        value.state = value.text === value.saved ? 'Saved' : 'Not saved'; value.error = ''; return true;
      } catch (reason) {
        if (reason instanceof ApiError && reason.status === 409) {
          conflicts.set(key, (conflicts.get(key) ?? 0) + 1);
          try { await refresh(); } catch { /* retain the original conflict */ }
        }
        value.state = 'Not saved'; value.error = `${reason instanceof Error ? reason.message : String(reason)} Retry saving this value.`; return false;
      } finally { if (pending.get(key)?.promise === promise) pending.delete(key); notify(); }
    });
    pending.set(key, { text, promise }); return promise;
  }
  async function mutate(action: () => Promise<MeasurementDocument>) {
    return enqueue(async () => {
      try { document = await action(); notify(); return true; }
      catch (reason) { if (reason instanceof ApiError && reason.status === 409) await refresh(); throw reason; }
    });
  }
  return {
    get document() { return document; }, get workflow() { return workflow; }, draft, setDraft, commit,
    precisionDraft(key: string) { return precisionDrafts.get(key); },
    setPrecisionDraft(key: string, text: string) { precisionDrafts.set(key, text); notify(); },
    bindWorkflow(view: WorkflowView | null) { workflow = view; notify(); },
    setChecklist(batches: ChecklistBatch[]) {
      const bound = workflow; if (!bound) return Promise.reject(new Error('Workflow is unavailable.'));
      return enqueue(async () => {
        try { const saved = await editWorkflow(bound.workflow.id, { revision: workflow?.workflow.id === bound.workflow.id ? workflow.revision : bound.revision, checklist_batches: batches });
          if (workflow?.workflow.id === bound.workflow.id) { workflow = saved; notify(); } return saved;
        } catch (reason) { if (reason instanceof ApiError && reason.status === 409) { const refreshed = await readWorkflow(bound.workflow.id);
          if (workflow?.workflow.id === bound.workflow.id) { workflow = refreshed; notify(); } } throw reason; }
      });
    },
    setCandidateSigma(pair: Pair, sigma: number | null) {
      const bound = workflow; if (!bound) return Promise.reject(new Error('Workflow is unavailable.'));
      const key = pairKey(pair); const submitted = precisionDrafts.get(key);
      return enqueue(async () => {
        try {
          const current = workflow?.workflow.id === bound.workflow.id ? workflow : bound;
          const candidate_sigmas = { ...current.workflow.candidate_sigmas };
          if (sigma === null) delete candidate_sigmas[key]; else candidate_sigmas[key] = sigma;
          const saved = await editWorkflow(bound.workflow.id, { revision: current.revision, candidate_sigmas });
          if (workflow?.workflow.id === bound.workflow.id) workflow = saved;
          if (precisionDrafts.get(key) === submitted) precisionDrafts.delete(key);
          settingsError = ''; notify(); return saved;
        } catch (reason) {
          if (reason instanceof ApiError && reason.status === 409) {
            const refreshed = await readWorkflow(bound.workflow.id);
            if (workflow?.workflow.id === bound.workflow.id) workflow = refreshed;
          }
          settingsError = reason instanceof Error ? reason.message : String(reason); notify(); throw reason;
        }
      });
    },
    remove(pair: Pair) { return mutate(async () => { const row = record(pair); if (!row) return document;
      const result = await removeMeasurement(document, row); const value = draft(pair); value.saved = ''; if (value.text === row.entered_text) value.text = ''; value.state = value.text ? 'Not saved' : 'Saved'; return result; }); },
    setExclusion(pair: Pair, reason: string | null) {
      return mutate(() => {
        const excluded = (document.excluded_pairs ?? []).filter(item => pairKey(item) !== pairKey(pair));
        if (reason) excluded.push({ tag_a: Math.min(pair.tag_a, pair.tag_b), tag_b: Math.max(pair.tag_a, pair.tag_b), reason });
        return configureMeasurements(document, document.default_sigma_m ?? null, {}, excluded);
      });
    },
    async configure(change: MeasurementSettings) {
      const keys = [...Object.keys(change.pair_sigmas ?? {}), ...(change.default_sigma_m === undefined ? [] : ['default'])];
      const submitted = new Map(keys.map(key => [key, precisionDrafts.get(key)]));
      try {
        const result = await mutate(() => configureMeasurements(document,
          change.default_sigma_m === undefined ? document.default_sigma_m ?? null : change.default_sigma_m,
          change.pair_sigmas ?? {}, change.excluded_pairs ?? document.excluded_pairs ?? []));
        for (const [key, value] of submitted) if (precisionDrafts.get(key) === value) precisionDrafts.delete(key);
        settingsError = ''; notify(); return result;
      } catch (reason) { settingsError = reason instanceof Error ? reason.message : String(reason); notify(); throw reason; }
    },
    async flush() { await queue; const unsaved = [...drafts.entries()].filter(([, value]) => value.state !== 'Saved' || value.text !== value.saved);
      return { ok: !unsaved.length && !precisionDrafts.size && !settingsError, settingsError, precision: [...precisionDrafts.keys()], pairs: unsaved.map(([key]) => { const [tag_a, tag_b] = key.split(':').map(Number); return { tag_a, tag_b }; }) }; },
    refresh() { return enqueue(refresh); },
    subscribe(listener: () => void) { listeners.add(listener); return () => listeners.delete(listener); },
    hasUnsaved() { return !!precisionDrafts.size || [...drafts.values()].some(value => value.state !== 'Saved' || value.text !== value.saved); },
  };
}
export type MeasurementSession = ReturnType<typeof createMeasurementSession>;
