# Scene-recognition feasibility spike

Explicitly requested trial, separate from the future workflow implementation. Uses existing exported RGB-D frames
and optical camera poses, Grounding DINO tiny and SAM 2.1 tiny. It does not modify captures, meshes or measurements.

Run from the repository root, using a fresh output directory:

```sh
uv run --locked --extra scan \
  --with torch==2.15.0 --with torchvision --with transformers==5.22.2 --with safetensors --with matplotlib \
  python docs/flow/2026-11-09-scan-measurement-workflow/spike/recognise.py \
  --run .local/scans/capture-00fe810c-6bba-4c5f-9f5a-da0d63c5a64f \
  --output .local/scene-understanding-trial/first-pass \
  --frames 76,415,470,770,1020 --device mps
```

`--with` adds temporary uv-run dependencies without editing the project's dependency files. Initial use downloads
public model weights to the normal Hugging Face cache. No images are uploaded. For another capture, provide its
run directory and frame IDs from `frames.json`. CPU can be selected explicitly with `--device cpu`.
Omit `--frames` to sample five frames across any new capture. Recognition concepts/colours are separate data in
`concepts.json`; provide `--concepts FILE` to try another vocabulary. `--finish` regenerates visualisation/aggregation
from an existing output's saved inference arrays without loading model weights or repeating inference.

Outputs include side-by-side recognition images, per-frame masks/detections, original-depth-projected labelled points,
a coarse semantic PLY, package/model-commit provenance and timings. Reproduce exact model weights with the recorded
`--detector-revision` and `--segmenter-revision` commit IDs. Predictions are not verified labels or calibrated
probabilities. Scores do not establish physical accuracy; windows can contain depths of objects beyond the glass.
This trial is not production cleanup, multi-view semantic validation or mesh correction.

## Context-aware vision-language trial

`vlm_recognise.py` evaluates scene interpretation separately from segmentation. It gives a local vision-language
model pairs of unlabelled original images plus the scene context in `vlm-cases.json`. It does not feed previous
detector predictions or expected feature answers to the model. Responses, source-image sheets, model revision,
prompt/settings, package versions and timing/memory metadata are saved for inspection.

```sh
HF_HUB_DISABLE_XET=1 uv run --locked --with mlx-vlm==0.7.12 \
  python docs/flow/2026-11-09-scan-measurement-workflow/spike/vlm_recognise.py \
  --run .local/scans/capture-00fe810c-6bba-4c5f-9f5a-da0d63c5a64f \
  --output .local/scene-understanding-trial/vlm-qwen35-4b \
  --revision 32f3e8ecf65426fc3306969496342d504bfa13f3
```

Use a fresh output directory. The default candidate is the public Apache-2.0 Qwen3.5-4B MLX 4-bit model (about 3 GB
of weights); `--model`/`--revision` can select another compatible model. The native Apple MLX runtime is supplied by
temporary uv dependencies. No model server is started and photos are not uploaded. For another capture, provide its
run and a separate `--cases FILE` containing the applicable frame IDs/context. This measures feature-identification
capability; it does not claim 3D localisation, correct masks or production scene understanding from prose alone.

For the region-with-context comparison, add:

```sh
--cases docs/flow/2026-11-09-scan-measurement-workflow/spike/vlm-region-cases.json --max-tokens 500
```

Use a different output directory. The region file supplies unlabelled bounding boxes from the earlier mask proposals
and one broad roof patch; no expected category is included in a model prompt. This isolates identity recognition
given a region. Automatic proposal selection/coverage remains later work. The script also produces a static HTML
report and a recognition summary image for visual inspection.

## Automatic region-proposal trial

`automatic_regions.py` replaces supplied region coordinates with class-agnostic masks and geometric patches.
All output paths below refer to the completed trial; choose fresh paths for another run.

```sh
PYTORCH_ENABLE_MPS_FALLBACK=1 uv run --locked --extra scan \
  --with torch==2.15.0 --with torchvision --with transformers==5.22.2 \
  python docs/flow/2026-11-09-scan-measurement-workflow/spike/automatic_regions.py \
  --stage masks --run .local/scans/capture-00fe810c-6bba-4c5f-9f5a-da0d63c5a64f \
  --output .local/scene-understanding-trial/automatic-regions --frames 76,415,470,770,1020

uv run --locked --extra scan \
  python docs/flow/2026-11-09-scan-measurement-workflow/spike/automatic_regions.py \
  --stage assemble --run .local/scans/capture-00fe810c-6bba-4c5f-9f5a-da0d63c5a64f \
  --output .local/scene-understanding-trial/automatic-regions --max-regions 24
```

The first stage uses SAM2 automatic grid-point mask generation without text categories or target coordinates.
The second projects masks through depth/poses, adds connected planar patches from Open3D, conservatively associates
overlapping 3D proposals, and chooses a recorded coverage/diversity batch. `--max-regions 0` includes every proposal;
the bounded default retains all alternatives in `proposals.json`, `proposals.html` and `automatic-proposals.jpg`.
No expected classes guide selection. `region-points.npz` retains source-frame 3D associations. This conservative
association is not the full published MaskClustering implementation or verified object-instance segmentation.

Pass generated `automatic-cases.json` to the same `vlm_recognise.py --cases FILE` runner. Recognition does not require
another save, model-wrapper or report implementation.

For geometry-only regions, `automatic_regions.py --stage highlight` writes `surface-cases.json` and source-supported
pixel masks so the VLM sees which pixels belong to a proposed surface; a box alone can contain unrelated foreground.
The stage uses retained depth and region points, not another segmentation run.

For a symmetry comparison, run `--stage symmetry --recognition RECOGNITION_REPORT_JSON`. It uses the largest
automatically recognised floor candidate, estimates a robust approximate longitudinal reflection plane from the
original cloud and generates mutual-best region counterpart candidates. `symmetry.json` records the hypothesis,
geometric residuals and candidate pairs. `symmetry-cases.json` contains only those generated pairs and generic scene
context; it does not contain expected identities. Run the same VLM runner on that file to assess the pairings.

The larger-model comparison uses:

```sh
--model mlx-community/Qwen3.5-9B-MLX-4bit --revision 938d8919941c6e7efd3c7150eff7fe9d12afa631
```

The original download was stopped for disk pressure and removed. After Gert freed space and authorised resuming,
the exact comparison was restarted with the following command (the output directory must be fresh):

```sh
HF_HUB_DISABLE_XET=1 uv run --locked --with mlx-vlm==0.7.12 \
  python docs/flow/2026-11-09-scan-measurement-workflow/spike/vlm_recognise.py \
  --run .local/scans/capture-00fe810c-6bba-4c5f-9f5a-da0d63c5a64f \
  --output .local/scene-understanding-trial/automatic-symmetry-recognition-9b-resumed \
  --cases .local/scene-understanding-trial/automatic-regions/symmetry-cases.json \
  --model mlx-community/Qwen3.5-9B-MLX-4bit \
  --revision 938d8919941c6e7efd3c7150eff7fe9d12afa631 --max-tokens 500
```

The model files total approximately 6 GB, excluding runtime dependencies. No source photographs are uploaded.

The data remains in the source scan frame. No inferred symmetry, label, axis or cleanup is applied to source geometry.
Glass can produce depths beyond the glass, planar patches can cross object boundaries, and raw model statements of
"None" uncertainty are not calibrated confidence. This is an inspectable offline experiment, not the staged app UX.

## Target-directed interior feature detection

Following Gert's clarification, the current trial locates only the requested features in full original photographs
before proposing detailed regions. It does not classify every arbitrary mask. The vocabulary and detection contract
are data in `feature-detection-prompt.json`; frame selection is data in `feature-detection-cases.json`.

```sh
HF_HUB_DISABLE_XET=1 uv run --locked --with mlx-vlm==0.7.12 \
  python docs/flow/2026-11-09-scan-measurement-workflow/spike/vlm_recognise.py \
  --run .local/scans/capture-00fe810c-6bba-4c5f-9f5a-da0d63c5a64f \
  --output .local/scene-understanding-trial/target-features-9b \
  --cases docs/flow/2026-11-09-scan-measurement-workflow/spike/feature-detection-cases.json \
  --model mlx-community/Qwen3.5-9B-MLX-4bit \
  --revision 938d8919941c6e7efd3c7150eff7fe9d12afa631 --max-tokens 1200
```

Only the six configured categories are accepted as detections. Boxes must be ordered, normalized 0–1000 image
coordinates; invalid/category-extraneous predictions remain in the raw response and rejection log, not the region
list. Absence can produce an empty detections array. Annotated JPEGs/report preserve proposed boxes for inspection;
these are model proposals, not validated masks or measured 3D surfaces. No new model download or service is needed
once the selected 9B weights are cached. Choose a fresh output path for another run.
