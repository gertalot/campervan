# Scene understanding and editable capture review

**Status:** approved requirements reorganised into a split draft; boundary review pending.
**Flow folder:** [scan-scene-review](./).
**Programme:** [scope index](../2026-11-09-scan-measurement-workflow/README.md).
**Binding shared contracts:** [shared ownership and interchange](../2026-11-09-scan-measurement-workflow/shared-contracts.md).
**Approved baseline:** [combined spec](../2026-11-09-scan-measurement-workflow/approved-combined-spec.md) §6.1–6.2 and scene clauses in §9–§14.
**Normative processing/UX contract:** [scene-review design](../2026-11-09-scan-measurement-workflow/scene-review-design.md).
**Research/tool evaluation:** [recognition improvements](../2026-11-09-scan-measurement-workflow/recognition-improvements.md) and [recorded trials](../2026-11-09-scan-measurement-workflow/spike/automatic-region-results.md).

## 1. Outcome and closed boundary

Automatically interpret the captured van's requested features, show source-associated regions/evidence, allow label
and boundary corrections, retain those corrections, reuse van knowledge and expose coherent geometry/axes proposals.
The complete scene-review contract above is normative, including pinned models, explicit numerical defaults,
association/consistency algorithms, bounded reconciliation and known failure/quality limits. No new model selection,
optimiser, cloud service or unbounded investigation is part of this scope.

Use existing exported RGB-D, optical poses and reconstruction artifacts, whether imported by the current native
tools or the embedded importer. Native packaging and measurement-network mathematics are separate deliverables.
This scope contributes to the shared Review capture stage; it must not add a second panel, store, save coordinator,
job poller, reference transform or artifact-freshness implementation.

The measurement scope supplies the shared stage/store/freshness foundation. This dependency is explicit: land that
foundation before this scope's application integration. Scene review can be verified using any existing saved
capture, without importing new databases or finishing the embedded RTAB-Map deliverable. Semantic interpretation is
not required to measure or perform best-effort correction in the earlier scope.

## 2. Automatic interpretation and correction UX

### 2.1 Automatic scene understanding and geometry context

On import, intelligently analyse the captured space to recognise and spatially segment floor, ceiling, walls,
wheel wells, windows/openings, front seats and the complex front/cab area. Use the point cloud/mesh and original
posed RGB-D observations together where useful. Plane detection alone is not this feature, and a collection of
manual region-labelling controls does not satisfy it. Vehicle/scene context guides recognition; tag IDs, dimensions
and physical placements remain data, not hardcoded project logic.

Make region generation target-directed: locate the requested interior features in scene context before generating
their detailed masks/3D associations. Do not ask the recogniser to name every class-agnostic patch, handle or piece
of trim. Keep the target feature vocabulary in configuration data and restrict accepted semantic detections to it.
An unobserved/unlocatable target produces no detection; do not force an unrelated patch into a requested category.
Uncertainty remains evidence/status about a target detection, not an extra object category to identify.

Produce source-associated 3D regions with semantic labels, spatial extent, detection confidence/evidence and
relationships such as above/below, opposite sides, approximately parallel and roughly symmetric. Distinguish
observed geometry from inferred labels/relationships; do not generate missing metric geometry from a recognition
model. Merge supporting observations across views rather than treating each image mask as a separate object.
Missing depth on glass can support a window label/outline without inventing a measured glass surface.

Show detected regions as selectable coloured overlays with a compact named list in Review capture. Selecting a
feature highlights its observed extent and supporting images. The user can inspect, correct, merge/split or dismiss
an incorrect detection using the same region editor. Review is correction of automatic analysis, not a prerequisite
to manually naming every feature. Low-confidence/missing detections remain explicitly uncertain and do not block
best-effort processing. Candidate windows require visual/spatial support; holes alone do not establish windows.

Use the recognised scene to propose alignment/centre plane, distinguish wheel wells from side walls, identify
exterior geometry through openings, scope body symmetry to appropriate surfaces, and exempt front seats/dashboard
from box-shaped assumptions. Tag-placement and tape-path assessments consume these source-associated regions through
the existing overlay and visibility owners. Detection uncertainty propagates as uncertainty in advice; it is not
converted into exact physical constraints. Optional user-supplied approximate geometry statements remain an input
to this interpretation rather than a replacement for automatic recognition.

Use Qwen3.5-9B MLX 4-bit target-feature proposals, SAM2.1 Hiera tiny box/point-guided boundaries, calibrated RGB-D
association and Open3D geometric checks, followed by one scene-level reconciliation call to the same VLM and
rechecking. Exact artifact revisions, input/output contracts, matching criteria and initial editable defaults are
part of the normative [scene-review contract](../2026-11-09-scan-measurement-workflow/scene-review-design.md). This is the selected design; the complete
pipeline is not yet demonstrated. Do not substitute another backend or a new semantic optimiser silently.

The shared panel contains a feature list linked to the actual observed 3D regions. Selection from the list or model
shows the same feature's label, Automatic/User-corrected provenance, supporting source images, boundary and measured
conflicts. Provide Show/hide, Relabel, Edit boundary and Dismiss detection as distinct named actions. Relabel preserves
the region; boundary editing previews mask changes in an original supporting image before Save boundary/Cancel.
Dismiss removes an interpretation, not scan points. Add missing feature, merge and split reuse the same region editor.
Rerunning analysis preserves user corrections; Restore automatic result is an explicit per-feature action. Explain
What supports this? and Why flagged? using actual images and geometric residuals rather than only model confidence.

Region editing selects detected patches by click; remaining regions can be marked by a polygon on a chosen original
RGB frame, using its depth/other observations for 3D association. This is a bounded mask/region editor, not a general
mesh editor. Persist original frame/pixel or source-element association, not only derived world XYZ coordinates.
Where depth is missing, an image label can remain a 2D exclusion; it cannot invent a 3D surface or occluder.

Supported context: approximately planar floor; ceiling above/approximately parallel; roughly parallel opposite walls;
approximate bilateral body symmetry; roughly orthogonal main directions; interior boundary/openings; and a front
region exempt from simple box/symmetry expectations. Relationships are selectable and individually enabled, with
visible angular/linear tolerances. Suggested tolerances derive from fitted-patch residuals and sensor resolution,
are labelled estimates, and have editable numerical values before use. Recognition checks have explicit initial
defaults in the scene-review contract; those defaults are engineering tolerances, not measured precision. Optional
geometry factors used to change the reconstruction still require explicit configured tolerances before use; missing
values leave a factor inactive with a reason. The user can proceed without these optional assumptions.

Symmetry concerns corresponding body regions, excluding openings, seats and other identified asymmetric features.
It must not mirror every point, fill absent surfaces or erase genuine taper/curvature to force an ideal box.

### 2.2 Axes and origin

Propose Z from the floor normal and the longitudinal direction/centre plane from reviewed geometry and explicit tag
references. Preserve the project's right-handed coordinates. Front/back direction requires a confirmed semantic or
tag reference; an approximately rectangular volume cannot supply its sign. Origin is explicitly selected, for example
a tag centre or its projection onto floor/centre plane. Show the proposed axes and reference in the viewer before
**Use these axes**. On a slope, van-floor up and gravity up are distinct; do not force the floor to world level.

Extend the current explicit `TagAlignment`/reference-transform mechanism rather than introducing another alignment
stack. Store reusable reference definitions with context; per-capture solved transforms remain derived. Missing
reference tags or surfaces yield an actionable unaligned state, not borrowed roles from another layout.

## 3. Ownership and integration

Scene processing owns target proposals, masks, observed 3D associations, feature identities, geometric relationship
findings, axes proposals and region review/editor content. Its typed `context_review` artifact and review mutations
use the shared contracts and `ScanWorkflowStore`; no alternative data/persistence path is introduced.

Reusable van context has editable text for model context and structured target/geometry/tag-reference definitions.
Per-capture masks, coordinates, feature corrections and reviewed profile revision remain source-specific. Existing
workflows keep their prior revision; Update reusable van profile is explicit. New captures rematch observed features
rather than inherit old masks/coordinates. User corrections survive reanalysis and can be explicitly restored.

Source-associated reviewed relationships/masks are supplied to placement, visibility and reconstruction owners.
Those consumers remain in the measurement/reconstruction scope. This scope supplies the same region editor in
Review cleanup to inspect/adjust optional exclusions, including observed exterior points beyond confirmed openings.
Symmetry alone cannot authorise removal/mirroring; unknown/thin surfaces are retained unless explicitly excluded.
Preserve pre-cleanup source support. The reconstruction owner applies supplied masks/relationships through original
RGB-D and corrected poses, not a separate semantic meshing or deformation path.

This scope owns end-to-end verification of reviewed semantic inputs through that existing reconstruction contract.
It must not reimplement graph fitting, range uncertainty, suggestion scoring, fusion or texture publication. The
physical measurement-network result remains independent of scene assumptions and user labels.

## 4. Acceptance and independent verification

| ID | Required result | Baseline |
| --- | --- | --- |
| S1 | Automatically detect the requested floor/ceiling/wall/wheel-well/window/seat features, retaining observed 3D/source-image support; manual labelling alone is insufficient. | AC3 |
| S2 | Selecting a region or list entry exposes matching evidence; relabeling preserves the boundary; boundary editing previews changes; dismissing never deletes scan points. | AC14 review clause |
| S3 | Geometric contradictions and missing opposing wheel-well coverage are inspectable; do not accept a vertical door panel as validated floor or invent an unobserved counterpart. | AC14 contradiction clause |
| S4 | Reanalysis preserves user corrections; reusable textual/structured van knowledge is separate from per-capture masks/bindings/corrections. | AC15 |
| S5 | Geometry-derived axes/context are explained, reviewable and reusable with honest unavailable/ambiguous states; applying axes is explicit and preserves navigation otherwise. | AC2 geometry/axes clause |
| S6 | Reviewed source-associated cleanup/context feeds the existing placement/visibility/reconstruction consumers, preserving original data and explicit preview/update semantics. | Detailed §6.1 and §9 |

Verification uses the existing app and representative saved captures after shared foundation delivery, not a new
native import, a fully constrained physical network, automated browser checks or a new test suite. No services or
models run during planning. Complete recognition quality remains unproven; do not substitute manual-only annotation
or another backend to claim completion. Respect the existing single expensive-worker and best-effort policies.

README and docs/photogrammetry.md updates describe detected-region inspection, corrections, profile reuse, model
footprint and region-based cleanup. This scope owns those scene facts; it does not rewrite native setup or the
independent measurement semantics owned by the other scopes.
