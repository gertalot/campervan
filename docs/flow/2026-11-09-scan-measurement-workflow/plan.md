# Measurement workflow implementation plan

> For implementers: execute only after `flow:implement` is invoked. Repository instructions override generic testing,
> worktree and verification defaults. This document is planning, not authority to start processing or install packages.

**Goal:** turn the existing tape/measurement manager into Review capture → Measure → Check accuracy → Update
reconstruction, with independent physical-network assessment and explicit scan correction.
**Architecture:** retain the existing measurement/layout stores, processing worker, native importer, renderer and
reconstruction. Add scan-local typed workflow/artifact persistence, a position-only physical-network calculation,
and one shared measurement session/editor and job view. Evolve the existing panel rather than adding another one.
**Stack:** existing Python 3.13/uv, FastAPI/Pydantic, GTSAM 4.3.0, NumPy/SciPy/Open3D and TypeScript/native DOM.
PyRigi 1.3.0 is the selected optional scan dependency for generic 3D graph rigidity.
**Flow folder:** [measurement workflow](./). **Spec:** [spec.md](spec.md).
**Shared contracts:** [C1–C5](shared-contracts.md). **Related scene contract:** [scene-review-design.md](scene-review-design.md).

## Global constraints and current baseline

Implementation status: Tasks 1–6 and the practical documentation are implemented and source-reviewed. Checked boxes
record source implementation, not runtime acceptance. The unchecked real-job and manual inspection items remain
pending Gert's existing app; no tests, browser automation or reconstruction jobs were run for acceptance.

- Spec §§2–12 and M1–M11 are binding. In particular, captured coordinates initialise/orient the physical fit but
  are absent from its objective and information matrix. Independent measurement assessment cannot Apply a mesh.
- No tests, fixtures, test infrastructure, services, browser automation, model runs or capture processing during
  planning. Implementation uses existing runtime validation and Gert's existing app for acceptance. Do not introduce
  test/verification processes, full-project builds or broad lint/type campaigns contrary to AGENTS.md.
- No native compilation or new native packaging. Use the implemented installed RTAB-Map CLI resolver and optional
  `CAMPERVAN_RTABMAP_BIN_DIR`; preserve its scoped macOS library environment and Linux discovery semantics.
- Existing GTSAM/Open3D/OpenMVS algorithms stay. No new optimiser, mesher, frontend framework, service, queue,
  readiness/retry system or app-wide ownership change. One expensive action uses `ScanProcessing.start_action`.
- Preserve originals, entered physical values, saved layouts, existing result assets, group deletion/moves, source/corrected
  grouping, active input, focus, camera position/projection/zoom and the existing single reference-transform owner.
- Replace the old workflow directly. Do not add legacy-artifact readers/adapters, compatibility exports, old/new
  modes or rollback/acceptance-history machinery. Remove superseded routes, UI and consumers. Existing capture and
  measurement data remain intact; obsolete analysis/history files need not be read, migrated or deleted.
- The working tree already contains capture-group/delete/move/lineage and camera-preservation edits. Those working
  versions are the substrate, not unrelated defects to roll back. Before implementation record HEAD and hashes of
  owned working files; preserve user data changes/deletions separately. Do not commit unrelated working data.
- Stage/review completion and precision goals are advice, not permission gates. Incomplete or uncertain work may
  proceed to an explicitly labelled best-effort correction. Missing input may prevent only its specific calculation.
- No region recognition/editor/model installation in this scope. Scene supplies source-bound reviewed context later;
  measurement foundations own its schema/store/freshness and optional consumer seams once. Missing context is explicit.
- All tag IDs, coordinates, roles, dimensions, layouts and paths are data. Defaults are visible/editable: 3 mm typical
  range sigma, 5 mm longest 95% positional-ellipsoid semi-axis target, separate 5 mm meaningful-improvement threshold.
- Reuse evidence for unchanged inputs. Task 7 owns integrated manual acceptance; earlier tasks own their code and
  existing runtime checks only. A reviewer does not trigger another reconstruction or invented verification gate.

## Scope traceability

| Criterion | Implementation | Final evidence owner/action in Gert's existing app |
| --- | --- | --- |
| M1 import handoff | 1, 2, 6 | 7: Process captures completion / Review capture, including changed selection/edit |
| M2 placement advice | 4, 6 | 7: Review placement; inspect reasons, coverage and comparable effort/precision |
| M3 physical completeness | 3 | 7: Check measurements on actual partial network; inspect missing modes/status |
| M4 direct entry/shared tape values | 2, 6 | 7: checklist entry → tape/saved list; same acknowledged values |
| M5 normal editing/save failures | 2 | 7: Enter/blur/Escape, invalid text and visible unsuccessful-save state |
| M6 shared components | 1, 2, 6 | 7: four stages, row contexts and import/analysis/rebuild job views |
| M7 separate report meanings | 3, 5, 6 | 7: Check accuracy versus Preview corrections; no scan priors in physical report |
| M8 one all-useful-pairs planner | 4 | 7: Generate checklist / Suggest more; all useful alternatives and access reasons |
| M9 reload/layout safety | 1, 2, 6 | 7: reopen/reload; explicitly revised layout retains only confirmed fixed pairs |
| M10 explicit new reconstruction | 5, 6 | 7: Preview corrections → Update mesh → Show original; originals/values retained |
| M11 retained data/navigation | 1, 2, 5, 6 | 7: existing capture/measurement assets, group actions, tape and camera navigation; old-workflow compatibility explicitly waived |

These actions are acceptance scenarios, not instructions to create tests or automate the browser. Use real saved
inputs; do not edit their physical measurements merely to manufacture cases. Unavailable scenarios remain unverified.

## Ownership and closed file map

| Path | Responsibility |
| --- | --- |
| `scan_workflow_models.py` (new backend) | Typed workflow/profile/source-binding/artifact and pair contracts |
| `scan_workflows.py` (new backend) | Project-adjacent revisioned store and one fingerprint/freshness policy |
| `scan_workflow_api.py` (new backend) | Workflow reads/edits/action eligibility using existing stores/job owner |
| `scan_network.py` (new backend) | Independent Point3 range fit, completeness, consistency, free-network covariance |
| `scan_suggestions.py` (extend) | One physical candidate enumeration/scoring/batch/reverse-deletion engine |
| `scan_placement.py` (new backend) | Placement report comparing networks through that engine |
| `scan_visibility.py` (extend) | Existing finite-segment mesh/depth check plus optional reviewed source context |
| `scan_analysis.py`, `scan_analysis_api.py`, `scan_analysis_worker.py` | Reused joint-correction math, new typed dispatch; remove superseded analysis API |
| `scan_context_factors.py` (new backend) | Optional reviewed structural-relationship consumption in joint correction |
| `scan_rebuild.py`, `scan_reconstruction.py` | Existing corrected RGB-D fusion, optional source masks, provenance |
| `scan_measurements.py`, `scan_measurements_api.py`, `scan_layouts.py` | Existing physical store/API; revised-layout fork |
| `api.py`, `scan_processing.py`, `scan_solutions.py` | Inject workflow store, reuse jobs/lineage; remove obsolete rollback-history owner |
| `scan_groups.py`, `scan_library_api.py` | Direct callers: remove obsolete solution-history dependencies when that owner is retired |
| `scan-measure-session.ts` (new frontend) | One mutation queue/document/draft/save-state owner per physical layout |
| `scan-measure-row.ts` (new frontend) | Shared pair entry, precision, exclusion and save feedback component |
| `scan-job-status.ts` (new frontend) | One presentation/polling subscription owner for existing jobs |
| `scan-workflow-api.ts` (new frontend) | Typed workflow/artifact/action API; no independent eligibility rules |
| `scan-measure-panel.ts` (evolve), `scan-measure.ts` | Four-stage panel composition; tape delegates to shared session |
| `scan.ts`, `scan-tags.ts`, `scan-import.ts`, existing API modules/CSS | Workspace handoff, highlights, existing import/view integration |
| Root `pyproject.toml`/`uv.lock`, README/photogrammetry docs | Scan-only dependency declarations and factual workflow setup |

Backend paths above are under `src/campervan/`; frontend paths under `frontend/src/`. This inventory is not authority
to refactor entire files. Keep unrelated CAD/planner/native-runtime owners unchanged. New components replace their
superseded in-file responsibility; do not leave parallel save paths, pollers or scoring implementations.

## Shared contracts fixed before implementation

### Store and wire data

`ScanWorkflowStore(path)` receives `project_path.with_name("scan-workflows.json")` in `api.build_app`. Reuse the
existing local lock, expected revision, validated read and sibling `.tmp` replacement pattern. No env variable is
required. Missing store means an empty v1 store; malformed existing content is an error, never an empty replacement.

```text
WorkflowDocument v1: revision, profiles{profile_id: immutable ProfileRevision[]}, workflows{workflow_id: Workflow}
ProfileRevision: profile_id, revision, layout_id, context_text, target_classes, relationships, tag_references
Workflow: id, source_run_id, layout_id, group_id, profile_ref|null, source_binding|null,
          stage, target_mm=5, improvement_mm=5, candidate_sigmas{}, checklist_batches[], artifact_refs{},
          corrected_run_id|null, review_decisions
Stage: review_capture | measure | check_accuracy | update_reconstruction
ChecklistBatch: id, kind(initial|additional|recheck), ordered_pairs[], current_pair|null, producing_artifact_id
Pair: canonical positive tag_a<tag_b; candidate precision overrides use "a:b" keys
ArtifactKind: measurement_network | measurement_plan | placement_review | context_review | scan_correction
ArtifactEnvelope v1: id, kind, algorithm_version, workflow_id, source_run_id, layout_id,
                    measurement_revision, profile_ref|null, fingerprints{}, assumptions{}, job_id, payload
ArtifactStatus: current|stale|unavailable, reasons[], available_actions[]
```

Store original physical distances only in `MeasurementStore`. Artifact snapshots may record their immutable input
snapshot, never replace authoritative values. Store authoritative checklist order/progress, not duplicate distances.
A workflow refers to its source; corrected results resolve through `source_run_id`/`reference_run_id` in the source
manifest to that workflow. Different source captures get distinct workflows sharing the physical layout.
Reads derive current group from source library membership; renaming/moving groups does not alter numerical freshness.
Missing/deleted source gives Unavailable while physical observations/profile remain preserved.

`SourceBinding` belongs to one source run and reviewed profile revision. Its region IDs and support reference original
frame IDs and relative mask/source-element assets, optional observed XYZ support, reviewed labels and correction
revision. `ReviewedRelationship` carries kind, participating region IDs, enabled, explicit angular/linear sigma,
units and supporting association references. Missing sigma/support makes it inactive with a reason. `CleanupMask`
references source frame ID plus original-pixel mask asset and its revision, never only world XYZ. Models validate
local relative assets/source ownership. The scene scope produces/edits this content later; no substitute editor here.

### One content-based freshness policy

Canonical SHA-256 inputs use sorted pair/ID ordering and JSON with sorted keys and finite numbers. Revisions protect
writes and record provenance; they are not automatically included in every content dependency. Include algorithm
versions and relevant settings in each fingerprint. On action and read, the same backend policy returns eligibility
and reasons; frontend renders those responses and adds only local unsaved/saving input state.

| Artifact | Content dependencies |
| --- | --- |
| measurement_network | active tag IDs/layout, entered ranges/effective sigmas, robust/numerical algorithm settings |
| measurement_plan | physical inputs/network, planning positions, source mesh/depth/poses, access exclusions, candidate sigmas, targets/thresholds, reviewed context when used |
| placement_review | planner inputs, retained coverage, tag observation support and available reviewed context |
| context_review | source geometry/RGB-D/poses, profile revision/content and source-specific review/masks/model settings |
| scan_correction | original graph/optical data, physical observations, registration settings, enabled reviewed relationships/masks |

Physical-fit canonical coordinates are independent of display axes; registration to a new scan is separate. Changing
source shape does not invalidate an otherwise identical physical fit. Changing access exclusions does not invalidate
physical consistency; changing scene labels does not invalidate measurement-only uncertainty. Stale artifacts remain
inspectable, but stale correction cannot be applied. Only new typed artifacts participate in this workflow. No
legacy scan-assisted analysis reader, migration, adapter or compatibility label is implemented.

### Existing jobs and new action routes

Reuse `ProcessingJob` and `ScanProcessing.start_action`, with source group lineage. Numerical/report actions retain
`kind="analysis"` so existing publication handling does not mistake them for reconstructed runs; carry `artifact_kind`
separately. Rebuild retains `kind="rebuild"`. One existing worker CLI dispatches to the new functions and writes
immutable artifacts in its action directory. Register workflow routes once through `api.build_app`.

| Route | Request / response |
| --- | --- |
| `POST /api/v1/scans/workflows` | source_run_id, layout_id → existing-or-new WorkflowView; no source mutation |
| `GET /api/v1/scans/workflows/{id}` | workflow, current document references, derived stage states, ArtifactStatus and jobs |
| `PATCH /api/v1/scans/workflows/{id}` | expected workflow revision plus stage/settings/checklist/review edits → acknowledged view |
| `POST /api/v1/scans/workflows/{id}/actions/{action}` | current workflow revision and relevant acknowledged input revisions → job/artifact ID |
| `GET /api/v1/scans/workflows/{id}/artifacts/{artifact_id}` | typed envelope and current freshness status; validate workflow ownership |
| `POST /api/v1/scans/layouts/{id}/revise` | new layout definition and explicit unchanged/moved/removed/added tag sets → new layout |

Actions are `review-placement`, `plan-measurements`, `check-measurements`, `suggest-more`, `preview-correction` and
`update-mesh`. Backend captures authoritative input snapshots/fingerprints at dispatch and rechecks before publishing
current status/applying correction. A failed action leaves the previous successful artifact intact. Stage states
Not started/In progress/Complete/Needs updating come from artifacts/review decisions, not unrelated saved booleans.

## Task 1: Workflow/artifact persistence and API foundation

**Spec coverage:** M1, M6, M9, M11; shared C1–C5.

- [x] Implement the typed models/store/freshness table above in the three new workflow modules. Store profile versions
  append-only; source review and physical-layout revision are separate. Lazily create workflows for existing runs;
  keep captures/measurements intact without adapting obsolete analyses/history. Validate IDs/asset ownership using
  existing scan path mechanisms.
- [x] Register the listed read/create/edit/artifact routes with the existing library/layout/processing
  instances. Extend `scan-workflow-api.ts` with the same discriminated unions and `ProcessingJob.group_id` nullability.
  UI consumers must narrow by kind; a measurement report has no camera-pose requirement.
- [x] Implement revised-layout fork in `ScanLayouts`: validate disjoint tag-change sets, including all known tags
  involved in preserved observations. Copy only pairs with both endpoints explicitly confirmed unchanged, retaining
  entered_text, sigma and original source provenance. Retain old layout/documents. Context/tag references touching
  changed tags need reconfirmation; never copy old source masks or silently rebind old runs to the revised layout.
- [x] Wire action dispatch metadata to the existing worker, initially reporting unsupported producers as unavailable
  until their owning tasks land. Keep no completed placeholder reports. Delete/missing-source reads preserve saved
  physical observations/context; reuse current group movement/deletion behavior rather than creating another owner.
- [ ] Focused evidence: inspect actual workflow create/read/edit and revised-layout acknowledgements through Gert's
  existing app when Task 6 exposes them. The implementation uses model/runtime checks on normal requests. Do not
  invoke standalone test scripts or migrate saved data on application startup.

## Task 2: Shared mutation session, pair row and job view

**Spec coverage:** M4–M6, M9, M11.

- [x] Move `parseDistance` unchanged into `scan-measure-session.ts` and update direct imports; no compatibility re-export.
  Keep mm/cm/m/in/ft, positive finite validation and bare-mm behavior. Create one session per active layout and reuse
  it across tape, saved rows, checklist/rechecks, default/pair precision and exclusions. Remove direct mutation calls
  from `scan-measure.ts` and `scan-measure-panel.ts` as each is routed through the session.
- [x] Session interface: `document`, `draft(pair)`, `setDraft(pair,text)`, `commit(pair)`, `remove(pair)`,
  `configure(change)`, `flush()`, `subscribe(listener)`. One promise queue sequences every authoritative mutation;
  acquire the latest acknowledged measurement revision when sending, not when enqueuing. Associate source/layout
  identity with each operation so a response after source switching cannot overwrite another document's state.
- [x] Deduplicate Enter/blur per pair/value, keep pending drafts editable, and distinguish Saved/Saving/Not saved.
  Acknowledgement advances the baseline only for its submitted value; newer draft text survives. On 409, refresh the
  authoritative document without losing the draft; expose explicit retry. Failures do not count toward completion
  or silently allow analysis of draft values. `flush()` reports remaining unsaved/errors and focuses the relevant row.
- [x] Implement `scan-measure-row.ts` once: canonical pair, separately labelled Scan estimate, physical input, sigma,
  Save/highlight and Cannot measure reason. Empty physical input stays empty. Enter saves then advances after ack;
  valid changed blur saves; Escape restores the last saved text before panel handling. Preserve selection/paste/IME
  and prevent numeric/T/Escape leakage into renderer shortcuts. Values for absent tags remain visible/unavailable.
- [x] Persist acknowledged checklist order/current row through the workflow API; keep uncommitted drafts in the
  shared session across panel/stage switches. A beforeunload warning applies only when those drafts could be lost.
  Polling/status updates patch existing keyed DOM rows rather than rebuilding active editors or changing order/scroll.
- [x] Extract `scan-job-status.ts`: one subscription/polling presentation owner keyed by existing job ID, actual stages,
  error/log tail and explicit retry callback. Adapt `scan-import.ts` and the evolving measurement panel to it and
  remove their duplicate timers/status rendering. Preserve file upload progress from XHR as actual upload progress.
- [ ] Focused acceptance owner: Task 7 checks direct row/tape agreement, save/error feedback, normal editing, reload
  and reused job views in the existing app. No new polling service, framework, browser automation or tests.

## Task 3: Independent physical-network fit and rigidity

**Spec coverage:** M3, M7, M9.

- [x] Add `pyrigi==1.3.0` only to the scan extra, and declare directly used NumPy/SciPy at the currently locked
  compatible versions (currently 2.5.4/1.18.1), without unrelated upgrades. Regenerate the lock. Use
  `uv sync --locked --extra scan --no-build` for installation so third-party native source builds cannot start.
  PyRigi's own `py3-none-any` wheel exists (166,894 bytes); its mandatory notebook/plotting dependencies must be
  included in the resolution/footprint record even though their UIs are unused. No extras are needed. If Python 3.13
  resolution/binary availability fails, report it; do not vendor a rigidity algorithm or compile the dependency chain.
- [x] Implement `analyse_network(run, measurements, settings, output)` in `scan_network.py`, exposed by the existing
  worker's `check-measurements` dispatch. Select detected active tag IDs; retain but explicitly count measurements
  involving absent tags as inactive. An empty/sparse network returns completeness diagnostics, not a solver error
  claiming the distances are wrong. Use sorted positive tag keys and Point3 values.
- [x] Build range observations with `gtsam.RangeFactor3(key_a,key_b,distance_m,noise)`. Keep Huber k=1.345 and
  effective sigma=`pair_sigma or document_default`, reporting model/weights. Use captured tag positions solely for
  initial coordinates and a display mirror convention. No Pose3 scan graph, gravity/plane priors or captured-position
  residual belongs in this graph. Solver damping is not physical information.
- [x] Numerical gauge: choose deterministic separated/noncollinear anchor tags from the initial coordinates. Translate
  anchor A to zero, rotate B onto +X and C into XY. B's X and C's X/Y remain unknown. Use constrained point/partial
  coordinate factors only to fix global translation and rotation during optimisation: A xyz=0, B yz=0, C z=0.
  GTSAM `PriorFactorPoint3` plus two small `CustomFactor` coordinate selectors suffice; do not reimplement range
  residuals/Jacobians. For fewer available noncoincident/noncollinear anchors constrain only the supported gauge,
  report inadequate 3D geometry, and leave internal modes unbounded. Coincident positions produce an explicit
  conditioning diagnostic instead of invented metric perturbations.
- [x] Separate solver gauge from reported information. At fitted positions, reuse the existing `pair_jacobian` in a
  neutral helper consumed by both correction/planning. Build whitened rows with `sqrt(Huber weight)/sigma` and the
  rigid-motion generator (common translations plus rotations of centred coordinates). Orthonormalise its actual
  span, then obtain complement Q. Use SVD of `A=J_weighted @ Q`, not squared information, for rank/conditioning.
  Record a shared numerical rank tolerance `rtol=1e-9`; this is an algorithmic setting, not a physical tolerance.
  Report singular values/condition number and flag a nonzero shape singular-value ratio below `1e-8` as poorly
  conditioned. Record both tolerances with the algorithm settings; do not call a threshold-truncated mode precise.
- [x] If A has remaining null modes, retain their basis and report unbounded/unknown uncertainty. Never invert only
  its positive modes to show finite whole-network precision. For full column rank, compute
  `C = Q @ V @ diag(1/s**2) @ V.T @ Q.T` from the full shape SVD. No gauge factors, scan factors or damping enter C.
  This is the equal-weight, orthogonally aligned free-network convention for all planning/comparisons. Reassess
  effective rank after robust weights; report near-singular conditioning and nonlinear ambiguity separately.
- [x] Construct PyRigi with `Graph.from_vertices_and_edges(sorted_ids, sorted_unique_edges)` to preserve isolated
  tags; call `.is_globally_rigid(dim=3, algorithm="randomized", prob=1e-4)`. Seed Python's stdlib `random` in the
  isolated worker with a recorded content-derived seed, not only NumPy. Cache identical topology results within the
  job. Record package version, graph, seed, algorithm and bounded false-negative qualification. Generic topology
  certification is separate from actual geometry, which must span 3D with at least four independent tag positions.
- [x] Publish separate completeness, consistency and uncertainty payloads. Residual sign is fitted−entered; retain
  standardised residuals/robust weights and warn when redundancy cannot check errors. For finite 3×3 tag blocks,
  use `sqrt(chi2.ppf(.95,3)*eigenvalues)` for 95% ellipsoid axes; longest semi-axis determines the worst tag/target.
  Use 1.96 only for one-dimensional range intervals. Unknown/unbounded values use explicit status/null, not JSON NaN.
- [ ] First normal Check measurements job records dependency import/version, timing and model diagnostics. Do not
  run synthetic networks, package smoke-test scripts or separate benchmark/verification processes. Unavailable
  PyRigi means generic status Unknown and no claim of completion; the dependency failure remains visible.

## Task 4: One pair planner, additional suggestions and placement assessment

**Spec coverage:** M2, M8; consumes Task 3's same uncertainty/gauge convention.

- [x] Extend `scan_suggestions.py` into the one engine: `enumerate_pairs`, `score_addition`, `select_batch`,
  `plan_measurements`, `suggest_more`. Enumerate every canonical active-tag pair; keep saved observations immutable,
  distinguish measured/recheck/proposed pairs and apply manual exclusions as a separate reason/status. Replace the
  old pair-to-pair uncertainty improvement ranking outright; do not retain a legacy reader or alternate scoring mode.
- [x] Reuse `assess_segments` for actual finite tape paths. Extend its outputs with Manually excluded rather than
  pretending an exclusion is an observed obstruction. Keep Obstructed/No obstruction detected/Unknown, hit/reason and
  observed coverage. Mesh miss alone is Unknown. Unknown candidates may enter the recommended set marked Check
  access; known obstruction/exclusion stays inspectable but outside the default batch. Missing/deformed source
  associations leave clearance Unknown, never a synthetic free path.
- [x] For a candidate, update the full correlated information in the same free-network complement. When finite,
  Sherman–Morrison gives `C_after=C-(C h h.T C)/(sigma**2+h.T C h)`; recompute tag ellipsoid metrics from its blocks.
  Before finite covariance exists, score projected null-mode/rank reduction instead of fictitious millimetre gain.
  Use planning coordinates as estimates only, clearly separated from entered physical distances.
- [x] Greedy priority: restore connectivity/shape rank and global rigidity, then reduce worst positional uncertainty.
  Evaluate topology certification for the chosen topology and cache it; don't run exact symbolic certification for
  every geometric score when it cannot affect that step. Among equal benefit prefer known clear, shorter span,
  canonical tag IDs. Use null-mode energy/information gain to discriminate rank-restoring edges. Stop at the target
  with a generic certificate and adequate conditioning, or explain exhausted feasible candidates. Reverse-delete
  only proposed/unmeasured edges when all goals still hold; never remove an entered distance.
- [x] Suggest more evaluates all eligible unmeasured pairs against one current baseline. Include any whose maximum
  individual-tag longest-axis reduction meets the threshold, even if the globally worst tag is unchanged; also
  include constraint-restoring pairs without finite gains. Report local maximum and global-worst reduction separately.
  Sequentially select a recommended batch with recomputed marginal gains after each hypothetical addition. Preserve
  every individually useful alternative with shared-baseline/overlap explanation; no top-N cutoff. Remeasure edits
  the existing observation rather than appending an allegedly independent duplicate.
- [x] `scan_placement.py` uses this same engine to compare retained-tag coverage and common-budget/common-target
  networks. Keep reliable coverage/loop ties/redundancy; moving/removing needs a concrete reliability/effort reason,
  not merely proximity. Expose tag extent/weak directions and available multi-view support, stating missing support.
- [x] Supported new positions come only from reviewed, source-associated interior surface patches with mounting/
  access evidence supplied through the context contract; score their assumed connections/precision with the same
  engine. Without that support, return qualitative weak-region advice, not arbitrary floating XYZ or false mm gains.
  Compare the same retained tag/reference coverage before/after; omitting a weak tag is not an improvement. Record
  candidate assumptions, selected order and settings. Do not implement scene recognition or another plane editor.
- [x] Publish `measurement_plan` and `placement_review` artifacts through the common job/API/freshness owner. No
  useful pair, no finite gain and unattainable target are valid outcomes, with explicit next choices/best-effort path.
  Task 7 owns inspection of actual planning results and timing; no standalone graph/performance test campaign.

## Task 5: Separate correction preview, original RGB-D rebuild and optional context consumption

**Spec coverage:** M7, M10, M11; shared C1–C4.

- [x] Retain `scan_analysis._build`, existing native graph decoding and Pose3 correction; rename/expose the new joint
  action as `preview_correction`. Use only active physical pairs; absent-tag observations remain stored and counted.
  Register an identifiable measured shape to captured tags with weighted rigid alignment and determinant +1, no
  scale. For incomplete networks, retain captured support only in this joint-correction stage and label the affected
  positions/modes scan-dependent. Do not require the physical network to be complete or meet the target to attempt it.
- [x] Initialise camera/tag graph poses consistently from the registered proposal, then optimise original graph
  factors plus original ranges exactly once. Do not add fitted tag XYZ/covariance as independent priors on top of those
  ranges. Publish a `scan_correction` artifact with captured-to-proposed movements, residuals, source fingerprints and
  optional skipped assumptions. These movements are never the physical-network consistency report.
- [x] Add `scan_context_factors.py` as the one consumer of enabled reviewed relationships. Refetch observed source
  samples through original calibration/depth and current camera poses; refit supported region geometry as poses
  change. Use GTSAM custom soft factors over those contributing camera poses: normalized normal cross-product for
  parallelism, normal dot product for orthogonality, one-sided separation violation for above, and reflected matched body-support
  residuals for symmetry. Whiten by explicit user-configured angular/linear sigma. Use GTSAM numerical derivatives
  where needed; no extra optimiser or independent surface-observation priors. Scope symmetry to supplied matched
  body regions, never excluded seats/openings/front detail. Unsupported/no-tolerance relations are inactive with
  reasons. Physical-network information never includes these factors.
  In particular Above uses `max(0, minimum_separation - signed_separation)`, with the configured minimum (zero if
  only ordering is specified); it must not pull already separated floor/ceiling surfaces toward zero separation.
- [x] Extend `scan_rebuild.rebuild` and reconstruction frame ingestion to accept reviewed per-frame pixel exclusion
  masks by source frame ID. Apply masks/confidence/depth validity before the existing RGB-D fusion; preserve the
  pre-cleanup source, masks and provenance. Region editor/Review cleanup controls are supplied by the scene scope;
  absent masks mean the current fusion path unchanged and a visible skipped-context explanation.
- [x] `Update mesh` accepts only a current correction artifact, revalidates its full fingerprints and uses the same
  corrected camera/tag solution and existing publication path. Preserve hardlinked source assets/original DBs; save a
  new result in the source's current capture group via existing lineage handling. No published-mesh deformation or
  display-only transform masquerades as reconstruction. Record original/corrected provenance and enabled/missing
  context. Show original switches viewer selection only; it does not revert measurements or delete results.
- [x] Remove the superseded `/analyses` workflow and Analyse→Apply/Revert UI. Only the new workflow's Update mesh
  action accepts a current `scan_correction`; measure-only artifacts cannot rebuild. Original viewing is plain result
  selection. Keep source/revision checks; store corrected-result reference in the workflow, remove ScanSolutions
  rollback-history code and its direct group-deletion/API consumers. Do not delete old saved files.
- [ ] Task 7 owns one explicit Update mesh on Gert's selected real source after preview, preserving that output for
  comparison. Do not reimport raw DBs, automatically retexture or repeat reconstruction to satisfy another reviewer.

## Task 6: Compose the four-stage panel and non-disruptive import handoff

**Spec coverage:** M1–M11, especially M5/M6/M9/M11; consumes completed domain/session contracts.

- [x] Evolve `scan-measure-panel.ts` into the single workflow controller, reusing the nonmodal `side-panel.ts` shell.
  Replace Manage measurements… with Review and improve scan… through the existing command definitions; retain
  Measure tags (T). Use an ordered list of stage buttons with `aria-current="step"`, stable title/source/layout,
  backend-derived stage states/reasons, one primary next action and the shared job view. No numeric stage shortcuts.
- [x] Review capture shows source/tag information, placement findings and optional-context Unavailable status with
  Continue to measurements/Add replacement captures. It cannot claim automatic semantic review completed. Findings
  highlight tags/paths through `scan-tags.ts`; highlighting never moves the camera. Any Frame selection is explicit.
- [x] Measure composes the same keyed row for initial, additional, recheck and saved lists, including unavailable
  absent tags. Show measuring precision before actions. Persist batch order/progress; suggestions refresh only on
  explicit request. Stages/polling retain drafts, row focus, scroll and camera, including switching original/corrected.
- [x] Check accuracy separates completeness, consistency and uncertainty summaries, details and assumptions. No
  captured-to-fitted movement table or Apply button in this assessment. Suggest more remains available with partial
  networks and explains unknown gains/access. Update reconstruction owns Preview corrections and Update mesh, with
  scan-dependent/ambiguous warnings and future optional cleanup-content slot, without adding a second region editor.
- [x] Adapt `scan-import.ts` completion to create/resume its workflow and notify the workspace with source/result ID.
  Auto-show/open Review capture only if that import is still active and no tab/result/edit state changed. Otherwise
  announce completion with Review capture, preserving current selection/typing. Track a local interaction generation
  and session drafts for this guard; no global activity framework. Existing file picker/drop/advanced settings stay.
- [x] Revised layout action exposes the explicit changed-tag selection and resulting new-layout summary; no automatic
  copying across moved IDs. Existing physical measurements, result assets and library actions remain usable. Scene content
  plugs into shared stage/store/source-binding contracts later; do not introduce a competing panel or freshness rule.

## Task 7: Integrated real workflow evidence and practical documentation

**Spec coverage:** final verification owner for M1–M11.

- [ ] After Tasks 1–6, use the existing app started by Gert. Run the actual workflow actions on a selected existing
  capture, recording artifact kinds/input fingerprints, package versions and timings from normal job logs. Check
  physical completeness/consistency/uncertainty before any correction, inspect all useful pairs/visibility reasons,
  then preview and explicitly Update mesh once if Gert chooses. Do not manufacture/delete physical observations to
  create cases; reuse existing sparse/history inputs and report any unexercised acceptance rows.
- [ ] Gert inspects direct entry, save states, Escape/typing, stage/reload persistence, revised-layout behavior,
  non-disruptive import completion, source/corrected grouping and camera preservation. Existing runtime model/
  numerical assertions must expose invalid data/rank/covariance rather than hide it. No tests, standalone smoke or
  benchmarking scripts, browser automation, service launches, full builds or broad lint/type gates are added/run.
- [ ] Record the original source/measurement hashes, artifact/result IDs, authoritative measurement changes actually
  made by the user, timing, errors and visual limits in this Flow folder. Reuse these facts for review; do not repeat
  jobs just because a phase or reviewer changes. Missing visual evidence remains pending, never a fabricated pass.
- [x] Update README and docs/photogrammetry.md for the four stages, defaults/units, independent physical versus
  scan-correction meanings, uncertainty limits, explicit rebuild and saved-layout reuse/revision. Preserve the current
  installed RTAB-Map instructions; do not reopen native packaging or recognition/model setup.
- [ ] Commit only owned implementation/docs/dependency changes, preserving unrelated working data. Final review stays
  scoped to approved requirements/direct contracts and reuses evidence. No extra cleanup/platform task is authorised.

## Planning evidence, risks and self-review

Reuse/tool evaluation gate passed from spec §§3/13: existing owners are explicitly retained and PyRigi, handwritten
rigidity, fixed-anchor-only and rank-only alternatives are evaluated. PyRigi's mandatory plotting/notebook dependencies
are new observed packaging cost, not authority to install them during planning. Its repeated exact SymPy topology
checks may be the numerical critical path; record actual normal-job cost and memoize identical graph inputs. No
performance claim is made before the first real job.

Read-only planning inspected the working measurement/tape/API/layout/store, visibility/suggestion, job/import,
correction/rebuild/reference and shared panel contracts. It also checked the selected package's release metadata and
public APIs. No production files were changed, packages installed/imported, project Python executed, services/models
started, tests run or capture data modified by this planning task.

One author self-review mapped M1–M11 to final owners, checked API/model/component/task dependencies and separated
physical information from scan correction/context. The plan keeps one row/session/job view/store/freshness/planner,
no native build and no semantic producer. The optional context consumer is explicitly owned here; its end-to-end
scene verification remains S6. Current numerical defaults/probabilistic certification and real-job performance retain
stated limits. This is one cohesive measurement-to-reconstruction delivery using the already approved three-way split.

Primary references: [PyRigi release API](https://raw.githubusercontent.com/PyRigi/PyRigi/4dfb435260a7417fb4b2c5ab0bc1d434d2618d41/pyrigi/graph/graph.py),
[global check](https://raw.githubusercontent.com/PyRigi/PyRigi/4dfb435260a7417fb4b2c5ab0bc1d434d2618d41/pyrigi/graph/_rigidity/global_.py),
[random framework](https://raw.githubusercontent.com/PyRigi/PyRigi/4dfb435260a7417fb4b2c5ab0bc1d434d2618d41/pyrigi/framework/framework.py),
[PyPI metadata](https://pypi.org/pypi/pyrigi/1.3.0/json),
[GTSAM Point3 range binding](https://raw.githubusercontent.com/borglab/gtsam/4.3.0/gtsam/sam/sam.i),
[range factor](https://raw.githubusercontent.com/borglab/gtsam/4.3.0/gtsam/sam/RangeFactor.h),
[SciPy null space](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.null_space.html),
[chi-square quantiles](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html).
The spec's §12 primary UX sources remain the selected interaction guidance; no new navigation/widget library is proposed.
