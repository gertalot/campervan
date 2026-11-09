# Tag tape-measure implementation plan

> **For implementers:** Use `superpowers:executing-plans` task by task. Repository instructions prohibit creating or
> running tests, service startup and unsolicited delegated reviews. Those instructions override generic workflows.
> Gert authorised milestone 1 with “do it”. Service restarts remain user-owned; GTSAM is a separate follow-up.

**Goal:** Enter and edit physical tag-to-tag distances in the Scan viewer, preserving them as reusable input data for
later GTSAM optimisation.

**Architecture:** Extend the existing projected tag overlay and native viewer toolbar. A small measurement controller
owns interaction state; the existing FastAPI application persists a separate measurement document. Processing and
optimisation consume explicitly supplied documents, without embedding this van's tag IDs, measurements or paths.

**Tech stack:** Existing TypeScript/Three.js/SVG, FastAPI/Pydantic, Python 3.13 through uv. No new dependency for the
tape-measure milestone. GTSAM is a later dependency decision.

**Spec:** Gert's approved interaction in this conversation; [photogrammetry workflow](../../photogrammetry.md),
especially sections 4–6. The current scope specialises that document to recognised tag centres. Arbitrary surface
points, image-observation editing, CAD refinement and automatic optimisation are outside the first milestone.

## Constraints and implementation evidence

- Code and scene data stay separate. No automatic lookup of a van-specific reference file inside the pipeline.
- Fixed physical tag layout: measurements survive new captures and reconstruction settings. Reusing tag numbers
  after moving tags requires a new layout identity and measurement document.
- Existing `scan.ts` owns layer loading, the native viewer and camera persistence. `scan-tags.ts` projects stored tag
  centres/outlines through the same camera, including the optional scan-to-reference transform.
- The SVG currently has `pointer-events: none`; introduce explicit picking only while the measurement tool is active.
- `viewer-drag.ts` demonstrates native toolbar attachment, a 4 px drag threshold and guarded keyboard handling.
  Reuse those conventions without enabling furniture dragging in Scan.
- The original generic Scan actions menu was superseded by the
  [scan library and compact controls plan](2026-11-09-scan-library-and-controls.md): use a tape toggle, a labelled
  Measurements button and a contextual Escape action instead.
- `api.ts` exports the shared HTTP request helper. `settings.py` is the single environment boundary. Project saves use
  a sibling temporary file followed by replace; reuse that local file-writing convention.
- Preserve projection, pan, rotation and zoom. A measurement edit never changes geometry or starts processing.
- Do not create/run tests, start services, open browser tabs, introduce a job platform or commit unrelated changes.
- Gert's visual interaction is acceptance. Existing static checks may be used once for changed code.

## Agreed interaction

Add a tape-measure icon to the existing Scan viewer toolbar, with accessible name **Measure tags**, pressed state,
tooltip and shortcut **T**. Add a visible **Show saved measurements…** button opening saved records independently of tape mode.
Show cancellation rules and the current Escape action in the contextual bottom status line. Keyboard activation is scoped to
Scan and never consumes ordinary input in another field, select, contenteditable element or composition session.

| State | Viewer | Bottom status / distance field |
| --- | --- | --- |
| Off | Measurement lines hidden; normal navigation | No measurement prompt |
| Choose first | Saved lines visible; tags available | Select first tag |
| Choose second | First tag highlighted; rubber-band line follows pointer and snaps to hovered tag | Select second tag · Esc to cancel |
| Edit pair | Both endpoints and connecting line highlighted | Tags A ↔ B · Scan: … mm; editable Distance field |
| Saving | Pair retained; prevent duplicate submissions | Saving… |
| Saved | Line and endpoints use the saved style | Saved … mm; return to Select first tag |

- Distances are full 3D centre-to-centre lengths, not horizontal projection lengths. The UI labels this explicitly.
- A newly selected pair starts with its saved measured value, if present; otherwise the current scan distance.
  Scan distance remains separately visible. Merely selecting a pair never creates a saved constraint.
- First numeric keystroke replaces the prefilled value and focuses the input automatically. Subsequent characters,
  selection, deletion, paste and unit text behave like normal text entry. Clicking the field also permits normal edits.
- Accept decimal values with optional whitespace and units `mm`, `cm`, `m`, `in`, `ft`, case-insensitively. Bare numbers
  mean millimetres. Examples: `12.4cm`, `234mm`, `841 mm`. Normalize once into metres. Reject zero, negative, non-finite,
  unknown units and compound expressions with a clear inline message; retain the draft for correction.
- Enter validates and saves/upserts the pair. Only successful persistence changes its appearance to saved.
  Accepting an unchanged prefill still requires Enter; no inferred physical measurements are saved automatically.
- Escape while text is dirty restores the pair's previous value, leaving the pair selected. Escape again with a clean
  field cancels the active pair and returns to Choose first. During Choose second, Escape clears the pending line.
- A primary click on empty viewer space cancels the unfinished pair/draft, restoring any previous saved value.
  Clicking the first tag again requests a different second tag; it never creates a zero-length constraint.
- Orbit/pan drags over 4 px, wheel/pinch zoom, toolbar clicks and field clicks are not empty-space cancellation.
  Ignore non-primary clicks for measurement selection. Handle pointer cancellation without saving.
- Selecting a previously measured pair edits it, independent of endpoint order. Only one saved value exists per pair.
- Disabling the tool discards unfinished edits and hides all measurement lines/labels. Saved data remains.
- Changing capture or leaving Scan discards only the draft. Preserve tool preference, camera and saved constraints;
  show saved lines only where both tags are present. Explain missing endpoints in the measurement list.
- Active tool temporarily shows tag markers even if the ordinary AprilTags visibility toggle is off; restore that
  preference when the tool is disabled. Use colour plus line style/text: pending dashed, editing solid, saved labelled.
- Provide a compact **Measurements…** list for reviewing, editing and removing saved pairs. Show tag IDs, measured
  distance, current scan distance and signed residual (`scan − measured`). Missing tags display “Unavailable”.
  Removing a constraint requires its explicit Remove action; cancellation never deletes saved constraints.
- Tag selection is also keyboard-operable: focusable, labelled tag targets and Enter/Space, plus pair selection from
  the measurement list. Bottom prompts use a polite status region; validation errors remain adjacent to the input.

## Data and API contracts

The independent measurement document has `version: 1`, a nonempty `tag_layout_id`, a monotonic `revision`, and a list
of records. Each record contains canonical endpoints `tag_a < tag_b`, positive finite `distance_m`, original
`entered_text`, `source_run_id` for provenance, and nullable `sigma_m` for a future explicitly supplied uncertainty.
No current tag XYZ positions or scan-derived distances become authoritative measurement data. No uncertainty is
invented from the number of digits typed. Layout and record fields are validated with Pydantic; malformed existing
files produce an error, never a silent empty replacement.

For this van, create a separate empty `data/scan-measurements.json` with a data-defined layout ID. Do not prepopulate
any distances discussed in chat: those were scan readings, not supplied physical measurements.

- The application passes `project_path.with_name("scan-measurements.json")` to the reusable store, following existing
  adjacent planner-data storage. No extra environment setting is needed. The reusable store accepts a path argument
  and knows no project path. This replaces the initial extra-setting proposal following Gert's correction.
- Extend `scan process` and `scan align` with optional explicit `--measurements FILE`. Read/validate the document and
  record only its `tag_layout_id` in the run metadata, without applying its distances. Associate the existing runs
  using this explicit input; do not infer a layout from tag numbers, filenames or the coordinate-frame name.
- A run's layout must match the configured document before saving. An unassociated/mismatched run remains inspectable
  but cannot silently write constraints into the wrong physical layout. Association is independent of axis alignment.
- `GET /api/v1/scans/measurements` returns `{configured: true, document}` using the project's measurement document.
- `PUT /api/v1/scans/measurements/{tag_a}/{tag_b}` takes `{revision, tag_layout_id, distance_m, entered_text,
  source_run_id}` and returns the updated document. Validate the referenced run/layout and that both IDs were detected.
  Preserve an existing `sigma_m` when editing distance; a new record starts with null.
- `DELETE` on the same route takes the expected revision and layout ID and returns the updated document.
- Canonicalize unordered pairs server-side. Reject self-pairs and invalid distances. Return 409 for stale revision or
  layout mismatch, 422 for invalid input, and a plain save error for filesystem failure. Serialize the short
  read-modify-replace operation locally; no database, generic transaction layer, retry or multi-user framework.
- Define measurement routes before the existing `/api/v1/scans/{filename}` route. Retain existing list/asset routes.
- A save error leaves the entered value and pair selected, shows the error and does not show a saved line. On a stale
  revision, retain the draft and refresh the document; require another explicit Enter rather than silently overwriting.

## Milestone 1: Usable tape measure and persistent constraints

### Task 1: Measurement data, explicit association and API

**Files:** Create `src/campervan/scan_measurements.py`, `src/campervan/scan_measurements_api.py` and the empty data file.
Modify `api.py`, `cli.py`, `scans.py` and `scan_alignment.py` only at their direct integration points.

**Interfaces:** `MeasurementDocument` and `DistanceMeasurement` models; `MeasurementStore(path: Path)` with `read()`,
`upsert(expected_revision, record)` and `remove(expected_revision, tag_a, tag_b)` returning `MeasurementDocument`.
`register_scan_measurements(app, path: Path)` installs the routes. The store is independent of run discovery;
the route layer validates provenance using the existing run manifests.

- [x] Implement validated document models, canonical pairs and file persistence using sibling temporary-file replace.
- [x] Add explicit app-path configuration and run-layout association, including the current captures' association.
- [x] Register the GET/PUT/DELETE routes and expose `tag_layout_id` in scan listing metadata.
- [x] Document local launch configuration and both CLI options. Do not start or restart the user's services.

### Task 2: Tag selection and projected measurement geometry

**Files:** Modify `frontend/src/scan-tags.ts`; add `frontend/src/scan-measure.ts` for the interaction controller.

**Interfaces:** Extend `createScanTags` with `pickTag(clientX, clientY): number | null`, `setSelection(ids: number[])`
and `setMeasurements(records, pending)`; continue using its existing projection/update path. Export projected picking
without a second render loop. `createScanMeasure(host)` owns the states above; its host supplies current tags,
layout/run identity, measurement API operations and status/field elements.

- [x] Retain the transformed 3D centres used by the overlay. Pick within a 12 CSS-pixel radius of a centre, or its
  visible outline/label; choose the nearest projected centre for overlapping hits and ignore clipped/behind-camera tags.
- [x] Draw pending/saved lines and labels in the existing SVG. Endpoints follow tag centres during navigation;
  the rubber band is a screen-space preview and never creates a false 3D point on an arbitrary surface.
- [x] Implement first/second tag selection, distinct endpoint enforcement, cancellation and the 4 px click/drag rule.
- [x] Add keyboard-operable tag targets while active; leave passive overlay pointer behaviour unchanged when off.

### Task 3: Toolbar, bottom status line, entry and save/edit loop

**Files:** Modify `frontend/src/scan.ts`, `frontend/src/style.css`; add `frontend/src/scan-measurements-api.ts` using
the existing `request` helper. Keep measurement-specific state and command definitions in `scan-measure.ts`.

- [x] Add the tape toggle and labelled Measurements button to the existing native toolbar, reattaching after scene
  replacement without duplicate listeners. The compact-controls follow-up supersedes the original generic menu.
- [x] Overlay the status line and labelled distance input at the bottom of the viewer. Do not add a grid row or resize
  the Three.js canvas when showing it; preserve the current camera view.
- [x] Implement input parsing, prefill, numeric type-to-replace, Enter save and the two-stage Escape behaviour above.
  Guard modifier keys, composition, other editable fields and hidden panels. Keep focus predictable after saving.
- [x] Connect async persistence with the existing HTTP helper. Prevent repeated Enter while saving. Capture the pair,
  layout and run when submitting so a response cannot attach the saved style to a subsequently selected pair/run.
- [x] Add the compact measurement list, existing-pair editing, removal and numerical residuals. Render stored text
  through DOM text APIs; do not inject user-entered strings into markup.
- [x] Preserve tool preference through layer changes; discard drafts on capture/tab changes. Keep camera navigation
  intact, show tag markers temporarily while measuring, and draw stored constraints against the current run's poses.

### Task 4: Documentation and Gert's acceptance

**Files:** Update `README.md` and `docs/photogrammetry.md` with the finished interaction, data schema and commands.

- [x] Run the existing focused Ruff/format/mypy checks and frontend `npm --prefix frontend run check` once. Report
  the known unrelated frontend diagnostic separately; do not create or run tests or additional validation suites.
- [x] No extra service configuration or manual restart is needed after removing the measurement environment setting.
- [ ] Have Gert inspect: new pair → units entry → Enter; edit same pair reversed → Escape restore; empty click cancel;
  orbit/pan/zoom during selection; hide/show tool; reload persistence; same constraints on another associated capture;
  missing endpoints; malformed value and visible save failure. No browser interaction suite or delegated review.
- [x] Confirm no physical measurements were invented, no CAD/scan geometry changed, and all scene-specific values are
  in data. The milestone is usable without GTSAM installed.

## Milestone 2: GTSAM optimisation and reconstruction

This is a separate follow-up, not a hidden side effect of measurement entry. The installed RTAB-Map build has g2o,
not GTSAM, and the project currently declares no GTSAM dependency. Do not promise a ready Optimise button in milestone 1.

1. **Resolve the runtime and graph adapter first.** Verify a supported GTSAM route on this Mac/Python 3.13 before
   choosing a dependency. Inspect original node poses, odometry/loop links, tag observation transforms and information
   matrices. Record node/base/optical pose conventions, tangent-space ordering and covariance conversions. Saved
   optimised poses are initial values, not substitute independent odometry measurements.
2. **Extend the measurement UI deliberately.** Add editable uncertainty and input/check roles before optimisation.
   Hold check measurements out of the graph. Null uncertainty requires an explicit choice; do not treat it as an exact
   constraint or invent a precision. Snapshot the chosen data/revision for each optimisation run.
3. **Optimise connected camera and tag poses.** Use the original graph plus tag observations and measured range factors;
   anchor gauge freedom once and diagnose disconnected/weakly constrained components. Retain tag orientation where
   observed. Report inconsistent constraints rather than silently stretching the mesh or changing global scale.
4. **Rebuild a new result.** Export corrected optical camera poses and corrected tag poses in a consistent frame.
   The current `--poses` path deliberately omits saved tags, so extend that contract to accept corrected landmarks too.
   Reuse `process_scan`, Open3D reconstruction and optional photo texturing. Recalculate the tag-defined alignment.
   Keep original databases/results intact; store source hashes, measurement snapshot, solver settings and residuals.
5. **Then add Optimise scan to the existing API/UX.** Use an offline command first, then a single local subprocess from
   the existing API with visible progress/error and one active operation. No service, queue or worker platform. Keep
   viewing the original until a new result is ready; preserve camera when switching between matching reference frames.
   Compare measured-input residuals and held-out checks separately. Do not expose a nonfunctional action meanwhile.

The runtime/dependency choice and graph conventions need their own bounded implementation plan after inspection.
Confirm that choice in the follow-up plan before introducing GTSAM. Do not implicitly change the Python runtime or
add an external service. This planning task installs no dependencies.

## Research and UX decisions

- [WAI button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/): use a native, consistently named toggle with
  `aria-pressed`, keyboard activation and a visible focus indication.
- [WAI toolbar example](https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/examples/toolbar/): preserve a discoverable,
  keyboard-operable toolbar; extending the existing toolbar does not justify replacing its navigation mechanism.
- [WAI status messages](https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html): announce stage/save changes
  politely without making the entire viewer a live region. No broad accessibility-compliance claim.
- [GTSAM factor-graph introduction](https://gtsam.org/tutorials/intro.html) and
  [range factors](https://github.com/borglab/gtsam/blob/develop/gtsam/sam/RangeFactor.h): distances belong in a graph
  connected to the camera/landmark observations; range constraints alone do not correct dense RGB-D geometry.

## Review focus

- Normal typing, native field editing and IME must survive the global type-to-enter affordance (Task 3).
- Camera dragging is not a failed destination click; overlay labels must not steal navigation (Task 2).
- Prefilled scan distance is not persisted until explicit Enter, and Escape cannot erase a saved record (Task 3).
- An async save or capture change cannot save against the wrong pair/layout; failed saves remain visibly unsaved (Tasks 1/3).
- Identical tag numbers in a different physical layout cannot silently reuse constraints (Task 1).

**Planning verification:** inspected the viewer, tag projection, camera/drag interaction, API/settings, existing file
save and menu conventions, and the photogrammetry specification. No product code, services or tests changed/run for
this planning task. Independent review was not delegated, per repository instructions.

## Milestone 1 execution record

Implemented 8 November 2026. The existing browser tab shows the tape toggle and Scan actions control; passive console
inspection found no errors. Current captures were explicitly associated with the empty measurement document through
`scan align --measurements`; its revision is still zero and no physical values were invented.

Focused Ruff/format and mypy checks pass. Frontend type checking reports only the pre-existing
`plan-dropdown.ts:82` `onfocusout` error. No tests, interaction suites, services, dependencies, commits or delegated
review passes were created/run. The initial implementation required an extra environment setting; the follow-up below
supersedes that requirement. The broader manual acceptance remains Gert's. GTSAM remains unimplemented.

### Follow-up: storage, overlay and shortcuts

Removed the extra setting and used the existing adjacent-project-file convention. The live API returns the valid
empty measurement document without environment configuration. Positioned the status line absolutely over the viewer;
live canvas dimensions remained 1720 × 1214 before, during and after tool activation.

The native renderer consumes `t` for transparency, Escape for stop, and numeric view keys before a window bubble
listener. Measurement shortcuts now run in capture phase with field/menu/composition guards. At the idle prompt,
Escape exits the tool. On Gert's explicit shortcut bug report, checked real T/Enter/numeric/Escape keys in the existing
tab: activation works, typing replaces the prefill, Escape restores 1214.6 mm, subsequent Escapes cancel then exit.
No distances were saved during this check; the data document remains empty.

### Follow-up: first numeric key must not change view

Gert reported numeric distance entry activating the native front/right/top view shortcuts. The numeric type-to-replace
branch prevented default input and focused the Distance field, but did not stop propagation. The installed renderer's
container key handler dispatches number shortcuts without checking `defaultPrevented`; its event target/path still
refer to the viewer for this first key. Added `stopPropagation()` to this consumed numeric event, matching T/Escape/
Enter handling. Later keystrokes target the input and retain native text editing; the renderer already skips text inputs.
No native renderer/global keymap changes were needed.

This follows [MDN event propagation guidance](https://developer.mozilla.org/en-US/docs/Web/API/Event/stopPropagation):
preventing default behaviour and stopping propagation are separate operations. No tests or browser interaction flows
were run, per repository instructions. TypeScript checking still reports only existing plan-dropdown.ts:82 TS2551.
Gert's numeric-entry check remains the interaction acceptance.
