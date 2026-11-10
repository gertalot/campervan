# Capture/reconstruction implementation and single Flow review

Date: 11 November 2026. [Approved spec §4](../spec.md#4-stage-1--review-capture), [plan](../plan.md).
Base: `e9a123521a6f4d4a52bcf4ad4c6ba2d1cc8f2156`, branch `develop`, current checkout, initially clean.
Scope: C1–C8 and their direct input/job/result/viewer contracts. No unrelated project edits were included.
Plan-specific ledger: `.superpowers/sdd/plan-2026-11-10-capture-workflow-redesign/progress.md`.

## Outcome

Both capture actions use the shared importer/store/job owner/result library. The preview retains RGB-D fusion;
detailed reconstruction performs photographic features, matching, camera solving/BA, dense stereo, meshing,
refinement and texturing. Original JPEG/PNG/HEIC and explicitly selected database photographs are supported.
Per-result tags and scale come from photographic observations, without tape fitting or copied preview coordinates.
Later workflow stages remain Upcoming.

The real baseline is published in the source group as **Photo baseline — floor and sliding-door sill**, run
`.local/scans/photo-baseline-20261111`. Inspect **Shaded surface — full resolution** before evaluating its texture.
It uses a separately solved camera frame; use the explicit Fit control if the previously saved view misses it.

| Result | Actual evidence |
| --- | --- |
| Inputs | 51 original exported JPEGs, each 720 × 960, from source `capture-fdfb86a1-db42-4087-8863-8f26568da3c5` |
| Selection | All saved images in explicit ranges 890–927 and 967–981, chosen after inspecting the contact sheet for connected floor/sill and overlapping seat-base views |
| Cameras | 50 registered of 51 selected, real sparse points/tracks imported into OpenMVS |
| Dense cloud | 1,430,533 photographic points |
| Full refined master | 701,613 vertices; 1,402,821 triangles |
| Viewing copy | 250,192 vertices; 500,000 triangles |
| Texture | OBJ/MTL and one 4096-pixel atlas; native TextureMesh completed |
| Metric reference | Configured 80 mm black-square tags 5 and 18; uniform scale factor 0.07119871142444859 |
| Unsupported detection | Tag 11 detected in one registered image, retained as Detected but not located |
| Storage | 1,379,518,437 bytes for this run, including retained intermediates; original sources unchanged |
| Elapsed | 1,159.517 seconds from original worker start through manual handoff repair and final publication; not an uninterrupted runtime benchmark |

The actual untextured inspection shows the circular floor stamping and some pressed boundaries, with substantial
noise/faceting around reflective metal and pillar/occluded areas. This is not a fine-detail/accuracy certificate.
Gert's visual judgement remains the acceptance criterion. The low-resolution database-photo baseline is not a
measurement of what original high-resolution iPhone stills can achieve.

## Processing evidence and repaired handoff

Installed only the approved additions from official wheels using `uv lock` and
`uv sync --locked --extra scan --no-build`: PyCOLMAP 4.2.1 and pillow-heif 1.8.1. Install completed in seconds.
uv refreshed the local editable Python package; no native dependency was compiled or Homebrew package installed.
The installed OpenMVS 2.4 tools were unchanged. API/help inspection confirmed the installed callable/CLI contracts.

The actual initial command was:

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 uv run --locked --no-sync campervan scan reconstruct \
  --request .local/experiments/photo-baseline/request.json --output .local/scans/photo-baseline-20261111
```

It completed camera solving, dense depth/fusion and meshing, then exited 1: ReconstructMesh's default interface
archive mode saved `surface.ply` without `surface.mvs`. Its v2.4 source explicitly conditions scene serialization on
archive format. This was an introduced handoff defect, fixed by specifying `--archive-type 2` for native stages.
The already completed camera/depth/surface outputs were retained; no matching or dense reconstruction was repeated.

For this same baseline, RefineMesh consumed `dense.mvs` plus explicit `-m surface.ply`, with archive type 2. It
completed refinement in 237.761 seconds. The common photographic publication helper then created the viewing copy,
ran TextureMesh and published the manifest through `ScanLibraryStore.associate`; continuation exited 0. Texturing
took approximately 238 seconds. No processing-quality parameters were searched or tools swapped.
One initial shell invocation used a relative executable from the native working directory and exited 127; its
absolute-path correction started no duplicate processing. This is recorded rather than counted as a successful run.

This is one completed baseline with a repaired handoff, not a claim that a fresh uninterrupted full CLI invocation
was rerun after the fix. Future requests use the corrected native archive flags. No automatic resume/retry system
was added; the one-off local continuation reused the same publisher and explicit saved inputs.

Retained local evidence:

- `.local/experiments/photo-baseline/request.json`: exact selected files, hashes, source node IDs, calibration and reason.
- `contact.jpg`: inspected input coverage; `processing.log`: original CLI stdout/stderr.
- `refinement-recovery.log` and `publication.log`: corrected remaining stages and successful publication.
- `geometry-inspection.png`: actual refined mesh, untextured, raycast from registered source frame 916 beside its photo.
- Run `processing.log`, `request.json`, `image_sources.json`, `tag-support.json`, `poses.json`, `frames.json`, COLMAP
  models/tracks, native depth maps and dense/refined assets. Frame depth provenance is photographic, not fabricated LiDAR.

## Single accumulated source review

Flow review was applied once locally with the approved project overrides: **no tests/build/lint/browser automation,
services, per-task review agents or repeated review passes**. The three bounded implementation agents did not run
tests or delegate reviewers. The optional simplification scope was limited to shared native texturing and a common
photographic publisher; no architecture rewrite was admitted.

| Review responsibility | Finding/disposition |
| --- | --- |
| Direct security/data contracts | Existing upload streaming/hash/group checks and manifest asset allowlisting remain; photo decode failures clean temporary uploads; source bytes and measurements are not rewritten. No new service or implicit installer. |
| Quality/native correctness | Native archive handoff defect fixed as above. Existing process-group cancellation covers worker and native children. Real native percentages are surfaced only when printed by the tool. |
| Plan completeness | T1–T6 implementation complete; C1–C8 source/runtime evidence recorded below. No later-stage implementation included. |
| Intent | Distinct quick/depth and detailed/photo paths; explicit mixed-source selection; no preview prerequisite or copied tag positions. |
| Test quality | Not applicable: repository explicitly forbids creating/running tests. No new tests or replacement infrastructure. |
| Documentation | README and photogrammetry guide now describe actual photo geometry, HEIC, selection, scale, shared jobs and unfinished later stages. |

The final source review also removed stale importer guidance that described tag settings as manually saved positions;
it now states positions are detected from the selected reconstruction. Existing axis **definitions**, not solved
matrices, propagate from result actions and are solved against the new tags when supported.

## Coverage and verification limits

| Criteria | Evidence/status |
| --- | --- |
| C1/C2 | Named shared actions and explicit request discrimination inspected; depth preview delegates to existing fusion. No redundant preview run. Gert's input/UI acceptance pending. |
| C3 | All photographic stages executed on the baseline; native handoff fix and recovery are explicit above. |
| C4 | Snapshot/source map and same-group publication recorded; source preparation writes only new working copies; measurement owners untouched. No per-batch layout gates. |
| C5 | Actual supported/unsupported tag evidence and scale recorded. Unscaled code path omits metric overlays and reports arbitrary units. No synthetic unscaled scenario run. |
| C6 | Shared runner/poller/error/result-handoff and process-group cancellation traced; one actual native failure was reported with its diagnostic. Pointer cancellation/retry and modal focus require Gert's inspection. |
| C7 | Actual full/viewing/texture assets exist; existing camera/lighting owner retained. Live camera preservation remains Gert's visual check. |
| C8 | One explicit existing-photo baseline completed and untextured geometry inspected. No further parameter experiment. |

`git diff --check` passed for the accumulated implementation. No tests, frontend build, lint, browser interaction,
service launch, unrelated repair or extra baseline was performed. No actual HEIC capture was supplied for this run;
support uses the approved decoder, with end-user import acceptance pending. No unresolved implementation blocker or
decision bead remains. Do not convert these visual-acceptance limits into an automated test/review campaign.

Production/dependency source identity (sorted relative path + NUL + bytes + NUL, SHA-256):
`4c11e1d4d6923d900efcf3d705cf96a69206c98d087365f38f7e7e40b9df81db` across 19 changed production/dependency files.
