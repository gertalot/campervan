import { request } from './api';
import type { Backup, PlanningClient } from './planning-api';
import { createPlanEditor } from './plan-editor';
import { action, el } from './purchase-grid';
import { onTab } from './tabs';
import { createPlanDropdown, type PlanMenuItem } from './plan-dropdown';
import { isStaticSite } from './site-runtime';

function download(name: string, body: string, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([body], { type }));
  const link = el('a'); link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function setupPlanner(root: HTMLElement, client: PlanningClient) {
  const heading = el('div'); heading.className = 'plan-heading'; heading.append(el('h2', 'Conversion plan'));
  const tools = el('div'); tools.className = 'plan-page-tools';
  const feedback = el('div'); feedback.className = 'planner-feedback'; feedback.setAttribute('role', 'status');
  const surface = el('div'); surface.className = 'plan-document-host';
  root.append(heading, tools, feedback, surface);
  let documentEditor: ReturnType<typeof createPlanEditor> | null = null;
  let query = ''; let hideCompleted = false;
  const report = (error: unknown) => alert(error instanceof Error ? error.message : String(error));
  const search = el('input'); search.type = 'search'; search.placeholder = 'Find in plan…'; search.setAttribute('aria-label', 'Find in plan');
  search.oninput = () => { query = search.value; documentEditor?.setView(query, hideCompleted); };
  search.onkeydown = event => { if (event.key === 'Enter') { event.preventDefault(); documentEditor?.find(event.shiftKey ? -1 : 1); } };
  const hideLabel = el('label', 'Hide completed'); const hide = el('input'); hide.type = 'checkbox'; hideLabel.prepend(hide);
  hide.onchange = () => { hideCompleted = hide.checked; documentEditor?.setView(query, hideCompleted); };
  const fileMenu = createPlanDropdown();
  const fileButton = action('File ▾', () => openFiles());
  fileButton.className = 'plan-file-trigger'; fileButton.setAttribute('aria-label', 'File');
  fileButton.setAttribute('aria-haspopup', 'menu'); fileButton.setAttribute('aria-expanded', 'false');
  fileButton.onkeydown = event => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault(); openFiles(event.key === 'ArrowUp' ? 'last' : 'first');
    }
  };
  const file = el('input'); file.type = 'file'; file.accept = '.json,application/json'; file.hidden = true;
  const exportFile = async (format: 'json' | 'markdown' | 'csv') => {
    try {
      await client.flush();
      const response = await fetch(`/api/v1/planning/export?format=${format}`);
      if (!response.ok) throw new Error(await response.text());
      download(`conversion-plan.${format === 'markdown' ? 'md' : format}`, await response.text(), response.headers.get('Content-Type') ?? 'text/plain');
    } catch (error) { report(error); }
  };
  file.onchange = async () => {
    const selected = file.files?.[0]; if (!selected) return;
    try {
      const backup = JSON.parse(await selected.text()) as Backup;
      if (confirm('Replace the plan, purchases and CAD settings with this backup? Save a backup first if needed.')) {
        await client.restore(backup); location.reload();
      }
    } catch (error) { report(error); }
    file.value = '';
  };
  const fileItems: PlanMenuItem[] = [
    { label: 'Reload saved plan', group: 'Reload', run: () => {
      if (!client.dirty || confirm('Discard unsaved edits and reload? Download unsaved edits first to keep a copy.')) void client.read();
    } },
    { label: 'Download full backup (.json)', group: 'Export', run: () => { void exportFile('json'); } },
    { label: 'Export notes (.md)', group: 'Export', run: () => { void exportFile('markdown'); } },
    { label: 'Export purchases (.csv)', group: 'Export', run: () => { void exportFile('csv'); } },
    { label: 'Import backup…', group: 'Restore', run: () => file.click() },
    { label: 'Restore previous save…', group: 'Restore', run: () => { void (async () => {
      try {
        if (!client.blocked) await client.flush();
        const previous = await request<Backup>('planning/previous');
        if (confirm('Restore the previous planning save? Current CAD settings are retained.')) {
          await client.restore(previous); location.reload();
        }
      } catch (error) { report(error); }
    })(); } },
  ];
  function openFiles(initial: 'first' | 'last' = 'first') {
    fileMenu.open({ label: 'File', items: fileItems, trigger: fileButton, initial, className: 'plan-file-dropdown' });
  }
  tools.append(search, action('Previous match', () => { documentEditor?.find(-1); }),
    action('Next match', () => { documentEditor?.find(1); }), hideLabel);
  if (!isStaticSite) tools.append(fileButton, file);

  function status() {
    feedback.replaceChildren(el('span', client.status));
    if (client.error) {
      feedback.append(el('p', client.error));
      if (!isStaticSite) feedback.append(action('Download unsaved edits', () => {
        download('unsaved-planning-edits.json', JSON.stringify(client.document, null, 2));
      }));
    }
    const editable = !isStaticSite && !client.blocked;
    if (documentEditor && documentEditor.editor.isEditable !== editable) documentEditor.editor.setEditable(editable, false);
  }
  function load() {
    documentEditor?.destroy(); documentEditor = null; surface.replaceChildren();
    if (!client.document) { surface.append(el('p', 'Loading the plan…')); return; }
    try {
      documentEditor = createPlanEditor(surface, {
        content: client.document.content, client, fileButton: isStaticSite ? undefined : fileButton,
        onChange(content) { try { client.setContent(content); } catch (error) { report(error); } },
      });
      documentEditor.setView(query, hideCompleted);
    } catch (error) {
      surface.replaceChildren(el('p', `Cannot open the saved document: ${String(error)}.`
        + (isStaticSite ? '' : ' Use File to reload or import a backup.')));
      if (!isStaticSite) tools.append(fileButton);
    }
  }
  const unsubscribe = client.subscribe(change => { if (change.loaded) load(); status(); });
  const unsubscribeTab = onTab(tab => { if (tab !== 'plan') void client.flush().catch(() => {}); });
  load(); status();
  return { destroy() { fileMenu.destroy(); unsubscribe(); unsubscribeTab(); documentEditor?.destroy(); } };
}
