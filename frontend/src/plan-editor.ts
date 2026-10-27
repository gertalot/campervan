import { Editor, Extension, type JSONContent } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import { TaskList } from '@tiptap/extension-list';
import { TableKit } from '@tiptap/extension-table';
import UniqueID from '@tiptap/extension-unique-id';
import { Plugin, PluginKey, TextSelection } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { Node as PMNode } from '@tiptap/pm/model';
import { PlanTaskItem } from './plan-task';
import { mountPlanInsert, PlanSlash } from './plan-insert';
import { PlanActionKeys } from './plan-actions';
import { mountPlanMenu } from './plan-menu';
import { outlineNumbers } from './plan-numbering';
import { purchaseExtension } from './plan-purchases';
import type { PlanningClient } from './planning-api';
import { isStaticSite } from './site-runtime';

type ViewState = { query: string; hideCompleted: boolean };
const viewKey = new PluginKey<ViewState>('planView');
function matches(doc: PMNode, query: string) {
  const ranges: { from: number; to: number }[] = [];
  if (!query) return ranges;
  doc.descendants((node, pos) => {
    if (!node.isTextblock) return;
    const text = node.textBetween(0, node.content.size, '\n', '\n').toLowerCase();
    for (let index = text.indexOf(query); index >= 0; index = text.indexOf(query, index + Math.max(query.length, 1))) {
      ranges.push({ from: pos + 1 + index, to: pos + 1 + index + query.length });
    }
    return false;
  });
  return ranges;
}
const PlanView = Extension.create({
  name: 'planView',
  addProseMirrorPlugins() {
    return [new Plugin<ViewState>({
      key: viewKey,
      state: {
        init: () => ({ query: '', hideCompleted: false }),
        apply: (tr, value) => tr.getMeta(viewKey) ?? value,
      },
      props: {
        decorations(state) {
          const view = viewKey.getState(state)!;
          const found = matches(state.doc, view.query);
          const decorations = [...outlineNumbers(state.doc), ...found.map(range => Decoration.inline(range.from, range.to, { class: 'plan-match' }))];
          state.doc.descendants((node, pos) => {
            if (node.type.name !== 'taskItem') return;
            const active = state.selection.from > pos && state.selection.from < pos + node.nodeSize;
            const matched = found.some(range => range.from > pos && range.to < pos + node.nodeSize);
            const caretHidden = active && state.selection.from >= pos + 1 + (node.firstChild?.nodeSize ?? 0);
            let unfinished = false;
            node.descendants(child => { if (child.type.name === 'taskItem' && !child.attrs.checked) unfinished = true; });
            const hidden = view.hideCompleted && node.attrs.checked && !unfinished && !active && !matched;
            const reveal = matched || caretHidden;
            if (hidden || reveal) decorations.push(Decoration.node(pos, pos + node.nodeSize,
              { class: hidden ? 'plan-hidden' : 'is-expanded-in-view' }));
          });
          return DecorationSet.create(state.doc, decorations);
        },
      },
    })];
  },
});
const PublishedPlan = Extension.create({
  name: 'publishedPlan',
  addProseMirrorPlugins() {
    return [new Plugin({
      // Disclosure is a local view change. All content-changing commands, including built-in
      // keyboard shortcuts and table actions, are rejected in the published document.
      filterTransaction: tr => !tr.docChanged || Boolean(tr.getMeta('planViewCollapse')),
    })];
  },
});

export function createPlanEditor(
  root: HTMLElement,
  options: { content: JSONContent; client: PlanningClient; onChange: (content: JSONContent) => void;
    fileButton?: HTMLButtonElement },
) {
  const toolbar = document.createElement('div');
  const area = document.createElement('div'); area.className = 'document-surface'; root.append(toolbar, area);
  const editor = new Editor({
    element: area,
    editable: !isStaticSite,
    extensions: [
      StarterKit.configure({ link: { openOnClick: true }, bulletList: false, orderedList: false, listItem: false, listKeymap: false }),
      TaskList.extend({
        addKeyboardShortcuts() { return {}; },
        parseHTML() { return [...(this.parent?.() ?? []), { tag: 'ul' }, { tag: 'ol' }]; },
      }), PlanTaskItem,
      TableKit.configure({ table: { resizable: !isStaticSite } }),
      purchaseExtension(options.client), UniqueID.configure({ types: ['taskItem', 'purchaseView'], updateDocument: !isStaticSite }),
      ...(isStaticSite ? [PlanView, PublishedPlan] : [PlanSlash, PlanView, PlanActionKeys]),
    ],
    content: options.content, enableContentCheck: true,
    editorProps: { attributes: { class: 'plan-rich-text continuous-document', 'aria-label': 'Conversion plan document' } },
    onUpdate: ({ editor }) => { if (!isStaticSite) options.onChange(editor.getJSON()); },
    onBlur: () => { void options.client.flush().catch(() => {}); },
  });
  // Do not accept editor repair as a substitute for validating the saved document.
  editor.schema.nodeFromJSON(options.content).check();
  const menu = isStaticSite ? null : mountPlanMenu(editor);
  const controls = menu ? mountPlanInsert(toolbar, editor, menu.open, options.fileButton) : null;
  if (isStaticSite) toolbar.remove();
  return {
    editor,
    setView(query: string, hideCompleted: boolean) {
      editor.view.dispatch(editor.state.tr.setMeta(viewKey, { query: query.toLowerCase(), hideCompleted }));
    },
    find(direction: -1 | 1) {
      const query = viewKey.getState(editor.state)?.query ?? '';
      const ranges = matches(editor.state.doc, query); if (!ranges.length) return 0;
      const position = editor.state.selection.from;
      const target = direction > 0 ? ranges.find(range => range.from > position) ?? ranges[0]
        : [...ranges].reverse().find(range => range.from < position) ?? ranges.at(-1)!;
      editor.view.dispatch(editor.state.tr.setSelection(TextSelection.create(editor.state.doc, target.from, target.to)).scrollIntoView());
      editor.view.focus(); return ranges.length;
    },
    destroy() { menu?.destroy(); controls?.destroy(); editor.destroy(); root.replaceChildren(); },
  };
}
