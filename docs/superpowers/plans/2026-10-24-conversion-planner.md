# Conversion Planner Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task locally.
> Repository instructions override skill defaults: no tests, delegated reviews or service starts.

**Goal:** Add an editable conversion outline and shared purchasing records to the existing local CAD application.

**Architecture:** Keep the CAD project and material catalogue authoritative for geometry. A separate local planning
document holds tasks, rich content and purchasing metadata. One purchase grid serves the BOM tab and filtered inline
views; all mutations go through the existing FastAPI application.

**Tech Stack:** Python 3.13 through uv, FastAPI/Pydantic, vanilla TypeScript/Vite, Tiptap open-source editor extensions.

**Spec:** `docs/superpowers/specs/2026-10-24-conversion-planner-design.md` (approved).

## Global constraints

- One-person, local-only hobby project. No accounts, team workflows, deadlines or spreadsheet formula engine.
- Do not create or run tests, browser interaction checks or delegated review passes. Do not start services.
- Preserve existing Makefile, cabinet and CAD-documentation edits. Do not access protected environment files or beads.
- Keep CAD mounted when changing tabs. Purchase and outline edits do not trigger geometry regeneration.
- Unknown prices and quantities remain unknown. Existing bought stock retains its identity when CAD selections change.
- Use the recorded conversion TODO inventory as initial content; do not invent prices, contacts or construction advice.

## Review focus

These are implementation and user-inspection concerns, not a request to create automated tests.

- Stale browser saves after assistant edits must preserve unsaved text and reject overwrites (tasks 1, 3).
- Shared sheet stock shown in several inline views must count once in project totals (tasks 2, 4).
- Changing stock or reducing requirements must retain previous purchases and actual spending (task 2).
- Moving/deleting a collapsed branch must retain descendants or allow recovery (task 3).
- Reload/export/restore must preserve rich text, table content, references and purchase history (tasks 1, 5).

## Files and ownership

| File | Responsibility |
| --- | --- |
| `src/campervan/planning.py` (new) | Models, seed content, revision-checked atomic persistence and outline operations |
| `src/campervan/purchases.py` (new) | Purchasing projection, grouping, status and totals |
| `src/campervan/planning_api.py` (new) | Planner/purchase/export/restore routes using the existing app |
| `src/campervan/api.py` | Register routes and initialize the local planning store |
| `src/campervan/materials.py`, `coordinator.py` | Reuse material identities; bounded restore integration only |
| `frontend/src/planning-api.ts` (new) | Shared planner types and HTTP operations |
| `frontend/src/planner.ts`, `plan-editor.ts` (new) | Task outline interactions and rich content editing |
| `frontend/src/purchase-grid.ts` (new) | Reusable filtered purchasing grid |
| `frontend/src/tabs.ts` (new) | Extract current navigation so Plan and BOM share it |
| `frontend/src/materials.ts` | Retain CAD stock controls/cut details and embed purchasing grid |
| `frontend/src/main.ts`, `frontend/index.html`, `frontend/src/style.css` | Mount and style new views |
| `frontend/package.json`, `frontend/package-lock.json` | Minimal pinned editor dependencies |
| `README.md`, `docs/planner.md` (new) | Practical usage, backup and assistant API examples |

## Task 1: Persist tasks and expose editing operations

**Interfaces:** `PlanningStore(path: Path)`, `read() -> PlanningDocument`,
`apply(expected_revision: int, operation: PlanningOperation) -> PlanningDocument`.
`PlanningDocument` holds schema version, revision, ordered root IDs, nodes and purchase metadata.
`PlanNode` holds ID, title, completed, needs-review, collapsed, ordered child IDs and content blocks.
Content blocks are rich-text JSON documents or BOM-view filters with their own stable IDs.

- [x] Define Pydantic models with unique IDs, existing-reference checks, one parent per node and no cycles.
- [x] Implement create/update/move/delete node operations. Move uses destination parent and sibling index; deleting
  removes a whole subtree. Represent ordinary tables inside rich-text JSON, not as task children.
- [x] Seed from the full captured TODO list in `docs/conversion-plan.md` only when the store is absent. Ship explicit
  initial content with the application so installed packages do not depend on the repository docs directory.
- [x] Store at the project file's sibling `planning.json`. Reuse atomic temporary-file replacement, retaining a previous
  successful save. Invalid stored JSON produces a visible error, never silent replacement with defaults.
- [x] Add `GET /api/v1/planning` and `POST /api/v1/planning/operations`; each mutation carries expected revision.
  Reject stale mutations with HTTP 409 and invalid operations with 422. Save successfully before reporting success.
- [x] Extend operations with purchase upsert/delete so all planner mutations share revision and persistence semantics.

**Inspection outcome:** The original CAD save path cannot erase planning content. Empty existing plans stay empty.

## Task 2: Extend BOM records and cost calculations

**Interfaces:** `purchase_view(document, material_data) -> PurchaseView` returns rows and totals;
`PurchaseRecord` contains ID, product/role reference or manual identity, category, tags, supplier, URL, notes,
sale unit, required quantity, owned quantity, bought quantity, estimated unit price and actual total spent.
`GET /api/v1/purchases` returns that projection; updates use Task 1's operations.

- [x] Reuse existing product-based stock grouping. Use one record per selected product, custom role or manual purchase;
  show all associated CAD uses. Never create a purchase record per inline table or per role sharing the same product.
- [x] Keep CAD counts/cuts read-only; explicit purchase quantity overrides inferred pack counts. Sheet/timber purchase
  quantity remains unknown until entered. Preserve existing owned flags and quantities during migration without
  fabricating measured inventory; label legacy fully-supplied uses until the user supplies a precise count.
- [x] Add editable category/tags and manual items for fabric, tools, consumables and services. Retain old records when
  selected stock changes; show purchased but no-longer-required items as unused stock, including their actual costs.
- [x] Calculate remaining quantity and remaining estimate using the approved formulas. Use decimal money arithmetic;
  return null for unknown amounts and explicit incomplete counts. Zero is a valid amount, including free items.
- [x] Compute status from quantities; Bought records outstanding quantity only when required quantity is known.
  Bought never inserts an actual cost. Corrections and partial quantities remain editable.
- [x] Return filtered and whole-project totals, deduplicating IDs. Label shared stock rather than inventing allocations.
  Include delivery as explicit manual rows. Keep stock-selection changes on the existing CAD mutation route.

**Inspection outcome:** Buying two of three known units leaves one outstanding; changing estimated unit price leaves
actual spending untouched. Two tasks showing the same sheet purchase do not double the whole-project total.

## Task 3: Build the outline and rich editor

**Interfaces:** `setupPlanner(root: HTMLElement, client: PlanningClient): PlannerView`;
`createPlanEditor(root, content, onChange): { destroy(): void }`.
`PlanningClient` exposes `read`, `mutate` and `subscribe`, and serializes saves with the latest server revision.

- [x] Install the smallest compatible Tiptap core, starter formatting, link and table extensions; verify current official
  package instructions. No framework conversion, hosted features or experimental Markdown dependency.
- [x] Implement client state with visible Saving/Saved/Error. Debounce typing, serialize mutations and retain edits on
  failures. On 409 stop automatic writes, offer copy/reload, and never overwrite external edits through Undo.
- [x] Build editable titles, ordered children, collapse/expand, complete/uncomplete, unfinished-child counts, add/remove,
  search with ancestor context, and manual needs-review indicators. Parent completion changes only the parent.
- [x] Implement drag handles with explicit before/after/inside targets and cycle prevention. Include menu and keyboard
  alternatives; Enter/Tab/Shift-Tab title behaviour must not intercept table or rich-text editor keys.
- [x] Embed editor content directly beneath nodes: formatting, links, headings, numbered instructions and ordinary tables
  with insert/delete row/column controls. Allow only supported content and safe links when rendering imported content.
- [x] Add session Undo/Redo for structural and completion operations; use inverse operations at the current revision,
  not old whole-document snapshots. Keep text undo scoped to the active editor. Confirm branch deletion scope.

**Inspection outcome:** Editing does not replace focused DOM on every keystroke; moving a branch carries its notes,
tables and descendants; reopening completed work is straightforward.

## Task 4: Connect tabs and inline purchasing views

**Interfaces:** `mountPurchaseGrid(root, client, filter): { refresh(): void; destroy(): void }`;
`setupTabs()` routes `/cad`, `/bom`, `/bom/:role` and `/plan` while keeping CAD mounted.

- [x] Extract the existing tab switch from `materials.ts`; preserve role links, browser history and viewer dimensions.
- [x] Add Plan navigation and initialize the planner alongside existing materials controls.
- [x] Build the shared editable purchase grid with category/tag/supplier/status/text filters, quantity/cost fields,
  purchase action, partial purchase editing and filtered/project totals. Show unknown and shared-stock notices.
- [x] Mount this grid in the BOM tab without duplicating old price/quantity editors; retain stock selection, measured
  dimensions and cut details. Keep IDs stable across rerenders and refresh changes through the shared client.
- [x] Add insert/remove/configure inline BOM-view blocks. Filter changes alter only the view. Creating an item from
  a category/tag filter pre-fills it; explain when editing an item moves it outside the current filter.
- [x] Clearly distinguish ordinary tables from purchasing views; only purchasing records enter cost totals.

**Inspection outcome:** Recording a purchase inline updates the main BOM and other views, without regenerating CAD.

## Task 5: Backup, restore, exports and handoff

**Interfaces:** `GET /api/v1/planning/export?format=json|markdown|csv`;
`POST /api/v1/planning/restore` accepts a validated backup with expected current revision.

- [x] Export a versioned JSON bundle containing planning records, CAD project selections/parameters and referenced
  catalogue product snapshots. Export outline Markdown and purchase CSV with proper escaping and units.
- [x] Validate the complete restore before any writes, including supported editor nodes and product references. Resolve
  referenced products against the current catalogue; reject incompatible/missing definitions with a useful message
  rather than silently substituting materials. Keep snapshots in exports for readable independent recovery.
- [x] Restore through one backend operation with saved previous versions and rollback if either file write fails.
  Update live coordinator state only after successful persistence; regenerate CAD if restored geometry inputs differ.
  Give the restored planning document a fresh revision to invalidate stale browser state.
- [x] Add download/restore controls, explicit overwrite confirmation and previous-save recovery. Protect dirty edits
  when navigating away or restoring. Preserve all purchased unused stock and inline view filters.
- [x] Document plan editing, totals, product changes, backup/restore and assistant curl examples with revision handling
  in `docs/planner.md`; link from README. State that the original TODO Markdown is an initial snapshot.
- [x] Inspect the final diff for scope and accidental changes. Do not run automated tests or additional verification
  processes; hand Gert the short manual walkthrough from the approved design using services Gert has started.

## Execution and completion

Implement locally in this session; no delegated review or browser automation. Track task completion in this file.
Do not claim visual acceptance before Gert tries the interface. Report actual changes and verification limits.
No research into all vendors, sewing groups or construction techniques is implied by building the planner: those
remain recorded conversion tasks to refine together in the new UI.

Implementation completed on 24 October 2026. Inspected the affected sources and diff; `git diff --check` passed.
No tests, builds, typechecks, browser checks or services were run. Visual acceptance remains with Gert.
