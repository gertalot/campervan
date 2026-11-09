# Automatic region proposal and recognition trial — 9 November 2026

Status: automatic region generation and 4B comparisons complete; open-ended 9B comparison interrupted after three
responses; two-view target-directed 9B detection trial complete following Gert's clarification.

## Replacing the manual region specification

The trial now generates regions without supplied target coordinates or semantic category prompts:

1. SAM2.1 tiny automatic mask generation over the five representative source frames (76, 415, 470, 770, 1020),
   using a 32×32 point grid and library-default IoU/stability filtering.
2. Native source depth/confidence/optical poses associate masks with observed 3D points.
3. Open3D robust plane fitting and connected-component clustering add broad geometric patches.
4. Conservative voxel-overlap matching produces tentative associations. This is not a reimplementation/validation
   of full MaskClustering or a proof that every region corresponds to one physical object.
5. A documented, category-independent 3D coverage/diversity rule selects 24 regions for the recognition budget.
   All alternatives remain visible; no hand-selected successful regions replace that list.
6. The existing VLM runner consumes generated region coordinates and source images. No separate recogniser or save
   path is created for automatic regions.

The five views are the same representative views used for the earlier comparison. Automatic source-view selection
and whole-capture coverage are not established by this bounded trial. Omitting `--frames` samples five frames across
another capture; the geometric/region algorithms contain no project tag assignments or manually specified regions.

## Counts and artifacts

- SAM2 generated 63 raw masks; 37 met the recorded 0.5%–85% image-area filter.
- Seven connected geometric proposals brought the raw candidate count to 44.
- Conservative matching produced 40 tentative regions, of which 24 were selected for recognition.
- Raw masks, candidate views/boxes, selection metadata and per-region observed-depth points are retained at
  `.local/scene-understanding-trial/automatic-regions/`.
- `proposals.html` and `automatic-proposals.jpg` show all regions, marking the chosen recognition batch.
- The automatic masks include both visible foil-covered protrusions, rear-door inserts, plywood roof and seat
  parts. The broad floor proposal comes from geometry. Small controls/trim also appear; these are unlabelled
  proposals, not assumed semantic objects.

## 4B recognition outcomes and failures

Qwen3.5-4B/MLX identified appropriate broad floor-pan, roof-panel, door-panel, seat-back/headrest and windshield
regions in the automated batch. It also confidently labelled one foil-covered wheel-well region a battery pack
and another only as insulation. Correctly finding a region therefore does not guarantee correct identification.

Bounding boxes around geometric patches can include unrelated foreground objects. A follow-up for all seven
selected geometry-only proposals projected the actual source-supported surface mask into the views rather than
highlighting everything inside the box. This improved the floor/rear-floor interpretation in one example, but
ambiguous/mixed geometric patches and semantic mistakes remain. Do not call a plane a complete object instance.

The model's textual "None" uncertainty is demonstrably unreliable: it accompanied the incorrect battery-pack
identity. These outputs are provisional observations, not measurements or calibrated class probabilities.

## Automatic geometric counterpart comparison

The largest automatically recognised floor proposal provides a coordinate seed. A clipped reflection-distance
search over the original cloud estimates a longitudinal body-symmetry plane. Mutual-best matching of reflected
region point sets produces four counterpart hypotheses without expected category names.

The best geometric pair is the two opposite foil-covered regions; its median reflected-surface residual is about
21 mm. This is a heuristic geometry-fit diagnostic, not surveyed positional accuracy or a physical measurement.
Other matches include headrest/seat-region and body-panel candidates; not every pair is semantically valid.

Giving the 4B VLM these counterpart hypotheses did not reliably fix the labels. It called the wheel-well pair a
rear cargo floor panel and conflated a broad body-region pairing with a seat. This negative result is retained at
`.local/scene-understanding-trial/automatic-symmetry-recognition/`; it is not hidden or counted as successful recognition.

## Larger-model comparison

The initial bounded comparison changed only the model to Qwen3.5-9B/MLX on the same four automatically generated
counterpart queries. It does not add category hints, manual coordinates or corrective examples. The 4B model cache
snapshot downloaded during these trials was removed through the official Hugging Face cache API to make room;
all prompts, responses, output artifacts and source captures remain retained. Re-running 4B would redownload weights.

The initial download was stopped for disk pressure and removed, then restarted after Gert freed space. The resumed
open-ended run produced three responses before being stopped for a prompt change. It called the foil-covered
wheel-well pair a body panel, the broad body pairing a rear door, and the seat pair headrests (with an unsupported
front/rear distinction). These partial results are retained in `automatic-symmetry-recognition-9b-resumed/`.
This does not establish that the model cannot perform the actual target-directed task.

## Target-directed correction to the experiment

Gert clarified that we should search only for the requested interior features, rather than ask for identities of
arbitrary regions. A category-limited reclassification of the same arbitrary proposals was also stopped: it still
put proposal generation in the wrong order. Neither interrupted comparison is reported as a completed benchmark.

The revised trial gives Qwen3.5-9B full original photographs and explicitly asks for only floor, ceiling, wall, wheel
well, window and seat detections with bounding boxes. It supplies no target coordinates, no hand-picked wheel-well
region and no expected answer for a particular image. Absent/unlocatable features are omitted; no other/unknown
object categories are requested. Detailed segmentation/3D association should consume those target detections, subject
to visually checking their localisation, rather than generating every arbitrary region first.

The first bounded run uses rear/front frames 76 and 1020, configured separately from the prompt/model runner.
Outputs: `.local/scene-understanding-trial/target-features-9b/`. The exact vocabulary is data in
`feature-detection-prompt.json`. Model-proposed boxes and rejected/invalid outputs are recorded by the same runner;
the existing report shows annotated source photos. This is not yet mask segmentation or semantic mesh cleanup.

### Observed target-directed results

Both responses completed with valid JSON and no out-of-vocabulary/invalid-box detections. Rear frame 76 produced
six detections in 56.03 seconds: ceiling, two windows, broad wall, a narrow floor strip and the foil-covered wheel
well. Direct inspection of the annotated source supports those identities, although the broad wall box spans
openings and the ceiling/wheel-well boxes are approximate rather than precise surface boundaries.

Front frame 1020 produced five detections in 57.66 seconds: ceiling, wall, window, seat and floor. The seat/window
identities are useful. The purported floor is actually the vertical black lower door panel, so this is a retained
false positive. The ceiling box also includes adjacent body/cab trim. Syntactic validity is not semantic accuracy.
The trial is not a whole-capture accuracy benchmark and cannot justify automatic cleanup or metric constraints.

Peak MLX allocation was approximately 6.99 GB. These are measured model allocations, not total process/system RAM.
The completed report and annotated source JPEGs are in `target-features-9b/`; original RGB-D, poses, mesh and physical
measurements are unchanged. No tests or services were run. The model now demonstrably recognises the wheel well
when given the intended task; the earlier open-ended result was insufficient evidence to reject it for this task.

Next work is target-directed mask refinement and depth/multi-view geometric checks (including rejecting a vertical
door patch as floor), not returning to exhaustive arbitrary-region classification. This has not been implemented
or applied to the production scan pipeline.

## Boundaries

This adds automatic proposal/identification experiments, not app integration or semantic mesh cleanup. All
captures, physical measurements, original poses/meshes and current viewer state remain unchanged. The scripts reuse
one RGB-D projection helper, one region-context prompt, the existing VLM runner and its report renderer. Dependencies
remain temporary uv-run additions. No tests, services, browser interactions or new model servers were created/run.

See [commands and data contracts](README.md). Final outcomes of the larger-model comparison will be recorded here.
