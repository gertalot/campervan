import { request, type ModelStatus, type Parameters } from './api';
import type { PlanningClient } from './planning-api';
import { mountPurchaseGrid } from './purchase-grid';
import { onTab, showTab } from './tabs';

interface Role { id: string; name: string; kind: 'sheet' | 'timber' | 'hardware'; fields: Record<string, string>; note: string; quantity: number | null }
interface Product {
  id: string; name: string; supplier: string; url: string; kind: string;
  dimensions: Record<string, number>; specification: string; checked: string;
  price_nzd: number | null; sale_unit: string; pack_quantity: number; availability: string;
}
interface Selection { product_id: string | null; measured: Record<string, number>; owned: boolean; purchase_quantity: number | null }
interface Cut { path: string; material: string; length: number; width: number; thickness: number }
interface Materials {
  roles: Role[]; products: Product[]; selections: Record<string, Selection>; parameters: Parameters;
  cuts: Cut[]; cuts_revision: number | null; requested_revision: number;
}
interface MaterialUse { role: Role; cuts: Cut[]; owned: boolean }
interface StockGroup { key: string; product?: Product; uses: MaterialUse[] }

function stockGroups(data: Materials): StockGroup[] {
  const groups = new Map<string, StockGroup>();
  for (const role of data.roles) {
    const selection = data.selections[role.id];
    const product = data.products.find(p => p.id === selection?.product_id);
    // Unspecified stock stays separate: equal thickness alone does not make materials interchangeable.
    const key = product ? `product-${product.id}` : `custom-${role.id}`;
    if (!groups.has(key)) groups.set(key, { key, product, uses: [] });
    groups.get(key)!.uses.push({ role, cuts: data.cuts.filter(c => c.material === role.id),
      owned: selection?.owned ?? role.id === 'slats' });
  }
  return [...groups.values()];
}

const el = <K extends keyof HTMLElementTagNameMap>(tag: K, text = '') => {
  const node = document.createElement(tag); node.textContent = text; return node;
};
const size = (cut: Cut) => `${cut.length} × ${cut.width} × ${cut.thickness}`;

export function setupMaterials(client: PlanningClient) {
  const panel = document.getElementById('bom-panel')!;
  let purchaseGrid: ReturnType<typeof mountPurchaseGrid> | null = null;
  let data: Materials | null = null;
  let loading = false;
  let statusKey = '';
  let stale = true;
  let modelError = '';
  let focusRole: string | undefined;
  let scrollToRole = false;
  const expandedGroups = new Set<string>();
  const feedback = el('p'); feedback.className = 'bom-feedback'; feedback.setAttribute('role', 'status');

  function setExpanded(body: HTMLTableSectionElement, expanded: boolean) {
    const key = body.dataset.stock!;
    if (expanded) expandedGroups.add(key); else expandedGroups.delete(key);
    body.querySelector<HTMLTableRowElement>('.stock-detail')!.hidden = !expanded;
    body.querySelector<HTMLButtonElement>('.stock-toggle')!.setAttribute('aria-expanded', String(expanded));
  }

  function highlightMaterial() {
    for (const body of panel.querySelectorAll<HTMLTableSectionElement>('tbody[data-stock]')) {
      let selectedUse: HTMLElement | undefined;
      for (const use of body.querySelectorAll<HTMLElement>('.material-use')) {
        const selected = use.id === `material-${focusRole}`;
        use.classList.toggle('material-highlight', selected);
        if (selected) selectedUse = use;
      }
      body.querySelector('.stock-summary')!.classList.toggle('material-highlight', Boolean(selectedUse));
      if (selectedUse && scrollToRole && !panel.hidden) {
        setExpanded(body, true);
        selectedUse.scrollIntoView({ block: 'center' });
        scrollToRole = false;
      }
    }
  }

  onTab((tab, role) => {
    if (tab !== 'bom') return;
    focusRole = role; scrollToRole = Boolean(role);
    const detail = panel.querySelector<HTMLDetailsElement>('.cad-stock-details');
    if (role && detail) detail.open = true;
    highlightMaterial();
    if (stale || !data) void refresh();
    else void purchaseGrid?.refresh();
  });

  async function refresh() {
    if (loading) return;
    loading = true;
    try {
      data = await request<Materials>('materials'); stale = false; render(data);
      highlightMaterial();
    } catch (error) {
      feedback.textContent = String(error);
      if (!feedback.isConnected) panel.append(feedback);
    } finally { loading = false; }
  }

  function render(data: Materials) {
    const host = document.getElementById('bom-panel')!;
    purchaseGrid?.destroy(); host.replaceChildren();
    host.append(el('h2', 'Bill of materials & purchases'));
    const purchaseHost = el('div'); host.append(purchaseHost);
    purchaseGrid = mountPurchaseGrid(purchaseHost, client);
    const details = el('details'); details.className = 'cad-stock-details';
    details.open = Boolean(focusRole); details.append(el('summary', 'CAD stock and cutting details'));
    const panel = el('div'); details.append(panel); host.append(details);
    const groups = stockGroups(data);
    const intro = el('div'); intro.className = 'bom-intro';
    intro.append(el('h2', 'Bill of materials'), el('p', 'By material / product · NZD incl. GST · freight excluded'));
    panel.append(intro, feedback);
    feedback.textContent = modelError || (data.cuts_revision === data.requested_revision ? ''
      : 'Cut quantities await regeneration; any displayed parts are from the previous model.');
    const table = el('table'); table.className = 'materials-table';
    const head = el('tr');
    for (const title of ['Material / product', 'Combined requirement', 'Price', 'Availability']) {
      const th = el('th', title); th.scope = 'col'; head.append(th);
    }
    const thead = el('thead'); thead.append(head); table.append(thead); panel.append(table);
    const money = (value: number) => `$${value.toFixed(2)}`;
    for (const group of groups) {
      const { product, uses } = group;
      const cuts = uses.flatMap(use => use.cuts);
      const toBuy = uses.filter(use => !use.owned);
      const owned = !toBuy.length;
      const kind = product?.kind ?? uses[0].role.kind;
      const body = el('tbody'); body.dataset.stock = group.key;
      const row = el('tr'); row.className = 'stock-summary';
      const productCell = el('td'); const required = el('td');
      const price = el('td'); price.className = 'bom-price'; const availability = el('td');
      row.append(productCell, required, price, availability); body.append(row); table.append(body);

      const toggle = el('button'); toggle.type = 'button'; toggle.className = 'stock-toggle';
      toggle.setAttribute('aria-label', `Show uses and cut list for ${product?.name ?? uses[0].role.name}`);
      const label = el('div'); label.className = 'stock-label';
      const title = el('div'); title.className = 'stock-title'; title.append(toggle, label); productCell.append(title);
      if (product) {
        const link = el('a', `${product.name} ↗`);
        link.href = product.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
        link.className = 'product-link'; label.append(link, el('small', product.supplier));
        if (kind !== 'hardware') label.append(el('small',
          `${product.dimensions.length} × ${product.dimensions.width} × ${product.dimensions.thickness} mm stock`));
        price.append(el('strong', product.price_nzd === null ? 'Price not published' : money(product.price_nzd)),
          el('small', `/ ${product.sale_unit}`));
        availability.append(el('p', product.availability), el('small', `Checked ${product.checked}`));
      } else {
        label.append(el('strong', uses[0].role.name), el('small', owned ? 'Reused stock' : 'Supplier match needed'));
        price.append(el('strong', owned ? '$0.00' : '—'));
      }
      label.append(el('small', uses.map(use => use.role.name).join(' · ')));
      const mismatch = product && uses.some(({ role }) => Object.entries(role.fields)
        .some(([dimension, parameter]) => data.parameters[parameter] !== product.dimensions[dimension]));
      const oversized = product && kind !== 'hardware' && cuts.some(c =>
        c.length > product.dimensions.length || c.width > product.dimensions.width || c.thickness > product.dimensions.thickness);
      if (mismatch || oversized) {
        const warning = el('span', 'Stock allowance / measured size — see uses'); warning.className = 'bom-warning'; label.append(warning);
      }
      if (kind === 'hardware') {
        const quantities = toBuy.map(use => use.role.quantity ?? (use.cuts.length || null));
        const count = quantities.every(q => q !== null) ? quantities.reduce<number>((sum, q) => sum + q!, 0) : null;
        required.append(el('strong', owned ? 'Already owned' : count === null ? 'Count to confirm' : `${count} needed`));
        if (count !== null && product && !owned) {
          const packs = Math.ceil(count / product.pack_quantity);
          required.append(el('p', `Buy ${packs} × ${product.sale_unit}`));
          if (product.price_nzd !== null) price.append(el('small', `${money(packs * product.price_nzd)} total`));
        }
      } else {
        required.append(el('strong', cuts.length ? `${cuts.length} pieces` : 'Awaiting cut list'));
        if (cuts.length) required.append(el('p', kind === 'sheet'
          ? `${(cuts.reduce((sum, c) => sum + c.length * c.width, 0) / 1e6).toFixed(2)} m² cutting rectangles`
          : `${(cuts.reduce((sum, c) => sum + c.length, 0) / 1000).toFixed(2)} m cut length`));
        required.append(el('small', owned ? 'Already owned' : 'Purchase count needs cutting layout'));
      }
      if (owned) availability.replaceChildren(el('span', 'Already owned'));
      else if (toBuy.length < uses.length) required.append(el('small', 'Includes owned parts — see uses'));

      const detailRow = el('tr'); detailRow.className = 'stock-detail'; detailRow.id = `detail-${group.key}`;
      const detailCell = el('td'); detailCell.colSpan = 4; detailRow.append(detailCell); body.append(detailRow);
      toggle.setAttribute('aria-controls', detailRow.id);
      toggle.addEventListener('click', () => setExpanded(body, detailRow.hidden));
      setExpanded(body, expandedGroups.has(group.key));
      if (product) {
        const spec = el('p', product.specification); spec.className = 'stock-spec'; detailCell.append(spec);
      }
      const breakdown = el('div'); breakdown.className = 'stock-breakdown'; detailCell.append(breakdown);
      const useList = el('div'); useList.append(el('h3', 'Used by'));
      const cutList = el('div'); cutList.append(el('h3', kind === 'hardware' ? 'Parts' : 'Combined cut list · mm'));
      breakdown.append(useList, cutList);
      for (const use of uses) {
        const { role } = use;
        const section = el('section'); section.className = 'material-use'; section.id = `material-${role.id}`;
        const count = role.quantity ?? (use.cuts.length || null);
        section.append(el('strong', `${role.name}${count === null ? '' : ` · ${count} ${kind === 'hardware' ? 'needed' : 'pieces'}`}${use.owned ? ' · already owned' : ''}`));
        if (role.note) section.append(el('p', role.note));
        for (const [dimension, parameter] of Object.entries(role.fields)) {
          const current = data.parameters[parameter];
          const stock = product?.dimensions[dimension];
          if (stock === undefined || current !== stock) {
            const note = el('p', stock === undefined ? `Model ${dimension}: ${current} mm`
              : `${dimension}: measured ${current} mm · listed stock ${stock} mm`);
            if (stock !== undefined) note.className = 'bom-warning'; section.append(note);
          }
        }
        const assemblies = [...new Set(use.cuts.map(c => c.path.split(' / ').slice(0, -1).join(' / ')))];
        if (assemblies.length) section.append(el('small', assemblies.join(' · ')));
        useList.append(section);
      }
      const sizes = new Map<string, Cut[]>();
      for (const cut of cuts) { const key = size(cut); sizes.set(key, [...(sizes.get(key) ?? []), cut]); }
      for (const [dimensions, parts] of sizes) {
        const entry = el('details'); entry.className = 'cut-size';
        entry.append(el('summary', `${parts.length} × ${dimensions}`));
        for (const part of parts) entry.append(el('p', part.path));
        cutList.append(entry);
      }
      if (!cuts.length) cutList.append(el('p', kind === 'hardware' ? 'No modelled parts; requirement noted under uses.' : 'Awaiting cut list.'));
      if (oversized) { const note = el('p', 'Some cuts exceed the stock dimensions.'); note.className = 'bom-warning'; cutList.append(note); }
    }
    const unassigned = data.cuts.filter(c => c.material === 'unassigned');
    if (unassigned.length) {
      const rest = el('details'); rest.className = 'bom-unassigned';
      rest.append(el('summary', `Stock not assigned (${unassigned.length} modelled parts)`));
      for (const cut of unassigned) rest.append(el('p', `${cut.path} · ${size(cut)} mm envelope`));
      panel.append(rest);
    }
    panel.append(el('p', 'Sheet and timber purchase counts need a cutting layout allowing for kerf, grain and waste. Selected stock dimensions drive the model.'));
    panel.append(el('p', 'Still to detail: drawer restraint / M5 slide fixings, lid screws, timber joint fixings and adhesive. Existing cushions and vehicle are outside this furniture shopping list.'));
  }
  return {
    show: (role?: string) => showTab('bom', role),
    onStatus(status: ModelStatus) {
      modelError = status.error ? `Regeneration failed: ${status.error.message}` : '';
      const key = `${status.session_id}:${status.requested_revision}:${status.state}`;
      if (key !== statusKey) {
        statusKey = key; stale = true;
        client.refreshPurchases();
        if (!panel.hidden) void refresh();
      }
    },
  };
}
