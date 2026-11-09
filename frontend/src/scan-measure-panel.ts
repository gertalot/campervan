import { createSidePanel } from './side-panel';
import { createMeasureRow } from './scan-measure-row';
import { pairKey, type MeasurementSession } from './scan-measure-session';
import { createWorkflow, type Pair } from './scan-workflow-api';
import type { ScanTag } from './scan-tags';
interface Capture { id?: string; name?: string; display_name?: string; group_name?: string | null; tag_layout_id?: string | null; tags?: ScanTag[] }
interface Host {
  capture(): Capture | undefined; session(): MeasurementSession | null; layoutName(): string;
  error(): string; distance(a: number, b: number): number | null;
  highlight(pair: Pair | null): void;
}
export function createMeasurePanel(host: Host) {
  const side = createSidePanel({ id: 'measurement-manager', title: 'Manage measurements', mode: 'nonmodal',
    onClose: () => host.highlight(null) });
  side.element.classList.add('scan-measure-panel');
  const form = document.createElement('form'); form.className = 'measurement-precision';
  const label = document.createElement('label'); label.textContent = 'Typical measuring precision (mm) ';
  const precision = document.createElement('input'); precision.type = 'number'; precision.min = '0.01'; precision.step = 'any'; label.append(precision);
  const save = document.createElement('button'); save.textContent = 'Save precision'; save.type = 'submit'; form.append(label, save); side.actions.append(form);
  const status = document.createElement('p'); status.setAttribute('role', 'status'); side.status.append(status);
  const heading = document.createElement('h3'); heading.textContent = 'Saved measurements'; side.body.append(heading);
  const list = document.createElement('div'); side.body.append(list);
  const empty = document.createElement('p'); empty.textContent = 'No measured distances saved for this layout.'; side.body.append(empty);
  let current: MeasurementSession | null = null; let unsubscribe: (() => void) | undefined;
  let identity = ''; let generation = 0;
  async function bindWorkflow(session: MeasurementSession, source: string, layout: string, token: number) {
    try { const view = await createWorkflow(source, layout); if (token === generation && current === session) session.bindWorkflow(view); }
    catch (reason) { if (token === generation) status.textContent = String(reason); }
  }
  const rows = new Map<string, ReturnType<typeof createMeasureRow>>();
  function render() {
    const capture = host.capture(); const session = host.session();
    side.context.textContent = [capture?.group_name ?? 'Ungrouped', capture?.display_name ?? capture?.name ?? 'No result selected', host.layoutName()].filter(Boolean).join(' · ');
    const nextIdentity = `${capture?.id ?? ''}:${capture?.tag_layout_id ?? ''}`;
    const changed = nextIdentity !== identity || session !== current;
    if (session !== current) {
      unsubscribe?.(); rows.forEach(row => row.destroy()); rows.clear(); list.replaceChildren(); current = session;
      unsubscribe = session?.subscribe(render);
      precision.value = session?.precisionDraft('default') ?? String((session?.document.default_sigma_m ?? .003) * 1000);
    }
    if (changed) { identity = nextIdentity; generation++; session?.bindWorkflow(null);
      if (session && capture?.id && capture.tag_layout_id) void bindWorkflow(session, capture.id, capture.tag_layout_id, generation); }
    status.textContent = host.error();
    if (!session) { empty.hidden = false; return; }
    const batches = session.workflow?.workflow.checklist_batches ?? [];
    const pairs: Pair[] = []; const seen = new Set<string>();
    for (const pair of [...batches.flatMap(batch => batch.ordered_pairs), ...session.document.distances]) {
      const key = pairKey(pair); if (!seen.has(key)) { seen.add(key); pairs.push(pair); }
    }
    const wanted = new Set(pairs.map(pairKey));
    for (const [key, row] of rows) if (!wanted.has(key)) { row.destroy(); row.element.remove(); rows.delete(key); }
    for (const [position, pair] of pairs.entries()) {
      const key = pairKey(pair); let row = rows.get(key);
      if (!row) {
        row = createMeasureRow({ session, pair, estimate: () => host.distance(pair.tag_a, pair.tag_b),
          highlight: () => host.highlight(pair), advance: () => {
            const all = [...rows.values()]; const index = all.findIndex(item => item.element.dataset.pair === key);
            const next = all.slice(index + 1).find(item => { const [tag_a, tag_b] = item.element.dataset.pair!.split(':').map(Number);
              const value = session.draft({ tag_a, tag_b }); return !value.saved || value.state !== 'Saved'; });
            next?.input.focus();
          } });
        row.input.addEventListener('focus', () => {
          const batches = session.workflow?.workflow.checklist_batches ?? [];
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
      if (list.children[position] !== row.element) list.insertBefore(row.element, list.children[position] ?? null);
    }
    empty.hidden = !!rows.size;
  }
  precision.oninput = () => host.session()?.setPrecisionDraft('default', precision.value);
  precision.onkeydown = event => event.stopPropagation();
  form.onsubmit = event => { event.preventDefault(); const session = host.session(); const value = Number(precision.value) / 1000;
    if (!session || !Number.isFinite(value) || value <= 0) { status.textContent = 'Enter a positive precision.'; precision.focus(); return; }
    void session.configure({ default_sigma_m: value }).catch(reason => { status.textContent = String(reason); }); };
  return { open() { side.open(); render(); }, refresh: render, render, hide: () => side.close(),
    async flush() { const result = await host.session()?.flush(); if (result && !result.ok) { if (result.pairs.length) rows.get(pairKey(result.pairs[0]))?.input.focus(); else if (result.precision[0] && result.precision[0] !== 'default') rows.get(result.precision[0])?.sigma.focus(); else precision.focus(); } return result; } };
}
