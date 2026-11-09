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
  const workflowViews = new Map<string, WorkflowView>();
  const checklists = new Map<string, { batches: ChecklistBatch[]; error: string; blocked: boolean; version: number; attempt: number }>();
  const drafts = new Map<string, Draft>();
  const precisionDrafts = new Map<string, string>();
  const candidateDrafts = new Map<string, Map<string, string>>();
  const candidateErrors = new Map<string, Map<string, string>>();
  const exclusions = new Map<string, { pair: Pair; reason: string | null; error: string; blocked: boolean; version: number; attempt: number }>();
  let settingsError = '';
  const pending = new Map<string, { text: string; promise: Promise<boolean> }[]>();
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
    const existing = pending.get(key)?.at(-1); if (existing?.text === text) return existing.promise;
    if (text === value.saved && !existing) { value.state = 'Saved'; value.error = ''; notify(); return Promise.resolve(true); }
    let distance: number;
    try { distance = parseDistance(text); } catch (reason) { value.state = 'Not saved'; value.error = (reason as Error).message; notify(); return Promise.resolve(false); }
    const sourceId = source();
    const workflowId = workflow && workflow.workflow.source_run_id === sourceId ? workflow.workflow.id : undefined;
    if (!sourceId) { value.state = 'Not saved'; value.error = 'Select a capture before saving.'; notify(); return Promise.resolve(false); }
    value.state = 'Saving'; value.error = ''; notify();
    const conflictVersion = conflicts.get(key) ?? 0;
    const promise: Promise<boolean> = enqueue(async () => {
      try {
        if ((conflicts.get(key) ?? 0) !== conflictVersion) {
          value.error = 'The document changed. Retry saving this value.'; return false;
        }
        if (!record(pair) && !workflowId) throw new Error('Wait for this capture’s workflow to load before saving.');
        if (!record(pair) && workflowId && candidateDrafts.get(workflowId)?.has(key)) throw new Error('Save the pair precision before saving this distance.');
        const candidate = workflowId ? workflowViews.get(workflowId)?.workflow.candidate_sigmas[key] : undefined;
        document = await saveMeasurement(document, { tag_a: Math.min(pair.tag_a, pair.tag_b), tag_b: Math.max(pair.tag_a, pair.tag_b),
          distance_m: distance, entered_text: text.trim(), source_run_id: sourceId,
          ...(!record(pair) && candidate !== undefined ? { sigma_m: candidate } : {}) });
        value.saved = text.trim(); if (value.text === text) value.text = value.saved;
        value.error = ''; return true;
      } catch (reason) {
        if (reason instanceof ApiError && reason.status === 409) {
          conflicts.set(key, (conflicts.get(key) ?? 0) + 1);
          try { await refresh(); } catch { /* retain the original conflict */ }
        }
        value.state = 'Not saved'; value.error = `${reason instanceof Error ? reason.message : String(reason)} Retry saving this value.`; return false;
      } finally {
        const outstanding = (pending.get(key) ?? []).filter(item => item.promise !== promise);
        if (outstanding.length) pending.set(key, outstanding); else pending.delete(key);
        value.state = outstanding.length ? 'Saving' : value.error || value.text !== value.saved ? 'Not saved' : 'Saved';
        notify();
      }
    });
    pending.set(key, [...pending.get(key) ?? [], { text, promise }]); notify(); return promise;
  }
  async function mutate(action: () => Promise<MeasurementDocument>) {
    return enqueue(async () => {
      try { document = await action(); notify(); return true; }
      catch (reason) { if (reason instanceof ApiError && reason.status === 409) await refresh(); throw reason; }
    });
  }
  function saveChecklist(id: string, draft: { batches: ChecklistBatch[]; error: string; blocked: boolean; version: number; attempt: number }) {
    const submitted = draft.batches; const version = draft.version; const attempt = draft.attempt;
    return enqueue(async () => {
      if (draft.blocked || draft.attempt !== attempt) throw new Error(draft.error || 'Retry saving checklist progress.');
      const current = workflowViews.get(id);
      if (!current) throw new Error('Workflow is unavailable.');
      try {
        const saved = await editWorkflow(id, { revision: current.revision, checklist_batches: submitted });
        workflowViews.set(id, saved); if (workflow?.workflow.id === id) workflow = saved;
        if (draft.version === version) checklists.delete(id);
        notify(); return saved;
      } catch (reason) {
        draft.blocked = true; draft.attempt++;
        draft.error = `${reason instanceof Error ? reason.message : String(reason)} Retry saving checklist progress.`;
        if (reason instanceof ApiError && reason.status === 409) {
          try { const refreshed = await readWorkflow(id); workflowViews.set(id, refreshed);
            if (workflow?.workflow.id === id) workflow = refreshed; } catch { /* retain the original conflict */ }
        }
        notify(); throw reason;
      }
    });
  }
  function saveExclusion(key: string, change: { pair: Pair; reason: string | null; error: string; blocked: boolean; version: number; attempt: number }) {
    const { pair, reason, version, attempt } = change;
    return enqueue(async () => {
      if (change.blocked || change.attempt !== attempt) throw new Error(change.error || 'Retry saving this exclusion.');
      try {
        const excluded = (document.excluded_pairs ?? []).filter(item => pairKey(item) !== key);
        if (reason) excluded.push({ tag_a: Math.min(pair.tag_a, pair.tag_b), tag_b: Math.max(pair.tag_a, pair.tag_b), reason });
        document = await configureMeasurements(document, document.default_sigma_m ?? null, {}, excluded);
        if (change.version === version) exclusions.delete(key);
        notify(); return true;
      } catch (failure) {
        change.blocked = true; change.attempt++;
        change.error = `${failure instanceof Error ? failure.message : String(failure)} Retry saving this exclusion.`;
        if (failure instanceof ApiError && failure.status === 409) { try { await refresh(); } catch { /* retain the original conflict */ } }
        notify(); throw failure;
      }
    });
  }
  return {
    get document() { return document; }, get workflow() { return workflow; }, draft, setDraft, commit,
    precisionDraft(key: string, candidate = false) { return candidate ? workflow && candidateDrafts.get(workflow.workflow.id)?.get(key) : precisionDrafts.get(key); },
    setPrecisionDraft(key: string, text: string, candidate = false) {
      if (candidate) { if (!workflow) return; const id = workflow.workflow.id;
        let values = candidateDrafts.get(id); if (!values) { values = new Map(); candidateDrafts.set(id, values); } values.set(key, text);
      } else precisionDrafts.set(key, text); notify();
    },
    candidateError(key: string) { return workflow ? candidateErrors.get(workflow.workflow.id)?.get(key) : undefined; },
    discardCandidatePrecision(key: string) {
      if (!workflow) return; const id = workflow.workflow.id;
      const values = candidateDrafts.get(id); values?.delete(key); if (values && !values.size) candidateDrafts.delete(id);
      const errors = candidateErrors.get(id); errors?.delete(key); if (errors && !errors.size) candidateErrors.delete(id); notify();
    },
    bindWorkflow(view: WorkflowView | null) { workflow = view; if (view) workflowViews.set(view.workflow.id, view); notify(); },
    checklistDraft() { return workflow ? checklists.get(workflow.workflow.id) : undefined; },
    setChecklist(batches: ChecklistBatch[]) {
      const bound = workflow; if (!bound) return Promise.reject(new Error('Workflow is unavailable.'));
      const id = bound.workflow.id;
      let draft = checklists.get(id);
      if (!draft) { draft = { batches, error: '', blocked: false, version: 0, attempt: 0 }; checklists.set(id, draft); }
      else { draft.batches = batches; draft.version++; }
      notify();
      if (draft.blocked) return Promise.reject(new Error(draft.error));
      return saveChecklist(id, draft);
    },
    retryChecklist() {
      const id = workflow?.workflow.id; const draft = id ? checklists.get(id) : undefined;
      if (!id || !draft) return Promise.reject(new Error('No checklist changes to retry.'));
      draft.blocked = false; notify(); return saveChecklist(id, draft);
    },
    setCandidateSigma(pair: Pair, sigma: number | null) {
      const bound = workflow; if (!bound) return Promise.reject(new Error('Workflow is unavailable.'));
      const key = pairKey(pair); const values = candidateDrafts.get(bound.workflow.id); const submitted = values?.get(key);
      return enqueue(async () => {
        try {
          const current = workflowViews.get(bound.workflow.id) ?? bound;
          const candidate_sigmas = { ...current.workflow.candidate_sigmas };
          if (sigma === null) delete candidate_sigmas[key]; else candidate_sigmas[key] = sigma;
          const saved = await editWorkflow(bound.workflow.id, { revision: current.revision, candidate_sigmas });
          workflowViews.set(bound.workflow.id, saved);
          if (workflow?.workflow.id === bound.workflow.id) workflow = saved;
          if (values && candidateDrafts.get(bound.workflow.id) === values && values.get(key) === submitted) {
            values.delete(key); if (!values.size) candidateDrafts.delete(bound.workflow.id);
          }
          const errors = candidateErrors.get(bound.workflow.id); errors?.delete(key);
          if (errors && !errors.size) candidateErrors.delete(bound.workflow.id);
          notify(); return saved;
        } catch (reason) {
          if (reason instanceof ApiError && reason.status === 409) {
            try { const refreshed = await readWorkflow(bound.workflow.id);
              workflowViews.set(bound.workflow.id, refreshed);
              if (workflow?.workflow.id === bound.workflow.id) workflow = refreshed;
            } catch { /* retain the original conflict */ }
          }
          if (values && candidateDrafts.get(bound.workflow.id) === values && values.has(key)) {
            let errors = candidateErrors.get(bound.workflow.id);
            if (!errors) { errors = new Map(); candidateErrors.set(bound.workflow.id, errors); }
            errors.set(key, reason instanceof Error ? reason.message : String(reason));
          }
          notify(); throw reason;
        }
      });
    },
    remove(pair: Pair) { return mutate(async () => { const row = record(pair); if (!row) return document;
      const result = await removeMeasurement(document, row); const value = draft(pair); value.saved = ''; if (value.text === row.entered_text) value.text = ''; value.state = value.text ? 'Not saved' : 'Saved'; return result; }); },
    exclusionDraft(pair: Pair) { return exclusions.get(pairKey(pair)); },
    setExclusion(pair: Pair, reason: string | null) {
      const key = pairKey(pair); let change = exclusions.get(key);
      if (!change) { change = { pair, reason, error: '', blocked: false, version: 0, attempt: 0 }; exclusions.set(key, change); }
      else { change.reason = reason; change.version++; }
      notify();
      if (change.blocked) return Promise.reject(new Error(change.error));
      return saveExclusion(key, change);
    },
    retryExclusion(pair: Pair) {
      const key = pairKey(pair); const change = exclusions.get(key);
      if (!change) return Promise.reject(new Error('No exclusion change to retry.'));
      change.blocked = false; notify(); return saveExclusion(key, change);
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
      const checklist = workflow ? checklists.get(workflow.workflow.id) : undefined;
      const checklistFailures = [...checklists].map(([workflowId, value]) => ({ workflowId, error: value.error }));
      const candidatePrecision = [...candidateDrafts].flatMap(([workflowId, values]) => [...values.keys()].map(key => ({ workflowId, key })));
      const exclusionDrafts = [...exclusions.values()].map(({ pair, reason, error }) => ({ pair, reason, error }));
      return { ok: !unsaved.length && !precisionDrafts.size && !candidatePrecision.length && !candidateErrors.size && !exclusions.size && !settingsError && !checklists.size, candidatePrecision, exclusionDrafts, settingsError, checklistError: checklist?.error ?? '', checklistFailures, precision: [...precisionDrafts.keys()], pairs: unsaved.map(([key]) => { const [tag_a, tag_b] = key.split(':').map(Number); return { tag_a, tag_b }; }) }; },
    refresh() { return enqueue(refresh); },
    subscribe(listener: () => void) { listeners.add(listener); return () => listeners.delete(listener); },
    hasUnsaved() { return !!exclusions.size || !!candidateDrafts.size || !!candidateErrors.size || !!checklists.size || !!precisionDrafts.size || [...drafts.values()].some(value => value.state !== 'Saved' || value.text !== value.saved); },
  };
}
export type MeasurementSession = ReturnType<typeof createMeasurementSession>;
