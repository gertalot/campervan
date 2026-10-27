import { request, type ModelStatus } from './api';
import { onTab, showTab } from './tabs';
import { createPlanDropdown } from './plan-dropdown';
import { pieceGallery, sheetDrawing } from './cutting-diagrams';
import { assembly, csv, download, el, fullName, isPlywood, materialName, mm, option, partColour, pieceKey } from './cutting-types';
import type { Data, Grain, Group, Mode, Part, Result, StockOptions } from './cutting-types';
import './cutting.css';

const methodNames: Record<Mode, string> = { straight: 'Straight saw cuts', nesting: 'Nested shapes' };

export function setupCutting(host: HTMLElement, showInCad: (path: string) => void) {
  let data: Data | null = null, filter = 'all', loading = false, statusKey = '', modelSession = '', savingFailed = false;
  let pending = Promise.resolve();
  let refreshPromise: Promise<void> | null = null, selectedPath: string | null = null, pointerX: number | null = null;
  let returnSpot: { path: string; filter: string; scroll: number } | null = null;
  const pieceMenu = createPlanDropdown();
  const starting = new Set<string>(), errors = new Map<string, string>(), attempted = new Set<string>();
  let progressLoading = false;
  const layoutHosts = new Map<string, HTMLElement>();
  const openDetails = new Set<string>();
  const feedback = el('p'); feedback.className = 'cut-feedback'; feedback.setAttribute('role', 'status');
  const content = el('div'); content.className = 'cut-content';
  const inspector = el('dialog'); inspector.className = 'cut-inspector'; inspector.setAttribute('aria-label', 'Wood piece details');
  inspector.addEventListener('click', event => { if (event.target === inspector) inspector.close(); });
  function goToCad(path: string) {
    returnSpot = { path, filter, scroll: host.scrollTop };
    inspector.close(); showInCad(path);
  }
  function clearSelection() {
    selectedPath = null; inspector.close();
    markSelected();
  }
  function pieceAt(event: Event) {
    return (event.target as Element).closest<HTMLElement | SVGElement>('[data-part]')?.dataset.part;
  }
  host.addEventListener('pointerdown', event => { pointerX = event.clientX; });
  host.addEventListener('keydown', event => {
    pointerX = null;
    if (event.key === 'ContextMenu' || (event.key === 'F10' && event.shiftKey)) {
      const path = pieceAt(event);
      if (path) { event.preventDefault(); openPieceMenu(path, event.target as HTMLElement); }
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || host.hidden || event.defaultPrevented || (!selectedPath && !inspector.open)) return;
    // Menus dismiss themselves first. Selection also clears when a layout refresh
    // has removed the focused piece and keyboard focus has returned to the body.
    if ((event.target as Element).closest('[role="menu"]')) return;
    event.preventDefault(); clearSelection();
  }, true);
  host.addEventListener('dblclick', event => {
    const path = pieceAt(event);
    if (path) { event.preventDefault(); goToCad(path); }
  });
  function openPieceMenu(path: string, trigger?: HTMLElement, x?: number, y?: number) {
    pieceMenu.open({ label: 'Piece actions', trigger, x, y, items: [
      { label: 'Show in 3D', group: 'piece', shortcut: 'Double-click', run: () => goToCad(path) },
      { label: 'Piece details', group: 'piece', run: () => selectPart(path) },
      { label: 'Clear selection', group: 'selection', shortcut: 'Esc', ariaShortcut: 'Escape', run: clearSelection },
    ] });
  }
  host.addEventListener('contextmenu', event => {
    const path = pieceAt(event);
    if (path) { event.preventDefault(); openPieceMenu(path, undefined, event.clientX, event.clientY); }
  });
  host.addEventListener('pointerover', event => {
    const piece = (event.target as Element).closest<HTMLElement | SVGElement>('[data-part]');
    if (piece && !piece.getAttribute('title')?.includes('Double-click')) {
      piece.setAttribute('title', `${piece.getAttribute('title') ?? ''}\nDouble-click to show in 3D`.trim());
      const title = piece.querySelector('title');
      if (title && !title.textContent?.includes('Double-click')) title.textContent += '\nDouble-click to show in 3D';
    }
  });
  document.addEventListener('pointerdown', event => {
    if (inspector.open && !inspector.contains(event.target as Node)
      && !(event.target as Element).closest('[data-part]')) inspector.close();
  });

  const mode = () => data!.state.settings.algorithm;
  const resultKey = (g: Group) => `${g.key}:${mode()}`;
  const groupOptions = (g: Group): StockOptions => data!.state.options[g.key] ??= {
    confirmed: false, orientations: {}, stock: structuredClone(g.stock),
  };
  function filteredGroups() {
    return data!.groups.filter(g => filter === 'all' || (filter === 'timber' && g.kind === 'timber')
      || filter === `sheet:${g.key}`
      || (filter.startsWith('ply:') && isPlywood(g) && g.thickness === Number(filter.slice(4))))
      .sort((a, b) => Number(b.stock_sourced) - Number(a.stock_sourced));
  }
  function isCurrent(g: Group, result: Result) {
    return data!.current && result.source === data!.sources[g.key];
  }
  function message(text: string) { feedback.textContent = text; feedback.hidden = !text; }
  function save(path: string, body: unknown) {
    const snapshot = structuredClone(body);
    pending = pending.then(async () => {
      const fresh = await request<Data>(path, 'PUT', snapshot);
      data!.sources = fresh.sources; data!.current = fresh.current;
      data!.jobs = fresh.jobs;
      savingFailed = false;
      if (filter !== 'all') { renderFocus(); startFocusedLayouts(); }
      else message('Cutting settings saved for the whole project.');
    }).catch(error => { savingFailed = true; message(`Could not save cutting settings: ${error.message}`); });
  }
  function settingsChanged() {
    attempted.clear(); save('cutting/settings', data!.state.settings);
  }
  function stockChanged(g: Group) {
    attempted.clear(); save('cutting/options', { group: g.key, options: groupOptions(g) });
  }
  function details(title: string, key: string) {
    const element = el('details'); element.open = openDetails.has(key); element.append(el('summary', title));
    element.addEventListener('toggle', () => element.open ? openDetails.add(key) : openDetails.delete(key));
    return element;
  }
  function numberField(parent: HTMLElement, title: string, value: number, update: (n: number) => void,
                       min = 0, max = 10000, integer = false) {
    const label = el('label', title), input = el('input'); input.type = 'number'; input.value = String(value);
    input.min = String(min); input.max = String(max); input.step = integer ? '1' : 'any';
    input.onchange = () => { if (input.reportValidity()) update(input.valueAsNumber); };
    label.append(input); parent.append(label); return input;
  }
  function globalSettings() {
    const settings = details('Cutting settings · apply to the whole project', 'global'); settings.className = 'cut-global-settings';
    const form = el('div'); form.className = 'cut-settings-fields';
    const methodLabel = el('label', 'Arrange sheets for'), select = el('select');
    select.append(option('straight', methodNames.straight), option('nesting', methodNames.nesting));
    select.value = mode(); select.onchange = () => { data!.state.settings.algorithm = select.value as Mode; settingsChanged(); };
    methodLabel.append(select); form.append(methodLabel);
    numberField(form, 'Blade kerf / tool width (mm)', data!.state.settings.kerf,
      n => { data!.state.settings.kerf = n; settingsChanged(); }, 0, 20);
    numberField(form, 'Trim from each sheet edge (mm)', data!.state.settings.trim,
      n => { data!.state.settings.trim = n; settingsChanged(); }, 0, 100);
    const grainLabel = el('label', 'Default grain direction'), grain = el('select');
    grain.append(option('length', 'Along each piece’s length'), option('width', 'Along each piece’s width'), option('free', 'Either direction'));
    grain.value = data!.state.settings.grain;
    grain.onchange = () => { data!.state.settings.grain = grain.value as Grain; settingsChanged(); };
    grainLabel.append(grain); form.append(grainLabel); settings.append(form);
    settings.append(el('p', 'Kerf is the material removed by a cut. Edge trim reserves a strip around the sheet; use 0 for untrimmed edges.'));
    settings.append(el('p', 'Straight saw cuts arrange rectangular blanks; their curves and holes are cut afterwards. Nested shapes fit the actual profiles together.'));
    return settings;
  }

  function refresh(): Promise<void> {
    if (refreshPromise) return refreshPromise;
    loading = true;
    const scroll = host.scrollTop;
    refreshPromise = (async () => {
      try { await pending; data = await request<Data>('cutting'); render(); host.scrollTop = scroll; }
      catch (error) { host.replaceChildren(feedback); message((error as Error).message); }
      finally { loading = false; refreshPromise = null; }
    })();
    return refreshPromise;
  }
  function render() {
    if (!data) return;
    layoutHosts.clear(); host.replaceChildren();
    const header = el('div'); header.className = 'cut-page-header';
    const title = el('div'); title.append(el('h2', 'Cut list'), el('p', `${data.groups.reduce((n, g) => n + g.parts.length, 0)} pieces from the van design · dimensions in mm`),
      el('p', 'Click a piece for details · double-click to show it in 3D'));
    const actions = el('div'); actions.className = 'cut-page-actions';
    const print = el('button', 'Print'); print.type = 'button'; print.onclick = () => window.print();
    const exportList = el('button', 'Export cut list'); exportList.type = 'button'; exportList.onclick = exportCsv;
    actions.append(print, exportList); header.append(title, actions);
    host.append(header, globalSettings());
    const filters = el('nav'); filters.className = 'cut-filters'; filters.setAttribute('aria-label', 'Show wood pieces');
    const choices = [['all', 'All pieces'], ...[...new Set(data.groups.filter(isPlywood).map(g => g.thickness))]
      .sort((a, b) => a - b).map(n => [`ply:${n}`, `${mm(n)} mm plywood`]),
      ...(data.groups.some(g => g.kind === 'timber') ? [['timber', 'Timber']] : []),
      ...data.groups.filter(g => g.kind === 'sheet' && !isPlywood(g))
        .map(g => [`sheet:${g.key}`, /bamboo/i.test(g.name) ? `${mm(g.thickness)} mm bamboo` : materialName(g)])];
    if (!choices.some(([key]) => key === filter)) filter = 'all';
    for (const [key, name] of choices) {
      const button = el('button', name); button.type = 'button'; button.setAttribute('aria-pressed', String(filter === key));
      button.onclick = () => { filter = key; render(); }; filters.append(button);
    }
    host.append(filters, feedback, content, inspector);
    if (!data.current) message('These pieces are from the previous CAD model. The updated model is still loading.');
    if (filter === 'all') renderOverview();
    else { renderFocus(); startFocusedLayouts(); }
    markSelected();
  }

  function renderOverview() {
    content.replaceChildren(); layoutHosts.clear();
    const parts = data!.groups.flatMap(g => g.parts);
    const groups = new Map<string, Part[]>();
    for (const part of parts) groups.set(assembly(part), [...(groups.get(assembly(part)) ?? []), part]);
    const overview = el('div'); overview.className = 'cut-overview';
    const order = ['Long bench', 'Cross bench', 'Cabinet', 'Drawer', 'Laptop table', 'Floor'];
    for (const [name, pieces] of [...groups].sort(([a], [b]) => order.indexOf(a) - order.indexOf(b))) {
      const section = el('section'); section.className = 'cut-assembly';
      const heading = el('div'); heading.className = 'cut-section-heading';
      const h3 = el('h3', name); h3.style.setProperty('--part-colour', partColour(pieces[0]));
      heading.append(h3, el('span', `${pieces.length} pieces`)); section.append(heading);
      section.append(pieceGallery(pieces, data!.groups, selectPart)); overview.append(section);
    }
    content.append(overview);
    content.append(el('p', 'Select a plywood thickness above for sheet layouts and its detailed cut list. Select a piece for its full name and measurements.'));
    const excluded = el('small', 'Vehicle references, cushions and purchased hardware are outside this cutting list.');
    content.append(excluded);
  }

  function selectPart(path: string) {
    const g = data!.groups.find(g => g.parts.some(p => p.path === path));
    const part = g?.parts.find(p => p.path === path); if (!g || !part) return;
    selectedPath = path; markSelected();
    inspector.replaceChildren();
    const close = el('button', 'Close'); close.type = 'button'; close.className = 'cut-inspector-close'; close.onclick = () => inspector.close();
    inspector.append(close, el('h2', fullName(part)), el('p', part.path.split(' / ').join(' › ')),
      pieceGallery([part], [g], () => {}), el('strong', `${mm(part.length)} × ${mm(part.width)} × ${mm(part.thickness)} mm`),
      el('p', materialName(g)));
    const show = el('button', 'Show in 3D'); show.type = 'button'; show.onclick = () => goToCad(path);
    show.title = 'Double-click a piece to show it in 3D'; inspector.append(show);
    const result = data!.state.results[resultKey(g)];
    const sheetIndex = result?.sheets.findIndex(s => s.parts.some(p => p.path === path)) ?? -1;
    if (sheetIndex >= 0) inspector.append(el('p', `${g.kind === 'timber' ? 'Timber length' : 'Sheet'} ${sheetIndex + 1}${isCurrent(g, result!) ? '' : ' · previous layout'}`));
    if (part.profile_note) inspector.append(el('p', part.profile_note));
    const matching = g.parts.filter(p => pieceKey(p) === pieceKey(part));
    if (matching.length > 1) {
      const names = el('ul');
      for (const piece of matching) names.append(el('li', piece.path.split(' / ').join(' › ')));
      inspector.append(el('h3', `${matching.length} matching pieces`), names);
    }
    const focus = el('button', `Show ${isPlywood(g) ? `${mm(g.thickness)} mm plywood` : g.kind === 'timber' ? 'timber' : 'this sheet material'}`);
    focus.type = 'button'; focus.onclick = () => {
      inspector.close(); filter = isPlywood(g) ? `ply:${g.thickness}` : g.kind === 'timber' ? 'timber' : `sheet:${g.key}`; render();
    }; inspector.append(focus);
    inspector.style.width = pointerX === null ? 'min(560px, calc(100vw - 32px))' : 'min(560px, 44vw)';
    inspector.style.left = pointerX !== null && pointerX > window.innerWidth / 2 ? '16px' : 'auto';
    inspector.style.right = pointerX !== null && pointerX > window.innerWidth / 2 ? 'auto' : '16px';
    const focused = document.activeElement as HTMLElement | null;
    if (!inspector.open) inspector.show();
    if (pointerX !== null) focused?.focus({ preventScroll: true });
  }
  function markSelected() {
    for (const node of host.querySelectorAll<HTMLElement | SVGElement>('[data-part]')) {
      node.classList.toggle('cut-selected', Boolean(selectedPath && represents(node, selectedPath)));
    }
    for (const svg of host.querySelectorAll('.cut-sheet-svg')) {
      svg.classList.toggle('has-selection', Boolean(svg.querySelector('.cut-selected')));
    }
  }
  function represents(node: HTMLElement | SVGElement, path: string) {
    return node.dataset.part === path || (JSON.parse(node.dataset.partPaths ?? '[]') as string[]).includes(path);
  }

  function renderFocus() {
    content.replaceChildren(); layoutHosts.clear();
    for (const g of filteredGroups()) {
      const section = el('section'); section.className = 'cut-material';
      const header = el('div'); header.className = 'cut-section-heading';
      header.append(el('h3', materialName(g)), el('span', `${g.parts.length} pieces`)); section.append(header);
      const layoutHost = el('div'); layoutHosts.set(g.key, layoutHost); section.append(layoutHost);
      section.append(stockSettings(g));
      const partsHeading = el('h4', 'Pieces in this material'); section.append(partsHeading, pieceGallery(g.parts, [g], selectPart));
      const cutList = details(`Cut list · ${g.parts.length} pieces and dimensions`, `parts:${g.key}`);
      cutList.className = 'cut-detail-list'; cutList.append(partTable(g)); section.append(cutList);
      content.append(section); renderLayouts(g);
    }
  }
  function stockSettings(g: Group) {
    const opts = groupOptions(g), stock = details('Sheet sizes & offcuts', `stock:${g.key}`); stock.className = 'cut-stock';
    if (g.kind === 'timber') stock.querySelector('summary')!.textContent = 'Timber lengths & offcuts';
    if (!g.stock_sourced && !opts.confirmed) {
      stock.open = true;
      stock.append(el('p', 'No stock size has been selected for this material. Enter the available dimensions below.'));
      const confirm = el('button', 'Use these stock sizes'); confirm.type = 'button';
      confirm.onclick = () => { opts.confirmed = true; stockChanged(g); }; stock.append(confirm);
    }
    for (const [index, entry] of opts.stock.entries()) {
      const row = el('div'); row.className = 'cut-stock-row'; row.append(el('strong', entry.name));
      numberField(row, 'Length (mm)', entry.length, n => { entry.length = n; stockChanged(g); }, 1);
      const width = numberField(row, 'Width (mm)', entry.width, n => { entry.width = n; stockChanged(g); }, 1);
      width.disabled = g.kind === 'timber';
      numberField(row, entry.offcut ? 'Pieces available' : 'Available (0 = unlimited)', entry.copies,
        n => { entry.copies = n; stockChanged(g); }, entry.offcut ? 1 : 0, 1000, true);
      if (opts.stock.length > 1) {
        const remove = el('button', 'Remove'); remove.type = 'button';
        remove.onclick = () => { opts.stock.splice(index, 1); stockChanged(g); }; row.append(remove);
      }
      stock.append(row);
    }
    const add = el('button', 'Add offcut'); add.type = 'button'; add.onclick = () => {
      opts.stock.push({ name: `Offcut ${opts.stock.filter(s => s.offcut).length + 1}`, length: 600,
        width: g.kind === 'timber' ? g.stock[0].width : 400, copies: 1, offcut: true }); stockChanged(g);
    }; stock.append(add); return stock;
  }
  function partTable(g: Group) {
    const table = el('table'); table.className = 'cut-parts';
    const head = el('thead'), row = el('tr');
    for (const title of ['Piece', 'Length × width (mm)', 'Thickness', 'Grain direction']) {
      const th = el('th', title); th.scope = 'col'; row.append(th);
    }
    head.append(row); table.append(head); const body = el('tbody'); table.append(body);
    for (const part of g.parts) {
      const tr = el('tr'); tr.dataset.part = part.path;
      const td = el('td'), name = el('button', fullName(part)); name.type = 'button'; name.dataset.part = part.path; name.onclick = () => selectPart(part.path);
      td.append(name); tr.append(td, el('td', `${mm(part.length)} × ${mm(part.width)}`), el('td', `${mm(part.thickness)} mm`));
      const orientation = el('td'), select = el('select'); select.setAttribute('aria-label', `Grain direction for ${fullName(part)}`);
      select.append(option('', 'Use global setting'), option('length', 'Along length'), option('width', 'Along width'), option('free', 'Either direction'));
      select.value = groupOptions(g).orientations[part.path] ?? ''; select.disabled = g.kind === 'timber';
      select.onchange = () => {
        if (select.value) groupOptions(g).orientations[part.path] = select.value as Grain;
        else delete groupOptions(g).orientations[part.path]; stockChanged(g);
      }; orientation.append(select); tr.append(orientation); body.append(tr);
    }
    return table;
  }

  function renderLayouts(g: Group) {
    const root = layoutHosts.get(g.key); if (!root) return;
    root.replaceChildren();
    const key = resultKey(g), result = data!.state.results[key];
    const running = starting.has(key) || data!.jobs[key]?.state === 'running';
    const status = el('div'); status.className = 'cut-layout-status';
    const regenerate = el('button', running ? 'Stop optimisation' : 'Arrange sheets'); regenerate.type = 'button';
    if (g.kind === 'timber' && !running) regenerate.textContent = 'Arrange timber lengths';
    regenerate.onclick = () => {
      if (running) void stop(g);
      else void generate(g);
    };
    regenerate.disabled = !data!.current || (!g.stock_sourced && !groupOptions(g).confirmed);
    const countProven = result && (result.stock_count_optimal ?? result.optimal) && !result.unplaced.length;
    const state = !result ? running ? 'Finding a layout…' : 'Sheet layout not calculated yet'
      : !isCurrent(g, result) ? 'Previous layout · cutting settings or design changed'
      : running ? result.optimises_offcuts && countProven ? 'Minimum sheet count proven · improving offcuts…'
        : 'Improving this layout…'
      : countProven ? result.optimises_offcuts ? 'Minimum sheet count proven · best offcut found'
        : 'Minimum stock count proven' : 'Best layout found';
    status.append(el('span', state), regenerate); root.append(status);
    if (!g.stock_sourced && !groupOptions(g).confirmed) root.append(el('p', 'Choose the available stock sizes below to calculate a layout.'));
    if (errors.has(key)) { const error = el('p', errors.get(key)!); error.className = 'cut-warning'; root.append(error); }
    if (data!.jobs[key]?.error) {
      const error = el('p', data!.jobs[key].error!); error.className = 'cut-warning'; root.append(error);
    }
    if (!result) return;
    if (result.best_offcut) {
      const offcut = result.best_offcut;
      root.append(el('p', `Best rectangular offcut: ${mm(offcut.length)} × ${mm(offcut.width)} mm · sheet ${offcut.sheet + 1}`));
    }
    if (result.unplaced.length) {
      const unplaced = result.parts.filter(p => result.unplaced.includes(p.id));
      const warning = el('p', `${unplaced.length} pieces still need placing: ${unplaced.map(fullName).join(', ')}`);
      warning.className = 'cut-warning'; root.append(warning);
    }
    const sheets = el('div'); sheets.className = 'cut-sheets';
    result.sheets.forEach((sheet, index) => {
      const card = el('section'); card.className = 'cut-sheet';
      const heading = el('div'); heading.className = 'cut-sheet-heading';
      heading.append(el('h4', `${materialName(g)} · ${g.kind === 'timber' ? 'Length' : 'Sheet'} ${index + 1} of ${result.sheets.length}`));
      heading.append(el('span', `${mm(sheet.stock.length)} × ${mm(sheet.stock.width)} mm${sheet.stock.offcut ? ' · owned offcut' : ''}`));
      card.append(heading);
      const svg = sheetDrawing(sheet, g, result, index, selectPart); card.append(svg);
      card.append(el('p', `${mm(result.options.kerf)} mm ${g.kind === 'timber' ? 'crosscut kerf' : 'tool width'}${result.profile_allowance ? ` + ${mm(result.profile_allowance)} mm curve allowance` : ''} · ${result.options.trim ? `${mm(result.options.trim)} mm ${g.kind === 'timber' ? 'end' : 'edge'} trim (hatched)` : 'untrimmed edges'}`));
      const keyList = el('ul'); keyList.className = 'cut-sheet-key';
      for (const placed of sheet.parts) {
        const part = result.parts.find(p => p.path === placed.path)!;
        const li = el('li'), button = el('button', fullName(part)); button.type = 'button'; button.dataset.part = part.path;
        button.style.setProperty('--part-colour', partColour(part)); button.onclick = () => selectPart(part.path);
        li.append(button, el('span', `${mm(part.length)} × ${mm(part.width)}`)); keyList.append(li);
      }
      card.append(keyList);
      const actions = el('div'); actions.className = 'cut-sheet-actions';
      const exportSvg = el('button', 'Save drawing'); exportSvg.type = 'button'; exportSvg.onclick = () => {
        const copy = svg.cloneNode(true) as SVGSVGElement;
        copy.setAttribute('width', `${svg.dataset.physicalWidth}mm`); copy.setAttribute('height', `${svg.dataset.physicalHeight}mm`);
        copy.querySelector('.cut-saw-lines')?.setAttribute('display', svg.classList.contains('show-cuts') ? 'inline' : 'none');
        download(`${materialName(g).replace(/[^\w-]+/g, '-')}-${index + 1}.svg`, new XMLSerializer().serializeToString(copy), 'image/svg+xml');
      }; actions.append(exportSvg); card.append(actions);
      if (sheet.cuts.length) {
        const sequence = details(`Saw-cut sequence · ${sheet.cuts.length} cuts`, `sequence:${g.key}:${index}`);
        sequence.className = 'cut-sequence';
        sequence.addEventListener('toggle', () => svg.classList.toggle('show-cuts', sequence.open));
        svg.classList.toggle('show-cuts', sequence.open);
        const list = el('ol');
        for (const [x1, y1, x2, y2] of sheet.cuts) list.append(el('li', x1 === x2
          ? `Crosscut at length ${mm(x1)} mm, across width coordinates ${mm(y1)}–${mm(y2)} mm.`
          : `Rip at width ${mm(y1)} mm, along length coordinates ${mm(x1)}–${mm(x2)} mm.`));
        sequence.append(el('p', 'Straight cuts separate rectangular blanks. Cut curves, openings and notches afterwards.'),
          el('p', 'Coordinates start at the top-left corner. Lines mark finished edges; keep the blade on the waste side.'), list); card.append(sequence);
      }
      sheets.append(card);
    });
    root.append(sheets);
    markSelected();
  }

  function startFocusedLayouts() {
    if (!data?.current || filter === 'all' || savingFailed) return;
    for (const g of filteredGroups()) {
      if (!g.stock_sourced && !groupOptions(g).confirmed) continue;
      const result = data.state.results[resultKey(g)], key = `${resultKey(g)}:${data.sources[g.key]}`;
      const needsSearch = !result || !isCurrent(g, result) || result.unplaced.length > 0
        || (!result.optimal && !data.jobs[resultKey(g)]);
      if (needsSearch && !attempted.has(key)) { attempted.add(key); void generate(g); }
    }
  }
  async function generate(g: Group) {
    const key = resultKey(g); if (starting.has(key) || data?.jobs[key]?.state === 'running' || !data?.current) return;
    starting.add(key); errors.delete(key); renderLayouts(g);
    try {
      await pending; if (savingFailed || !starting.has(key)) return;
      mergeProgress(await request<Data>('cutting/layout', 'POST', { group: g.key }));
    } catch (error) {
      errors.set(key, (error as Error).message);
    } finally { starting.delete(key); renderLayouts(g); }
  }
  function mergeProgress(fresh: Data) {
    if (!data) return;
    data.jobs = fresh.jobs; data.sources = fresh.sources; data.current = fresh.current;
    data.state.results = fresh.state.results;
  }
  async function stop(g: Group) {
    starting.delete(resultKey(g));
    try { mergeProgress(await request<Data>('cutting/stop', 'POST', { group: g.key })); renderLayouts(g); }
    catch (error) { message((error as Error).message); }
  }
  async function refreshProgress() {
    if (progressLoading || loading) return;
    progressLoading = true;
    try {
      await pending;
      const fresh = await request<Data>('cutting');
      const changed = filteredGroups().filter(g => {
        const key = resultKey(g);
        return data!.state.results[key]?.created !== fresh.state.results[key]?.created
          || JSON.stringify(data!.jobs[key]) !== JSON.stringify(fresh.jobs[key]);
      });
      mergeProgress(fresh);
      for (const g of changed) renderLayouts(g);
    } catch (error) { message((error as Error).message); }
    finally { progressLoading = false; }
  }
  function exportCsv() {
    const rows: (string | number)[][] = [['Assembly', 'Piece', 'Material', 'Length mm', 'Width mm', 'Thickness mm', 'CAD location']];
    for (const g of filteredGroups()) for (const p of g.parts) rows.push([assembly(p), fullName(p), materialName(g), p.length, p.width, p.thickness, p.path]);
    download('campervan-cut-list.csv', csv(rows), 'text/csv;charset=utf-8');
  }
  void refresh();
  onTab(tab => { if (tab === 'cuts') void refresh(); else { inspector.close(); pieceMenu.close(); } });
  return {
    hasPart(path: string) { return Boolean(data?.groups.some(g => g.parts.some(p => p.path === path))); },
    async showPart(path: string) {
      showTab('cuts'); await refresh();
      const group = data?.groups.find(g => g.parts.some(p => p.path === path)); if (!group) return;
      const returning = returnSpot?.path === path ? returnSpot : null;
      returnSpot = null;
      filter = returning?.filter ?? (isPlywood(group) ? `ply:${group.thickness}`
        : group.kind === 'timber' ? 'timber' : `sheet:${group.key}`);
      selectedPath = path; render(); markSelected();
      const matches = [...host.querySelectorAll<HTMLElement | SVGElement>('[data-part]')].filter(n => represents(n, path));
      const target = matches.find(n => n.closest('.cut-sheet')) ?? matches[0];
      if (returning) host.scrollTop = returning.scroll;
      else target?.scrollIntoView({ block: 'center' });
      target?.focus({ preventScroll: true });
      message(`${fullName(group.parts.find(p => p.path === path)!)}${target?.closest('.cut-sheet') ? '' : ' · sheet layout not available in this view'}`);
    },
    onStatus(status: ModelStatus) {
      if (modelSession !== status.session_id) { modelSession = status.session_id; attempted.clear(); }
      if (data && !host.hidden && Object.values(data.jobs).some(job => job.state === 'running')) void refreshProgress();
      const key = `${status.session_id}:${status.requested_revision}:${status.state}`;
      if (key === statusKey) return; statusKey = key;
      if (data) data.current = status.state === 'ready';
      if (!host.hidden || status.state === 'ready') void refresh();
    },
  };
}
