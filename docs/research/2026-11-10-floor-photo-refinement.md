# Bounded floor photo-refinement experiment

Date: 10 November 2026. User-authorised experiment, separate from implementation of the six-stage workflow.

## Result

OpenMVS image-based refinement produced visible ridge-shaped geometry in a 650 × 650 mm floor patch that was much
flatter in the depth-fused input. This establishes a working image-driven refinement path with these saved photos;
it does not establish true ridge depths or metric accuracy. No whole-van reconstruction was attempted.

The input was cropped from the saved **full mesh before display simplification**. The ridges were therefore already
weak before the display triangle reduction; that reduction alone cannot explain their absence in this patch.

The source reconstruction and physical measurements were unchanged. Two copied experimental results were published
in the source capture's existing group, without creating another group or switching the current view:

- **Floor experiment — before photo refinement**
- **Floor experiment — after photo refinement**

In Scan, choose **Refresh scans**, either result, then **Layer → Shaded surface**. Switching results preserves the
view, so both can be inspected with the same camera and lighting. These are floor-only patches in the source frame.

## Inputs and actual execution

| Item | Value |
| --- | --- |
| Source | `capture-fdfb86a1-db42-4087-8863-8f26568da3c5` |
| Source mesh | `working/full-mesh.ply`, before display decimation |
| Patch | 650 × 650 mm; configured using floor tag 1 and longitudinal reference tag 11 |
| Photographs | Frames 155, 158, 159, 146; native exported RGB, 720 × 960 pixels |
| Calibration/poses | Existing exported optical calibration and camera-to-world poses, unchanged |
| Input and output mesh | 20,621 vertices; 40,623 faces; topology unchanged |
| Tools | Existing precompiled OpenMVS 2.4.0 InterfaceCOLMAP and RefineMesh |
| Import runtime | 0.041 seconds |
| Refinement runtime | 1.614 seconds, including tool startup/output; 20 optimisation iterations |
| Experiment files | 4,498,501 bytes, including copied photos, logs, scripts and comparison figure |
| Published meshes | 2,355,831 bytes combined, plus small manifests |
| Limits | Four threads, one image scale, five-minute timeout per processing command; no retries |

Only four views met the chosen whole-patch framing/distance/view-selection conditions; the initial upper budget was
ten. The marked source-photo contact sheet was inspected: the selected floor area is unobstructed. The viewpoint
spacing used for this small sample is an experiment-selection choice, not an adequacy or independence criterion.

RefineMesh can derive image-neighbour support from a supplied mesh when the sparse point cloud is empty. This was
verified in the [pinned implementation](https://raw.githubusercontent.com/cdcseacave/openMVS/v2.4.0/libs/MVS/SceneRefine.cpp)
before running. The log confirms mesh visibility sampling and four calibrated images; no SfM or dense-stereo stage
was run. This trial refines existing topology rather than reconstructing missing surfaces from scratch.

Settings: `--resolution-level 0 --scales 1 --max-views 4 --decimate 1 --close-holes 0 --ensure-edge-size 0
--max-face-area 16 --gradient-step 20.05 --regularity-weight 0.2 --reduce-memory 1 --max-threads 4 --archive-type 2`.
Projected-face subdivision was allowed, but the log reports no topology change for this patch.

## Comparison

For corresponding vertices, median movement was **0.839 mm**, 95th percentile **2.748 mm**, maximum **10.014 mm**.
RMS movement along the approximate floor normal was **1.110 mm**. These are algorithm-induced changes, not error or
accuracy measurements; the maximum is not evidence that a 10 mm real ridge was correctly recovered.

The static comparison uses the same grey material/shading, camera, metric scale and no vertical exaggeration.
A plane fitted to the input patch is subtracted from both copies for that figure only. Published meshes retain
their actual source coordinates.

Remaining limitations: only four photos; reflective/repetitive metal; existing camera-pose/calibration errors;
no independently measured cross-section; bounded iterations and regularisation. Photometric optimisation can
convert changing highlights/shadows into false relief. Recognisable grooves are encouraging evidence, not validation
for fabrication or proof that the complete van will behave similarly.

## Local artifacts and reproducibility

Experiment directory: `.local/experiments/floor-photo-refinement-20261110/`.

- `config.json`: capture/reference/patch choices kept separate from the helper code.
- `prepare.py`: selects/copies posed views, exports the cropped full-resolution mesh and COLMAP text input.
- `run.py`: executes the installed binaries once with explicit timeout and saves commands/timing to `execution.json`.
- `compare.py`: writes `comparison.json` and `comparison.png` from input/output geometry.
- `publish.py`: copies the meshes into normal result directories and associates them with the current source group.
- `selected-views.jpg`, `1-InterfaceCOLMAP.log`, `2-RefineMesh.log`, `prepared.json` and `published.json`: evidence.

Helpers run from the repository root with `uv run --locked --no-sync python <helper-path>`. Outputs already exist;
do not rerun merely to reproduce this report. A new experiment needs a separate output directory/config; publishing
refuses to overwrite the existing experiment runs.

No dependencies were installed, sources compiled, services started, tests run or application pipeline code changed.
The experiment does not automatically enable photo refinement in production or start work on later UX stages.

## Follow-up after Gert's visual feedback

Gert found the first refined surface too soft to describe the actual floor. Two bounded alternatives were checked
against pinned OpenMVS source and run on the same four photographs, with original camera calibration/poses unchanged.
No additional sources were compiled or dependencies installed.

| Variant | Actual processing | Outcome |
| --- | --- | --- |
| Image-derived dense depth, meshing, then refinement | 18.053 s densification + 1.957 s meshing + 3.598 s refinement | More relief, but large noisy distortions; not a demonstrated improvement |
| Finer two-scale refinement of the original depth mesh | 4.106 s | Modestly stronger/sharper grooves, still soft; metric accuracy unverified |

Dense reconstruction used the fresh camera scene and `--mesh-file floor-input.ply` to derive image visibility and
initial depth-search ranges. Native implementation then releases that mesh before estimating image depths; it does
not force the output onto the original surface. `--tower-mode 0 --estimate-roi 0` disabled synthetic tower assistance
and automatic ROI estimation. Densification used full image resolution, three neighbour views, four threads and
default matching/fusion settings. Meshing used no decimation or smoothing. Refinement used two scales,
`--max-face-area 4 --gradient-step 45.05`, default regularity weight 0.2, no decimation/hole filling, and four threads.
Output was cropped back to the same floor region.

The dense route fused 62,821 points; its final crop had 75,416 faces. The central 90% of its vertex heights spanned
about 31.7 mm around the common input plane, versus 8.3 mm for the original and 9.6 mm for the first refinement.
Those distributions involve different vertex sampling and are not ground-truth error measures. The visible large
distortions make the dense result unsuitable as an improvement claim, regardless of its extra triangles.

Finer refinement increased the original mesh from 40,623 faces to 45,587 before the final crop (45,548 afterward).
Its central 90% height span was about 13.1 mm. This also does not establish correct ridge depths. One copied result,
**Floor experiment — finer photo refinement**, was added to the same capture group for Gert's inspection. The failed
dense variant was retained only in the experiment directory, not added to the quick Result selector.

Evidence: `.local/experiments/floor-photo-dense-20261110/`, including `execution.json`, native logs, the copied images,
`comparison.png` (dense route) and `comparison-strong.png` (finer refinement). The dense pipeline had a shared
five-minute timeout; later refinement commands were separately capped at three/two minutes and finished in seconds.
These are finite comparisons, not a parameter sweep. No further run is automatically queued.

Remaining questions are whether these views provide sufficiently accurate correspondences and whether RGB-specific
camera-pose/calibration refinement or improved capture would help. This trial held RTAB-Map poses fixed; it did not
perform image-based bundle adjustment. Repetitive/specular metal and changing highlights are possible limitations,
not established causes. A 720 × 960 image is not, by itself, proof that useful finer geometry is impossible.
