# Scan library and compact controls implementation plan

> **For implementation:** Use `superpowers:executing-plans`. Do not create/run tests, start services, open browser tabs,
> delegate review passes or commit unrelated changes. Those repository instructions override generic skill workflows.
> Implementation authorised by Gert on 9 November 2026. See the execution record below for verification limits.

**Goal:** Make the result selector a curated working list, provide explicit scan management, and replace the generic
ellipsis menu with separate measurement-tool and saved-measurement controls.

**Architecture:** Keep discovery and asset serving unchanged in responsibility. A small project-adjacent library file
stores display names, capture groups, archive state and a default. The existing scan list merges discovery with that
data. A native HTML dialog styled as a side panel manages the library without resizing the canvas. The measurement
controller retains its established interaction and saved-constraint document.

**Stack:** Existing Python/FastAPI/Pydantic and TypeScript/Three.js/HTML/CSS. No new dependencies or settings.

**Spec:** Option 1 selected in the preceding UX discussion; current [photogrammetry workflow](../../photogrammetry.md)
and [measurement interaction](2026-11-08-tag-measurements.md). This plan supersedes the latter's generic Scan actions
ellipsis menu; the corrected overlay and keyboard-capture behaviour remain requirements.

## Scope and current evidence

- `scans.completed_scans()` discovers published `run.json` files and projects a limited metadata list. The current
  `GET /api/v1/scans` prepends loose PLY previews. Neither has saved library preferences.
- `scan.ts` currently lists every discovered item, selecting by array index and sorting completed runs before previews.
  `name` is also used in preview asset URLs. Renaming that field would break preview loading.
- Completed runs already have stable directory IDs used by assets and measurement `source_run_id`. These must not change.
- Existing manifests contain input paths/hashes, settings, pose provenance, creation time, frame/triangle counts and
  available layers. Expose those existing facts; do not invent provenance or imply resolution establishes accuracy.
- `scan-measure.ts` owns the tape button, generic ellipsis/menu, measurement dialog, capture-phase shortcuts and status
  overlay. Its saved Measurements dialog can already open independently of measurement mode.
- The native renderer rebuilds its toolbar during scene changes. Current `measure.attach()` reattaches owned controls.
- Measurement data is stored beside `project.json` as `scan-measurements.json`; the app supplies the path. Follow that
  convention for library preferences. No environment variable or project-specific path inside reusable storage code.
- Existing measurement/planner saves demonstrate a local revision check and sibling temporary-file replacement.
  Adapt this simple convention; do not redesign shared storage ownership or introduce a database/framework.
- Preserve unrelated working-tree changes. No processing, retexturing, original-database edits or GTSAM work.

## Product decisions

### Quick selection and management

1. Rename the existing **Scan** selector label to **Result**. Show only active, available entries, using their display
   names. Use native optgroups when multiple capture groups exist; do not add another capture selector for one group.
2. Add a visible **Manage scans…** button beside it. The manager opens as a modal side panel over the existing viewport,
   with a visible Close button and normal Escape/focus restoration. No new browser/viewer connection or canvas resizing.
3. The manager has search, **Active / Archived / All** filters, capture-group headings and rows with explicit actions:
   **View**, **Rename**, **Set default**, **Archive** or **Restore**. Row details expand independently.
4. Details show original result identifier/preview filename, input filenames, merge/pose source, resolution, frame and
   triangle counts, available layers and creation time when recorded. Label missing information Unknown/Unavailable.
   Explain that preview files have only a point cloud. Do not walk entire output directories to calculate sizes.
5. Display names are editable metadata, not filesystem renames. Permit duplicate names, but disambiguate with group
   and the original identifier in details. Render names as text, never HTML.
6. Capture groups are user-managed labels for source capture sets. They are independent of tag-layout IDs and reference
   frames. A tag layout can span many capture sessions; merging/reprocessing the same captures can produce many results.
   Provide **New capture group**, group renaming and **Move to group**. No folder browser or draggable hierarchy.
7. Archive hides a result from the quick selector. Restore returns it. Neither action moves, edits or deletes any
   geometry, manifest, original capture, alignment or measurement. Permanent deletion/disk cleanup is out of scope.
8. Setting a default applies on next initial view load; it does not force a switch immediately. A refresh preserves
   the current active result and layer. Otherwise choose the available active default, then first active result in
   group/name order. No silent fallback to archived results.
9. Archiving the default clears the default. Archiving the displayed result cancels its draft measurement and selects
   the fallback above. If none remains, clear displayed geometry/tags and disable result-dependent controls; show
   **No active results — open Manage scans to restore one.** The manager remains usable.
10. A newly discovered result starts active with its original name in **Ungrouped**, until the user organises it. This
    is a predictable default, not automatic classification by filename/date or assumptions about accuracy.

### Initial curation, kept in data

Seed the project library with one group named **Interior trial**, with these explicit data entries:

| Existing identifier | Display name | State |
| --- | --- | --- |
| `van-10mm` | Existing merge — 10 mm | Active, default |
| `van-5mm` | Existing merge — 5 mm | Active |
| `van-raw-10mm` | Reprocessed merge — 10 mm | Active |
| `van-quick-baked` | Quick baked experiment | Archived |
| `van-trial-10mm` | Dense 10 mm experiment | Archived |
| `van-interior-preview_cloud.ply` | Original point-cloud preview | Archived |

This preserves the current default and the useful comparison pair while removing experiments from everyday selection.
It does not choose an accuracy winner. These identifiers/names belong only in the data file, never library logic.

### Measurement controls

- Keep one **Measure tags** tape icon, pressed state and **T** tooltip/shortcut.
- Replace the adjacent `…` with a visible, labelled **Measurements** button opening the existing saved-constraint list.
  It works while the tape tool is off; it does not activate the tool or discard a draft merely by opening the list.
- Remove the generic Scan actions dropdown and its canvas-context-menu/Shift-F10 entry points. Do not retain a second
  hidden route to that same menu. Leave the renderer's other native behaviour alone.
- Remove the duplicate Measurements button from the bottom status overlay. The overlay contains the prompt,
  scan/reference distance, entry field, validation and one contextual Escape action:
  **Restore** for dirty text; **Cancel pair** for a clean pending/selected pair; **Done** at the first-tag prompt.
  Show **Esc** beside that action. Its click and Escape execute the same current command.
- Share local command definitions between toolbar buttons, tooltips, contextual button and keyboard handlers. Retain
  the existing capture-phase priority over native transparency/stop/numeric-view shortcuts, including repeat guards.
  Preserve editable fields, menus, IME, Enter-save, type-to-replace and normal camera navigation.
- Keep the bottom bar an overlay. Neither activation, prompt length, validation nor opening management changes canvas
  dimensions. No new global command registry or general toolbar framework is needed for these few controls.

## Data and contracts

Create `scan-library.json` beside the application's project file. `build_app` supplies that path to a dedicated
`ScanLibraryStore`; offline processing need not know it exists. Keep the library separate from `run.json` manifests,
the tag alignment definition and `scan-measurements.json`.

Version-1 document:

- `version: 1`, nonnegative integer `revision`, nullable `default_key`.
- `groups`: mapping stable group IDs to nonblank display names.
- `entries`: mapping stable result keys to `{display_name: string | null, group_id: string | null, archived: boolean}`.
- Stable keys are `run:<run_id>` and `preview:<filename>`. A key is metadata identity, never a filesystem path.
- Validate trimmed names (1–120 characters when present), known group references and that a configured default is not
  archived. Deleting a group is not needed; moving entries and renaming groups suffice.
- A missing file reads as an empty revision-zero document, written only on the first change. An invalid existing file
  is a visible error; never silently replace it. The project's seeded document is created during implementation.
- Preserve entries for missing/unavailable assets. Show them as Unavailable in the manager, with View/Set default
  disabled; they are excluded from the quick selector. Do not erase preferences merely because discovery skipped one.
- Store updates use a short local lock, expected revision, validated document and atomic sibling-file replacement.
  No optimistic archive/rename success in the UI before persistence succeeds.

API:

- Preserve `GET /api/v1/scans` as an array and retain existing `id`, `name`, `layers`, tag/layout/alignment fields.
  Add `key`, `display_name`, `group_id`, `group_name`, `archived`, `is_default` and the compact provenance/settings
  fields required by details. Return active and archived discoveries; clients decide which view to show.
  `name` stays the original manifest name or preview filename so existing asset addressing remains valid.
- `GET /api/v1/scans/library` returns the library document, including preferences for unavailable items.
- `PUT /api/v1/scans/library` accepts the complete candidate document with its expected revision and returns the
  saved document with incremented revision. A handful of rows does not need a generic operation protocol.
- Reject stale revisions with 409 and invalid documents with 422. Report I/O failures plainly. A failed save leaves
  the existing selector/scene/default unchanged and the edit available for correction. After 409, reload preferences
  and require an explicit retry; do not replay an archive/default operation automatically.
- Register literal library routes before `/api/v1/scans/{filename}`. Continue enforcing existing asset containment.
  Archiving is a UI preference, not an access restriction: historical asset links and measurement provenance still work.

## Implementation tasks

### Task 1: Library data and decorated discovery

**Files:** Create `src/campervan/scan_library.py`, `src/campervan/scan_library_api.py`, `data/scan-library.json`.
Modify `src/campervan/api.py` and `src/campervan/scans.py` at the existing discovery/list integration points.

**Interfaces:** `ScanLibraryDocument` and `ScanEntryPreferences` Pydantic models; `ScanLibraryStore(path)` exposes
`read()` and `save(expected_revision, candidate)` returning `ScanLibraryDocument`. `decorate_scans(discovered,
document)` adds library fields without replacing asset identity. `register_scan_library(app, project_path)` registers
the literal library routes. Keep one implementation of scan discovery and the existing GET-list route.

- [x] Implement validated models and the project-adjacent store using the established atomic-save convention.
- [x] Extend current completed-run metadata projection with existing provenance/settings/count fields.
- [x] Merge library preferences into the current discovered list, including stable keys for loose previews.
- [x] Register GET/PUT library routes and seed the agreed initial curation as project data. Do not change assets,
  run IDs, source paths, measurement records or alignment files.

### Task 2: Manage scans overlay

**Files:** Create `frontend/src/scan-library.ts` and `frontend/src/scan-library-api.ts`; modify `scan.ts` and `style.css`.

**Interfaces:** `ScanResult` is the single shared scan-list type, retaining existing fields plus the library metadata.
`readScanLibrary()` / `saveScanLibrary(candidate)` use the existing HTTP helper. `createScanLibrary(host)` owns the
dialog, with `open()` and `refresh()`; the host supplies discoveries/current key, `view(key)` and a callback after a
successful save. The measurement controller keeps ownership of its own dialog/state.

- [x] Build a native HTML dialog styled as a right-side management panel, with labelled search/filter controls, group
  headings, details and explicit row actions. Restore focus on Close/Escape; no new tabs or viewport connection.
- [x] Implement display-name and group editing with explicit save/cancel, default selection and archive/restore.
  A modal backdrop/close discards only unsaved metadata drafts; it never triggers an archive or switches results.
- [x] Derive unavailable rows from saved preferences absent in discovery; show their original key without fabricating
  provenance. Keep archive/restore preferences for when the assets return.
- [x] Show pending save/error inline; prevent duplicate submissions. Use text nodes for all user/file-provided names.

### Task 3: Curated quick selector and stable result lifecycle

**Files:** Modify `frontend/src/scan.ts`; consume shared types/API from Task 2. Extend `scan-measure.ts` only where
empty-result handling requires it.

**Interfaces:** Add `clearDisplayedResult(): void` in Scan ownership: invalidate pending loads, dispose/remove the
attached `/Scan/Cloud` children using existing disposal, clear tag overlay/rendered capture and disable per-result
controls. Add `measure.clearCapture()` to deactivate/cancel the tool when no valid result exists, without deleting data.

- [x] Use stable result keys as selector values; filter to active/available entries and apply the exact initial/default/
  refresh rules above. Introduce the Result label, optgroups and Manage scans button.
- [x] Route View from the manager through the same result-loading function as the selector, preserving camera whenever
  the reference frame matches. Preserve the current layer when the destination supports it, otherwise use the existing
  preferred-layer rule.
- [x] Metadata-only changes refresh names/options without fetching geometry, cancelling a measurement draft or moving
  the camera. Do not run the existing unconditional asset reload merely to rename a result.
- [x] On archival/disappearance of the current result, invalidate async loads before selecting the fallback or clearing
  the scene. Late asset responses must not republish an archived result. Restore must not steal current selection.
- [x] Make all-active-empty and no-discoveries states useful: manager remains enabled, selector/layer/tool controls
  reflect availability, archived geometry is not left displayed, and restoring an item makes it selectable again.

### Task 4: Distinct measurement tool and library controls

**Files:** Modify `frontend/src/scan-measure.ts` and `frontend/src/style.css`. Reuse its existing measurement API,
overlay, modal list and save logic; do not introduce another measurement store or dialog implementation.

- [x] Replace `data-actions` / ellipsis with the labelled Measurements button wired directly to `showList()`.
  Remove unused dropdown imports, generic commands menu and the associated context-menu/keyboard handlers.
- [x] Remove the duplicate bottom Measurements button and add the contextual Restore / Cancel pair / Done control,
  using the same local command as Escape. Keep T on the tape button and all shortcut/focus protections.
- [x] Reattach both toolbar controls idempotently after native scene replacement; opening Measurements while the tape
  tool is off must work. Editing a saved pair may enter measurement mode through the existing `selectPair` path.
- [x] Keep status and manager overlays independent of canvas sizing. Preserve existing selected/saved line colours,
  pending dash style, entry parsing, save feedback and layout association.

### Task 5: Documentation and acceptance

**Files:** Update `README.md`, `docs/photogrammetry.md` and the current measurement plan where it prescribes the
superseded generic menu. This plan's implementation record should distinguish code completion from visual acceptance.

- [x] Document names/default/archive semantics and where the project library file lives. Explain that archive is not
  deletion and that processing resolution is not an accuracy ranking. No new startup/environment instructions.
- [x] Run focused Ruff/format/mypy for changed backend files and the existing frontend TypeScript check once. Classify
  required failures; the known `plan-dropdown.ts:82` error is unrelated. Do not create or run tests/extra suites.
- [ ] Have Gert inspect: curated startup list; rename without reloading geometry; archive/restore/current/default/all
  results; grouped browsing; details; invalid/failed save; active measurement while renaming; tape T/Escape; opening
  Measurements while tape is off; and canvas size while panels/status appear. Do not automate interactions unless asked.
- [x] Confirm original captures/assets and physical measurements are unchanged, the old ellipsis menu is gone, and
  there is exactly one primary toolbar entry for measuring and one for its saved records.

## Review focus

- Renaming previews cannot change the filename used to load them (Tasks 1/3).
- Archiving a displayed/default/all remaining result cannot leave a hidden result selected or restore it via a late
  async asset response (Task 3).
- Metadata updates cannot reset camera, reload textures or cancel an unrelated measurement draft (Task 3).
- Library metadata must survive missing files and malformed preferences must never be silently replaced (Tasks 1/2).
- Keyboard shortcuts must retain priority over native renderer bindings while respecting editable fields and dialogs
  (Task 4); empty-result cleanup must not delete measured constraints (Task 3).

## Sources and decisions

These precedents support the chosen separation, not a claim that one layout is universally best:

- [SketchUp Tape Measure](https://help.sketchup.com/en/measuring-distance): direct tool activation plus contextual
  measurement entry. Preserve the interaction Gert already chose.
- [FreeCAD measuring tutorial](https://blog.freecad.org/2026/05/15/tutorial-tips-for-the-measuring-tool/): a dedicated
  measurement operation rather than a miscellaneous overflow bucket.
- [Onshape measurement](https://cad.onshape.com/help/Content/View/measure_tool.htm): measurements tied to current
  selection and expanded details. Keep the active pair's information contextual.
- [Unreal Content Browser](https://dev.epicgames.com/documentation/en-us/unreal-engine/content-browser-interface-in-unreal-engine):
  separate asset organisation/search from viewport tools. Adapt this to a small list, not a complete editor browser.
- [Unity overlay guidance](https://unityeditordesignsystem.unity.com/patterns/overlays): contextual tool controls and
  overlays; preserve the user's requirement that transient controls do not resize the viewport.

**Planning record:** started 8 November 2026 21:53 UTC (9 November NZDT), approximately five minutes of inspection and
planning. Inspected current discovery, manifest projection, API/storage conventions, selector lifecycle and measurement
controller. No product code/data changed, services started, tests run, browser interactions or delegated reviews.

## Execution record — 9 November 2026

Implemented the library store/API, initial project curation, scan manager, stable result selection/empty-state cleanup
and compact measurement controls. Preferences live in `data/scan-library.json`; original databases, manifests, geometry,
alignment and physical measurements were not modified. README and photogrammetry guidance now describe the controls.

The manager uses native `dialog.showModal()`, an accessible title, a Close button, Escape/light dismissal and focus
restoration, following [MDN dialog guidance](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog)
and the [WAI modal-dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/). Measurement shortcuts defer to
open dialogs. These decisions do not establish universal accessibility compliance; interaction acceptance remains open.

Ruff lint passed for the four affected backend files. Format passed for the three scan files; api.py has pre-existing
format differences in unrelated parameter/PDF/cutting functions. Nonincremental mypy reported only seven existing bare
`dict` return annotations in api.py cutting functions; no scan-code errors. Frontend TypeScript still reports only
`plan-dropdown.ts:82` (`onfocusout`, TS2551). These unrelated issues were left unchanged.

A passive snapshot of the existing app tab shows the three curated results, Manage scans, tape and Measurements.
Its console has no warnings/errors. No browser interaction checks, tests, processing jobs, services, commits or delegated
reviews were run. Gert's manual acceptance above remains outstanding. Implementation took approximately eight minutes
against the 20–30 minute estimate; detailed execution notes are in `.local/scan-library-implementation.md`.

### Follow-up: action labels and result comprehension

Gert's visual feedback rejected the noun-only Measurements button, oversized repeated action blocks and unexplained
result names. The initial research did not justify that presentation. This follow-up supersedes the original row
presentation and noun-only toolbar label:

- **Show saved measurements…** explicitly opens the saved-pair dialog, with `aria-haspopup="dialog"` and its target ID.
- Results use compact separated rows with reconstruction method, fusion resolution and frame count visible. These
  summaries derive from manifest metadata, without interpreting filenames or introducing van-specific code.
- **Show in viewer** is the visible result action. **Inspect result** discloses provenance and secondary management
  actions, keeping rename/group/default/archive controls out of the comparison list until requested.
- **In viewer** and **Opens at startup** are state labels, not disabled action buttons. Secondary actions describe
  their result: Rename result, Change capture group, Use at startup, Archive result, Restore to selector.
- Fixed inherited sidebar heading styling and gave search enough width to display its purpose. Kept the existing
  viewport overlay, data model, save behaviour and separate measurement tool/list responsibilities.

Sources consulted 9 November 2026:
[GOV.UK buttons](https://design-system.service.gov.uk/components/button/) requires action-describing text;
[GOV.UK summary-list guidance](https://design-system.service.gov.uk/components/summary-list/) explains association and
context for repeated row actions. Applying a compact comparison list with disclosed management actions is this
project's design decision, not a claim those references prescribe a specific CAD layout.

Frontend TypeScript checking still reports only existing plan-dropdown.ts:82 TS2551. No backend changes, tests,
services, browser interaction checks or delegated reviews. The revised appearance and interactions remain for Gert's
visual acceptance.

### Follow-up: direct rename and confirmed deletion

Gert explicitly requested visible pencil and trash-can actions in Manage scans, with confirmation for deletion.
This authorises permanent result deletion and supersedes the original deletion exclusion above.

- Result rows expose labelled/tooltip pencil and trash icons. Group renaming uses the same pencil affordance.
- Pencil reuses the existing display-name editor; no filesystem rename. Removed the duplicate rename action from
  the inspection disclosure.
- Trash opens a native confirmation naming the result/path and the generated files being removed. Cancel is initially
  focused; the final action says Delete result. Original capture DBs and physical measurements are kept.
- Added revision-checked DELETE /api/v1/scans/library/result. Deletion is contained to one published run directory or
  preview PLY; linked result paths and escaping identifiers are rejected. Missing assets can have preferences removed.
- Successful deletion removes its library entry/default and refreshes the existing selector/fallback path. On failure,
  discovery is refreshed as deletion can have removed some files before an I/O failure. File removal and preference
  persistence are not a cross-filesystem transaction; failures state that deletion did not finish.

Sources: [GOV.UK warning-button guidance](https://design-system.service.gov.uk/components/button/) distinguishes the
initial delete trigger from the final destructive confirmation; [WAI modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
supports initially focusing the least destructive action and restoring focus on dismissal.

No actual result/capture/measurement files were deleted during implementation. No tests, services or browser interaction
checks were run. Ruff lint/format pass for the three changed backend files. Frontend checking still reports only the
existing plan-dropdown.ts:82 TS2551. Visual interaction acceptance remains Gert's.

### Follow-up: database import and processing UX

Gert authorised the group-level upload workflow on 9 November: choose/drop original databases, review inputs and tag
setup, process, inspect progress/errors, then explicitly open the generated result. Implemented with retained source
imports, new physical tag-layout identities and per-layout measurement stores, plus one existing-environment CLI
subprocess managed by the local API. It uses the existing reconstruction function and result discovery, not a parallel
pipeline or additional service. Group assignment merges into current library preferences. A new layout receives no
old distances, tag roles or alignment transform.

The [browser import documentation](../../photogrammetry.md#browser-import) records the controls, storage, endpoints,
progress semantics and interruption limits. Single-database processing with tag settings now detects tags through
native reprocessing too. Uploaded identical bytes in one group reuse their source identity; failed jobs retain inputs
for explicit reruns. Optional photo failure can expose the already published baked result.

Focused scan backend Ruff/format/mypy checks pass. Integration mypy including api.py/cli.py reports only the seven
existing cutting-endpoint bare-dict annotations. Frontend TypeScript still reports only existing plan-dropdown.ts:82
TS2551. Passive console inspection found no warnings/errors and API logs show successful watcher-driven startup.
No services were started by the agent, and no uploads, reconstruction jobs, tests, browser interaction flows or
independent reviews were run. Gert's first new-capture import is still the end-to-end acceptance.

### Follow-up: reload must retain the working result

Gert reported apparent measurement loss after a hot reload, then identified that the viewer had selected the older
capture group. Read-only inspection confirmed the new layout still held four measurements (1–2, 1–3, 1–6, 1–7) at
revision 5; the old layout separately held 1–11. API logs showed the reload requesting the old layout. No measurement
files were modified during diagnosis or correction.

Added tab-local session storage for the selected result and layer. Reload restores that active/available result before
considering the startup default; a fresh tab uses the default. Archived/deleted results still fall back normally, and
an empty active library clears the remembered selection. This refines the original initial/default-load semantics.
Seeded the live tab's existing result/layer preference before code reload, without changing its selection or data.
Frontend TypeScript checking reports only the existing plan-dropdown.ts:82 TS2551. No tests or automated interaction
flows were run; the persistence behaviour remains for Gert to confirm visually.
