/** Project result management; source captures and measured constraints remain independent. */
import { ApiError } from './api';
import { createScanImport } from './scan-import';
import { createSidePanel } from './side-panel';
import { readScanLibrary, saveScanLibrary, deleteScanResult, deleteCaptureGroup, moveScanItem,
  type ScanLibraryDocument, type ScanResult } from './scan-library-api';

interface Host {
  results(): ScanResult[];
  currentKey(): string;
  view(key: string): void;
  changed(): Promise<void>;
  interactionGeneration(): number;
  importCompleted(key: string, autoOpen: boolean): void;
}
function element<K extends keyof HTMLElementTagNameMap>(tag: K, text?: string) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}
function button(text: string, run: () => void) {
  const node = element('button', text); node.type = 'button'; node.onclick = run; return node;
}
function iconButton(icon: 'pencil' | 'trash', label: string, run: () => void) {
  const node = button('', run); node.className = `scan-result-icon scan-result-${icon}`;
  node.title = label; node.setAttribute('aria-label', label);
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS(svg.namespaceURI, 'path');
  path.setAttribute('d', icon === 'pencil'
    ? 'm15 4 5 5M4 20l5-1L21 7a2 2 0 0 0-5-5L4 14Z'
    : 'M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7');
  svg.append(path); node.append(svg); return node;
}

export function createScanLibrary(host: Host) {
  const side = createSidePanel({ id: 'scan-library', title: 'Manage scans', mode: 'modal',
    onClose: () => { editor.hidden = true; } });
  const dialog = side.element; dialog.classList.add('scan-library-dialog');
  const close = side.closeButton;
  const description = element('p', 'Groups contain imported databases and processed results. Drag an item onto another group to move it. Corrections stay with their source result.');
  const filters = element('div'); filters.className = 'scan-library-filters';
  const searchLabel = element('label', 'Search '); const search = element('input'); search.type = 'search';
  search.placeholder = 'Name, group or identifier'; searchLabel.append(search);
  const filterLabel = element('label', 'Show '); const filter = element('select');
  for (const value of ['Active', 'Archived', 'All']) filter.add(new Option(value, value)); filterLabel.append(filter);
  const newGroup = button('Create capture group…', () => editGroup()); filters.append(searchLabel, filterLabel, newGroup);
  const alert = element('p'); alert.setAttribute('role', 'alert');
  const editor = element('div'); editor.className = 'scan-library-editor'; editor.hidden = true;
  const list = element('div'); list.className = 'scan-library-list';
  side.context.append(description); side.actions.append(filters); side.status.append(alert); side.body.append(editor, list);
  const confirmation = element('dialog'); confirmation.className = 'scan-delete-dialog';
  confirmation.setAttribute('aria-labelledby', 'scan-delete-title');
  confirmation.setAttribute('aria-describedby', 'scan-delete-description'); document.body.append(confirmation);
  let library: ScanLibraryDocument | undefined;
  let busy = false;
  let focusAfterRender: string | undefined;
  const importer = createScanImport({
    defaultLayout: group => library?.group_layouts?.[group],
    async changed() { await host.changed(); library = await readScanLibrary(); if (!busy) render(); },
    view(key) { side.close(); host.view(key); },
    interactionGeneration: host.interactionGeneration,
    completed(key, autoOpen) { if (autoOpen) side.close({ restoreFocus: false }); host.importCompleted(key, autoOpen); },
    closed(group) {
      if (!dialog.open) return;
      const trigger = [...list.querySelectorAll<HTMLButtonElement>('[data-import-group]')]
        .find(button => button.dataset.importGroup === group);
      (trigger ?? newGroup).focus();
    },
  });

  function message(error: unknown) { alert.textContent = error instanceof Error ? error.message : String(error); }
  function preference(candidate: ScanLibraryDocument, key: string) {
    return candidate.entries[key] ??= { display_name: null, group_id: null, archived: false };
  }
  function pending(value: boolean) {
    busy = value; dialog.setAttribute('aria-busy', String(value));
    for (const control of dialog.querySelectorAll<HTMLButtonElement | HTMLInputElement | HTMLSelectElement>('button,input,select')) {
      if (control === close) continue;
      if (value) { control.dataset.wasDisabled = String(control.disabled); control.disabled = true; }
      else { control.disabled = control.dataset.wasDisabled === 'true'; delete control.dataset.wasDisabled; }
    }
  }
  async function commit(change: (candidate: ScanLibraryDocument) => void) {
    if (!library || busy) return;
    const candidate = structuredClone(library);
    change(candidate); alert.textContent = ''; pending(true);
    try {
      library = await saveScanLibrary(candidate);
      await host.changed(); editor.hidden = true; editor.replaceChildren();
      pending(false);
      const restoreRow = !!focusAfterRender; render();
      if (dialog.open && !restoreRow) newGroup.focus();
    } catch (error) {
      let refreshed = false;
      if (error instanceof ApiError && error.status === 409) {
        try { library = await readScanLibrary(); await host.changed(); refreshed = true; }
        catch (reloadError) { message(reloadError); pending(false); return; }
      }
      message(error); pending(false);
      if (refreshed) {
        focusAfterRender = undefined; render();
        if (!editor.hidden) editor.querySelector<HTMLElement>('input,select')?.focus();
      }
    }
  }
  function editName(label: string, current: string, save: (value: string) => void) {
    editor.replaceChildren(); editor.hidden = false;
    const form = element('form'); const field = element('label', `${label} `); const input = element('input');
    input.value = current; input.required = true; input.maxLength = 120; field.append(input);
    const submit = element('button', 'Save'); submit.type = 'submit';
    const cancel = button('Cancel', cancelEditing);
    form.append(field, submit, cancel);
    form.onsubmit = event => {
      event.preventDefault(); const value = input.value.trim();
      if (!value) { input.setCustomValidity('Enter a name.'); input.reportValidity(); return; }
      save(value);
    };
    input.oninput = () => input.setCustomValidity(''); editor.append(form); input.focus(); input.select();
  }
  function cancelEditing() {
    editor.hidden = true;
    const restoreRow = !!focusAfterRender; render();
    if (!restoreRow) newGroup.focus();
  }
  function editGroup(id?: string) {
    editName(id ? 'Capture group name' : 'New capture group', id ? library?.groups[id] ?? '' : '', value => {
      const key = id ?? crypto.randomUUID();
      void commit(candidate => { candidate.groups[key] = value; });
    });
  }
  async function transfer(kind: 'result' | 'capture', key: string, group: string | null) {
    if (!library || busy) return;
    pending(true); alert.textContent = '';
    try {
      library = await moveScanItem(kind, key, group, library.revision);
      await host.changed(); await importer.refresh();
      editor.hidden = true; editor.replaceChildren();
    } catch (error) {
      message(error);
      try { library = await readScanLibrary(); await host.changed(); await importer.refresh(); }
      catch (reloadError) { message(reloadError); }
    } finally { pending(false); render(); if (dialog.open) filter.focus(); }
  }
  function move(kind: 'result' | 'capture', key: string, name: string, current: string | null) {
    editor.replaceChildren(); editor.hidden = false;
    const form = element('form'); const label = element('label', `Move ${name} to `);
    const group = element('select');
    if (kind === 'result') group.add(new Option('Ungrouped', ''));
    for (const [id, name] of Object.entries(library?.groups ?? {}).sort((a, b) => a[1].localeCompare(b[1]))) {
      group.add(new Option(name, id));
    }
    group.value = current ?? ''; label.append(group);
    const save = element('button', 'Save'); save.type = 'submit';
    form.append(label, save, button('Cancel', cancelEditing));
    form.onsubmit = event => { event.preventDefault(); void transfer(kind, key, group.value || null); };
    editor.append(form); group.focus();
  }
  function confirmRemoval(row: ScanResult, available: boolean) {
    confirmDeletion({
      title: `Delete “${row.display_name}”?`,
      description: available
        ? row.id ? 'Permanently delete this generated result, including its meshes, textures, exported frames and working copies.'
          : 'Permanently delete this point-cloud preview file.'
        : 'Remove this unavailable result and its saved library preferences. Any remaining published result files will also be deleted.',
      location: row.id ? `.local/scans/${row.id}/` : row.name,
      retained: 'Original capture databases and saved tag measurements are kept. This cannot be undone.',
      action: 'Delete result', run: revision => deleteScanResult(row.key, revision),
      restore: () => [...list.querySelectorAll<HTMLElement>('article')].find(node => node.dataset.key === row.key)
        ?.querySelector<HTMLButtonElement>('.scan-result-trash') ?? filter,
    });
  }
  function confirmGroupRemoval(id: string, name: string) {
    confirmDeletion({
      title: `Delete capture group “${name}”?`,
      description: 'Permanently delete this group, its imported database copies, generated results and linked corrections, including meshes, textures and processing history.',
      retained: 'Reusable tag layouts and physical measurements are kept. Original files outside the app’s capture storage are kept. This cannot be undone.',
      action: 'Delete capture group', run: revision => deleteCaptureGroup(id, revision),
      restore: () => [...list.querySelectorAll<HTMLElement>('section')].find(node => node.dataset.groupId === id)
        ?.querySelector<HTMLButtonElement>('.scan-result-trash') ?? newGroup,
    });
  }
  function confirmDeletion(options: {
    title: string; description: string; location?: string; retained: string; action: string;
    run(revision: number): Promise<ScanLibraryDocument>; restore(): HTMLElement;
  }) {
    if (busy || !library) return;
    confirmation.replaceChildren();
    const heading = element('h2', options.title); heading.id = 'scan-delete-title';
    const explanation = element('p', options.description);
    explanation.id = 'scan-delete-description';
    const location = element('code', options.location); location.hidden = !options.location;
    const retained = element('p', options.retained);
    const error = element('p'); error.setAttribute('role', 'alert');
    const controls = element('div'); controls.className = 'scan-delete-actions';
    const cancel = button('Cancel', () => confirmation.close());
    const remove = button(options.action, () => { void performRemoval(); }); remove.className = 'scan-delete-confirm';
    controls.append(cancel, remove); confirmation.append(heading, explanation, location, retained, error, controls);
    confirmation.oncancel = event => { if (busy) event.preventDefault(); };
    confirmation.addEventListener('close', () => {
      if (!dialog.open) return;
      options.restore().focus();
    }, { once: true });
    confirmation.showModal(); cancel.focus();
    async function performRemoval() {
      if (busy || !library) return;
      const revision = library.revision;
      pending(true); remove.disabled = true; cancel.disabled = true; error.textContent = ''; remove.textContent = 'Deleting…';
      try {
        library = await options.run(revision);
        await host.changed(); await importer.refresh(); confirmation.close(); editor.hidden = true; editor.replaceChildren();
        pending(false); render(); if (dialog.open) filter.focus();
      } catch (reason) {
        // A filesystem operation can fail after removing some files; always reflect current discovery.
        try { library = await readScanLibrary(); await host.changed(); await importer.refresh(); }
        catch (reloadError) { message(reloadError); }
        pending(false); render();
        cancel.disabled = false;
        error.textContent = reason instanceof Error ? reason.message : String(reason);
        if (reason instanceof ApiError && reason.status === 409) {
          error.textContent += ' Cancel and review the refreshed results before trying again.';
        } else remove.disabled = false;
        remove.textContent = options.action;
      }
    }
  }
  function details(row: ScanResult, available: boolean) {
    const node = element('details');
    const summary = element('summary', 'Inspect result');
    summary.setAttribute('aria-label', `Inspect result: ${row.display_name}`); node.append(summary);
    const values: [string, string][] = [['Original identifier', row.id ?? row.name]];
    if (!available) values.push(['Availability', 'Unavailable — preferences retained; no current asset was discovered.']);
    else if (!row.id) values.push(['Format', 'Point cloud only'], ['Processing details', 'Unknown']);
    else {
      const source: Record<string, string> = { saved_camera_poses: 'Saved poses from input database',
        rtabmap_merge_g2o: 'RTAB-Map multi-session merge (g2o)', rtabmap_reprocess_g2o: 'RTAB-Map tag reprocessing (g2o)',
        external_camera_poses: 'External camera poses', gtsam_measured_distances: 'GTSAM fit using physical distances' };
      values.push(['Inputs', row.input_filenames?.join(', ') || 'Unknown'],
        ['Pose source', row.pose_source ? source[row.pose_source] ?? row.pose_source : 'Unknown'],
        ['Fusion resolution', typeof row.settings?.voxel_mm === 'number' ? `${row.settings.voxel_mm} mm` : 'Unknown'],
        ['Frames', row.frame_count?.toLocaleString() ?? 'Unknown'],
        ['Triangles', row.geometry?.triangles?.toLocaleString() ?? 'Unknown'],
        ['Layers', row.layers?.map(layer => layer.label).join(', ') || 'Unknown'],
        ['Created', row.created_at ? new Date(row.created_at).toLocaleString() : 'Unknown']);
    }
    const dl = element('dl');
    for (const [label, value] of values) dl.append(element('dt', label), element('dd', value));
    node.append(dl); return node;
  }
  function processingSummary(row: ScanResult, available: boolean) {
    if (!available) return 'Files unavailable — saved preferences retained';
    if (!row.id) return 'Point-cloud preview — no reconstructed surface';
    const methods: Record<string, string> = {
      saved_camera_poses: 'Reconstructed using poses saved in the database',
      rtabmap_merge_g2o: `Re-merged ${row.input_filenames?.length ?? 'multiple'} databases, then reconstructed`,
      rtabmap_reprocess_g2o: 'Detected tags and reconstructed from one database',
      external_camera_poses: 'Reconstructed using supplied camera poses',
      gtsam_measured_distances: 'Rebuilt using camera poses fitted to physical distances',
    };
    const parts = [methods[row.pose_source ?? ''] ?? 'Reconstructed surface — pose source unknown'];
    if (typeof row.settings?.voxel_mm === 'number') parts.push(`${row.settings.voxel_mm} mm fusion`);
    if (row.frame_count != null) parts.push(`${row.frame_count.toLocaleString()} frames`);
    return parts.join(' · ');
  }
  const dragType = 'application/x-campervan-scan-item';
  function draggable(node: HTMLElement, kind: 'result' | 'capture', key: string) {
    node.draggable = true;
    node.ondragstart = event => {
      if (busy || !event.dataTransfer) { event.preventDefault(); return; }
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData(dragType, JSON.stringify({ kind, key }));
    };
  }
  function dropTarget(section: HTMLElement, id: string, name: string) {
    section.ondragover = event => {
      if (busy || !event.dataTransfer) return;
      const internal = event.dataTransfer.types.includes(dragType);
      if (internal || (id && event.dataTransfer.types.includes('Files'))) {
        event.preventDefault(); event.dataTransfer.dropEffect = internal ? 'move' : 'copy';
        section.classList.add('scan-group-drop-target');
      }
    };
    section.ondragleave = event => {
      if (!(event.relatedTarget instanceof Node) || !section.contains(event.relatedTarget)) {
        section.classList.remove('scan-group-drop-target');
      }
    };
    section.ondrop = event => {
      section.classList.remove('scan-group-drop-target');
      if (busy) { event.preventDefault(); return; }
      const payload = event.dataTransfer?.getData(dragType);
      if (!payload) { if (id) importer.drop(event, id, name); return; }
      event.preventDefault();
      try {
        const item = JSON.parse(payload);
        if ((item.kind !== 'capture' && item.kind !== 'result') || typeof item.key !== 'string') {
          throw new Error('This item cannot be moved to a capture group.');
        }
        void transfer(item.kind, item.key, id || null);
      } catch (error) { message(error); }
    };
  }
  function render() {
    if (!library) return;
    list.replaceChildren();
    const discovered = new Map(host.results().map(row => [row.key, row]));
    const rows = [...discovered.values()];
    for (const [key, prefs] of Object.entries(library.entries)) {
      if (discovered.has(key)) continue;
      const name = key.slice(key.indexOf(':') + 1);
      rows.push({ key, name, id: key.startsWith('run:') ? name : undefined, bytes: 0,
        display_name: prefs.display_name ?? name, group_id: prefs.group_id,
        group_name: prefs.group_id ? library.groups[prefs.group_id] : null, archived: prefs.archived,
        is_default: library.default_key === key });
    }
    const needle = search.value.trim().toLocaleLowerCase();
    const filtered = rows.filter(row => (filter.value === 'All' || row.archived === (filter.value === 'Archived'))
      && `${row.display_name} ${row.name} ${row.id ?? ''} ${row.group_name ?? 'Ungrouped'}`.toLocaleLowerCase().includes(needle));
    // Keep empty groups manageable before databases/results are added.
    const groups = new Map<string, string>(Object.entries(library.groups)); groups.set('', 'Ungrouped');
    for (const [id, name] of [...groups].sort((a, b) => a[1].localeCompare(b[1]))) {
      const groupRows = filtered.filter(row => (row.group_id ?? '') === id).sort((a, b) => a.display_name.localeCompare(b.display_name) || a.key.localeCompare(b.key));
      const captures = importer.captures().filter(capture => capture.group_id === id
        && (!needle || `${name} ${capture.filename}`.toLocaleLowerCase().includes(needle)));
      if (!groupRows.length && !captures.length && (needle || filter.value === 'Archived' || !id)) continue;
      const section = element('section'); section.className = 'scan-library-section'; section.dataset.groupId = id;
      const heading = element('div'); heading.className = 'scan-library-group';
      const title = element('div'); title.className = 'scan-group-title';
      title.append(element('span', id ? 'Capture group' : 'Ungrouped results'), element('h3', name)); heading.append(title);
      if (id) {
        const groupActions = element('div'); groupActions.className = 'scan-result-tools';
        const add = button('Add capture databases…', () => { void importer.open(id, name); });
        add.dataset.importGroup = id;
        add.title = `Add .db files to ${name}, or drop files onto this capture group`;
        groupActions.append(add,
          iconButton('pencil', `Rename capture group: ${name}`, () => editGroup(id)),
          iconButton('trash', `Delete capture group: ${name}`, () => confirmGroupRemoval(id, name)));
        heading.append(groupActions);
      }
      dropTarget(section, id, name);
      section.append(heading);
      if (id) section.append(importer.activity(id, name));
      if (captures.length) {
        const databases = element('details'); databases.className = 'scan-group-captures';
        databases.append(element('summary', `Imported databases (${captures.length})`));
        for (const capture of captures) {
          const row = element('div'); row.className = 'scan-capture-row'; draggable(row, 'capture', capture.id);
          const label = element('span', `${capture.filename} · ${capture.frames} frames`);
          row.tabIndex = 0;
          row.title = 'Drag to another capture group. Press Enter to choose a group with the keyboard.';
          row.setAttribute('aria-label', `${capture.filename}, ${capture.frames} frames. Drag to another group, or press Enter to choose a group.`);
          row.setAttribute('aria-keyshortcuts', 'Enter');
          row.onkeydown = event => {
            if (event.key === 'Enter' && !busy) {
              event.preventDefault(); move('capture', capture.id, capture.filename, capture.group_id);
            }
          };
          row.append(label); databases.append(row);
        }
        section.append(databases);
      }
      for (const row of groupRows) {
        const available = discovered.has(row.key);
        const article = element('article'); article.dataset.key = row.key;
        draggable(article, 'result', row.key);
        const identity = element('div'); identity.className = 'scan-result-identity';
        const caption = element('h4', row.display_name);
        const state = [row.key === host.currentKey() ? 'In viewer' : '', row.is_default ? 'Opens at startup' : '',
          row.archived ? 'Archived' : ''].filter(Boolean).join(' · ');
        if (state) caption.append(element('span', state));
        identity.append(caption, element('p', processingSummary(row, available))); article.append(identity);
        const actions = element('div'); actions.className = 'scan-library-row-actions';
        const view = button('Show in viewer', () => { side.close(); host.view(row.key); });
        view.className = 'scan-result-view'; view.disabled = !available || row.archived;
        view.setAttribute('aria-label', `Show ${row.display_name} in viewer`);
        const rename = iconButton('pencil', `Rename result: ${row.display_name}`, () => {
          focusAfterRender = row.key; editName('Display name', row.display_name,
          value => { void commit(candidate => { preference(candidate, row.key).display_name = value; }); }); });
        const trash = iconButton('trash', `Delete result: ${row.display_name}`, () => confirmRemoval(row, available));
        const setDefault = button('Use at startup', () => { focusAfterRender = row.key;
          void commit(candidate => { preference(candidate, row.key); candidate.default_key = row.key; }); });
        setDefault.disabled = !available || row.archived || row.is_default;
        const archive = button(row.archived ? 'Restore to selector' : 'Archive result', () => { focusAfterRender = row.key;
          void commit(candidate => { preference(candidate, row.key).archived = !row.archived;
            if (!row.archived && candidate.default_key === row.key) candidate.default_key = null; }); });
        actions.append(button('Change capture group…', () => {
          focusAfterRender = row.key; move('result', row.key, row.display_name, row.group_id);
        }));
        if (!row.is_default) actions.append(setDefault);
        actions.append(archive);
        const inspect = details(row, available);
        const note = element('p', row.archived ? 'Restore makes this result available in the Result selector.'
          : 'Archive hides this result from the Result selector. All files and measurements are kept.');
        note.className = 'scan-result-action-help'; inspect.append(actions, note);
        const rowTools = element('div'); rowTools.className = 'scan-result-tools'; rowTools.append(view, rename, trash);
        article.append(rowTools, inspect); section.append(article);
      }
      list.append(section);
    }
    if (!filtered.length) list.prepend(element('p', 'No processed results match. Imported databases are listed within their capture groups.'));
    if (focusAfterRender && dialog.open) {
      const row = [...list.querySelectorAll<HTMLElement>('article')].find(node => node.dataset.key === focusAfterRender);
      (row?.querySelector<HTMLButtonElement>('button:not(:disabled)') ?? filter).focus(); focusAfterRender = undefined;
    }
  }
  search.oninput = render; filter.onchange = render;
  async function refresh() {
    library = await readScanLibrary(); await importer.refresh(); if (dialog.open) render();
  }
  return {
    async open() {
      alert.textContent = ''; list.replaceChildren(); editor.hidden = true; newGroup.disabled = false;
      side.open(); search.focus();
      pending(true);
      try { await refresh(); pending(false); render(); if (dialog.open) search.focus(); }
      catch (error) { pending(false); newGroup.disabled = true; message(error); if (dialog.open) close.focus(); }
    },
    refresh,
  };
}
