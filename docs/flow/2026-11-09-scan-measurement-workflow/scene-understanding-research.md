# Scene-understanding clarification and initial tool research

Initial research snapshot: no recognition backend had been selected, installed or executed at this point.
Subsequent trial evidence is in [the recorded results](spike/automatic-region-results.md); the selected design is
now specified in the normative [scene-review contract](scene-review-design.md).

## User clarification

During decision D5, Gert rejected reducing the geometry stage to physical-distance fitting or manual surface/tag
association. The requirement is intelligent analysis of the captured space that attempts to recognise floor,
ceiling, walls, wheel wells, windows and seats at the front. Detection/semantic segmentation must be automatic;
optional user correction cannot stand in for that capability.

This sends D5 back to design discussion under the Flow exception allowing immediate correction of a misunderstood
design. Other collected decisions remain pending the final batched spec update. The six reviews are not rerun.

## Intended mechanism and evidence boundary

Combine observed 3D geometry with the saved calibrated RGB-D views where useful. Infer source-associated semantic
regions and spatial relationships, then expose them on the existing model/overlay. Geometry supplies positions;
semantic recognition supplies interpretations. Do not use generated object meshes as metric replacement geometry.

Outputs can inform axes, centre plane, wheel-well/body distinctions, openings/exterior cleanup, complex-front
exemptions, tag placement and physical-path assessment. Label confidence/evidence and permit correction. Detecting
an object class does not by itself prove a parallelism/symmetry constraint or a physically measurable tape path.

## Primary sources checked 9 November 2026

| Tool class/candidate | Supported by primary source | Fit/limit still to resolve |
| --- | --- | --- |
| Open3D geometry | Existing plane/patch extraction and scan geometry stack | Appropriate for structural geometry; no evidence that planar patches alone recognise seats, windows and wheel wells |
| Open3D-ML pretrained point-cloud segmentation | [Upstream](https://github.com/isl-org/Open3D-ML) documents pretrained semantic segmentation and PyTorch/TensorFlow integration | Training classes/domain, vehicle-interior generalisation, current Python 3.13/macOS support and added runtime need evaluation; existing Open3D dependency is not proof ML support is installed |
| OpenMask3D/open-vocabulary RGB-D fusion | [Project](https://openmask3d.github.io/) and [official setup](https://raw.githubusercontent.com/OpenMask3D/openmask3d/main/README.md) use point clouds plus posed RGB-D views and aggregate visual features into 3D instance masks | Data contract matches retained capture inputs; upstream setup uses Python 3.8.5 and additional model/engine dependencies. Local Mac compatibility and operational cost are unverified; not selected |
| SAM 3 concept segmentation | [Official README](https://raw.githubusercontent.com/facebookresearch/sam3/main/README.md) supports text/visual-prompt image/video segmentation; image masks would still need calibrated multi-view fusion | Documented prerequisites include CUDA-compatible GPU/CUDA 12.6+, PyTorch 2.7+, Python 3.12+. The documented runtime is not a drop-in solution for this Mac. Model access/download has additional conditions. Not selected |

These establish plausible approaches, not successful recognition of this van or a complete library evaluation.
The next design step must choose a feasible local recognition path or explicitly agree a different processing
arrangement. No model, dependency, service or capture upload has been added. No project Python or tests were run.

## Follow-up: hardware and candidate recommendation

Read-only hardware inventory identifies this machine as an Apple M1 MacBook Pro with 16 GB memory. No serial number
or device UUID was printed. This makes a documented Linux/CUDA setup a poor default integration choice.

OpenMask3D's [official install script](https://raw.githubusercontent.com/OpenMask3D/openmask3d/main/install_requirements.sh)
pins PyTorch 1.12.1 and Open3D 0.16.0, documents Ubuntu/CUDA 11.x verification, and includes MinkowskiEngine,
Detectron2, torch-scatter and native pointnet2 code. Its [MIT licence](https://raw.githubusercontent.com/OpenMask3D/openmask3d/main/LICENSE)
is permissive, but the runtime/version burden is materially different from this Python 3.13/Open3D 0.20 project.
Keep it as a conceptual/reference candidate, not the default local dependency choice. This is not a claim that it
cannot be ported or that its full dependency/model licensing has been audited.

The recommended route to evaluate first is image-guided 3D segmentation using:

1. Existing Open3D plane/patch extraction and local geometry to identify/support structural regions.
2. Grounding DINO to locate text-described features in selected original images, followed by a small SAM 2.1 model
   to obtain masks. These are automatic detector-generated prompts; the user does not need to click each object.
3. Calibrated projection of masks through original depth/poses, depth/occlusion checks and cross-view aggregation to
   label observed 3D points/regions, using existing Open3D/NumPy/OpenCV geometry responsibilities.
4. Spatial relationship/shape fitting to combine recognition with structure, including wheel-well candidates whose
   labels cannot simply be assumed to be supplied reliably by a pretrained model.

[Grounding DINO's official README](https://raw.githubusercontent.com/IDEA-Research/GroundingDINO/main/README.md)
documents CPU inference. [Transformers Grounding DINO](https://huggingface.co/docs/transformers/model_doc/grounding-dino)
and [SAM2](https://huggingface.co/docs/transformers/model_doc/sam2) provide an established model runtime. The
[SAM2 licence](https://raw.githubusercontent.com/facebookresearch/sam2/main/README.md) covers checkpoints/code under
Apache 2.0. Model revisions and complete dependency licensing still need evaluation before selecting/installing them.
Transformers documents [Apple Silicon/MPS](https://huggingface.co/docs/transformers/apple_silicon), but this does not
prove these exact models/operators work efficiently on this machine. Exact Python 3.13, memory and performance remain
unmeasured. A local model installation would add PyTorch/Transformers/model weights; none is currently authorised for
installation by this research alone.

Also evaluate [SAM3 through Transformers](https://huggingface.co/docs/transformers/model_doc/sam3), which combines
concept detection and masks in one model. Its existence means the original repository's CUDA prerequisites do not
alone settle whether another implementation can run locally. Access/licensing, exact MPS operator coverage and
16 GB memory/runtime cost must be established before choosing it over the smaller two-model route.

No tool has been selected as production-ready. No claimed recognition accuracy on seats, windows or wheel wells is
supported by a run on the user's captures. Multi-view geometry/image fusion is an established method family, but the
bounded association/glue code is still application work, not functionality automatically supplied by installing SAM.

## Requested feasibility trial

Gert subsequently explicitly authorised trying the proposed stack. The [completed spike](spike/results.md) ran
Grounding DINO tiny + SAM2.1 tiny locally on five capture views and a two-view vocabulary follow-up. It established
local runtime and useful mask proposals, but found substantial semantic errors and prompt sensitivity. Earlier
statements that no models had been run describe the pre-trial investigation only. No backend is yet accepted as
sufficient for automatic scene interpretation/cleanup. Dependencies were temporary uv-run additions; the application
dependency files and source capture/measurement/reconstruction data were not changed.

The subsequent [vision-language trial](spike/vlm-results.md) compared open-ended scene summaries with context-aware
unlabelled region queries using Qwen3.5-4B/MLX. The broad summaries retained significant issues; all four selected
region queries produced appropriate broad wheel-well, rear-door-panel, seat and plywood-ceiling identities on manual
inspection. This supports local region identification, not automatic complete-scene discovery or metric semantics.
