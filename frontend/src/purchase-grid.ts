import {
  emptyFilter, newPurchase, type PlanningClient, type PurchaseFilter, type PurchaseRecord,
  type PurchaseRow, type PurchaseView, type Totals,
} from './planning-api';

const money = (value: number) => new Intl.NumberFormat('en-NZ', { style: 'currency', currency: 'NZD' }).format(value);
export const el = <K extends keyof HTMLElementTagNameMap>(tag: K, text = '') => {
  const node = document.createElement(tag); node.textContent = text; return node;
};
export function action(label: string, run: () => void) {
  const button = el('button', label); button.type = 'button'; button.onclick = run; return button;
}
export function safeURL(value: string) { return /^(https?:\/\/|mailto:|tel:)/i.test(value); }

function matches(row: PurchaseRow, filter: PurchaseFilter) {
  const r = row.record;
  return (!filter.category || r.category === filter.category) && (!filter.tag || r.tags.includes(filter.tag))
    && (!filter.supplier || r.supplier === filter.supplier) && (!filter.status || row.status === filter.status)
    && (!filter.search || [r.name, r.notes, r.supplier, ...r.tags, ...row.uses].join(' ').toLowerCase().includes(filter.search.toLowerCase()));
}
function totalText(label: string, totals: Totals) {
  const incomplete = totals.unknown_remaining + totals.unknown_spent;
  return `${label}: spent ${money(totals.spent)} · estimated remaining ${money(totals.remaining)} · combined ${money(totals.forecast)}`
    + (incomplete ? ` — incomplete: ${totals.unknown_remaining} unpriced/unknown quantities, ${totals.unknown_spent} bought items without actual cost` : '');
}
function sum(rows: PurchaseRow[]): Totals {
  // Values returned by the server are already rounded to cents; add integer cents for filtered totals.
  const spent = rows.reduce((n, r) => n + Math.round((r.record.spent ?? 0) * 100), 0) / 100;
  const remaining = rows.reduce((n, r) => n + Math.round((r.remaining_cost ?? 0) * 100), 0) / 100;
  return { spent, remaining, forecast: (Math.round(spent * 100) + Math.round(remaining * 100)) / 100,
    unknown_remaining: rows.filter(r => r.remaining_cost === null).length,
    unknown_spent: rows.filter(r => r.record.bought > 0 && r.record.spent === null).length };
}

export function mountPurchaseGrid(
  root: HTMLElement, client: PlanningClient, initial = emptyFilter(), onFilter?: (filter: PurchaseFilter) => void,
) {
  root.classList.add('purchase-view');
  let filter = { ...initial };
  let data: PurchaseView | null = null;
  let disposed = false;
  let serial = 0;
  const controls = el('div'); controls.className = 'purchase-filters';
  const feedback = el('p'); feedback.className = 'planner-feedback'; feedback.setAttribute('role', 'status');
  const totals = el('div'); totals.className = 'purchase-totals';
  const content = el('div'); content.className = 'purchase-scroll';
  root.append(controls, feedback, totals, content);
  const selectInputs = new Map<string, HTMLSelectElement>();
  for (const [key, label] of [['category', 'Category'], ['tag', 'Tag'], ['supplier', 'Supplier'], ['status', 'Status']] as const) {
    const wrapper = el('label', label); const input = el('select'); wrapper.append(input); controls.append(wrapper);
    selectInputs.set(key, input);
    input.onchange = () => { filter[key] = input.value; onFilter?.({ ...filter }); render(); };
  }
  const search = el('input'); search.type = 'search'; search.placeholder = 'Find purchases…'; search.value = filter.search;
  search.setAttribute('aria-label', 'Search purchases');
  search.oninput = () => { filter.search = search.value; onFilter?.({ ...filter }); renderRows(); };
  const save = (record: PurchaseRecord) => {
    try {
      client.mutate({ kind: 'purchase', id: record.id, values: record as unknown as Record<string, unknown> }, false);
      feedback.textContent = 'Saving purchase…';
    } catch (error) { feedback.textContent = String(error); }
  };
  controls.append(search, action('+ Item', () => {
    const record = newPurchase(); const name = prompt('Item or service name'); if (!name?.trim()) return;
    record.name = name.trim(); record.category = filter.category; record.tags = filter.tag ? [filter.tag] : [];
    record.supplier = filter.supplier;
    // New items start unbought; show them even if this view was previously showing only bought stock.
    filter.status = ''; filter.search = ''; search.value = ''; onFilter?.({ ...filter }); save(record);
  }), action('Clear filters', () => { filter = emptyFilter(); search.value = ''; onFilter?.({ ...filter }); render(); }));

  function render() {
    if (!data || disposed) return;
    for (const [key, input] of selectInputs) {
      const values = key === 'status' ? data.rows.map(r => r.status)
        : key === 'tag' ? data.rows.flatMap(r => r.record.tags)
        : data.rows.map(r => r.record[key as 'category' | 'supplier']);
      const current = filter[key as keyof PurchaseFilter];
      input.replaceChildren(new Option('All', ''), ...[...new Set([...values, current])].filter(Boolean).sort().map(v => new Option(v, v)));
      input.value = current;
    }
    renderRows();
  }
  function renderRows() {
    if (!data || disposed) return;
    const rows = data.rows.filter(r => matches(r, filter));
    totals.replaceChildren(el('p', totalText('Shown items', sum(rows))), el('p', totalText('Whole project', data.totals)),
      el('small', 'NZD incl. GST. Add delivery as an item. Shared stock is counted once; filtered views are not separate budgets.'));
    const table = el('table'); table.className = 'purchase-grid';
    const head = el('tr');
    ['Item / source', 'Category / tags', 'Purchase unit', 'Required', 'Owned', 'Bought', 'Est. unit $', 'Actual spent $', 'Remaining', 'Actions'].forEach(label => head.append(el('th', label)));
    const thead = el('thead'); thead.append(head); table.append(thead);
    const body = el('tbody'); table.append(body); content.replaceChildren(table);
    if (!rows.length) { content.append(el('p', 'No items match. Add an item here or change the filters.')); return; }
    for (const row of rows) {
      let record = structuredClone(row.record);
      const tr = el('tr'); const cells = Array.from({ length: 10 }, () => el('td')); tr.append(...cells); body.append(tr);
      const edit = (cell: HTMLElement, key: keyof PurchaseRecord, label: string, numeric = false) => {
        const input = el('input'); input.type = numeric ? 'number' : 'text'; input.setAttribute('aria-label', `${record.name}: ${label}`);
        input.dataset.purchaseId = record.id; input.dataset.field = key;
        input.value = key === 'tags' ? record.tags.join(', ') : String(record[key] ?? '');
        if (numeric) {
          input.min = '0'; input.step = key === 'unit_price' || key === 'spent' ? '0.01' : 'any';
          input.placeholder = key === 'required' && row.required !== null ? `${row.required} auto` : 'Unknown';
        }
        const draftKey = record.id + ':' + key;
        let committed = input.value;
        input.value = client.getDraft(draftKey) ?? input.value;
        input.oninput = () => client.setDraft(draftKey, input.value !== committed, input.value);
        input.onchange = () => {
          if (!input.checkValidity()) { input.reportValidity(); return; }
          const value = numeric ? input.value === '' ? (key === 'owned' || key === 'bought' ? 0 : null) : Number(input.value)
            : key === 'tags' ? [...new Set(input.value.split(',').map(t => t.trim()).filter(Boolean))] : input.value;
          record = { ...(client.document?.purchases[record.id] ?? record), [key]: value };
          if ((key === 'category' && filter.category) || (key === 'tags' && filter.tag) || (key === 'supplier' && filter.supplier)) {
            feedback.textContent = 'Changing this field may move the item outside this filter.';
          }
          committed = input.value; client.setDraft(draftKey, false); save(record);
        };
        cell.append(input); return input;
      };
      edit(cells[0], 'name', 'Name');
      const source = el('details'); source.dataset.purchaseId = record.id;
      source.append(el('summary', 'Supplier, link & notes'));
      for (const [key, label] of [['supplier', 'Supplier'], ['url', 'Product URL'], ['notes', 'Notes']] as const) {
        source.append(el('label', label)); edit(source, key, label);
      }
      if (record.url && safeURL(record.url)) {
        const link = el('a', 'Open source ↗'); link.href = record.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; source.append(link);
      }
      cells[0].append(source, el('small', row.uses.join(' · ')));
      if (row.shared) cells[0].append(el('small', 'Shared stock — whole item cost'));
      if (row.legacy_owned) cells[0].append(el('small', 'Existing CAD uses marked owned are excluded from automatic need.'));
      edit(cells[1], 'category', 'Category'); edit(cells[1], 'tags', 'Tags, comma separated');
      edit(cells[2], 'unit', 'Unit');
      edit(cells[3], 'required', 'Required quantity (blank uses CAD count)', true);
      edit(cells[4], 'owned', 'Already owned quantity', true); edit(cells[5], 'bought', 'Bought quantity', true);
      edit(cells[6], 'unit_price', 'Estimated price per purchase unit', true); edit(cells[7], 'spent', 'Total actually spent', true);
      cells[8].append(el('strong', row.remaining === null ? 'Quantity unknown' : `${row.remaining} ${record.unit}`),
        el('small', row.remaining_cost === null ? 'Cost unknown' : money(row.remaining_cost)), el('small', row.status));
      if (row.status === 'Unused stock') cells[3].append(el('small', 'No current CAD requirement'));
      cells[9].append(action('Bought', () => {
        record = structuredClone(client.document?.purchases[record.id] ?? record);
        const required = row.status === 'Unused stock' ? 0 : record.required ?? row.required;
        const remaining = required === null ? null : Math.max(required - record.owned - record.bought, 0);
        if (remaining === null) {
          const value = prompt('Total quantity bought so far', String(record.bought)); if (value === null) return;
          const count = Number(value); if (!value.trim() || !Number.isFinite(count) || count < 0) { alert('Enter a non-negative quantity.'); return; }
          save({ ...record, bought: count });
        } else save({ ...record, bought: record.bought + remaining });
      }));
      if (!row.generated) cells[9].append(action('Delete', () => {
        if (!confirm(`Delete ${record.name}${record.bought || record.spent ? ' and its purchase/spending record' : ''}? You can Undo this.`)) return;
        try { client.mutate({ kind: 'delete_purchase', id: record.id }, false); } catch (error) { feedback.textContent = String(error); }
      }));
    }
  }
  async function refresh() {
    const ticket = ++serial;
    try {
      const next = await client.purchases();
      if (disposed || ticket !== serial) return;
      data = next; feedback.textContent = client.status;
      // A completed save may arrive while the next cell is being typed in. Preserve its unsaved draft and caret.
      const active = document.activeElement instanceof HTMLInputElement && content.contains(document.activeElement)
        ? document.activeElement : null;
      const draft = active ? { id: active.dataset.purchaseId, field: active.dataset.field,
        value: active.value, start: active.selectionStart, end: active.selectionEnd } : null;
      const expanded = new Set([...content.querySelectorAll<HTMLDetailsElement>('details[open]')]
        .map(detail => detail.dataset.purchaseId));
      render();
      content.querySelectorAll<HTMLDetailsElement>('details').forEach(detail => {
        detail.open = expanded.has(detail.dataset.purchaseId);
      });
      if (draft) {
        const replacement = [...content.querySelectorAll<HTMLInputElement>('input')]
          .find(input => input.dataset.purchaseId === draft.id && input.dataset.field === draft.field);
        if (replacement) {
          replacement.value = draft.value; replacement.focus({ preventScroll: true });
          if (draft.start !== null) replacement.setSelectionRange(draft.start, draft.end);
        }
      }
    } catch (error) { if (!disposed) feedback.textContent = String(error); }
  }
  const undo = action('Undo purchase', () => client.undoPurchase());
  const redo = action('Redo purchase', () => client.redoPurchase());
  controls.append(undo, redo);
  const status = () => {
    undo.disabled = !client.canUndoPurchase; redo.disabled = !client.canRedoPurchase;
    feedback.textContent = client.error ? client.status + ': ' + client.error + ' — use Plan → Reload or recovery controls.' : client.status;
    content.inert = client.blocked;
  };
  const unsubscribe = client.subscribe(change => { status(); if (change.purchases) void refresh(); });
  status();
  void refresh();
  return {
    refresh,
    setFilter(next: PurchaseFilter) {
      if (JSON.stringify(next) === JSON.stringify(filter)) return;
      filter = { ...emptyFilter(), ...next }; search.value = filter.search; render();
    },
    destroy() { disposed = true; unsubscribe(); root.replaceChildren(); },
  };
}
