# Conversion plan and purchases

Open **Plan** in the existing app. It is one rich-text document: click and type, mix tasks with paragraphs and tables,
and keep writing beneath them. This replaces the earlier single-line titles and separate notes editors.
The first project starts from [the captured conversion list](conversion-plan.md); existing plans retain their content.

## Writing

There is one list type: numbered items with checkboxes. Numbers reflect nesting (`1`, `1.1`, `1.2`, `1.2.1`, `2`)
and update when items move, nest or are deleted. Hidden/completed items retain their place in the numbering.
There are no task/bullet/numbered type choices. Each item can still contain several paragraphs, tables and purchases.

Use the compact toolbar for paragraph styles, bold/italic/links, new Item, Table and Purchases.
Click a link in the document to open its destination in a new tab. Use the Link action or Cmd/Ctrl+K to edit its address.
Open **Actions**, right-click the writing surface, or click an item's dotted handle for a contextual menu with action
names and their Mac/Windows shortcut labels. **Shift+F10** opens it from the keyboard. Arrows, Home/End and typing a
name navigate; Enter/Space runs an action; Escape returns focus; Tab leaves the menu. Unavailable actions are dimmed.
**Keyboard shortcuts** in the menu opens the full reference. Shift+right-click retains the browser's normal menu;
purchase inputs keep their native menus. Clipboard access from Paste can require browser permission; keyboard paste
continues to work normally. Drag the dotted handle to move the entire item.
Important writing actions are available directly. **File**, at the left of the sticky formatting toolbar, contains
reload, exports and restoration. Its grouped menu closes after an action, on Escape or on an outside click. Enter/Space
opens it, Up/Down selects an item, Home/End jumps to an end, and typing finds an action. Tab leaves the menu.

| Action | Behaviour |
| --- | --- |
| Enter in prose | Another paragraph |
| Enter in a task | Another paragraph in the same task; no extra checkbox |
| Cmd/Ctrl+Shift+Enter | New task after the current task |
| Shift+Enter | Another line in the same paragraph, without another checkbox |
| Alt/Option+Enter or `/text` | Another paragraph within the same task/container |
| Enter in an empty final list item | Leave/outdent the list and continue writing |
| Tab / Shift+Tab in a list | Indent/outdent |
| Tab / Shift+Tab in a table | Next/previous cell; Tab from the final cell adds a row |
| Cmd/Ctrl+Z and redo | Undo/redo document writing, tables, completion and movement |
| Alt/Option+Up / Down | Move the current task up/down |

Type `/` at a fresh line or after a space for insertion commands: `/text`, `/task`, `/heading`, `/table`, `/purchases`.
Choose with arrows, then Tab or Enter to insert the highlighted item. The picker shows these keys in its footer.
Tab accepts only while a matching item is highlighted; otherwise normal Tab behaviour applies. Shift+Tab is unchanged.
Escape dismisses the picker and leaves your typed text intact.
Use the toolbar if you prefer the mouse; shortcuts are optional.

A **Table** starts with three rows and columns, including a header. Click a cell and type. Use the row/column controls
that appear while editing a table to resize it; drag a column boundary to change its width. Arrow navigation and
the arrow keys let you continue writing after the table. Paste supported formatted text or HTML tables into the document.

Tasks show a checkbox and, when they contain more text or subtasks, an expand/collapse arrow. Completing a task changes
only that task. Its unfinished count makes outstanding subtasks visible. Drag the dotted handle to move a whole task;
use Indent/Outdent for nesting. Click its dotted handle for moving, marking Needs review and deleting an item with its contents.
Copies get new IDs but retain copied status; new items start unchecked. Undo restores deleted content.

Search highlights matches; Previous/Next match visits them and reveals collapsed matching content temporarily.
Hide completed retains parents that still contain unfinished subtasks. These actions and switching tabs keep the
editor's current session history; explicit reload/restore starts a new history.

## Purchases

**Purchases** inserts the same editable grid used by **Bill of materials**. Filter it by category/tag/supplier/status
or text. For squabs, choose a Squabs category or tag; adding an item there prefills that filter's category/tag/supplier.
All views reference the same records. Copying or removing a view never duplicates/deletes stock or actual spending.
Ordinary document tables do not affect costs.

| Field | Meaning |
| --- | --- |
| Required | Total purchase units needed; blank uses CAD counts where known |
| Owned | Units already on hand before this project |
| Bought | Total purchased so far; edit for partial purchases/corrections |
| Estimated unit price | Estimate per displayed purchase unit, including GST |
| Actual spent | Total actually paid so far for this item |
| Remaining | Required minus owned minus bought, minimum zero |

**Bought** records the outstanding quantity, or asks for the total bought when the requirement is unknown.
It does not guess actual spending: enter that separately. Quantity/cost cells commit when you leave them; correct
invalid input before exporting. Unsaved purchase drafts are retained during refresh and can also be recovered in the BOM.
Use **Undo purchase / Redo purchase** for committed purchase records. A focused input has normal text undo.
Document Undo covers the view/filter, not the stock purchases.

Remaining estimate is remaining quantity × unit price. Combined is actual spent plus remaining estimate. Unknown
quantities/prices/actual costs are labelled incomplete; zero is valid. Currency is NZD. Add delivery as its own item.
Changing a unit label does not convert quantities. Each shared product contributes once to whole-project totals.

CAD stock is grouped by product. Hardware uses pack counts; sheets/timber need a cutting layout before purchase
quantities are known. Existing owned flags exclude supplied uses from automatic need and are labelled. Required can
override calculated need. Saved purchases of a product no longer selected in CAD remain as Unused stock with actual
spending retained. CAD source specifications/cut lists remain under **CAD stock and cutting details** in the BOM.

## Saving, conversion and recovery

Changes autosave. Check **Saved locally** before closing. Neither writing nor recording a purchase regenerates CAD.
The new planning document has version 2; the full backup envelope remains version 1 because its fields are unchanged.

- `.local/planning.json`: rich document, revision and purchase records.
- `.local/planning.previous.json`: document before the latest successful write.
- `.local/planning.v1-backup.json`: untouched original saved before the first old-format conversion.
- `.local/project.json`: existing CAD parameters and material selections.

Old plans convert on load, retaining task IDs, text, tables, statuses, subtasks, purchase filters and records. Existing
empty plans stay empty. Former bullet/numbered lists become unchecked numbered items, preserving their contents and
nesting; an active-file conversion retains the original in Previous save and advances the revision.
Invalid/unknown content produces an error and retains the source, rather than resetting it.
A tab left open before the update must reload before editing.

**File → Download full backup (.json)** downloads the full document, purchases, CAD selections and product snapshots.
**Import backup…** accepts old/new planning formats after confirmation and reloads the page. It validates product compatibility
before writing and regenerates CAD only if restored geometry inputs change. **Restore previous save…** restores the preceding
planning save with current CAD settings; it is one write back, not a session history.
**File → Reload saved plan** loads changes made by the assistant or another tab, confirming before discarding unsaved edits.

**Export notes** gives Markdown with item numbers and checkboxes; **Export purchases** gives CSV. JSON is the complete
restorable backup. Keep a JSON
backup before large revisions. Reading an old backup/previous-save candidate converts in memory until you choose Restore.

If the assistant or another tab changes the plan, a stale save stops with an error. Your draft remains visible.
Download unsaved edits before Reload if needed. That draft download is a planning document for reconciliation, not a
full backup bundle. Do not edit files behind the running app.

## Assistant editing

Development API: `http://127.0.0.1:8000/api/v1`. Read `/planning`, edit its `content`, and send only content plus the
revision to `PUT /planning/content`. Task and purchaseView IDs are stable. Ordinary prose/tables are addressed through
their containing task and document path. On HTTP 409 reread and reconcile; never blindly replay a stale document.

```json
{
  "revision": 12,
  "content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Example"}]}]}
}
```

This example replaces the whole writing document with one paragraph; construct the body from the current content to
preserve other writing. Store your intended body in a file and send it without shell interpolation:

```sh
curl -s http://127.0.0.1:8000/api/v1/planning
curl -s -X PUT http://127.0.0.1:8000/api/v1/planning/content \
  -H 'Content-Type: application/json' --data-binary @/tmp/planning-content.json
curl -s 'http://127.0.0.1:8000/api/v1/purchases?category=Squabs'
```

Content PUT preserves purchases. Purchase mutations retain `POST /planning/operations` with the current revision and
an operation `{kind: "purchase", id, values: <complete record>}`. Start from `/purchases`' projected record to preserve
identity/defaults. Manual IDs are `manual-<unique ID>`; stock uses `product-<catalogue ID>` or `custom-<role ID>`.
`delete_purchase` removes manual records; `reset_purchase` removes saved overrides while retaining generated CAD need.
The old add/update/move/delete task-tree operations are retired. Use `/docs` for current request schemas.

Exports use `/planning/export?format=json|markdown|csv`; Restore posts `{revision, backup}` to `/planning/restore`.

## First visual check

Type a task, add a second line, add a paragraph, insert a table, then continue writing. Complete/reopen/move/collapse
it and Undo. Add a filtered Purchases view and record a partial purchase; check the same record in the BOM. Reload
after Saved locally to check persistence. No tests, builds, typechecks or browser interaction checks were run;
Gert's use of the existing app tab is the visual acceptance check.
