# Conversion planner

Status: approved by Gert in chat. No application changes implemented.

## Purpose and agreed approach

Help Gert carry out a one-person campervan conversion in small, concrete steps, while freely changing the design,
materials and order of work. Preserve instructions, sources, measurements, contacts, quotes and decisions with the work.
The initial inventory is in `docs/conversion-plan.md`.

We considered a nested list alone, a spreadsheet-style grid alone, and a linked combination. Gert selected the
combination: nested tasks with rich editing and inline tables, plus improvements to the existing BOM. Lists handle
instructions and sequence; grids handle quantities, sourcing and costs. Inline BOM tables reference the same items
as the BOM tab. Ordinary tables remain available for measurements, comparisons and contacts.

There are no deadlines, team roles, cash-flow forecasts, accounts, cloud services or general spreadsheet formulas.

## Plan tab

Each item has a stable identity, editable title, completion state, rich content and ordered child items. Its content
can contain paragraphs, headings, bold/italic text, links, numbered instructions, ordinary tables and linked BOM views.
Notes and tables appear directly beneath the item in the outline; editing does not require navigating to another page.

- Click a title to edit. Enter creates a sibling; provide an explicit add-child action.
- Tab/Shift-Tab in an item title indent/outdent it; inside rich text and tables, editor shortcuts retain their meaning.
- Drag a handle to move an item, with a visible before/after/inside drop target. Move its entire subtree with it.
- Also provide move up/down and indent/outdent actions so dragging is not the only method.
- Collapse/expand individual branches and remember their state. Collapsing never completes or deletes work.
- Check/uncheck any task. Proposed default: a parent checkbox changes only that item, with unfinished-child counts
  visible; it does not silently mark every descendant complete. Show/hide completed work without deleting it.
- Add/delete ordinary table rows and columns in place. These tables contain editable text, not arbitrary formulas.
- Search titles and notes, revealing matching items with their parent context.
- Delete a branch through an explicit action showing that children will also be removed. Provide Undo for deletion,
  moves and completion, plus the editor's text undo/redo. Never delete a nonempty subtree through an accidental Backspace.
- Mark an item as needing review manually when a measurement, material or decision changes. Keep a short reason in
  its notes. Automatic CAD-to-task dependency tracking is outside the initial scope.

Seed the plan once from the captured inventory, retaining its structure and optional drawer. Do not reseed on reload
or recreate items the user deleted. The Markdown file then remains the initial reference, not a competing live plan.
Refining the actual conversion instructions and researching vendors remains ongoing work in the planner.

## BOM and purchase tracking

Extend the existing BOM instead of introducing another catalogue. Keep CAD material roles, selected products and
generated cut information. Add manually entered purchases for fabric, tools, consumables, finishing and services.

Each purchasing item has a stable ID, name, category, tags, supplier/product link, notes, purchase unit, quantity needed,
quantity already owned, quantity bought, estimated unit price and actual amount spent. Unknown values are blank,
not zero. Quantities are in the displayed purchasing unit: sheets, packs, lengths, metres, bottles or a service job.
Existing CAD piece counts and cutting dimensions remain separate from purchase quantities.

- Categories and tags are editable. Filter by category, tag, supplier, purchase status and text.
- Status is not bought, partly bought or bought, derived from quantities. Already owned remains distinct from bought.
- A quick Bought action records the outstanding known quantity; the user can correct it or record a partial purchase.
  If required quantity is unknown, request the quantity bought rather than pretending all requirements are satisfied.
- Actual spending is entered explicitly and can be corrected; marking Bought does not fabricate an actual price.
- Remaining quantity = max(required - already owned - bought, 0).
- Estimated remaining cost = remaining quantity × estimated unit price.
- Show actual spending, estimated remaining cost and their combined forecast. Label incomplete totals and report how
  many items have unknown quantities/prices. Actual spending also remains incomplete when bought items have no cost.
- Show filtered totals distinctly from whole-project totals. Use NZD including GST; record delivery as a separate item
  when applicable. No automatic currency conversion or accounting system.

Shared stock is purchased once: a selected product used by several CAD roles has one purchasing item with multiple
uses/tags. Filtering by one use shows that stock item's whole cost, labelled as shared; category subtotals must not be
added together as though they were exclusive allocations. Sheet and timber purchase counts require the cutting layout,
as they do today; do not derive sheet purchases just by dividing total cut area by sheet area.

Changing selected stock does not transfer purchase history to the replacement product. Keep purchased old stock visible
as unused stock, and show the new requirement separately. CAD-generated requirements cannot be erased by deleting a
shopping row: change the design/selection or mark the requirement already supplied. Manual rows can be deleted, with
Undo and a warning if they have recorded spending.

## Inline BOM tables

Insert a BOM view under any plan item and choose its filters (for example, tag = squabs). Store only the filter and
display settings, not copies of rows. Use the same editable grid component in the Plan and BOM tabs.

Changes to quantity, price, tags or purchases update the shared record and every view. Removing the embedded table
removes only that view, not its purchases. Editing a tag can move an item out of a filtered view; explain this visibly.
An Add action from a tag/category-filtered view pre-fills those values. Unknowns and shared-stock totals behave exactly
as they do in the BOM tab. Ordinary tables are clearly labelled differently and do not contribute to BOM totals.

## Saving and assistant access

Proposed implementation: a local planning JSON file next to the existing project JSON stores the outline and purchase
metadata, referencing existing product/role IDs. The existing catalogue and project selections stay authoritative for
CAD dimensions. Planning edits must not trigger CAD regeneration, nor be overwritten by parameter saves.

Expose read and edit operations through the existing local FastAPI app, so both the UI and assistant use the same
validation and IDs. Support fetching the plan, updating a node, moving it, and reading/updating purchase records.
Document the API with examples so the assistant can query incomplete steps, filter supplies and update agreed details.
Do not edit the underlying JSON behind the running app.

Autosave with visible Saving/Saved/Error status. Save using the existing temporary-file-and-replace convention.
Serialize browser saves and use a simple document revision check to reject stale writes rather than silently overwriting
an assistant edit. On conflict preserve the unsaved text and offer reload/copy; no real-time collaboration framework.

Provide a downloadable JSON backup and validated restore, warning before replacing existing data. Backup must include
the plan, purchases and the material selections needed to resolve their references. Offer a readable Markdown export
of the outline and CSV export of purchases. Keep one previous successful local save as recovery from accidental edits.

## Fit with the current app and implementation choices

Observed: `frontend/src/materials.ts` owns the current CAD/BOM tab switching and grouped-stock UI. `materials.py`
owns the catalogue, roles and selections. `coordinator.py` recreates and saves the CAD Project when parameters change.
Consequently, adding arbitrary planner fields to that object without updating its save path would lose them.

Keep the current TypeScript/Vite frontend and FastAPI backend. Add Plan to the existing navigation and keep the CAD
viewer mounted, preserving the current camera/WebSocket behaviour. Reuse the BOM stock grouping and material-selection
path; selection changes affecting geometry continue to use the existing parameter validation/regeneration flow.

Proposed dependency: Tiptap's open-source editor core with basic formatting, links and tables, integrated in vanilla
TypeScript. It supplies rich-text editing and structured JSON without introducing React or a hosted service.
Use an explicit task tree around rich-content editors, rather than a second task list buried in editor content.
Implement task-tree movement once; editor content owns text/table editing. Use a normal editable HTML table for the
BOM with fixed calculations, rather than a spreadsheet engine. The exact editor package versions and minimal extension
set are implementation details to verify before installation. This new editor dependency is part of the proposal.

Sources checked:
- https://workflowy.com/help/bullets — nested items with notes and children.
- https://tiptap.dev/docs/editor/getting-started/install/vanilla-javascript — integration without a UI framework.
- https://tiptap.dev/docs/editor/extensions/nodes/table — ordinary editable tables.
- https://tiptap.dev/docs/editor/core-concepts/persistence — structured JSON persistence.

## Completion and verification

Implementation must include both the outline and linked BOM functionality, initial task content, persistent edits,
purchase calculations, assistant-facing operations, export/restore and practical README instructions.
Use Gert's manual interaction to assess editing, dragging, nesting, undo, filtered views and purchases. Do not create
or run tests, browser interaction checks or delegated review passes. Do not start services. Follow repository rules.

Useful manual examples: edit squab instructions; move a child task; complete and reopen it; insert a contact table;
show squab purchases inline; record half a purchase; change the estimated price without altering actual spending;
confirm a shared plywood purchase is counted once; reload and confirm persistence; restore an exported backup.

This document records the proposed behaviour. Approval precedes an implementation plan and application edits.
