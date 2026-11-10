# Capture-to-measurement workflow redesign

Status: approved by Gert on 10 November 2026. [Flow folder](./). Supersedes the previous four-stage workflow,
not the original capture data.

Delivery decision: plan and implement one stage at a time, starting with stage 1. All stage-specific plans live in
this folder. Gert visually reviews each stage before the next stage is planned; do not automatically implement later
stages. [Stage 1 implementation plan](stage-1-plan.md).

## 1. Outcome and hard boundary

Replace the workflow with six clear stages. Gert can visually inspect and extend a capture before measuring,
explicitly run and correct scene understanding, set the coordinate frame, compare tag layouts by predicted measuring effort, enter a useful
measurement checklist, investigate inconsistent measurements, and explicitly rebuild the reconstruction.

This is one local hobby application. Keep the implementation direct. No backward compatibility, legacy workflow,
parallel interface, old-stage adapter, rollback layer, new infrastructure or dependency upgrades. Reuse the existing
domain algorithms and shared UI mechanisms; replacing the workflow does not mean rewriting working reconstruction
or numerical libraries. Preserve original databases, source RGB-D, reconstructions, layout definitions and physical
distance measurements. They are input data, not the workflow being removed.

The current deliverable is this specification and one spec-review pass. It authorises no application edits, model
runs, downloads, services, tests or implementation-plan execution. Later implementation must have a finite checklist
derived only from this spec, one accumulated source review rather than per-task review loops, and Gert's visual
acceptance. Do not create or run tests, browser interaction suites, benchmark campaigns or repeated review cycles.
Do not add requirements merely because a reviewer suggests them. Material scope changes require Gert's decision.
Before presenting a new idea that assumes technological behaviour, announce it and have a focused subagent verify
the assumption against the code, primary documentation or research. Report the result and limitations. This is not
permission for per-task reviews, repeated speculative investigations or scope expansion; abandon unsupported ideas.

## 2. Decisions, alternatives and existing implementation

Gert chose a clean replacement over retaining the old workflow or putting every assessment inside Review capture.
Upload/reconstruction is the entry operation. Visual capture inspection precedes semantic interpretation. Scene understanding
is explicit, not automatically launched on import, navigation, guidance editing or a stale result. Planning and
distance entry are one stage. Physical network checking precedes correction of the captured reconstruction.

Existing implementation inspected on `develop`, including uncommitted scan changes:

| Responsibility | Existing owner and required direction |
| --- | --- |
| Import, native reconstruction, capture groups | `scan_processing*.py`, `scan_import*.ts`; retain RTAB-Map CLI integration/configuration and same-group ownership |
| Workflow state, API, artifact publication | `scan_workflow_models.py`, `scan_workflows.py`, `scan_workflow_api.py`; replace stage contracts in place |
| Jobs and cancellation | `scan_analysis_worker.py`, `scan-job-status.ts`; extend existing task owner, no second runner or poller |
| Distances and physical layouts | `scan_measurements.py`, `scan_layouts.py`; retain independent input data and existing save-conflict handling |
| Range fit and uncertainty | `scan_network.py`; reuse GTSAM robust range fit and free-network information convention |
| Pair selection, layout comparisons, access | `scan_suggestions.py`, `scan_placement.py`, `scan_visibility.py`; one shared planner and one access assessment |
| Scene interpretation | Existing [scene design](../2026-11-09-scan-measurement-workflow/scene-review-design.md); approved approach, complete pipeline not yet implemented |
| Coordinate frame | `scan_alignment.py` / `TagAlignment`; extend this owner for geometry references, no second transform stack |
| Correction and fusion | `scan_analysis.py`, `scan_rebuild.py`; reuse original-observation correction and RGB-D reconstruction |
| Panel, measurement entry, overlays | `side-panel.ts`, `scan-measure-panel.ts`, `scan-measure.ts`, `scan-tags.ts`; one shared shell, row editor and highlight mechanism |

The current placement report starts from entered tape distances. That is unsuitable for comparing layouts before
measurement. Its conditional per-tag coverage diagnostic is not the layout score and must not be presented as one.
The existing worker has no complete scene-understanding task; exposing a button alone will not deliver stage 2.

This spec includes the scene execution, review and guidance capabilities necessary for stage 2, using the already
selected scene design. It does not absorb every feature from the earlier scene spec. New scene-model evaluation,
automatic cleanup, symmetry-based reconstruction factors, general mesh editing, automatic CAD creation and general
annotation tooling are excluded. The earlier scene spec remains the algorithm reference, not an additional backlog
to execute in full. Its mandatory automatic-on-import behaviour is superseded here.

No new numerical optimiser, graph package, recognition backend or package installation strategy is selected.
Existing NumPy/SciPy, Open3D, GTSAM, PyRigi and approved optional recognition dependencies retain their roles.
Experimental-design principles inform the existing planner; this is not a new optimisation framework.

## 3. Navigation and shared interaction

Entry: upload databases into a capture group, explicitly process them, then show the reconstructed result and tags
at stage 1. Reuse the existing upload/group UX. The stages are:

1. Review capture (`review_capture`).
2. Understand the scene (`understand_scene`).
3. Improve tag layout (`improve_layout`).
4. Take measurements (`take_measurements`).
5. Check measurements (`check_measurements`).
6. Update reconstruction (`update_reconstruction`).

Use one stepper in the shared side panel, with current-stage heading, `Step N of 6`, Back and an action-labelled
Continue button. Completed stages remain navigable. The last stage visibly completes the process after save.
Do not render an additional nested wizard for optional recapture actions.

Each stage has a short outcome summary, its relevant content and a clear next action. Status vocabulary:
Not started, In progress, Reviewed, Skipped, Needs review, and Saved for the final result. A generated report alone
does not mean the user reviewed it. Explain Needs review with the changed input, not a generic Needs updating badge.
Allow explicit best-effort continuation/skipping with limitations recorded and shown downstream. Missing semantic
interpretation, a nonrigid network or an unmet precision target is advisory, not an artificial navigation gate.
Actual missing source assets or processing failures remain real errors; do not manufacture a successful result.

Reuse the shared panel shell: X closes; Escape first cancels an active edit, otherwise closes; clicking outside does
not. An edit that consumes Escape must not also close the panel. Retain camera/projection across stages,
selection, report updates and result changes. Applying axes compensates the viewer camera for the frame change.
Only an explicit view action changes framing. Perspective is the default for a new view.

One linked finding presentation is used by stages 2–3: action and affected place, reason, evidence, proposed benefit
or limitation, and relevant action. Select a finding to show its geometry and source photos. Use the shared magenta
selection highlight, separate from quality colours; repeat selection deselects. Show pertinent edges, triangles,
regions or direction arrows through the same owner. Do not dim all other tags in one selection mode only.
Text remains selectable. Colour always has a textual status and never stands alone.

## 4. Stage 1 — Review capture

Show the reconstructed scene and detected tags in the existing interactive viewer. Gert inspects the result and
decides where more capture is needed. Reuse existing viewing/rendering controls; no automatic capture-quality
classifier, coverage heatmap, residual map, missing-area detector, viewpoint advice, quality score or automated
before/after assessment is part of this work. Do not invent sufficient-view counts, independence thresholds or
sensor-accuracy claims. No recognition model runs in this stage.

`Add capture databases…` reuses import in the same group and same physical layout, then explicitly processes the
selected cumulative database set and displays the new result. Keep previous reconstructions available as normal
results so Gert can inspect the improvement using the existing result selector, preserving camera/projection.
This is ordinary capture data, not an old-workflow compatibility path. Do not add a comparison engine or new
comparison UI. Scene analysis remains an explicit later action.

The intended economical capture strategy is first a basic scan sufficient to see the tags and assess their layout,
then a detailed, time-consuming capture once Gert is satisfied with tag placement. The workflow must support this
without requiring complete interior coverage to reach stage 3. Added detailed scans can reuse the accepted physical
layout, applicable distances and reusable scene/frame reference definitions. New source-specific interpretation
still requires explicit reanalysis/review; never silently copy old masks or solved coordinates.

Completion: Gert chooses `Continue to scene understanding`. Visual review is acceptance for the current purpose,
not certification of completeness or accuracy. Adding further captures remains available from later stages through
the same action, returning to this stage after processing; Gert can revisit subsequent stages without reentering data.

## 5. Stage 2 — Understand the scene; set axes and origin

`Analyse scene` explicitly runs the approved target-directed pipeline: Qwen3.5-9B MLX 4-bit proposals, SAM2.1 Hiera
tiny boundaries, calibrated RGB-D association/Open3D checks, and one bounded scene reconciliation. Keep the exact
revisions, defaults, view budgets and evidence rules in the linked scene design; do not reselect models or introduce
iterative self-prompting. Target classes remain configured data: floor, ceiling, walls, wheel wells, windows, seats.
The cab is a spatial role, not permission to classify arbitrary extra objects. Missing features remain not observed.
No downloads run implicitly; show missing optional dependencies plainly using the existing setup mechanism.

Show a compact feature list linked to observed regions and original photographs. Selecting a feature exposes
label, source support and conflicts. Allow relabelling, editing a boundary in a source photo, and dismissing a false
detection through the single scene-owned region editor. Dismissal changes interpretation, not source points. A
general-purpose region merge/split tool is not required for this change. User corrections are authoritative reviewed
data, separate from the automatic proposal; reanalysis preserves them and surfaces conflicts rather than overwriting.

An `Additional guidance` text field is saved per capture/workflow as data. Editing it does not run inference.
`Reanalyse scene` uses the guidance plus existing vehicle context, and records the guidance revision used. Scope
guidance to the target vocabulary; it cannot supply invented metric geometry, silently change physical distances,
or trigger tools. `Save guidance for future captures…` explicitly updates reusable vehicle context; new captures
reuse text/reference definitions, never old masks or solved coordinates. Display the context actually used.

After scene inspection, a visible `Set axes and origin` section proposes a frame from supported floor/body geometry
and/or configured tag references. Retain Y along the van, Z up from its floor and X across it, right-handed. Resolve
front/back with explicit evidence or user confirmation. Floor-up is not necessarily gravity-up on a slope.

Show proposed axes/origin before `Apply axes and origin`. Allow choosing reference tags or supported surfaces,
reversing longitudinal direction and choosing an origin at a tag, its projection on the floor, or its projection on
the floor/centre plane. Ambiguous/missing references remain actionable, not guessed. Keep `Edit axes and origin…`
available in the viewer later. Save reference definitions separately from per-capture transforms; reuse
`TagAlignment` and the existing reference-transform owner. Frame changes do not alter distances or deform geometry.
Reanalysis proposes changed axes for explicit approval; it never replaces an accepted frame automatically.

Completion: `Continue to tag layout`, or an explicit skip when doing a trial. Axes can remain unconfirmed with a
visible limitation. Recognition unavailable is not completion of scene understanding; mark Skipped/unavailable.

## 6. Stage 3 — Improve tag layout

Question: can this arrangement deliver a rigid, precise tag network with reasonable measuring effort?

Show editable assumptions before results: desired tag-network uncertainty (default 5 mm), typical tape precision
(default 3 mm, one standard deviation), and required coverage. These are starting assumptions, not measured sensor
performance. Use the existing free-network convention: remove whole-shape translation/rotation, then report the
largest per-tag 95% ellipsoid semi-axis. This is not simultaneous 95% whole-network coverage or mesh accuracy.

Primary score: predicted total measurement count of the shared planner's smallest found target-reaching plan.
Show the predicted worst tag uncertainty beside it. Smaller count is better only for the same target, tape precision,
required coverage and access assumptions. Label `Proposed minimum`, not a proven combinatorial optimum. If the
target cannot be reached, show achievable uncertainty/remaining flexibility instead of a numeric success score.
If rigidity/uniqueness is unverified, make the score provisional, never an achieved-accuracy claim.

Critically, layout comparison starts with an empty distance graph at captured tag positions, regardless of entered
distances. Hypothetical edges use assumed precision, never captured distances as observations or pose priors.
Existing entered distances may show separately as work already done; their presence cannot improve the layout score.
For additions/moves compare the same retained reference coverage; auxiliary proposed tags are additional unknowns,
not exact anchors. Calculate retained uncertainty after marginalising auxiliary unknowns. Also evaluate each existing
tag's removal individually rather than declaring every original tag mandatory. Show the saving in measurements,
remaining-network precision and removed tag's location/coverage contribution together. Identify explicitly required
reference tags, reduced end/side/height spread and reviewed regions that would lose their only tag. Show this as
coverage evidence for Gert to judge, not a guarantee of surface accuracy between tags. A removal becomes a
recommendation only if the remaining network reaches the target with less measuring effort and Gert confirms the
required spatial coverage is retained. Otherwise display the trade-off or reject it. Do not award an unqualified
better score for dropping a desired part of the van. Removed-tag uncertainty is not claimed to remain constrained.

Use the existing deterministic numeric planner: connect components/remove internal flexible modes, improve weakest
correlated precision, then reverse-delete proposed edges while retaining the target. Use its shared range Jacobian,
robust/precision conventions and final bounded rigidity check. No exhaustive graph search, symbolic checks per pair,
or new solver. Necessary edge/degree counts are not a rigidity proof. Preserve local/global ambiguity distinctions.

Assess tape access using existing original-depth/mesh visibility. Present Accessible, Obstructed, Check access;
distinguish source evidence from Gert's confirmation. A camera-visible pair is not automatically tape-accessible.
Compare a confirmed-access plan with a conditional plan including unknown paths; label assumptions explicitly.
Keep manual access decisions separate from geometry inference. A saved physical measurement supplies evidence of
that pair's access in that layout, not a reason to hide contradictory visibility diagnostics.

Produce keep/move/add/optional-remove recommendations with evidence and predicted effect. Capture reliability
(usable views, corner/pose consistency where available) is supporting evidence; observation count or decoding
margin alone does not establish positional accuracy. Recapture a poorly observed tag only when it affects this goal.

Candidates must lie on observed fixed-body mounting patches, using the scene design's connected patches, with
reviewable surface/source associations. Reuse existing source-binding candidate checks. No invented floating XYZ,
seat-mounted suggestion or generic copy-pasted advice for every tag. If source context is unavailable, assess the
current layout and explain that automatic mounting advice is unavailable; do not claim placement review is complete.

Bound candidate generation to one representative supported point per connected mounting patch, chosen in the
patch interior nearest the highlighted weak area. Compare each single addition or move independently against the
unchanged baseline, and each individual existing-tag removal. Use the same planner/assumptions in every comparison.
Do not recursively search combinations of relocations or promise globally optimal placements. Show every evaluated
change that reduces proposed measurement count, reaches a previously unmet target or improves a currently
unreachable worst uncertainty by the configured meaningful-improvement threshold (default 5 mm). Benefits from
alternative changes are not additive. Display the actual finite candidate set, including why a candidate is rejected.

`Keep this layout and take measurements` shows the consequence: proposed count and conditional accuracy, including
unresolved access/uniqueness limitations. `Revise tags and recapture…` records unchanged/moved/added/removed IDs before
importing the new layout. Copy only distances between unchanged tags. Keep old/new layout scores comparable where
their required coverage agrees; tag-ID equality does not mean a moved tag stayed in place.

## 7. Stage 4 — Take measurements

Open directly on the generated checklist. Reuse stage 3's hypothetical pair set when no distances exist. When saved
applicable distances exist, run the same planner seeded with those observations to minimise remaining work; do not
merely mark matching rows complete in the empty-graph plan. Show saved distances as completed, and recommend only
useful remaining work. Layout scoring remains independent of already completed work. If inputs require recomputation,
show progress in this stage; there is no separate Plan/Approve/Open checklist ceremony. List tag pair, captured
estimate clearly labelled as such, measured-distance input with units, access state and Saved/Unsaved/error status.
Keep progress and next action visible, not a wall of diagnostic prose.

Clicking a row highlights the pair; it does not require selecting tags first. Reuse the same row editor for initial,
additional and recheck entries, and the existing tape tool's parser/save command. Support `12.4cm`, `234mm`, `841 mm`
and unitless input using the visible default unit. Enter validates and saves, then advances to the next unfinished
row only after acknowledgement. Escape restores the last saved value. Tab follows normal focus order. Typing never
triggers viewer numeric views or tool shortcuts. Preserve focus and draft text during job/poll updates; no save on
every keystroke. Failed saves retain the draft with a specific inline message and explicit retry.

`Cannot measure this pair…` records the obstruction and offers replanning; do not remove entered data or rearrange
the checklist while Gert is typing. Completed entries persist across reloads. Permit additional manually chosen
pairs through the existing tape tool. `Check measurements` advances with partial data if desired.

## 8. Stage 5 — Check measurements

`Calculate network` (then `Recalculate network` after edits) explicitly fits only entered ranges with their
measurement precision, using existing GTSAM Point3/range factors and Huber settings. Captured coordinates initialise
the solve and choose display handedness; no scan-position, floor or symmetry prior enters the physical network.

Keep three conclusions separate: consistency of distances; rigidity/ambiguity of the shape; and predicted precision.
Explain whether the evidence is strong enough to identify a suspicious measurement. A flexible/isostatic network
can fit erroneous ranges with small residuals, so a good residual alone cannot mean Good accuracy.

List suspect pairs by absolute standardised residual (existing review threshold greater than 2), displaying entered
distance, fitted distance, signed difference and expected precision. Label Possible measurement issue, not Wrong.
Show robust downweighting separately; never silently exclude a measurement, inflate its precision or replace its
entered value with the fitted value. Explain coupled conflicts when a unique culprit is not established. Remeasure
using the shared entry rows, preserving the previous value until the new entry saves, then explicitly recalculate.

Show all additional pairs that meaningfully reduce flexibility or uncertainty, using the same planner and access
owner. Distinguish baseline individual gains from a sequential recommended batch; overlapping benefits are not
additive. No arbitrary top-N truncation of useful pairs. Enter extras here without returning to another editor.
Reuse conditional per-tag coverage/triangles only as secondary explanations, with their conditional assumptions.
Do not colour every tag poor solely because another part of the network is unresolved.

`Continue to reconstruction` records accepted limitations. Network calculation changes no mesh or original distance.

## 9. Stage 6 — Update reconstruction

`Preview correction` aligns the fitted shape to captured tags, then uses the existing joint original-observation
graph correction with each original physical range once. Do not insert fitted tag positions as independent new
measurements or count the ranges twice. Underconstrained fits remain best effort using existing scan evidence;
explain where that evidence supplies information absent from the physical-only network.

Show movements/residuals and the proposed result before `Update reconstruction`. Use corrected camera/tag poses
and original RGB-D through the existing fusion/texturing path, not a new mesh-warping mechanism. Applying a display
frame and changing geometry remain distinct operations. Keep current axes definitions and solve them for the result.
Save the corrected result in the same capture group, preserving source inputs. Show Saved, the resulting reconstruction
and Done only after the actual rebuild/save completes. Editing inputs makes an earlier preview outdated with a reason.
No automatic rebuild after network analysis or scene reanalysis. Semantic cleanup/optional geometry factors are not
added by this redesign.

## 10. State, source changes and clean replacement

One workflow store owns stage decisions, selected source/layout, scene guidance/corrections, accepted frame and
artifact references. Physical distances remain in the independent measurement store. Keep last selected capture
group/result and stage on reload. Reuse existing revisions/fingerprints and atomic write/conflict handling; do not
introduce another save coordinator, persistence framework or freshness system.

For new databases with an unchanged layout: preserve distances and user intent, return to visual capture review after
processing, retain the old result for inspection, and mark source-dependent scene/layout/plan/correction results Needs review.
Do not copy old region coordinates onto a new source. Preserve source-associated user corrections on the old result;
transfer only where source identity or verified association supports it, otherwise request review. Scene reanalysis
and axes application remain explicit. A physical-only fit need not become invalid just because a new photo arrived.

For changed tags: use an explicitly revised physical layout. Do not merge old/new tag positions by ID. Existing
unchanged-tag measurement reuse is input-data handling, not a legacy workflow compatibility requirement.

Replace old stage enums, API stage mappings, progress UI, obsolete nested process lists and workflow-derived state.
Discard old workflow progress/artifact references at cutover; do not parse/translate old stages, maintain schema
fallbacks, dual-write, preserve an old route or add a migration framework. Existing input data and reconstruction
assets remain usable through a fresh six-stage workflow. Restrict any discarded files to workflow-owned derived
metadata; do not delete physical measurement files, layout profiles or shared/source assets. Earlier Flow docs are
historical where they conflict; update the practical photogrammetry guide and scope index to point here.

## 11. Finite delivery and acceptance

Implementation locations are the scan-owned modules listed in section 2, their direct types/callers and factual scan
documentation. Changes to the shared panel/overlay are allowed only as needed by this workflow, preserving Manage
scans behaviour. No unrelated CAD/planner/UI refactor, native packaging change, service, new dependency, general
geometry editor, CAD inference, background automation or compatibility project.

Each row is an observable completion criterion, not a request for a test suite:

| ID | Required result and visual evidence |
| --- | --- |
| A1 | Six-stage stepper replaces the old workflow; current stage, next action, best-effort skips and final save completion are clear |
| A2 | Gert can inspect the reconstruction/tags, add databases in the same group and inspect the new result; a basic layout scan can precede detailed capture without lost measurements |
| A3 | Scene analysis runs only on explicit action; target regions/photos are inspectable/correctable; guidance reruns preserve corrections |
| A4 | Axes/origin are proposed and explicitly editable/applied through one transform owner; camera and distances remain consistent |
| A5 | Layout score is computed without entered ranges, states comparable assumptions and measuring effort, and evaluates supported placement changes with finite work |
| A6 | Recommended pairs are directly editable; units, Enter/Escape, acknowledged saves, reload, access alternatives and focus work without viewer shortcut interference |
| A7 | Physical-only fit separates disagreement, rigidity and uncertainty; rechecks/additional pairs share the editor and never silently change entered values |
| A8 | Correction preview and rebuild are explicit; original observations/ranges are used correctly, output stays in the group, and Saved follows actual completion |
| A9 | Old workflow code/state is removed without compatibility; original capture/measurement/layout data remain usable; shared panels/highlights remain shared |

The later implementation plan must map a finite set of tasks to A1–A9, identify the unfinished scene producer and
layout-comparison work explicitly, and estimate those separately from UI rearrangement. It must not claim a mere
UI shell completes A3/A5. A2 deliberately reuses visual inspection/import rather than introducing automatic capture
assessment. Use focused source inspection and Gert's visual inspection of the existing app. Do not
create/run tests, start services, launch repeated verification processes or delegate per-task reviews. One accumulated
review may identify directly blocking defects; it may not enlarge the scope or restart an endless review loop.
If a required algorithm cannot deliver the specified result, report that concrete limitation for a decision rather
than substituting a generic score, hiding the stage or silently initiating research/model replacement.

## 12. Research and decisions

References support the listed decisions; they do not establish universal UX compliance or prove this pipeline works.

- [USWDS step indicator](https://designsystem.digital.gov/components/step-indicator/): explicit progress and current
  stage; keep navigation controls separate and use the existing shared stepper.
- [GOV.UK multiple tasks](https://design-system.service.gov.uk/patterns/complete-multiple-tasks/): avoid unnecessary
  nested task workflows; optional recapture actions are branches within the relevant stage.
- [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html): announce actual job/save
  progress without stealing focus; use indeterminate progress where no measured total exists.
- [W3C error identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) and
  [On Input](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html): identify invalid fields in text, preserve
  editing context, and require explicit actions for expensive scene/network work.
- [AprilTag definitions](https://raw.githubusercontent.com/AprilRobotics/apriltag/master/apriltag.h): decoding margin
  is not a general positional-quality score; inspect source observations and geometric consistency separately.
- [Open3D registration](https://www.open3d.org/docs/release/tutorial/pipelines/icp_registration.html): overlap and
  residual are different evidence; do not equate one with whole-capture accuracy.
- [Joshi/Boyd sensor selection](https://stanford.edu/~boyd/papers/sensor_selection.html): measurement selection under
  an uncertainty/effort objective is established; practical approximate selection is not proof of a global optimum.
- [Existing scene processing contract](../2026-11-09-scan-measurement-workflow/scene-review-design.md): use its pinned
  proposals/masks/association/geometry approach and finite call budgets. Whole-capture reliability remains unproven.

One focused technical verification found that retained RGB-D/poses could support an evidence map, but did not
validate the proposed automatic recapture classifier. Gert explicitly removed that feature: human inspection and
adding captures is sufficient. The earlier 100 mm/10 degree view-selection and 30 mm association settings are not
capture-quality/accuracy rules and must not be repurposed as such. Their original scene-processing use does not
establish statistical independence or guarantee reconstruction accuracy. Do not resurrect this removed feature
through a review finding, implementation interpretation or the linked older specifications.

The single review pass and resolved decisions are recorded in [review notes](review-notes.md). No further review
cycle is authorised by this specification. No tests, app services, recognition models or capture processing were
run while preparing this specification.
