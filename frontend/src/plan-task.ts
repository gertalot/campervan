import { TaskItem } from '@tiptap/extension-list';
import type { Editor } from '@tiptap/core';
import { NodeSelection, TextSelection } from '@tiptap/pm/state';
import type { Node as PMNode } from '@tiptap/pm/model';
import { isStaticSite } from './site-runtime';

export function currentTask(editor: Editor): { node: PMNode; pos: number; depth: number } | null {
  const { selection } = editor.state;
  if (selection instanceof NodeSelection && selection.node.type.name === 'taskItem') {
    return { node: selection.node, pos: selection.from, depth: selection.$from.depth + 1 };
  }
  for (let depth = selection.$from.depth; depth > 0; depth--) {
    const node = selection.$from.node(depth);
    if (node.type.name === 'taskItem') return { node, pos: selection.$from.before(depth), depth };
  }
  return null;
}

export function moveTask(editor: Editor, direction: -1 | 1): boolean {
  const task = currentTask(editor); if (!task) return false;
  const $pos = editor.state.doc.resolve(task.pos);
  const index = $pos.index(); const list = $pos.parent;
  const other = index + direction;
  if (other < 0 || other >= list.childCount) return false;
  const neighbour = list.child(other);
  const destination = direction < 0 ? task.pos - neighbour.nodeSize : task.pos + task.node.nodeSize + neighbour.nodeSize;
  const tr = editor.state.tr.delete(task.pos, task.pos + task.node.nodeSize);
  const at = tr.mapping.map(destination);
  tr.insert(at, task.node).setSelection(NodeSelection.create(tr.doc, at)).scrollIntoView();
  editor.view.dispatch(tr); editor.view.focus(); return true;
}

export function newTask(editor: Editor, placement: 'auto' | 'child' | 'sibling' = 'auto'): boolean {
  const task = currentTask(editor);
  if (!task) return placement === 'auto' && editor.chain().focus().toggleTaskList().run();
  const item = editor.schema.nodes.taskItem.createAndFill({ id: crypto.randomUUID(), checked: false,
    collapsed: false, needs_review: false });
  if (!item) return false;

  let childListPos: number | undefined;
  task.node.forEach((child, offset) => {
    if (childListPos === undefined && child.type.name === 'taskList') childListPos = task.pos + 1 + offset;
  });
  const asChild = placement === 'child'
    || placement === 'auto' && childListPos !== undefined && !task.node.attrs.collapsed;
  const tr = editor.state.tr;
  let at = task.pos + task.node.nodeSize;
  if (asChild) {
    tr.setNodeAttribute(task.pos, 'collapsed', false);
    if (childListPos !== undefined) {
      at = childListPos + 1;
      tr.insert(at, item);
    } else {
      const listPos = task.pos + task.node.nodeSize - 1;
      tr.insert(listPos, editor.schema.nodes.taskList.create(null, item));
      at = listPos + 1;
    }
  } else {
    tr.insert(at, item);
  }
  tr.setSelection(TextSelection.near(tr.doc.resolve(at + 2))).scrollIntoView();
  editor.view.dispatch(tr); editor.view.focus(); return true;
}

export function toggleReview(editor: Editor) {
  const task = currentTask(editor); if (!task) return;
  editor.view.dispatch(editor.state.tr.setNodeAttribute(task.pos, 'needs_review', !task.node.attrs.needs_review));
}

export function deleteTask(editor: Editor) {
  const task = currentTask(editor); if (!task) return;
  let count = 0; task.node.descendants(node => { if (node.type.name === 'taskItem') count++; });
  if (task.node.childCount > 1 && !confirm(`Delete this item and everything inside it${count ? `, including ${count} subtasks` : ''}? Undo can restore it.`)) return;
  editor.view.dispatch(editor.state.tr.deleteRange(task.pos, task.pos + task.node.nodeSize).scrollIntoView());
  editor.view.focus();
}

export const PlanTaskItem = TaskItem.extend({
  draggable: !isStaticSite,
  parseHTML() {
    return [...(this.parent?.() ?? []), { tag: 'li' }];
  },
  addAttributes() {
    return {
      ...this.parent?.(),
      checked: { default: false, keepOnSplit: false, parseHTML: element => element.getAttribute('data-checked') === 'true',
        renderHTML: attrs => ({ 'data-checked': attrs.checked }) },
      collapsed: { default: false, keepOnSplit: false,
        parseHTML: element => element.getAttribute('data-collapsed') === 'true',
        renderHTML: attrs => ({ 'data-collapsed': attrs.collapsed }) },
      needs_review: { default: false, keepOnSplit: false,
        parseHTML: element => element.getAttribute('data-needs-review') === 'true',
        renderHTML: attrs => ({ 'data-needs-review': attrs.needs_review }) },
    };
  },
  addKeyboardShortcuts() {
    return {
      ...this.parent?.(),
      Enter: () => {
        const { $from } = this.editor.state.selection;
        if ($from.depth < 2 || $from.node(-1).type.name !== 'taskItem') return false;
        if (!$from.parent.content.size && $from.node(-1).childCount === 1) {
          return this.editor.commands.liftListItem(this.name);
        }
        return this.editor.commands.splitBlock();
      },
    };
  },
  addNodeView() {
    return ({ node, editor, getPos, decorations }) => {
      let current = node;
      let number = String(decorations.find(d => d.spec.outlineNumber)?.spec.outlineNumber ?? '');
      const dom = document.createElement('li'); dom.className = 'document-task'; dom.draggable = !isStaticSite;
      const controls = document.createElement('span'); controls.className = 'task-controls'; controls.contentEditable = 'false';
      const handle = document.createElement('button'); handle.type = 'button'; handle.textContent = '⠿';
      handle.className = 'task-drag'; handle.draggable = true; handle.title = 'Drag to move · click for item actions';
      handle.setAttribute('aria-label', 'Move or manage item'); handle.setAttribute('aria-haspopup', 'menu');
      handle.setAttribute('aria-expanded', 'false');
      handle.onmousedown = () => { const pos = getPos(); if (pos !== undefined) editor.view.dispatch(editor.state.tr.setSelection(NodeSelection.create(editor.state.doc, pos))); };
      const collapse = document.createElement('button'); collapse.type = 'button'; collapse.className = 'task-collapse';
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox';
      checkbox.disabled = isStaticSite;
      handle.hidden = isStaticSite;
      const badge = document.createElement('span'); badge.className = 'task-detail-badge'; badge.contentEditable = 'false';
      const content = document.createElement('div'); content.className = 'task-content';
      controls.append(handle, collapse, checkbox); dom.append(controls, content, badge);
      handle.onclick = event => {
        event.preventDefault(); event.stopPropagation();
        const pos = getPos(); if (pos === undefined) return;
        editor.view.dispatch(editor.state.tr.setSelection(NodeSelection.create(editor.state.doc, pos)));
        editor.view.dom.dispatchEvent(new CustomEvent('plan-actions', { detail: { trigger: handle } }));
      };
      const numberLabel = document.createElement('span'); numberLabel.className = 'task-number';
      numberLabel.setAttribute('aria-hidden', 'true'); controls.insertBefore(numberLabel, checkbox);
      const change = (values: Record<string, unknown>, history = true) => {
        if (isStaticSite && Object.keys(values).some(key => key !== 'collapsed')) return;
        const pos = getPos(); if (pos === undefined) return;
        const tr = editor.state.tr;
        if (values.collapsed && tr.selection.from > pos && tr.selection.to < pos + current.nodeSize) {
          tr.setSelection(TextSelection.near(tr.doc.resolve(pos + 2)));
        }
        for (const [key, value] of Object.entries(values)) tr.setNodeAttribute(pos, key, value);
        if (isStaticSite) tr.setMeta('planViewCollapse', true);
        if (!history) tr.setMeta('addToHistory', false);
        editor.view.dispatch(tr);
        if (!isStaticSite) editor.view.focus();
      };
      checkbox.onmousedown = event => event.preventDefault();
      checkbox.onchange = () => change({ checked: checkbox.checked });
      collapse.onmousedown = event => { if (!isStaticSite) event.preventDefault(); };
      collapse.onclick = () => change({ collapsed: !current.attrs.collapsed }, false);
      const paint = () => {
        numberLabel.textContent = number;
        dom.style.setProperty('--item-number-width', Math.max(2, number.length + 1) + 'ch');
        dom.dataset.checked = String(Boolean(current.attrs.checked));
        dom.dataset.collapsed = String(Boolean(current.attrs.collapsed));
        dom.dataset.taskId = String(current.attrs.id ?? '');
        collapse.hidden = current.childCount < 2;
        collapse.textContent = current.attrs.collapsed ? '▸' : '▾';
        collapse.setAttribute('aria-expanded', String(!current.attrs.collapsed));
        collapse.setAttribute('aria-label', current.attrs.collapsed ? 'Expand item' : 'Collapse item');
        checkbox.checked = Boolean(current.attrs.checked);
        checkbox.setAttribute('aria-label', `${isStaticSite ? 'Completion status of' : 'Complete'} item ${number}: `
          + (current.firstChild?.textContent || 'Untitled'));
        let unfinished = 0;
        current.descendants(child => { if (child.type.name === 'taskItem' && !child.attrs.checked) unfinished++; });
        badge.textContent = [current.attrs.needs_review ? 'Needs review' : '', unfinished ? `${unfinished} unfinished` : ''].filter(Boolean).join(' · ');
      };
      paint();
      return {
        dom, contentDOM: content,
        update(updated, nextDecorations) {
          if (updated.type !== current.type) return false;
          current = updated; number = String(nextDecorations.find(d => d.spec.outlineNumber)?.spec.outlineNumber ?? '');
          paint(); return true;
        },
        stopEvent(event) { return controls.contains(event.target as globalThis.Node) && !handle.contains(event.target as globalThis.Node); },
        ignoreMutation(mutation) { return mutation.type !== 'selection' && !content.contains(mutation.target); },
      };
    };
  },
}).configure({ nested: true });
