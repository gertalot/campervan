# Repeatable scan reconstruction implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task by task. Repository
> instructions prohibit tests, service startup and unsolicited delegated review passes; those restrictions override
> generic skill workflows. Checkbox steps track implementation, not a test suite.

**Goal:** Turn one or more RTAB-Map databases into inspectable Open3D clouds, cleaned meshes and textures through a
repeatable local command, starting with Gert's unmeasured trial capture.

**Architecture:** RTAB-Map supplies decoded RGB-D frames, calibration and poses. A Python processing function performs
Open3D fusion, cleanup and texture generation independently of CAD regeneration. A CLI calls that function now; a
future upload action in the existing FastAPI application can call the same entry point in a subprocess.

**Tech stack:** Python 3.13 through uv, installed RTAB-Map 0.24.2 native tools, Open3D 0.20.0, existing FastAPI and
TypeScript/Three.js CAD renderer. OpenMVS is a separately evaluated photo-texturing addition, not a replacement
reconstruction pipeline.

**Spec:** [Photogrammetry workflow](../../photogrammetry.md), specialised by Gert's decisions in this conversation:
this is an ad-hoc visual trial; tag distances have not been measured; scripting is acceptable; future captures must
use the same process; eventual database drag-and-drop belongs in the existing web UX.

## Global constraints

- Do not create or run tests. Use existing static checks, actual capture processing and Gert's visual inspection.
- Do not start services or browsers. Browser inspection, only when requested, uses Chrome DevTools MCP.
- Never access `.env`, `.env.test` or `.envrc`; access `.beads` only through `bd`.
- Preserve original databases and unrelated working-tree edits. Do not commit capture binaries.
- Keep the documented RTAB-Map → camera/tag optimisation → Open3D → Scan/CAD architecture.
- For this trial, use saved poses without measured-distance factors. Do not invent measurements or claim accuracy.
- GTSAM-based measurement optimisation remains a later milestone; do not label native g2o processing as GTSAM.
- Keep processing in metres in the scan frame. Vehicle alignment and conversion to CAD millimetres remain separate.
- Reuse the installed renderer, shared Three.js runtime, camera module and one existing OCP connection.
- No new service, queue, job platform, automatic retry system, collision framework or general pipeline framework.
- Approved for implementation by Gert after the plan was written. Commands below are now implemented.

## Current evidence and boundaries

- `src/campervan/cli.py` owns argparse commands. Its `site` branch demonstrates running an offline operation before
  resolving service settings. Follow that pattern so scan processing starts no services and needs no CAD rebuild.
- `frontend/src/scan.ts` currently loads loose PLY files from `data/`, with native renderer navigation and separate
  camera persistence through `viewer-camera.ts`.
- `src/campervan/api.py` lists and serves those PLY files. Preserve those existing routes and previews.
- `frontend/src/renderer.ts` exposes the installed renderer's Three.js namespace. Addons must use that same namespace.
- `data/van-interior-merged-tags.db` contains 890 RGB-D frames; the saved graph contains 850 camera nodes plus
  17 landmarks, used by the current preview. Report included/excluded frame IDs rather than assuming every frame
  has an optimised pose.
- Three raw trial inputs are `data/261107-170546-van-int.db`, `data/261107-171946-van-int.db` and
  `data/261107-172733-van-int.db`. They contain multiple internal sessions; file count is not session count.
- The database requests GTSAM, but the installed RTAB-Map build has g2o and no GTSAM. Record the actual available
  optimiser and pose provenance. Saved settings alone do not establish how a previous result was computed.
- No trial measurements exist. Nominal 80 mm 36h11 tags and shared observations may aid merging, but are not an
  independent dimensional validation.
- Open3D 0.20.0 publishes a Python 3.13 macOS ARM64 wheel. Its direct `project_images_to_albedo` implementation still
  requires x86/IPP. Do not plan to call it successfully on this Apple Silicon Mac.

## Deliverables and command contract

First deliverable: Open3D fused cloud, cleaned coloured mesh, UV-baked colour texture and Scan-tab inspection.
Second deliverable: photo texture comparison on the same Open3D geometry, using OpenMVS's texturing stage if its
native installation and camera conversion are feasible. These outputs must be labelled distinctly.

Proposed initial command:

```sh
uv run --locked --extra scan campervan scan process data/van-interior-merged-tags.db \
  --output .local/scans/van-trial-5mm --voxel-mm 5
```

Repeat at 10 mm with a different output directory to compare surface quality. The command must also support multiple
database paths. With multiple inputs, merge working copies through RTAB-Map before extraction; do not overlay their
independent coordinate systems. Optional `--tag-family 36h11 --tag-size-mm 80` enables explicit marker detection during
that merge. Without those flags, do not assume new captures use the same tags.

Use a new output directory for each run and refuse to overwrite an existing one. Suggested output layout:

```text
.local/scans/van-trial-5mm/
  run.json                    # Written last, marks a complete published run
  processing.log              # Native commands, progress and actual diagnostics
  working/                    # Working DB copies/merge and native extraction outputs
  frames.json                 # Node IDs, per-frame calibration, paths and inclusion decisions
  poses.json                  # Explicit camera-to-world matrices, keyed by working DB node ID
  cloud.ply                   # Fused reference cloud
  mesh.ply                    # Cleaned mesh with vertex colours
  colour/mesh.obj              # UV-baked colour mesh, material and texture sidecars
  photo/mesh.obj               # Optional photographic variant, material and texture sidecars
```

`run.json` records schema version, ordered input paths and SHA-256 hashes, input database/tool versions, exact commands,
actual pose source, settings, frame counts and omitted IDs, geometry counts, elapsed stage times and an asset list.
Relative paths resolve inside the run directory. Record which working database owns each frame ID; retain originals
and their graph data instead of trying to infer original odometry from saved optimised poses.

The CLI prints stage progress and the final run directory. Failure exits nonzero and identifies the failed stage.
Keep its log/intermediates for diagnosis, but do not publish a completed manifest. Existing completed runs remain
available. No resume engine or automatic caching is needed initially.

## File responsibilities

| File | Responsibility |
| --- | --- |
| `src/campervan/scans.py` (new) | Run settings/manifest, orchestration, native extraction and pose normalisation |
| `src/campervan/scan_reconstruction.py` (new) | Open3D fusion, cleanup and texture baking |
| `src/campervan/scan_texturing.py` (second deliverable) | OpenMVS camera conversion and photo-texturer invocation |
| `src/campervan/cli.py` | Offline `scan process` command |
| `pyproject.toml`, `uv.lock` | Pinned Open3D dependency in a `scan` optional extra |
| `src/campervan/api.py` | Completed-run discovery and bounded asset serving |
| `frontend/src/scan.ts`, `renderer.ts`, `style.css` | Cloud/mesh display and shared navigation |
| `README.md`, `docs/photogrammetry.md` | Practical capture-to-viewer commands and actual implementation status |

Avoid importing Open3D when serving unrelated CAD/planning routes. Install the processing extra with
`uv sync --locked --extra scan`; processing commands use `uv run --locked --extra scan ...`.

## Review focus

1. RGB/depth resolutions, per-frame intrinsics, optical axes and inverse transforms must describe the same camera.
2. Disconnected sessions, absent saved poses and missing depth must be visible failures/omissions, not a plausible
   looking overlay or silent switch to a different pose source.
3. Changed settings/new captures must create distinct runs without touching originals or replacing a good result.
4. Baked colours must never be presented as full-resolution photographic textures or measurement validation.
5. Loading and switching cloud/mesh layers must retain camera framing and release replaced GPU resources.

## Task 1: Establish the native extraction and output contracts

**Files:** `scans.py`, processing dependency declarations, `docs/photogrammetry.md`.

- [x] Pin Open3D 0.20.0 in the `scan` extra; resolve the existing uv environment without changing unrelated dependency
  versions. Confirm import/version through Python 3.13 on this Mac. Do not install another Python environment.
- [x] On a working copy of the merged trial DB, use RTAB-Map's `--images_id`, `--poses_camera`, `--poses_format 11` and
  `--opt 2` exports. Source inspection confirms ID-named RGB/depth images, per-frame calibration files and camera poses
  are supported. Inspect actual filenames, depth types/units and camera-model transforms before implementing parsing.
- [x] Confirm saved optimised poses exist before requesting `--opt 2`: RTAB-Map otherwise permits an optimisation
  fallback. Fail plainly instead of silently changing the intended pose source.
- [x] Join exported images/calibration/poses by node ID, never filesystem order or rounded timestamp. Record missing
  data and excluded nodes. Confirm the merged capture's actual usable frame count; 867 is prior evidence, not a rule.
- [x] Establish RGB/depth registration and intrinsics scaling from native calibration. Preserve depth discontinuities;
  never resize depth with bilinear interpolation. Apply the camera's local transform exactly once.
- [x] Establish `poses.json` as node-ID-keyed 4×4 camera-to-world matrices in metres. Open3D integration consumes their
  inverses. Keep camera optical axes separate from the viewer's Z-up world convention.
- [x] Confirm built-in Open3D OBJ export preserves UVs, colours/materials and texture sidecars, and list the actual
  emitted assets. Use its existing writers rather than inventing a mesh/texture serialization format.

**Evidence:** Record the actual native commands, export formats, included IDs and calibration conventions in the
photogrammetry document. This is real input processing, not a new test harness. Stop if calibration cannot be resolved
correctly; do not guess a transform to make the image look aligned.

## Task 2: Add one reusable processing function and CLI

**Files:** `scans.py`, `cli.py`.

**Interfaces:** Define `ScanSettings` with `voxel_mm=5`, `sdf_trunc_mm=25`, `depth_max_m=4`,
`min_component_triangles=200`, `target_triangles=500000`, `texture_size=4096`, `uv_partitions=4`, optional paired tag family/size, and
`texture_mode="baked" | "photo"`. Expose
`process_scan(inputs: list[Path], output: Path, settings: ScanSettings, poses: Path | None = None) -> Path`, returning
the completed `run.json` path. `poses`, when supplied, follows Task 1's exact frame/coordinate contract.

- [x] Add the offline `scan process` argparse branch before `load_settings()`. Accept multiple positional inputs,
  required output directory and explicit settings flags. Expose `--poses` for future corrected poses without adding
  a placeholder GTSAM implementation.
- [x] Validate positive units/limits, supported input schemas and non-overlapping input/output paths. Hash and copy
  originals before invoking tools; native tools operate on copies. Never replace an original DB or completed run.
- [x] For multiple inputs, call `rtabmap-reprocess` sequentially with the provided input order, explicit available
  optimiser (`--Optimizer/Strategy 1` on the current build) and optional tag settings. Reject disconnected sessions
  using its supported disconnected-session option; preserve the failed derived DB for inspection.
- [x] For one prepared database use saved poses; for a newly merged database use that merge's saved result; for
  explicit pose input validate matching frame IDs and record the external file's hash. These are explicit provenance
  choices, not interchangeable fallback paths.
- [x] Stream real native diagnostics to terminal/log using direct subprocess calls with argument arrays and
  `check=True`. No shell interpolation, additional service, retry layer or readiness protocol.
- [x] Write the completed manifest only after required outputs exist. Print settings, actual optimiser availability,
  omitted frames and final run path. Preserve useful diagnostics on failure.

**Evidence:** Process the merged trial input through extraction once. Later use the raw three-file input as the
separate multi-session acceptance case, without rebuilding previously completed runs needlessly.

## Task 3: Fuse and clean geometry in Open3D

**File:** `scan_reconstruction.py`.

**Interfaces:** `reconstruct(frames_path: Path, poses_path: Path, output: Path, settings: ScanSettings) -> dict` returns
geometry counts and asset-relative paths for the run manifest. Task 2 calls it after extraction.

- [x] Integrate frames in stable node-ID order using `VoxelBlockGrid` CPU TSDF with RGB colour integration (see execution record), recorded voxel
  size/SDF truncation and actual depth scale/calibration. Read frames incrementally to bound memory.
- [x] Mask invalid depth and use recorded depth-confidence data where available and interpretable; record whether it
  was available/applied. Do not invent confidence for captures that lack it.
- [x] Extract and save the fused cloud and full mesh before simplification. Apply duplicate/degenerate/unreferenced
  geometry cleanup and small connected-component filtering, recording removals. Treat empty results as failures.
- [x] Simplify the mesh toward the triangle budget before UV generation. Preserve a full-resolution intermediate
  under `working/`. Do not close all holes, flatten panels or apply aggressive smoothing by default.
- [ ] Compare 5 mm/25 mm and 10 mm/50 mm voxel/SDF settings in separate runs. Report timings/counts, with Gert judging
  broad surfaces, pillars, wheel arches, gaps and duplicated edges. Keep both results available.

**Evidence:** Actual successful reconstruction and Gert's visual comparison. No dimensional-error claims without
independent physical measurements. Do not add photometric pose optimisation that silently supersedes GTSAM's future
ownership of geometry poses.

## Task 4: Produce a baked colour texture

**File:** `scan_reconstruction.py`.

**Interface:** `bake_colour_texture(mesh_path: Path, output: Path, texture_size: int) -> list[Path]` returns all emitted
mesh/material/texture assets. It operates on Task 3's cleaned display mesh.

- [x] Generate a UV atlas with Open3D's `compute_uvatlas`; handle non-manifold geometry with its existing cleanup
  functions and report removals. Do not assume a mesh must be watertight to display it.
- [x] Bake the mesh's fused vertex colours into an albedo texture with `bake_vertex_attr_textures`, then export OBJ,
  material and texture sidecars. Preserve the mesh's geometric frame and units.
- [x] Label this output **Baked colour**, distinct from **Photo texture**. A larger atlas must not be described as
  recovering detail absent from the vertex colours.
- [x] Include all sidecars in the manifest asset list. If baking fails, retain the cloud/coloured mesh intermediates
  and report the failed stage; do not claim that a textured run completed.

**Evidence:** Inspect actual output assets and load them through Task 5. Native macOS ARM64 baking capability is to be
confirmed during execution; the known x86 restriction applies to direct photo projection, not a promise that every
other Open3D operation has already run on this machine.

## Task 5: Inspect completed runs in the existing Scan tab

**Files:** `api.py`, `frontend/src/scan.ts`, `renderer.ts`, `style.css`.

- [x] Extend `GET /api/v1/scans` with completed run entries from `.local/scans/*/run.json`, retaining loose `data/*.ply`
  previews and their existing download route. Include run ID, label, geometry counts and available layers.
- [x] Add `/api/v1/scans/runs/{run_id}/assets/{asset_name}` for manifest-listed assets only. Resolve paths beneath the
  corresponding run, reject traversal/symlink escapes, and do not expose working databases or arbitrary local paths.
- [x] Extend the existing selector and add **Cloud**, **Coloured mesh**, **Baked colour**, and, when present,
  **Photo texture** choices. Show only applicable point-size controls and give empty/error states plainly.
- [x] Use Three.js OBJ/MTL addon loaders and the shared renderer runtime. Export only constructors the addons require
  from `renderer.ts`; do not introduce another Three.js copy or another OCP connection.
- [x] Preserve scan coordinates, camera framing and the existing view cube when changing layers. Dispose replaced
  geometry, materials and textures; prevent a late load from replacing a newer selection.
- [x] Display textured scans without adding misleading CAD lighting to baked photographic illumination. Identify the
  run as an unmeasured trial in its metadata/status, not with an intrusive warning flow.
- [x] Consult current primary accessibility guidance for the added labelled controls and keyboard operation and record
  the decisions. Gert performs interaction checks; do not launch browser automation or services.

**Evidence:** Gert can switch between cloud and mesh at the same viewpoint and see the same surfaces at the same scale.
Existing PLY previews and CAD navigation continue to work. Partial runs never appear as completed results.

## Task 6: Compare actual photo texturing on the same Open3D mesh

**Files:** `scan_texturing.py`, `scans.py`, processing documentation; native tool setup only as necessary.

- [x] Confirm an OpenMVS `TextureMesh` CPU build can be installed/run on this Mac and capture its version. There was no
  confirmed Homebrew formula in the research. Do not promise a one-line installation or quietly introduce an x86
  Python environment, remote service or another reconstruction stack if native setup fails.
- [x] Convert exported calibrated images and Task 1's selected poses into OpenMVS's supported scene representation.
  Establish the conversion against the installed version's source/docs. Avoid new SfM or MVS depth reconstruction.
- [x] Implement `texture_mode="photo"` as the same reconstruction and baked-colour steps followed by photographic
  texturing. Keep both texture variants in the completed run so their comparison uses identical geometry.
- [x] Run only `TextureMesh` against Task 3's unchanged Open3D mesh, with geometry decimation and hole closing disabled
  (`--decimate 1 --close-holes 0`). Use its existing view selection and seam-levelling options.
- [ ] Export a separate OBJ/material/texture set and record settings, selected image IDs and native diagnostics.
  Compare it against the baked-colour variant on identical geometry in Scan.
- [x] If native installation/conversion proves impractical, report the concrete limitation and keep the completed
  Open3D result. Do not silently relabel baked colours as the photographic deliverable. Any broader platform change
  requires Gert's decision under AGENTS.md.

**Evidence:** Successful native texturing and Gert's comparison of seams, ghosting, photographic detail and uncovered
surfaces. Unobserved surfaces remain identifiable; do not synthesize photographic evidence through inpainting.

## Task 7: Document, verify and hand off

**Files:** `README.md`, `docs/photogrammetry.md`, this plan.

- [x] Document the scan-extra installation and exact implemented commands for a prepared DB, several raw DBs and
  comparison settings. Include where outputs/logs live and how to open a completed run in Scan.
- [x] Distinguish original captures from disposable `.local/scans` products and explain that originals need their own
  backup. Do not move/delete Gert's existing captures or change Git policy for unrelated `data/` inputs.
- [x] Record actual implemented stages, versions, timings, image/calibration conventions and outstanding limits.
- [x] Run `make check` once after implementation. Diagnose any failures in changed code; report unrelated failures
  without expanding scope. No tests, new test scaffolding or browser interaction checks.
- [ ] Ask Gert to inspect the trial outputs in his existing app tab. Never start/restart services on his behalf.

Completion requires the first deliverable to be visible and reusable with another input/run. Report the photo-texture
comparison separately as complete or concretely blocked; a baked texture is not completion of that comparison.

## Later milestones, deliberately outside this implementation

- **GTSAM measured reconstruction:** Import original graph constraints/tag observations and add optional physical
  distances with uncertainties and separate check measurements. Output corrected poses using the same frame contract,
  then rerun reconstruction. Preserve the documented optimisation architecture; no measurement prerequisite now.
- **Database drop zone:** Add upload/file-picker UI to Scan, persist raw inputs safely, and call `process_scan` in a
  subprocess from the existing API. Show real progress and errors. No new processing implementation or service.
- **Vehicle alignment/CAD overlay:** Add a separate measured scan-to-vehicle transform; preserve original scan assets.

## Primary sources and verification limits

- [RTAB-Map 0.24.2 exporter](https://github.com/introlab/rtabmap/blob/0.24.2/tools/Export/main.cpp): ID-based image and
  calibration export, optical camera poses and saved-pose fallback behaviour.
- [RTAB-Map optimiser selection](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/src/Optimizer.cpp): unavailable
  GTSAM falls back to g2o where available. Local `--version` previously confirmed the installed build's capabilities.
- [Open3D RGB-D integration](https://www.open3d.org/docs/latest/tutorial/pipelines/rgbd_integration.html): TSDF fusion,
  RGB integration and the resolution/noise trade-off.
- [Open3D mesh API](https://www.open3d.org/docs/latest/python_api/open3d.t.geometry.TriangleMesh.html): UV generation,
  simplification and attribute texture baking.
- [Open3D 0.20.0 source](https://github.com/isl-org/Open3D/blob/v0.20.0/cpp/open3d/t/geometry/TriangleMesh.cpp):
  direct photo projection's x86/IPP restriction, which overrides the less specific API prose saying CPU-only.
- [Open3D distribution](https://pypi.org/project/open3d/): Python 3.13 macOS ARM64 package availability.
- [OpenMVS TextureMesh](https://github.com/cdcseacave/openMVS/blob/master/apps/TextureMesh/TextureMesh.cpp): external
  mesh input, geometry-preserving options and seam levelling. Native installation/conversion remain unverified.

At plan-writing time, only code/docs and native exporter source were inspected. Execution evidence follows.

## Execution record — 8 November 2026

Implemented the CLI, reusable processing function, native extraction/merge, Open3D tensor fusion, manifold cleanup,
colour baking, OpenMVS photo texturing and completed-run Scan viewing. No services or tests were started. No delegated
review passes or automatic commits were performed; existing CAD edits remain separate.

Decisions established by actual processing:

- Legacy `ScalableTSDFVolume` produces empty geometry in Open3D 0.20.0 because it divides metric depth twice
  ([upstream #7592](https://github.com/isl-org/Open3D/issues/7592)). The documented tensor `VoxelBlockGrid` backend works
  with explicit millimetre depth and preserves the planned Open3D/TSDF stage.
- Saved graph entries include tag landmarks. There are 850 usable saved optical-camera frames, not 867 cameras.
  Reprocessing the original three databases yielded 848 usable frames; omissions are recorded by ID.
- Edge-only cleanup was insufficient for UVAtlas. Removing non-manifold vertex fans made both meshes parameterisable;
  removals are recorded, and the original full mesh remains available.
- Requested UV partitions default to four after multi-minute single-partition processing was observed. Open3D may
  choose a larger actual partition count. More UV islands are the trade-off; this does not alter the mesh geometry.
- Native baking returns float colours; convert albedo to UInt8 with scale 255 before PNG export. Use the tensor mesh
  writer to preserve materials and texture sidecars.
- OpenMVS v2.4.0 has official ARM64 binaries. Camera conversion uses its COLMAP interface, including the half-pixel
  principal-point correction. Its output argument must have an extension (`mesh.mvs`), and its process working
  directory is the run's `working/` directory. These choices keep relative images/logs/assets inside their run.
- OpenMVS writes opaque material values as `Tr=1`; the photo layer uses MTLLoader's documented inversion option.
  Baked colour layers retain the ordinary material convention. Textures are displayed unlit without multiplying
  them by the original vertex colours.

Outputs available for Gert's inspection:

| Run | Source | Display triangles | Available result |
| --- | --- | ---: | --- |
| `van-5mm` | Existing merged database, 850 cameras | 495,197 | Cloud, coloured mesh, baked colour, photo texture |
| `van-10mm` | Existing merged database, 850 cameras | 249,504 | Cloud, coloured mesh, baked colour, photo texture |
| `van-raw-10mm` | Three raw databases, native g2o merge, 848 cameras | 249,621 | Cloud, coloured mesh, baked colour, photo texture |
| `van-quick-baked` | Existing merged database, 850 cameras | 99,134 | Fresh one-command baked run; 36.1 seconds |

Early trial runs were continued from retained geometry/UV intermediates while implementation defects were fixed.
Their manifests say so and do not invent full-run timings. Superseded scratch copies were removed after retaining
failure diagnostics; original `data/*.db` files were untouched. The new command was separately run from input through
published baked assets. The denser 5 mm photo-texturing stage took about nine minutes on this Mac.

Verification: focused Ruff checks, formatting and mypy pass for the processing modules and CLI. Repository `make check`
stops on 32 pre-existing Ruff findings. Full mypy also reports existing planning/cutting/CAD/API annotation errors;
frontend type checking reports the existing `plan-dropdown.ts:82` `onfocusout` error. These unrelated issues were not
changed. Browser rendering, geometry quality and the 5/10 mm comparison await Gert's visual inspection. No dimensional
accuracy is claimed; physical tag-distance measurements and GTSAM correction remain later work.
