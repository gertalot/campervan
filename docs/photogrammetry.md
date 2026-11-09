# Van scanning, measurement and CAD workflow

Status: the four-stage measurement workflow replaces the earlier analysis/acceptance UI. The CLI extracts RTAB-Map
RGB-D captures and uses Open3D for TSDF fusion, cleanup and colour baking, with optional OpenMVS photo texturing.
The browser imports databases, shows job progress and edits per-layout physical measurements. Independent physical
assessment and joint scan correction have different meanings, described below. Source implementation is recorded;
the integrated workflow's normal-job execution and Gert's visual/physical acceptance remain pending. CAD overlay
remains unimplemented.

The [repeatable reconstruction implementation plan](superpowers/plans/2026-11-08-scan-reconstruction.md) scopes the
current unmeasured trial: saved poses, Open3D fusion and cleanup, texture comparison, and a scripting-first entry point
that the browser's database import now reuses. It does not require measured tag distances before producing a preview.

## Inspecting the current scan

Open the **Scan** tab in the local application. The Result selector lists active reconstruction results and loose PLY
previews. Manage scans organises results and imports original capture databases into a capture group.
The scan uses the installed CAD renderer, the same Z-up orbit/pan/zoom controls and the shared view cube. Fit and
projection controls are available in its toolbar; Point size adjusts screen-space point coverage. CAD and Scan retain
separate camera views. Viewing a cloud opens no additional OCP WebSocket connection.

The current `data/van-interior-preview_cloud.ply` was exported from `van-interior-merged-tags.db` with:

```sh
rtabmap-export --cloud --opt 2 --voxel 0.005 --output van-interior-preview data/van-interior-merged-tags.db
```

This export contains 1,904,238 points. The saved graph has 867 entries: 850 camera nodes and 17 tag landmarks, rather
than 867 camera poses. The three original databases retain 890 RGB-D frames; the export is the saved optimised subset,
not evidence that every original frame contributed.
Coordinates remain in metres in the saved scan frame. The 5 mm voxel setting is display downsampling, not an
accuracy claim. Original databases remain separate from the derived preview. The loose preview is unaligned;
processed runs can carry a separate, explicit tag-based reference-frame transform.

The basic viewer uses the existing tab roles, selected states, arrow/Home/End navigation and native labelled controls.
The interaction reference is the [WAI-ARIA tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/); this records
the relevant design decision, not a claim of comprehensive accessibility compliance.

## Purpose

Capture the actual NV200 interior, correct the reconstruction using measured reference distances, and use it to refine
the parametric campervan model. Gert continues to describe the design and supply measurements; Codex implements the
geometry in Python with build123d. The browser provides interactive inspection of the scan and CAD together.

This combines RGB imagery and LiDAR depth through RGB-D simultaneous localisation and mapping (SLAM). It extends the
earlier Dot3D and CloudCompare workflow in the saved Plan. That plan still contains the older tool instructions;
this document records the proposed RTAB-Map route without changing those tasks.

The required accuracy remains an open decision. A successful optimisation does not establish woodworking accuracy.
Independent measurements and physical templates remain necessary for fitted parts.

## Architecture

```text
RTAB-Map iOS
    │ original scan database: RGB, depth, calibration, poses and graph relationships
    ▼
Existing Python application / FastAPI
    ├─ RTAB-Map import and decoding
    ├─ AprilTag observations and measured distances
    ├─ GTSAM: camera and landmark optimisation
    ├─ Open3D: corrected point cloud and optional mesh
    └─ build123d: parametric CAD authored through Codex
    ↕ scan assets, observations, constraints, status and CAD display geometry
Existing browser application / Three.js
    └─ Scan tab: inspect, enter physical ranges, assess them and preview/rebuild corrections
```

| Tool | Responsibility |
| --- | --- |
| RTAB-Map iOS | Capture LiDAR and RGB data, estimate motion, recognise revisited locations and save a database. |
| RTAB-Map native tools; Python `sqlite3` where needed | Extract frames, calibration, graph links and initial poses. |
| AprilTag detection | Identify reference targets and their observations in individual RGB images. |
| GTSAM | Optimise camera poses and tag landmarks using scan observations and measured distances. |
| Open3D | Reconstruct corrected dense geometry, filter it and optionally generate a mesh. |
| build123d | Define the parametric vehicle references and fabrication geometry. |
| Three.js | Display geometry, camera poses, tags and measurement constraints. |

Use the existing local API and subprocess pattern for expensive work. This proposal needs no additional long-running
service. Keep scan processing separate from CAD regeneration so a measurement edit does not rebuild the furniture.

## Workflow

Keep the original RTAB-Map databases. They retain RGB-D frames, calibration, original graph relationships and poses
needed for corrected reconstruction; an exported PLY or OBJ alone is insufficient. Place flat, stationary AprilTags
with unique IDs around the capture, including different heights and long spans. Record the family and actual printed
black-square size, excluding paper margins. Only 36h11 is currently supported. Measure straight centre-to-centre
ranges: a tape bent around trim does not represent the application's straight-line constraint.

Import captures through **Scan → Manage scans…**, or use the [CLI processing instructions](#cli-processing).
Choose a saved layout only while its physical tags remain fixed. Capture groups organise files; membership and
matching tag numbers do not establish physical layout compatibility. Keep changed door positions or moved geometry
as separate capture configurations.

Open **Review and improve scan…** to work through four stages. The nonmodal panel leaves the viewer available for
orbit/pan and does not resize its canvas. The selected stage, checklist order/current pair, acknowledged values and
settings are saved. Stage labels describe progress and stale reports; they are advice, not precision gates. Missing
source inputs can prevent the calculation that requires them, but an incomplete physical network can still support
an explicitly labelled best-effort correction.

### 1. Review capture

Inspect the surface, tags and coverage. **Review placement** evaluates the tag arrangement and explains weak geometry,
coverage and expected measuring effort through the same planner used for checklists. Captured positions are planning
estimates, not evidence of physical accuracy. Missing reviewed scene context is stated explicitly; this workflow does
not recognise regions or install a recognition model.

After **Process captures**, **Review capture** opens the completed result and this stage. Completion should preserve
another selected result or an active edit; use the offered result action when ready. Processing progress and errors
remain available if the import dialog is closed.

### 2. Measure

Set **Typical measuring precision (mm)** to a realistic range standard deviation. Its editable initial value is
**3 mm**, not a guaranteed bound or a precision inferred from decimal places. Individual pairs can override it;
blank per-pair precision uses the saved default. **Generate checklist** supplies ordered pairs. Type the actual
physical distance into a row; the scan estimate is a separate label and is not an observation.

Rows accept `mm`, `cm`, `m`, `in` and `ft`; bare values mean millimetres. Only positive finite values can be saved.
**Enter** saves and advances after acknowledgement. Leaving an edited, nonempty row also saves; **Save** is explicit.
**Escape** restores acknowledged text and keeps normal editing focus. Saving, Saved and error feedback distinguish
acknowledged values from drafts. A failed save retains its draft; resolve the error and retry. A revision conflict
refreshes the acknowledged state without silently overwriting it. Resolve unsaved fields before a workflow action.

The tape tool (**T**) selects the same tag pairs and uses the same physical measurement session. Select two tags,
type the physical centre-to-centre distance in the bottom field and press Enter. Selecting a pair may display an
existing distance or a separately labelled scan estimate; it never saves a prefill automatically. Escape restores a
dirty tape edit, then cancels the pair; at the first-tag prompt it exits the tool. The contextual Restore / Cancel
pair / Done control performs the same action. Turning tape mode off hides saved lines. Camera navigation and normal
writing remain available; the workflow panel can be used without tape mode.

Use **Cannot measure this pair…** to record an access reason instead of entering an invented distance. Candidate
precision applies to that proposed pair and is carried into its first physical observation. Saved physical distances,
precision and exclusions are shared by compatible captures using the layout. Checklist order and candidate settings
belong to the source workflow.

### 3. Check accuracy

**Check measurements** assesses the physical ranges independently of the scan. It fits Point3 positions using only
entered ranges and effective sigmas. Captured coordinates initialise and orient the fit; they are absent from its
objective and information matrix. Display alignment and numerical gauge anchors do not provide physical information.

Read these three report sections separately:

| Section | Meaning and limits |
| --- | --- |
| Completeness | Connectivity, generic 3D uniqueness, actual geometric rank and remaining motions. |
| Consistency | Fitted-minus-entered and standardised residuals, robust weights and redundancy. |
| Uncertainty | Free-network covariance and approximate 95% positional ellipsoids under stated noise assumptions. |

Connected does not necessarily mean determined. Downweighted readings need review; a network without redundant
observations cannot strongly check itself. Rank deficiency is unbounded. Unresolved global ambiguity remains Unknown
even when a local covariance exists.

The editable **5 mm positional target** means the longest semi-axis of a tag's 3D 95% ellipsoid, not a range sigma or
a guaranteed physical error bound. Its equal-weight free-network alignment convention removes arbitrary rigid motion.
The generic topology certificate is probabilistic and is reported separately from actual geometric rank/conditioning.
Sparse, disconnected, coincident or poorly distributed inputs expose diagnostics rather than invented finite precision.
A physical fit cannot establish LiDAR calibration or accuracy of unmeasured surfaces.

**Suggest more** uses the same all-useful-pairs planner as **Generate checklist** and **Review placement**. It considers
all eligible unmeasured pairs, including possible connections across weak/disconnected parts, rather than a fixed
shortlist. It explains geometry/rank improvements before finite precision where necessary, and separates rechecks of
existing observations from new information. The independent **5 mm meaningful-improvement threshold** controls useful
additional suggestions; it is distinct from the positional target. Candidate sigmas affect predicted benefit. Benefits
from a shared baseline overlap and must not be added together. Alternatives show their individual baseline gains;
recommended checklist rows also show marginal gains after earlier proposed ranges. The batch recalculates those
gains and removes redundant proposed pairs. Unavailable global gains remain Unknown; finite local-model gains are
labelled separately and do not establish global uniqueness.

Clearance labels are **No obstruction detected**, **Unknown** and **Obstructed**. The assessment uses the finite tape
segment, neighbouring mesh rays and retained depth/pose coverage. An absent surface alone does not establish a clear
path. If the physical shape cannot be registered to the source, clearance stays Unknown. Unknown is not a clear path;
manual exclusions record reach/access or obstacles the scan cannot decide.
Inspect the reasons and highlights before attempting a measurement. Physical assessments do not rebuild geometry.

### 4. Update reconstruction

**Preview corrections** is a separate joint, scan-assisted fit. It uses original camera/tag observations and graph
constraints together with the physical ranges. Its movement and residual summaries are conditional on scan and
measurement assumptions; they do not establish measurement-only completeness or precision. Reviewed source-bound
relationships and cleanup masks are optional inputs when supplied. Missing/disabled relationships, absent support,
missing tolerances or unusable geometry are inactive with individual reasons. Cleanup masks refer to original frame
pixels and exclude depth samples during reconstruction; they never rewrite the original database. Missing masks
retain the ordinary fusion path with an explicit skipped-context explanation. This workflow provides no
region-recognition/editor setup.

Inspect the preview over the unchanged original surface. **Update mesh** explicitly rebuilds a new result from the
retained RGB-D frames and corrected poses; editing measurements, checking accuracy and previewing corrections never
rebuild automatically. A stale preview requires a new preview before updating. Inputs and saved solution/graph
content are rechecked immediately before reconstruction, and freshness is checked again when the result completes.
A result completed against changed inputs retains its assets and reports the mismatch instead of becoming the current
corrected result. A failed action reports its actual error and retains the previous successful report; no automatic
retry is implied.

The new result retains its source/layout/group association and records correction provenance. Originals and entered
physical distances remain intact. A completed rebuild never switches the displayed result automatically. Use
**Show original** and **Show corrected result** to compare results explicitly. Camera position, projection, pan and
zoom are preserved across result/layer changes.
Use **Fit** when a deliberate new framing is wanted. Physical checks not included in fitting and Gert's visual
inspection remain necessary before relying on the mesh for fabrication. No CAD dimension changes automatically.

### Saved layouts, state and freshness

Managed layout definitions and separate measurement documents live under `data/scan-tag-layouts/<layout-id>/`.
The original trial uses `data/scan-measurements.json`. `--measurements FILE` on `scan process` or `scan align` records
the intended physical layout without applying its distances. Reuse it only while the tags remain fixed.

When tags move, choose **Revise tag layout…** and classify unchanged, moved, removed and added IDs. Only observations
and exclusions whose two endpoints are confirmed unchanged are copied, with their original precision/provenance;
the old layout remains intact. Existing captures are not rebound: choose the new layout for replacement captures.
New layouts do not inherit vehicle-axis roles. Reviewed context references need reconfirmation for the revised layout. A fresh layout instead starts with an empty physical measurement document.

Physical observations are authoritative in the measurement document: canonical positive `tag_a < tag_b`, `distance_m`,
entered text, source run and optional `sigma_m`; the default sigma and access exclusions are stored there too. Storage
and numerical coordinates use metres; precision/target controls display millimetres. Fitted distances and XYZ positions
never overwrite physical observations. Files use revision checks and atomic replacement; malformed files and failed
writes are errors, not permission to reset data.

`scan-workflows.json`, beside the project file, stores source workflows, immutable profile revisions, stages,
checklists, settings and artifact references. Separate captures can share one physical layout while retaining their
own source workflow. Immutable report snapshots live in the adjacent `scan-workflow-artifacts/<id>/` directory.
Freshness depends on relevant content: changing source geometry does not invalidate an otherwise identical physical
range assessment; planning and correction additionally depend on their scan evidence/settings. Stale reports remain
inspectable, with reasons. Moving or renaming a group does not change numerical freshness. A missing source makes
source-dependent work unavailable while preserving observations.

This replaces the old workflow directly. Obsolete analysis/history files are not read or automatically migrated;
there is no old/new mode or acceptance-history/rollback owner. Existing capture and physical measurement files remain.

The workflow uses the existing scan-job owner and shared progress presentation for import, assessment and rebuild.
One expensive scan action runs at a time. The API registers workflow reads/edits and explicit actions under
`/api/v1/scans/workflows`; physical values remain under `/api/v1/scans/measurements`, and explicit layout revision uses
`POST /api/v1/scans/layouts/{id}/revise`. The backend supplies action eligibility and stale/unavailable reasons; a
visible error or missing input is not an accuracy certification. No new service is required.

### Result library

The quick **Result** selector contains active discoveries, using display names and capture-group headings when needed.
**Manage scans…** opens a modal side panel over the viewport, with search, Active / Archived / All filters, processing
summaries and explicit **Show in viewer** actions. **Inspect result** expands processing details and the secondary
Rename result, Change capture group, Use at startup and Archive / Restore actions. State labels identify the result
currently displayed and the startup default. Capture groups describe
source capture sets independently of tag-layout IDs and coordinate frames. Details use recorded input filenames,
pose source, resolution, frame/triangle counts, layers and date; missing information is Unknown. Resolution does not
establish reconstruction accuracy.

The app supplies `project_path.with_name("scan-library.json")` to a reusable library store. Its version-1 document has
`revision`, nullable `default_key`, `groups` (ID to name) and `entries` keyed by `run:<id>` or `preview:<filename>`.
Each entry has nullable `display_name`, nullable `group_id` and `archived`. This is presentation data: manifests,
asset paths, alignment definitions and physical measurements are independent. The initial Interior trial curation
keeps the existing 10 mm / 5 mm and reprocessed 10 mm results active; the earlier experiments/preview are archived.

Archiving hides a result without deleting or moving files. Missing discoveries retain their preferences and appear
as Unavailable in the manager. New discoveries start active in Ungrouped. Reload restores the current tab's result and
layer from session storage, provided that result is still active and available. A fresh tab uses the available active
default, then group/name order. Metadata edits and Refresh preserve the current active result/layer and camera;
setting the default does not switch immediately. Archiving the current result cancels its draft and uses the same
fallback, or clears geometry/tags if no active result remains. Restore does not replace another displayed result.

GET `/api/v1/scans` remains an array with original asset identities plus library metadata and compact processing
details. GET/PUT `/api/v1/scans/library` reads/saves the preference document; PUT sends its expected `revision` and
returns the incremented revision. Invalid documents are 422, stale edits 409, and filesystem errors are visible.
The store uses a short local lock and atomic sibling-file replacement. A missing preference file is empty revision
zero; malformed existing data is never reset. Failed edits remain available to correct; conflicts refresh preferences
and require an explicit retry. Asset serving remains unchanged, including for archived results.

Each result row also exposes a pencil to rename it and a trash can to delete it. The deletion confirmation names the
result and path, explains what is removed and initially focuses Cancel. Confirming deletes the published run directory
(including generated assets, exports, logs and working copies) or the loose preview PLY, then removes its library
preferences and clears a matching default. It never follows a linked result path or accepts a path outside the owned
result/preview directory. Original capture databases and physical measurement records remain unchanged. Measurements
can consequently retain a source-run ID whose geometry has been deleted. An unavailable result can have its retained
preferences removed as well.

DELETE `/api/v1/scans/library/result` accepts `key` and expected `revision`, returning the updated library document.
A stale revision is rejected before file deletion. Filesystem deletion and the subsequent atomic preference save are
not one transaction: a filesystem/save failure is reported plainly and the UI refreshes discovery to reflect any
files already removed. Deleting the displayed result uses the same active fallback/empty-view behaviour as archive.

The toggle follows the [WAI button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/), with its stable name,
pressed state and keyboard activation. The bottom stage/save prompt uses a polite status region, following
[WAI status-message guidance](https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html). Validation remains
adjacent to the input. This is not a comprehensive accessibility audit.

## Joint correction model

Use a batch GTSAM factor graph with camera poses and tag landmarks as unknowns. Connect them through the original
odometry and loop-closure constraints and tag observations. Add measured distances between landmark centres, with
uncertainty for both physical measurements and image/depth observations. Use robust losses where appropriate for
outliers, and expose inconsistent constraints for inspection.

For endpoint positions $p_a$ and $p_b$ and a measured distance $d_{ab}$, display the signed distance residual:

$$
e_{ab} = \lVert p_a - p_b \rVert - d_{ab}.
$$

GTSAM provides a point-to-point range factor; see its
[range-factor bindings](https://github.com/borglab/gtsam/blob/develop/gtsam/sam/sam.i).

Anchor the graph to remove arbitrary global translation and rotation. Pairwise distances alone do not establish the
van's coordinate axes, and a sparse or poorly distributed measurement network may leave some motion weakly constrained.
Retain the original graph measurements; use saved optimised poses as initial estimates, rather than deriving new
odometry measurements from those poses and treating them as independent evidence.

Optimising landmark markers alone does not correct the dense scan. Their observations must constrain the camera
poses, and reconstruction must use those corrected poses.

Pose optimisation also cannot correct every LiDAR error. A rigid transform of one frame preserves distances within
that frame. Persistent depth scale, bias or local distortion would need a separate correction model supported by
measured residuals. Begin with camera and landmark optimisation; add depth calibration only if the sample justifies it.

Retain the original result and correction inputs/settings so Gert can compare source and corrected results.
Keep independent check measurements outside the optimiser.

## Reconstruction limits

Reproject the original RGB-D frames using corrected camera poses, then assemble a coloured point cloud. Open3D can
also fuse RGB-D observations into a truncated signed distance field (TSDF) and extract a mesh. See its
[RGB-D integration documentation](https://www.open3d.org/docs/latest/tutorial/pipelines/rgbd_integration.html).

Deliver the corrected cloud first. Add meshing once the cloud and measurements support it. Keep the cloud available
beside the mesh: surface reconstruction can fill poorly observed regions, and a smooth mesh is not evidence that
those surfaces were captured. Open3D documents this behaviour for
[Poisson reconstruction](https://www.open3d.org/docs/release/tutorial/geometry/surface_reconstruction.html).

Compare before/after geometry and report input residuals separately from independent check errors. Inspect local
regions as well as long spans. A low error on distances used by the optimiser does not establish accuracy elsewhere.
If errors vary by location, investigate capture, correspondence or depth issues before applying a global scale change.

Filter and downsample display geometry as needed, while retaining the original observations for reconstruction and
measurement refinement. Serve binary geometry assets and small metadata documents rather than large point arrays in
the project's JSON files. Measure actual scan sizes before choosing more elaborate rendering mechanisms.

## Align to the van and refine CAD

Keep scan processing and optimisation in metres. Store a separate scan-to-vehicle alignment and convert units once at
the CAD/display boundary. Keep every camera, tag, constraint and geometry layer consistent with that transform.

Use the existing [CAD coordinate conventions](cad-model.md):

- X runs across the van from the left/passenger side to the right/driver side.
- Y runs from the rear doors toward the cab; Y = 0 is the rear opening at its side pillars.
- Z points upward; Z = 0 is the finished plywood floor. The current model places the bare vehicle floor about 18 mm
  lower.

Choose measured references for alignment. Account for the actual floor build-up when locating a bare-interior scan.
Keep alignment independent of furniture-local coordinates and the browser's optional cabinet-side reflection.
Pairwise distances correct internal relationships; identifying the vehicle frame is a separate operation.

#### Reusable tag-based axes

The alignment solver takes an explicit definition as input. It contains no tag assignments, van dimensions, target
frame name or implicit project-file lookup. A definition supplies the origin tag, the tags whose local normals
establish up, and two tag pairs defining the positive X and Y directions. `data/scan-alignment.json` is this van's
data: origin 1, up normals from 1 and 17, X from 2 to 3, and Y from 1 to 11. The target frame is named `van_trial`.
That origin is provisional, not the measured CAD rear-opening/finished-floor datum.

The solver averages the up normals with consistent signs, projects both direction references into that plane, and
uses SciPy's [align-constrain algorithm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.align_vectors.html)
to hold up fixed while fitting perpendicular X/Y axes equally to the two noisy direction references. It translates
the selected origin to zero, without changing scale or assuming tag 11's height. Diagnostics retain angular agreement
and the transformed reference positions, including floor-tag height residuals.

Supply the same definition explicitly for future captures whose physical tag positions are unchanged:

```sh
uv run --locked --extra scan campervan scan process data/new-capture.db \
  --output .local/scans/new-capture --alignment data/scan-alignment.json
```

Or align an existing completed run without reconstruction or texturing:

```sh
uv run --locked --extra scan campervan scan align .local/scans/van-5mm \
  --alignment data/scan-alignment.json
```

Each capture solves its own transform from its detected poses. No definition means no alignment; a missing required
tag is reported as unaligned, with no guessed substitute. An explicitly supplied unreadable/invalid definition is an
error. `alignment.json` and `run.json` retain the transform, definition snapshot and diagnostics. Geometry, camera
poses and tag observations stay in their original scan frame. The viewer applies the common transform to geometry
and tag overlays at display time; any later camera/constraint display or CAD consumer must apply that same transform.
The view fits once when changing coordinate frames, then preserves navigation between layers and captures sharing
the reference frame. A different physical tag layout requires a different definition.

Gert and Codex then use the scan, measurements and useful cross-sections to refine the build123d model. The current
body surfaces also supply cabinet-fitting volumes through `body_space` and `interior_limits` in
[`cad/body.py`](../src/campervan/cad/body.py). Extend that shared geometry source when refining the vehicle envelope.

Keep the dense scan as reference geometry outside fabricated parts and the cut list. CAD solids remain the source for
fabrication dimensions, cutting optimisation and model-derived material requirements. Validate fitted edges against
the physical van before cutting final stock.

## Storage and local operation

Keep lightweight scan metadata, measured constraints and alignment separate from large binary assets. Decide which
inputs belong in Git during implementation. Back up irreplaceable raw databases separately from regenerable caches;
the existing ignored `.local/` cache alone is not a preservation strategy for original scans.

Use subprocesses through the existing backend for expensive native processing. Display real failures and keep the
previous complete result available. Avoid an additional service, job platform or changes to BOM and Plan ownership.
The final file layout and asset formats remain open until a sample establishes the data requirements.

## Licensing considerations

The main proposed libraries permit proprietary commercial applications under their respective terms: build123d uses
[Apache-2.0](https://github.com/gumyr/build123d/blob/v0.13.0/LICENSE), Three.js and Open3D use
[MIT](https://github.com/mrdoob/three.js/blob/r184/LICENSE) and
[MIT](https://github.com/isl-org/Open3D/blob/main/LICENSE), and GTSAM and RTAB-Map use
[BSD-3-Clause](https://github.com/borglab/gtsam/blob/develop/LICENSE.BSD) and
[BSD-3-Clause](https://github.com/introlab/rtabmap/blob/master/LICENSE).

Retain the required notices when distributing software and inspect the exact packaged dependencies. OpenCascade,
underneath build123d, uses
[LGPL-2.1 with an exception](https://occt3d.com/dev/doc/overview/html/occt_public_license.html),
with library-source and linking obligations when distributing it. RTAB-Map's
[upstream licensing guidance](https://introlab.github.io/rtabmap/#license) warns about nonfree/SURF configurations;
do not assume a prebuilt desktop package has suitable terms for a commercial product. These are packaging
considerations, not a complete dependency licence audit.

## First milestone and open decisions

Carry one small, physically measured capture through the complete path:

1. Import its database and confirm RGB, depth, calibration, poses and original graph links are available.
2. Display the original cloud, camera poses and tag observations.
3. Enter measured distances, retaining separate independent checks.
4. Optimise camera poses and landmarks, then rebuild and display the corrected cloud.
5. Compare the independent check errors and inspect the geometry before expanding to the whole van.

Gert's visual inspection and the recorded physical measurements provide acceptance evidence.

Before implementation, resolve the following from the sample and Gert's requirements:

- Required accuracy over furniture-sized distances, and how it will be assessed.
- The actual iOS database version, capture settings and available per-frame data.
- Native RTAB-Map tooling and Python 3.13 dependency compatibility on the development Mac.
- The target family, measured tag sizes and practical measurement uncertainty.
- The references used for scan-to-vehicle alignment.
- Whether multiple captures, changed door configurations and mesh output belong in the first version.
- Durable storage, backup and Git policy for the original scans and derived assets.

## Repeatable local processing

### Browser import

In **Manage scans**, each named capture group has **Add capture databases…**. Choose multiple original `.db` files or
drop them onto the group. The review dialog lists filenames/sizes, existing reusable imports and frame counts after
validation. Choose a new tag layout for moved/new tags, enter its name and printed black-square size, and choose the
result name, 5/10 mm fusion resolution and optional photo texture. Only AprilTag 36h11 is currently supported. Existing
managed layouts can be reused explicitly while the tags remain fixed. No previous axis definition is applied to a new
layout. **Process captures** uploads the sources and starts the same CLI pipeline used below.

Source imports live at `data/scan-captures/<capture-id>/<original-name>.db`, with a small capture metadata file. The
server streams uploads to disk, validates the RTAB-Map schema/version/frame availability read-only, then publishes the
import. Identical uploaded bytes within one group reuse the existing capture identity. Failed/incomplete uploads are
removed. Sources are independent of generated runs and survive result deletion.
New tag metadata lives at `data/scan-tag-layouts/<layout-id>/layout.json`, with a separate empty `measurements.json`.
The library's optional `group_layouts` map remembers a group's preferred layout. Group membership does not establish
physical tag compatibility; the user chooses the layout explicitly.

The app starts one reconstruction subprocess at a time using its own Python environment and the existing CLI. Stages
come from real pipeline output; full stdout/stderr is saved under `.local/scan-jobs/` and a bounded tail is visible in
the dialog. The group has **Show processing progress…** after processing starts. Closing the dialog does not stop the
job. **Show result in viewer** opens a published result; successful results are assigned to the chosen group without
replacing other library preferences. Optional photo failure can still expose the published baked result. Failures show
diagnostics and retain sources for a manually requested rerun. Stopping/reloading the API interrupts processing;
there is no automatic resume or retry. A hard process crash is not a managed recovery mechanism.

Measurement GET accepts optional `tag_layout_id`; PUT/DELETE resolve the submitted layout to its own measurement store.
The no-query GET selects the original trial document. On result changes the frontend loads the matching document and
ignores stale reads from a previous selection. Creating a layout does not reuse measured distances, optimise geometry
or set vehicle axes.

API: GET `/api/v1/scans/imports` lists imported sources, managed layouts and processing summaries; POST
`/api/v1/scans/captures?group_id=...&filename=...` streams one raw database body; POST `/api/v1/scans/layouts` creates
a layout; POST `/api/v1/scans/process` accepts group, capture IDs, layout ID, result name and scan settings; GET
`/api/v1/scans/process/{job_id}` returns current stage, status, error and log tail. IDs address registered imports/layouts,
not arbitrary client filesystem paths. No extra server, environment setting or package was introduced.

The picker plus optional drop interaction follows [GOV.UK file-upload guidance](https://design-system.service.gov.uk/components/file-upload/),
including explicit file selection and reuse of uploaded files. Stage text is a polite status region; upload progress is
determinate, reconstruction progress is indeterminate. These choices require Gert's visual interaction acceptance.

### CLI processing

On macOS, download `RTABMap-0.24.2-Darwin-Tahoe-Apple-Silicon-cv4.dmg` from the
[official 0.24.2 release](https://github.com/introlab/rtabmap/releases/tag/0.24.2), verify its SHA-256 against the
[release checksums](https://github.com/introlab/rtabmap/releases/expanded_assets/0.24.2), and drag `RTABMap.app` to
`/Applications`. The verified DMG hash was `e1ada2b05fb274287b6a3d8f3785224afc9ba13422b948500afad2d7e7d11872`;
the installed app occupies 677M according to `du -sh`. Its bundled libraries are used automatically in RTAB-Map child
processes. Both installed tools reported version 0.24.2 with g2o enabled on macOS 26.6.2 arm64; their version invocations
loaded only app and system libraries. CAD-only use does not require RTAB-Map.

The optional `CAMPERVAN_RTABMAP_BIN_DIR=/path/to/bin` setting selects a directory containing the required executables;
it is authoritative and does not fall back to another location. Without it, macOS uses the installed app and Linux
uses PATH. Linux runtime compatibility has not been exercised. Each completed run records the resolved executable
paths and hashes, together with the native version, in `run.json`.

The scripting entry point is `campervan scan process`; `uv sync --locked --extra scan` installs only its Python scan
dependencies:

```sh
uv sync --locked --extra scan
uv run --locked --extra scan campervan scan process \
  data/261107-170546-van-int.db data/261107-171946-van-int.db data/261107-172733-van-int.db \
  --output .local/scans/van-new-5mm --voxel-mm 5 --sdf-trunc-mm 25 \
  --tag-family 36h11 --tag-size-mm 80
```

This example uses the original trial captures; substitute the paths and tag size for another capture set. Use a fresh
output directory. A single prepared database without tag detection uses its saved optical camera poses. Multiple database paths
are first merged with RTAB-Map/g2o on working copies; a single database with tag settings is also reprocessed to detect
the targets. Disconnected sessions fail explicitly. Optional paired
`--tag-family 36h11 --tag-size-mm 80` flags enable marker detection during merging. These are nominal marker
settings, not measured centre-to-centre constraints. `--poses path/to/poses.json` can instead supply corrected
camera-to-world matrices in metres, keyed by the exact exported node IDs. This is the future GTSAM integration seam;
no custom measured-distance optimiser has been implemented yet.

Fusion uses Open3D 0.20's CPU `VoxelBlockGrid` TSDF backend. The planned legacy `ScalableTSDFVolume` returned empty
geometry on actual RGB-D data; [upstream issue #7592](https://github.com/isl-org/Open3D/issues/7592) documents its
internal double depth scaling. The tensor backend uses the correct native millimetre depth input and avoids modifying
library code or changing the project's Python version.

RGB is downsampled to native depth resolution for colour fusion; depth is not interpolated. Each frame's intrinsics
are scaled accordingly. Native optical camera exports already include the camera-local transform, which must not be
applied again. The initial input is registered, single-camera iOS RGB-D; unsupported non-rectified calibration fails
rather than guessing registration. Depth-confidence values below `--depth-confidence-min` (default 50 on the exported
0–100 scale) are excluded when a confidence image exists. Absent confidence is recorded, not fabricated.

The pipeline removes small disconnected components and non-manifold vertex fans before UV generation. It preserves
the full mesh under `working/` and records geometry counts. Default display budget is 500,000 triangles; the UV atlas
uses four partitions to keep processing practical on the local CPU. `--uv-partitions 1` favours fewer UV islands at
potentially much greater processing time. Voxel size, truncation, depth range, component threshold, triangle budget,
texture size and partition count are explicit command settings.

### Baked colour and photographic texturing

The default **Baked colour** layer uses fused vertex colours baked into a UV texture. This makes a conventional
textured asset but does not recover photographic detail beyond the mesh's colour sampling.

For **Photo texture**, add `--texture-mode photo`. OpenMVS projects the original exported RGB images onto the same
cleaned Open3D display mesh. Its geometry decimation and hole closing are disabled; view selection uses the existing
texturer. It does not rerun structure-from-motion or replace Open3D reconstruction.

The pinned OpenMVS 2.4.0 has an [upstream colour-sampling bug](https://github.com/cdcseacave/openMVS/issues/1251)
in seam levelling. Its defaults produced black and fluorescent patches in our actual texture atlases even though the
input photos were normal. The processor explicitly passes `--global-seam-leveling 0 --local-seam-leveling 0`.
This preserves the source photo colours but leaves exposure/colour differences between neighbouring photo patches.
Do not enable those options with the pinned binary; reconsider them only after evaluating an upstream-fixed build.

The official OpenMVS v2.4.0 release supplies macOS ARM64 binaries. For this Mac, install them locally as follows:

```sh
mkdir -p .local/tools/openmvs-2.4.0
curl -fL https://github.com/cdcseacave/openMVS/releases/download/v2.4.0/OpenMVS_macOS_arm64.zip \
  -o .local/OpenMVS_macOS_arm64.zip
unzip -q .local/OpenMVS_macOS_arm64.zip TextureMesh InterfaceCOLMAP -d .local/tools/openmvs-2.4.0
```

The processor finds `InterfaceCOLMAP` and `TextureMesh` on PATH or in that directory. The COLMAP text scene is only
an interchange of known cameras/images: no COLMAP installation or new reconstruction is required. Camera conversion
inverts the optical camera-to-world transform and accounts for InterfaceCOLMAP's half-pixel principal-point convention.

Open3D's direct `project_images_to_albedo` is not used: its implementation requires x86/IPP despite the general API
prose saying CPU-only. See the [0.20.0 implementation](https://github.com/isl-org/Open3D/blob/v0.20.0/cpp/open3d/t/geometry/TriangleMesh.cpp).

### Outputs and viewing

A completed run writes `run.json`, including source hashes, versions, settings, pose source, included/omitted frame
IDs, geometry counts, timings and a public asset list. `frames.json` and `poses.json` retain the reconstruction inputs.
`processing.log` retains native commands and diagnostics. `working/` contains native exports, database copies and the
full-resolution mesh. Incomplete geometry/baking runs retain diagnostics without appearing as completed results.
If optional photographic texturing fails after baking completes, the completed Open3D layers remain available and
the manifest records the photo error; the command still exits unsuccessfully.

Open **Scan → Refresh scans**, choose the run, then select Cloud, Coloured mesh, Baked colour or Photo texture.
**AprilTags (count)** toggles labelled tag centres and outlines on every layer. These are the saved RTAB-Map landmark
estimates in the scan's coordinate frame, drawn through surfaces so hidden tags can still be located. The current
captures contain IDs 1–17 and recorded 80 mm sizes. Their positions are not surveyed vehicle coordinates.
Future runs export these poses and observation counts automatically; they are retained in `run.json` and returned as
small metadata by the scan-list API. The decoder follows RTAB-Map 0.24's
[saved-pose implementation](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/src/DBDriverSqlite3.cpp) and
[matrix compression format](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/src/Compression.cpp).
Runs with external camera poses omit the original tag estimates until correspondingly corrected landmark poses are
available. The overlay uses the existing camera projection and does not affect geometry, camera fit or navigation.
The toggle uses a native labelled checkbox, following the same WAI labelling guidance as the other controls.

The initial selection prefers a processed run and its baked/coloured mesh; loose point-cloud previews appear after
processed runs and are labelled "point cloud only". The photographic layer is labelled experimental: inspection in
the live viewer found severe colour artifacts in the first atlases; corrected atlases were regenerated with seam
levelling disabled and the 10 mm result was inspected in the live viewer. Capture/mesh quality remains approximate.
Refresh retains an existing selection. These defaults keep the reconstruction visible while retaining native labelled
selects, consistent with [WAI form-control labelling guidance](https://www.w3.org/WAI/tutorials/forms/labels/).
Switching layers and captures retains projection, zoom, rotation and pan, including changes made while assets load.
Use the existing Fit control to frame a different capture when needed. This avoids unexpected viewport changes while
comparing results; it follows the predictability intent of
[WAI On Input guidance](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html), without claiming a compliance audit.
Camera controls and the view cube remain
shared with CAD. Assets are served only from completed manifests, with path containment enforced. New controls use
native labelled selects/buttons and the existing tab keyboard behaviour, following the
[WAI-ARIA tabs guidance](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/); this is not a comprehensive accessibility audit.

These are unmeasured visual trials. Original captures remain unchanged and need their own backup. `.local/scans` is
ignored derived storage, not archival storage. Browser uploads invoke the same `process_scan` function through the
existing CLI in an API-managed subprocess. GTSAM distance adjustment uses explicit Preview corrections → Update mesh;
measured CAD-datum alignment and physical validation remain later work.

### Trial outputs from 8 November 2026

- `van-5mm`: 850 saved camera frames, 1,429,180 fused points and 495,197 display triangles, with baked colour and
  photographic variants. Native photo texturing took about nine minutes.
- `van-10mm`: the same merged capture at 10 mm, with 249,504 display triangles and both texture variants. Native photo
  texturing took about four minutes; this is a useful smaller comparison with `van-5mm`.
- `van-raw-10mm`: rebuilt from the three original databases, with 848 camera frames and 249,621 display triangles,
  with both texture variants. Session merging uses g2o; this is not GTSAM measured-distance optimisation.
- `van-quick-baked`: a fresh command from the merged database through published baked assets completed in 36.1 seconds,
  using 10 mm voxels, a 100,000-triangle budget and a 2048-pixel atlas.

The early trials resumed retained geometry during implementation fixes; their manifests identify that continuation
and omit unavailable whole-run timings. Visual comparison and dimensional validation have not been performed.

The three photographic results were subsequently regenerated with both seam-levelling options disabled, fixing the
black/fluorescent corruption. `run.json` records this correction and `working/photo-correction.log` retains the native
diagnostics. Earlier broken atlases remain in `working/photo-broken-seam-leveling/` for diagnosis. Meshes and camera
poses were unchanged. Orange texture patches identify faces without a selected photo; they are not van colours.
