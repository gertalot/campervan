import type { Editor } from '@tiptap/core';
import Suggestion, { exitSuggestion } from '@tiptap/suggestion';
import { Extension } from '@tiptap/core';
import { action, el } from './purchase-grid';
import { actionLabel, ariaShortcut, getAction, runAction, runPlanCommand, shortcutLabel, type PlanCommand } from './plan-actions';
import type { MenuRequest } from './plan-menu';

const choices: { command: PlanCommand; label: string }[] = [
  { command: 'text', label: 'Add text' }, { command: 'task', label: 'New item' },
  { command: 'heading', label: 'Heading' }, { command: 'table', label: 'Table' },
  { command: 'purchases', label: 'Purchases' },
];

export const PlanSlash = Extension.create({
  name: 'planSlash',
  addProseMirrorPlugins() {
    return [Suggestion<{ command: PlanCommand; label: string }>({
      editor: this.editor, char: '/', allowedPrefixes: [' ', '\n'],
      allow: ({ state }) => {
        if (this.editor.view.composing || this.editor.isActive('code')) return false;
        for (let d = state.selection.$from.depth; d > 0; d--) if (state.selection.$from.node(d).type.name === 'codeBlock') return false;
        return true;
      },
      items: ({ query }) => choices.filter(item => (item.command !== 'task' || !this.editor.isActive('table'))
        && `${item.command} ${item.label}`.toLowerCase().includes(query.toLowerCase())),
      command: ({ editor, range, props }) => {
        editor.chain().focus().deleteRange(range).run(); runPlanCommand(editor, props.command);
      },
      render: () => {
        let popup: HTMLDivElement | null = null;
        let selected = 0;
        let items: { command: PlanCommand; label: string }[] = [];
        let choose: (item: { command: PlanCommand; label: string }) => void = () => {};
        let activeEditor: Editor | null = null;
        const paint = () => {
          if (!popup) return;
          popup.replaceChildren();
          if (!items.length) { popup.append(el('span', 'No matching insert action')); return; }
          items.forEach((item, index) => {
            const button = action('', () => choose(item)); button.setAttribute('role', 'option');
            button.append(el('span', item.label), el('kbd', item.command === 'task' ? shortcutLabel(getAction('newItem').shortcut) : '/' + item.command));
            button.id = `plan-insert-option-${index}`;
            button.setAttribute('aria-selected', String(index === selected));
            button.onmousedown = event => event.preventDefault(); popup!.append(button);
          });
          const hint = el('div', '↑↓ choose · Tab / Enter insert · Esc cancel');
          hint.className = 'plan-slash-hint'; popup.append(hint);
          activeEditor?.view.dom.setAttribute('aria-activedescendant', `plan-insert-option-${selected}`);
        };
        const position = (rect: DOMRect | null | undefined) => {
          if (!popup || !rect) return;
          popup.style.left = `${Math.min(rect.left, window.innerWidth - 230)}px`;
          popup.style.top = `${Math.min(rect.bottom + 6, window.innerHeight - popup.offsetHeight - 12)}px`;
        };
        return {
          onStart(props) {
            activeEditor = props.editor;
            popup = el('div'); popup.className = 'plan-slash'; popup.setAttribute('role', 'listbox');
            popup.id = 'plan-insert-options';
            activeEditor.view.dom.setAttribute('aria-controls', popup.id);
            activeEditor.view.dom.setAttribute('aria-expanded', 'true');
            popup.setAttribute('aria-label', 'Insert content'); document.body.append(popup);
            items = props.items; choose = props.command; selected = 0; paint(); position(props.clientRect?.());
          },
          onUpdate(props) { items = props.items; choose = props.command; selected = Math.min(selected, Math.max(items.length - 1, 0)); paint(); position(props.clientRect?.()); },
          onKeyDown({ event }) {
            if (event.key === 'Escape') { if (activeEditor) exitSuggestion(activeEditor.view); return true; }
            if (!popup) return false;
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
              selected = (selected + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % Math.max(items.length, 1); paint(); return true;
            }
            if ((event.key === 'Enter' || event.key === 'Tab') && items[selected]
                && !event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey
                && !event.isComposing && !activeEditor?.view.composing) {
              event.preventDefault(); choose(items[selected]); return true;
            }
            return false;
          },
          onExit() {
            popup?.remove(); popup = null;
            for (const attribute of ['aria-controls', 'aria-expanded', 'aria-activedescendant']) activeEditor?.view.dom.removeAttribute(attribute);
          },
        };
      },
    })];
  },
});

const iconPaths = {
  link: ['M10 13a5 5 0 0 0 7 .1l3-3a5 5 0 0 0-7-7l-1.7 1.7', 'M14 11a5 5 0 0 0-7-.1l-3 3a5 5 0 0 0 7 7l1.7-1.7'],
  task: ['M12 5v14M5 12h14'],
  table: ['M3 3h18v18H3zM3 9h18M9 3v18'],
  costs: ['M6 3h12v18l-3-2-3 2-3-2-3 2zM9 7h6M9 11h6M9 15h3'],
  undo: ['M9 5L4 10l5 5', 'M4 10h10a6 6 0 0 1 6 6v3'],
  redo: ['M15 5l5 5-5 5', 'M20 10H10a6 6 0 0 0-6 6v3'],
};
function icon(name: keyof typeof iconPaths) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  for (const [key, value] of Object.entries({ viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
    'stroke-width': '1.7', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' })) svg.setAttribute(key, value);
  for (const path of iconPaths[name]) {
    const element = document.createElementNS('http://www.w3.org/2000/svg', 'path'); element.setAttribute('d', path); svg.append(element);
  }
  return svg;
}

export function mountPlanInsert(
  root: HTMLElement, editor: Editor, openMenu: (request?: MenuRequest) => void, fileButton?: HTMLButtonElement,
) {
  root.className = 'document-toolbar'; root.setAttribute('aria-label', 'Text formatting and insertion');
  if (fileButton) root.append(fileButton);
  const controls: { button: HTMLButtonElement; available: () => boolean; active?: () => boolean }[] = [];
  const group = (label: string) => { const node = el('div'); node.className = 'format-group'; node.setAttribute('role', 'group'); node.setAttribute('aria-label', label); root.append(node); return node; };
  const styles = group('Paragraph style');
  const marks = group('Text formatting');
  const inserts = group('Insert');
  const history = group('History');
  const button = (parent: HTMLElement, label: string, content: HTMLElement | SVGSVGElement, run: () => void,
    available = () => true, active?: () => boolean, visibleLabel = '') => {
    const item = action('', run); item.title = label; item.setAttribute('aria-label', label);
    item.append(content); if (visibleLabel) item.append(el('span', visibleLabel));
    item.onmousedown = event => event.preventDefault(); parent.append(item);
    controls.push({ button: item, available, active }); return item;
  };
  const format = el('select'); format.setAttribute('aria-label', 'Paragraph style');
  format.append(new Option('Normal text', 'paragraph'), new Option('Heading 1', '1'), new Option('Heading 2', '2'), new Option('Heading 3', '3'));
  format.onchange = () => {
    const heading = Number(format.value);
    runAction(editor, getAction(heading ? 'heading' + heading : 'paragraph'));
  };
  styles.append(format);
  const commandButton = (parent: HTMLElement, actionId: string, content: HTMLElement | SVGSVGElement, visibleLabel = '') => {
    const entry = getAction(actionId);
    const label = actionLabel(entry, editor) + (entry.shortcut ? ' · ' + shortcutLabel(entry.shortcut) : entry.alias ? ' · ' + entry.alias : '');
    const control = button(parent, label, content, () => { runAction(editor, entry); },
      () => (!entry.enabled || entry.enabled(editor)) && (!entry.when || entry.when(editor)),
      entry.checked ? () => entry.checked!(editor) : undefined, visibleLabel);
    if (entry.shortcut) control.setAttribute('aria-keyshortcuts', ariaShortcut(entry.shortcut)!);
    return control;
  };
  commandButton(marks, 'bold', el('b', 'B'));
  commandButton(marks, 'italic', el('i', 'I'));
  commandButton(marks, 'link', icon('link'));
  commandButton(inserts, 'newItem', icon('task'), 'Item');
  commandButton(inserts, 'table', icon('table'), 'Table');
  commandButton(inserts, 'purchases', icon('costs'), 'Purchases');
  commandButton(history, 'undo', icon('undo'));
  commandButton(history, 'redo', icon('redo'));
  const menuButton = action('Actions ▾', () => openMenu({ trigger: menuButton, full: true }));
  menuButton.className = 'context-actions-trigger'; menuButton.title = 'Actions for current selection · Shift+F10';
  menuButton.setAttribute('aria-haspopup', 'menu'); menuButton.setAttribute('aria-expanded', 'false');
  menuButton.onmousedown = event => event.preventDefault();
  menuButton.onkeydown = event => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault(); openMenu({ trigger: menuButton, full: true, initial: event.key === 'ArrowUp' ? 'last' : 'first' });
    }
  };
  root.append(menuButton);
  const tables = el('div'); tables.className = 'document-table-tools'; root.append(tables);
  for (const actionId of ['rowAfter', 'columnAfter', 'deleteRow', 'deleteColumn', 'deleteTable']) {
    const entry = getAction(actionId);
    const b = action(actionLabel(entry, editor), () => { runAction(editor, entry); });
    b.onmousedown = event => event.preventDefault(); tables.append(b);
  }
  const update = () => {
    format.value = editor.isActive('heading') ? String(editor.getAttributes('heading').level) : 'paragraph';
    format.disabled = !editor.isEditable;
    for (const option of Array.from(format.options)) if (option.value !== 'paragraph') {
      option.disabled = !editor.can().setHeading({ level: Number(option.value) as 1 | 2 | 3 });
    }
    for (const control of controls) {
      control.button.disabled = !editor.isEditable || !control.available();
      if (control.active) control.button.setAttribute('aria-pressed', String(control.active()));
    }
    tables.hidden = !editor.isActive('table');
  };
  editor.on('transaction', update); update();
  return { destroy() { editor.off('transaction', update); root.replaceChildren(); } };
}
