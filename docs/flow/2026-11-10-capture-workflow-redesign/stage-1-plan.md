# Stage 1 — Review capture: implementation plan

Status: implemented and source-reviewed; awaiting Gert's visual acceptance. [Flow folder](./) · [approved specification](spec.md).

**Goal:** Gert can inspect a reconstructed scene and tags, add capture databases to its group, explicitly reconstruct
again and inspect the new result using the same viewer. A basic tag-layout scan is sufficient.

**Architecture:** Replace the old workflow UI with the new shared-panel workflow shell, implementing only Review
capture. Reuse the existing renderer/camera, tag overlay, capture importer, library and native reconstruction jobs.
Retire the old workflow's reachable interface/API; retain domain input data and numerical/reconstruction machinery.

**Stack:** Existing TypeScript/Three.js frontend and local Python/FastAPI app; installed RTAB-Map CLI unchanged.

**Execution:** Work locally in the current directory/branch. Three tasks, implemented sequentially by the main agent.
No worktree, per-task reviewer, delegated implementation, tests, builds, lint campaigns or automatic later-stage work.
This plan overrides heavier generic Flow/sub-skill instructions. One accumulated source check and Gert's visual
review are the acceptance path. Estimated coding effort: 30–60 minutes, excluding Gert's capture/reconstruction time;
reassess if that estimate is exceeded rather than enlarging the work.

## Global constraints

- Authority: approved spec §§1–4, §10, §11, A1/A2/A9, plus Gert's explicit stage-by-stage delivery decision.
- Implement stage 1 only. No scene model execution/editor, axes changes, layout scores, tape-entry workflow,
  network fits or correction rebuilds. The full six-stage experience is not claimed complete.
- No automatic capture assessment, coverage maps, quality thresholds, before/after engine or viewpoint advice.
- No new dependencies, native compilation, model downloads, services or changes to native reconstruction algorithms.
- Preserve databases, source assets, processed results, layout definitions, reusable profile data and measurements.
  Only old workflow progress/reference metadata is discarded; no legacy parser, adapter, dual store or backup layer.
- Preserve unrelated dirty changes. At implementation start inspect the current diff of each planned file before
  editing; make the listed changes on top of the existing scan work. Never stage unrelated CAD/planner/data edits.
- Use `createSidePanel` unchanged: outside clicks stay open; X/Escape close. Preserve selectable text and camera state.
- Use the existing import progress/cancellation and interaction-generation handoff. Do not create another job poller.
- Do not run tests, browser interaction automation, builds or lint. Never start a service/browser. Gert starts any
  required process and performs visual acceptance. Source checks use `rg` and one final `git diff --check` only.
- For a genuinely new technical assumption, announce it and use one focused verification subagent before proposing
  it. Ordinary reuse already established by source inspection does not require a new investigation/review loop.
- All plans stay here as `stage-N-plan.md`; later stage plans are written only after Gert's feedback on this stage.

## Scope traceability

| Criterion | Stage-1 scope | Owner and focused evidence |
| --- | --- | --- |
| A1 | New shell, Review capture active; remaining five stages visibly upcoming, no old navigation or fake stage screens | T1 source inventory; Gert opens Review capture |
| A2 | Visual reconstruction/tag inspection and cumulative add/reconstruct loop, including a basic capture | T2/T3 source tracing; Gert imports or reuses databases and inspects the result |
| A9 | Retire old workflow UI/API; shared shell/renderer retained; source/input data remain usable | T1 direct-reference searches and cutover inventory; T3 accumulated diff inspection |
| §3/§10 | Camera/result selection, group/layout context and successful-result handoff remain coherent | T2/T3 source tracing; Gert changes results, reloads and adds captures |
| A3–A8 | Deferred to the relevant later stage plans, except the stage-1 shell and preserved input contracts | Not verified or claimed complete by this plan |

There is no automated integration gate for this hobby-project change. Final integration evidence is one source
inspection of the accumulated changes and Gert's visual checks below. No extra reviewer/task gate is authorised.

## Existing behaviour and exact reuse points

- `frontend/src/scan.ts:setupScan` already loads mesh/colour/photo/cloud layers, applies saved tag alignment, creates
  `createScanTags`, preserves `CameraState` through `loadLayer`, and stores selected result/layer. Keep these paths.
- Its `importCompleted` callback already distinguishes safe automatic handoff from a completion announcement when
  Gert has navigated away. Preserve that policy; do not simplify it into unconditional selection of a finished job.
- `scan-library.ts:createScanLibrary().addCaptures(resultKey)` resolves the existing group and opens the importer.
- `scan-import.ts:createScanImport().open` already selects imported databases in that group; `start()` uploads new
  files and sends the selected cumulative IDs to `processCaptures`. It currently defaults layout from the group,
  rather than necessarily the displayed result. The explicit stage-1 path must pass the current result's layout.
- Import completion currently calls `createWorkflow` before handing off. Remove this dependency on the old workflow;
  failure to create old workflow metadata must no longer hide a successfully reconstructed result.
- `scan_processing.py:ScanProcessing.start` checks group membership, layout identity and duplicate capture IDs, then
  creates a new result. No new reconstruction endpoint or importer is needed.
- The old workflow's only frontend entry owner is `createScanMeasure`; the only HTTP registration is
  `api.py:build_app` calling `register_scan_workflows`. Remove those old interface paths as part of the cutover.

## Task 1 — Replace the old workflow with the stage-1 shell

**Spec coverage:** A1 (stage-1 portion), A9, §§1/3/4/10.

**Files:**

- Create `frontend/src/scan-workflow-panel.ts`.
- Modify `frontend/src/scan.ts`, `frontend/src/scan-tags.ts`, `frontend/src/style.css`.
- Delete superseded UI/orchestration files: `scan-measure-panel.ts`, `scan-measure.ts`, `scan-measure-session.ts`,
  `scan-measure-row.ts`, `scan-tag-confidence.ts`, `scan-workflow-api.ts` under `frontend/src/`.
- Modify `src/campervan/api.py`; delete `src/campervan/scan_workflow_api.py`.
- Modify only the old `Stage` literal in `src/campervan/scan_workflow_models.py` to the six approved IDs. Keep source
  binding, profile, artifact and other types/functions still consumed by numerical/rebuild modules.
- Cutover data: clear only the `workflows` member in the existing project-owned `data/scan-workflows.json`, if present,
  preserving `profiles` and document metadata. Do this once during implementation using the declared uv environment,
  not through a startup migration/fallback. Do not read/delete artifact directories or measurement/source files.

**Interfaces:**

```ts
interface CaptureReviewHost {
  capture(): ScanResult | undefined;
  loading(): boolean;
  addCaptures(): Promise<void>;
}
// scan-workflow-panel.ts; reuse ScanResult from scan-library-api.ts.
export function createScanWorkflowPanel(host: CaptureReviewHost): {
  openReview(): void;
  refresh(): void;
  hide(): void;
};
```

- [x] Create the panel using `createSidePanel({ id: 'scan-workflow', title: 'Review and improve scan' })`.
  Show `Step 1 of 6 — Review capture`, the actual result/group name once, and one primary `Add capture databases…`
  action. Short copy: `Inspect the reconstruction and detected tags. Add more captures if you need more detail.
  A basic scan is enough to start checking tag placement.` Do not recreate a detected-tag chip grid or generic
  navigation tutorial. Existing viewer controls and tag visibility remain the inspection tools.
- [x] Define the six approved stage names/IDs once in this panel. Stage 1 is current; stages 2–6 are noninteractive
  upcoming labels with the accessible explanation `Available in a later stage of this workflow's implementation`.
  No clickable empty pages or enabled Continue-to-scene action. The next plan replaces stage 2's unavailable state.
  This is staged delivery, not a precision/completeness gate. Do not claim the six-stage process is complete.
- [x] Replace `createScanMeasure` in `setupScan` with the new panel. Create a `Review capture…` toolbar button using
  existing toolbar sizing. Remove the old tape icon, measurement-entry status bar, old keyboard handlers and manager
  wiring. They return only through later approved stages, not through hidden old UI. Persisted distances remain intact.
- [x] Replace `measure.*` call sites in `scan.ts` with panel `refresh/openReview/hide` where relevant; remove measurement
  session reads, flush/unsaved checks and `reload` calls that are no longer relevant to a read-only stage. Keep the
  existing camera methods, asset loaders, tag rendering and load-generation guards. Do not replace the renderer.
- [x] Remove the deleted confidence module's import/state/`setConfidence` presentation from `scan-tags.ts`; retain
  tag outlines, IDs and the single shared highlight owner. Remove only CSS selectors belonging to deleted workflow
  views/status bars. Keep shared panel, toolbar, scan-library and tag-selection styling.
- [x] Remove `register_scan_workflows` and `ScanWorkflowStore` imports/initialisation from `api.py`; delete the old
  route module, not the independent measurement/layout/import/library APIs. Keep domain numerical modules and their
  directly used artifact/source types. No replacement workflow HTTP API is needed for read-only stage 1.
- [x] Change the retained Python Stage literal to `review_capture`, `understand_scene`, `improve_layout`,
  `take_measurements`, `check_measurements`, `update_reconstruction`. Discard old workflow progress once, preserving
  reusable `profiles`. Do not convert old stages or create new workflow records during import.
- [x] Source-check remaining imports/calls with `rg -n 'createScanMeasure|createWorkflow|register_scan_workflows|scan-measure-panel|scan-measure-session|scan-workflow-api|scan-tag-confidence' frontend/src src/campervan`.
  Resolve direct dangling references caused by these deletions only. Other domain measurement/rebuild functionality
  is retained for later stages, not refactored in anticipation of them.

## Task 2 — Keep add-capture context and reuse the existing importer

**Spec coverage:** A2, A9 input preservation, §§4/10.

**Files:** `frontend/src/scan-import.ts`, `frontend/src/scan-library.ts`, `frontend/src/scan.ts`.

**Direct contract change:** extend the current importer, do not wrap it with a second upload flow.

```ts
// Existing third argument remains File[] for library drag-and-drop.
open(id: string, label: string, incoming: File[] = [], layoutId?: string): Promise<void>
```

- [x] Extend `createScanImport().open` with the optional explicit layout ID. `createScanLibrary().addCaptures(resultKey)`
  looks up the current `ScanResult` and passes its `tag_layout_id` as that fourth argument. Calls from group management
  continue to use the group's default layout; drag-and-drop retains its existing third argument. This is explicit
  invocation context, not a compatibility branch or new persisted state.
- [x] When an explicit current-result layout is provided, select it instead of the group default. If unavailable,
  display the actual error and require a deliberate layout selection; never silently create a new layout. Keep the
  existing explanation that moved tags require a different layout. Do not implement tag revision UI in stage 1.
- [x] Preserve the existing imported-database checklist and cumulative selection. Keep the selection visible and
  editable: group members may include scans from another layout. Gert chooses only databases from the unchanged
  physical arrangement. No automatic inference that every database in a group has the same tag arrangement.
- [x] Keep `start()` using `{ group_id, capture_ids, layout_id, name, settings }` through the existing process endpoint.
  Preserve duplicate upload handling, native settings, cancellation and job progress. No processing starts merely
  from opening the panel or adding a file. Remove `createWorkflow` from the completion callback; pass successful
  results straight through the existing completion host callbacks.
- [x] Use the current `addCaptures` group-resolution behaviour for ungrouped/loose results: open Manage scans with its
  existing actionable explanation, rather than inventing a group. Missing tags are not an error for visual inspection.
- [x] Source-trace both call paths: group/drop import and current-result add-capture. Verify that only the latter
  supplies the explicit current layout and that neither changes measurement documents for an existing layout.

## Task 3 — Complete handoff, factual docs and visual acceptance

**Spec coverage:** A1/A2/A9 stage-1 scope, §§3/4/10.

**Files:** `frontend/src/scan.ts`, `frontend/src/scan-workflow-panel.ts`,
`docs/photogrammetry.md`, `docs/flow/2026-11-09-scan-measurement-workflow/README.md`.

- [x] Adapt existing `importCompleted` handoff to open stage 1 on the newly loaded result. Preserve the interaction
  and scene tokens so navigating to another result/tab during processing or asset loading takes precedence. If
  automatic handoff is no longer appropriate, show the existing explicit `Review capture` completion action.
  Failed/cancelled processing leaves the current result available with the existing job error/progress presentation.
- [x] Keep `sessionStorage` result/layer selection and existing `CameraState` persistence. Panel refresh follows
  `renderedScan`, not a future selected-but-unloaded result. No geometry-fit or view reset on panel open/close,
  cumulative reconstruction handoff or result/layer selection. Use existing latest-load generation/disposal logic.
- [x] In `docs/photogrammetry.md`, replace the obsolete four-stage UI instructions with the approved six-stage outline,
  marking only Review capture implemented. Explain basic scan -> visual review -> add databases -> explicit process
  -> inspect result, followed by later detailed capture after layout work becomes available. Document the deliberate
  temporary absence of the old measurement UI and preservation of physical data; no old-workflow fallback instructions.
  In the older scope index, link to the new approved spec and this stage-specific plan as the active workflow change.
- [x] Perform one accumulated source review restricted to these tasks: closed imports, no old reachable UI/API,
  group/layout context, unchanged source/measurement writes, shared shell behaviour, guarded completion and preserved
  camera. Run `git diff --check` once; no tests, build/lint, service launch or automated browser interaction.
- [x] Commit only the stage-1 code/docs and explicit workflow-progress cutover. Record what was source-checked and
  what awaits Gert. Do not mark visual or real capture acceptance complete until Gert reports the result.

### Gert's visual acceptance (not an automated test suite)

In Gert's existing app, with services started by Gert if needed:

1. Open a reconstruction: mesh/texture and tags remain visible, Review capture opens the shared side panel, and the
   five later stages are clearly upcoming. No old measurement/analysis workflow is offered.
2. Orbit/pan/zoom, toggle tags or switch result/layer; the panel and existing result controls remain coherent. X and
   Escape close the panel; a canvas click does not. The view is not reset by panel or result changes. Reload retains
   the selected result/layer and camera through the existing persistence behaviour.
3. Add databases from Review capture: the same group and current tag layout are selected, imported databases remain
   selectable, and explicit Process captures runs the existing job with progress/cancellation. A completed result
   appears in the same group; the old result remains selectable. Inspect whether the added capture helped.
4. If Gert navigates away during processing, completion offers Review capture rather than taking over that view.
   No scene understanding, layout analysis or network fit runs automatically.

No new capture is mandatory solely to review the UI: existing imported databases can be explicitly reprocessed if
Gert chooses. The agent does not start that processing on Gert's behalf during implementation verification.

## Stop condition and handoff

Stage 1 is ready when T1–T3 are implemented/source-checked and the result is presented for Gert's visual inspection.
Stage 1 is accepted only after Gert's feedback. Do not run the full six-stage programme, create stage-2 tasks, execute
scene recognition, or automatically proceed into another plan. If Gert requests changes, amend stage 1 first.

Single plan self-review: confirmed stage-1 traceability, current reuse points, direct API/caller removal, optional
layout argument compatibility with existing drop callers, preservation of input/profile data, and the explicit
absence of tests/services/per-task reviews. No external plan-review pass is required.
