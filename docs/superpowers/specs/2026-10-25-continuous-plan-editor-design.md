# Continuous conversion plan editor

Status: authorised and implemented in source on 25 October 2026; visual acceptance remains pending.
Supersedes the separate task-title/notes-editor interaction in the 24 October planner design.

## What Gert should be able to do

Write the conversion plan as a document: mix paragraphs, collapsible numbered checkbox items, tables and linked purchases
in the order that makes sense. Click and type directly. Write several lines without creating another checkbox.
Insert a table where the caret is, fill it, and continue writing underneath. Common writing actions must not require
opening “⋯”, constructing a notes container, or switching to another editor.

Keep the existing task completion, review flags, nesting, collapse, movement, purchasing totals, sourcing notes,
backups and assistant editing. Use task, subtask, text, table and purchases in the UI. Remove branch/node/child terminology.
This is one person's local hobby app; avoid unrelated editor features and project-management machinery.

## Chosen mechanism

Use one persistent Tiptap editor for the Plan document. Its document is the only owner of outline structure and its
history handles text, task completion, tables and moves. Retain the existing purchase records/calculations and mount
the existing purchase grid as a document element. No nested Editors, parallel task tree, or synchronisation adapter
between two live representations.

More buttons around the existing editors would retain disconnected selection and undo. Changing editor frameworks
has no demonstrated benefit here. Reuse StarterKit, TableKit and the installed list package; extend only task controls,
purchase embedding and the few commands described below. Prefer supplied editor commands over custom input handling.

## Writing surface and controls

One compact sticky toolbar provides:

- A format selector: Paragraph / Heading, plus familiar bold, italic and link controls.
- Direct **Item**, **Table** and **Purchases** insertion buttons, plus Undo/Redo.
- A visible **Actions** trigger for contextual commands with shortcut labels; item handles and right-click open the
  same relevant actions. Keyboard invocation, navigation, Escape/focus return and a shortcut reference are included.

There is one list type, with checkboxes and hierarchical numbering (`1`, `1.1`, `1.2.1`, `2`). There are no Task/Bullets/
Numbered type choices. Numbers are derived from order and nesting, including hidden/completed items. Stable task IDs
remain independent of numbering. Existing and pasted conventional lists become unchecked items in this hierarchy.
The format selector changes text formatting within an item; New paragraph preserves its checkbox/review metadata.

Controls retain the caret when clicked and work by keyboard. Show shortcuts in tooltips and make disabled actions
explainable. A slash picker is a second route to the same commands, never the only route. File/export/restore and
infrequent destructive actions can live in an overflow menu. No repeated note cards or per-item formatting bars.

## Keyboard contract

Use supplied editor commands, with the explicit typing contract refined by Gert: Enter continues writing within an
item; creating an item is a separate action. These application shortcuts are shown in the menu, not assumed known.

| Context/action | Result |
| --- | --- |
| Click existing text / document's blank final area | Place caret and write; an empty document has a paragraph |
| Enter in prose | New paragraph |
| Enter in an item | New paragraph in the same item; no extra checkbox |
| Item, `/task`, Cmd/Ctrl+Shift+Enter | New unchecked sibling after the current item |
| Cmd/Ctrl+Enter in an item outside tables | Complete/reopen that item |
| Shift+Enter, including in a task or table cell | New line in the same paragraph; no new task |
| New paragraph, `/text`, or Alt/Option+Enter | Another paragraph in the same item/container |
| Enter in an empty final list item | Outdent one level, or leave the outer list and continue prose |
| Tab / Shift+Tab in a list | Indent/outdent; table context takes precedence |
| Tab / Shift+Tab in a table | Next/previous cell; Tab in the last cell adds a row |
| Tab in ordinary prose | Normal keyboard focus navigation |
| Table or `/table` | Insert a 3×3 table at the selection, with caret in the first cell |
| Purchases or `/purchases` | Insert a linked purchase view at the selection |
| Cmd/Ctrl+Z and redo | Document undo/redo when the editor has focus |

There is no “first paragraph is a title field, later paragraphs use another editing mode” rule. Enter splits prose
within the current item. New item inserts a sibling after the entire current item, retaining its contents and metadata.
New items start unchecked, expanded and without a review flag. Normal editor undo restores removed/merged content.

For empty-paragraph exit, only lift/exit an empty final paragraph/item. An item with later notes, tables or subtasks is
not empty; do not discard or detach that content. Plain Enter after prose stays prose; tasks never need to be created
in order to write. Preserve IME/composition and native selection/clipboard behaviour.

The slash picker triggers at a fresh line or after whitespace, supports filtering, arrows/Enter/Escape, and replaces
only the matched command text. Escape leaves the typed text intact. Do not trigger inside URLs, code, purchase inputs
or while composing text. Support `/text`, `/task`, `/heading`, `/table` and `/purchases`.

## Tables and purchases

Use TableKit for direct cell editing, multiline text, selection, resizing, row/column operations and HTML-table paste.
When inside a table, show labelled row/column controls in the shared toolbar. Use these controls first; do not require
custom floating edge controls as a separate UI mechanism. Do not promise spreadsheet/TSV import beyond library support.
Keep the table horizontally scrollable, without making the entire document overflow.

Every inserted table/purchase view has an accessible following paragraph within the same containing task or document.
Arrow navigation, Add text and clicking after it must let the user continue writing. Table insertion must not replace
the surrounding task or lose the text on either side of the selection.

A Purchases view stores only its ID and filters. Filter changes are document edits; record/quantity/cost changes go to
the purchase API. Copying a view creates a new view ID that shows the same records. Removing a view never deletes stock
or spending. The embedded controls are ordinary inputs outside the editor's editable DOM and must not trigger editor
shortcuts. Commit a changed valid cell on blur before moving focus out; invalid input stays visible with an error.
Refresh/filter updates preserve a focused draft and do not silently replace it.

Document Undo and **Undo purchase / Redo purchase** have separate, clearly labelled scopes. A purchase input retains
its native text undo while focused. Document undo can restore a removed Purchases view or a filter, never an old bought
quantity. Collapse/tab switching does not destroy the embedded grid and its active draft.

## Collapse, movement, search and undo

Tasks show a checkbox, drag handle, collapse control where there is content to hide, review indicator and unfinished
subtask count. Checking a task changes only that task. Collapse hides everything after its first paragraph, retaining
the actual document data. Move the caret to the visible paragraph before hiding content that contains it.

Keep collapse as an in-document attribute for persistence, but excluded from editing history; set it not to inherit on
split. A move includes the whole item, notes and subtasks, retaining IDs, and is one undoable transaction. Use the
editor's drag/drop support and drop indicator; nest using indent/outdent, rather than inventing a second independent
HTML drag tree. Show the drag handle for a hovered or keyboard-focused item. Indent/Outdent and Move up/down must also
be keyboard accessible. Reject a move into the moved item's own contents.

Use document search highlights with next/previous navigation. Temporarily reveal matching collapsed/hidden ancestors
without changing saved collapse state. Hide completed hides a task only when it contains no unfinished subtasks.
These views must not reconstruct document content or reset undo. Temporarily reveal the active task while editing so
completing it or a search match cannot strand the caret in invisible content.

Use standard editor selection, copy/paste, Backspace/Delete and undo. Do not introduce transaction-wide confirmation
interception for normal keyboard edits. An explicit Delete item action states the included subtask count and confirms
if it removes nested/hidden contents. Selected/deleted content remains recoverable through document undo. A collapsed
item's handle selects the entire task, including the hidden content. Copy creates new task/view IDs while preserving
copied text and status; cut/move preserves identity within this document. A new task created by splitting starts unchecked,
unlike a copied task. Pasting external formatted text must retain supported formatting and tables.

Keep one editor alive across saves, tab switches, completion, collapse and movement. Only explicit Reload/Restore
replaces the document and resets session history. In addition to the dirty guard, flush a pending valid save on editor
blur or tab switch; do not delay a navigation indefinitely if saving fails. Show Saved/Saving/Error plainly.

## Document storage and compatibility

Version 2 is `{version: 2, revision, content: <Tiptap JSON>, purchases}`. Only tasks and purchase views require stable
IDs. Prose, headings, lists and table cells use editor positions; the assistant can locate them by their containing
task and document path. Do not require a global ID registry for every table cell/paragraph. Optional legacy prose IDs
can be retired: searches found their only consumers inside the superseded note editor, not external links.

Reuse existing atomic JSON saves and the single serial revision-guarded client queue. Content saves replace only
content; purchase saves replace only purchase metadata. Never use a whole planning-document replacement for ordinary
editing. On a stale write retain the draft, stop automatic writes and offer download/reload; do not silently rebase.

A narrow legacy converter preserves task IDs, completion/review/collapse, title text/line breaks, note contents/tables,
BOM filters, subtask order and all purchase records. Convert each old task to first paragraph + old note/BOM contents
in order + nested tasks. Do not guess that root tasks are headings or discard empty notes. Preserve existing task/view
IDs; if legacy namespaces collide, retain task IDs and deterministically rename the view ID. Record IDs are unchanged.
Legacy rich text uses editor positions after conversion; there is no need to retain meaningless note-wrapper identities.

Validate the converted document before persistence. Keep the exact current version-1 file as `planning.v1-backup.json`
using exclusive creation, never overwriting it. If a different v1 file is later restored after that backup exists, its
imported contents are protected by normal restore/previous-save handling; do not reuse the first migration as an excuse
to reset it. Unsupported/invalid data produces an error and retains the source, never a fresh seed.

Use the converter when loading v1 files and importing v1 backups. Only conversion of the active file writes/increments
its revision. Reading a previous save or import candidate converts in memory and must not touch current/backup files.
Keep backup envelope version 1: its fields (planning/project/products) are unchanged; the nested planning document's
version identifies the new format. Accept nested planning v1/v2; reject unknown future versions without file changes.
Exports, Markdown, previous-save recovery and restore must all understand v2. CSV/purchase calculations remain intact.

Expose `PUT /api/v1/planning/content` with expected revision; preserve purchase operations. Retire old task-tree
operations with an explicit reload/version error. The assistant reads content, edits by task ID/document path and saves
against the read revision. No patch framework, CRDT or permanent second representation is needed.

## Implementation order and limits

Establish the editor schema and convert old content in memory, then implement continuous writing/insertion before
wiring active-file migration and saves. The first UX checkpoint is the user's actual task → multiline text → table →
more prose interaction. This is a checkpoint in implementation order, not a second editor, preview app or new approval
system. Then integrate purchasing, persistence, movement and recovery, and check the complete saved workflow.

No tests, delegated reviews, browser automation, extra verification processes or service starts. Gert's interaction
in the existing app tab is the visual acceptance check. No React conversion, paid UI, collaboration, deployment work,
formula engine or unrelated CAD changes. Preserve unrelated working-tree edits.

## Evidence and review decisions

The reviewed implementation has title inputs and separately instantiated note Editors in `planner.ts`/`plan-editor.ts`;
structural rendering destroys all note Editors. `planning.py` fixes note order before children. `planning-api.ts` owns
the save queue and separate structural inverse history. `purchase-grid.ts` owns committed purchase updates and refresh.
No external consumers of the old note-wrapper IDs were found in frontend source, Python source or `docs/planner.md`.

Installed Tiptap 3.32.0 sources establish that nested TaskItem already accepts `paragraph block*`, provides
split/sink/lift commands, and StarterKit already includes standard lists, gap cursor, trailing paragraph and history.
HardBreak maps Shift+Enter; Cmd/Ctrl+Enter is completion in item context and retains hard-break behaviour elsewhere.
TableKit supplies table operations. StarterKit's bullet/ordered/list-item extensions are disabled in the current design.
The plan extends these mechanisms instead of reimplementing their responsibilities.

Reviewed official documentation:
- https://tiptap.dev/docs/editor/extensions/nodes/task-item — list behaviour and vanilla integration.
- https://tiptap.dev/docs/editor/extensions/functionality/uniqueid — ID handling on splits/paste/undo.
- https://tiptap.dev/docs/editor/extensions/functionality/drag-handle — supplied drag handles and nested targeting;
  inspect compatibility with 3.32.0 before adopting it, rather than copying newer documentation uncritically.
- https://workflowy.com/help/add-edit-format and https://workflowy.com/help/tables — writing/table conventions.
- https://www.notion.com/help/writing-and-editing-basics and https://www.notion.com/help/keyboard-shortcuts — document UX.
- https://www.nngroup.com/articles/progressive-disclosure/ — primary actions remain exposed.
- https://www.nngroup.com/articles/recognition-and-recall/ and
  https://www.nngroup.com/articles/ten-usability-heuristics/ — discoverability, familiar language and user control.

These conventions inform the proposal; Gert's typing experience remains the evidence that it fits this application.
The later [menu and numbering research](../../planner-ux.md) records the 25 October refinements and current limits.
