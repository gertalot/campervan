# Capture/reconstruction implementation plan

**Goal:** deliver quick RTAB-Map previews and actual photographic reconstruction through the existing capture UX.
**Spec:** [approved section 4](spec.md#4-stage-1--review-capture). [Flow folder](./).
**Scope:** C1–C8 only. This replaces the database-only stage-1 delivery plan for this revision; it does not implement
the other five stages. The original [stage-1 plan](stage-1-plan.md) remains the record of the delivered shell.
**Architecture:** extend the capture store, importer and subprocess runner. Keep Open3D for quick previews; add one
photographic producer using PyCOLMAP and the installed OpenMVS tools. Publish through the existing library/renderer.
**Stack:** Python 3.13/uv, existing OpenCV/Open3D/Three.js, PyCOLMAP 4.2.1, pillow-heif 1.8.1, OpenMVS 2.4.0 binaries.

## Global Constraints

- Approved spec commit: `8d4b76a`; reviewed decisions: [single-pass record](reviews/04-capture-reconstruction-spec.md).
  Starting branch `develop`, current working directory, no worktree. The working tree was clean before this plan.
- **Do not create or run tests, builds, lint, browser automation or benchmark campaigns.** Repository `AGENTS.md`
  overrides generic TDD/review instructions. Do not start services/browsers; Gert starts any needed app process.
- No per-task review agents, nested reviewers or task approval gates. Execute locally, then perform one accumulated
  source review and Gert's visual inspection. Reuse this plan's evidence; do not repeat checks without a changed input
  or concrete failure. Flow transitions must retain these explicit overrides, not reintroduce its generic test loops.
- Preserve source files, saved measurements, current results, group ownership, selection and camera state. No legacy
  workflow adapters, schema migration framework, copied tag coordinates or per-batch physical-layout assignments.
- Upload supported databases/photos into the same group; detailed processing accepts an explicitly selected mixture.
  Never silently include older captures, select a hidden top-N set, or require a preview before original-photo input.
- Only install the two approved additions using precompiled wheels through the existing uv environment. No Homebrew,
  source compilation, native upgrades, separate environment, CUDA/Mac work, Windows worker or implicit UI installer.
- Keep RTAB binary configuration and the existing OpenMVS tool resolver. Do not redesign packaging or configuration.
- Later scene understanding, tag-placement suggestions, measurement fitting, axes editor and corrected photo rebuild
  remain out of scope. Their current Upcoming state remains honest. Do not adapt all numerical consumers in advance.
- Current-stage verification owners: implementer for source inspection and one real photographic baseline (T6),
  Gert for pointer/keyboard interaction and visual acceptance. The only final shell check is `git diff --check`.
  There is no automated integration suite/gate. C8 is actual requested processing, not a synthetic test campaign.
- If an unverified technology assumption becomes necessary, follow the spec's focused technical-check rule. That is
  not permission to reopen tool selection, add reviews or expand scope. Stop on a genuine binary/tool incompatibility.

## Scope Traceability

| Criterion | Implementation | Final verification owner and focused evidence |
| --- | --- | --- |
| C1: named actions, no texture checkbox or preview prerequisite | T5 | T6/Gert: open both actions from Review capture and Manage scans; original photos can start an empty group |
| C2: repeatable database preview/tags | T1/T2/T5 | T6: trace preview dispatch to existing `process_scan`; Gert inspects/repeats a normal preview when needed |
| C3: complete photographic pipeline for original/database photos | T1–T4 | T6: one `scan reconstruct` baseline; native logs/model and published mesh establish actual stages, not just buttons |
| C4: explicit inputs, per-result tags, same group and preserved measurements | T1/T2/T4/T5 | T6: compare request/result source IDs and group; inspect unchanged measurement paths; Gert changes selected inputs |
| C5: geometric tag support, honest scale/units | T3/T4/T5 | T6: inspect baseline tag-support/scale record and rejection paths; Gert sees located versus unsupported detections |
| C6: shared progress/cancel/errors/retry/handoff | T2/T5 | T6: source-trace process-group cancellation, failed/partial publication and interaction token; Gert exercises normal app actions |
| C7: master/shaded/texture layers and camera retention | T4/T5 | T6: baseline asset paths/counts; Gert compares shaded full mesh/texture without a reset |
| C8: bounded existing-data floor/sill baseline | T6 | Implementer: exact selected image list, one actual pipeline invocation/log, resulting untextured mesh; Gert judges useful detail |

Focused task checks below are source inspections, not independent runtime gates. T6 owns the final accumulated
checkpoint and records evidence at `reviews/05-capture-reconstruction-completeness.md`. Mark unperformed visual
acceptance pending; never claim a source inspection proves that an interaction or reconstruction looks correct.

## Review Focus

Only these approved direct risks inform the final source review:

1. Explicit mixed-source selection, duplicate filenames and group moves/deletion retain the intended source files.
2. Camera/lens grouping, image orientation, pixel conventions and uniform scale agree across images/poses/tags/mesh.
3. Photographic geometry really comes from dense stereo, retains sparse tracks and is refined before simplification.
4. Worker/native cancellation, native failure and texture-only failure remain visible without losing earlier results.
5. Units, tag support and camera state are correct when switching preview, metric photo and unscaled photo results.

## Execution map and direct contracts

Reuse confirmed in `scan_processing.py`, `scan_processing_api.py`, `scans.py`, `scan_texturing.py`, `cli.py`,
`scan_groups.py`, `scan_library.py`, `scan_alignment.py`, `scan-import*.ts`, `scan-library*.ts`, `scan.ts`,
`scan-workflow-panel.ts` and `scan-job-status.ts`. `scan_texturing.texture_photos` currently writes empty sparse
points and textures a depth mesh; it must not be called as the detailed geometry producer.

New bounded modules:

| File | Responsibility |
| --- | --- |
| `src/campervan/scan_photos.py` | Prepare selected original/database images and their stable source/calibration metadata |
| `src/campervan/scan_photogrammetry.py` | Photographic settings, COLMAP/OpenMVS chain, result publication |
| `src/campervan/scan_photo_tags.py` | 2D corner observations, supported triangulation, one scale estimate and existing tag-pose representation |

Keep third-party imports inside processing functions so missing optional dependencies do not prevent the app opening.
Use dictionaries/JSON consistent with current scan manifests; do not add a generic pipeline/plugin framework.

The request extends the existing `/api/v1/scans/process` contract, not a second endpoint:

```python
# In scan_processing.py, factor existing common request fields without changing their meaning.
class CaptureRequest(BaseModel):
    group_id: str
    capture_ids: list[str]  # nonempty, distinct IDs, all in this group
    layout_id: str         # existing tag settings/measurement association, not per-input layout bookkeeping
    name: Name

class PreviewCaptures(CaptureRequest):
    purpose: Literal["preview"]
    settings: ScanSettings = Field(default_factory=ScanSettings)

class ReconstructPhotos(CaptureRequest):
    purpose: Literal["photographic"]
    settings: PhotographicSettings = Field(default_factory=PhotographicSettings)

ProcessCaptures = Annotated[PreviewCaptures | ReconstructPhotos, Field(discriminator="purpose")]
```

`PhotographicSettings` in `scan_photogrammetry.py` retains the current display/texture defaults
(`target_triangles=500000`, `texture_size=4096`), with `num_threads=4`. Matching is exhaustive and dense processing
is native resolution as specified; those are recorded algorithm settings, not additional quality dropdowns.
Resolve tag family/size from the existing layout at job start, separately from user algorithm settings.

Capture responses add `kind: 'database' | 'photo'` and photo `width`/`height`. Derive kind from the validated stored
file type when reading the existing capture record, including existing `.db` records: it is a file classification,
not a legacy schema parser/migration. Databases keep their existing frame count; a still has one frame. Preserve
IDs, filename, group, byte count and SHA-256. Store any extra photo metadata beside the original in that capture's
existing directory, never a second photo store. No new physical-layout field on imported inputs.

The existing job JSON gains an immutable `request` member containing the worker input snapshot:

```text
purpose, name, group_id, tag_layout_id, tag_family, tag_size_mm, settings,
inputs: [{capture_id, kind, path, filename, sha256}], alignment_definition: optional existing definition
```

Resolved source paths refer to immutable input files. The frontend submits IDs, never filesystem paths. The server
retains current membership/path checks and snapshots the selected inputs/settings before launching the subprocess.
The CLI reads `request` from the supplied JSON, then creates its new output directory and retains a copy there.
Do not create extra sibling JSON files in `scan-jobs`: its existing discovery expects every JSON stem to be a job ID.

Extend the existing result manifest, keeping `schema_version=1`, `layers`, `assets`, `tags` and `geometry`:

```text
purpose: preview | photographic
units: m | arbitrary
scale: {status: metric | unscaled, factor, source, supporting_tag_ids, reason}
photo_reconstruction: {selected_image_count, registered_image_count, unregistered_image_ids,
                      component_summaries, selected_component_id, settings, versions, tag_support_asset}
inputs: exact selected source records; image_sources.json maps working images back to those records
tags: existing {id, pose, size_m, observations} for supported landmarks only
```

Original photos and working/derived image coordinates remain distinguishable. Missing optional provenance on
previously saved results stays Unknown in the existing details UI; no fake reconstructed metadata or result migration.
For unscaled photo tags, retain detection/triangulation evidence in the support asset but omit metric overlays
(`tags=[]`), because the existing tag renderer requires `size_m`. Show why; do not pretend arbitrary units are metres.

## Task 1 — Extend the existing input store and prepare photographic sources

**Spec coverage:** C2, C3, C4; §4.2 and binary dependency decision.
**Files:** `pyproject.toml`, `uv.lock`, `scan_processing.py`, `scan_processing_api.py`, `scans.py`, new `scan_photos.py`.

- [ ] Add pinned `pycolmap==4.2.1` and `pillow-heif==1.8.1` to the existing `scan` extra. During implementation only,
  run `uv lock` then `uv sync --locked --extra scan --no-build`. Stop on missing compatible wheels; never retry with
  source builds, Homebrew or another Python. Keep the approved OpenMVS binaries unchanged.
- [ ] Generalise the current upload route in place for `.db`, `.jpg`, `.jpeg`, `.png`, `.heic` (case-insensitive).
  Keep streaming/hash/temp-file cleanup, group checks and duplicate handling. Validate databases with `database_info`;
  validate photos using Pillow and registered pillow-heif. Retain the original bytes and actual dimensions.
- [ ] Produce the capture responses described above. Extract only the upload-finalisation code needed to reuse
  validation/storage; do not redesign the upload service or change group ownership.
- [ ] Implement `prepare_photo_inputs(inputs: list[dict], output: Path, log: Path) -> dict` in `scan_photos.py`.
  Give every working image a capture-ID-qualified name. Decode full-size working PNGs as needed for orientation/HEIC,
  retaining original file metadata and source coordinates in `image_sources.json`. No resize before the chosen tools.
- [ ] For selected databases, factor/reuse the native image-export portion of `extract_frames` in `scans.py`, rather
  than repeating merging/TSDF reconstruction. Read exported RGB/calibration as available; detailed reconstruction
  does not require fixed saved camera poses or depth. Do not copy database images from an already textured mesh.
- [ ] Group calibration by original EXIF camera/lens/focal setting and oriented dimensions; absent metadata gets a
  separate per-image group, not a guessed shared lens. Prepare groups as subdirectories and use COLMAP's
  `CameraMode.PER_FOLDER`; retain original EXIF-derived calibration information in prepared image metadata.

**Focused source check:** `rg -n 'kind|heic|prepare_photo_inputs|extract_frames' src/campervan/scan*.py`.
Confirm only explicit inputs are prepared and existing database originals are not rewritten. No processing run yet.

## Task 2 — Carry both purposes through the existing worker and progress contract

**Spec coverage:** C2, C3, C4, C6.
**Files:** `scan_processing.py`, `scan_processing_api.py`, `cli.py`; direct imports/types only where needed.

- [ ] Implement the discriminated request and immutable input snapshot above. Keep one-active-job handling and
  current capture/group/tag-settings validation. Reject a preview request containing selected stills with a useful
  message; uploading them remains allowed. Photographic requests accept either input kind or a mixture.
- [ ] Add `campervan scan reconstruct --request <request.json> --output <new-directory>` in `cli.py` for the photographic
  worker. Keep existing `scan process` as the preview CLI and dispatch preview jobs to current `process_scan` with
  baked colour only. No photo-texture checkbox/setting is accepted from the revised preview UI.
- [ ] In `ScanProcessing.start/_run`, snapshot inputs/settings as `job['request']` before launch, leaving it unchanged
  during stage/status updates; pass that existing job JSON to the photographic CLI. Reuse `_run`
  for both commands, process groups and `cancel_requests`; no second runner or poller. Record purpose on the job.
- [ ] Keep `[stage]` progress parsing and log storage. The photographic worker prints real stage names/counts and
  `Scan processing failed: <operation>: <actual error>` on failure; `_run` carries this concrete message into job.error.
  Do not replace native diagnostics with only an exit code. Logs keep the complete tool output.
- [ ] Preserve current manifest-before-nonzero-exit publication for texture-only failure: a completed geometry
  manifest can provide `result_key` while job state is failed and `photo_error` is visible. No result for an earlier
  failed dense/mesh stage. Cancel must not publish incomplete geometry or change selected old results.

**Focused source check:** `rg -n 'reconstruct|purpose|killpg|result_key|Scan processing failed' src/campervan/{cli,scan_processing}.py`.
Trace cancellation from shared UI to worker/native process group. Do not run fault-injection scenarios.

## Task 3 — Reconstruct photographic cameras and supported tags

**Spec coverage:** C3, C5; §4.3 steps 1–3 and §4.4.
**Files:** new `scan_photogrammetry.py`, `scan_photo_tags.py`; existing alignment owner reused unchanged unless its
direct tag-pose input requires a small correction.

- [ ] Implement `process_photos(request: dict, output: Path) -> Path` in `scan_photogrammetry.py` (returns run.json).
  Consume T1's prepared images and source map. Use `extract_features`/`match_exhaustive` on CPU, four threads where
  supported, then `incremental_mapping` with standard local/global BA. No fixed RTAB poses or LiDAR mesh seed.
- [ ] Select the component by registered-image count, sparse-point count, then component ID as specified. Write
  component/image-registration summaries; stop with an actual camera-reconstruction error if none exists.
  `undistort_images(..., output_type='COLMAP')` retains the standard camera/image/point/track interchange.
- [ ] Implement `localise_photo_tags(model, image_sources: dict, tag_family: str, tag_size_mm: float,
  output: Path) -> dict` in `scan_photo_tags.py`. Detect ordered corners on registered undistorted images using
  existing `cv2.aruco.DICT_APRILTAG_36h11`. Unproject with those exact cameras, converting OpenCV pixel centres to
  COLMAP's convention, then use `pycolmap.triangulate_multi_view_point`.
- [ ] Use the installed mapper's `filter_max_reproj_error`/`filter_min_tri_angle` defaults for track rejection;
  record resolved thresholds, support image IDs and rejection reasons. Reject nonfinite/behind-camera tracks.
  Four supported corners are required for a tag to contribute side lengths to scale. No single-view PnP fallback.
- [ ] Return `{tags, scale, support_asset}`. Estimate scale as the median of known-side/reconstructed-side ratios;
  use the existing corner ordering and right-handed tag pose convention so `TagAlignment` normals agree. Keep
  rejected/single-view detections as Detected but not located in `tag-support.json`. No tape-distance fitting.
- [ ] Apply the one uniform scale to the COLMAP reconstruction's camera translations/rig-frame transforms, sparse
  points and tag translations using its similarity-transform API before MVS import. With no scale, retain arbitrary
  units and support evidence. Do not copy an older preview's solved transform. Apply an available alignment
  definition through `tag_alignment` only after metric tag support exists; otherwise record the unaligned reason.

**Focused source check:** `rg -n 'extract_features|match_exhaustive|incremental_mapping|undistort_images|triangulate_multi_view_point|filter_min_tri_angle' src/campervan/scan_photo*.py`.
Trace one scale application, matching image/camera coordinates and omission of unsupported metric landmarks.

## Task 4 — Generate and publish photographic geometry

**Spec coverage:** C3, C5, C7; §4.3 steps 4–5, §4.5.
**Files:** `scan_photogrammetry.py`, `scan_texturing.py`, `scans.py`.

- [ ] Reuse `scan_texturing._tool` and `scans.native_command` for installed OpenMVS. Generalise only the native
  texturing invocation that both publishers need: accept an explicit scene and mesh path instead of duplicating
  texture command flags. Keep the existing 2.4 seam-levelling workaround; do not upgrade native tools.
- [ ] Run `InterfaceCOLMAP` on the real undistorted model with sparse points/tracks, then `DensifyPointCloud`,
  `ReconstructMesh`, `RefineMesh`, `TextureMesh`. Set CPU thread limits and dense `resolution-level=0`, with
  `max-resolution` at least the largest undistorted dimension. Set `decimate=1` through refinement/texturing; avoid
  automatic hole filling presented as observed detail. Log actual commands, stages, tool versions and dimensions.
- [ ] Keep native dense/depth/model/refinement artifacts. Export refined geometry to `working/full-mesh.ply` before
  any display simplification. Make `mesh.ply` as the separate current 500,000-triangle viewing copy; no additional
  parameter experiments. Publish cloud, simplified/full shaded surfaces and photographic OBJ/material/texture assets.
- [ ] Write the existing manifest shape plus the fields above; include tags freshly reconstructed from these sources.
  Keep geometry success inspectable if texturing alone fails, with `photo_error`, then propagate a failed job rather
  than claiming full completion. Failures earlier in the chain leave inputs/logs and previous results intact.
- [ ] Extend `completed_scans` to expose purpose, units, scale, photo summary and support-asset URL to direct frontend
  consumers. Keep `scan_asset`'s manifest allowlist/path checks. Do not expose arbitrary working paths or change
  artifact ownership. Reuse automatic full-mesh discovery for both new and already saved runs.

**Focused source check:** `rg -n 'DensifyPointCloud|ReconstructMesh|RefineMesh|TextureMesh|points3D|full-mesh|photo_error' src/campervan/scan_photo*.py src/campervan/scans.py`.
Trace geometry origin and stage ordering; do not equate triangle count with detail or accuracy.

## Task 5 — Expose both actions through the shared capture UX

**Spec coverage:** C1, C2, C4, C5, C6, C7.
**Files:** `frontend/src/scan-import-api.ts`, `scan-import.ts`, `scan-workflow-panel.ts`, `scan-library.ts`,
`scan-library-api.ts`, `scan.ts`, `scan-job-status.ts`, `style.css`; `scan_groups.py:move_item` only for its two
database-only error labels. Existing move/delete mechanics already operate on capture directories and need no redesign.

- [ ] Add `CapturePurpose = 'preview' | 'photographic'` and the capture/result fields above. Change
  `createScanImport.open` to `open(groupId, groupName, incoming=[], layoutId?, purpose?)`. With no purpose (file drop),
  show the two named actions before starting work; retain uploaded originals regardless of purpose.
- [ ] Replace Review capture's single Add databases button and the group Add databases action with
  `Create quick preview…` / `Create detailed reconstruction…`, both calling that importer. Change
  `createScanLibrary.addCaptures(resultKey, purpose)` and its `CaptureReviewHost` caller together. No duplicated forms.
- [ ] Show all imported database/photo source rows with explicit selected checkboxes, source type and frame count
  or pixel dimensions. Preserve the checked source set when switching purposes; surface incompatible preview
  selections, not silent dropping. Existing `open` preselection remains visible/editable; do not impose photo-only
  selection, hidden filtering or automatically include later imports in an already running request.
- [ ] Accept `.db,.jpg,.jpeg,.png,.heic` in the existing file/drop controls. Remove the texture checkbox and misleading
  Surface detail wording for photographic reconstruction; preview can retain its existing coarse resolution input.
  Labels/submit text describe the chosen action. Keep existing tag settings association without adding layout gates.
- [ ] Reuse `createJobView` and `jobStatus`. On geometry-only publication from a failed texture job, show the error
  and explicit Show result action; do not auto-open it as a completed textured job. Keep successful completion's
  interaction-generation guard. Show retry as an explicit new run using the visible selected input/settings snapshot.
- [ ] In result details, show purpose, exact source list, original/working dimensions, selected/registered counts,
  component omissions, tag-support summary and scale source. Unsupported detections are readable here/logs, not
  invented overlays. Keep only supported metric tags in the existing shared highlight/overlay owner.
- [ ] Replace `scan.ts`'s unconditional 'metres' status with the manifest units; old RGB-D outputs remain metric by
  their existing contract. For arbitrary units, keep visual inspection, mark scale unavailable and suppress metric
  readouts/actions. Keep lighting/layer switching and camera snapshots unchanged; do not add an axes editor.
- [ ] Give the two named actions concise contextual capture help from §4.2. Reuse existing button hover/pressed/
  focus styles and live status regions. Update imported-input group wording/drag labels to include photos; preserve
  actual group deletion/move semantics. Do not rebuild the scan manager or other shared UI.
  In `move_item`, replace 'imported database' with 'imported capture' in the two relevant messages, leaving its logic.

**Focused source check:** `rg -n 'Add photographic texture|data-photo|Create quick preview|Create detailed reconstruction|purpose|arbitrary' frontend/src/scan*.ts`.
Check no old checkbox/duplicate importer remains. Interaction acceptance is Gert's normal app use, not automation.

## Task 6 — One real baseline, final source review and factual documentation

**Spec coverage:** C1–C8; final verification owner for the whole revision.
**Files:** update `docs/photogrammetry.md` and the scan setup subsection of `README.md`; evidence stays in this Flow
folder at `reviews/05-capture-reconstruction-completeness.md`. Baseline inputs/outputs/logs stay under `.local/`.

- [ ] Prepare one explicit connected floor/sill photo set from the existing database RGB exports. Select it by
  inspecting the original photographs/known camera coverage, not an arbitrary top-N score or fixed four-view rule.
  Record the exact filenames/source node IDs and source run in `.local/experiments/photo-baseline/request.json`.
  Use the same `{"request": {...}}` envelope as the job runner, with resolved selected-photo records in `inputs`.
  This is capture-specific data, not tag IDs/van regions embedded in product code. Do not process all 1,068 frames
  blindly as a supposedly bounded experiment or perform another LiDAR reconstruction first.
- [ ] Run the implemented worker once through the same command used by the job runner:
  `uv run --locked --no-sync campervan scan reconstruct --request .local/experiments/photo-baseline/request.json --output .local/scans/photo-baseline-20261111`.
  The local request uses the worker snapshot shape above, with exact selected existing image paths and their source
  identities; T1 preparation accepts these resolved photo records. Save stdout/stderr beside the request. Publish
  the finished result into the source group with existing `ScanLibraryStore.associate`, not a new capture group or
  publication framework. Normal UI jobs already use that same library owner in T2.
- [ ] Record exit status, actual dependency/tool versions, input/registered counts, component omissions, scale/tag
  support, output asset paths, elapsed processing and available geometric result. Inspect the shaded geometry before
  its texture: did floor/sill relief improve over the preview? Ask Gert to inspect the result in their existing app.
  Do not claim metric accuracy without independent measurements or claim detail merely from a larger triangle count.
- [ ] If this one run fails, diagnose its actual failed stage and fix only a demonstrated implementation/integration
  defect. Do not retry quality knobs, swap tools/models, build from source or turn inadequate captured data into an
  endless experiment. Record source-quality limitations honestly; a failed pipeline is not C3/C8 completion.
- [ ] Review the accumulated scoped diff once against C1–C8 and the five Review Focus risks, including actual error
  propagation, cancellation ownership and units. Run `git diff --check` once. No tests/build/lint, browser checks,
  extra review agents, release gates or repeated verification processes. Record unresolved visual checks explicitly.
- [ ] Update practical documentation to distinguish preview depth fusion from real photogrammetry, the two actions,
  supported formats, binary-only setup, same-group repetition, tag/scale limitations, progress/cancel and the CLI.
  Explain that photo correction/scene understanding remain later work. Commit the coherent implementation and
  factual evidence without pulling unrelated edits into this revision.

## Self-review and handoff

One planning self-review completed: C1–C8 have owners; worker/request/result names agree; inputs precede SfM/tag
support, which precedes dense publication and UI handoff. The original layout-bookkeeping proposal is excluded.
Existing tag settings association is retained, not redefined as per-capture solved tag positions. No tests,
per-task reviewers, new services, video, native upgrades or later-stage implementations are in the execution map.
No installation, app changes or processing were performed while writing this plan.

The plan is ready for the user-invoked implementation phase. Do not automatically invoke it or plan stage 2.
