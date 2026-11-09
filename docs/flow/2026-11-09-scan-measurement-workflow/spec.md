# Measurement network and reconstruction workflow

**Status:** approved by Gert on 9 November 2026, including split boundaries and delivery order.
**Flow folder:** [scan-measurement-workflow](./).
**Programme and dependencies:** [scope index](README.md).
**Binding shared ownership:** [shared contracts](shared-contracts.md).
**Approved baseline:** [original combined specification](approved-combined-spec.md), approved at commit `5e32a66`.

## Scope boundary

Deliver the staged workflow, tag-placement advice, direct measurement entry, independent physical-network analysis,
all-useful-pair suggestions and explicit reconstruction correction. This scope owns the shared workflow state,
measurement save session, stage composition, pair editor and job-status presentation. Its final verification is the
physical measure/analyse/improve/correct loop, using existing captures and the current importer.

Embedded native packaging is owned by the [RTAB-Map scope](../2026-11-09-embedded-rtabmap/spec.md). Automatic semantic
recognition, region editing, geometry-derived axes and reusable-knowledge authoring UI are owned by the
[scene-review scope](../2026-11-09-scan-scene-review/spec.md). They are not deliverables of this implementation plan.
This workflow consumes their typed artifacts when present; absent scene context is explicitly unavailable and does
not block measuring, analysis or best-effort correction. No second manual region editor or recognition placeholder
implementation is introduced here. Existing imported meshes, tag references and native graph remain usable.
Before scene delivery, Review capture exposes the existing source/tag information and placement findings; it does
not claim semantic review completed. The rest of this scope's cycle remains usable and independently verifiable.

The source boundary below is the existing local scan subsystem. No CAD, planner, renderer-navigation or app-wide
ownership redesign, new service/cloud dependency, framework or general workflow engine is introduced. Original
sources and physical measurements are retained. No tests are created or run; no services are started by the agent.

## 2. User decisions and approaches

The user approved a single staged nonmodal side panel beside the existing model:

**Review capture → Measure → Check accuracy → Update reconstruction**.

This evolves the current measurement-panel responsibility. It reuses the existing panel shell, measurement storage,
tag projection, scan-job owner and reconstruction path. Stages are revisitable, including the repeated
Measure/Check accuracy loop. The model stays interactive and stage changes do not move its camera.

A separate wizard was considered: it explains a first-time linear sequence but makes physical measurement sessions,
revisiting captures and repeated analysis awkward. It was not selected. A separate dashboard was rejected because
the findings need direct spatial context in the existing viewer and would create another navigation surface.

## 3. Existing system and changes of responsibility

Research found that `scan_analysis.py` currently builds original scan factors before adding physical ranges. Its
scan-only/with-distances covariance and captured-to-fitted deltas answer scan-correction questions, not physical-network
sufficiency. Preserve that fitting capability for correction; replace its use as the measurement assessment.

There is no current persisted workflow, geometry context, tag-placement report or initial pair checklist. Direct
checklist entry does not exist: current Edit/Measure pair actions route back to selecting tags with the tape tool.

| Responsibility | Reuse or bounded extension | Ownership after change |
| --- | --- | --- |
| Scan workspace/result selection | `frontend/src/scan.ts` | Composes workflow and existing renderer |
| Panel header, X, slots, scroll, focus and dismissal | `frontend/src/side-panel.ts` | One shared shell for workflow and scan library |
| Scan library/import entry points | `scan-library.ts`, `scan-import.ts` | Groups, result management, uploads and import form |
| Distance editing/save/validation | `scan-measure.ts`, `scan-measurements-api.ts` | One measurement session shared by tape and rows |
| Stage content and navigation | Evolve `scan-measure-panel.ts` into scan workflow view/controller | One active stage and action definition |
| Pair input/feedback | Shared scan measurement-row component | Initial checklist, extras, rechecks and saved distances |
| Processing status/logs | Shared scan job-status component over `ProcessingJob` | Import, review, analysis, suggestions and rebuild |
| Tag/line/context projection | `scan-tags.ts` and current scan scene | One projection/reference-frame owner |
| Physical observations/layouts | `scan_measurements.py`, `scan_layouts.py` | Existing authoritative distance store/layout registry |
| Durable context and workflow progress | Small scan-owned `ScanWorkflowStore` | New responsibility; not library preferences |
| Measurement-only fit and rigidity | Scan analysis domain with explicit measurement mode | Position-only model, independent of scan factors |
| Pair selection and placement scoring | Extend `scan_suggestions.py` | One candidate/visibility/information-scoring mechanism |
| Native graph and scan correction | `scan_graph.py`, scan-conditioned analysis path | Original graph plus physical constraints |
| Fusion, cleanup and textures | `scans.py`, `scan_rebuild.py`, existing texturing | Same publication/reconstruction path |

Extraction into small scan-specific files is permitted where it establishes these owners. It must remove the
superseded implementation, not leave a second save path, projection pipeline, job poller or competing panel manager.
No unrelated consumers migrate. Existing import form layout is adapted within its touched boundary; its obsolete
claim that distance correction is unimplemented is removed.

## 4. Workspace and navigation

The existing Scan tab remains the workspace. Result selection and Manage scans remain available. The current
**Manage measurements…** toolbar entry becomes **Review and improve scan…**, opening this workflow at its saved stage.
The tape icon remains **Measure tags (T)** for ad-hoc measurements. There is no extra measurements-manager window or
duplicate overflow-menu action. Within the workflow, the Measure stage exposes saved distances and pair entry.

The overlay panel has a stable title, capture/layout context, compact ordered stage navigation, one primary next
action, a status area and a scrolling body. An accessible X closes it without discarding saved progress. Navigation
uses an ordered list of named stage buttons with `aria-current="step"`; it is not a collection of independently
implemented tab widgets. Stage states are Not started, In progress, Complete and Needs updating, with an adjacent
reason where work depends on earlier inputs. Users can inspect any stage, including an explanation of unmet inputs.

Completed review recommendations do not block measuring. Computing an unavailable report requires the corresponding
inputs; a visible action explains/focuses missing input rather than silently disabling based on a field elsewhere.
Actions may be disabled while their request is saving/running, with the reason beside them. An empty or invalid field
has a label, inline error, `aria-invalid` and associated error text. Errors never rely on colour alone.

No panel/stage changes resize the canvas, reset projection/zoom/orbit/pan, or select another result unexpectedly.
Selecting a finding highlights it without moving the camera. An explicit **Frame selection** action may move the view.
Perspective remains the default when no user camera preference exists.

Allow best-effort progress throughout, including an initial capture, incomplete measurement network, uncertain scene
recognition or an unmet precision target. Missing inputs can prevent a specific calculation, but review/completeness
badges and suggested targets are not permission gates. Explain what remains scan-dependent or unknown alongside the
available action; do not report that proceeding establishes physical completeness or the requested precision.

## 5. Import and completion handoff

The user selects a capture group and chooses or drops databases through the existing import surface. A visible file
picker is equivalent to dropping files. Confirm the physical tag layout, family/printed size and source databases
before **Process captures**; reuse existing defaults/settings and expose uncommon reconstruction settings in Details.
Import does not ask for physical distances before constructing a usable mesh.

Actual stages and logs use the shared job-status view; no fabricated percentage is shown. Uploaded sources survive
failure or interruption. Failed work offers an explicit retry through the existing worker and shows the real error.

On completion in the active import flow, with no editing activity or changed selection, show the new model and open
Review capture. If the user has switched result, tab or begun another edit, announce completion with **Review capture**
instead of taking over. A fresh import creates a workflow record; reopening a known result resumes that record.
Historical/unmanaged results can start a workflow lazily without altering their original manifests or measurements.

## 6. Tag-placement advice and optional scene inputs

Evaluate all detected tags together: spatial extent along all three directions, weak modes of a feasible range
network, original multi-view observation support/consistency, and likely measurable straight-line connections.
Observation count alone is not a calibrated precision estimate. State when image/viewpoint information is missing.

Return Keep, Consider moving/removing, and Suggested additions with a reason, highlighted location/region, useful
connections and predicted benefit. Keep tags that supply coverage, loop ties or useful redundancy. Removing a valid
observation does not create information: recommend removal only for concrete unreliability, unstable mounting or
avoidable physical measuring effort, not simply because another tag is nearby.

Addition candidates are supported, accessible interior surface patches near weakly constrained regions, with usable
viewing directions and candidate tape paths; never arbitrary floating XYZ points. Without sufficient surface/access
evidence, give a qualitative region recommendation, not false millimetre gains. User-confirmed mount stability/access
remains necessary. Candidate positions and measuring precision are assumptions; predictions are not achieved accuracy.

Use the same planner/score as measurement selection to compare the best supported network before/after a proposed
change. Show both predicted uncertainty at a common measurement budget and measurement count needed for a common
precision target. Preserve coverage of retained reference regions in the comparison: removing a weak target and
its coverage is not an accuracy improvement. State additions' assumed measuring precision and connections. Do not
rank by visual even spacing alone.
All material recommendations remain inspectable. Main actions are **Continue to measurements** and
**Add replacement captures…**. Explain why recapture is recommended without making it mandatory.

Semantic regions and geometry-derived axes are supplied by the scene-review scope. This owner performs the
placement/network comparison and consumes supported regions for candidate surfaces/access; it can return qualitative
or Unknown advice when they are absent. It does not invent semantic regions to complete its placement report.

## 7. Measure: one persistent checklist and editor

Create an initial recommended batch using existing valid observations, detected positions as planning estimates,
measuring precision and feasible pair paths. It aims for the smallest practical measurement effort that achieves a
rigid, unambiguous, well-conditioned shape at the chosen precision. Redundancy is useful when it reduces error
sensitivity or permits consistency checks. It is not just a spanning tree, triangle count or `3n-6` edge count.

Show compact rows: tag pair, accessible highlight action, physical-distance input, save state, and contextual reason.
An optional captured estimate is separately labelled **Scan estimate** and never fills a blank physical observation.
Saved physical readings can be edited; fitted values are never inserted into those fields.

The same row/editor is used for initial pairs, additional recommendations, suspect rechecks and the full saved list.
All invoke the same measurement session/store as the tape tool; no tag clicking is required. Retain tape snapping and
ad-hoc entry as an alternative way to select a pair, not another persistence implementation.

Enter commits a valid value and advances to the next unfinished row after server acknowledgement. Blur also commits
a changed valid value. Explicit Save is available for discoverability. Serialise the commit for that row so blur and
Enter cannot submit it twice. Accept current units (`mm`, `cm`, `m`, `in`, `ft`; bare values mean mm). Escape restores
the last saved value, without modifying the measurement, before any panel-level Escape handling. Normal typing,
selection, paste, IME and modifier shortcuts remain normal; digits/T/Escape never leak into viewer actions.

One shared measurement session sequences every document mutation across rows, the tape tool, measuring precision
and pair exclusions, using each acknowledged revision for the next request. Per-row duplicate suppression alone is
insufficient. Allow continued typing and navigation while saves run, retaining distinct drafts and save states.
External revision conflicts remain explicit; never overwrite another writer's change or discard a draft silently.

Save each observation promptly through the existing atomic revisioned store, showing Saving, Saved or Not saved.
Invalid/failed/conflicted input stays visible and editable; never mark an unacknowledged value Saved. A 409 refreshes
the authoritative document while retaining the draft for explicit retry. Pending/failed rows are not counted complete
or included in analysis. Save failure is shown at the row, not only in a global log.

Each candidate offers **Cannot measure this pair** with a reason, using existing physical exclusions. Refresh the
recommended alternatives explicitly; do not move rows while the user is measuring. Preserve batch/order/current row,
drafts, scroll and focus during polling, analysis completion or viewer refresh. Uncommitted drafts survive panel/stage
changes and are visibly unsaved; a tab reload warns if any unsaved values would be lost. Server-acknowledged values,
checklist state and completed work survive reload. Do not introduce browser storage as an authoritative data store.

**Check measurements** is usable partway through: incomplete networks return useful completeness diagnostics instead
of pretending optimisation failure means the entered distances are bad. Saved measurements for tags absent from the
selected capture remain visible as unavailable, are never deleted, and are excluded from that capture's active fit
with an explicit count. There is no automatic reuse across incompatible physical layouts.

## 8. Measurement planning and independent analysis

### 8.1 Defaults and objective

Retain the editable typical measuring precision default of 3 mm (one standard deviation); retain existing saved
values and pair overrides. Expose it before the checklist actions. The target defaults to 5 mm as the longest
semi-axis of each tag's approximate 95% positional uncertainty ellipsoid after removing global rigid motion. This is
a modelling target, not physical calibration. Show the worst tag and direction; do not conflate it with range residuals.
The additional-pair meaningful-improvement threshold remains a separate editable value, initially 5 mm.

Use a greedy information-based planner with a reverse-deletion pass, preserving existing valid measurements. First
connect missing tags/eliminate non-rigid modes and establish generic global rigidity; then reduce the worst positional
uncertainty until the target is met or feasible candidates are exhausted. For equal information/benefit, prefer known
clear paths, then shorter tape spans, then canonical tag IDs. Record the ordered selected set and algorithm/settings.
Reverse deletion removes only proposed, unmeasured pairs if all stated sufficiency/precision goals still hold.
Report the result as a recommended efficient set, without claiming a globally optimal combinatorial search.

Generic graph rigidity and actual geometric conditioning are checked separately. The graph check may reject
flip-ambiguous locally rigid graphs. Actual geometry uses the weighted rigidity Jacobian and its singular values
after removing rigid-motion gauge; coplanarity/collinearity and nearly singular modes cannot be hidden by graph
topology. Handle fewer than four spatially independent tags as an inadequate 3D network with specific guidance.

### 8.2 Measurement-only fit

Unknowns are tag centre positions, not six-DOF tag poses with unobserved rotations. Fit original range observations
using their supplied/default sigmas and a visible robust loss model. Fix only the six global rigid-motion freedoms
for a nondegenerate 3D network, using a coordinate convention that does not fix a measured length or angle. An overall
mirror convention is resolved for display/reference using the scan; it supplies no additional physical length.
Captured coordinates initialise/orient the solution and support proposals, but are absent from its objective and
information matrix. Do not use weak scan priors or a pseudoinverse to display finite uncertainty for free modes.

Evaluate free-network shape covariance after equal-weight best-fit alignment across the active tag set, removing
global rigid-motion directions orthogonally. Use the same convention for planning, analysis and comparisons. Display
origin/axis choices must not change uncertainty scores or pair rankings. Internal disconnected/degenerate motions
remain unbounded; gauge removal must not silently remove them. Captured tag positions may choose the initial
configuration and display alignment, but do not supply missing physical constraints or establish global uniqueness.

Return three independent report sections:

1. **Completeness:** unmeasured/disconnected tags, remaining independent motions, generic global-rigidity status and
   actual conditioning. A solver success or finite edge count does not establish completion. A generic certificate
   is labelled as such and does not claim exact uniqueness for exceptional geometry.
2. **Consistency:** entered and fitted distances, signed `fitted - entered` residuals, standardised residuals and
   robust downweighting. No distance record is changed. A flagged pair is a recheck candidate, not proof it alone is
   wrong. For a barely constrained network, say that redundancy is insufficient to check errors reliably.
3. **Uncertainty:** correlated, gauge-removed covariance, worst tag/direction and approximate per-tag 95% ellipsoids.
   Use the 3D chi-square ellipsoid conversion rather than 1.96 for a three-dimensional region. One-dimensional range
   intervals may use 1.96. Report unbounded/unknown modes instead of a finite global precision figure when incomplete.

If robust fitting substantially downweights observations, reassess effective rank/conditioning. Display uncertainty
as local/model-dependent, not a guarantee against tape bias, wrong tag centres or LiDAR systematic errors. Nonlinear
ambiguity/degeneracy warnings remain visible even if a local covariance happens to be finite.

The independent report is always available without context. This workflow does not add a geometry-assisted physical
network fit: scene relationships support interpretation, planning and later scan correction. Do not treat
scan-derived planes as independent physical measurements or change the measurement-only completeness badge.

### 8.3 Additional pairs

Use the same candidate enumeration, exclusions, visibility and scoring as initial planning. Recompute after actual
measurements; the initial checklist was a prediction. Evaluate every unmeasured eligible pair, with default precision
or an explicit candidate override, by its update to the full correlated information/covariance. Report all pairs that
meet the meaningful-improvement threshold, not only the next pair or top N. Suggest constraint-restoring pairs even
when finite millimetre gain cannot yet be calculated.

For each pair, report the largest individual-tag uncertainty reduction and the reduction in the network's worst
uncertainty. Inclusion uses meaningful improvement at any tag, not only a change to the global worst value. For
example, improving one region from 12 mm to 3 mm remains useful when another region stays at 20 mm. Recommended
batch ordering can prioritise missing modes and the global worst region without hiding these local improvements.

Rank all useful pairs and select a recommended batch sequentially, recomputing marginal gain after each hypothetical
addition so overlapping benefits are not summed. Keep the complete individually scored alternatives available with
their shared-baseline explanation. Remeasuring a suspect/imprecise existing pair is a separate action, not a supposedly
independent duplicate observation: this version replaces its current value through the existing store.

### 8.4 Feasibility and stopping

Reuse the existing finite tape-segment mesh/depth check. A mesh miss is not proof of a clear path. Label Obstructed,
No obstruction detected, Unknown or Manually excluded, showing reasons and hits. Hide known obstructions/exclusions
from the default recommended batch; inspectable alternatives remain available. Unknown candidates may be recommended
with a check-access label, never a fabricated clearance claim. Context helps interpret openings but does not turn
missing depth into observed free space or establish hand/tape reach.

When target precision is unattainable with current placement/access/precision, report the best predicted result and
why. Offer improved placement or measuring precision rather than an endless checklist. No-benefit and no-candidate
are valid outcomes. Allow an explicit best-effort correction with a partial network, showing which positions/modes
remain scan-dependent and any ambiguity. Missing constraints or failure to meet a precision target do not block this
attempt; it never changes the physical-network status to Complete.

## 9. Update reconstruction: preview, correction and cleanup

**Preview corrections** is separate from Check measurements. Register the independently fitted shape to captured
tags using weighted rigid alignment without scale, retaining the measured shape. Show captured-to-proposed tag
movements and distinguish them from physical-distance residuals and uncertainty. For a partial network, show which
parts remain scan-dependent; finite proposal positions are not presented as physical validation.

Then fit camera/tag poses with the original native graph factors plus the original physical distances exactly once.
Use the measured shape as an initializer/reference, not a second set of independent exact XYZ observations. Preserve
native frame/transform conventions and current gauge handling. The standalone fitted network's correlated information
must not be discarded and reintroduced as independent per-tag priors.

Enabled geometry context supplies explicit soft structural relationships over its matched regions. Maintain source
frame/pixel associations so regions can be refit after pose changes. Approximate relations must not flatten every
point or enforce global box assumptions in excluded/front regions. Derived surface fits are not counted as new
independent sensor evidence for measurement-only uncertainty. Where surface associations are unavailable, a relation
is inactive with a reason rather than a guessed positional prior.

**Update mesh** explicitly starts the existing reconstruction path with corrected optical camera poses and landmark
poses together, fusing original RGB-D again and regenerating colours/textures. A rigid display transform or direct
rubber-sheet edit of the published mesh is insufficient. The worker retains original observations and source lineage.

Offer **Review cleanup** before committing optional region-based removals. Highlight candidate exterior geometry
(including observed points beyond confirmed openings/interior boundary), disconnected noise and uncertain surfaces.
Confirm/adjust the exclusion mask before fusion/meshing; preserve a source-supported pre-cleanup view. Symmetry can
flag suspicious patches but does not authorise automatic mirroring/removal. Grass is exterior because of reviewed
spatial/observational evidence, not because it fails to resemble the opposite wall. Thin features and unknown regions
are retained unless explicitly excluded.

Cleanup masks are applied through the same reconstruction pipeline and preserved as parameters/source associations
so future runs repeat the operation. Preview changes do not mutate originals. Corrected output includes enabled
context/masks and any skipped assumptions in its provenance. Original/corrected comparison uses the same viewer and
compatible reference transform; result changes never happen over active editing.

Successful rebuilding publishes a new saved result in the same capture group with clear **Original reconstruction**
or **Corrected reconstruction** provenance and meaningful settings in Details. There is no separate ambiguous Save
step: distances/context save as edited, analysis snapshots on analysis, new geometry on successful Update mesh.
**Show original** changes the viewed result; it never rolls back distances or deletes the corrected result.

This owner implements graph fitting, original RGB-D reconstruction and application of supplied reviewed
source-associated context/masks. The scene scope supplies region editing and cleanup-selection UI through this
existing stage; absent optional masks/relationships are skipped with a visible reason. End-to-end scene cleanup
verification belongs to that scope; this scope verifies the explicit physical-distance correction/rebuild path.

## 10. Persistence, layouts and freshness

Extend the existing layouts/measurement store and add a small project-adjacent `scan-workflows.json` supplied by the
application, with explicit paths passed into reusable code. `ScanWorkflowStore` owns version/revision, reusable
contexts keyed by physical layout, and workflows keyed by ID referencing group, layout and source run. It owns
review decisions, current stage, target/improvement settings, checklist batches/order and immutable artifact/job IDs.
Use the established local lock, expected revision and atomic sibling-file replacement pattern. No hardcoded tag IDs,
vehicle roles, dimensions or data paths belong in algorithms. Generic UI defaults are explicit editable settings.

Reusable knowledge has two inspectable/editable data forms: textual van/interior context supplied to the vision
model, and structured target classes, geometric relationships/tolerances and tag-based axis/origin references.
Keep these layout-associated definitions separate from each source/workflow's region IDs, frame/pixel masks,
source-element associations, matched profile revision and review corrections. Source-specific masks/coordinates
cannot become reusable definitions or replace another capture's bindings. Editing a detection changes only that
capture; Update reusable van profile explicitly promotes reusable context/reference changes. Existing workflows
retain the profile revision they used and do not silently change when its latest version changes.

Context/profile and per-capture review revisions are independent of physical-distance revision. Save user edits
explicitly or on valid field commit with feedback. Workflow stage/progress is derived from current artifacts and
review decisions, not four independent sets of booleans. Browser session storage remains only a presentation
preference for selected result/layer.

Each artifact records its kind, mode, source run/fingerprints, layout, measurement revision, context revision when
used, candidate/exclusion/settings fingerprint, algorithm version, assumptions and producing job. Replace the old
analysis workflow directly, without legacy readers, adapters, compatibility modes or rollback history. Existing
captures, physical measurements and reconstruction assets remain intact; obsolete analysis/history files need not
be read, migrated or deleted. Opening the app never automatically reprocesses sources or migrates observations.

One scan-owned artifact-kind dependency policy computes freshness from canonical fingerprints of relevant content.
Keep revisions for concurrency/provenance, but do not invalidate every result on every shared-document revision.
The policy covers physical ranges/precision, source geometry/poses, profile text/relationships/references, per-capture
labels/masks, access exclusions, settings and algorithm/model versions as relevant to each artifact kind. Backend
action eligibility and frontend status consume that same policy; do not implement separate UI staleness rules.

Changing a measurement/precision invalidates dependent fits, pair scores, correction preview and corrected-result
currency. Changing context invalidates context-derived review/alignment/cleanup and assisted/correction artifacts,
not an independent measurement fit. Changing access exclusions invalidates pair plans, not an otherwise unchanged
physical fit. Source reconstruction changes invalidate scan-dependent placement/visibility/registration, not saved
physical observations for a confirmed unchanged layout. Stale results remain inspectable with a reason; never apply
stale corrections. A corrected historical mesh remains a saved result, labelled inputs changed when applicable.

Unchanged tag placement can reuse measurements and reviewed reference definitions across new capture groups. Match
regions against each new source and require review of uncertain matches. Reused geometry context is not blindly
copied as valid coordinates. A missing tag retains its saved observations but is unavailable in that source fit.

If tags move, **Create revised tag layout…** forks the layout. Explicitly identify moved/removed/added/unchanged tags.
Copy only distances whose two endpoints the user confirms remained fixed; preserve their entered values, precision
and original provenance. Old data is retained under the old layout. Reconfirm affected context/references. Old and
new placements with the same numeric ID must not be merged into one static reconstruction; replacement captures
using the revised layout are processed separately, even if displayed in the same capture group.

The store/schema/freshness foundation is owned here. Scene processing owns feature interpretations and their
content, writing through this same revisioned store. The scene scope implements textual/structured knowledge
editing and promotion UI. Source run and source associations stay explicit, regardless of which importer produced
them. No separate scene store or competing artifact-freshness policy is permitted.

## 11. Direct application contracts

Reuse `/api/v1/scans/measurements` and its revisioned mutations/settings for every physical input. Reuse uploads,
processing jobs, asset serving and scan-library API contracts. Extend analysis snapshots with explicit kinds/modes
for `measurement_network`, `measurement_plan`, `placement_review`, `context_review` and `scan_correction`; every UI
consumer must branch on kind, not assume all analyses contain camera poses or captured-to-fitted movements.

Expose scan-workflow read/create and revisioned context/progress/checklist edits within the existing scan API, plus
actions for reviewing placement, generating a checklist, checking measurements, suggesting more and previewing
correction. Long actions return a job/artifact ID through the existing `ScanProcessing.start_action` owner. Reads
return domain status, freshness reason and artifact availability; do not spread completion rules across the frontend.
Exact route spelling and wire models are implementation-plan work; these ownership/semantic contracts are fixed.

Remove the superseded `/analyses` routes and Analyse→Apply/Revert workflow. The new workflow's Update mesh action
accepts only a current scan-correction artifact and retains source/revision checks. Measurement-only artifacts cannot
rebuild geometry. Original-result viewing is ordinary result selection; it does not roll back measurements or delete
results. Store the corrected-result reference in the workflow without a separate acceptance-history owner.

Keep one active expensive subprocess. Do not add queues, services, retries or readiness protocols. Workflows can be
viewed/edited while another task runs; explain why a competing expensive action cannot start. Source deletion/missing
assets leave an Unavailable workflow with saved observations/context retained. Corrupt saved files are reported and
never silently reset. Failed jobs do not advance stages or replace last successful artifacts.

## 12. Shared UX behavior and accessibility decisions

| Pattern | Decision and source |
| --- | --- |
| Multi-session tasks | Four revisitable action-oriented stages and saved progress; [GOV.UK task flow](https://design-system.service.gov.uk/patterns/complete-multiple-tasks/) |
| Status updates | Shared polite status for save/job changes without focus theft; [WAI status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) |
| Input errors | Visible adjacent errors, retained text and associated descriptions; [GOV.UK errors](https://design-system.service.gov.uk/components/error-message/) |
| Predictable input | Stable rows, viewport and selection; [WAI On Input](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html) |
| Panel and confirmations | Shared nonmodal workflow shell; modal deletion/layout-change confirmations only where required; [WAI dialogs](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) |
| Disclosure | Compact summary first; solver details, logs and alternatives on demand; native controls and existing styling |

Use real buttons with verbs and accessible icon names; toolbar action height matches existing icons. Stage actions,
menus/tooltips and any shortcuts share command definitions. Existing tape shortcuts retain their contextual behavior.
Do not invent numeric stage shortcuts. X/Escape return focus appropriately; an editor's Escape is handled before the
panel's. No global focus trap in the nonmodal workflow. Narrow windows retain usable scrolling and visible actions,
without adding a second UI implementation. These are specific design decisions, not a comprehensive compliance claim.

## 13. Algorithms and dependency choices

Existing GTSAM/Open3D/native texturing and RTAB-Map processing algorithms are reused. RTAB-Map packaging changes in
its separate scope; this scope uses the existing importer contract. No alternative optimiser, mesher or web
component framework is added.
Existing `gtsam.RangeFactor3` point-to-point range factors serve the independent fit; do not
reimplement their residuals/Jacobians. NumPy/SciPy already present through scan dependencies provide SVD/eigen/covariance algebra.
Declare direct use in the scan extra if needed without opportunistic upgrades.

### 13.1 Measurement rigidity

For generic 3D graph rigidity, propose the scan-only optional dependency **PyRigi 1.3.0** rather than writing a global
rigidity package. Its [documented global-rigidity check](https://pyrigi.github.io/PyRigi/development/internal_reference/graph/global_rigidity.html)
supports dimension 3 via a probabilistic algorithm; report its assumptions/error bound and record randomness for a
reproducible worker result. Actual-geometry SVD/conditioning checks remain separate. Dependency availability and
runtime cost on Python 3.13 must be confirmed without adding a test suite during implementation.

| Candidate | Evaluation and proposed decision |
| --- | --- |
| PyRigi | MIT; public Python research package, named maintainers and published rigidity methods; 1.3 docs/PyPI list Python 3.13. Fits small local graphs without a service. Small ecosystem/support team; performance for repeated planning calls is unmeasured. Public installation needs no credentials/network during processing. No security audit claimed. Accept for the bounded generic check, subject to compatibility/runtime confirmation. |
| Hand-written global rigidity | Could avoid a dependency but duplicates specialist exact/probabilistic mathematics and carries a larger correctness burden. Reject as the default. Small application-specific range Jacobian/scoring code remains appropriate. |
| Fixed four-anchor lateration | A useful sufficient construction when feasible, but can demand inaccessible anchor connections and additional measurements. Reject as the only planner/checker; it would undermine the user's placement/effort objective. |
| Rank/count alone | Existing numerical stack can check local rank but cannot establish generic global rigidity. Reject as a substitute for the separate graph check. |

Sources checked 9 November 2026: [PyRigi upstream](https://github.com/PyRigi/PyRigi),
[PyPI metadata](https://pypi.org/project/pyrigi/), [generic/global rigidity paper](https://arxiv.org/abs/0710.0926),
[GTSAM range-factor source](https://github.com/borglab/gtsam/blob/develop/gtsam/sam/RangeFactor.h),
[GTSAM robust models](https://gtsam.org/2019/09/20/robust-noise-model.html),
[Open3D 0.20 planar patches](https://www.open3d.org/docs/latest/tutorial/geometry/pointcloud.html), and
[GlobFit relational surface fitting](https://graphics.stanford.edu/~niloy/research/globFit/globFit_sigg11.html).
GlobFit is algorithmic precedent, not a new runtime dependency or promise to reproduce its entire system.

## 14. Acceptance and verification boundary

Gert manually inspects the existing app; no tests, browser automation, service launches or extra processing are run
as part of this planning change. Existing required checks and manual verification are assigned in this scope's
future implementation plan. These criteria own the corresponding original baseline acceptance clauses:

| ID | Required result | Baseline |
| --- | --- | --- |
| M1 | Import completion hands off to the new model/review without interrupting selection or editing. | AC1 |
| M2 | Tag-placement advice is explained, preserves spatial coverage and compares effort/precision fairly; unavailable geometry is explicit. | AC2 placement clause |
| M3 | Sparse/disconnected/degenerate measurement networks remain incomplete even when captured poses look confident. | AC4 |
| M4 | Checklist values can be entered without clicking tags; tape and rows share parsing, save state and authoritative values. | AC5 |
| M5 | Numeric typing/Escape preserve normal editing; invalid/conflicted/failed values stay visibly unsaved. | AC6 |
| M6 | All four stages use one shell, all pair contexts one editor, all job contexts one status/log view; future scene content reuses them. | AC7 |
| M7 | Completeness, residuals, uncertainty and scan movement are distinct, including ambiguous/degenerate cases. | AC8 |
| M8 | Initial and extra-pair planning share one scoring/visibility mechanism and expose all meaningfully useful pairs. | AC9 |
| M9 | Reload preserves acknowledged measurements, capture selection and workflow; moved tags cannot silently inherit distances. | AC10 |
| M10 | Only explicit correction/rebuild publishes new geometry; original sources and physical values remain intact. | AC11 |
| M11 | Old-layout measurements, saved reconstruction/library actions and camera/navigation remain usable; old-workflow compatibility is waived. | AC12 |

README and docs/photogrammetry.md updates belong here for measurement-only semantics, shared workflow and explicit
correction. Other scopes own their factual import/scene documentation changes; do not rewrite their sections here.
All preserved requirements above remain binding; this table identifies final verification ownership rather than
reducing the detailed contracts. Plan only this file's scope, not the other two scopes as extra tasks.
