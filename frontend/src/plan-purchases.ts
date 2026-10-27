import { Node, mergeAttributes } from '@tiptap/core';
import { mountPurchaseGrid } from './purchase-grid';
import { emptyFilter, type PlanningClient, type PurchaseFilter } from './planning-api';
import { isStaticSite } from './site-runtime';

export function purchaseExtension(client: PlanningClient) {
  return Node.create({
    name: 'purchaseView', group: 'block', atom: true, draggable: !isStaticSite, selectable: true,
    addAttributes() { return { filter: { default: emptyFilter(), parseHTML: element => {
      try { return JSON.parse(element.getAttribute('data-filter') || '{}'); } catch { return emptyFilter(); }
    }, renderHTML: attrs => ({ 'data-filter': JSON.stringify(attrs.filter) }) } }; },
    parseHTML() { return [{ tag: 'section[data-purchases]' }]; },
    renderHTML({ HTMLAttributes }) { return ['section', mergeAttributes(HTMLAttributes, { 'data-purchases': '' }), 'Purchases']; },
    addNodeView() {
      return ({ node, getPos, editor }) => {
        let current = node;
        const dom = document.createElement('section'); dom.className = 'document-purchases'; dom.contentEditable = 'false';
        const heading = document.createElement('strong'); heading.textContent = 'Purchases · shared with Bill of materials';
        const body = document.createElement('div'); dom.append(heading, body);
        const grid = mountPurchaseGrid(body, client, { ...emptyFilter(), ...node.attrs.filter } as PurchaseFilter, filter => {
          if (!editor.isEditable) return;
          const pos = getPos(); if (pos === undefined) return;
          editor.view.dispatch(editor.state.tr.setNodeMarkup(pos, undefined, { ...current.attrs, filter }));
        });
        return {
          dom,
          update(updated) {
            if (updated.type !== current.type) return false;
            current = updated; grid.setFilter(updated.attrs.filter as PurchaseFilter); return true;
          },
          stopEvent(event) { return !['dragstart', 'dragover', 'drop'].includes(event.type); },
          ignoreMutation() { return true; },
          destroy() { grid.destroy(); },
        };
      };
    },
  });
}
