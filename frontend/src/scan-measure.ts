/** Tag tape measure: interaction state and physical constraints, never geometry optimisation. */
import { createMeasurePanel } from './scan-measure-panel';
import { readMeasurements, type MeasurementDocument, type DistanceMeasurement } from './scan-measurements-api';
import { createMeasurementSession, type MeasurementSession } from './scan-measure-session';
import type { createScanTags, ScanTag, MeasurementPreview } from './scan-tags';

export interface MeasurementCapture { id?: string; name?: string; display_name?: string; group_name?: string | null;
  analysis_id?: string | null; tag_layout_id?: string | null; tags?: ScanTag[] }
interface Host {
  panel: HTMLElement; container: HTMLElement; bar: HTMLElement;
  capture(): MeasurementCapture | undefined;
  overlay(): ReturnType<typeof createScanTags> | undefined;
  loading(): boolean;
  view(key: string): Promise<void>;
}
const mm = (metres: number) => `${(metres * 1000).toFixed(1)} mm`;
const emptyRecords: DistanceMeasurement[] = [];
export function createScanMeasure(host: Host) {
  const { panel, container, bar } = host;
  bar.innerHTML = `<span role="status" aria-live="polite" data-prompt></span>
    <label>Distance <input type="text" inputmode="decimal" aria-label="Measured tag centre-to-centre distance"
      aria-describedby="scan-distance-help scan-distance-error" spellcheck="false" autocomplete="off" /></label>
    <span id="scan-distance-help">3D centre-to-centre · units: mm, cm, m, in, ft · Enter saves · Esc restores/cancels</span>
    <span id="scan-distance-error" role="alert"></span><button type="button" data-escape></button>`;
  const prompt = bar.querySelector<HTMLElement>('[data-prompt]')!;
  const input = bar.querySelector('input')!;
  const errorText = bar.querySelector<HTMLElement>('[role=alert]')!;
  const escapeButton = bar.querySelector<HTMLButtonElement>('[data-escape]')!;
  const tools = document.createElement('div'); tools.className = 'scan-measure-tools';
  tools.dataset.campervanControl = 'true';
  tools.innerHTML = `<button type="button" aria-label="Measure tags" aria-pressed="false" aria-keyshortcuts="T" title="Measure tags (T)"
    data-tape><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h10a5 5 0 0 1 5 5v5H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Zm2 3v4m4-4v2m4-2v4m5 3h3v4H11v-4" /></svg></button>
    <button type="button" data-list aria-haspopup="dialog" aria-controls="measurement-manager"
      title="Manage measured distances, uncertainty and additional measurements">Manage measurements…</button>`;
  const tape = tools.querySelector<HTMLButtonElement>('[data-tape]')!;
  const listButton = tools.querySelector<HTMLButtonElement>('[data-list]')!;
  let active = false;
  let first: number | null = null;
  let second: number | null = null;
  let hover: number | null = null;
  let pointer: { x: number; y: number } | undefined;
  let baseline = '';
  let notice = '';
  let error = '';
  let configured = false;
  let measurementData: MeasurementDocument | null = null;
  let session: MeasurementSession | null = null;
  const sessions = new Map<string, MeasurementSession>();
  window.addEventListener('beforeunload', event => { if ([...sessions.values()].some(item => item.hasUnsaved())) event.preventDefault(); });
  let readError = '';
  let layoutName = '';
  let reading = true;
  let readGeneration = 0;
  let busy = false;
  let generation = 0;
  let gesture: { id: number; x: number; y: number; dragged: boolean } | undefined;
  const commands = {
    tape: { label: 'Measure tags', shortcut: 'T', run: () => { if (host.capture()?.tags?.length) setActive(!active); } },
    escape: { shortcut: 'Esc', run: escape },
    list: { label: 'Manage measurements…', run: showList },
  };
  tape.title = `${commands.tape.label} (${commands.tape.shortcut})`;

  const manager = createMeasurePanel({ capture: host.capture, session: () => session, layoutName: () => layoutName,
    error: () => error || readError, distance,
    highlight: pair => host.overlay()?.setSuggestedPair(pair ? { from: pair.tag_a, to: pair.tag_b } : null) });

  function distance(a: number, b: number): number | null {
    const tags = host.capture()?.tags ?? [];
    const pa = tags.find(tag => tag.id === a)?.pose; const pb = tags.find(tag => tag.id === b)?.pose;
    return pa && pb ? Math.hypot(...[0, 1, 2].map(i => pa[i][3] - pb[i][3])) : null;
  }
  function records() {
    return measurementData && host.capture()?.tag_layout_id === measurementData.tag_layout_id ? measurementData.distances : emptyRecords;
  }
  function unavailable(): string {
    if (reading) return 'Loading measurement document…';
    if (readError) return readError;
    if (!configured || !measurementData) return 'Measurement data is unavailable. Use Refresh scans to reload it.';
    if (!host.capture()?.tag_layout_id) return 'Saving unavailable: associate this capture with a measurement document.';
    if (host.capture()?.tag_layout_id !== measurementData.tag_layout_id) return 'Saving unavailable: this capture has a different tag layout.';
    return '';
  }
  function paint() {
    bar.hidden = !active;
    tape.setAttribute('aria-pressed', String(active));
    const overlay = host.overlay();
    overlay?.setInteractive(active && !panel.hidden && !host.loading(), selectTag);
    overlay?.setSelection(active && first !== null ? second === null ? [first] : [first, second] : []);
    const preview: MeasurementPreview | null = active && first !== null
      ? { from: first, to: second ?? hover ?? undefined, pointer } : null;
    overlay?.setMeasurements(records(), preview);
    input.disabled = busy || host.loading() || second === null;
    input.setAttribute('aria-invalid', String(!!error)); errorText.textContent = error;
    let stage = 'Select first tag · T or Esc to exit';
    if (host.loading()) stage = 'Loading scan…';
    else if (busy) stage = 'Saving…';
    else if (second !== null && first !== null) stage = `Tags ${first} ↔ ${second} · Scan estimate: ${mm(distance(first, second)!)} · ${session?.draft({ tag_a: first, tag_b: second }).state ?? 'Not saved'}`;
    else if (first !== null) stage = 'Select second tag · Esc or click empty space to cancel';
    const message = [notice, stage, unavailable()].filter(Boolean).join(' · ');
    if (prompt.textContent !== message) prompt.textContent = message;
    tape.disabled = !host.capture()?.tags?.length;
    const escapeLabel = second !== null && input.value !== baseline ? 'Restore' : first !== null ? 'Cancel pair' : 'Done';
    escapeButton.textContent = `${escapeLabel} (${commands.escape.shortcut})`;
    escapeButton.title = `${escapeLabel} (${commands.escape.shortcut})`;
    escapeButton.disabled = busy;
  }
  function cancel() {
    generation++; first = second = hover = null; pointer = undefined; baseline = ''; input.value = '';
    error = notice = ''; paint();
  }
  function setActive(value: boolean) {
    active = value; cancel();
    if (active) container.focus({ preventScroll: true });
  }
  function selectPair(a: number, b: number) {
    if (host.loading() || distance(a, b) === null) return;
    active = true; generation++; first = a; second = b; hover = null; pointer = undefined; error = notice = '';
    const value = session?.draft({ tag_a: a, tag_b: b });
    baseline = value?.saved ?? ''; input.value = value?.text ?? ''; paint();
  }
  function selectTag(id: number) {
    if (!active || busy || host.loading()) return;
    if (first === null || second !== null) {
      generation++; first = id; second = null; hover = null; baseline = ''; input.value = ''; error = notice = ''; paint();
    } else if (first === id) { notice = 'Choose a different second tag'; paint(); }
    else selectPair(first, id);
  }
  async function refreshDocument() {
    const token = ++readGeneration;
    reading = true; readError = '';
    if (host.capture() && !host.capture()?.tag_layout_id) {
      measurementData = null; session = null; layoutName = 'No tag layout'; reading = false;
      readError = 'Select a reconstruction associated with a tag layout to manage measurements.';
      manager.refresh(); paint(); return;
    }
    if (host.capture()?.tag_layout_id && host.capture()?.tag_layout_id !== measurementData?.tag_layout_id) { measurementData = null; session = null; }
    manager.refresh(); paint();
    try {
      const response = await readMeasurements(host.capture()?.tag_layout_id);
      if (token !== readGeneration) return;
      configured = response.configured; measurementData = response.document; layoutName = response.layout_name ?? response.document?.tag_layout_id ?? ''; readError = '';
      if (response.document) {
        let next = sessions.get(response.document.tag_layout_id);
        if (!next) {
          next = createMeasurementSession(response.document, () => host.capture()?.id);
          const owned = next;
          next.subscribe(() => { if (session === owned) { measurementData = owned.document;
            if (first !== null && second !== null && document.activeElement !== input) {
              const value = owned.draft({ tag_a: first, tag_b: second }); input.value = value.text; baseline = value.saved; error = value.error;
            } manager.refresh(); paint(); } });
          sessions.set(response.document.tag_layout_id, next);
        } else await next.refresh();
        if (token !== readGeneration) return;
        session = next; measurementData = next.document;
      } else session = null;
      if (first !== null && second !== null && distance(first, second) !== null) {
        const dirty = input.value !== baseline;
        const value = session?.draft({ tag_a: first, tag_b: second });
        baseline = value?.saved ?? '';
        if (!dirty) input.value = value?.text ?? '';
      }
    } catch (reason) {
      if (token !== readGeneration) return;
      readError = String(reason instanceof Error ? reason.message : reason);
    }
    reading = false; manager.refresh(); paint();
  }
  async function save(advance = true) {
    if (first === null || second === null || host.loading() || !session) return;
    const reason = unavailable(); if (reason) { error = reason; paint(); return; }
    const a = first; const b = second; const token = generation; const owned = session;
    owned.setDraft({ tag_a: a, tag_b: b }, input.value);
    const ok = await owned.commit({ tag_a: a, tag_b: b });
    if (generation !== token || session !== owned) return;
    const value = owned.draft({ tag_a: a, tag_b: b }); baseline = value.saved; error = value.error;
    if (ok && value.state === 'Saved' && advance) { cancel(); notice = `Saved tags ${a} ↔ ${b}`; container.focus({ preventScroll: true }); }
    paint();
  }
  function escape() {
    if (busy) return;
    if (second !== null && input.value !== baseline) {
      input.value = baseline; if (first !== null && second !== null) session?.setDraft({ tag_a: first, tag_b: second }, baseline); input.select(); error = ''; notice = 'Previous value restored'; paint();
    }
    else if (first === null) setActive(false);
    else cancel();
  }
  function showList() { manager.open(); }
  tape.onclick = commands.tape.run; listButton.onclick = commands.list.run; escapeButton.onclick = commands.escape.run;
  input.oninput = () => { if (first !== null && second !== null) session?.setDraft({ tag_a: first, tag_b: second }, input.value); error = notice = ''; paint(); };
  input.onblur = () => { if (!error && input.value.trim() && input.value !== baseline) void save(false); };
  input.onkeydown = event => {
    event.stopPropagation(); if (event.isComposing) return;
    if (event.key === 'Enter') { event.preventDefault(); event.stopPropagation(); void save(); }
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); if (!event.repeat) commands.escape.run(); }
  };
  container.tabIndex = 0;
  container.addEventListener('pointerdown', event => {
    if (event.pointerType === 'touch' && !event.isPrimary) {
      if (gesture) gesture.dragged = true;
      return;
    }
    if (active && !busy && event.button === 0 && event.isPrimary && event.target instanceof HTMLCanvasElement) {
      gesture = { id: event.pointerId, x: event.clientX, y: event.clientY, dragged: false };
    }
  }, true);
  container.addEventListener('pointermove', event => {
    if (gesture?.id === event.pointerId && Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) > 4) gesture.dragged = true;
    if (!active || first === null || second !== null || host.loading()) return;
    if (!(event.target instanceof HTMLCanvasElement)) return;
    pointer = { x: event.clientX, y: event.clientY }; hover = host.overlay()?.pickTag(event.clientX, event.clientY) ?? null; paint();
  });
  window.addEventListener('pointerup', event => {
    const click = gesture; gesture = undefined;
    if (!click || click.id !== event.pointerId || click.dragged || !active || busy || host.loading()
      || !(event.target instanceof HTMLCanvasElement) || !container.contains(event.target)
      || Math.hypot(event.clientX - click.x, event.clientY - click.y) > 4) return;
    const tag = host.overlay()?.pickTag(event.clientX, event.clientY);
    if (tag !== null && tag !== undefined) selectTag(tag); else cancel();
    container.focus({ preventScroll: true });
  }, true);
  container.addEventListener('pointercancel', () => { gesture = undefined; });
  container.addEventListener('lostpointercapture', () => { gesture = undefined; });
  container.addEventListener('pointerleave', () => { pointer = undefined; hover = null; if (active) paint(); });
  window.addEventListener('blur', () => { gesture = undefined; });
  window.addEventListener('keydown', event => {
    if (panel.hidden || document.querySelector('dialog:modal') || event.defaultPrevented || event.isComposing || event.metaKey || event.ctrlKey || event.altKey) return;
    if ((event.target as Element).closest('[role=menu],.side-panel')) return;
    const editable = (event.target as HTMLElement).closest('input,textarea,select,[contenteditable]');
    if (editable) return;
    if (event.key.toLowerCase() === 't') {
      event.preventDefault(); event.stopPropagation(); if (!event.repeat) commands.tape.run();
    }
    else if (active && event.key === 'Escape') {
      event.preventDefault(); event.stopPropagation(); if (!event.repeat) commands.escape.run();
    }
    else if (active && second !== null && event.key === 'Enter'
      && !(event.target as HTMLElement).closest('button,[role=button]')) {
      event.preventDefault(); event.stopPropagation(); void save();
    }
    else if (active && second !== null && !busy && !host.loading() && /^[\d.]$/.test(event.key)) {
      // Focusing the field does not retarget this key event away from the viewer.
      event.preventDefault(); event.stopPropagation();
      input.value = event.key; if (first !== null && second !== null) session?.setDraft({ tag_a: first, tag_b: second }, input.value); error = notice = ''; input.focus(); paint();
    }
  }, true);
  void refreshDocument(); paint();
  return {
    cancel, refresh: paint, reload: refreshDocument,
    session: () => session, flush: () => manager.flush(),
    clearCapture() { setActive(false); manager.refresh(); },
    attach() { (container.querySelector('.tcv_cad_toolbar') ?? panel.querySelector('.scan-controls'))?.append(tools); paint(); },
    tabChanged(shown: boolean) { if (!shown) { cancel(); manager.hide(); } paint(); },
  };
}
