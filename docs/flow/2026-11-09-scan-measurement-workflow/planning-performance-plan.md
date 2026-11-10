# Responsive tag-placement and measurement planning

**Status:** Tasks 1–4 implemented; real-job timing and visual/cancellation acceptance in Task 5 remain pending.
**Basis:** Gert approved the revised behaviour in the conversation on 10 November 2026.
**Related:** [workflow spec](spec.md), [original implementation plan](plan.md).
This follow-up supersedes the original plan's repeated certification inside hypothetical planning and mandatory
complete baseline checklist before placement findings. Other workflow requirements remain in force.

**Goal:** make placement review useful before measurements exist, generate an efficient practical checklist without
repeated symbolic checks, and expose progress and cancellation through the existing job UI.

**Architecture:** retain the scan worker, stores, artifact/freshness policy, shared panel, pair editor and job view.
Separate captured-geometry planning, numerical information scoring and physical-network certification within the
existing scan modules. Retain NumPy/SciPy, GTSAM, Open3D and PyRigi; no new dependencies or custom rigidity prover.

## Evidence and constraints

- The actual Review placement job `4ff1a0f3-5f77-4bed-93d3-55b3bff8f106` was stopped after 6m51s without a report.
  It contained 24 tags and 35 measurements. Its saved network fit took 0.004s; the network stage including imports
  and topology assessment took 5.64s. Two tags were isolated; 31 internal motions remained.
- One bounded 20s diagnostic replay sampled two topology checks consuming 13.48s and 7,263 repeated information
  decompositions. This is partial replay evidence, not a completed planner timing or full original-job profile.
- `review_placement` currently calls the entire `plan_measurements` before building placement findings.
  `refresh_state` certifies successive hypothetical graphs; reverse deletion also certifies trial graphs.
- Original values, captures, meshes and user edits remain untouched. No hardcoded tag IDs or van dimensions.
- No tests, scripts for benchmarking, services, browser automation, delegated reviews or package installation.
  Implement locally in the current checkout. Use Gert's normal app actions for runtime evidence.
- Best-effort continuation remains available. A timeout or missing evidence must never become a passing certificate.
- No changes to native integration, recognition, mesh correction/rebuild mathematics, or general application ownership.

## Behaviour and acceptance

| ID | Outcome | Owner |
| --- | --- | --- |
| P1 | Placement works from captured tags without a measurement fit, checklist or global certificate prerequisite. | Task 2 |
| P2 | Advice explains coverage, weak directions, observation support and practical connections; unsupported mounting positions stay qualitative. | Task 2 |
| P3 | One numerical engine serves initial planning, additional pairs and supported placement comparisons, without per-candidate symbolic checks. | Task 1 |
| P4 | Local precision, global uniqueness and achieved measurement consistency remain distinct. Unknown uniqueness never means complete. | Task 3 |
| P5 | All meaningfully useful pairs remain visible; recommended order uses conditional marginal gains and preserves entered distances. | Tasks 1, 3 |
| P6 | Shared progress describes actual work; Cancel stops the selected workflow job and preserves previous reports and measurements. | Task 4 |
| P7 | Normal real-data actions establish timing and visual acceptance; no new automated verification machinery. | Task 5 |

Performance goals for the existing 24-tag capture on this machine: placement report within 5s; checklist within
15s including a bounded uniqueness check. These are acceptance goals, not measured claims or reasons to skip evidence.
If missed, inspect the recorded phase timings and fix the demonstrated bottleneck before calling this complete.
Cold dependency imports and source geometry work count toward elapsed time.

## Task 1 — Make hypothetical information scoring numerical and reusable

**Coverage:** P3, P5. **Files:** `src/campervan/scan_suggestions.py`, `scan_network.py`.

- [x] Make `refresh_state` numerical only. It must never call `topology_certificate` implicitly. Keep topology
  evidence attached only to the exact matching vertex/edge set; adding/removing an edge cannot reuse an unrelated
  certificate. Replace `_useful`'s current rule that every pair is useful merely because certification is unknown.
- [x] Separate the rigid-motion complement from range-row decomposition in `free_network_information` so planning
  can reuse the same Q for fixed positions. Preserve the equal-weight orthogonal free-network convention, rank
  tolerance `1e-9`, conditioning warning ratio `1e-8`, and absence of finite covariance for remaining free modes.
  Physical analysis continues using this same convention; do not implement another information definition.
- [x] Prepare canonical pair IDs, positions, Jacobians, sigmas and projected rows once per planning geometry.
  For an incomplete network, score candidate rank gain by projection on the current null space. Do not perform a
  full SVD for each trial pair. Recompute the actual weighted decomposition after the selected addition, using
  the existing relative rank cutoff; handle a non-improving/ill-conditioned addition without looping forever.
- [x] Once full rank is reached, use the existing correlated rank-one covariance update. Cache the current tag
  ellipsoids per selected state; evaluate candidate reductions from the relevant updated 3x3 covariance blocks.
  Continue recomputing marginal scores after each selected pair. Do not sum shared-baseline gains.
- [x] Keep two sets: all individually useful alternatives against the shared baseline, and the ordered recommended
  batch. A pair is useful if it restores a connection/mode, makes a demonstrated structural contribution, or reduces
  any tag's longest 95% semi-axis by the configured threshold. Do not truncate to top N or hide useful alternatives
  because the globally worst tag is unchanged. Unknown-precision/excluded/obstructed pairs retain explicit reasons.
- [x] Keep reverse deletion numerical and limited to proposed pairs. Preserve local rank, precision target and
  necessary topology conditions described in Task 3. Final uniqueness certification belongs after this pass.
  If certification is inconclusive, label the resulting list an efficient provisional set, never a certified minimum.

## Task 2 — Review placement directly in captured coordinates

**Coverage:** P1, P2, P3. **Files:** `scan_placement.py`, `scan_suggestions.py`, `scan_visibility.py`,
`scan_analysis_worker.py`, `scan_workflow_api.py`, `scan_workflows.py`,
`frontend/src/scan-workflow-api.ts`, `scan-measure-panel.ts`.

- [x] Dispatch `review-placement` separately from measurement planning in the worker. Remove its automatic
  `analyse_network` prerequisite. Change `review_placement` to consume source manifest, measurement snapshot,
  planning settings and optional reviewed context directly; remove the mandatory `network` argument and nested
  full `baseline_plan` from its payload. It must not create or overwrite a measurement checklist.
- [x] Use captured tag centres for placement geometry and source visibility. Extend `planning_state` with explicit
  planning positions/basis metadata: `captured_estimate` or `registered_measured_shape`. Checklist planning may use
  a current identifiable registered measured shape; otherwise use captured positions, not an arbitrary deformation
  of an underconstrained range fit. Rebuild derivatives at those positions. Existing range precision/robust weights
  remain explicit assumptions; capture contributes geometry for prediction, never extra physical information rows.
- [x] Report source-coordinate extents/principal directions, tag distribution, existing measurement connections,
  original camera observation support and weak directions. PCA directions are not labelled floor/ceiling or van
  axes without supporting reviewed references. A single captured view prompts checking mounting/recapture;
  observation count alone does not prove poor precision or justify removal.
- [x] Reuse `assess_segments` with an explicit mesh-only assessment mode for the quick placement review. Reuse one
  raycasting scene per action. Mesh hits may indicate obstruction; a miss without depth evidence remains Unknown.
  Captured endpoints have direct source association; do not require a complete measured-shape registration to
  inspect their paths. Full checklist visibility retains original depth-based free-space assessment. Preserve the
  existing displacement/tolerance guard when endpoints come from a registered measured shape.
- [x] Use the numerical information engine on feasible connections to identify attainable weak directions, and
  distinguish already measured ties from hypothetical/Unknown-access ties. An all-available-pairs estimate is an
  optimistic geometric bound, not a practical checklist, measured uncertainty or uniqueness certificate.
- [x] Keep tags that contribute coverage or redundancy. Give concrete keep/check/move reasons and highlight tag
  locations/directions through the existing viewer hooks without changing the camera. Recommend removal only for
  actual reliability/access evidence. With no reviewed mounting surfaces, additions stay qualitative regions.
- [x] If reviewed candidate surfaces are supplied, retain common-budget/common-target comparisons using Task 1's
  numerical engine, with the same retained tags, explicit candidate connections and precision. Run no symbolic
  certificate per comparison; label local predictions and unknown global uniqueness honestly. Unsupported or
  unbounded comparisons show their reason rather than fabricated mm gains. Do not add a scene detector/editor.
- [x] Update `PlacementReview` and `describePlacement` together. Show concise findings first, assumptions/details
  in disclosures, and the existing Continue action. Remove consumers of mandatory `baseline_plan`; do not add
  adapters for obsolete artifact payloads. Bump affected producer versions/settings so old reports become stale
  through the existing freshness policy. Include captured geometry/access inputs in fingerprints; never treat
  physical-fit readiness as placement eligibility.

## Task 3 — Check ambiguity once for the selected graph, with an explicit limit

**Coverage:** P4, P5. **Files:** `scan_network.py`, `scan_suggestions.py`, `scan_analysis_worker.py`,
`scan_workflow_api.py`, `frontend/src/scan-workflow-api.ts`, `scan-measure-panel.ts`.

- [x] Before importing PyRigi, reject obviously insufficient generic 3D topologies. For more than four vertices,
  fewer than `3N-5` distinct edges or any vertex with fewer than four neighbours is insufficient. Handle small
  complete graphs separately and still assess actual 3D geometry. These are necessary screens, not certificates.
- [x] Numeric selection first restores connectivity/rank, then reinforces weak directions and reduces positional
  uncertainty. Do not stop at local full rank alone: preserve the necessary edge/degree conditions above and
  prioritize resolving deficient degrees with informative accessible ties. Necessary conditions still do not
  establish global rigidity. If candidates cannot meet them, return the useful partial list with the reason.
- [x] Call the existing seeded PyRigi checker only for the final selected graph after numerical pruning. An actual
  Check measurements action checks its actual measured graph separately. Planning must not first certify a
  baseline measured graph and then each hypothetical graph. Additional-pair planning checks its final graph once.
- [x] Give that single optional certificate a 5s computation budget, included in recorded settings/fingerprints.
  Keep this local to `topology_certificate`, using Python's Unix `SIGALRM`/`setitimer` in the existing worker's
  main thread and restoring timer/handler/random state in `finally`. On expiry return `status=unknown`, reason
  `time_budget_exceeded`, elapsed time and unchanged numeric results. Do not retry automatically or start a
  background job. This bounds the observed Python/SymPy work; it is not a hard preemption guarantee for native
  extensions. Task 4 provides process-level cancellation if native work stalls.
- [x] A negative/inconclusive final check returns a provisional checklist with a clear warning, not another loop
  that keeps adding every pair merely because no certificate exists. No custom stress-matrix proof engine,
  fixed-anchor-only replacement, additional package or weakened meaning of certified rigidity.
- [x] Keep separate report fields for local rank/conditioning/ellipsoids, generic uniqueness status/reason and
  physical residual consistency. Retain `target_met` only when both the precision target and required uniqueness
  evidence hold; expose local target attainment separately. Explain that a generic certificate excludes generic
  alternative shapes up to rigid motion/reflection; exceptional geometry remains a separate numerical concern.
  Physical fit objective/covariance still contain only actual range observations, never captured-position priors.
- [x] Bump affected algorithm versions and update direct report consumers through the existing artifact policy.
  Do not silently make previously saved physical values stale or alter authoritative distances.

## Task 4 — Progress and Cancel in the existing shared job view

**Coverage:** P6. **Files:** `src/campervan/scan_processing.py`, `scan_processing_api.py`,
`scan_analysis_worker.py`, numerical/placement modules; `frontend/src/scan-import-api.ts`,
`scan-job-status.ts`, `scan-measure-panel.ts` and direct shared-view callers.

- [x] Reuse bracketed worker stage lines and existing polling/logs. Emit distinct placement, path assessment,
  numerical selection, pruning and final uniqueness stages. Include real counts such as “Selected 12 additional
  pairs” or “Checked 80 of 276 paths” where meaningful; show indeterminate progress where total work is unknown.
  Record elapsed phase times and selected/candidate counts in existing logs/report timings, not a profiling service.
- [x] Add `POST /api/v1/scans/process/{job_id}/cancel` and `ScanProcessing.cancel(job_id)`. Validate the job ID and
  cancel only its active task. Return the terminal job; an already terminal job is unchanged. Reuse `_run`'s existing
  process-group termination and wait in `finally`. Distinguish user cancellation from API shutdown with
  `state=cancelled`, stage “Cancelled”, no misleading process-failed error. Skip artifact publication on cancellation
  and reap the process before releasing the single-task slot. No separate process manager or retry protocol.
- [x] Wire a Cancel button into `createJobView`, used by the workflow's shared job subscription. Show it only for
  the current cancellable running job; during its request show “Cancelling…”. Use the existing API error handling,
  refresh the same job, and allow explicit rerun after terminal cancellation. Update direct consumers of the job
  state union. Closing the panel leaves processing alone; Cancel stops work without closing the panel.
- [x] Keep prior completed reports and acknowledged measurements visible/preserved. Cancelling an unfinished
  computation does not publish its partial artifact, delete a report or mark a workflow stage complete. No new
  partial-result persistence mechanism. Keep camera, input drafts and focus stable during progress refreshes.
- [x] Use the existing labelled native `progress`, `role=status` and non-disruptive status updates. Do not announce
  every candidate or invent percentages. Guidance: [MDN progress](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/progress)
  and [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html). These sources inform
  the interaction; they do not establish universal accessibility compliance.

## Task 5 — Establish real-job evidence and update practical documentation

**Coverage:** P1–P7. **Files:** this follow-up plan, relevant sections of `docs/photogrammetry.md` and original
workflow spec/plan where their old ordering/certification policy conflicts with this approved follow-up.

- [ ] In Gert's existing app, have Gert run Analyse tag placement on the same capture. Record elapsed phase times
  and inspect the resulting reasons/highlights. Verify the worker log contains neither physical fitting nor full
  checklist/certification before placement findings. Do not rerun the original seven-minute job unchanged.
- [ ] Have Gert generate a checklist and Check measurements once on the existing saved data. Reuse those outputs
  to assess timing, provisional/certified status, all useful alternatives, sequential recommendations and the
  completeness/consistency/precision distinction. Do not manufacture measurements or publish a mesh for this work.
- [ ] Have Gert cancel a normal running workflow action if it lasts long enough to exercise Cancel. Confirm the
  process ends, the task slot is available, previous artifacts/measurements remain and the terminal state is shown.
  If too fast to cancel naturally, record cancellation as unexercised; do not create a synthetic slow job.
- [x] Update docs to explain planning estimates versus physical evidence, separate uniqueness status, the certificate
  limit and Cancel. Record measured performance and remaining visual/runtime limits honestly. No tests or additional
  verification processes; no acceptance claim for actions Gert has not exercised.

## Research and execution boundary

Primary algorithm source: [pinned PyRigi global-rigidity implementation](https://raw.githubusercontent.com/PyRigi/PyRigi/4dfb435260a7417fb4b2c5ab0bc1d434d2618d41/pyrigi/graph/_rigidity/global_.py).
It documents the randomized check and uses symbolic framework stresses/rank in 3D. Retain its mathematical
qualification; application-level timeout returns Unknown, never PyRigi False.
Timer behaviour/limitations: [Python 3.13 signal documentation](https://docs.python.org/3.13/library/signal.html).
No dependency changes or replacement solver are approved by this plan.

Implement Tasks 1–4 as one coherent follow-up, then Task 5's ordinary app acceptance. Do not introduce per-task
review loops or repeat processing for reviewers.

## Implementation record — 10 November 2026

Tasks 1–4 are implemented in the named existing modules and their direct report/overlay consumers. Placement now
uses captured coordinates, mesh-only connection evidence and an all-available-connections numerical bound; reviewed
mounting alternatives alone trigger numerical common-budget comparisons. Pair selection no longer invokes symbolic
certification. Fixed-geometry complements/Jacobians/current ellipsoids are reused, candidate gains use null-space
projection or correlated covariance block updates, and selected additions retain a full numerical rank assessment.
Final certificates have a five-second computation budget and explicit Unknown reasons. The existing worker/task
owner and shared job component provide Cancel. Weak directions reuse the existing source-transformed line overlay
with an illustrative label, rather than displaying them as captured-to-fitted movements.

Source inspection covered changed numerical paths, worker dispatch, artifact versions/freshness, direct TypeScript
consumers, shared job cancellation and practical docs. No tests, builds, browser actions, services, package installs
or scan-processing jobs were run. The 5s/15s performance goals and process cancellation remain unverified in the
running app. Task 5's real-data evidence must be supplied by Gert's ordinary actions; no previous timing is presented
as evidence for this new implementation. Unrelated working changes and all capture/measurement data are preserved.

### Correction: partial networks and confidence scope

Gert's real report `00fb4fe2-090c-4a56-aa15-234595c1c4e0` contained 35 entered distances and nine fully measured
triangles. Its optimistic graph had rank 60/66, six free modes, and disconnected tag 21. The previous colour policy
mapped whole-network null modes to a red state at every tag, losing the distinction between internal shape and
attachment. This did not mean the measured triangles provided no information.

The shared numerical owner now retains its observable singular modes and reports locally constrained groups with
finite **within-group** covariance only after removing the group's own rigid motion and checking that its projected
null modes vanish. Full-network covariance/completeness is unchanged. Existing NetworkX clique enumeration on
invariant pair distances and a triangle fallback identify candidate groups; no symbolic certificate runs per group.
Shape uniqueness is established directly only for groups with every pair measured; otherwise it stays unverified.
Largest-group scope, overlapping memberships and unresolved outside-tag relationships are explicit in the shared
confidence UI. Selecting a group-scoped indicator highlights its tags through the existing overlay owner.

Review capture's primary indicators now use entered connections at captured geometry. Its all-feasible-connections
prediction is separate. Check accuracy uses the fitted ranges. Producer versions invalidate the previous reports;
they must be regenerated in Gert's app. No saved measurements are edited, no jobs/services/tests are started, and
new runtime group counts and timings remain pending Gert's normal actions. Source inspection and a scoped
whitespace check are the implementation evidence, not a claim that this revised report has run successfully.

### Follow-up: actionable measurement coverage

Primary colours now diagnose each tag's own weighted measuring directions, with neighbours held fixed only for
this conditional diagnostic. A shared small QR/SVD calculation reports rank, missing directions, optimistic 95%
precision and geometric spread. Full-network fit/covariance/uniqueness remains independent and unchanged. One
underconstrained leaf no longer propagates a red colour to otherwise well-measured tags. Relative groups remain
secondary context, not a substitute for this tag-level diagnostic.

The existing baseline pair scorer now reports endpoint coverage-rank gains and conditional mm improvements as well
as whole-network rank/precision gains. Placement performs one baseline scoring pass and exposes all useful repairs;
both checklist modes reuse the same scorer and sequential selection. No full checklist or symbolic certificate is
introduced into placement. Conditional gains are labelled as optimistic; access checks and exclusions still apply.
Near-singular spread is distinguished from insufficient reading precision through the 2x geometry-penalty setting.
Producer versions invalidate old reports; regenerating them in the existing app is required for runtime acceptance.

The duplicate detected-ID picker is removed; its count remains. All emphasis uses normal opacity for other tags,
and repeating the same highlight request toggles it off through the one overlay owner. Coverage selection sends
one atomic request containing group IDs and direction vectors; no second callback reselects a deselected tag.
Source/whitespace inspection only: no tests, processing, service launches, dependency installs or browser interaction
checks were run. New diagnostic values, repair rankings and visual toggling remain for Gert's normal app inspection.
