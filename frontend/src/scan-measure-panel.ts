import { createSidePanel } from './side-panel';
import { createMeasureRow } from './scan-measure-row';
import { pairKey, type MeasurementSession } from './scan-measure-session';
import { createWorkflow, readWorkflow, readWorkflowArtifact, runWorkflowAction,
  type Pair, type Stage, type WorkflowAction, type MeasurementNetwork, type MeasurementPlan, type PlacementReview,
  type ScanCorrection, type CorrectionMovement, type PlanGain } from './scan-workflow-api';
import { createJobView, jobStatus } from './scan-job-status';
import { readScanImports } from './scan-import-api';
import { reviseTagLayout } from './scan-workflow-api';
import type { ScanTag } from './scan-tags';
interface Capture { id?: string; source_run_id?: string | null; reference_run_id?: string | null; name?: string; display_name?: string; group_name?: string | null; tag_layout_id?: string | null; tags?: ScanTag[] }
interface Host {
  capture(): Capture | undefined; session(): MeasurementSession | null; layoutName(): string;
  error(): string; distance(a: number, b: number): number | null;
  highlight(pair: Pair | null): void;
  highlightTag(id: number | null): void;
  highlightMovements(movements: CorrectionMovement[]): void;
  view(key: string): Promise<void>;
  addCaptures(): void;
  layoutTagIds(layout: string): number[];
  otherUnsaved(): boolean;
}
export function createMeasurePanel(host: Host) {
  const side = createSidePanel({ id: 'measurement-manager', title: 'Review and improve scan', mode: 'nonmodal',
    onClose: () => { host.highlight(null); host.highlightTag(null); host.highlightMovements([]); } });
  side.element.classList.add('scan-measure-panel');
  const stages: { id: Stage; label: string }[] = [
    { id: 'review_capture', label: 'Review capture' }, { id: 'measure', label: 'Measure' },
    { id: 'check_accuracy', label: 'Check accuracy' }, { id: 'update_reconstruction', label: 'Update reconstruction' },
  ];
  const navigation = document.createElement('ol'); navigation.className = 'scan-workflow-stages';
  const stageButtons = new Map<Stage, HTMLButtonElement>();
  for (const stage of stages) { const item = document.createElement('li'); const button = document.createElement('button');
    button.type = 'button'; button.onclick = () => { void changeStage(stage.id); }; item.append(button); navigation.append(item); stageButtons.set(stage.id, button); }
  side.actions.append(navigation);
  const form = document.createElement('form'); form.className = 'measurement-precision';
  const label = document.createElement('label'); label.textContent = 'Typical measuring precision (mm) ';
  const precision = document.createElement('input'); precision.type = 'number'; precision.min = '0.01'; precision.step = 'any'; label.append(precision);
  const save = document.createElement('button'); save.textContent = 'Save precision'; save.type = 'submit'; form.append(label, save); side.actions.append(form);
  const targets = document.createElement('form'); targets.className = 'measurement-precision';
  targets.innerHTML = `<label>Target, longest 95% ellipsoid semi-axis (mm) <input name="target" type="number" min="0.01" step="any"></label>
    <label>Meaningful improvement (mm) <input name="improvement" type="number" min="0.01" step="any"></label><button type="submit">Save targets</button>`;
  side.actions.append(targets); const target = targets.elements.namedItem('target') as HTMLInputElement;
  const improvement = targets.elements.namedItem('improvement') as HTMLInputElement;
  const targetDrafts = new Map<string, { target: string; improvement: string }>();
  targets.oninput = () => { const id = host.session()?.workflow?.workflow.id; if (id) targetDrafts.set(id, { target: target.value, improvement: improvement.value }); };
  targets.onkeydown = event => event.stopPropagation();
  targets.onsubmit = event => { event.preventDefault(); void (async () => {
    const session = host.session(); const workflowId = session?.workflow?.workflow.id;
    const targetValue = Number(target.value); const improvementValue = Number(improvement.value);
    const submitted = workflowId ? targetDrafts.get(workflowId) : undefined;
    if (!session || !workflowId) return;
    const result = await flush(true);
    if (host.session() !== session || session.workflow?.workflow.id !== workflowId) return;
    if (!result?.ok) { status.textContent = 'Save or resolve the highlighted draft first.'; return; }
    if (![targetValue, improvementValue].every(value => Number.isFinite(value) && value > 0)) { status.textContent = 'Enter positive target and improvement values.'; return; }
    try { await session.editMetadata({ target_mm: targetValue, improvement_mm: improvementValue });
      if (targetDrafts.get(workflowId) === submitted) targetDrafts.delete(workflowId); render(); }
    catch (reason) { status.textContent = String(reason); }
  })(); };
  const status = document.createElement('p'); status.setAttribute('role', 'status'); side.status.append(status);
  const checklistFailure = document.createElement('p'); checklistFailure.setAttribute('role', 'alert');
  const retryChecklist = document.createElement('button'); retryChecklist.type = 'button'; retryChecklist.textContent = 'Retry saving checklist progress';
  retryChecklist.onclick = () => { void host.session()?.retryChecklist().catch(() => undefined); };
  side.status.append(checklistFailure, retryChecklist);
  const stageBody = document.createElement('section'); side.body.append(stageBody);
  const stageHeading = document.createElement('h3'); const summary = document.createElement('div');
  const actions = document.createElement('div'); stageBody.append(stageHeading, summary, actions);
  const actionNodes = new Map<string, { button: HTMLButtonElement; reason: HTMLParagraphElement }>();
  const correctionWarning = document.createElement('p');
  const measurementSection = document.createElement('section'); side.body.append(measurementSection);
  const heading = document.createElement('h3'); heading.textContent = 'Measurements'; measurementSection.append(heading);
  const list = document.createElement('div'); measurementSection.append(list);
  const empty = document.createElement('p'); empty.textContent = 'No measured distances saved for this layout.'; measurementSection.append(empty);
  const jobView = createJobView(() => { if (jobId) void jobStatus.refresh(jobId); }); side.body.append(jobView.element); jobView.element.hidden = true;
  let jobId: string | undefined; let unsubscribeJob: (() => void) | undefined;
  let artifactKey = ''; let artifactGeneration = 0; let plan: MeasurementPlan | null = null;
  let stageError = ''; let actionPending = false; let requestedStage: Stage | null = null;
  const revisionDialog = document.createElement('dialog'); revisionDialog.className = 'scan-import-dialog';
  revisionDialog.innerHTML = `<form><h2>Revise tag layout</h2><p>Classify every existing tag. Only measurements between two unchanged tags are copied to the new layout; the capture is not rebound.</p>
    <label>New layout name <input name="name" required maxlength="120"></label><div data-tags></div>
    <label>Additional tag IDs (comma-separated) <input name="added"></label>
    <p data-summary></p><p role="alert"></p><button type="submit">Create revised layout</button><button type="button" data-cancel>Cancel</button></form>`;
  document.body.append(revisionDialog);
  revisionDialog.querySelector<HTMLButtonElement>('[data-cancel]')!.onclick = () => revisionDialog.close();
  async function reviseLayout() {
    const session = host.session(); const capture = host.capture(); if (!session || !capture?.tag_layout_id) return;
    const result = await flush(); if (!result?.ok) { status.textContent = 'Save or resolve the highlighted draft before revising the layout.'; return; }
    try {
      const layouts = await readScanImports(); const layout = layouts.layouts.find(item => item.id === capture.tag_layout_id);
      if (!layout) throw new Error('This tag layout is unavailable.');
      const ids = new Set([...host.layoutTagIds(capture.tag_layout_id), ...(capture.tags ?? []).map(tag => tag.id), ...session.document.distances.flatMap(pair => [pair.tag_a, pair.tag_b]),
        ...(session.document.excluded_pairs ?? []).flatMap(pair => [pair.tag_a, pair.tag_b])]);
      const form = revisionDialog.querySelector<HTMLFormElement>('form')!; const tags = form.querySelector<HTMLElement>('[data-tags]')!; tags.replaceChildren();
      for (const id of [...ids].sort((a, b) => a - b)) { const label = document.createElement('label'); label.textContent = `Tag ${id} `;
        const select = document.createElement('select'); select.name = String(id); select.required = true;
        select.add(new Option('Choose classification', '')); for (const value of ['unchanged', 'moved', 'removed']) select.add(new Option(value, value)); label.append(select); tags.append(label); }
      const added = form.elements.namedItem('added') as HTMLInputElement; const name = form.elements.namedItem('name') as HTMLInputElement;
      name.value = `${layout.name} revised`; added.value = ''; const summary = form.querySelector<HTMLElement>('[data-summary]')!;
      const alert = form.querySelector<HTMLElement>('[role=alert]')!; alert.textContent = '';
      const describe = () => { const counts = ['unchanged', 'moved', 'removed'].map(value => `${value}: ${[...tags.querySelectorAll('select')].filter(item => item.value === value).length}`);
        summary.textContent = `${counts.join(' · ')} · added: ${added.value || 'none'}`; }; form.oninput = describe; describe();
      form.onsubmit = event => { event.preventDefault(); const groups = { unchanged: [] as number[], moved: [] as number[], removed: [] as number[], added: [] as number[] };
        for (const select of tags.querySelectorAll('select')) groups[select.value as 'unchanged' | 'moved' | 'removed'].push(Number(select.name));
        groups.added = added.value.trim() ? added.value.split(',').map(value => Number(value.trim())) : [];
        if (groups.added.some(id => !Number.isInteger(id) || id <= 0)) { alert.textContent = 'Enter positive whole-number tag IDs separated by commas.'; return; }
        void reviseTagLayout(layout.id, { name: name.value.trim(), tag_family: '36h11', tag_size_mm: layout.tag_size_mm,
          revision: session.document.revision, ...groups }).then(created => { revisionDialog.close(); status.textContent = `Created ${created.name}. Choose it when processing replacement captures.`; })
          .catch(reason => { alert.textContent = String(reason); }); };
      revisionDialog.showModal();
    } catch (reason) { status.textContent = String(reason); }
  }
  let current: MeasurementSession | null = null; let unsubscribe: (() => void) | undefined;
  let identity = ''; let generation = 0; let measuredRevision = -1;
  function ownsWorkflow(session: MeasurementSession, workflowId: string, source: string, token: number) {
    const capture = host.capture();
    return token === generation && host.session() === session && session.workflow?.workflow.id === workflowId
      && (capture?.reference_run_id ?? capture?.source_run_id ?? capture?.id) === source;
  }
  async function changeStage(stage: Stage, isCurrent = () => true) {
    const session = host.session(); if (!session?.workflow) return;
    host.highlight(null); host.highlightTag(null); host.highlightMovements([]);
    try { await session.editMetadata({ stage }); } catch (reason) { if (isCurrent()) { stageError = String(reason); render(); } }
  }
  function watchJob(session: MeasurementSession, id: string) {
    const view = session.workflow; const job = view?.jobs.find(item => item.id === id); if (!view || !job || jobId === id) return;
    const token = generation; const isCurrent = () => ownsWorkflow(session, view.workflow.id, view.workflow.source_run_id, token);
    jobId = id; unsubscribeJob?.(); jobStatus.publish(job); jobView.element.hidden = false;
    unsubscribeJob = jobStatus.subscribe(id, update => { if (!isCurrent()) return; jobView.update(update);
      if (update.state !== 'processing') void readWorkflow(view.workflow.id).then(latest => {
        if (isCurrent() && session.workflow && latest.revision >= session.workflow.revision) session.bindWorkflow(latest);
      }).catch(reason => { if (isCurrent()) { stageError = String(reason); render(); } }); });
  }
  async function dispatch(action: WorkflowAction) {
    const session = host.session(); const bound = session?.workflow; if (!session || !bound || actionPending) return;
    const token = generation; const isCurrent = () => ownsWorkflow(session, bound.workflow.id, bound.workflow.source_run_id, token);
    if (!isCurrent()) return;
    const result = await flush(false, isCurrent); if (!isCurrent()) return;
    if (!result?.ok) { status.textContent = 'Save or resolve the highlighted draft before continuing.'; return; }
    if (session.document.default_sigma_m == null) {
      const value = Number(precision.value) / 1000;
      if (!Number.isFinite(value) || value <= 0) { precision.setAttribute('aria-invalid', 'true'); status.textContent = 'Enter a positive precision.'; precision.focus(); return; }
      try { await session.configure({ default_sigma_m: value }); } catch (reason) { if (isCurrent()) { status.textContent = String(reason); precision.focus(); } return; }
      if (!isCurrent()) return;
    }
    const view = session.workflow; if (!view) return;
    actionPending = true; stageError = ''; render();
    try {
      const started = await runWorkflowAction(view.workflow.id, action, view.revision, session.document.revision);
      if (!isCurrent()) return;
      const fresh = await readWorkflow(view.workflow.id);
      if (!isCurrent()) return;
      session.bindWorkflow(fresh);
      watchJob(session, started.id);
    } catch (reason) { if (isCurrent()) stageError = String(reason); }
    finally { actionPending = false; render(); }
  }
  async function bindWorkflow(session: MeasurementSession, source: string, layout: string, token: number) {
    try { const view = await createWorkflow(source, layout); if (token === generation && current === session) { session.bindWorkflow(view);
      if (requestedStage) { const stage = requestedStage; requestedStage = null; void changeStage(stage); } } }
    catch (reason) { if (token === generation) status.textContent = String(reason); }
  }
  const rows = new Map<string, ReturnType<typeof createMeasureRow>>();
  function describeNetwork(node: HTMLElement, network: MeasurementNetwork) {
    const sections = [
      ['Completeness', `${network.completeness.status} · ${network.completeness.active_measurement_count} active measurements · ${network.completeness.remaining_motions} remaining motions · ${network.completeness.inactive_measurement_count} unavailable measurements`],
      ['Consistency', `${network.consistency.status} · ${network.consistency.redundancy} redundant measurements · ${network.consistency.downweighted_pairs} downweighted pairs`],
      ['Uncertainty', `${network.uncertainty.status} · ${network.uncertainty.qualification}`],
    ];
    for (const [title, text] of sections) { const heading = document.createElement('h4'); heading.textContent = title;
      const paragraph = document.createElement('p'); paragraph.textContent = text; node.append(heading, paragraph); }
    const details = document.createElement('details'); const label = document.createElement('summary'); label.textContent = 'Details and assumptions';
    const content = document.createElement('pre'); content.textContent = JSON.stringify({ completeness: network.completeness,
      consistency: network.consistency, uncertainty: network.uncertainty, solver: network.solver, warnings: network.warnings }, null, 2);
    details.append(label, content); node.append(details);
  }
  function describePlan(node: HTMLElement, payload: MeasurementPlan, artifactId: string, session: MeasurementSession,
    workflowId: string, source: string, token: number) {
    const intro = document.createElement('p'); intro.textContent = `Target: ${payload.target_mm} mm longest 95% ellipsoid semi-axis · Meaningful improvement: ${payload.improvement_mm} mm · ${payload.stop_reason}`; node.append(intro);
    const notes = document.createElement('p'); notes.textContent = payload.notes.join(' · '); node.append(notes);
    const batch = document.createElement('button'); batch.type = 'button'; batch.textContent = 'Add recommended checklist';
    batch.disabled = !payload.recommended_pairs.length; batch.onclick = () => { void (async () => {
      const isCurrent = () => ownsWorkflow(session, workflowId, source, token); if (!isCurrent()) return;
      const result = await flush(false, isCurrent); if (!isCurrent()) return;
      if (!result?.ok) { status.textContent = 'Save or resolve the highlighted draft first.'; return; }
      const batches = session.checklistDraft()?.batches ?? session.workflow?.workflow.checklist_batches ?? [];
      if (batches.some(item => item.producing_artifact_id === artifactId)) return;
      void session.setChecklist([...batches, { id: crypto.randomUUID(), kind: payload.mode, ordered_pairs: payload.recommended_pairs,
        current_pair: payload.recommended_pairs[0] ?? null, producing_artifact_id: artifactId }]).catch(reason => { if (isCurrent()) { stageError = String(reason); render(); } });
    })(); }; node.append(batch);
    const list = document.createElement('ul');
    const gainText = (gain: PlanGain | null) => {
      if (!gain) return 'Unknown';
      const number = (value: number | null) => value === null ? 'Unknown' : value.toFixed(2);
      return `rank reduction ${gain.rank_reduction}, connectivity reduction ${gain.connectivity_reduction}, null-mode energy ${number(gain.null_mode_energy)}, information gain ${number(gain.information_gain)}, largest local tag reduction ${number(gain.max_tag_reduction_mm)} mm${gain.most_improved_tag_id === null ? '' : ` (tag ${gain.most_improved_tag_id})`}, global worst-tag reduction ${number(gain.global_worst_reduction_mm)} mm`;
    };
    for (const pair of payload.rows) { const item = document.createElement('li');
      const access = pair.manual_exclusion ? `Manually excluded: ${pair.manual_exclusion}` : pair.check_access ? `Check access: ${pair.clearance_reason}` : pair.clearance_reason;
      item.textContent = `Tags ${pair.tag_a} ↔ ${pair.tag_b} · ${pair.state}${pair.recommended_order === null ? '' : ` · recommended ${pair.recommended_order}`} · Scan estimate ${(pair.estimate_m * 1000).toFixed(1)} mm · ${access} · ${pair.reason}`;
      if (pair.useful) { const gain = document.createElement('p'); gain.textContent = `Baseline gain: ${gainText(pair.baseline_gain)}. Marginal gain: ${gainText(pair.marginal_gain)}.`; item.append(gain); }
      list.append(item); }
    node.append(list);
  }
  function describePlacement(node: HTMLElement, payload: PlacementReview) {
    const availability = document.createElement('p'); availability.textContent = 'Optional reviewed scene context: Unavailable unless supplied by the scene. Placement advice does not constitute semantic review.'; node.append(availability);
    for (const tag of payload.tags) { const row = document.createElement('p'); row.textContent = `Tag ${tag.tag_id}: ${tag.recommendation.replace('_', ' ')} · ${tag.reason}`;
      const highlight = document.createElement('button'); highlight.type = 'button'; highlight.textContent = 'Highlight';
      highlight.onclick = () => { host.highlightTag(tag.tag_id); host.highlight(tag.useful_connections.length ? { tag_a: tag.tag_id, tag_b: tag.useful_connections[0] } : null); }; row.append(' ', highlight); node.append(row); }
    for (const note of payload.notes) { const p = document.createElement('p'); p.textContent = note; node.append(p); }
  }
  function describeCorrection(node: HTMLElement, payload: ScanCorrection) {
    const introduction = document.createElement('p'); introduction.textContent = `Registration: ${payload.registration.status} · ${payload.registration.reasons.join(' · ')} · ${payload.inactive_measurement_count} inactive measurements`; node.append(introduction);
    const heading = document.createElement('h4'); heading.textContent = 'Proposed tag movements'; node.append(heading);
    for (const movement of payload.movements) { const row = document.createElement('p');
      row.textContent = `Tag ${movement.id}: ${(movement.distance_m * 1000).toFixed(1)} mm${movement.scan_dependent ? ' · scan-dependent' : ''} `;
      const highlight = document.createElement('button'); highlight.type = 'button'; highlight.textContent = 'Highlight movement';
      highlight.onclick = () => host.highlightMovements([movement]); row.append(highlight); node.append(row); }
    const context = document.createElement('h4'); context.textContent = 'Optional context'; node.append(context);
    if (!payload.context.length) { const p = document.createElement('p'); p.textContent = 'Unavailable: no reviewed context supplied.'; node.append(p); }
    for (const item of payload.context) { const p = document.createElement('p'); p.textContent = `${item.kind ?? 'Relationship'} · ${item.active ? 'active' : 'inactive'}${item.reason ? ` · ${item.reason}` : ''}`; node.append(p); }
    const cleanup = document.createElement('p'); cleanup.textContent = `Cleanup: ${payload.cleanup.note}`; node.append(cleanup);
  }
  function showArtifact(session: MeasurementSession, kind: 'measurement_network' | 'measurement_plan' | 'placement_review' | 'scan_correction') {
    const view = session.workflow; const id = view?.workflow.artifact_refs[kind];
    const state = view?.artifacts[kind];
    const key = `${view?.workflow.id ?? ''}:${kind}:${id ?? ''}:${state?.status ?? ''}:${state?.reasons.join('|') ?? ''}`;
    if (key === artifactKey) return;
    artifactKey = key; const token = ++artifactGeneration; const workflowGeneration = generation; summary.replaceChildren(); if (kind === 'measurement_plan') plan = null;
    const info = document.createElement('p');
    info.textContent = state ? `${state.status}: ${state.reasons.join(' · ')}` : 'No report yet.'; summary.append(info);
    if (kind === 'placement_review') { const capture = host.capture(); const source = document.createElement('p');
      source.textContent = `Captured tags: ${(capture?.tags ?? []).map(tag => tag.id).join(', ') || 'none available'}. Optional reviewed context: ${view?.workflow.source_binding ? 'available' : 'unavailable'}.`;
      summary.append(source); }
    if (!view || !id) return;
    void readWorkflowArtifact(view.workflow.id, id).then(({ artifact, status: freshness }) => {
      if (token !== artifactGeneration) return;
      info.textContent = `${freshness.status}${freshness.reasons.length ? `: ${freshness.reasons.join(' · ')}` : ''}`;
      const artifactBody = document.createElement('div'); summary.append(artifactBody);
      if (artifact.kind === 'measurement_network') describeNetwork(artifactBody, artifact.payload);
      else if (artifact.kind === 'measurement_plan') { plan = artifact.payload; describePlan(artifactBody, artifact.payload, artifact.id, session,
        view.workflow.id, view.workflow.source_run_id, workflowGeneration); render(); }
      else if (artifact.kind === 'placement_review') describePlacement(artifactBody, artifact.payload);
      else if (artifact.kind === 'scan_correction') describeCorrection(artifactBody, artifact.payload);
      else { const details = document.createElement('details'); const label = document.createElement('summary'); label.textContent = 'Report details';
        const content = document.createElement('pre'); content.textContent = JSON.stringify(artifact.payload, null, 2); details.append(label, content); artifactBody.append(details); }
    }).catch(reason => { if (token === artifactGeneration) info.textContent = String(reason); });
  }
  function render() {
    const capture = host.capture(); const session = host.session();
    side.context.textContent = [capture?.group_name ?? 'Ungrouped', capture?.display_name ?? capture?.name ?? 'No result selected', host.layoutName()].filter(Boolean).join(' · ');
    const source = capture?.reference_run_id ?? capture?.source_run_id ?? capture?.id;
    const nextIdentity = `${source ?? ''}:${capture?.tag_layout_id ?? ''}`;
    const changed = nextIdentity !== identity || session !== current;
    if (session !== current) {
      unsubscribe?.(); rows.forEach(row => row.destroy()); rows.clear(); list.replaceChildren(); current = session;
      unsubscribe = session?.subscribe(render);
      precision.value = session?.precisionDraft('default') ?? String((session?.document.default_sigma_m ?? .003) * 1000);
    }
    if (changed) { identity = nextIdentity; generation++; plan = null; artifactKey = ''; unsubscribeJob?.(); unsubscribeJob = undefined;
      jobId = undefined; jobView.element.hidden = true; session?.bindWorkflow(null);
      if (session && source && capture?.tag_layout_id) void bindWorkflow(session, source, capture.tag_layout_id, generation); }
    if (session && session.document.revision !== measuredRevision) {
      measuredRevision = session.document.revision; const bound = session.workflow;
      if (bound) void readWorkflow(bound.workflow.id).then(latest => {
        if (session.workflow?.workflow.id === bound.workflow.id && latest.revision >= session.workflow.revision) session.bindWorkflow(latest);
      }).catch(reason => { stageError = String(reason); });
    }
    status.textContent = stageError || host.error();
    const checklist = session?.checklistDraft();
    checklistFailure.textContent = checklist?.error ?? ''; retryChecklist.hidden = !checklist?.blocked;
    const view = session?.workflow; const stage = view?.workflow.stage ?? 'review_capture';
    const activeJob = view?.jobs.find(job => job.state === 'processing');
    if (session && activeJob) watchJob(session, activeJob.id);
    for (const item of stages) { const button = stageButtons.get(item.id)!;
      button.textContent = `${item.label} · ${view?.stages[item.id] ?? 'Not started'}`;
      if (item.id === stage) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
      button.disabled = !view; }
    stageHeading.textContent = stages.find(item => item.id === stage)!.label;
    form.hidden = false; targets.hidden = stage !== 'measure'; measurementSection.hidden = stage !== 'measure';
    if (view && document.activeElement !== target && document.activeElement !== improvement) {
      const draft = targetDrafts.get(view.workflow.id);
      target.value = draft?.target ?? String(view.workflow.target_mm); improvement.value = draft?.improvement ?? String(view.workflow.improvement_mm);
    }
    const definitions: Record<Stage, { action: WorkflowAction; label: string }[]> = {
      review_capture: [{ action: 'review-placement', label: 'Review placement' }],
      measure: [{ action: 'plan-measurements', label: 'Generate checklist' }],
      check_accuracy: [{ action: 'check-measurements', label: 'Check measurements' }, { action: 'suggest-more', label: 'Suggest more' }],
      update_reconstruction: [{ action: 'preview-correction', label: 'Preview corrections' }, { action: 'update-mesh', label: 'Update mesh' }],
    };
    const desired: { key: string; label: string; disabled: boolean; reason?: string; run(): void }[] = definitions[stage].map(definition => {
      const eligibility = view?.actions[definition.action]; return { key: definition.action, label: definition.label,
        disabled: actionPending || !eligibility?.available, reason: eligibility?.reasons.join(' · ') ?? 'Workflow unavailable',
        run: () => { void dispatch(definition.action); } };
    });
    if (stage === 'review_capture') desired.push(
      { key: 'continue', label: 'Continue to measurements', disabled: !view, run: () => { void changeStage('measure'); } },
      { key: 'captures', label: 'Add replacement captures…', disabled: false, run: host.addCaptures },
      { key: 'revise', label: 'Revise tag layout…', disabled: !view, run: () => { void reviseLayout(); } });
    if (stage === 'update_reconstruction' && view) {
      desired.push({ key: 'original', label: 'Show original', disabled: false, run: () => { void host.view(`run:${view.workflow.source_run_id}`); } });
      if (view.workflow.corrected_run_id) desired.push({ key: 'corrected', label: 'Show corrected result', disabled: false,
        run: () => { void host.view(`run:${view.workflow.corrected_run_id}`); } });
    }
    const ordered: HTMLElement[] = [];
    for (const item of desired) {
      let nodes = actionNodes.get(item.key);
      if (!nodes) { const button = document.createElement('button'); button.type = 'button'; const reason = document.createElement('p');
        nodes = { button, reason }; actionNodes.set(item.key, nodes); }
      const { button, reason } = nodes; button.textContent = item.label; button.setAttribute('aria-disabled', String(item.disabled));
      button.title = item.reason ?? ''; button.onclick = () => { if (!item.disabled) item.run(); };
      reason.textContent = item.reason ?? ''; reason.hidden = !item.reason; ordered.push(button, reason);
    }
    if (stage === 'update_reconstruction') { correctionWarning.textContent = 'Corrections can be best effort. Scan-dependent or ambiguous positions require review before updating the mesh.'; ordered.push(correctionWarning); }
    for (const child of [...actions.children]) if (!ordered.includes(child as HTMLElement)) child.remove();
    ordered.forEach((node, index) => { if (actions.children[index] !== node) actions.insertBefore(node, actions.children[index] ?? null); });
    if (session && view) showArtifact(session, stage === 'review_capture' ? 'placement_review' : stage === 'measure' ? 'measurement_plan' : stage === 'check_accuracy' ? 'measurement_network' : 'scan_correction');
    else { artifactKey = ''; ++artifactGeneration; summary.textContent = 'Select a capture with a tag layout.'; }
    if (!session) { empty.hidden = false; return; }
    const batches = session.checklistDraft()?.batches ?? session.workflow?.workflow.checklist_batches ?? [];
    const pairs: Pair[] = []; const seen = new Set<string>();
    for (const pair of [...batches.flatMap(batch => batch.ordered_pairs), ...(plan?.rows ?? []), ...session.document.distances]) {
      const key = pairKey(pair); if (!seen.has(key)) { seen.add(key); pairs.push(pair); }
    }
    const wanted = new Set(pairs.map(pairKey));
    for (const [key, row] of rows) if (!wanted.has(key)) { row.destroy(); row.element.remove(); rows.delete(key); }
    for (const [position, pair] of pairs.entries()) {
      const key = pairKey(pair); let row = rows.get(key);
      if (!row) {
        row = createMeasureRow({ session, pair, estimate: () => host.distance(pair.tag_a, pair.tag_b),
          highlight: () => host.highlight(pair), advance: () => {
            const all = [...list.children].map(element => rows.get((element as HTMLElement).dataset.pair ?? '')).filter((item): item is ReturnType<typeof createMeasureRow> => !!item);
            const index = all.findIndex(item => item.element.dataset.pair === key);
            const next = all.slice(index + 1).find(item => { const [tag_a, tag_b] = item.element.dataset.pair!.split(':').map(Number);
              const value = session.draft({ tag_a, tag_b }); return !item.input.disabled && (!value.saved || value.state !== 'Saved'); });
            next?.input.focus();
          } });
        row.input.addEventListener('focus', () => {
          const batches = session.checklistDraft()?.batches ?? session.workflow?.workflow.checklist_batches ?? [];
          const updated = batches.map(batch => batch.ordered_pairs.some(item => pairKey(item) === key)
            && (!batch.current_pair || pairKey(batch.current_pair) !== key) ? { ...batch, current_pair: pair } : batch);
          if (updated.some((batch, index) => batch !== batches[index])) {
            void session.setChecklist(updated).catch(reason => { status.textContent = String(reason); });
          }
        });
        const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove';
        remove.onclick = () => { void session.remove(pair).catch(reason => { status.textContent = String(reason); }); }; row.element.append(remove);
        rows.set(key, row);
      } else row.update();
      const available = host.distance(pair.tag_a, pair.tag_b) !== null;
      row.input.disabled = !available; row.input.title = available ? '' : 'Unavailable: one or both tags are absent from this capture.';
      if (list.children[position] !== row.element) list.insertBefore(row.element, list.children[position] ?? null);
    }
    empty.hidden = !!rows.size;
  }
  precision.oninput = () => { precision.removeAttribute('aria-invalid'); host.session()?.setPrecisionDraft('default', precision.value); };
  precision.onkeydown = event => event.stopPropagation();
  form.onsubmit = event => { event.preventDefault(); const session = host.session(); const value = Number(precision.value) / 1000;
    if (!session || !Number.isFinite(value) || value <= 0) { precision.setAttribute('aria-invalid', 'true'); status.textContent = 'Enter a positive precision.'; precision.focus(); return; }
    void session.configure({ default_sigma_m: value }).catch(reason => { status.textContent = String(reason); }); };
  async function flush(ignoreTargets = false, isCurrent = () => true) { const result = await host.session()?.flush();
    if (!isCurrent()) return;
    if (result && host.otherUnsaved()) { status.textContent = 'Return to the other layout with unsaved measurements.'; return { ...result, ok: false }; }
    if (result && (!result.ok || (!ignoreTargets && targetDrafts.size)) && host.session()?.workflow?.workflow.stage !== 'measure') await changeStage('measure', isCurrent);
    if (!isCurrent()) return;
    if (result && !ignoreTargets && targetDrafts.size) {
      if (host.session()?.workflow && targetDrafts.has(host.session()!.workflow!.workflow.id)) target.focus();
      else status.textContent = 'Return to the source with unsaved targets.';
      return { ...result, ok: false };
    }
    if (result && !result.ok) { if (result.exclusionDrafts.length) rows.get(pairKey(result.exclusionDrafts[0].pair))?.retryExclusion.focus(); else if (result.checklistError) retryChecklist.focus(); else if (result.pairs.length) rows.get(pairKey(result.pairs[0]))?.input.focus(); else if (result.precision[0] && result.precision[0] !== 'default') rows.get(result.precision[0])?.sigma.focus(); else if (result.candidatePrecision.length) {
      const candidate = result.candidatePrecision.find(item => item.workflowId === host.session()?.workflow?.workflow.id);
      if (candidate) { const row = rows.get(candidate.key); if (row && !row.discardCandidate.hidden) row.discardCandidate.focus(); else row?.sigma.focus(); } else status.textContent = 'Return to the source with unsaved candidate precision.';
    } else precision.focus(); } return result; }
  return { open() { side.open(); render(); }, openReview() { side.open(); render();
      if (host.session()?.workflow) void changeStage('review_capture'); else requestedStage = 'review_capture'; },
    refresh: render, render, hide: () => side.close(), flush, hasUnsaved: () => !!targetDrafts.size };
}
