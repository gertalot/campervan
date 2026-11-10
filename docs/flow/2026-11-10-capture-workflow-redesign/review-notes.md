# Single-pass specification review and decisions

Date: 10 November 2026. Scope: [draft specification](spec.md), read-only review before user approval.

The six requested roles ran once: gaps/builder completeness, ambiguity, scope coherence, design integrity,
reuse/tool evaluation, and documentation/refactor quality. Seven returned findings reduced to four distinct issues.
No out-of-scope findings were admitted. No further spec-review pass is required.

| Distinct issue | Disposition |
| --- | --- |
| Escape could cancel an entry and close the panel | Clarified the previously agreed behaviour: the active editor consumes Escape; otherwise the shared panel closes |
| Making every original tag mandatory prevents redundancy advice | Gert approved individual tag-removal evaluation against measuring effort, remaining precision and retained spatial coverage; show coverage trade-offs rather than awarding an unconditional better score |
| Empty-graph layout scoring could discard useful saved measurement information in the checklist | Gert approved empty-graph comparison for layout scores and the same planner seeded with applicable saved distances for actual remaining work |
| Capture-review thresholds lacked a defensible basis | Initial proposal withdrawn after technical checking; Gert explicitly removed automatic coverage analysis and advice, choosing visual inspection plus adding capture databases |

The final capture decision also clarified the economical workflow: a basic scan may be sufficient for initial tag
layout work; detailed captures can be added once the tags are in satisfactory positions. No completeness gate.

## Focused technical check, not another spec-review round

After the unsupported threshold proposal was challenged, Gert required advance notice and independent verification
for new technology-dependent ideas. One read-only subagent checked the alternative idea of using original posed
depth observations as support/disagreement evidence. It inspected `scans.py`, `scan_reconstruction.py`,
`scan_visibility.py`, official RTAB-Map/Open3D source and published RGB-D reconstruction work.

Findings:

- Original RGB/depth, optional confidence, calibration and poses are retained, so source-evidence analysis is feasible.
- The transient TSDF volume is not persisted with its weights. Fusion weights accumulate accepted observations;
  neither they nor a fixed frame count establish independent measurements or calibrated accuracy.
- RTAB-Map's motion thresholds control map updates; they are not capture-quality thresholds.
- Depth disagreement can arise from depth errors, wrong poses, movement or mismatches; another capture is not a
  universally justified remedy. Unseen surfaces cannot be evaluated from absent evidence.
- An evidence map is technically plausible, but an automatic recapture classifier was not validated by this check.
  Gert chose to omit both rather than expand the implementation into that research problem.

Primary references:

- [RTAB-Map 0.24.2 parameters](https://raw.githubusercontent.com/introlab/rtabmap/0.24.2/corelib/include/rtabmap/core/Parameters.h).
- [Open3D TSDF integration source](https://raw.githubusercontent.com/isl-org/Open3D/main/cpp/open3d/t/geometry/kernel/VoxelBlockGridImpl.h).
- [Accurate 3D reconstruction with RGB-D cameras](https://cg.cs.tsinghua.edu.cn/papers/TOG-2018-reconstruction.pdf).

No application changes, tests, builds, services, processing jobs, downloads or recognition runs were performed.
The specification still requires Gert's final written-spec approval before implementation planning.
