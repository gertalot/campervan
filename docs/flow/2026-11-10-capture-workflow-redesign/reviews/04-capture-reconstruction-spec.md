# Capture/reconstruction revision: single-pass review

Date: 10 November 2026. Draft: [spec section 4](../spec.md#4-stage-1--review-capture).
Scope: capture-stage additions against commit `d7649a6` and directly conflicting cross-references. Existing later
stages were excluded. Six read-only roles ran once: gaps, ambiguity, scope, design integrity, reuse/tool evaluation
and documentation/refactor quality. No tests, processing, installation or application edits were performed.

Seven reported findings reduce to four distinct decisions. None are editorial obvious fixes. No out-of-scope findings
were admitted. The decisions below were collected in ordinary chat and applied in one batched spec update on
11 November 2026. Gert then approved the final written capture-stage specification on 11 November 2026.
Do not repeat the review pass. Implementation planning remains a separate user-invoked phase.

| Decision | Sources | Gert's decision |
| --- | --- | --- |
| Native HEIC import versus JPEG/PNG-only | G1, AM2, CL1, T1 | Include HEIC using the verified precompiled pillow-heif decoder; retain originals and full-resolution working copies. |
| Default input selection for detailed reconstruction | AM1 | No arbitrary photo-only restriction/default. Upload supported sources into the same group; visibly select original photos, database photographs or a mixture. Nothing silently included/excluded. |
| Physical layout ownership of selected inputs | G2 | Proposed extra bookkeeping withdrawn after clarification. Detect/recompute and save tags per source reconstruction. Do not copy prior positions or silently add earlier captures. Existing measurement association stays separate; no new layout-assignment/gating mechanism. |
| Operational support policy for triangulated tag scale | G3 | Use COLMAP standard geometric support checks; keep unsupported detections as Detected but not located, exclude them from scale, and allow scene reconstruction/inspection. No new tuning controls or approval steps. |

Scope and design-integrity roles found no additional material issue. Reuse of importer, job owner, progress/poller,
result library, renderer and alignment owner is grounded in the current code. The selected PyCOLMAP/OpenMVS pipeline
has a documented binary route; its runtime integration remains future implementation evidence.

HEIC verification: [official package](https://pypi.org/project/pillow-heif/),
[installation](https://pillow-heif.readthedocs.io/en/latest/installation.html),
[image/metadata support](https://pillow-heif.readthedocs.io/en/latest/pillow-plugin.html).
Official Python 3.13/macOS ARM64 wheel exists (1.8.1, approximately 4.3 MB). The package has BSD-3-Clause licensing;
native bundled components retain their own licences. Gert selected this option for the spec; installation remains
implementation work, not an action authorised during planning.
