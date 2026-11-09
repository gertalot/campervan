# Measurement management, uncertainty and suggestions implementation plan

> Planning only. Use `superpowers:executing-plans` if Gert approves implementation. Repository instructions take priority:
> do not create/run tests, start services, automate browser interaction flows, dispatch review agents or alter capture /
> measurement data during planning. Keep this local scan subsystem simple. No job framework or general panel platform.

**Goal:** Manage measured tag distances in a side panel, preview a statistically weighted reconstruction adjustment,
apply/revert it without overwriting observations, and recommend every additional worthwhile, physically plausible pair.

**Architecture:** A shared side-panel component owns the shell, action/content slots, X close control, focus and dismissal
for both scans and measurements. Domain controllers supply their own content and behaviour. Extend the existing
measurement store/controller, reconstruction worker and tag overlay. A pure GTSAM
analysis consumes original graph observations plus physical distances, producing an immutable solution and covariance
summary. Apply rebuilds through the existing Open3D pipeline into a separate result. Suggestions use this same model
and the existing mesh for conservative straight-segment obstruction checks.

**Stack:** Existing Python 3.13 / uv, FastAPI, TypeScript, Three.js and Open3D. Propose adding pinned `gtsam==4.3.0` to
optional scan dependencies; official PyPI lists a CPython 3.13 macOS universal2 wheel. No dependency change in planning.

**Requirements:** Gert's current request; [photogrammetry workflow](../../photogrammetry.md), especially joint camera /
landmark optimisation and preservation of original observations. Predecessors:
[measurement interaction](2026-11-08-tag-measurements.md) and
[scan management](2026-11-09-scan-library-and-controls.md).

## Evidence and scope

- `scan-measure.ts` currently owns tape interaction, saved-pair dialog, parsing and saves. The toolbar says Show saved
  measurements. `scan-library.ts` provides the right-side manager and named Close button. Do not rebuild tape selection.
- Measurement documents are per physical tag layout and store original distance/text, source run, revision and nullable
  `sigma_m`. The current interior layout has 35 distances touching 22 of 24 detected tags; all sigma values are null
  at inspection time. The full 24-point 3D network has 66 internal degrees of freedom before distance constraints, so
  35 distances alone cannot fully determine it. Counts are evidence, never constants in implementation.
- `saved_tags()` currently exports estimated landmark poses and observation counts, not the observation transforms or
  information matrices needed by GTSAM. The retained merged database has Link.transform and Link.information_matrix,
  with types 0/1/2/8/9 present. Their exact meanings, directions and tangent conventions must be decoded from the
  applicable RTAB-Map source; do not infer them from the integer or duplicate inverse links as independent evidence.
- The existing run retains frames, optical camera poses and working DBs. `--poses` is already the reconstruction seam,
  but currently causes saved tags to be omitted. A corrected result must receive correspondingly corrected tag poses.
- `ScanProcessing` manages one CLI subprocess, stored stage/log progress and result-group publication. Extend this
  scan-owned mechanism for analysis/rebuild; no separate scheduler, service or parallel reconstruction implementation.
- This plan includes joint graph optimisation because tag-only changes would leave the visible mesh inconsistent and
  would not fulfil the saved pipeline. Camera/landmark observations supply real constraints; saved global estimates
  are initial values, not synthetic independent measurements with invented confidence.

## Product decisions proposed for approval

### Panel and actions

- Rename the toolbar action **Manage measurements…**. Open a right-side overlay with the same width, colours, heading
  and spacing conventions as Manage scans. Keep the canvas dimensions and camera unchanged.
- Implement this as one reusable side-panel component, not two similarly styled dialogs. Both managers use the same
  shell and close/focus behaviour; measurement/scanning business logic remains in their respective controllers.
- Use an X icon in the top-right of both managers, implemented as a real button with an accessible Close measurements /
  Close scans name and tooltip. Escape/focus restoration remain available. Do not change unrelated dialogs.
- The measurements panel should be nonmodal so Gert can orbit/pan the viewport while inspecting an analysis. Keep the
  existing scans manager modal; consistency here is visual. At most one management panel is displayed at a time.
  Do not apply a modal focus trap/aria-modal to the nonmodal measurement panel. Existing import/delete confirmations
  remain modal. Explicitly scope Escape to its owner and make scan shortcuts respect active text fields/modal dialogs.
- Heading/context first: capture group, selected result and physical tag-layout name; a result switch cannot silently
  display another layout's distances. Preserve tab-local result selection on reload.
- A compact action strip near the top contains **Analyse uncertainty**, **Suggest more**, and contextual **Apply** /
  **Revert** while a preview exists. Show real stage/error feedback immediately below; lists follow underneath.
- Measurements list columns: Tags, Entered distance, Current fitted distance, Difference, Measuring precision. Retain
  edit and explicit remove through the existing store. Analysis also exposes before/after residuals and likely outliers.
- Add a clearly labelled layout-level typical measuring precision, with per-record overrides using existing sigma_m.
  Require an explicit assumption before quantitative analysis. Help must define that stored precision is 1-sigma;
  reported uncertainty is an approximate 95% interval. Do not silently invent precision from decimal places or residuals.
- Changes to precision are ordinary measurement-model edits, revisioned separately from accepting a fitted solution.

### Analyse, Apply and Revert

1. Analyse snapshots the selected run, layout, measurement revision and noise assumptions; it changes no source data.
2. Show original and proposed tag locations with movement vectors in the viewer, plus per-measurement before/after
   residuals, uncertainty changes, downweighted measurements and graph/rank diagnostics. Original surface stays visible
   and is explicitly the pre-adjustment surface during this preview.
3. Apply accepts that solution and starts rebuilding a **new corrected result** using its camera poses and landmarks.
   Never rewrite the entered distances/text or the original DB, run manifest or geometry. Keep the old result usable
   until the new result publishes successfully. Show rebuilding progress; a failure preserves the accepted solution
   and original result so rebuilding can be requested explicitly again.
4. On successful publication, open the corrected result in the same group/layout, preserving camera if its frame is
   compatible. Its manifest references the analysis, source result, source measurement revision and original captures.
5. Revert during preview discards only the preview. After Apply, Revert returns to the prior result/accepted solution;
   both results remain available. It never deletes measurements, undoes later manual edits or deletes generated files.
6. Close/X hides the panel and unapplied overlay, retaining the draft analysis for reopening while its inputs remain
   current. It does not apply changes or stop an explicitly launched rebuild. A fresh page load does not activate an
   unapplied draft. Persist accepted solution/source history so an applied result can be reverted after reload.
7. A measurement edit/removal, precision change, source-result change or layout switch invalidates its preview and
   suggestions. Apply rejects stale inputs with 409; rerun analysis explicitly. Async responses cannot repaint another
   capture/layout. Do not silently rerun/replay a rejected Apply.

### Suggest more: all useful pairs

- Suggest more uses a current analysis, automatically performing the same analysis first if none is current; it
  presents no numerical improvements until graph/noise prerequisites succeed.
- Enumerate every unordered detected-tag pair. Exclude already measured pairs from the additional-measurements list;
  separately offer useful repeats of inconsistent/low-confidence readings as **Remeasure** recommendations.
- Use joint covariance, including cross-correlations. For each candidate, predict the information added by a distance
  measured with the chosen precision, and recompute uncertainty in target dimensions using a linearised information
  update. Do not confuse large fit residuals with large information gain.
- Initial target set: all distances between detected tags, a coordinate-invariant, explicitly named metric. Permit
  pinning a smaller set of important dimensions later; furniture/semantic dimension recognition is outside this work.
- Initial threshold: **at least 5 mm reduction in the approximate 95% uncertainty half-width of at least one target
  distance**. Expose the threshold and assumed measuring precision. For every row identify the affected dimension,
  before/after interval and predicted reduction. This is a model prediction, not guaranteed physical accuracy and not
  necessarily a 5 mm movement of a tag. Document this default for Gert's approval.
- Show **all** qualifying pairs ranked by predicted gain, with independent gains evaluated against the same current
  baseline. Identify largely overlapping benefits; never add them as independent improvements. After each accepted
  measurement, invalidate/recompute the list rather than leaving stale recommendations.
- A weak/unobservable graph is a diagnostic, not a finite confidence interval. Show connections that may remove weak
  modes separately, without a fabricated millimetre score. Do not force invertibility with arbitrary tiny priors.
- Each row has an explicit Measure pair action to highlight endpoints, close the manager and use the existing tape
  entry flow. Original input values are never prefilled as if they were newly observed physical measurements.

### Can the tape pass between them?

- Build one Open3D RaycastingScene from the selected result's untextured mesh in the same coordinates as its tags.
  Test the finite straight centre-to-centre segment, not an infinite ray and not visibility from the current camera.
- Ignore only small endpoint neighbourhoods attributable to tag-on-surface placement and reconstruction tolerance.
  Derive/report tolerance from scan resolution and uncertainty. Test nearby clearance rays to avoid interpreting a
  single mesh hole as a clear path; report uncertainty when results disagree. Exclude endpoint contact, not genuine
  obstructions near a tag. Do not require the tags to face each other: the physical tape path is the criterion.
- Classify **Obstructed**, **No obstruction detected**, or **Unknown clearance**. No detected hit is conditional on the
  reconstructed surfaces; it cannot prove free space in unobserved regions. Missing/incomplete geometry, holes, large
  preview tag movement relative to the original mesh or unsupported point-cloud-only results cannot be called clear.
- Assess coverage using retained RGB-D frames: sample the interior segment at scan-resolution spacing, project samples
  into calibrated source depth frames, and require valid depth showing free space up to each sample, with depth/noise
  tolerance. Uncovered/ambiguous spans yield Unknown even when mesh rays miss everything. Use the source poses with
  the source depth, or corrected poses with corrected geometry; never mix these coordinate models. This is local
  evidence for a clear segment, not a general-purpose occupancy or reachability framework.
- Default list shows worthwhile pairs with no detected obstruction, alongside a separately accessible Unknown list.
  Hide known-obstructed pairs by default but retain an inspectable reason and highlight the obstruction if available.
  Add a per-layout manual Not physically measurable flag/reason; scanning cannot infer hand access or all obstacles.
- Store visibility assessment with source mesh fingerprint, tolerance and analysis identity. Rebuilding geometry or
  changing tag estimates invalidates it. Treat line-of-sight as a conservative filter, not a promise of tape access.

## Durable data and contracts

- Extend MeasurementDocument compatibly with optional/default-null `default_sigma_m` and any manual pair exclusions.
  Keep existing distances/text/source IDs. Missing sigma falls back only to an explicitly entered document default.
  Updates use the existing revision lock/atomic save; API edits preserve per-record overrides and unrelated records.
- Publish decoded original graph observations as a versioned derived `graph.json` per run, identifying node frames,
  original links, noise/information convention, source DB fingerprint and exported-frame mapping. Existing runs can
  extract it from their retained DB without re-fusing. No hardcoded tag IDs, van axes or capture names.
- Store immutable analyses under `.local/scan-analyses/<id>/`: request snapshot, corrected camera/tag poses, residuals,
  covariance summary/rank diagnostics, suggestions and provenance. Large matrices stay off routine UI responses.
- Keep accepted-analysis/history references in a separate project-adjacent `scan-solutions.json` keyed by source result
  and layout, with revision. Do not put user acceptance state into original run manifests or overwrite measurements.
- API proposal: POST `/scans/analyses` (run/layout/revision/settings), GET `/scans/analyses/{id}` (status/summary), POST
  `/scans/analyses/{id}/apply`, POST `/scans/analyses/{id}/revert`, POST `/scans/analyses/{id}/suggestions`. Paths use the
  existing `/api/v1` prefix. Register literal routes before generic filename routes. API serves only contained files.
- Apply validates run/layout/measurement revision, source graph/mesh fingerprints and expected solution revision;
  result changes cannot apply an old network to another capture. Persist units in metres; format millimetres in UI.

## Implementation sequence

### 1. Graph/noise prerequisites and GTSAM compatibility

**Files:** `pyproject.toml`, `uv.lock`, create `src/campervan/scan_graph.py`; extend `scans.py` at export only.
**Interface:** `extract_graph(database, frame_mapping) -> GraphDocument`; typed versioned nodes, links, information and
camera-to-optical transforms. GTSAM integration consumes this same document from CLI/API.

- [x] Confirm the official 4.3.0 Python 3.13 macOS binding exposes required Pose3/Between/Prior/range factors and joint
  marginals before pinning the optional scan dependency. Keep project Python unchanged; report a genuine incompatibility.
- [x] Decode original odometry/loop/tag/prior links and information matrices using RTAB-Map's supported version source.
  Account for translation/rotation tangent ordering, inverse-link covariance transformations and camera-local extrinsics.
  Handle supported gravity/prior links correctly; report unsupported/conflicting types without silently discarding them.
- [x] Deduplicate inverse representations, preserve actual original constraints and include graph nodes needed for
  connectivity even when their RGB-D frames were omitted. Retain explicit graph-to-optical exported-camera mappings.
- [x] Diagnose disconnected/rank-deficient data before fitting. No fabricated factors from pairs of saved global poses.

### 2. Precision editing and immutable joint analysis

**Files:** `scan_measurements.py`, `scan_measurements_api.py`, create `scan_analysis.py`, `scan_analysis_api.py`.
**Interface:** `analyse(graph, measurements, settings) -> AnalysisResult`; run/layout/revision-bound immutable solution.

- [x] Add compatible default precision plus per-pair precision updates and revision preservation; existing null fields
  must not become assumed high precision. Keep save/edit/remove semantics and cross-layout isolation intact.
- [x] Fit camera/landmark graph with physical range factors, weighted noise and a documented robust loss. Use saved
  poses as initial values. Remove global gauge with a reference frame, without claiming a physical absolute survey.
- [x] Compute before/after residuals, endpoint shifts, robust weights and joint covariance. Keep noise assumptions and
  linearisation limitations visible. Detect bad conditioning and avoid finite confidence for unconstrained motion.
- [x] Extend the existing scan subprocess owner for analysis status/logs with one active expensive task; no new service
  or auto-retry system. Fail visibly while preserving sources, measurements and previous accepted solutions.

### 3. Measurement side panel and preview

**Files:** create `frontend/src/side-panel.ts`; `scan-measure.ts`, create `scan-measure-panel.ts` and `scan-analysis-api.ts`;
extend `scan-tags.ts`, `scan.ts`,
`scan-library.ts` and `style.css` only at direct integration points.
**Interface:** `createSidePanel({ id, title, mode, onClose? })` returns the root element and stable context, actions,
status and body DOM slots, plus `open()` / `close()` and open-state access. Mode is explicitly modal or nonmodal.
The shared shell owns its native dialog, X close button, accessible title/name, Escape handling, focus restoration,
right-side overlay dimensions, scrolling and one-management-panel-at-a-time behaviour. Slots accept normal DOM;
no schema-driven forms, command registry or domain-specific data in the component. Opening a manager does not rebuild
its content or implicitly discard its draft. Close must support a caller-controlled focus destination for actions
that intentionally return to measurement entry/viewer inspection.

Measurement panel consumes measurement/analysis snapshots; tape controller retains selection/parser/save ownership;
tag overlay gains explicit set/clear analysis-preview and suggested-pair highlighting methods.

- [x] Extract the reusable side-panel shell from the current scan manager first. Put structure/layout/scrolling,
  header, accessible X, action/status/content slots and modal/nonmodal focus/dismissal behaviour in this component.
- [x] Migrate Manage scans to that shell, preserving search/filter, import controls, rename/delete confirmations,
  result selection and metadata-save semantics. Remove the superseded scan-specific shell CSS/close implementation.
- [x] Replace the old saved-list dialog with Manage measurements using the same shell: context and actions near the
  top, compact measurement list in its body. No second implementation of side-panel layout, X, Escape or focus logic.
- [x] Support precision editing, current-analysis status and before/after inspection. Preserve entered values, tape
  drafts, native writing, focus, numeric shortcut interception, camera and viewport dimensions.
- [x] Add proposed tag positions/movement vectors without moving the original surface. Identify the preview clearly;
  avoid showing camera-fixed tag movements as a fully corrected mesh.
- [x] Bind panel state to run/layout/revision; invalidate stale responses and keep pending previews out of fresh loads.

### 4. Apply/revert and corrected reconstruction

**Files:** extend `scan_analysis.py`, `scan_analysis_api.py`, `scan_processing.py`, `scans.py`, `cli.py`; create the small
`scan_solutions.py` store for accepted solution/history references.
**Interface:** `apply(analysis_id, expected_solution_revision)` starts an existing-pipeline reconstruction; `revert(...)`
selects the prior accepted/source result. Both validate ownership and immutable source identity.

- [x] Extend the existing corrected-pose seam to carry corresponding tag poses and exported-frame mapping. Never
  suppress landmarks in the corrected result or align them with incompatible camera coordinates.
- [x] Reuse retained RGB-D/calibration and existing Open3D cleanup/texturing with corrected optical poses. Publish a new
  manifest/assets under a fresh result ID with solution provenance and the same group/layout. Do not redo raw merging
  and obtain new node IDs after solving the original graph.
- [x] Recompute tag-based display alignment from the solution only when an explicit matching layout definition exists;
  otherwise retain a documented compatible scan frame. Never borrow the old trial's roles for interior-v1.
- [x] Apply/rebuild failures retain original geometry/accepted history; stale inputs reject with 409. Revert returns to
  the previous result without deleting any result or observation, including after a page reload.

### 5. Candidate scoring and physical clearance

**Files:** create `scan_suggestions.py`, `scan_visibility.py`; extend analysis API, panel and tag overlay.
**Interface:** `suggest_pairs(analysis, target_pairs, precision, threshold) -> SuggestionReport`; visibility consumes mesh
and tag locations plus explicit endpoint/clearance tolerance, returning classification/reason/optional hit location.

- [x] Enumerate all eligible pairs and calculate expected target uncertainty reduction using full joint covariance.
  Score every candidate independently; expose all qualifying rows, overlapping benefits and useful remeasurements.
- [x] Implement finite-segment ray tests and conservative Unknown handling with Open3D. Preview shifts relative to
  the source surface must affect trust in clearance, not be ignored. Check segment coverage against retained depth /
  calibration/poses so missing surfaces are not classified as clear. Respect manual blocked-pair flags.
- [x] Wire Suggest more and Measure pair to the existing tape flow. Editing/adding a measurement invalidates the old
  report. Explain empty lists: threshold, no new useful information, insufficient graph/noise data or physical blockage.

### 6. Documentation and acceptance

**Files:** `README.md`, `docs/photogrammetry.md` and this plan's execution record.

- [x] Document uncertainty assumptions, threshold meaning, Apply/Revert history, line-of-sight limitations, storage and
  independent-check workflow. Keep some physical measurements out of the optimisation to assess predictions.
- [x] Run focused existing Ruff/format/mypy and TypeScript checks only; fix introduced errors and classify known unrelated
  ones. Do not create/run tests, standalone verification scripts, services, browser interaction suites or review agents.
- [ ] Gert visually checks old/new layout isolation, all original distances preserved, side-panel/camera behaviour,
  analysis preview, stale Apply rejection, corrected result/revert after reload, all-pair suggestions, overlapping gains,
  blocked/unknown/clear examples, near-surface endpoints and manual tape-access exclusions.
- [ ] Compare independent physical checks before/after before describing predicted millimetre intervals as calibrated.

## Review focus

- A lower residual is not proof of higher physical accuracy; all confidence estimates must identify their noise model.
- Distance-only graphs can flex, and nearly planar tags can have weak out-of-plane information. Do not conceal this
  with rigid tag priors or an undiagnosed pseudoinverse. Use genuine scan observations and proper gauge handling.
- Raw distance records, accepted fitted positions and rebuilt geometry have distinct ownership and revisions. Revert
  never rewrites the first to match the second; deleted assets do not silently redirect to a different layout.
- Occlusion depends on physical segment geometry, reconstructed surface coverage and coordinate consistency. Mesh
  holes, endpoint contacts and unrebuilt preview positions cannot create confident false clearance.
- Candidate benefits overlap. The report lists all useful alternatives, not a promise that their individual gains sum.

## Sources and planning record

- [GTSAM 4.3.0 distributions](https://pypi.org/project/gtsam/): CPython 3.13 macOS wheel availability.
- [GTSAM marginals](https://borglab.github.io/gtsam/marginals/): joint covariance and nonlinear linearisation.
- [GTSAM robust noise models](https://gtsam.org/2019/09/20/robust-noise-model.html): robust weighting.
- [RTAB-Map SQLite implementation](https://github.com/introlab/rtabmap/blob/master/corelib/src/DBDriverSqlite3.cpp): source
  for version-specific link decoding; implementation must inspect the applicable version, not assume master matches.
- [Open3D RaycastingScene](https://www.open3d.org/docs/release/python_api/open3d.t.geometry.RaycastingScene.html): finite
  ray parameters/occlusion support. Published release docs currently identify 0.19; verify installed 0.20 signatures.
- [WAI modal dialogs](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) and
  [Chrome dialog guidance](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-components/dialog): labelled
  close controls and the distinction between modal and nonmodal focus behaviour.

Started 9 November 2026 01:15 UTC. Read existing measurement/panel/overlay/store/pipeline code, package declarations and
saved photogrammetry requirements. Inspected current measurement counts and retained SQLite Link schema read-only.
No application code, capture/measurement data, dependencies or services changed; no tests or browser interactions run.
The panel interaction, Apply-as-new-result and default improvement metric above are recommendations for approval.

### Design clarification — shared panel shell

Gert explicitly requires one shared UX component that accepts different scans/measurements content. Task 3 now extracts
that component before migrating both consumers. Sharing only CSS is insufficient. The component owns panel structure,
slots, close/accessibility/focus and dismissal; domain controllers retain their state, API operations and content.
This bounded reuse replaces the two current dialog shells without introducing a general UX framework.

## Execution record — 9 November 2026

Implemented inline after Gert's execution instruction. The shared panel shell is used by both managers; measurements
provides the analysis/acceptance/suggestion UX through its slots. GTSAM 4.3.0 was added to optional scan dependencies.
The joint optimiser, original graph export, precision editing, immutable snapshots, separate acceptance history,
corrected reconstruction and all-pair/clearance recommendations are connected through the existing subprocess owner.
README and photogrammetry documentation describe the implemented controls and limitations.

Ruff lint and format pass for the scan subsystem. Focused mypy passes 13 scan modules; integration checking still
reports only seven existing bare-dict annotations in unrelated api.py cutting endpoints. Frontend tsc still reports
only existing plan-dropdown.ts:82 TS2551. Passive app inspection shows the new toolbar action and retains interior-v1;
console has no warnings/errors. No tests, interaction suites, service starts, delegated reviews or commits were run.

No analysis/reconstruction was launched and no original measurement/capture/geometry data changed by implementation.
Gert must supply an explicit measuring-precision assumption and visually exercise the first fit/Apply/Revert/Suggest
workflow. Physical calibration with independent checks remains outstanding; model predictions are not fabrication
accuracy guarantees. Detailed implementation notes/rulings are in `.local/measurement-analysis-implementation.md`.

### UX correction — precision defaults and validation

Gert explicitly rejected disabled Analyse/Suggest buttons depending on fields below them. This supersedes the original
requirement to manually save an initially empty precision field before action availability. The UI now offers an
editable 3 mm default when no precision exists, keeps Analyse/Suggest available, validates on use and automatically
saves valid precision before proceeding. Save precision remains optional. Invalid/empty precision and threshold fields
show red borders, adjacent actionable errors and aria-invalid/aria-describedby; bad per-pair overrides are indicated
as well. A failed/conflicting save preserves the typed precision for explicit correction/retry. No precision is
persisted merely by opening the panel.

Applied [GOV.UK error-message guidance](https://design-system.service.gov.uk/components/error-message/): locate errors
beside the field, identify them visually and programmatically, explain how to correct them and retain entered values.
Frontend TypeScript still reports only existing plan-dropdown.ts:82 TS2551. No tests, service starts or browser
interaction flows were run.
