# Scene understanding and review — specification contract

Status: normative part of the [scene-review scope](../2026-11-09-scan-scene-review/spec.md). Its design was approved
by Gert on 9 November 2026; the subsequent [scope split](README.md) awaits boundary review. Gert approved the review
interaction and proposed processing approach during D5; the numerical defaults below are explicit engineering
choices for that design, not measured guarantees. This document is not an implementation plan and authorises no
additional model runs, downloads or application changes during planning. Written 9 November 2026.

## User outcome

After processing captures, Review capture shows detected floor, ceiling, walls, wheel wells, windows and seats as
regions on the existing model. The user can inspect their source observations, correct labels and boundaries, and
understand how scene interpretation supports or conflicts with geometric evidence. Interpretation is of one
captured van, not an unrelated list of image classifications. Analysis and editing do not alter the reconstruction.

## Selected technical choices

| Responsibility | Concrete choice | Evidence and limitation |
| --- | --- | --- |
| Target feature proposals | Local Qwen3.5-9B MLX 4-bit, revision `938d8919941c6e7efd3c7150eff7fe9d12afa631`, through mlx-vlm 0.7.12 | Completed two-image target-directed trial; wheel well, windows and seat identified, but a door panel was wrongly labelled floor. About 6 GB model files and 7 GB measured peak MLX allocation; whole-capture quality/runtime unproven. |
| Region boundaries | Box/point-prompted SAM2.1 Hiera tiny, revision `de431c4043854a71d8101e17995dfe596bf101a5`, Transformers 5.22.2/PyTorch runtime | Existing masks ran locally. Target-directed end-to-end box-to-mask-to-3D recognition is not yet demonstrated. SAM supplies boundaries, not feature identities. |
| Metric geometry | Existing calibrated RGB-D, optical poses, confidence filtering and Open3D geometry | Captured depth remains authoritative; model boxes/prose never become invented metric surfaces. |
| Scene consistency | Explicit geometric relationship checks plus one scene-level reconciliation call to the same VLM | Defined below. No second recognition backend, new semantic optimiser or unspecified general-purpose rule engine. Complete reconciler remains unimplemented. |
| Inspection and correction | Existing side-panel shell, renderer, source assets and scan-owned region editor | One linked feature list/overlay/editor for automatic regions and user corrections. No second annotation application. |

Both selected model cards list Apache-2.0. Public local operation requires no subscription or photo upload. MLX
quantization/runtime compatibility is measured only for the pinned trial configuration; local feasibility does not
establish reliable detection. Model statements of confidence are not treated as calibrated probabilities. The model
artifacts/runtime must be explicit optional scan dependencies, with download/installed size shown before installation.

## Processing contract

1. Select overlapping posed views using the depth-coverage method below, rather than a fixed project-specific frame list.
   Retain selected view IDs, coverage and selection scores. Source-view selection is a required implementation task;
   the two/five manually selected trial views do not establish whole-capture coverage.
2. Ask the VLM for only the configured target features in full interior photos, including their image boxes. The
   scene context describes the van structure and expected relationships. Do not generate arbitrary patches to ask
   what every handle or piece of trim might be. Omitted targets are recorded as not observed, not absent.
3. Refine target boxes into masks using SAM2. Preserve source boxes, masks and region-to-frame associations. User
   point corrections use that same segmentation owner. A box containing a wall and window is not a single measured
   wall surface; overlapping masks/occlusion must be resolved before fitting that surface.
4. Project valid mask pixels through native calibration/depth/poses. Associate observations across views by 3D overlap
   with depth-consistent reprojection; reject occluded/depth-inconsistent correspondences. Keep original masks and
   disagreement evidence. Multiple observations of one feature have one persistent feature identity; approximate
   mirror partners remain distinct objects. No merging solely because two masks have the same class label.
5. Estimate supported planes, main directions and an approximate bilateral reflection plane using Open3D robust
   plane fitting, connected patches and robust nearest-neighbour reflection residuals. Use multiple hypotheses
   where the reference frame is ambiguous. Existing trial reflection code is evidence, not a validated production
   symmetry detector. Store numeric residuals/support for inspection. Orientation is relative to the van floor;
   neither screen orientation nor an assumed world Z establishes the floor.
6. Evaluate the configured relationships below and create explicit conflict/missing-observation findings. Pass those
   findings, current feature identities, geometric summaries and supporting source images together to one scene-level
   VLM reconciliation call. It may propose relabelling existing features or a targeted counterpart search in another
   retained view. Search hypotheses do not create geometry, and invalid/out-of-vocabulary model output is rejected.
7. Run geometric checks on proposed revisions again. Apply supported automatic revisions with recorded before/after
   evidence; unresolved conflicts remain Needs review. This is one reconciliation pass, not an autonomous loop of
   model calls. Return the complete review artifact before any cleanup/correction. Preserve user-reviewed labels
   and boundaries on rerun; conflicting new evidence becomes a finding instead of silently replacing those edits.

All processing artifacts retain the source run, source node IDs, model revisions, runtime versions, prompt/profile
revision, explicit parameters, raw proposals, accepted/rejected masks, 3D associations, relationship findings and
proposed/accepted label revisions. Invalid or truncated model output is a failed observation with a visible reason,
not a fallback to open-ended recognition. Existing worker/job logs expose the real processing stages.

## Geometry and association algorithm

These defaults are editable scan-analysis settings stored with the result. They control recognition support,
not metrology accuracy, and do not change original reconstruction resolution or physical measuring precision.

| Parameter | Initial value | Use |
| --- | --- | --- |
| Coverage voxel | 50 mm | Choose representative views |
| Initial view budget | 12 | Maximum initial full-image recognition calls |
| Additional search budget | 4 | Maximum new views for missing/counterpart features |
| Independent-view baseline | 100 mm translation or 10° camera rotation | Distinguish supporting observations |
| Association voxel | 20 mm | Compare observed target masks across views |
| Depth agreement tolerance | 30 mm | Reject inconsistent reprojections |
| Minimum common projected samples | 30 | Avoid declaring agreement from a few pixels |
| Mask merge support | Intersection/minimum size ≥ 0.6 and intersection/union ≥ 0.2 | Propose same-instance correspondence |
| Common-view agreement | At least 0.8 of usable samples | Prevent merging inconsistent observations |
| Plane fit | RANSAC, 30 mm inlier distance, 3-point samples, 500 iterations, seed 0 | Fit observed structural surfaces |
| Connected patch | DBSCAN, 60 mm radius, 30 minimum points | Separate disconnected plane support |
| Plane usability | At least 200 inliers and 70% inliers within its patch | Suppress unsupported orientation claims |
| Parallel/upright tolerance | 15° | Floor/ceiling/wall checks |
| Opposing-pair longitudinal/base-height tolerance | 150 mm each | Compare body intrusions at the same station |
| Reflection support | Symmetric median nearest-neighbour residual ≤ 50 mm, reflected overlap ≥ 25% within 50 mm | Suggest corresponding body regions |

Reuse the source reconstruction's depth units, confidence threshold and depth cutoff; never substitute image
brightness or a VLM distance for depth. A source without confidence uses its recorded importer semantics. Analysis
points retain source associations and do not replace full-resolution reconstruction points.

For each frame, voxelize valid depth points in the native common frame. Greedily select the view maximizing
`newly observed voxels + 0.5 × voxels receiving a second independent observation`, breaking ties by source node ID.
Stop at the initial budget or when no positive gain remains. Record uncovered/singly observed voxels; reaching the
budget is not proof of complete coverage. A selected view pair below both baseline thresholds counts as one
observation for support. Empty/invalid-depth frames cannot improve geometric coverage; preserve their photos for
review rather than claiming free space. The selection budget can be increased explicitly in another run.

SAM box/point proposals use the pinned processor's coordinate convention and return pixel masks in original image
dimensions. Retain the highest predicted-IoU mask when multiple masks are returned, but record alternatives; its
score is not a calibrated semantic confidence. Empty/invalid masks are failed detections. Window masks remain
image-supported features until an actual boundary/surface is observed; exclude their pixels from a containing
wall's surface fit. Do not treat depth beyond glass as glass position or a reliable interior occluder.

For observed 3D mask sets A and B, compute voxel intersection/minimum size and intersection/union. Only independently
viewed candidates meeting both support thresholds become merge candidates. Project their shared supported points
into each other's source images. Agreement requires the projection inside the target mask and camera-axis depth
within tolerance of measured depth. Depth hidden behind an observed foreground is occluded, not disagreement.
Out-of-frame/missing-depth samples supply no support. Fewer than the minimum samples means Not enough evidence;
a sufficient comparison below the agreement threshold is a conflict. Merge in descending overlap-score order,
with canonical source IDs as tie breakers, only if all usable pairwise checks between the two clusters pass.
This prevents an A–B–C chain hiding a known A–C contradiction. Preserve category disagreements for reconciliation.

Fit connected planes and evaluate all geometrically usable floor-labelled candidates. A floor normal needs
consistent support from at least two independent views or a user-confirmed floor/tag reference. Do not select the
largest arbitrary plane as floor. Multiple incompatible floor hypotheses remain Needs review; neither a model
sentence nor camera orientation establishes the reference alone. Checks needing an unresolved reference return
Not enough evidence. A preliminary single-view proposal remains visible without controlling axes.

For established unit floor normal n and candidate unit normal m, compute
`angle = degrees(acos(clamp(abs(dot(n,m)),0,1)))`. Floor/ceiling parallelism uses angle ≤ tolerance; wall uprightness uses
`abs(90° - angle) ≤ tolerance`. Ceiling support must lie above the supported floor in the signed floor frame; a
separation no larger than twice the plane-fit tolerance is inconclusive rather than a second surface. Store
angular/height residuals and support counts. Curved/complex regions without a usable plane cannot fail a plane
check merely because a fit is unavailable.

Resolve the floor normal's sign from a confirmed reference or the median signed distance of observing camera
centres: camera centres should be above the cargo floor. A distance within the depth-agreement tolerance is
inconclusive. Front/cab is a derived spatial role from supported seat/window interpretation and explicit reference
data, not a seventh arbitrary object class. Retain its evidence and unresolved direction where necessary.

Estimate the longitudinal reflection plane using the existing partial-reflection search method: floor-aligned XY,
both principal in-plane directions as starting hypotheses, and symmetric nearest-neighbour distances clipped at
150 mm. Search ±15° around each direction in 1° steps and offsets in 20 mm steps across the central 20% of the
observed body span. Minimize mean squared clipped distance; break ties by greater supported overlap, then canonical
search order. Do not apply the result to axes automatically. If competing non-equivalent solutions differ by less
than 5% of the best objective, retain both and mark ambiguous. Restrict support to observed interior body regions;
exclude reviewed seats, exterior points and confirmed openings. An ambiguous seat/wheel-well candidate remains
eligible for a counterpart check until resolved. No sufficiently supported body region means no plane.

Reflection supplies correspondences only when both regions lie on opposite sides, meet reflection-support criteria
and are distinct observed instances. Wheel-well partners also need longitudinal centroid difference within tolerance
and lower-bound height difference within tolerance, using the 5th percentile floor-frame height. A mixed
seat/wheel-well classification for supported body counterparts is a scene conflict. Missing lower-bound/body support
means Not enough evidence. These engineering tolerances do not prove identity; they check visual compatibility.

For counterpart searches, reflect the observed extent into each supported body-frame hypothesis, then rank
unselected frames by the number of projected search voxels with depth-consistent observation, breaking ties by
node ID. Search only retained photographs within the additional-view budget, using the same target-only path.
No supporting view means missing coverage; never synthesize a mask or surface.

The one reconciliation request sees feature IDs, source images, measured relationship findings and configured van
knowledge. It returns six-class proposed labels with cited source/relationship IDs, plus targeted search requests.
Perform bounded searches, then recheck proposals once without another reconciliation call. Auto-accept a revision
only with independent-view visual support or a matched observed counterpart, no usable geometric conflict, and no
affected user correction. Otherwise retain a reviewable proposal. Model text cannot override failed numeric checks,
invent an unobserved counterpart or establish certainty.

## Vehicle structure and contradictions

Use a versioned cargo-van scene profile stored separately from algorithms and individual capture data. It names the
target classes and approximate relationships, not project tag IDs, measured dimensions or hand-drawn target boxes.
Show its assumptions in Review capture and permit corrections for a different vehicle/configuration.

| Relationship | Required inference and inspectable failure |
| --- | --- |
| Floor, ceiling and walls | Floor is the supported lower walking/loading surface; ceiling is above it and approximately parallel; main walls are approximately upright. A vertical door-panel candidate must conflict with a floor label. Report measured normal/height residuals against the current floor hypothesis, or insufficient geometry when unavailable. |
| Opposing wheel wells | Expect two body-attached intrusions at floor level, on opposite sides, at approximately the same longitudinal station and with corresponding shape. Seeing one initiates a counterpart search in supporting views; missing visibility remains a coverage finding. Two supported mirrored bulges cannot independently pass as seat and wheel well without a recorded contradiction. |
| Seats and cabin | Seat/headrest hypotheses should agree with the observed front cabin and other source views. Do not infer front/back from a rectangular box alone. Unknown cabin direction prevents a positional rejection until direction has evidence. |
| Windows | Window interpretation needs image/opening evidence; depth beyond glass is not the window surface. Window overlap is excluded from a fitted wall patch unless the actual body surface is observed. |
| Body symmetry | Approximate paired body structure supports correspondence and label consistency. Door openings, cab clutter and missing views do not require mirrored geometry. Never manufacture a second wheel well or flatten real body taper. |

Each relationship result records feature IDs, the assumption/profile version, source evidence, measured residuals,
configured tolerance and outcome: Supported, Conflict or Not enough evidence. Derived relationships are not new
physical measurements. No label score, profile assumption or user relabel changes the independent tape-network fit.

## Inspectable Review capture UX

Use the existing nonmodal workflow side panel. Keep a compact feature list beside the model, grouped by the six
target classes, with individual entries such as Wheel well 1 and Wheel well 2. Names use left/right/front/rear only
when the reference direction is established. Distinguish Not observed from Detected and Needs review, without
requiring every feature to be reviewed before continuing. No artificial completeness gate.

Selecting either a region or a list entry selects the same feature and highlights its actual observed 3D extent.
The selection detail shows its current label, Automatic/User-corrected provenance, supporting image thumbnails,
region boundary and a plain-language evidence/conflict summary. Camera movement is only through Frame selection.
Show/hide controls allow viewing the original texture underneath. Status does not rely on colour alone.

Relabel, Edit boundary and Dismiss detection are distinct named actions. Relabel chooses one of the six feature
classes and preserves the boundary; correction does not require rerunning recognition or drawing a new region.
Boundary editing opens an original supporting image in the same panel detail and allows positive/negative point
refinement or polygon add/remove. Preview the mask/3D association, then Save boundary or Cancel. Escape cancels the
active edit before closing the panel. Merge/split use the same region ownership and save semantics.

A mistaken detection can be dismissed without deleting scan points. Restore automatic result is an explicit
per-feature action; rerunning automatic analysis never erases a user correction. Save state/errors remain beside
the edit. Changes are revisioned and invalidate only dependent interpretation/advice artifacts, preserving unrelated
measurements. An Add missing feature action uses the same label/boundary editor, not a second manual-label workflow.

Expose What supports this? and Why flagged? in the selected feature detail. Evidence links identify the actual source
frame/mask and geometric check, not only raw model prose or a percentage. Corrections resolve the current label while
preserving previous automatic evidence for inspection. Cleanup remains a separate preview/action.

## UX and technical sources checked

- [CVAT object sidebar](https://docs.cvat.ai/docs/annotation/annotation-editor/objects-sidebar/) is precedent for a
  linked object list and annotation editing. We reuse that interaction pattern, not its complete product/runtime.
- [CVAT mask editing](https://docs.cvat.ai/docs/annotation/manual-annotation/shapes/annotation-with-brush-tool/)
  distinguishes labels from mask addition/removal and exposes hide/save actions. Applied here to separate relabel
  and boundary edits with an inspectable original image.
- [WAI toolbar guidance](https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/) guides grouped editing actions and keyboard
  focus. Controls reuse shared command definitions and do not steal normal text or viewer input. These sources
  justify specific decisions, not a universal accessibility-compliance claim.
- [Qwen MLX model](https://huggingface.co/mlx-community/Qwen3.5-9B-MLX-4bit) and
  [SAM2.1 model](https://huggingface.co/facebook/sam2.1-hiera-tiny) document the proposed artifacts/licenses.
- [Trial outcomes](spike/automatic-region-results.md) are the evidence for local runtime and retained failure cases;
  [recognition research](recognition-improvements.md) records multi-view/context alternatives and limitations.

An end-to-end CUDA research stack was considered in the earlier tool research; it does not currently fit this
machine without a separate runtime/hardware decision. Independent image labels without geometric/scene checks
failed the trial's door-panel case. The hybrid pipeline is selected because it supports inspectable intermediate
regions and user correction while retaining calibrated geometry; its complete quality remains to be established.
