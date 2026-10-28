import type { Editor } from '@tiptap/core';
import { NodeSelection, TextSelection, type SelectionBookmark } from '@tiptap/pm/state';
import { actionLabel, ariaShortcut, planActions, runAction, shortcutLabel } from './plan-actions';
import { el } from './purchase-grid';
import { createPlanDropdown, type PlanMenuItem } from './plan-dropdown';

export type MenuRequest = { trigger?: HTMLElement; x?: number; y?: number; full?: boolean; initial?: 'first' | 'last' };
export function mountPlanMenu(editor: Editor) {
  const dropdown = createPlanDropdown();
  let bookmark: SelectionBookmark | null = null;
  const restoreSelection = () => {
    if (!bookmark || editor.isDestroyed) return;
    try { editor.view.dispatch(editor.state.tr.setSelection(bookmark.resolve(editor.state.doc))); } catch { /* Keep valid current selection. */ }
  };
  // A menu takes focus; map its saved document selection through any intervening transactions.
  const onTransaction = ({ transaction }: { transaction: import('@tiptap/pm/state').Transaction }) => {
    if (bookmark) bookmark = bookmark.map(transaction.mapping);
  };
  const showHelp = () => {
    const dialog = document.createElement('dialog'); dialog.className = 'plan-shortcut-help';
    const heading = el('h2', 'Editor shortcuts'); heading.id = 'plan-shortcut-heading'; dialog.setAttribute('aria-labelledby', heading.id);
    const intro = el('p', 'Actions menus show the shortcuts for your current selection. Enter continues writing; a new item is a separate action. Shift + right-click opens the browser menu.');
    const insertionHelp = el('p',
      'New item adds the first subitem of an expanded item with subitems. Otherwise it adds an item at the same level. '
      + 'Use Add subitem or Add item at same level to choose explicitly. '
      + 'Tab indents; Shift+Tab moves an item up one level.');
    const table = el('table');
    for (const [label, key] of [['New paragraph', 'Enter'], ['Line break', 'Shift-Enter'],
      ['Open actions menu', 'Shift-F10'], ...planActions.filter(a => a.shortcut).map(a => [actionLabel(a, editor), a.shortcut!] as [string, string])]) {
      const row = el('tr'); row.append(el('td', label), el('td', shortcutLabel(key))); table.append(row);
    }
    const done = el('button', 'Close'); done.type = 'button'; done.onclick = () => dialog.close();
    dialog.append(heading, intro, insertionHelp, table, done); dialog.onclose = () => { dialog.remove(); editor.view.focus(); };
    document.body.append(dialog); dialog.showModal();
  };
  const open = (request: MenuRequest = {}) => {
    if (dropdown.isOpen(request.trigger)) { dropdown.close(true); return; }
    dropdown.close(); bookmark = editor.state.selection.getBookmark();
    const items: PlanMenuItem[] = planActions
      .filter(entry => (!entry.when || entry.when(editor)) && (request.full || entry.context))
      .map(entry => ({
        label: actionLabel(entry, editor), group: entry.group,
        shortcut: entry.shortcut ? shortcutLabel(entry.shortcut) : entry.alias,
        ariaShortcut: ariaShortcut(entry.shortcut),
        enabled: editor.isEditable && (!entry.enabled || entry.enabled(editor)),
        checked: entry.checked?.(editor), danger: entry.danger,
        run: () => { runAction(editor, entry); if (document.activeElement === request.trigger) editor.view.focus(); },
      }));
    items.push({ label: 'Keyboard shortcuts', group: 'Help', run: showHelp });
    const rect = editor.view.coordsAtPos(editor.state.selection.from);
    dropdown.open({
      label: 'Actions for current selection', items, trigger: request.trigger, initial: request.initial,
      x: request.x ?? (request.trigger ? undefined : rect.left),
      y: request.y ?? (request.trigger ? undefined : rect.bottom + 5),
      onClose: () => { restoreSelection(); bookmark = null; },
      returnFocus: () => { if (request.trigger?.isConnected) request.trigger.focus({ preventScroll: true }); else editor.view.focus(); },
    });
  };
  const pointSelection = (event: MouseEvent) => {
    const hit = editor.view.posAtCoords({ left: event.clientX, top: event.clientY }); if (!hit) return;
    const { selection, doc } = editor.state;
    if (hit.pos >= selection.from && hit.pos <= selection.to && !selection.empty) return;
    const inside = hit.inside >= 0 ? doc.nodeAt(hit.inside) : null;
    const next = inside?.type.name === 'purchaseView' ? NodeSelection.create(doc, hit.inside)
      : TextSelection.near(doc.resolve(hit.pos));
    editor.view.dispatch(editor.state.tr.setSelection(next));
  };
  const contextmenu = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    if (event.shiftKey) return;
    if (target.closest('input,textarea,select,button') && !target.closest('.task-drag')) return;
    event.preventDefault(); pointSelection(event); open({ x: event.clientX, y: event.clientY });
  };
  const keyboard = (event: KeyboardEvent) => {
    if (event.key !== 'ContextMenu' && !(event.shiftKey && event.key === 'F10')) return;
    if ((event.target as HTMLElement).closest('input,textarea,select')) return;
    event.preventDefault(); event.stopPropagation();
    const handle = (event.target as HTMLElement).closest<HTMLButtonElement>('.task-drag');
    if (handle) handle.click(); else open();
  };
  const handleRequest = (event: Event) => { open((event as CustomEvent<MenuRequest>).detail); };
  editor.view.dom.addEventListener('contextmenu', contextmenu);
  editor.view.dom.addEventListener('keydown', keyboard, true);
  editor.view.dom.addEventListener('plan-actions', handleRequest);
  editor.on('transaction', onTransaction);
  return {
    open,
    destroy() {
      dropdown.destroy(); editor.off('transaction', onTransaction);
      editor.view.dom.removeEventListener('contextmenu', contextmenu);
      editor.view.dom.removeEventListener('keydown', keyboard, true);
      editor.view.dom.removeEventListener('plan-actions', handleRequest);
    },
  };
}
