import { Extension, type Editor } from '@tiptap/core';
import { NodeSelection, TextSelection } from '@tiptap/pm/state';
import { emptyFilter, id } from './planning-api';
import { currentTask, newTask, moveTask, toggleReview, deleteTask } from './plan-task';

export type PlanCommand = 'text' | 'task' | 'heading' | 'table' | 'purchases';
export function addParagraph(editor: Editor): boolean {
  const { selection, schema } = editor.state;
  if (selection instanceof NodeSelection) {
    const at = selection.node.type.name === 'taskItem' ? selection.to - 1 : selection.to;
    const tr = editor.state.tr.insert(at, schema.nodes.paragraph.create());
    tr.setSelection(TextSelection.near(tr.doc.resolve(at + 1)));
    editor.view.dispatch(tr.scrollIntoView()); editor.view.focus(); return true;
  }
  return editor.chain().focus().splitBlock().setParagraph().run();
}

export function runPlanCommand(editor: Editor, command: PlanCommand): boolean {
  const selection = editor.state.selection;
  if ((command === 'table' || command === 'purchases') && selection instanceof NodeSelection
      && selection.node.type.name === 'taskItem') {
    editor.commands.setTextSelection(selection.from + (selection.node.firstChild?.nodeSize ?? 2));
  }
  switch (command) {
    case 'text': return addParagraph(editor);
    case 'task': return !editor.isActive('table') && newTask(editor);
    case 'heading': return editor.chain().focus().toggleHeading({ level: 2 }).run();
    case 'table': return editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true })
      .command(({ tr, state }) => {
        for (let depth = tr.selection.$from.depth; depth > 0; depth--) {
          if (tr.selection.$from.node(depth).type.name !== 'table') continue;
          const end = tr.selection.$from.after(depth);
          if (tr.doc.resolve(end).nodeAfter?.type.name !== 'paragraph') tr.insert(end, state.schema.nodes.paragraph.create());
          break;
        }
        return true;
      }).run();
    case 'purchases': return editor.chain().focus().insertContent([
      { type: 'purchaseView', attrs: { id: id(), filter: emptyFilter() } }, { type: 'paragraph' },
    ]).run();
  }
}


export type PlanAction = {
  id: string; label: string | ((editor: Editor) => string); group: string;
  shortcut?: string; alias?: string; bind?: boolean; context?: boolean; danger?: boolean;
  when?: (editor: Editor) => boolean; enabled?: (editor: Editor) => boolean;
  checked?: (editor: Editor) => boolean; run: (editor: Editor) => unknown;
};
export const isMac = () => /Mac|iPhone|iPad/.test(navigator.platform);
export function shortcutLabel(shortcut?: string): string {
  if (!shortcut) return '';
  const symbols: Record<string, string> = { Mod: isMac() ? '⌘' : 'Ctrl', Alt: isMac() ? '⌥' : 'Alt',
    Shift: isMac() ? '⇧' : 'Shift', Enter: '↵', ArrowUp: '↑', ArrowDown: '↓', Tab: 'Tab', F10: 'F10' };
  return shortcut.split('-').map(key => symbols[key] ?? key.toUpperCase()).join(isMac() ? '' : '+');
}
export function ariaShortcut(shortcut?: string) {
  return shortcut?.split('-').map(key => key === 'Mod' ? isMac() ? 'Meta' : 'Control' : key).join('+');
}
export const actionLabel = (action: PlanAction, editor: Editor) => typeof action.label === 'function' ? action.label(editor) : action.label;
const taskContext = (editor: Editor) => Boolean(currentTask(editor)) && !editor.isActive('table');
const tableContext = (editor: Editor) => editor.isActive('table');
function taskFlag(editor: Editor, key: 'checked' | 'collapsed') {
  const task = currentTask(editor); if (!task) return;
  const tr = editor.state.tr;
  const value = !task.node.attrs[key];
  if (key === 'collapsed') {
    if (value && tr.selection.from > task.pos) tr.setSelection(TextSelection.near(tr.doc.resolve(task.pos + 2)));
    tr.setMeta('addToHistory', false);
  }
  tr.setNodeAttribute(task.pos, key, value); editor.view.dispatch(tr); editor.view.focus();
}
function canMove(editor: Editor, direction: number) {
  const task = currentTask(editor); if (!task) return false;
  const pos = editor.state.doc.resolve(task.pos); const at = pos.index() + direction;
  return at >= 0 && at < pos.parent.childCount;
}
export function editLink(editor: Editor) {
  const href = prompt('Link URL', String(editor.getAttributes('link').href ?? ''));
  if (href === null) return;
  if (!href) editor.chain().focus().unsetLink().run();
  else if (/^(https?:\/\/|mailto:|tel:)/i.test(href)) editor.chain().focus().extendMarkRange('link').setLink({ href }).run();
  else alert('Use an https://, http://, mailto: or tel: link.');
}
function copyOrCut(editor: Editor, command: 'copy' | 'cut') {
  // Use the browser's clipboard event so ProseMirror's rich copy/cut and ID handling remain intact.
  editor.view.focus();
  if (!document.execCommand(command)) alert(`Use ${shortcutLabel('Mod-' + (command === 'copy' ? 'c' : 'x'))} to ${command} the selection.`);
}
async function paste(editor: Editor) {
  let bookmark = editor.state.selection.getBookmark();
  const map = ({ transaction }: { transaction: import('@tiptap/pm/state').Transaction }) => { bookmark = bookmark.map(transaction.mapping); };
  editor.on('transaction', map);
  try {
    const items = await navigator.clipboard.read();
    const item = items.find(item => item.types.includes('text/html') || item.types.includes('text/plain'));
    if (!item) throw new Error('The clipboard has no supported text or table.');
    const html = item.types.includes('text/html');
    const text = await (await item.getType(html ? 'text/html' : 'text/plain')).text();
    if (editor.isDestroyed) return;
    editor.view.dispatch(editor.state.tr.setSelection(bookmark.resolve(editor.state.doc)));
    editor.view.focus();
    const transfer = new DataTransfer(); transfer.setData(html ? 'text/html' : 'text/plain', text);
    editor.view.dom.dispatchEvent(new ClipboardEvent('paste', { clipboardData: transfer, bubbles: true, cancelable: true }));
  } catch (error) {
    if (!editor.isDestroyed) alert(`${error instanceof Error ? error.message : 'Clipboard access failed.'} Use ${shortcutLabel('Mod-v')} to paste.`);
  } finally { editor.off('transaction', map); }
}
export const planActions: PlanAction[] = [
  { id: 'newItem', label: 'New item', group: 'Item', shortcut: 'Mod-Shift-Enter', alias: '/task', context: true,
    when: e => !e.isActive('table'),
    run: e => newTask(e) },
  { id: 'newSubitem', label: 'Add subitem', group: 'Item', when: taskContext, context: true,
    run: e => newTask(e, 'child') },
  { id: 'newSibling', label: 'Add item at same level', group: 'Item', when: taskContext, context: true,
    run: e => newTask(e, 'sibling') },
  { id: 'complete', label: e => currentTask(e)?.node.attrs.checked ? 'Reopen item' : 'Complete item', group: 'Item',
    shortcut: 'Mod-Enter', when: taskContext, context: true, run: e => taskFlag(e, 'checked') },
  { id: 'collapse', label: e => currentTask(e)?.node.attrs.collapsed ? 'Expand item' : 'Collapse item', group: 'Item',
    when: taskContext, enabled: e => (currentTask(e)?.node.childCount ?? 0) > 1, context: true, run: e => taskFlag(e, 'collapsed') },
  { id: 'indent', label: 'Indent', group: 'Item', shortcut: 'Tab', bind: false, when: taskContext,
    enabled: e => e.can().sinkListItem('taskItem'), context: true, run: e => e.chain().focus().sinkListItem('taskItem').run() },
  { id: 'outdent', label: 'Outdent', group: 'Item', shortcut: 'Shift-Tab', bind: false, when: taskContext,
    enabled: e => e.can().liftListItem('taskItem'), context: true, run: e => e.chain().focus().liftListItem('taskItem').run() },
  { id: 'moveUp', label: 'Move up', group: 'Item', shortcut: 'Alt-ArrowUp', when: taskContext,
    enabled: e => canMove(e, -1), context: true, run: e => moveTask(e, -1) },
  { id: 'moveDown', label: 'Move down', group: 'Item', shortcut: 'Alt-ArrowDown', when: taskContext,
    enabled: e => canMove(e, 1), context: true, run: e => moveTask(e, 1) },
  { id: 'review', label: 'Needs review', group: 'Item', when: taskContext, checked: e => Boolean(currentTask(e)?.node.attrs.needs_review),
    context: true, run: e => toggleReview(e) },
  { id: 'bold', label: 'Bold', group: 'Text', shortcut: 'Mod-b', context: true, checked: e => e.isActive('bold'), run: e => e.chain().focus().toggleBold().run() },
  { id: 'italic', label: 'Italic', group: 'Text', shortcut: 'Mod-i', context: true, checked: e => e.isActive('italic'), run: e => e.chain().focus().toggleItalic().run() },
  { id: 'underline', label: 'Underline', group: 'Text', shortcut: 'Mod-u', context: true, checked: e => e.isActive('underline'), run: e => e.chain().focus().toggleUnderline().run() },
  { id: 'strike', label: 'Strikethrough', group: 'Text', shortcut: 'Mod-Shift-s', checked: e => e.isActive('strike'), run: e => e.chain().focus().toggleStrike().run() },
  { id: 'code', label: 'Inline code', group: 'Text', shortcut: 'Mod-e', checked: e => e.isActive('code'), run: e => e.chain().focus().toggleCode().run() },
  { id: 'link', label: 'Edit link…', group: 'Text', shortcut: 'Mod-k', context: true, run: editLink },
  { id: 'paragraph', label: 'Normal text', group: 'Style', shortcut: 'Mod-Alt-0',
    enabled: e => e.can().setParagraph(), run: e => e.chain().focus().setParagraph().run() },
  ...([1, 2, 3, 4, 5, 6] as const).map(level => ({ id: 'heading' + level, label: 'Heading ' + level, group: 'Style',
    shortcut: 'Mod-Alt-' + level, enabled: (e: Editor) => e.can().setHeading({ level }),
    run: (e: Editor) => e.chain().focus().setHeading({ level }).run() })),
  { id: 'text', label: 'New paragraph', group: 'Writing', shortcut: 'Alt-Enter', alias: '/text', run: addParagraph },
  { id: 'table', label: 'Insert table', group: 'Insert', alias: '/table', context: true, run: e => runPlanCommand(e, 'table') },
  { id: 'purchases', label: 'Insert purchases', group: 'Insert', alias: '/purchases', context: true, run: e => runPlanCommand(e, 'purchases') },
  { id: 'rowBefore', label: 'Insert row above', group: 'Table', when: tableContext, context: true, run: e => e.chain().focus().addRowBefore().run() },
  { id: 'rowAfter', label: 'Insert row below', group: 'Table', when: tableContext, context: true, run: e => e.chain().focus().addRowAfter().run() },
  { id: 'columnBefore', label: 'Insert column left', group: 'Table', when: tableContext, context: true, run: e => e.chain().focus().addColumnBefore().run() },
  { id: 'columnAfter', label: 'Insert column right', group: 'Table', when: tableContext, context: true, run: e => e.chain().focus().addColumnAfter().run() },
  { id: 'nextCell', label: 'Next cell', group: 'Table', when: tableContext, shortcut: 'Tab', bind: false,
    run: e => e.commands.goToNextCell() || e.chain().focus().addRowAfter().goToNextCell().run() },
  { id: 'previousCell', label: 'Previous cell', group: 'Table', when: tableContext, shortcut: 'Shift-Tab', bind: false, run: e => e.chain().focus().goToPreviousCell().run() },
  { id: 'deleteRow', label: 'Delete row', group: 'Table', when: tableContext, context: true, danger: true, run: e => e.chain().focus().deleteRow().run() },
  { id: 'deleteColumn', label: 'Delete column', group: 'Table', when: tableContext, context: true, danger: true, run: e => e.chain().focus().deleteColumn().run() },
  { id: 'deleteTable', label: 'Delete table', group: 'Table', when: tableContext, context: true, danger: true, run: e => e.chain().focus().deleteTable().run() },
  { id: 'removePurchases', label: 'Remove purchases view', group: 'Purchases', when: e => e.isActive('purchaseView'), context: true, danger: true,
    run: e => e.chain().focus().deleteSelection().run() },
  { id: 'cut', label: 'Cut', group: 'Clipboard', shortcut: 'Mod-x', bind: false, context: true,
    enabled: e => !e.state.selection.empty, run: e => copyOrCut(e, 'cut') },
  { id: 'copy', label: 'Copy', group: 'Clipboard', shortcut: 'Mod-c', bind: false, context: true,
    enabled: e => !e.state.selection.empty, run: e => copyOrCut(e, 'copy') },
  { id: 'paste', label: 'Paste', group: 'Clipboard', shortcut: 'Mod-v', bind: false, context: true, run: paste },
  { id: 'undo', label: 'Undo', group: 'History', shortcut: 'Mod-z', enabled: e => e.can().undo(), context: true, run: e => e.chain().focus().undo().run() },
  { id: 'redo', label: 'Redo', group: 'History', shortcut: 'Mod-Shift-z', enabled: e => e.can().redo(), context: true, run: e => e.chain().focus().redo().run() },
  { id: 'deleteItem', label: 'Delete item and contents…', group: 'Delete', when: taskContext, context: true, danger: true, run: e => deleteTask(e) },
];
export const getAction = (id: string) => planActions.find(action => action.id === id)!;
export function runAction(editor: Editor, action: PlanAction) {
  if (!editor.isEditable || action.when && !action.when(editor) || action.enabled && !action.enabled(editor)) return false;
  const result = action.run(editor);
  if (document.activeElement === document.body) editor.view.focus();
  return result !== false;
}
export const PlanActionKeys = Extension.create({
  name: 'planActionKeys', priority: 200,
  addKeyboardShortcuts() {
    return Object.fromEntries(planActions.filter(action => action.shortcut && action.bind !== false)
      .map(action => [action.shortcut!, () => runAction(this.editor, action)]));
  },
});
