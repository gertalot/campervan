# Continuous Plan Editor Implementation Plan

> Use superpowers:executing-plans for local implementation after authorisation.
> Project instructions override skill defaults: no tests, delegated reviews, browser interaction checks or service starts.

**Status:** implemented in source on 25 October 2026; visual acceptance remains pending.

**Later refinements:** Gert changed the typing contract and requested a single numbered checkbox list, with contextual
menus showing actions and shortcuts. The current contract in [the guide](../../planner.md) and
[UX decisions](../../planner-ux.md) supersedes the original list/split/toolbar task descriptions below.
Implementation now also includes `plan-actions.ts` (shared commands/keys), `plan-menu.ts` (context menus/help) and
`plan-numbering.ts` (derived hierarchical numbers). Conventional saved/pasted lists become checkbox items. No list-type
toggles remain. Enter adds prose; New item inserts an unchecked sibling. Menu behaviour has not been interaction-tested.

**Goal:** Make Plan a document Gert can write in continuously, mixing nested tasks, multiline prose, tables and purchases.

**Architecture:** One persistent Tiptap Editor owns content and document history. Existing purchase records and the
purchase grid retain their own responsibility. Store one rich document and purchase dictionary in the existing planning
file, with a narrow backed-up conversion from the current task tree.

**Stack:** Existing vanilla TypeScript/Vite, Tiptap 3.32.0, FastAPI/Pydantic and local JSON. Python runs only through uv.

**Design:** `docs/superpowers/specs/2026-10-25-continuous-plan-editor-design.md` (revised proposal).

## Corrections made in this review

| Earlier gap | Resolution |
| --- | --- |
| Supporting prose still required a special mouse action | Shift+Enter adds a line; Add text, `/text` and Alt/Option+Enter add a paragraph within the same task |
| Enter changed meaning between a task's first and later paragraphs | Uniform list semantics; no hidden title/notes editing modes |
| “Text” mixed insertion and conversion | Separate Paragraph formatting from the explicitly labelled Add text action |
| Splits/paste could inherit completed/review state or duplicate identities | Define fresh-item metadata, retained-content identity and copy versus move behaviour |
| IDs required on every table cell and paragraph | Stable IDs only for tasks and linked purchase views; editor positions for ordinary content |
| Custom edge controls and deletion interception | Reuse table/list/selection commands and normal keyboard undo; narrow explicit-delete confirmation |
| Migration on current/previous/import reads was underspecified | Pure converter; only active-file migration persists; backup envelope remains version 1 |
| Data work came before resolving the actual typing flow | First milestone is a working continuous editor with in-memory conversion, before storage cutover |

## Constraints and boundaries

- No implementation, dependency installation or live-file migration during this planning request.
- One-person local hobby app: no new framework/service, paid UI, collaboration, patch engine or unrelated CAD changes.
- No tests, test scaffolding, browser automation or delegated reviews. No builds/typechecks/extra verification processes
  under this plan. Source inspection and Gert's manual use provide the evidence; report those limits explicitly.
- Preserve existing uncommitted changes, especially Makefile, cabinet code and CAD documentation. Do not access protected
  environment files; beads access is only through bd if needed. Do not start services or another app/viewer tab.
- Keep CAD mounted and the Plan editor alive across tab switches. Planning/purchase saves never regenerate geometry.
- Important writing actions stay visible and keyboard accessible. No branch/node/child/block terminology in controls.
- Keep existing costs, purchase identities, filtering, review flags, backups and assistant access.

## Files and ownership

| File | Responsibility/change |
| --- | --- |
| `frontend/src/plan-editor.ts` | Single Editor, extension configuration, command API and history |
| `frontend/src/plan-task.ts` (new) | Extend TaskItem presentation and metadata; task move commands |
| `frontend/src/plan-insert.ts` (new) | One toolbar and slash picker invoking shared commands |
| `frontend/src/plan-purchases.ts` (new) | Embed/update/destroy the existing grid as a purchaseView |
| `frontend/src/planner.ts` | Page shell, search/view controls, editor lifecycle, backup/recovery |
| `frontend/src/planning-api.ts` | Document types, serial content/purchase saves, scoped purchase history |
| `frontend/src/purchase-grid.ts` | External filter updates, draft preservation, scoped undo labels |
| `frontend/src/style.css` | Document layout, nested tasks, toolbar, tables, focus and drag indicators |
| `src/campervan/planning.py` | Document v2 validation, atomic persistence and content replacement |
| `src/campervan/planning_migration.py` (new) | Pure v1-to-v2 conversion, legacy models, format dispatch |
| `src/campervan/planning_api.py` | Content route, compatible backup/restore, retirement of tree operations |
| `README.md`, `docs/planner.md` | Writing, storage and assistant API instructions |
| `frontend/package.json`, `frontend/package-lock.json` | Direct declarations of the editor extensions used |

Retain the current `setupPlanner(root, client)`, tabs and materials mounting contracts. Update direct callers only where
client events/history names change. `purchases.py` continues consuming `document.purchases`; its calculations need no
new ownership. Remove old task-tree rendering, per-note editors and structural inverse history at cutover.

## Task 1: Establish the document and an in-memory conversion

**Interfaces:**
- TS `PlanningDocument = {version: 2; revision: number; content: JSONContent; purchases: Record<string, PurchaseRecord>}`.
- Python equivalent uses existing Record/PurchaseRecord/PurchaseFilter.
- `convert_v1(raw: dict[str, Any]) -> dict[str, Any]` in `planning_migration.py`: pure, no filesystem access.
- `validate_document(content: dict[str, Any]) -> None` in `planning.py`.

- [x] Define the supported schema: existing StarterKit text/marks/lists and TableKit types, plus nested taskList/taskItem
  and purchaseView. TaskItem already supports `paragraph block*` with `nested: true`; do not invent another container.
  Its attributes are `id`, `checked`, `collapsed`, `needs_review`; purchaseView has `id` and PurchaseFilter.
- [x] Require unique nonempty IDs on taskItem/purchaseView only. Keep prose/table content free of ID requirements.
  Document those two attribute contracts for TS and Python before implementing either side.
- [x] Adapt the existing rich validator to check supported types, child/list/task/table structure, attribute types,
  safe links, finite dimensions and unique required IDs. Reuse Pydantic for filters and records. Keep validation
  bounded to this schema; do not build an extensible Python clone of ProseMirror. Frontend hydration also runs the
  editor schema's JSON parsing and document check; invalid content fails visibly instead of being silently dropped.
- [x] Move legacy tree models behind the converter. Preserve titles/line breaks, note content in order, BOM views,
  subtask order, flags and purchases. Flatten note documents into task contents without retaining note-wrapper IDs.
  Preserve task IDs and view IDs. If legacy namespaces collide, retain task IDs and deterministically rename view IDs;
  do not fail a valid old file merely because those formerly separate namespaces overlap.
- [x] Convert the existing seed in memory too. An existing empty document gets an empty paragraph, not seeded tasks.
  Repeated conversion of the same source produces the same task/view IDs. Unknown versions/content are rejected.

**Result:** a single document model and usable converted content, with no live file written or migrated yet.

## Task 2: Deliver the continuous writing interaction first

**Interfaces:**
- `createPlanEditor(root, {content, onChange, client}): {editor: Editor; destroy(): void}`.
- `runPlanCommand(editor, command): boolean` is the shared toolbar/slash command entry.
- `mountPlanInsert(root, editor): {destroy(): void}`.

- [x] Declare direct 3.32.0 dependencies on `@tiptap/extension-list` (already transitive),
  `@tiptap/extension-unique-id`, and `@tiptap/suggestion`. Confirm exact-version exports before installation/use.
  StarterKit already supplies normal lists, history, gap cursor and trailing paragraph; register only additional task
  extensions from the list package. Reuse TableKit; no duplicate list kits or a new editor framework.
- [x] Create one Editor with UniqueID scoped to taskItem/purchaseView. Extend TaskItem for collapse/review controls,
  retaining a real `contentDOM`. Use `keepOnSplit: false` for fresh task metadata, and the list split command's attribute
  overrides where needed. The existing content keeps its identity/status when an empty item is inserted before it.
- [x] Implement the design's keyboard table. Keep native Enter/splitListItem, Shift+Enter/hardBreak, sink/lift commands
  and table navigation. Alt/Option+Enter and Add text use splitBlock to add a paragraph within the current item.
  Do not distinguish first-versus-later task paragraphs. At a gap/selected table or purchase view, Add text inserts a
  following paragraph in the same container. At the document end, blank-area click provides a valid insertion point.
- [x] Put task/status defaults, list conversion and paragraph insertion in shared commands. Conversions preserve all
  text/tables/nested content; converting out of a task removes task metadata intentionally and can be undone.
  Empty-item exit applies only when there is no following contained content. Preserve IME and native clipboard input.
- [x] Build the compact toolbar from the design. Pointer actions retain selection without making controls inaccessible
  to keyboard users. Format selection and Add text have distinct actions/labels. Display the Alt/Option+Enter hint.
  Do not expose every command as a permanent button or repeat the toolbar for each task.
- [x] Add the slash picker through Suggestion. Use the same command functions, a bounded local command list and the
  specified trigger/dismissal behaviour. Retain normal URL/code input, keyboard navigation and accessible option state.
- [x] Use TableKit's insert/select/resize/row/column commands. Insert 3×3 with a header row and focus its first cell.
  Show row/column buttons only for an active table. Allow an editable paragraph after a table in its own container.
  Use existing table paste capabilities; do not implement a spreadsheet import subsystem or custom floating edge UI.

**Early UX checkpoint:** expose this same Editor through the existing Plan shell with in-memory converted content
before enabling new storage writes. This is implementation staging, not a second preview app, fake dataset or test
harness. Keep the existing file untouched until persistence is connected. Gert can try task → second line → paragraph
→ table → more text without menus. If visual feedback is unavailable, continue the remaining work while clearly
recording that this checkpoint is unverified; do not invent approval or claim the interaction has passed.

## Task 3: Embed the shared purchasing grid without losing drafts

**Interfaces:**
- `PurchaseView` block-level atom with a vanilla node view in `plan-purchases.ts`.
- `mountPurchaseGrid(...)` adds `setFilter(filter: PurchaseFilter): void` and a non-echoing external-update path.

- [x] Render the view's grid controls under `contenteditable=false`. Apply stopEvent/ignoreMutation only to its input UI;
  retain node selection, drag/drop and keyboard access into/out of the view. A following paragraph must remain reachable.
- [x] Mount once per node-view lifetime; update matching view/filter attributes in place. Destroy subscriptions on actual
  removal. If movement causes the editor to recreate a view, commit its changed valid input first or preserve the draft;
  “one Editor” alone does not guarantee embedded inputs survive node-view replacement.
- [x] Filter selection updates attributes through an editor transaction. setFilter applies undo/reload changes without
  calling onFilter back. If typing a filter, avoid an undo entry per keystroke; commit/debounce it as a user action.
- [x] Preserve the active input value/caret during a purchase refresh and blur a changed cell before editor toolbar,
  export or navigation actions. Keep invalid input and its message visible; do not mark an uncommitted draft Saved.
  Remove/change-filter actions must not silently erase a focused draft. Reuse the current grid's draft preservation.
- [x] Keep records/quantities/totals entirely on the purchase path. Rename public history actions to
  `undoPurchase`/`redoPurchase`, label their buttons Undo purchase/Redo purchase, and leave native input undo alone.
  Copying/removing/restoring a purchaseView only affects the view and filters, never records or actual spending.

**Inspect:** two views show the same purchase once in project totals; undoing a filter/removing a view cannot reverse
buying. Grid focus cannot send Enter/Tab/Delete/Cmd+Z into the surrounding document.

## Task 4: Connect persistence, migration and recovery

**Interfaces:**
- `PUT /api/v1/planning/content`: `{revision: number, content: JSONContent}` → validated PlanningDocument.
- `PlanningStore.replace_content(expected_revision, content) -> PlanningDocument`.
- `PlanningClient.setContent(content): void`; retain `flush()` and purchase mutation interfaces.
- Backup envelope stays `{version: 1, planning: PlanningDocument, project, products}`.

- [x] Make Store reads dispatch by document version. Before replacing an active v1 file, validate conversion, create an
  exclusive exact-byte `planning.v1-backup.json` if absent, then atomically save v2 with revision+1. Never overwrite
  that backup. If it exists, leave it intact and retain the active pre-write contents through normal previous-save
  handling. A failed conversion/backup/write must leave the active source recoverable and produce a visible error.
- [x] Previous-save/import reads convert in memory only. Validate nested v1/v2 planning in envelope version 1, reject
  unknown versions before writes, and retain current CAD/product compatibility checks and rollback. Do not change
  envelope versions unnecessarily. Restore/export/recovery share the same parser/converter; CSV calculations stay intact.
- [x] Content PUT changes only content, validates revision before writing, and uses existing atomic save semantics.
  Purchase operations change only records. Retire old tree operations with a useful 422 reload/version response.
  Old purchases still meet the shared revision guard. Active-file migration invalidates any old browser revision.
- [x] Refactor the existing queue to contain content and purchase requests serially. Debounce content at 450ms and only
  combine adjacent unsent content snapshots. Before enqueueing a purchase, capture any pending content in document
  order; do not lose it in a separate timer or combine across that purchase. An in-flight request is immutable.
- [x] Save acknowledgements advance revision/status without installing old server content over newer typing. Define
  distinct notifications for explicit load/restore, purchase refresh and status; those events never recreate the Editor
  on ordinary saves. Save success requires both no pending content and no pending purchase/draft changes.
- [x] On 409/network/validation failure retain the current draft, stop writes, show Download unsaved edits and explicit
  Reload. Do not silently retry a purchase after an unknown response. Reconcile by reading before any new write.
  Exports flush pending work; tab switch/blur flushes without blocking navigation indefinitely on failure.
- [x] Preserve dirty-page protection and explicit restore confirmation. Reload/restore starts a new history only after
  save/discard has been resolved. Markdown traverses the mixed document in order, representing task state, links,
  multiline text, tables and purchase-view filters. JSON remains the full-fidelity restoration format.

**Inspect:** newer typing survives slow acknowledgements; content saves retain concurrent purchase values; imported
backups do not mutate the active file until Restore; migration backup is not overwritten by subsequent saves.

## Task 5: Finish outline controls and replace the old view

- [x] Replace recursive rendering in planner.ts with the single-editor shell. Keep loading/recovery controls available
  on failure. Remove old title inputs, note-editor factories, task-tree position helpers and structural inverse stacks.
  Wire existing navigation/status consumers to the new notification types; retain mounted CAD and editor dimensions.
- [x] Task controls update attributes using editor transactions. Completion/review changes are undoable; collapse is
  persisted but excluded from history. Move the caret to visible content before collapsing its container. Retain full
  contents in document JSON and ensure hidden controls are absent from keyboard focus order.
- [x] Use one task handle selecting the whole task and the editor's native draggable node/selection/drop support.
  Use native drop indicators and explicit Indent/Outdent for nesting. Provide Move up/down commands as transactions;
  reject descendant/self destinations. Do not port the old HTML task-tree drag system or write another selection engine.
  The official DragHandle package was considered; task node-view handles plus core dragging cover this bounded need
  without another dependency or reliance on newer nested-targeting APIs.
- [x] Add search highlights/next/previous and hide-completed as view state/decorations. Reveal matches/active tasks and
  ancestors temporarily. Keep partially completed parents visible and persisted collapse unchanged. Do not mutate or
  rebuild document content for filtering. Standard Undo remains intact across movement, collapse and tab switches.
- [x] Keep standard editor deletion/selection/clipboard behaviour; confirm scope only for explicit Delete item with
  contained tasks/content. Do not add a global deletion/transaction interception framework. Handle copy versus cut/move
  with UniqueID/editor semantics, not ad hoc ID rewriting in event handlers.
- [x] Apply readable document styling, compact nesting, task guides, table overflow and visible focus/drop states.
  Narrow-window controls remain usable. Replace old branch/node/child wording in controls/errors/help. Keep review and
  unfinished-count functions and visibly Saved/Saving/Error status.

## Task 6: Inspect, document and hand over

- [x] Update README and docs/planner.md for the final keyboard contract, scoped purchase undo, migration backup and
  version-1-envelope/version-2-document distinction. Supersede the old note/menu instructions explicitly.
- [x] Document assistant editing: read current document, find a task/view ID or prose path, edit content, PUT with the
  read revision. Handle 409 by rereading/reconciling; never replay a whole stale plan. Keep purchase examples and explain
  that content PUT does not include purchases. Avoid introducing an extra patch/operation framework.
- [x] Inspect the final diff and the schema/client/API agreement. Run `git diff --check` only; do not run tests, builds,
  typechecks, services or browser automation under this plan. Report unperformed checks and actual errors honestly.
- [x] Hand over the short user walkthrough below in the existing app tab. User visual acceptance cannot be inferred
  from successful source inspection or HTTP responses.

## User walkthrough

1. Click and type prose, then a task. Use Shift+Enter for a second line and Alt/Option+Enter for another paragraph
   without another checkbox. Insert `/table`, fill it, then continue text underneath. Repeat with toolbar insertion.
2. Create a subtask, complete/reopen it, move its containing task, collapse/reopen it and Undo. Text, table, nested
   contents and original status stay attached to the document; no operation resets history.
3. Copy/paste mixed text/tasks/table content, cut/move a task, and split a completed task. Copies have fresh IDs and retain
   copied status; new tasks created by splitting start unchecked. Moved/original tasks retain identity and status.
   Pasted text is independently editable.
4. Insert Purchases, set Squabs filter, record a partial purchase, change its filter and Undo the filter. Compare main
   BOM totals, then remove the view. Purchased quantities/spending remain and are counted once.
5. While text or a purchase cell is active, switch tabs, search and collapse. Return and continue typing without a lost
   draft or invisible caret. Reload after Saved; confirm persistence and try export/restore after keeping a backup.

The primary acceptance criterion is uninterrupted task/text/table writing. If it still feels like assembling separate
form elements, the implementation has missed this plan even if every toolbar button exists.

## Implementation record

Started 25 October 2026 (UTC 24 October 22:41). Working in the existing workspace to preserve the prior planner edits.
Project overrides applied: no tests, delegated reviews, service starts or worktree/commit workflow.
Supporting Tiptap packages installed at 3.32.0. Editor/task work in progress; saved files have not been migrated manually.

Tasks 1–6 implemented in source. No live file was manually migrated or inspected; active-file conversion runs on the
application's next read and retains the exact v1 backup. No tests, builds, typechecks, browser checks or services run.
The early visual checkpoint was unavailable in this session; proceeded with the authorised work and left the user
walkthrough pending. Source inspection and git diff --check are the verification evidence.
Ruling: reuse core draggable task views plus explicit indent/outdent; no extra drag-handle package.
Ruling: retain purchase drafts in the shared client by record/field, so a recreated view can recover them in the BOM.

User correction after implementation: Enter continues paragraphs within a task. Cmd/Ctrl+Shift+Enter creates the next
task. Replaced the wide textual toolbar with grouped familiar formatting/list icons and direct Table/Purchases
insertion. Task actions moved to the item handle. Inspected the existing app tab using read-only Chrome DevTools
DOM/console/screenshot tools; no browser typing/interaction checks or automated tests were run.
