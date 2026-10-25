import type { Node as PMNode } from '@tiptap/pm/model';
import { Decoration } from '@tiptap/pm/view';

/** Numbers are a view of document order, never task identity or saved text. */
export function outlineNumbers(doc: PMNode): Decoration[] {
  const counts = new Map<number, number>();
  const labels = new Map<number, string>();
  const decorations: Decoration[] = [];
  doc.descendants((node, pos) => {
    if (node.type.name !== 'taskItem') return;
    const resolved = doc.resolve(pos);
    let parent = -1;
    for (let depth = resolved.depth; depth > 0; depth--) {
      const ancestor = resolved.node(depth);
      if (ancestor.type.name === 'taskItem') { parent = resolved.before(depth); break; }
    }
    const next = (counts.get(parent) ?? 0) + 1; counts.set(parent, next);
    const number = parent >= 0 ? `${labels.get(parent)}.${next}` : String(next);
    labels.set(pos, number);
    decorations.push(Decoration.node(pos, pos + node.nodeSize, { 'data-outline-number': number }, { outlineNumber: number }));
  });
  return decorations;
}
