import {
  emptyFilter, newPurchase, type PlanningClient, type PurchaseFilter, type PurchaseRecord,
  type PurchaseRow, type PurchaseView, type Totals,
} from './planning-api';
import { isStaticSite } from './site-runtime';

const money = (value: number) => new Intl.NumberFormat('en-NZ', { style: 'currency', currency: 'NZD' }).format(value);
const itemOrder = new Intl.Collator('en-NZ', { numeric: true, sensitivity: 'base' });
type SortKey = 'name' | 'required' | 'owned' | 'bought' | 'unit_price' | 'remaining_cost';
type SortDirection = 'ascending' | 'descending';
interface Sort { key: SortKey; direction: SortDirection }
const columns = [
  ['Item', 'name'], ['Required', 'required'], ['Owned', 'owned'], ['Bought', 'bought'],
  ['Unit price', 'unit_price'], ['Total price', 'remaining_cost'], ['', null],
] as const;

function savedSort(storageKey: string): Sort | null {
  try {
    const value = JSON.parse(localStorage.getItem(storageKey) ?? 'null');
    return value && columns.some(([, key]) => key !== null && key === value.key)
      && (value.direction === 'ascending' || value.direction === 'descending') ? value : null;
  } catch { return null; }
}

function sortValue(row: PurchaseRow, key: SortKey): string | number | null {
  if (key === 'required' || key === 'remaining_cost') return row[key];
  if (key === 'owned') return row.owned ?? row.record.owned;
  return row.record[key];
}
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
function missingDetails(row: PurchaseRow): string[] {
  const issues: string[] = [];
  if (row.required === null) issues.push('Quantity missing');
  if (row.remaining !== 0 && row.record.unit_price === null) issues.push('Price missing');
  return issues;
}
function fieldText(record: PurchaseRecord, key: keyof PurchaseRecord): string {
  const value = record[key];
  return key === 'tags' ? record.tags.join(', ')
    : (key === 'unit_price' || key === 'spent') && typeof value === 'number' ? value.toFixed(2) : String(value ?? '');
}
function fieldValue(input: HTMLInputElement, key: keyof PurchaseRecord) {
  return input.type === 'number'
    ? input.value === '' ? (key === 'owned' || key === 'bought' ? 0 : null) : Number(input.value)
    : key === 'tags' ? [...new Set(input.value.split(',').map(tag => tag.trim()).filter(Boolean))] : input.value;
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
  viewId = 'bom',
) {
  root.classList.add('purchase-view');
  let filter = { ...initial };
  let data: PurchaseView | null = null;
  let disposed = false;
  let serial = 0;
  let needsDetails = false;
  const sortStorageKey = `campervan.purchases.sort.${viewId}`;
  let sort = savedSort(sortStorageKey);
  const expanded = new Set<string>();
  const summary = el('div'); summary.className = 'purchase-summary';
  const controls = el('div'); controls.className = 'purchase-filters';
  const feedback = el('p'); feedback.className = 'planner-feedback'; feedback.setAttribute('role', 'status');
  const result = el('p'); result.className = 'purchase-result'; result.setAttribute('role', 'status');
  const content = el('div'); content.className = 'purchase-scroll';
  content.tabIndex = 0; content.setAttribute('role', 'region'); content.setAttribute('aria-label', 'Purchase list');
  root.append(summary, controls, feedback, result, content);
  const selectInputs = new Map<string, HTMLSelectElement>();
  for (const [key, label] of [['category', 'Category'], ['tag', 'Tag'], ['supplier', 'Supplier'], ['status', 'Status']] as const) {
    const wrapper = el('label', label); const input = el('select'); input.name = key;
    wrapper.append(input); controls.append(wrapper);
    selectInputs.set(key, input);
    input.onchange = () => { filter[key] = input.value; onFilter?.({ ...filter }); render(); };
  }
  const search = el('input'); search.type = 'search'; search.placeholder = 'Find purchases…'; search.value = filter.search;
  search.name = 'search'; search.autocomplete = 'off';
  search.setAttribute('aria-label', 'Search purchases');
  search.oninput = () => { filter.search = search.value; onFilter?.({ ...filter }); renderRows(); };
  const save = (record: PurchaseRecord) => {
    if (isStaticSite) return false;
    try {
      client.mutate({ kind: 'purchase', id: record.id, values: record as unknown as Record<string, unknown> }, false);
      feedback.textContent = 'Saving purchase…';
      return true;
    } catch (error) { feedback.textContent = String(error); return false; }
  };
  const searchLabel = el('label', 'Search'); searchLabel.className = 'purchase-search'; searchLabel.append(search);
  controls.prepend(searchLabel);
  const attention = el('input'); attention.type = 'checkbox'; attention.name = 'needs-details';
  const attentionLabel = el('label', 'Needs details'); attentionLabel.className = 'purchase-attention-filter';
  attentionLabel.prepend(attention); controls.append(attentionLabel);
  attention.onchange = () => { needsDetails = attention.checked; renderRows(); };
  if (!isStaticSite) {
    const add = action('Add item', () => {
      const record = newPurchase(); const name = prompt('Item or service name'); if (!name?.trim()) return;
      record.name = name.trim(); record.category = filter.category; record.tags = filter.tag ? [filter.tag] : [];
      record.supplier = filter.supplier;
      // New items start unbought; show them even if this view was previously showing only bought stock.
      filter.status = ''; filter.search = ''; search.value = ''; onFilter?.({ ...filter }); save(record);
    });
    add.className = 'purchase-add'; controls.append(add);
  }
  const clear = action('Clear filters', () => {
    filter = emptyFilter(); needsDetails = false; attention.checked = false;
    search.value = ''; onFilter?.({ ...filter }); render();
  });
  controls.append(clear);

  function render() {
    if (!data || disposed) return;
    for (const [key, input] of selectInputs) {
      const values = key === 'status' ? data.rows.map(r => r.status)
        : key === 'tag' ? data.rows.flatMap(r => r.record.tags)
        : data.rows.map(r => r.record[key as 'category' | 'supplier']);
      const current = filter[key as keyof PurchaseFilter];
      input.replaceChildren(new Option(`All ${key === 'category' ? 'categories' : key === 'status' ? 'statuses' : key + 's'}`, ''),
        ...[...new Set([...values, current])].filter(Boolean).sort().map(v => new Option(v, v)));
      input.value = current;
    }
    renderRows();
  }
  function renderRows() {
    if (!data || disposed) return;
    const rows = data.rows.filter(r => matches(r, filter) && (!needsDetails || missingDetails(r).length));
    if (sort) {
      const { key, direction } = sort;
      rows.sort((a, b) => {
        const first = sortValue(a, key), second = sortValue(b, key);
        // Unknown quantities/prices stay last in either direction; never treat them as zero.
        if (first === null && second !== null) return 1;
        if (second === null && first !== null) return -1;
        const comparison = typeof first === 'number' && typeof second === 'number' ? first - second
          : typeof first === 'string' && typeof second === 'string' ? itemOrder.compare(first, second) : 0;
        return comparison * (direction === 'ascending' ? 1 : -1)
          || itemOrder.compare(a.record.name, b.record.name) || itemOrder.compare(a.record.id, b.record.id);
      });
    }
    const filtered = Object.values(filter).some(Boolean) || needsDetails;
    clear.hidden = !filtered;
    const totals = data.totals;
    const amounts = el('dl'); amounts.className = 'purchase-amounts';
    for (const [label, amount] of [
      [totals.unknown_remaining || totals.unknown_spent ? 'Partial project estimate' : 'Project estimate', totals.forecast],
      ['Spent', totals.spent], ['Remaining estimate', totals.remaining],
    ] as const) {
      const metric = el('div'); metric.append(el('dt', label), el('dd', money(amount))); amounts.append(metric);
    }
    const notes = el('div'); notes.className = 'purchase-cost-notes';
    notes.append(el('span', 'NZD incl. GST'));
    const missing = data.rows.filter(r => missingDetails(r).length).length;
    if (missing) {
      const showMissing = action(`${missing} ${missing === 1 ? 'item needs' : 'items need'} details`, () => {
        filter = emptyFilter(); search.value = ''; needsDetails = true; attention.checked = true;
        onFilter?.({ ...filter }); render(); attention.focus();
      });
      showMissing.className = 'purchase-missing-link'; notes.append(showMissing);
    }
    summary.replaceChildren(amounts, notes);
    const shown = sum(rows);
    result.textContent = `${rows.length} of ${data.rows.length} items`
      + (filtered ? ` · shown: ${money(shown.spent)} spent, ${money(shown.remaining)} remaining estimate` : '')
      + (sort ? ` · ${columns.find(([, key]) => key === sort?.key)?.[0]}, ${sort.direction}` : '');
    const table = el('table'); table.className = 'purchase-grid';
    const caption = el('caption', 'Purchases and quantities. Activate a column header to sort. Unknown values appear last.');
    caption.className = 'visually-hidden'; table.append(caption);
    const head = el('tr');
    columns.forEach(([label, key]) => {
      const th = el('th'); th.scope = 'col';
      if (key === null) {
        const label = el('span', 'Item actions'); label.className = 'visually-hidden'; th.append(label);
      } else {
        const activeSort = sort?.key === key ? sort : null;
        const nextDirection = activeSort?.direction === 'ascending' ? 'descending' : 'ascending';
        if (activeSort) th.setAttribute('aria-sort', activeSort.direction);
        const button = action(label, () => {
          sort = { key, direction: nextDirection };
          localStorage.setItem(sortStorageKey, JSON.stringify(sort)); renderRows();
          content.querySelector<HTMLButtonElement>(`button[data-sort="${key}"]`)?.focus({ preventScroll: true });
        });
        button.className = 'purchase-sort'; button.dataset.sort = key;
        button.title = `Sort by ${label.toLowerCase()}, ${nextDirection}`;
        const icon = el('span', activeSort ? activeSort.direction === 'ascending' ? '↑' : '↓' : '↕');
        icon.className = 'purchase-sort-icon'; icon.setAttribute('aria-hidden', 'true'); button.append(icon);
        th.append(button);
      }
      head.append(th);
    });
    const thead = el('thead'); thead.append(head); table.append(thead);
    const body = el('tbody'); table.append(body); content.replaceChildren(table);
    if (!rows.length) {
      const empty = el('div'); empty.className = 'purchase-empty';
      empty.append(el('strong', data.rows.length ? 'No matching items' : 'No purchases yet'),
        el('p', data.rows.length ? 'Try a different search or clear the filters.' : 'Add an item to start the shopping list.'));
      content.append(empty);
      return;
    }
    for (const row of rows) {
      let record = structuredClone(row.record);
      const tr = el('tr'); tr.className = 'purchase-row';
      const cells = Array.from({ length: columns.length }, () => el('td'));
      const item = el('th'); item.scope = 'row'; tr.append(item, ...cells.slice(1)); body.append(tr);
      const detailRow = el('tr'); detailRow.className = 'purchase-detail-row'; detailRow.hidden = !expanded.has(record.id);
      const detailCell = el('td'); detailCell.colSpan = columns.length; detailRow.append(detailCell); body.append(detailRow);
      const detail = el('form'); detail.className = 'purchase-item-details'; detailCell.append(detail);
      detail.setAttribute('aria-label', `${record.name}: details`);
      const detailInputs = new Map<keyof PurchaseRecord, HTMLInputElement>();
      const detailBaseline = new Map<keyof PurchaseRecord, string>();
      const detailId = `purchase-${crypto.randomUUID()}`; detailRow.id = detailId;
      const issues = missingDetails(row);
      tr.classList.toggle('purchase-incomplete', issues.length > 0);
      const edit = (cell: HTMLElement, key: keyof PurchaseRecord, label: string, numeric = false, deferred = false) => {
        if (isStaticSite) {
          const value = key === 'required' ? record.required ?? row.required : record[key];
          const text = key === 'tags' ? record.tags.join(', ') : value === null ? 'Unknown' : String(value ?? '');
          const display = el('span', text); display.style.whiteSpace = 'pre-wrap'; cell.append(display);
          return;
        }
        const input = el('input'); input.type = numeric ? 'number' : key === 'url' ? 'url' : 'text';
        input.name = key; input.autocomplete = 'off'; input.setAttribute('aria-label', `${record.name}: ${label}`);
        input.dataset.purchaseId = record.id; input.dataset.field = key;
        input.value = key === 'required' ? String(record.required ?? row.required ?? '')
          : fieldText(record, key);
        if (numeric) {
          input.min = '0'; input.step = key === 'unit_price' || key === 'spent' ? '0.01' : 'any';
          input.placeholder = key === 'required' && row.required !== null ? String(row.required) : '—';
          if (key === 'required') input.title = row.required === null ? 'Quantity not established' : `Model requirement: ${row.required}. Leave blank to use this quantity.`;
        }
        const draftKey = record.id + ':' + key;
        let committed = input.value;
        if (deferred) { detailInputs.set(key, input); detailBaseline.set(key, committed); }
        input.value = client.getDraft(draftKey) ?? input.value;
        input.oninput = () => client.setDraft(draftKey, input.value !== committed, input.value);
        input.onchange = () => {
          if (deferred) return;
          if (!input.checkValidity()) { input.reportValidity(); return; }
          record = { ...(client.document?.purchases[record.id] ?? record), [key]: fieldValue(input, key) };
          if ((key === 'category' && filter.category) || (key === 'tags' && filter.tag) || (key === 'supplier' && filter.supplier)) {
            feedback.textContent = 'Changing this field may move the item outside this filter.';
          }
          committed = input.value; client.setDraft(draftKey, false); save(record);
        };
        cell.append(input); return input;
      };
      item.append(el('strong', record.name));
      const metadata = el('div'); metadata.className = 'purchase-item-meta';
      if (record.url && safeURL(record.url)) {
        const link = el('a', record.supplier || 'Product details'); link.href = record.url;
        link.target = '_blank'; link.rel = 'noopener noreferrer'; metadata.append(link);
      } else if (record.supplier) metadata.append(el('span', record.supplier));
      const state = el('span', row.status); state.className = 'purchase-state';
      state.dataset.complete = String(row.remaining === 0); metadata.append(state); item.append(metadata);
      if (issues.length) {
        const warnings = el('div'); warnings.className = 'purchase-missing';
        for (const issue of issues) warnings.append(el('span', issue));
        item.append(warnings);
      }
      const distinctUses = row.uses.filter(use => use.toLowerCase() !== record.name.toLowerCase());
      if (distinctUses.length) {
        const uses = el('small', distinctUses.join(', ')); uses.className = 'purchase-uses'; item.append(uses);
      }
      for (const [key, label] of [['name', 'Item name'], ['supplier', 'Supplier'], ['url', 'Product URL'],
        ['category', 'Category'], ['tags', 'Tags (comma separated)'], ['unit', 'Purchase unit'],
        ['spent', 'Actual spent (NZD, optional)'], ['notes', 'Notes']] as const) {
        const field = el('label', label); field.className = `purchase-field purchase-field-${key}`;
        const input = edit(field, key, label, key === 'spent', true);
        if (input && key === 'name') input.required = true;
        detail.append(field);
      }
      if (row.shared) detail.append(el('p', 'Shared stock is counted once across its uses.'));
      if (row.legacy_owned) detail.append(el('p', 'Existing stock counts towards the required quantity and reduces what remains to buy.'));
      const requiredInput = edit(cells[1], 'required', 'Required quantity (blank uses model count)', true);
      if (row.required === null) {
        requiredInput?.setAttribute('data-missing', 'true'); cells[1].append(el('small', 'Quantity missing'));
      }
      cells[1].append(el('small', record.unit));
      const owned = row.owned ?? record.owned;
      if (owned > record.owned) {
        cells[2].append(el('span', String(owned)), el('small', 'Existing stock'));
      } else edit(cells[2], 'owned', 'Already owned quantity', true);
      edit(cells[3], 'bought', 'Bought quantity', true);
      const priceInput = edit(cells[4], 'unit_price', 'Estimated price per purchase unit (NZD)', true);
      if (issues.includes('Price missing')) {
        priceInput?.setAttribute('data-missing', 'true'); cells[4].append(el('small', 'Price missing'));
      }
      const remainingCost = el('strong', row.remaining_cost === null ? 'Cost unknown' : money(row.remaining_cost));
      remainingCost.className = 'purchase-to-buy-price';
      cells[5].append(remainingCost,
        el('small', row.remaining === null ? 'Quantity unknown' : `${row.remaining} ${record.unit}`));
      if (row.status === 'Unused stock') cells[1].append(el('small', 'Not in current model'));
      const details = action(isStaticSite ? 'Details' : '', () => {
        detailRow.hidden = isStaticSite ? !detailRow.hidden : false;
        if (detailRow.hidden) expanded.delete(record.id); else expanded.add(record.id);
        details.setAttribute('aria-expanded', String(!detailRow.hidden));
        if (!isStaticSite) detailInputs.values().next().value?.focus();
      });
      if (!isStaticSite) {
        details.className = 'purchase-edit'; details.title = 'Edit details';
        details.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none"'
          + ' stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
          + '<path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15z"/></svg>';
      }
      details.setAttribute('aria-expanded', String(!detailRow.hidden)); details.setAttribute('aria-controls', detailId);
      details.setAttribute('aria-label', `${record.name}: ${isStaticSite ? 'details' : 'edit details'}`);
      details.dataset.purchaseId = record.id; details.dataset.field = 'details';
      cells[6].append(details);
      if (isStaticSite) continue;
      const closeDetails = () => {
        for (const key of detailInputs.keys()) client.setDraft(record.id + ':' + key, false);
        expanded.delete(record.id); renderRows();
        const pencil = [...content.querySelectorAll<HTMLButtonElement>('.purchase-edit')]
          .find(button => button.dataset.purchaseId === record.id);
        pencil?.focus({ preventScroll: true });
      };
      const actions = el('div'); actions.className = 'purchase-detail-actions'; detail.append(actions);
      if (!row.generated) actions.append(action('Delete item', () => {
        if (!confirm(`Delete ${record.name}${record.bought || record.spent ? ' and its purchase/spending record' : ''}? You can Undo this.`)) return;
        try {
          client.mutate({ kind: 'delete_purchase', id: record.id }, false);
          for (const key of detailInputs.keys()) client.setDraft(record.id + ':' + key, false);
          expanded.delete(record.id);
        } catch (error) { feedback.textContent = String(error); }
      }));
      const cancel = action('Cancel', closeDetails); cancel.className = 'purchase-detail-cancel';
      const submit = el('button', 'Save'); submit.type = 'submit'; submit.className = 'purchase-detail-save';
      actions.append(cancel, submit);
      detail.onsubmit = async event => {
        event.preventDefault();
        if (!detail.reportValidity()) return;
        const changes: Record<string, unknown> = {};
        for (const [key, input] of detailInputs) {
          if (input.value !== detailBaseline.get(key)) changes[key] = fieldValue(input, key);
        }
        if (!Object.keys(changes).length) { closeDetails(); return; }
        const updated = { ...(client.document?.purchases[record.id] ?? record), ...changes };
        if (!save(updated)) return;
        submit.disabled = true; cancel.disabled = true;
        try { await client.flush(false); closeDetails(); }
        catch (error) { feedback.textContent = String(error); }
        finally { submit.disabled = false; cancel.disabled = false; }
      };
    }
  }
  async function refresh() {
    const ticket = ++serial;
    try {
      const next = await client.purchases();
      if (disposed || ticket !== serial) return;
      data = next; feedback.textContent = client.status;
      // A completed save may arrive while the next cell is being typed in. Preserve its unsaved draft and caret.
      const active = document.activeElement instanceof HTMLElement && content.contains(document.activeElement)
        ? document.activeElement : null;
      const draft = active instanceof HTMLInputElement
        ? { value: active.value, start: active.selectionStart, end: active.selectionEnd } : null;
      const focus = active ? { id: active.dataset.purchaseId, field: active.dataset.field, sort: active.dataset.sort } : null;
      render();
      if (focus?.id) {
        const replacement = [...content.querySelectorAll<HTMLElement>('[data-purchase-id][data-field]')]
          .find(input => input.dataset.purchaseId === focus.id && input.dataset.field === focus.field);
        if (replacement) {
          replacement.focus({ preventScroll: true });
          if (draft && replacement instanceof HTMLInputElement) {
            replacement.value = draft.value;
            if (draft.start !== null) replacement.setSelectionRange(draft.start, draft.end);
          }
        }
      } else if (focus?.sort) {
        content.querySelector<HTMLButtonElement>(`button[data-sort="${focus.sort}"]`)?.focus({ preventScroll: true });
      }
    } catch (error) { if (!disposed) feedback.textContent = String(error); }
  }
  const undo = action('Undo purchase', () => client.undoPurchase());
  const redo = action('Redo purchase', () => client.redoPurchase());
  if (!isStaticSite) controls.append(undo, redo);
  const status = () => {
    undo.disabled = !client.canUndoPurchase; redo.disabled = !client.canRedoPurchase;
    feedback.textContent = client.error ? client.status + ': ' + client.error
      + (isStaticSite ? '' : ' — use Plan → Reload or recovery controls.') : client.status;
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
