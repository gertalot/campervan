# Van scanning, measurement and CAD workflow

Status: proposed workflow, recorded 6 November 2026. Scan import, scan viewing, AprilTag measurements and scan
optimisation are not implemented in this repository. RTAB-Map, GTSAM and Open3D are proposed additions.

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
