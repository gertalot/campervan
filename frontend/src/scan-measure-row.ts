import { pairKey, type MeasurementSession } from './scan-measure-session';
import type { Pair } from './scan-workflow-api';

export interface MeasureRowOptions {
  session: MeasurementSession; pair: Pair; estimate(): number | null; highlight(): void; advance(): void;
}
export function createMeasureRow(options: MeasureRowOptions) {
  const { session, pair } = options;
  const element = document.createElement('div'); element.className = 'measurement-row'; element.dataset.pair = pairKey(pair);
  const title = document.createElement('strong'); title.textContent = `Tags ${Math.min(pair.tag_a, pair.tag_b)} ↔ ${Math.max(pair.tag_a, pair.tag_b)}`;
  const estimate = document.createElement('span');
  const label = document.createElement('label'); label.textContent = 'Physical distance ';
  const input = document.createElement('input'); input.type = 'text'; input.inputMode = 'decimal'; input.autocomplete = 'off';
  input.setAttribute('aria-label', `Physical distance between tags ${pair.tag_a} and ${pair.tag_b}`); label.append(input);
  const sigmaLabel = document.createElement('label'); sigmaLabel.textContent = 'Precision (mm) ';
  const sigma = document.createElement('input'); sigma.type = 'number'; sigma.min = '0.01'; sigma.step = 'any'; sigma.placeholder = 'Default'; sigmaLabel.append(sigma);
  const candidateNotice = document.createElement('span');
  const discardCandidate = document.createElement('button'); discardCandidate.type = 'button';
  discardCandidate.textContent = 'Discard candidate precision draft';
  discardCandidate.onclick = () => session.discardCandidatePrecision(pairKey(pair));
  const save = document.createElement('button'); save.type = 'button'; save.textContent = 'Save';
  const highlight = document.createElement('button'); highlight.type = 'button'; highlight.textContent = 'Highlight'; highlight.onclick = options.highlight;
  const excluded = document.createElement('button'); excluded.type = 'button';
  const retryExclusion = document.createElement('button'); retryExclusion.type = 'button'; retryExclusion.textContent = 'Retry exclusion';
  retryExclusion.onclick = () => { void session.retryExclusion(pair).catch(() => undefined); };
  const exclusionError = document.createElement('span'); exclusionError.setAttribute('role', 'alert');
  const status = document.createElement('span'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const error = document.createElement('span'); error.setAttribute('role', 'alert'); error.className = 'measurement-field-error';
  element.append(title, estimate, label, sigmaLabel, candidateNotice, discardCandidate, save, highlight, excluded, retryExclusion, exclusionError, status, error);

  let sigmaWorkflow: string | undefined;
  let editingWorkflow: string | undefined;
  function update() {
    const value = session.draft(pair); if (document.activeElement !== input && input.value !== value.text) input.value = value.text;
    const row = session.document.distances.find(item => pairKey(item) === pairKey(pair));
    const candidateSigma = session.workflow?.workflow.candidate_sigmas[pairKey(pair)];
    const nextWorkflow = row ? undefined : session.workflow?.workflow.id;
    if (document.activeElement !== sigma || nextWorkflow !== sigmaWorkflow) sigma.value = session.precisionDraft(pairKey(pair), !row) ??
      (row?.sigma_m ? String(row.sigma_m * 1000) : candidateSigma ? String(candidateSigma * 1000) : '');
    const candidateDraft = session.precisionDraft(pairKey(pair), true);
    const orphaned = !!row && candidateDraft !== undefined && candidateDraft !== null;
    candidateNotice.textContent = orphaned ? `Unsaved candidate precision: ${candidateDraft || '(blank)'} mm. This pair now has a physical measurement. ${session.candidateError(pairKey(pair)) ?? ''}` : '';
    discardCandidate.hidden = !orphaned;
    sigmaWorkflow = nextWorkflow; sigma.disabled = !row && !session.workflow;
    const scan = options.estimate(); estimate.textContent = scan === null ? 'Scan estimate: unavailable' : `Scan estimate: ${(scan * 1000).toFixed(1)} mm`;
    highlight.disabled = scan === null;
    const exclusion = session.document.excluded_pairs?.find(item => pairKey(item) === pairKey(pair));
    excluded.textContent = exclusion ? `Allow measurement (${exclusion.reason})` : 'Cannot measure this pair…';
    const pendingExclusion = session.exclusionDraft(pair);
    exclusionError.textContent = pendingExclusion?.error ?? ''; retryExclusion.hidden = !pendingExclusion?.blocked;
    if (pendingExclusion) excluded.textContent = pendingExclusion.reason ? `Not saved: ${pendingExclusion.reason}` : 'Allow measurement not saved';
    status.textContent = value.state; error.textContent = value.error || (!row ? session.candidateError(pairKey(pair)) ?? '' : '');
    input.setAttribute('aria-invalid', String(!!value.error));
  }
  input.oninput = () => session.setDraft(pair, input.value);
  input.onkeydown = event => {
    event.stopPropagation(); if (event.isComposing) return;
    if (event.key === 'Enter') { event.preventDefault(); void session.commit(pair).then(ok => { if (ok && session.draft(pair).state === 'Saved') options.advance(); }); }
    if (event.key === 'Escape') { event.preventDefault(); session.setDraft(pair, session.draft(pair).saved); input.value = session.draft(pair).text; input.select(); }
  };
  input.onblur = () => { const value = session.draft(pair); if (!value.error && input.value !== value.saved && input.value.trim()) void session.commit(pair); };
  save.onclick = () => { void session.commit(pair); };
  sigma.onkeydown = event => event.stopPropagation();
  sigma.onfocus = () => { editingWorkflow = session.workflow?.workflow.id; };
  sigma.oninput = () => { editingWorkflow = session.workflow?.workflow.id; const candidate = !session.document.distances.some(item => pairKey(item) === pairKey(pair));
    session.setPrecisionDraft(pairKey(pair), sigma.value, candidate); };
  sigma.onchange = () => {
    const value = sigma.value.trim() ? Number(sigma.value) / 1000 : null;
    if (value !== null && (!Number.isFinite(value) || value <= 0)) { error.textContent = 'Enter a positive precision or leave it blank.'; return; }
    const saved = session.document.distances.some(item => pairKey(item) === pairKey(pair));
    if (!saved && editingWorkflow !== session.workflow?.workflow.id) return;
    const action = saved ? session.configure({ pair_sigmas: { [pairKey(pair)]: value } }) : session.setCandidateSigma(pair, value);
    const submittedWorkflow = session.workflow?.workflow.id;
    void action.then(() => update()).catch(reason => {
      if (saved || session.workflow?.workflow.id === submittedWorkflow) error.textContent = String(reason);
    });
  };
  excluded.onclick = () => {
    const wasExcluded = (session.document.excluded_pairs ?? []).some(item => pairKey(item) === pairKey(pair));
    const reason = wasExcluded ? null : window.prompt('Why is this pair not physically measurable?');
    if (!wasExcluded && !reason?.trim()) return;
    void session.setExclusion(pair, reason?.trim() ?? null).catch(failure => { error.textContent = String(failure); });
  };
  const unsubscribe = session.subscribe(update); update();
  return { element, input, sigma, discardCandidate, retryExclusion, update, destroy: unsubscribe };
}
