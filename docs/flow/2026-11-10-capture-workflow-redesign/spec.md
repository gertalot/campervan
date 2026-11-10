# Capture-to-measurement workflow redesign

Status: original six-stage workflow approved by Gert on 10 November 2026. The capture/reconstruction revision in
section 4 has completed its single Flow review and awaits final written-spec approval. [Flow folder](./). Supersedes the previous
four-stage workflow, not the original capture data. Sections 5–9 remain later-stage specifications, not work
authorised by this revision.

Delivery decision: plan and implement one stage at a time, starting with stage 1. All stage-specific plans live in
this folder. Gert visually reviews each stage before the next stage is planned; do not automatically implement later
stages. [Original stage 1 implementation plan](stage-1-plan.md) records the delivered database-only review stage;
it does not authorise implementation of the photographic reconstruction revision below. That requires a separate
implementation plan in this same folder after spec approval.

## 1. Outcome and hard boundary

Replace the workflow with six clear stages. Gert can visually inspect and extend a capture before measuring,
explicitly run and correct scene understanding, set the coordinate frame, compare tag layouts by predicted measuring effort, enter a useful
measurement checklist, investigate inconsistent measurements, and explicitly rebuild the reconstruction.

This is one local hobby application. Keep the implementation direct. No backward compatibility, legacy workflow,
parallel interface, old-stage adapter, rollback layer, new infrastructure or dependency upgrades. Reuse the existing
domain algorithms and shared UI mechanisms; replacing the workflow does not mean rewriting working reconstruction
or numerical libraries. Section 4 now explicitly adds the missing photographic geometry reconstruction; the old
depth-fusion/photo-texturing path is only the quick-preview mechanism. Preserve original databases, source RGB-D, reconstructions, layout definitions and physical
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

Outside the scoped capture revision in section 4, no new numerical optimiser, graph package, recognition backend or
package installation strategy is selected.
Existing NumPy/SciPy, Open3D, GTSAM, PyRigi and approved optional recognition dependencies retain their roles.
Experimental-design principles inform the existing planner; this is not a new optimisation framework.

## 3. Navigation and shared interaction

Entry: import databases for a quick preview or original photographs for detailed reconstruction into a capture group,
explicitly process them, then show the result and tags at stage 1. Reuse the existing upload/group UX. The stages are:

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

### 4.1 Approved capture strategy and scope

Two explicit actions serve two different purposes in this one stage:

| Action | Input | Output and purpose |
| --- | --- | --- |
| `Create quick preview…` | RTAB-Map `.db` captures | Coarse depth-fused mesh and detected tags for spatial inspection and later tag-layout advice |
| `Create detailed reconstruction…` | Original high-resolution still photographs | Camera alignment, dense photographic geometry, refined mesh, texture and supported tag positions |

The economical sequence is quick preview, later scene/tag-layout review, repeat preview after moving tags if useful,
then detailed photographs after placement is settled. A preview is not a prerequisite: original photos may be the
first capture. Both actions are available at stage 1 and from the existing capture-group management entry point.
Later stages return to these same actions, not another importer or nested wizard. This revision implements no
tag-placement suggestions, scene understanding, physical-network fit, axes editor or reconstruction correction.
Those remain in their existing later-stage scopes. Their current Upcoming state must not imply they are implemented.

Use the existing side panel, import UI, capture store, job runner/poller, library, tag overlay, alignment owner and
renderer. Extend those owners for source kind and processing purpose; do not create a second upload/job/result system.
Replace the misleading `Add photographic texture` checkbox in the new capture flow with the two named actions.
Quick preview does not offer that checkbox. Existing textured results remain viewable as ordinary saved input data.
Do not retain a legacy import form or route adapter alongside the revised flow.

### 4.2 Import, capture guidance and repetition

The action opens the shared importer with current group and existing tag settings selected. Show already imported inputs,
new files, selected cumulative inputs and result name before the explicit `Create preview` or `Reconstruct from photos`
submit action. File selection/drop uploads or queues inputs; it never starts reconstruction automatically. Preserve
original files, metadata and stable source identities; equal basenames from different sources must not overwrite.
Record source kind, exact selected input identities, layout and processing settings on each result. Inputs not selected
for this run do not contribute silently. Appending captures creates a new result; previous results remain selectable.
All supported source types can be uploaded into the same group. Uploading is separate from choosing processing inputs:
detailed reconstruction accepts original stills, database photographs or an explicit mixture. Show the selection and
let Gert change it before processing; do not impose a photo-only default or silently include/exclude earlier captures.
The depth-based preview requires databases containing depth; imported stills remain available for detailed processing.

Preview guidance recommends RTAB-Map LiDAR mode on, HD mode off initially, and inspection of detected tags. HD off
reduces colour-image memory compared with HD mode; it is not a guarantee that all tags will be readable. Capture
missed tags closer with surrounding context. Do not promise measurement accuracy from this coarse capture.

Detailed-capture guidance uses original overlapping still photographs from the iPhone Camera app, stable lighting,
translated viewpoints and connected overview/detail passes. Preserve original resolution/EXIF and distinguish
separate physical lenses in calibration. Do not use screenshots, texture-atlas crops or silently resized imports.
Use a concise contextual help disclosure rather than permanent instructions occupying the viewer.
Supported original-photo formats are JPEG, PNG and HEIC. Retain HEIC originals and use the official precompiled
`pillow-heif` decoder to create full-resolution working images for reconstruction, preserving original metadata
through the source mapping and handling image orientation consistently with calibration. No manual conversion,
Homebrew/source build, broader codec framework or video importer is required by this revision.

For the already-requested baseline on existing captures, detailed reconstruction may also use the original RGB
frames extracted from selected imported databases. Label these as database photographs and show their actual
dimensions. They enter the same photographic pipeline, without using recorded depth as its output geometry.
No hidden four-view cap, arbitrary top-N input selection or per-dataset hardcoded tag IDs/regions is permitted.

Each reconstruction detects and locates its own tags from its explicitly selected source captures and saves that tag
set with the result. A new result recomputes positions; it does not copy the preview's solved coordinates. Do not add
per-batch physical-layout assignment, mixed-layout gates or a tag-motion detector to this stage. Existing tag settings,
physical measurements and reference definitions remain separate data under their existing owners; this revision does
not redesign measurement association. Neither action edits measurements or marks later stages complete. Earlier
captures do not enter a new reconstruction unless explicitly selected. New source-specific interpretation requires
review; never copy old masks or solved coordinates blindly.

### 4.3 Processing ownership and actual photographic geometry

Quick preview reuses the current RTAB-Map extraction/pose/tag processing and Open3D RGB-D fusion. Keep its existing
coarse settings; this work does not tune LiDAR resolution or add more voxel experiments.

Detailed reconstruction uses this complete chain, with no silent fallback to depth fusion:

1. Prepare selected original photographs and stable source mappings. For database photographs, extract RGB and
   available calibration through the existing path; original camera metadata may initialise calibration, but saved
   RTAB poses must not be held fixed as a substitute for photographic camera reconstruction.
2. Official PyCOLMAP 4.2.1 CPU SIFT feature extraction, exhaustive matching/geometric verification and incremental
   mapping with standard local/global bundle adjustment. Use the selected input set, standard solver defaults and
   actual camera/lens groups. Record settings and registered/unregistered images. No custom matcher, optimiser,
   automatic parameter search or mandatory model downloads. Exhaustive matching is the simple initial baseline;
   it may be slow for large sets, so show image count and real progress rather than invent a runtime guarantee.
3. Export the selected reconstruction and undistorted images using COLMAP's standard model format, including sparse
   3D points and observation tracks. Select the component with the most registered input images, breaking ties by
   sparse-point count then component ID. Report other components/unregistered inputs; never imply complete coverage.
   No connected reconstruction is a real error; do not fabricate camera poses or a successful dense result.
4. Existing OpenMVS 2.4 binaries: `InterfaceCOLMAP` → `DensifyPointCloud` → `ReconstructMesh` → `RefineMesh` → `TextureMesh`.
   These stages create geometry from photographic correspondences and image-derived depth. The existing empty
   `points3D.txt` plus `TextureMesh` path does not satisfy this requirement. Do not seed this baseline with a LiDAR mesh.
5. Keep the refined full-resolution mesh as the master. Simplify only a separate viewer copy after refinement, with
   full-resolution shaded inspection retained. Texture the photographic geometry rather than a depth-fused substitute.

Use the current Mac CPU path, capped at four processing threads where supported. Dense reconstruction explicitly
uses `resolution-level=0` and a maximum image dimension at least as large as the selected undistorted images, so it
does not silently inherit half-resolution processing. Record actual image sizes. Preserve inputs if memory/disk
limits cause a tool failure; show the actual error. No automatic lower-quality retry, resource framework, CUDA/Mac
port, Windows execution integration, remote worker or processing service is part of this revision.

If geometry succeeds but texture generation fails, expose the completed shaded mesh with an explicit texture error;
do not label the job fully successful or silently substitute an older result. Retain stage outputs and native logs
for inspection; this is not an automatic resume/checkpoint framework. A retry is an explicit new run.

### 4.4 Tags, metric scale and frame

Detect configured AprilTag 36h11 corners using existing OpenCV support in registered undistorted photos. Triangulate
corresponding ordered corners with PyCOLMAP and those exact undistorted cameras/rays, respecting COLMAP/OpenCV pixel
conventions. Use the pinned COLMAP mapper's standard `filter_max_reproj_error` and `filter_min_tri_angle` defaults
for the geometric support policy, recording resolved values with the result. Reject behind-camera/failed estimates,
observations exceeding that reprojection threshold and corner tracks with insufficient triangulation angle. Require
four supported corners to use a tag's side lengths for scale; no new optimiser, tuning UI or approval gate is added.
Keep unsupported detections labelled `Detected but not located`; they do not contribute to scale. A single-view
detection is not a triangulated tag. These limitations never block reconstructing or inspecting the scene.
Keep source-image detections and supporting-view identities inspectable in the existing result details/logs; no
general annotation editor is added here.

Estimate one scale from the configured printed black-square side length and supported reconstructed tag side lengths
(median of valid side-length ratios). This establishes scale, not independent accuracy or distortion correction.
Apply that same scale to cameras, sparse/dense geometry and tag translations before publishing metric assets.
Do not fit tape distances in this stage or combine metre-valued monocular tag poses directly with arbitrary-scale
SfM coordinates. If no supported metric reference is available, retain an inspectable result explicitly labelled
arbitrary units; do not display metres or offer metric measurement against it. Missing tags do not block inspection.

Reuse `TagAlignment` for any applicable existing axis/origin definition; do not force the preview's solved transform
onto the new geometry or introduce another transform stack. Apply definitions only when required tag support and
scale exist; otherwise show the existing unaligned reason. Interactive axes/origin editing remains stage 2.

### 4.5 Shared progress, results and review

Show the actual stage and available counts: preparation, matching, camera reconstruction, dense reconstruction,
meshing, refinement, texturing, save. Use indeterminate progress when the tool supplies no measurable total; never
invent percentages. Reuse the existing status/log/cancellation presentation. Buttons have hover, pressed and focus
states; pending actions visibly change state. Cancel stops this run's worker/native subprocesses and retains inputs
and previous results. Errors identify the failed operation and remain visible without opening a log.

Publish both result kinds in the same capture group and existing result selector. Details identify preview versus
photographic reconstruction, source set, dimensions, registered image counts, settings, scale source and missing
coverage/texture limitations. Preserve the current completion handoff: show the result automatically only if Gert
has not navigated elsewhere; otherwise announce completion with the existing explicit view action.

Show the reconstructed scene and detected tags in the existing interactive viewer. Gert inspects the result and
decides where more capture is needed. Reuse existing viewing/rendering controls; no automatic capture-quality
classifier, coverage heatmap, residual map, missing-area detector, viewpoint advice, quality score or automated
before/after assessment is part of this work. Do not invent sufficient-view counts, independence thresholds or
sensor-accuracy claims. No recognition model runs in this stage.

Use the existing layer selector to inspect shaded simplified/full geometry and photographic texture, preserving
camera/projection. No comparison engine or automatic before/after assessment is added. Retain original photos,
calibration, reconstructed cameras, feature tracks, tag observations, image-derived depth and scale/frame provenance
for later stages. Do not mislabel generated depth as original LiDAR or invent confidence values for it.

Completion: Gert chooses `Continue to scene understanding`. Visual review is acceptance for the current purpose,
not certification of completeness or accuracy. Adding further captures remains available from later stages through
the same action, returning to this stage after processing; Gert can revisit subsequent stages without reentering data.

### 4.6 Dependency decision and delivery boundary

Selected: official precompiled PyCOLMAP 4.2.1 wheel (BSD licence), adding photographic camera reconstruction to the
existing Python environment, the already installed prebuilt OpenMVS 2.4.0 tools (AGPL-3.0), and `pillow-heif` 1.8.1
for HEIC decoding (BSD-3-Clause, bundled native components retain their licences). Official pillow-heif release
files include a Python 3.13/macOS ARM64 wheel, approximately 4.3 MB. Official PyCOLMAP release
metadata lists a Python 3.13/macOS 14+ ARM64 wheel; CPU sparse processing is supported. COLMAP CUDA dense stereo is
not used on this Mac. Standard undistorted COLMAP cameras/images/points are supported by the existing importer;
newer rigs/frames files need no custom converter. Runtime installation/interchange remains implementation evidence,
not something this spec claims to have executed. Use binary-only installation through the project's uv environment:
no Homebrew stack, source compilation, new Python environment or implicit installation from a UI action.

Alternatives evaluated for this bounded integration:

| Candidate | Decision and relevant trade-off |
| --- | --- |
| PyCOLMAP + installed OpenMVS | Selected: maintained official SfM API/wheels and documented interchange; adds one compiled wheel rather than a custom reconstruction engine. CPU processing can be slow; it runs in the existing cancellable worker. Free software; use official releases and retain native versions/logs. |
| pillow-heif versus JPEG/PNG-only | HEIC decoding selected: maintained documented decoder with compatible binary wheels and metadata support; adds a small dependency rather than requiring Camera setting changes or manual export conversion. No custom codec or implicit installation. |
| Newer OpenMVS native SfM tools | Not selected: current upstream documents `CreateStructure`, but our pinned 2.4 tool set lacks it. Upgrading and validating that different pipeline is outside this revision. |
| Metashape | Not selected: maintained commercial desktop workflow, but purchasing/licensing and automating another application adds integration work; full marker/scale-bar features require Professional. |
| Apple Object Capture | Not selected: no verified complete-interior/marker integration route for this workflow; it does not establish an advantage over the documented COLMAP/OpenMVS route. |
| Custom Rust/Go/native engine | Excluded by Gert: standalone extraction/language migration is deferred; changing orchestration language does not supply the missing reconstruction algorithms. |

Only this stage and its direct source/job/result contracts change. Preserve the later-stage specifications; detailed
photo results are not claimed compatible with the current RGB-D-only stage-6 rebuild. Stage 6 must be reconciled
when separately planned, using the retained photographic observations, rather than silently rebuilding photo results
from LiDAR. This revision does not implement that correction backend or the unfinished scene-understanding stage.

Finite capture-stage acceptance (visual/source evidence, not tests):

| ID | Observable result |
| --- | --- |
| C1 | Both named actions are discoverable; misleading photo-texture checkbox is removed; original-photo entry does not require a preview. |
| C2 | Existing databases produce a quick preview and tag overlays through current processing; repeated preview capture remains possible. |
| C3 | Original stills and extracted database photographs can complete the documented photographic camera/dense/mesh/refine/texture chain; no LiDAR-geometry substitution. |
| C4 | Explicitly selected inputs and provenance are preserved, including mixed original/database photographs; tags are recomputed per result, additional captures/results stay in the group and physical measurements are unchanged. |
| C5 | Supported photo tags establish a recorded uniform scale; missing/unsupported tags and unscaled results are labelled honestly. |
| C6 | Shared real progress, Cancel, errors, retry and result handoff work; previous results and sources survive failure/cancellation. |
| C7 | Full-resolution shaded geometry and texture can be inspected in the existing viewer with camera state preserved; dense/refined masters are not prematurely simplified. |
| C8 | One bounded connected floor/sill baseline uses existing database photographs through the complete chain; inspect actual untextured relief against the preview and record the outcome. No repeated parameter experiments or invented accuracy claims. |

No implementation plan or processing is authorised by this draft. After final approval, write one finite capture-stage
implementation plan here. Run one accumulated source review and Gert's visual inspection, not per-task reviewers,
tests, browser automation, repeated review cycles or benchmark campaigns.

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

For new databases or photographs with an unchanged layout: preserve distances and user intent, return to visual capture review after
processing, retain the old result for inspection, and mark source-dependent scene/layout/plan/correction results Needs review.
Do not copy old region coordinates onto a new source. Preserve source-associated user corrections on the old result;
transfer only where source identity or verified association supports it, otherwise request review. Scene reanalysis
and axes application remain explicit. A physical-only fit need not become invalid just because a new photo arrived.

Detected tag positions belong to their source reconstruction; do not merge old/new result coordinates by tag ID.
Physical measurement association remains separate under its existing owner. This capture revision adds no per-batch
layout declaration or mixed-layout gate. Changes to physical layouts/measurement reuse are not redesigned here.

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
geometry editor, CAD inference, background automation or compatibility project. Section 4's explicitly selected
PyCOLMAP and HEIC-decoder dependencies and photo-source processing are the only exceptions to this section's older no-new-dependency
boundary. The current revision's implementation plan maps C1–C8 only; it does not absorb A3–A8 or implement later stages.

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

Capture revision evidence: [depth diagnostic](../../research/2026-11-10-depth-detail-diagnostic.md),
[PyCOLMAP installation](https://colmap.github.io/pycolmap/index.html),
[official 4.2.1 release metadata](https://pypi.org/pypi/pycolmap/4.2.1/json),
[COLMAP reconstruction and capture](https://colmap.github.io/tutorial.html),
[camera conventions](https://colmap.github.io/cameras.html),
[OpenMVS interchange/pipeline](https://github.com/cdcseacave/openMVS/wiki/Usage),
[OpenCV tag detection](https://docs.opencv.org/4.13.0/d5/dae/tutorial_aruco_detection.html),
[COLMAP point-support defaults](https://colmap.github.io/pycolmap/pycolmap.html#pycolmap.IncrementalMapperOptions),
[HEIC decoder/binary releases](https://pypi.org/project/pillow-heif/),
[HEIC decoding and metadata](https://pillow-heif.readthedocs.io/en/latest/pillow-plugin.html),
[RTAB-Map capture settings](https://github.com/introlab/rtabmap/blob/master/app/ios/Settings.bundle/Mapping.plist).
Current upstream OpenMVS documentation includes tools newer than installed 2.4; it is not permission to invoke
unavailable binaries or upgrade the native stack. Existing worker/library/interchange sources were inspected before
selecting reuse. No runtime install or complete photographic reconstruction was run during this planning phase.

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
