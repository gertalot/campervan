# Van scanning, measurement and CAD workflow

Status: workflow recorded 6 November 2026; local reconstruction added 8 November 2026. The CLI extracts RTAB-Map RGB-D
captures and uses Open3D for TSDF fusion, cleanup and colour baking, with optional OpenMVS photo texturing. Scan displays
the resulting clouds and meshes. Database import, local processing progress and per-layout measurement editing are
available in the browser as of 9 November. Joint GTSAM analysis, explicit corrected reconstruction, and measurement
suggestions are implemented; physical/visual acceptance remains pending. CAD overlay remains unimplemented.

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
    └─ Proposed Scan tab: navigate, measure, optimise and compare with CAD
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

### 1. Prepare reference targets and measurements

Place flat, stationary AprilTags around the region to capture. Use a supported tag family and unique IDs for distinct
physical targets. Record the family, IDs and actual printed tag dimensions; the tag-size convention concerns its
border, not the paper margins. AprilTag pose estimation uses camera calibration and known target size.
See the [AprilTag pose-estimation documentation](https://github.com/AprilRobotics/apriltag#pose-estimation).

Distribute targets across the interior, including different heights and long spans. Measure straight centre-to-centre
distances with a suitable physical measuring tool. Record units and estimated measurement uncertainty. A distance
following curved trim or a bent tape is not the straight-line constraint represented in the application.

Assign each measurement one of two roles:

| Role | Use |
| --- | --- |
| Optimisation input | Constrain the reconstructed positions of its endpoints. |
| Independent check | Assess the result without contributing to the optimisation. |

Keep the tags and the surfaces they describe fixed during a capture. Treat different door positions or other changed
geometry as separate configurations rather than forcing them into one static reconstruction.

### 2. Capture and export from RTAB-Map iOS

Start with a small representative region, such as a rear corner, before scanning the whole van. Capture overlapping
views of the surfaces and targets, including revisits that support loop closures.

Save and transfer the original RTAB-Map `.db` file. Also export a point cloud or mesh if useful for an initial preview.
The iOS app supports database export, geometry export and AprilTags; see its
[official description](https://apps.apple.com/ca/app/rtab-map-3d-lidar-scanner/id1564774365).

Retain the database even after exporting geometry. A fused PLY or OBJ alone generally lacks the frame relationships
needed to rebuild the scan after changing camera poses. Confirm that the chosen capture settings retain the RGB-D
frames and calibration needed by this workflow. Record the app version and relevant capture settings with the scan.

### 3. Import frames and the original graph

Inspect a real database before choosing the importer. Prefer calling RTAB-Map's native tools from Python over
reimplementing its compressed formats. Its tools include database inspection, image and geometry export, reprocessing
and graph inspection. See the
[RTAB-Map command-line reference](https://introlab.github.io/rtabmap/api/latest/tools.html).

Python's `sqlite3` reads the tables, but compressed depth, calibration and transform blobs need RTAB-Map-specific
decoding. The schema also varies with database version. Use a limited, version-aware reader where native exports do
not supply what the optimiser needs. The
[database implementation](https://github.com/introlab/rtabmap/blob/master/corelib/src/DBDriverSqlite3.cpp) and
[exporter](https://github.com/introlab/rtabmap/blob/master/tools/Export/main.cpp) provide the source references.

Preserve these inputs:

- Frame and node IDs, timestamps, RGB images and depth images, plus depth confidence where available.
- Camera intrinsics, image dimensions, depth units and sensor-to-node transforms.
- Original odometry and loop-closure links, their uncertainty, and available landmark observations.
- Initial and saved optimised poses, with an explicit record of their coordinate convention.

A list of camera poses alone is insufficient for recreating the optimisation problem. Confirm which export supplies
the original graph links and information matrices. Translate pose conventions and covariance ordering explicitly.

Keep the imported database unchanged. Store measurements, manual corrections and derived outputs separately so another
optimisation can start from the same original observations.

### 4. Inspect the scan and define distances

Add a Scan tab inside the existing application. Give it a dedicated scene and controls while sharing the existing
Three.js runtime. Keep the current OCP CAD viewer and avoid another OCP WebSocket connection. Reuse cached tessellated
CAD geometry for the scan overlay; any new asset endpoint should use the existing FastAPI application.

The proposed view provides:

- Orbit, pan, zoom and fit controls, with camera poses and image viewpoints available for inspection.
- Coloured point-cloud and optional mesh layers, AprilTag IDs and centres, and a CAD overlay.
- Selection of two arbitrary reference points, with snapping to recognised tags for measured tag pairs.
- Straight constraint lines, measured-distance entry, uncertainty, and input/check roles.
- A list of constraints showing measured and reconstructed distances and signed errors.
- An Optimise action, visible processing status or errors, and refreshed geometry that preserves the camera view.

Use a visible measurement mode so selecting or dragging endpoints has a clear meaning alongside camera navigation.
Retain normal focus and text editing while entering measurements. Show numerical errors alongside any colour coding.
The detailed interaction design remains part of implementation planning.

For precise tag measurements, select the tag identity and inspect its original RGB observations. Retain detected image
corners and centres by frame. If RTAB-Map does not retain the required image observations, detect them again in the
saved RGB frames. Known tag size, depth and observations from multiple viewpoints can support the initial 3D estimate.

Support manual correction of an observation in its image or on the observed surface. A click in an RGB image defines
a ray; depth or multiple views are needed to locate it in 3D. Retain the originating frame, image coordinates and any
surface/depth association. Saving only a world-space XYZ position would lose the relationship after reconstruction.
Associate repeated observations of the same physical tag with one landmark.

#### Implemented tape-measure interaction

The Scan viewer's tape icon (**T**) selects tag centres, highlights the endpoints and previews a line to the pointer
or hovered destination. A second tag establishes the pair. Its bottom Distance field starts with an existing physical
measurement or the current scan distance, separately labelled. The distance is full 3D centre-to-centre, independent
of display alignment. First numeric typing replaces the prefill without an extra field click. Accepted units are
`mm`, `cm`, `m`, `in` and `ft`; bare values mean mm. Enter validates and saves a positive finite value in metres.

Escape discards dirty text and restores the previous value, leaving the pair selected; another Escape cancels the
pair. At the first-tag prompt, Escape exits the tool. Measurement shortcuts are handled before the renderer's own
shortcuts, preserving normal text-field and menu handling. The status line overlays the viewer without resizing it.
Clicking empty canvas cancels unfinished work. Camera drags over 4 px, pinch and wheel zoom do not commit or
cancel it. Switching captures or leaving Scan discards the draft. Tool preference survives layer/tab changes; turning
it off hides its lines. Saved lines are green and labelled; editing is gold and the rubber-band line is dashed.
The tool temporarily shows tags even when the ordinary tag toggle is off. Tag targets support keyboard focus and
Enter/Space while measuring. The tape button shows its T shortcut. A contextual Restore / Cancel pair / Done button
executes the same action as Escape; there is no generic Scan actions menu.

The toolbar's **Manage measurements…** button lists saved tag pairs, measured distance, current scan distance and signed residual.
It opens independently of tape mode without discarding the active draft. It supports
editing and explicit removal. Missing endpoints show Unavailable. Selecting a reversed pair edits the same record.
An API/save error keeps the draft visibly unsaved. Revision conflicts refresh stored values and require another Enter.
Prefills are never stored merely by selecting a pair; accepting one requires explicit Enter.

Physical constraints live in a separate, explicitly supplied measurement document. Its version-1 schema contains a
`tag_layout_id`, `revision` and `distances`. Each record stores canonical positive `tag_a < tag_b`, `distance_m`,
`entered_text`, `source_run_id` and nullable `sigma_m`. Compatible optional fields are `default_sigma_m` and
`excluded_pairs` (canonical tag IDs and a physical-access reason). No XYZ positions or fitted distances overwrite these
observations. A missing per-pair sigma uses an explicitly entered default; no noise is inferred from decimal places.
The original supplied `data/scan-measurements.json` started empty; later entered values belong to the user.

The app stores measurements alongside its project file as `scan-measurements.json`, just as the planner stores its
own adjacent data file. No environment setting is required. The reusable store still takes an explicit path, and
the offline pipeline still requires `--measurements FILE`; neither contains this van's tag identities or distances.

Run processing/alignment accepts explicit `--measurements FILE`, recording the document's layout ID without applying
its distances. All current completed runs have been associated this way. New captures can reuse the document while
the physical tags remain fixed. Different arrangements require another ID/document; matching tag numbers alone do
not establish compatibility. Saving requires both tags in the selected run and a matching layout ID. The file persists
independently of reconstruction outputs, using a short locally serialized revision check and atomic file replacement.

The existing API provides GET `/api/v1/scans/measurements` and PUT/DELETE
`/api/v1/scans/measurements/{tag_a}/{tag_b}`. PUT accepts revision, layout ID, distance in metres, entered text and
source run; DELETE accepts revision and layout ID. Mutations return the updated document. Invalid input is 422,
layout/revision conflicts are 409, and filesystem errors are shown plainly. Existing scan asset routes remain intact.
Saving a distance still does not run GTSAM or rebuild anything automatically. The analysis workflow below is explicit.

#### Implemented analysis, acceptance and recommendations

`frontend/src/side-panel.ts` owns the shared right-side shell for Manage scans and Manage measurements: header/title,
accessible X, context/actions/status/body slots, scrolling, Escape/focus restoration and single-panel ownership.
The scans manager is modal; measurements is nonmodal for viewport inspection. Domain controllers provide content and
keep their own state. Neither panel participates in the viewer grid or changes canvas size. Closing measurements hides
its unapplied overlay, retaining the draft in that tab while inputs remain current; a fresh load never activates an
unapplied preview. Modal import/delete confirmations remain separate.

The panel supplies an editable 3 mm default when no measuring precision has been saved. Analyse and Suggest more are
not disabled by blank/invalid/unsaved precision fields: clicking validates, shows inline field errors and focuses the
problem, or saves valid precision and proceeds. Save precision remains a separate optional action. Existing saved
precision is retained. The default is a visible modelling assumption, not a claim about Gert's actual measuring error.

**Analyse uncertainty** uses that saved precision. It snapshots the selected run/layout and measurement
revision, leaving the measurement file untouched. Original RTAB-Map transforms/information come from retained 0.24
SQLite Link rows. Saved global poses initialise the fit; they are not turned into invented independent observations.
Inverse stored edges are deduplicated only when transforms/information agree. Links outside the saved localised graph
are counted as excluded; saved graph nodes remain even when their images were omitted. Gravity uses the recorded
Optimizer/GravitySigma and native attitude-factor convention. The graph format records its source hash and each
exported optical camera's local transform. Existing runs extract this derived graph without repeating fusion.

GTSAM 4.3.0 Pose3 between/prior/attitude factors model camera/landmark observations, and robust Huber Pose3 range factors
add physical distances. When gravity observes global roll/pitch, only translation/yaw gauge is fixed; otherwise the
root pose is fixed. An existing absolute prior replaces this gauge constraint. Disconnected/unobservable graphs yield
diagnostics and qualitative possible connections, never finite-looking scores produced by arbitrary weak priors.

The preview shows fitted tag positions/movement vectors over the unchanged original surface. The list compares
original/fitted distances and residuals, marking downweighted readings. Covariance summaries compare the scan-only
model with the scan-plus-current-distances model, linearised at their fits. Joint pose covariance is transformed to
world tag-centre covariance, retaining cross-correlations. Approximate 95% intervals are conditional on those noise
assumptions; they are not an empirical calibration of LiDAR bias or physical accuracy.

**Apply** validates measurement revision plus source manifest/graph/mesh hashes and solution-history revision, then
starts a new reconstruction through the existing scan worker. Corrected optical poses and matching landmarks are
supplied together. It reuses retained RGB/depth/confidence via hard links, so deleting a source result does not remove
the corrected result's frame copies. Original observations are retained in its graph. Original DBs, distance records,
source manifest and geometry remain unchanged. Corresponding explicit alignment roles are recalculated where present;
new layouts receive none implicitly. Successful corrected results stay in the same group/layout and compatible camera
frame, labelled distance-adjusted. Rebuild failure keeps the accepted solution and original surface for explicit retry.
Automatic result selection does not interrupt an active tape draft/text field; Show corrected result remains available.

**Revert** clears an unapplied preview or returns to its source result after acceptance, including after reload. It
does not undo physical measurements, later precision edits or delete results. Accepted entries/history are stored in
project-adjacent `scan-solutions.json`; immutable analysis snapshots/poses/covariance are under `.local/scan-analyses/`.
Editing a distance, precision or physical exclusion invalidates earlier analysis/suggestions. Stale Apply is 409 and
requires explicit reanalysis. Analysis, suggestions and rebuild share the existing single-active-subprocess owner.

**Suggest more** enumerates all unmeasured pairs and predicts the effect of adding one independent range with the
chosen precision. Each candidate updates the full correlated tag-centre covariance using a rank-one information
update. Its score is the largest reduction in approximate 95% half-width across all tag-to-tag target dimensions.
The default 5 mm threshold is editable; all qualifying pairs are returned, not a top-one/top-N shortlist. Rows identify
the affected dimension, before/after interval and overlapping gain profiles. Individual gains share a baseline and
cannot be summed. Outlying/low-precision measured pairs are separately offered for remeasurement. New observations
invalidate the old report before another analysis/suggestion request.

Physical clearance uses Open3D finite mesh rays between centres plus nearby clearance rays. Endpoint tolerance is
twice the fusion voxel size. Large preview movements relative to the source mesh yield Unknown. For rays with no
obstruction, source depth/calibration/poses must show free-space coverage of the sampled interior segment; missing
surfaces alone never establish clearance. Mixed neighbouring hits, incomplete coverage and missing geometry remain
Unknown. Obstructed pairs and manually excluded pairs are hidden by the default filter but inspectable. A manual
Not physically measurable reason handles reach/access and unmodelled obstacles. This is not a hand-reach simulator.

API: PUT `/api/v1/scans/measurements/settings` saves revisioned default/per-pair precision and exclusions. POST
`/api/v1/scans/analyses` creates a snapshot/job; GET `/api/v1/scans/analyses/{id}` returns job/preview/acceptance state;
POST suffixes `/apply`, `/revert` and `/suggestions` perform those explicit actions. Status includes bounded native logs,
stale-input flags and qualitative diagnostics when applicable. No new service or automatic retry was introduced.

#### Result library

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

### 5. Optimise camera poses and landmarks

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

Retain the original result and each accepted correction's inputs and settings so Gert can compare or revert results.
Keep independent check measurements outside the optimiser.

### 6. Reconstruct and assess the result

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

### 7. Align to the van and refine CAD

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
The no-query GET and original document remain compatible with the old trial. On result changes the frontend loads the
matching document and ignores stale reads from a previous selection. Creating a layout does not reuse measured distances,
optimise geometry or set vehicle axes.

API: GET `/api/v1/scans/imports` lists imported sources, managed layouts and processing summaries; POST
`/api/v1/scans/captures?group_id=...&filename=...` streams one raw database body; POST `/api/v1/scans/layouts` creates
a layout; POST `/api/v1/scans/process` accepts group, capture IDs, layout ID, result name and scan settings; GET
`/api/v1/scans/process/{job_id}` returns current stage, status, error and log tail. IDs address registered imports/layouts,
not arbitrary client filesystem paths. No extra server, environment setting or package was introduced.

The picker plus optional drop interaction follows [GOV.UK file-upload guidance](https://design-system.service.gov.uk/components/file-upload/),
including explicit file selection and reuse of uploaded files. Stage text is a polite status region; upload progress is
determinate, reconstruction progress is indeterminate. These choices require Gert's visual interaction acceptance.

### CLI processing

The scripting entry point is `campervan scan process`, available after installing the optional scan dependencies:

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
existing CLI in an API-managed subprocess. GTSAM distance adjustment now uses the explicit analysis/Apply workflow;
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
