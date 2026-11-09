/** Measurement management content in the shared side-panel shell. Tape entry remains in scan-measure. */
import { ApiError } from './api';
import { createSidePanel } from './side-panel';
import { configureMeasurements, type MeasurementDocument, type DistanceMeasurement } from './scan-measurements-api';
import { analyseMeasurements, readAnalysis, applyAnalysis, revertAnalysis, suggestMeasurements,
  type AnalysisStatus, type SuggestedPair } from './scan-analysis-api';
import type { ScanTag } from './scan-tags';
interface Capture {
  id?: string; name?: string; display_name?: string; group_name?: string | null;
  tag_layout_id?: string | null; analysis_id?: string | null; tags?: ScanTag[];
}
interface Host {
  capture(): Capture | undefined; document(): MeasurementDocument | null; layoutName(): string;
  busy(): boolean; error(): string;
  canSwitch(): boolean;
  distance(a: number, b: number): number | null;
  selectPair(a: number, b: number): void;
  remove(record: DistanceMeasurement): Promise<void>;
  refresh(): Promise<void>;
  preview(result: AnalysisStatus['result']): void;
  highlight(pair: SuggestedPair | null): void;
  view(key: string): Promise<void>;
}
const mm = (m: number) => `${(m * 1000).toFixed(1)} mm`;
const DEFAULT_PRECISION_MM = 3;
function node<K extends keyof HTMLElementTagNameMap>(tag: K, text?: string) {
  const element = document.createElement(tag); if (text !== undefined) element.textContent = text; return element;
}
function button(text: string, action: () => void) {
  const element = node('button', text); element.type = 'button'; element.onclick = action; return element;
}
export function createMeasurePanel(host: Host) {
  const side = createSidePanel({ id: 'measurement-manager', title: 'Manage measurements', mode: 'nonmodal',
    onClose: () => { host.preview(null); host.highlight(null); } });
  side.element.classList.add('scan-measure-panel');
  const actions = node('div'); actions.className = 'measurement-actions';
  const analyse = button('Analyse uncertainty', () => { void runAnalysis(); });
  const suggest = button('Suggest more', () => { void suggestMore(); });
  const apply = button('Apply', () => { void applyPreview(); });
  const revert = button('Revert', () => { void revertPreview(); }); actions.append(analyse, suggest, apply, revert);
  const showCorrected = button('Show corrected result', () => {
    const key = snapshot?.accepted_job?.result_key; if (key) void host.view(key).catch(error);
  });
  showCorrected.hidden = true; actions.append(showCorrected);
  const form = node('form'); form.className = 'measurement-precision';
  const label = node('label', 'Typical measuring precision (mm) '); const precision = node('input');
  precision.type = 'number'; precision.min = '0.01'; precision.step = 'any'; precision.required = true;
  precision.value = String(DEFAULT_PRECISION_MM);
  const precisionError = node('span'); precisionError.id = 'measurement-precision-error';
  precisionError.className = 'measurement-field-error'; precisionError.setAttribute('role', 'alert');
  precision.setAttribute('aria-describedby', precisionError.id);
  precision.setAttribute('aria-label', 'Typical measuring precision in millimetres, one standard deviation'); label.append(precision);
  const savePrecision = node('button', 'Save precision'); savePrecision.type = 'submit';
  form.noValidate = true; form.append(label, savePrecision, precisionError);
  const help = node('p', 'Default precision: 3 mm; adjust for your measuring method. Precision is one standard deviation. Analysis reports approximate 95% uncertainty intervals. Entered distances are never replaced by fitted values.');
  help.className = 'measurement-help';
  const thresholdLabel = node('label', 'Minimum predicted improvement (mm) '); const threshold = node('input');
  threshold.type = 'number'; threshold.min = '0.01'; threshold.step = 'any'; threshold.value = '5'; thresholdLabel.append(threshold);
  const thresholdError = node('span'); thresholdError.id = 'measurement-threshold-error';
  thresholdError.className = 'measurement-field-error'; thresholdError.setAttribute('role', 'alert');
  threshold.setAttribute('aria-describedby', thresholdError.id);
  side.actions.append(actions, form, help, thresholdLabel, thresholdError);
  const status = node('p'); const failure = node('p'); failure.setAttribute('role', 'alert');
  const measurementFailure = node('p'); measurementFailure.setAttribute('role', 'alert');
  const logDetails = node('details'); logDetails.append(node('summary', 'Show analysis / rebuild log')); const log = node('pre'); logDetails.append(log);
  side.status.append(status, failure, measurementFailure, logDetails);
  let snapshot: AnalysisStatus | undefined;
  let analysisId: string | undefined;
  let identity = '';
  let busy = false;
  let generation = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let wantSuggestions = false;
  const opened = new Set<string>();
  const drafts = new Map<string, string>();
  const expandedSuggestions = new Set<string>();
  let filter = 'no_obstruction_detected';
  let lastRevision = -1;
  function error(reason: unknown) { failure.textContent = reason instanceof Error ? reason.message : String(reason); }
  function doc() { return host.document(); }
  function matches() { return snapshot?.result?.measurement_revision === doc()?.revision && !snapshot?.stale; }
  function working() { return [snapshot?.job, snapshot?.accepted_job, snapshot?.suggestions_job].some(job => job?.state === 'processing'); }
  function precisionDirty() {
    const document = doc();
    if ((precision.value.trim() ? Number(precision.value)/1000 : null) !== (document?.default_sigma_m ?? null)) return true;
    return [...drafts].some(([key, value]) => {
      const record = document?.distances.find(row => `${row.tag_a}:${row.tag_b}` === key);
      return (value.trim() ? Number(value)/1000 : null) !== (record?.sigma_m ?? null);
    });
  }
  function updateButtons() {
    const usable = !!host.capture()?.id && !!doc() && host.capture()?.tag_layout_id === doc()?.tag_layout_id;
    analyse.disabled = !usable || busy || host.busy() || working();
    suggest.disabled = analyse.disabled;
    apply.hidden = !snapshot?.result; revert.hidden = !snapshot?.result;
    const published = snapshot?.acceptance?.active && snapshot.accepted_job?.state === 'completed' && !!snapshot.accepted_job.result_key;
    apply.disabled = busy || host.busy() || working() || !matches() || !!published;
    apply.textContent = snapshot?.acceptance?.active && !published ? 'Retry rebuild' : 'Apply';
    revert.disabled = busy || (!snapshot?.result && !snapshot?.acceptance);
    showCorrected.hidden = !snapshot?.accepted_job?.result_key || snapshot?.acceptance?.result_run_id === host.capture()?.id;
    threshold.disabled = busy || working();
    savePrecision.disabled = !usable || busy || host.busy() || working();
  }
  function preview() {
    if (!side.isOpen || !matches() || precisionDirty()) host.highlight(null);
    host.preview(side.isOpen && matches() && !precisionDirty() && snapshot?.result?.run_id === host.capture()?.id ? snapshot?.result ?? null : null);
  }
  function messages() {
    const jobs = [snapshot?.job, snapshot?.accepted_job, snapshot?.suggestions_job].filter(job => !!job);
    const running = jobs.find(job => job?.state === 'processing');
    const failed = [...jobs].reverse().find(job => job?.state === 'failed' || job?.state === 'interrupted');
    let message = running ? `${running.name} · ${running.stage}`
      : precisionDirty() ? 'Analyse or Suggest more will save your precision settings before continuing.'
      : snapshot?.stale || snapshot?.result && !matches() ? 'Measurements changed. Analyse again before Apply or Suggest more.'
      : snapshot?.acceptance?.active && snapshot.acceptance.result_run_id === host.capture()?.id ? 'Applied reconstruction · original measurements retained.'
      : snapshot?.result ? 'Analysis ready · original surface remains unchanged until Apply rebuilds it.' : 'Ready to analyse the measurement network.';
    if (failed) message = `${failed.name}: ${failed.error ?? failed.state}`;
    if (status.textContent !== message) status.textContent = message;
    measurementFailure.textContent = host.error();
    log.textContent = (running ?? failed ?? snapshot?.accepted_job ?? snapshot?.job)?.log_tail ?? '';
    logDetails.hidden = !snapshot;
    updateButtons(); preview();
  }
  function measure(a: number, b: number) { side.close({ restoreFocus: false }); host.selectPair(a, b); }
  function validateField(input: HTMLInputElement, message: HTMLElement, title: string): boolean {
    const valid = input.value.trim() !== '' && Number.isFinite(Number(input.value)) && Number(input.value) > 0;
    input.setAttribute('aria-invalid', String(!valid));
    message.textContent = valid ? '' : `Enter ${title} greater than zero.`;
    return valid;
  }
  async function saveSettings(): Promise<boolean> {
    const document = doc(); if (!document || busy) return false;
    const context = generation; const submittedPrecision = precision.value;
    const value = Number(precision.value)/1000;
    if (!validateField(precision, precisionError, 'measuring precision')) { precision.focus(); return false; }
    const overrides: Record<string, number | null> = {};
    for (const [key, text] of drafts) {
      const sigma = text.trim() ? Number(text)/1000 : null;
      if (sigma !== null && (!Number.isFinite(sigma) || sigma <= 0)) {
        const input = [...side.body.querySelectorAll<HTMLInputElement>('input[data-pair]')].find(field => field.dataset.pair === key);
        input?.setAttribute('aria-invalid', 'true'); input?.focus();
        error(new Error(`Enter positive precision for tags ${key.replace(':', '–')}, or leave it blank to use the default.`)); return false;
      }
      overrides[key] = sigma;
    }
    busy = true; failure.textContent = ''; updateButtons();
    try {
      await configureMeasurements(document, value, overrides); drafts.clear();
      await host.refresh(); host.preview(null); render();
      return true;
    } catch (reason) {
      error(reason);
      if (reason instanceof ApiError && reason.status === 409) {
        await host.refresh(); if (context === generation) precision.value = submittedPrecision;
      }
      return false;
    }
    finally { busy = false; updateButtons(); }
  }
  form.onsubmit = event => { event.preventDefault(); void saveSettings(); };
  precision.oninput = () => { validateField(precision, precisionError, 'measuring precision'); messages(); };
  threshold.oninput = () => { validateField(threshold, thresholdError, 'an improvement threshold'); };
  async function ensurePrecision() { return precisionDirty() ? saveSettings() : validateField(precision, precisionError, 'measuring precision'); }
  async function runAnalysis() {
    if (busy || host.busy()) return;
    const context = generation;
    if (!await ensurePrecision() || context !== generation) return;
    const document = doc(); const capture = host.capture(); if (!document || !capture?.id) return;
    busy = true; failure.textContent = ''; const token = generation; updateButtons();
    try {
      const response = await analyseMeasurements(capture.id, document);
      if (token !== generation) return;
      analysisId = response.id; snapshot = undefined; await poll(token);
    } catch (reason) { error(reason); wantSuggestions = false; }
    finally { busy = false; updateButtons(); }
  }
  async function suggestMore() {
    if (busy || host.busy()) return;
    if (!validateField(threshold, thresholdError, 'an improvement threshold')) { threshold.focus(); return; }
    const context = generation;
    if (!await ensurePrecision() || context !== generation) { wantSuggestions = false; return; }
    if (!snapshot?.result || !matches() || snapshot.result.run_id !== host.capture()?.id) {
      wantSuggestions = true; await runAnalysis(); return;
    }
    if (!analysisId || busy) return;
    const value = Number(threshold.value);
    if (!Number.isFinite(value) || value <= 0) { error(new Error('Enter a positive improvement threshold.')); return; }
    busy = true; failure.textContent = ''; updateButtons();
    try { await suggestMeasurements(analysisId, value); await poll(generation); }
    catch (reason) { error(reason); }
    finally { busy = false; updateButtons(); }
  }
  async function applyPreview() {
    if (precisionDirty()) { error(new Error('Precision changed. Analyse uncertainty again to preview the new fit before applying.')); analyse.focus(); return; }
    if (!analysisId || !snapshot || !matches() || busy) return;
    busy = true; failure.textContent = ''; updateButtons();
    try { await applyAnalysis(analysisId, snapshot.solution_revision); await poll(generation); }
    catch (reason) { error(reason); }
    finally { busy = false; updateButtons(); }
  }
  async function revertPreview() {
    if (!analysisId || !snapshot || busy) return;
    busy = true; updateButtons();
    try {
      if (snapshot.acceptance && (snapshot.acceptance.active || snapshot.acceptance.result_run_id === host.capture()?.id)) {
        const response = await revertAnalysis(analysisId, snapshot.solution_revision);
        opened.add(snapshot.acceptance.result_run_id); await host.view(response.result_key);
      }
      snapshot = undefined; analysisId = undefined; wantSuggestions = false; host.preview(null); render();
    } catch (reason) { error(reason); }
    finally { busy = false; updateButtons(); }
  }
  async function poll(token: number) {
    if (!analysisId) return;
    try {
      const response = await readAnalysis(analysisId);
      if (token !== generation) return;
      const changed = JSON.stringify([snapshot?.job.state, snapshot?.accepted_job?.state, snapshot?.suggestions_job?.state, snapshot?.stale])
        !== JSON.stringify([response.job.state, response.accepted_job?.state, response.suggestions_job?.state, response.stale]);
      snapshot = response;
      if (response.job.state === 'failed' || response.job.state === 'interrupted') wantSuggestions = false;
      if (changed && side.isOpen) render(); else messages();
      const accepted = response.acceptance;
      if (accepted?.active && response.accepted_job?.state === 'completed' && !opened.has(accepted.result_run_id)
        && host.capture()?.id !== accepted.result_run_id && host.canSwitch() && !precisionDirty()
        && !(document.activeElement as HTMLElement)?.closest('input,textarea,[contenteditable]')) {
        opened.add(accepted.result_run_id); await host.view(`run:${accepted.result_run_id}`);
        if (token !== generation) return;
      }
      if (working()) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => { timer = undefined; void poll(token); }, 2000);
      } else if (wantSuggestions && response.result && matches()) {
        wantSuggestions = false; busy = false; await suggestMore();
      }
    } catch (reason) { if (token === generation) error(reason); }
  }
  async function exclude(pair: Pick<SuggestedPair, 'tag_a' | 'tag_b'>, remove = false) {
    const document = doc(); if (!document || busy) return;
    const reason = remove ? '' : window.prompt('Why is this pair not physically measurable?', 'Obstructed or inaccessible');
    if (reason === null || !remove && !reason.trim()) return;
    const records = (document.excluded_pairs ?? []).filter(row => row.tag_a !== pair.tag_a || row.tag_b !== pair.tag_b);
    if (!remove) records.push({ tag_a: pair.tag_a, tag_b: pair.tag_b, reason });
    busy = true;
    try { await configureMeasurements(document, document.default_sigma_m ?? null, {}, records); await host.refresh(); render(); }
    catch (failure) { error(failure); } finally { busy = false; updateButtons(); }
  }
  function render() {
    const capture = host.capture(); const document = doc();
    const context = [capture?.group_name ?? 'Ungrouped', capture?.display_name ?? capture?.name ?? 'No result selected', host.layoutName()].filter(Boolean).join(' · ');
    side.context.textContent = context;
    if (document?.revision !== lastRevision) {
      if (window.document.activeElement !== precision) precision.value = String(document?.default_sigma_m ? document.default_sigma_m*1000 : DEFAULT_PRECISION_MM);
      lastRevision = document?.revision ?? -1;
    }
    const activeInput = window.document.activeElement instanceof HTMLInputElement ? window.document.activeElement : null;
    const focusedPair = activeInput?.dataset.pair;
    const scroll = side.body.scrollTop;
    side.body.replaceChildren();
    const table = node('table'); const header = table.createTHead().insertRow();
    for (const title of ['Tags', 'Entered', 'Original → fitted', 'Difference', 'Precision mm', '']) header.append(node('th', title));
    for (const record of document?.distances ?? []) {
      const row = table.insertRow(); const fitted = matches() ? snapshot?.result?.residuals.find(r => r.tag_a === record.tag_a && r.tag_b === record.tag_b) : null;
      const current = fitted?.fitted_m ?? host.distance(record.tag_a, record.tag_b);
      for (const value of [`${record.tag_a} ↔ ${record.tag_b}`, mm(record.distance_m),
        fitted ? `${mm(fitted.scan_m)} → ${mm(fitted.fitted_m)}` : current === null ? 'Unavailable' : mm(current),
        fitted ? `${mm(fitted.scan_m-record.distance_m)} → ${mm(fitted.residual_m)}` : current === null ? 'Unavailable' : mm(current-record.distance_m)]) row.insertCell().textContent = value;
      if (fitted && fitted.weight < .8) {
        row.title = `Downweighted: ${(fitted.weight*100).toFixed(0)}% · residual ${fitted.standardised_residual.toFixed(1)} standard deviations`;
        row.cells[0].append(node('span', ' · Check')); row.classList.add('is-outlier');
      }
      const input = node('input'); input.type = 'number'; input.min = '0.01'; input.step = 'any'; input.placeholder = 'Default';
      const key = `${record.tag_a}:${record.tag_b}`; input.dataset.pair = key;
      const fieldError = node('span'); fieldError.className = 'measurement-field-error';
      fieldError.id = `precision-pair-${record.tag_a}-${record.tag_b}`; fieldError.setAttribute('role', 'alert');
      input.setAttribute('aria-describedby', fieldError.id);
      input.value = drafts.get(key) ?? (record.sigma_m ? String(record.sigma_m*1000) : '');
      input.setAttribute('aria-label', `Measuring precision for tags ${record.tag_a} and ${record.tag_b} in mm`);
      input.oninput = () => {
        drafts.set(key, input.value);
        const valid = !input.value.trim() || Number.isFinite(Number(input.value)) && Number(input.value) > 0;
        input.setAttribute('aria-invalid', String(!valid));
        fieldError.textContent = valid ? '' : 'Enter a value greater than zero, or leave blank for the default.';
        messages();
      }; row.insertCell().append(input, fieldError);
      const controls = row.insertCell();
      const edit = button('Edit', () => measure(record.tag_a, record.tag_b)); edit.disabled = current === null || busy || host.busy();
      const remove = button('Remove', () => { void host.remove(record); }); remove.disabled = busy || host.busy();
      edit.setAttribute('aria-label', `Edit measured distance between tags ${record.tag_a} and ${record.tag_b}`);
      remove.setAttribute('aria-label', `Remove measured distance between tags ${record.tag_a} and ${record.tag_b}`);
      controls.append(edit, remove);
    }
    side.body.append(node('h3', 'Saved measurements'), table);
    if (!document?.distances.length) side.body.append(node('p', 'No measured distances saved for this layout.'));
    if (document?.excluded_pairs?.length) {
      const exclusions = node('details'); exclusions.append(node('summary', `Physical-access exclusions (${document.excluded_pairs.length})`));
      for (const pair of document.excluded_pairs) {
        const row = node('p', `Tags ${pair.tag_a} ↔ ${pair.tag_b}: ${pair.reason} `);
        row.append(button('Allow measurement', () => { void exclude(pair, true); })); exclusions.append(row);
      }
      side.body.append(exclusions);
    }
    if (snapshot?.result && matches()) {
      const maximum = Math.max(0, ...snapshot.result.movements.map(row => row.distance_m));
      side.body.append(node('p', `Proposed maximum tag movement: ${mm(maximum)}. Preview markers only; Apply rebuilds the surface.`),
        node('p', snapshot.result.diagnostics.note));
      const details = node('details'); details.append(node('summary', 'Show uncertainty changes'));
      const dimensions = node('table'); const heading = dimensions.createTHead().insertRow();
      for (const value of ['Dimension', 'Scan-only ±95%', 'With distances ±95%']) heading.append(node('th', value));
      for (const dimension of snapshot.result.dimensions) {
        const row = dimensions.insertRow();
        for (const value of [`${dimension.tag_a} ↔ ${dimension.tag_b}`, mm(dimension.before_95_m), mm(dimension.after_95_m)]) row.insertCell().textContent = value;
      }
      details.append(dimensions); side.body.append(details);
    }
    if (snapshot?.suggestions && matches()) {
      const report = snapshot.suggestions;
      side.body.append(node('h3', 'Additional measurements'), node('p', report.note));
      side.body.append(node('p', `Report threshold: ${report.threshold_mm} mm reduction in 95% uncertainty half-width.`));
      const filterLabel = node('label', 'Clearance '); const select = node('select');
      for (const [value, title] of [['no_obstruction_detected', 'No obstruction detected'], ['unknown', 'Unknown — check physically'], ['obstructed', 'Obstructed / excluded'], ['all', 'All useful pairs']]) select.add(new Option(title, value));
      select.value = filter; select.onchange = () => { filter = select.value; render(); }; filterLabel.append(select); side.body.append(filterLabel);
      const pairs = report.rows.filter(row => filter === 'all' || row.clearance === filter);
      if (!pairs.length) side.body.append(node('p', `No pairs in this category. ${report.rows.length} pairs meet the predicted improvement threshold across all clearance categories.`));
      for (const pair of pairs) {
        const article = node('details'); article.className = 'measurement-suggestion';
        const key = `${pair.tag_a}:${pair.tag_b}`;
        const clearance = pair.clearance === 'unknown' ? 'Unknown clearance' : pair.clearance === 'obstructed' ? 'Obstructed' : 'No obstruction detected';
        article.append(node('summary', `Tags ${pair.tag_a} ↔ ${pair.tag_b} · ${mm(pair.gain_m)} less uncertainty · ${clearance}`),
          node('p', `${mm(pair.gain_m)} predicted reduction for ${pair.target_a} ↔ ${pair.target_b}: ±${mm(pair.before_95_m)} → ±${mm(pair.after_95_m)} (95%).`),
          node('p', pair.clearance_reason));
        article.open = expandedSuggestions.has(key);
        article.ontoggle = () => { if (article.open) expandedSuggestions.add(key); else expandedSuggestions.delete(key); };
        if (pair.overlaps_with.length) article.append(node('p', `Overlapping benefit: ${pair.overlaps_with.map(p => p.join('–')).join(', ')}.`));
        article.append(button('Measure pair', () => measure(pair.tag_a, pair.tag_b)),
          button('Show tape path', () => host.highlight(pair)),
          button(pair.manual ? 'Allow measurement' : 'Not physically measurable…', () => { void exclude(pair, !!pair.manual); }));
        side.body.append(article);
      }
      if (report.remeasure.length) {
        side.body.append(node('h3', 'Worth remeasuring'));
        for (const pair of report.remeasure) side.body.append(button(`Remeasure tags ${pair.tag_a} ↔ ${pair.tag_b}`, () => measure(pair.tag_a, pair.tag_b)));
      }
    }
    if (snapshot?.diagnostic && !snapshot.stale) {
      side.body.append(node('h3', 'Uncertainty not quantifiable'), node('p', snapshot.diagnostic.note));
      for (const pair of snapshot.diagnostic.pairs) {
        side.body.append(button(`Investigate tags ${pair.tag_a} ↔ ${pair.tag_b}`, () => measure(pair.tag_a, pair.tag_b)));
      }
    }
    side.body.scrollTop = scroll;
    if (focusedPair) [...side.body.querySelectorAll<HTMLInputElement>('input[data-pair]')].find(input => input.dataset.pair === focusedPair)?.focus({ preventScroll: true });
    messages();
  }
  function refresh() {
    const capture = host.capture(); const next = `${capture?.id ?? ''}:${capture?.tag_layout_id ?? ''}`;
    if (identity !== next) {
      generation++; identity = next; drafts.clear(); expandedSuggestions.clear(); filter = 'no_obstruction_detected'; lastRevision = -1; snapshot = undefined; analysisId = capture?.analysis_id ?? undefined;
      wantSuggestions = false; host.preview(null);
      if (timer) { clearTimeout(timer); timer = undefined; }
      if (analysisId && side.isOpen) void poll(generation);
    }
    if (side.isOpen) render(); else host.preview(null);
  }
  return {
    open() { const before = generation; side.open(); refresh(); if (analysisId && before === generation) void poll(generation); },
    refresh,
    render: () => { if (side.isOpen) render(); },
    hide: () => side.close(),
  };
}
