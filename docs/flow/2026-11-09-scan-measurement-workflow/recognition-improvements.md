# Improving scene recognition: multi-view geometry, symmetry and compute

Researched 9 November 2026 following the [completed tiny-model trial](spike/results.md). No new model, runtime,
service, dependency or hardware was installed/used during this research. The specification remains unapproved.

## Conclusion

The next improvement should combine several views into 3D instances and infer labels jointly using geometric and
scene context, including the user's approximate bilateral body-symmetry constraint. A stronger image recogniser is
also worth evaluating. There is not yet evidence that a bigger machine is necessary: the requested trial ran on the
M1/16 GB machine without an inference memory failure, but made substantial semantic errors.

Using the same model on a faster GPU is not expected to resolve those errors by itself. More capable hardware can
enable larger models, higher resolutions, more simultaneous observations and CUDA-centric research packages.
Actual quality must be compared on the same captured objects/views, not inferred from hardware or model size.

## 1. Replace independent frame decisions with persistent 3D instances

Select overlapping source views with useful coverage/viewing angles, project masks through retained calibration,
depth and poses with occlusion checks, then merge only observations that support the same physical region. Keep
disagreement/alternative labels and visibility support. Five isolated frames with raw maximum-score voxel labels
were enough to establish runtime feasibility, not a complete semantic fusion method.

[MaskClustering](https://openaccess.thecvf.com/content/CVPR2024/html/Yan_MaskClustering_View_Consensus_based_Mask_Graph_Clustering_for_Open-Vocabulary_3D_CVPR_2024_paper.html)
constructs a global mask graph and uses agreement across multiple views to merge masks into 3D instances.
[Open3DIS](https://open3dis.github.io/) combines 2D mask guidance with 3D regions and hierarchical merging.
These are established algorithmic references; neither entire research environment is automatically selected.

The [MaskClustering runtime](https://raw.githubusercontent.com/PKU-EPIC/MaskClustering/main/README.md) includes
PyTorch3D and a CUDA-oriented example setup; its full pipeline adds CropFormer/Detectron2 and OpenCLIP. The
[Open3DIS setup](https://raw.githubusercontent.com/VinAIResearch/Open3DIS/main/docs/INSTALL.md) assumes older
Python/PyTorch/CUDA versions and compiled sparse/point-cloud components. Reusing their methods does not imply those
packages fit the existing Python 3.13/Mac environment unchanged. Licensing and actual integration of reused code
must be evaluated before adopting code, rather than merely following a published method.

## 2. Use approximate symmetry and structural relationships to resolve labels jointly

Proposed application mechanism:

- Estimate floor/main directions and a candidate longitudinal reflection plane from supported geometry. Use robust
  partial matching to reduce the influence of openings, clutter, incomplete visibility and real asymmetry.
- Match opposite body regions using reflected position, surface extent/normals and shape, not only similar pixels.
- Preserve multiple object-label hypotheses for each matched 3D instance.
- Score visual evidence together with geometric plausibility, multi-view support, mirrored-body correspondence and
  spatial roles. A paired set of low body-attached bulges should not independently become seat/wheel-well labels.
- Treat symmetry as a soft relationship whose support is visible; apply it to corresponding body structure, not
  blanket mirroring of all seats, door openings and cab details.
- Do not deform measured geometry or fabricate a missing surface merely to make labels/shape symmetric.

Symmetry can favour matching classifications, but geometry/location/context must distinguish between two competing
shared labels. Missing counterpart observations remain unknown rather than evidence that the counterpart is absent.
Labels corrected by symmetry should retain their supporting evidence and the original competing hypotheses.

[Partial and approximate symmetry detection](https://graphics.stanford.edu/~niloy/research/approx_symmetry/approx_symm_sig_06.html)
is established in geometric processing. This paper does not itself provide vehicle semantic recognition.
[OV3D-CG](https://vipl-vsu.github.io/OV3D-CG/) specifically addresses ambiguity from object-only visual features by
adding scene/context-aware semantic reasoning. These support the design direction, not demonstrated success on the van.

One implementation candidate is an object-region scene graph with discrete semantic states. Existing
[GTSAM DiscreteFactorGraph](https://borglab.github.io/gtsam/discretefactorgraph/) supports joint discrete inference;
`DiscreteFactorGraph`, `DecisionTreeFactor` and `DiscreteKeys` are present in the installed 4.3.0 bindings (read-only
stub inspection). This could reuse the existing factor engine for label/context reasoning, separately from physical
distance fitting and camera-pose correction. Application-specific matching/factor design is still required, and
inference cost depends on graph connectivity/state counts. It is not a built-in van-recognition model.

An alternate established numerical route is [SciPy MILP](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)
for a finite region/label-assignment objective. No solver backend is selected/changed by this note. Avoid inventing
another optimisation framework when the existing stack has an appropriate solver.

## 3. Separate physical object identity from material and confidence

The follow-up trial exposed an avoidable modelling issue: a wheel arch may also be foil-covered insulation. These
are compatible attributes, not exclusive labels competing for the highest detector score. Keep object identity,
material and spatial role distinct, and preserve unknown/ambiguous states. Raw DINO scores are not calibrated class
probabilities, and repeated near-identical frames are correlated evidence, not independent votes.

## 4. Evaluate stronger recognition without assuming another machine

[SAM3](https://ai.meta.com/research/sam3) adds concept-prompted detection/segmentation; the
[Transformers implementation](https://huggingface.co/docs/transformers/model_doc/sam3) is one candidate on the existing
Python runtime. The exact MPS operator compatibility, memory and speed on M1/16 GB remain unmeasured. Official weights
have publisher access/licensing conditions. No weights were downloaded during this research.

The community [sam3.cpp implementation](https://raw.githubusercontent.com/PABannier/sam3.cpp/main/README.md) supports
SAM3 text detection and CPU/Apple Metal, with full and quantised model variants. Its own measurements are on an
M4 Pro/24 GB machine, not this M1. Model file sizes are not peak RAM. Quantisation/runtime parity and recognition
quality on this capture need checking. The [runtime code is MIT](https://raw.githubusercontent.com/PABannier/sam3.cpp/main/LICENSE);
model-weight licensing/access is separate. This is a plausible local candidate, not an installed or validated tool.

Apple also uses SAM3 as an example in its [WWDC26 ML operations presentation](https://developer.apple.com/videos/play/wwdc2026/330/).
That illustrates Apple-GPU execution work, not a ready-made supported Python M1 integration or performance guarantee.

A contextual vision-language recogniser can inspect a region with its surrounding scene instead of isolated noun
matching, as in OV3D-CG. This may help ambiguous wheel wells/rear trim but adds another model/runtime decision and
is not assumed to be metrically reliable. The measured geometry must remain authoritative.

## Recommended next bounded comparison

Keep the existing trial artifacts as a baseline. Compare a stronger concept/context recogniser on the same failure
cases and aggregate overlapping views into observed 3D instances. Then compare labels with and without geometric/
symmetry factors, retaining errors/unknowns. Start locally; if model compatibility, RAM or runtime is inadequate,
evaluate the same capture batch on an existing Linux/NVIDIA machine before recommending a purchase or service.

Subsequent user direction resolves the priority: reject the tiny keyword detector as the proposed primary semantic
recogniser. Start with context-aware vision-language scene interpretation, and establish correct feature identities
before implementing further association/fusion. Do not spend further iterations tuning the failed detector merely
because it is easy to run locally. The runtime choice follows the required recognition quality; no model is selected
as adequate without evidence on the actual capture. Retain segmentation as a boundary tool and RGB-D as metric data.

No claim is made that stronger hardware or forced symmetry will guarantee correct semantics. The integration goal
is explainable, source-supported scene interpretation whose uncertain detections do not block best-effort use.
