# Implementation notes

The replacement workflow has four stages: Review capture → Measure → Check accuracy → Update reconstruction.
The practical instructions are in [README](../../../README.md#review-and-improve-a-scan) and
[the scan guide](../../photogrammetry.md#workflow). The approved spec and implementation plan in this folder record
the design rationale. Earlier workflow instructions are superseded; no legacy-analysis adapter, automatic migration,
old/new mode or rollback-history owner is part of this implementation. Capture and physical measurement data remain.

## Source evidence

Task reports in the existing SDD workspace record scoped source inspection, changes, self-review and limits. They
are implementation evidence, not records of a working numerical job or visual acceptance.

- Task 1 established typed source workflows, immutable profile revisions, content-based freshness and explicit
  layout revision. The existing physical measurement store remains authoritative. Revised layouts copy only pairs
  whose two endpoints are explicitly unchanged; originals remain intact.
- Task 2 gave tape/checklist/saved rows one per-layout measurement session and mutation queue, retained drafts and
  explicit save feedback. Follow-up source fixes cover candidate precision, checklist/exclusion errors, outstanding
  writes and superseded job responses. Interaction/persistence still require manual acceptance.
- Task 3 implemented independent range-only fitting, separate completeness/consistency/uncertainty, projected
  free-network information and generic topology certification. Captured coordinates initialise/orient the fit and
  do not enter its physical objective or information. Local covariance does not establish global uniqueness.
- Task 4 replaced scan-assisted suggestion scoring with one physical all-pairs planner, reused for initial/additional
  checklists and supported placement comparisons. Alternatives retain baseline gains; checklist marginal gains are
  recomputed in their final order. Unregistered physical-to-source associations have Unknown clearance (`332139e`).
- Task 5 separates joint correction preview from explicit RGB-D rebuild (`e31c14b`), consumes optional reviewed
  source-pixel relationships/masks, and removes obsolete API/history owners without reading their saved files.
  Reconstruction rechecks current inputs before work; completion rechecks freshness before recording a corrected
  result. Changed-input results retain their assets and report the mismatch.
- Task 6 composes the four stages and shared reports/rows/jobs (`18642ef`), explicit layout revision and guarded import
  handoff. Corrected results are selected explicitly; a completed rebuild never automatically activates one. Its
  scoped source fixes (`8c430be`) preserve import context, target identity and action focus, display Unknown gains
  explicitly and skip unavailable rows when advancing. Runtime acceptance remains pending.

Task 3 records the one dependency resolution/install: `uv lock`, then `uv sync --locked --extra scan --no-build`,
both successful. PyRigi 1.3.0 and its mandatory dependencies were added; existing NumPy 2.5.4 and SciPy 1.18.1 became
direct scan-extra dependencies. The local editable package was rebuilt by uv; no third-party native source build
occurred. Installation was not repeated. This is installation evidence only, not import, fit or timing evidence.
The installed RTAB-Map CLI resolver/configuration and the official `/Applications/RTABMap.app` instructions are retained.

## Interpretation

| Setting/report | Meaning |
| --- | --- |
| Typical range precision, initially 3 mm | One standard deviation of a physical range; editable, with per-pair overrides. |
| Positional target, initially 5 mm | Longest semi-axis of an approximate 3D 95% tag-position ellipsoid under stated assumptions. |
| Meaningful-improvement threshold, initially 5 mm | Separate criterion for additional suggestions; not a precision guarantee. |
| Check measurements | Physical-only fit; separate completeness, consistency and uncertainty. |
| Preview corrections | Joint scan/physical correction; never evidence of independent physical precision. |
| Update mesh | Explicit new reconstruction from a current correction preview; never triggered by a measurement save. |

Storage/numerics use metres; distance entry accepts units and defaults to millimetres. Precision/goal controls display
millimetres. A connected network need not be determined, robust downweighting can remove information, and a smooth
mesh or small fitted residual does not establish accuracy on unmeasured surfaces. Stage/goal status is advice;
best-effort correction remains possible when its source inputs are available.

## Manual acceptance and normal-job evidence

No normal workflow job, runtime check, service/browser action, model processing, test, smoke script, lint/type check
or build was run for this documentation subset. No real input hashes, artifact IDs or job timings have been recorded
here. Task 3's runtime fields are instrumentation awaiting the first normal job. Older reconstruction trials in the
scan guide are historical evidence and do not validate the replacement workflow.

All acceptance rows remain pending Gert's existing app and real inputs. Reuse normal job evidence once recorded;
do not reconstruct again solely for another review. Do not manufacture sparse cases by changing physical values.
Unavailable scenarios remain unexercised.

| Row | Pending manual evidence |
| --- | --- |
| M1 | Process captures completion → Review capture; preserve changed selection and active entry. |
| M2 | Placement reasons, coverage and comparisons at comparable effort/precision. |
| M3 | Physical completeness, missing modes, consistency and uncertainty on a real partial network. |
| M4 | Checklist entry, tape and saved rows show the same acknowledged physical values. |
| M5 | Enter/blur/Escape, invalid text, focus, failed saves and explicit retry retain the intended draft. |
| M6 | Four stages, shared row contexts and import/assessment/rebuild progress presentation. |
| M7 | Physical-only Check measurements versus joint Preview corrections, with their assumptions. |
| M8 | All useful alternatives, overlapping benefits, visibility/access reasons and rechecks. |
| M9 | Reload/reopen persistence; revised layout retains only explicitly unchanged endpoint pairs. |
| M10 | Preview → explicit Update mesh → source/corrected comparison, preserving original data. |
| M11 | Capture/measurement retention, group actions, tape and camera position/projection/zoom. Old-workflow compatibility is waived. |

Before fabrication, inspect the actual source/corrected surfaces and physical checks withheld from fitting. Source
review alone cannot establish installed solver execution, numerical cost, successful rendering or physical accuracy.
