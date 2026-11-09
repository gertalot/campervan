# Scan measurement workflow: research

- **Subject:** capture review, tag placement, measurement planning, measurement-only fitting and scan correction.
- **Scope:** the local scan subsystem, its browser UI, direct API contracts and saved scan documentation.
- **Revision:** `develop`, HEAD `633943e`, with existing dirty/untracked scan implementation inspected read-only.
- **Downstream use:** `flow:plan`; this is research, not an approved specification or implementation plan.
- **Started:** 9 November 2026, approximately 02:47 UTC. Initial research estimate: 10–15 minutes.

## 1. Subject and stack

The existing local FastAPI/Python 3.13 application imports RTAB-Map databases, reconstructs with Open3D and displays
results through the existing Three.js/CAD renderer. Optional scan dependencies already include GTSAM 4.3.0 and
Open3D 0.20.0. The frontend uses TypeScript and native DOM controls, without a separate component framework.
[confirmed: pyproject.toml; frontend/package.json; src/campervan/scans.py]

## 2. Observed purpose

The user wants a repeatable capture-to-corrected-mesh workflow. Physical measurements must independently establish
whether the tag network is coherent, sufficiently constrained and precise. Only an explicit later action corrects
the scan. Tag placement advice precedes measuring. Approximate geometry context helps alignment and cleanup.
[user-stated]

The saved photogrammetry document records original RGB-D/graph preservation, GTSAM adjustment, Open3D fusion and
texture generation. Its current analysis section describes a joint scan-and-distance fit, which conflicts with the
new measurement-only assessment requirement. [confirmed: docs/photogrammetry.md]

## 3. Boundary and audiences

One local user; no deployment, new service, cloud API or generic workflow framework. The scan subsystem owns this
work. CAD generation, furniture, planner and general app navigation are outside the boundary. The shared camera and
renderer are direct dependencies whose controls and state must be preserved. [user-stated; confirmed: AGENTS.md]

## 4. Mental model

- Capture group: organises source databases and generated results.
- Tag layout: identifies a fixed physical arrangement; matching numeric IDs alone do not prove compatibility.
- Observation: immutable entered physical distance and precision, independent of fitted geometry.
- Measurement shape: positions inferred from physical distances, with explicit completeness and uncertainty.
- Geometry context: reviewed approximate regions and relationships, distinct from measured evidence.
- Corrected result: new derived reconstruction, preserving source captures and observations.

The first three and result lineage exist; the independent measurement shape and geometry context do not yet exist
as separate responsibilities. [confirmed: scan_layouts.py; scan_measurements.py; scan_rebuild.py; scan_analysis.py]

## 5. Contract and data

`MeasurementStore` owns canonical pairs, units in metres, entered text, source run, precision, exclusions, revision
checking and atomic replacement. Managed layouts live beside project data; legacy measurements remain supported.
The library owns presentation metadata, groups and result selection, not physical geometry.
[confirmed: src/campervan/scan_measurements.py; scan_layouts.py; scan_library.py]

Existing analysis APIs create immutable input snapshots and asynchronous jobs, check stale revisions/source hashes,
and explicitly rebuild/revert. Their current result semantics are scan-conditioned; they cannot merely be relabelled
as measurement-only. New context/checklist/progress state has no existing persistent owner.
[confirmed: src/campervan/scan_analysis_api.py; frontend/src/scan-measure-panel.ts]

## 6. Operations and lifecycle

Import already uploads multiple databases, selects a group/layout and starts the existing scan CLI worker. Completion
currently offers Show result in viewer. Measurement editing currently routes through two-tag tape selection; checklist
distance fields do not exist. Result/layer selection survives tab reload through session storage, while workflow
progress does not. [confirmed: frontend/src/scan-import.ts; scan-measure.ts; scan.ts]

## 7. Failures and recovery

Measurement conflicts are 409 and require explicit retry after refresh; failed saves must remain visibly unsaved.
The existing worker records actual stages/logs and failed/interrupted jobs. Original databases and physical records
are retained. Unobservable joint graphs produce diagnostics rather than fabricated finite uncertainty.
[confirmed: scan_measurements.py; scan_processing.py; scan_analysis.py]

## 8. Setup and operational concerns

Use existing local API/subprocess ownership. Do not start services, access protected environment files or run/create
tests. No runtime analysis, reconstruction, browser interaction or measurement mutation was performed in this research.
The worktree contains substantial unrelated edits; preserve them. [confirmed: AGENTS.md; git status --short]

## 9. Mechanism and rationale

### Existing reuse boundaries

| Responsibility | Existing owner | Decision for design |
| --- | --- | --- |
| Viewer and composition | `frontend/src/scan.ts` | Keep one workspace and renderer |
| Panel shell, X, focus, scrolling, modality | `frontend/src/side-panel.ts` | Reuse for stage content and both managers |
| Tape input and distance parsing | `frontend/src/scan-measure.ts` | Share save/validation with direct pair entry |
| Current analysis/recommendation UI | `frontend/src/scan-measure-panel.ts` | Evolve this responsibility; avoid parallel managers |
| Scan library | `frontend/src/scan-library.ts` | Retain library ownership and import entry point |
| Upload and processing | `frontend/src/scan-import.ts` | Reuse APIs/worker; provide review handoff |
| Tag/line projection | `frontend/src/scan-tags.ts` | Keep one overlay owner/reference transform |
| Jobs and logs | `scan_processing.py`, `ProcessingJob` frontend type | Share presentation, not another scheduler |
| Source graph | `scan_graph.py` | Preserve native links/information; fitted poses are initial values |
| Mesh/texture generation | `scans.py`, `scan_rebuild.py` | Keep shared reconstruction path |
| Clearance | `scan_visibility.py` | Reuse conservative obstruction/free-space assessment |

The panel shell is already shared, but progress/log views are duplicated between import and analysis. Pair-row
distance editing should be shared across initial checklist, extra suggestions, rechecks and saved measurements.
Both are bounded scan UI reuse opportunities, not an app-wide component-system redesign.

The current solver includes original odometry/loop closures/gravity/tag observations before adding physical ranges.
Its covariance and suggestions therefore cannot establish physical-network sufficiency. Existing pair Jacobians and
correlated covariance scoring can be adapted, but scan-correction and measurement-only factor models must be separate.
[confirmed: scan_analysis.py; scan_suggestions.py]

### Primary UX guidance consulted on 9 November 2026

- [GOV.UK: complete multiple tasks](https://design-system.service.gov.uk/patterns/complete-multiple-tasks/): group
  related tasks, explain order and status, support returning sessions. Applied to four stages with revisiting and
  persistent progress; does not require copying government page layouts.
- [WAI tabs](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/): use documented semantics/keyboard handling if stages
  are tabs. Do not label arbitrary progress indicators as tabs.
- [WAI status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html): announce saving and job
  progress without stealing focus.
- [GOV.UK error messages](https://design-system.service.gov.uk/components/error-message/): identify errors beside
  fields, associate error text and explain correction. Preserve typed values.
- [WAI On Input](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html): avoid unexpected context changes during
  editing. Preserve viewer camera, current row, drafts and focus during job updates.
- [WAI modal dialogs](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/): reserve modal semantics for actual
  blocking confirmations; workflow inspection must leave the viewer usable.

These support specific decisions, not a claim of comprehensive accessibility compliance.

### Technical primary sources

- [Global rigidity](https://arxiv.org/abs/0710.0926): local rank and global uniqueness differ. Counting distances or
  finding one converged fit does not prove a uniquely constrained 3D shape.
- [Open3D plane/patch detection](https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html): established
  geometric surface extraction. The release documentation currently identifies 0.19; implementation uses pinned
  0.20.0, so exact API/version details require source verification during specification.
- [GTSAM robust models](https://gtsam.org/2019/09/20/robust-noise-model.html): robust estimation can reduce outlier
  influence; it does not establish measurement completeness.

## 10. Outside scope

Automatic CAD generation, CAD overlays, service infrastructure, general frontend framework changes, model training,
dependency upgrades and unrelated cleanup. A new major vision dependency would require explicit scope approval.

## 11. Questions for downstream work

- Confirm UI approach: evolve the existing panel into the staged workspace versus a separate wizard.
- Specify observable-rigidity/ambiguity status, selection objective/stopping criteria and honest uncertainty claims.
- Specify layout changes and measurement carry-forward when some physical tags move.
- Specify automatic region/semantic suggestions versus manual review and what happens when evidence is insufficient.
- Specify durable workflow/context ownership without putting physical state in library presentation preferences.

## 12. Things I might be wrong about

- Geometric patch detection alone may not reliably identify windows or the front region in these captures; semantic
  confidence and user correction must be designed explicitly. [gap]
- Quantitative tag-placement recommendations depend on approximate geometry and measuring precision before physical
  ranges are entered; predictions cannot be presented as achieved physical accuracy. [likely]

## 13. Source coverage

Read the current scan pipeline, alignment, graph, measurements/layouts, analysis APIs, suggestions, rebuild,
visibility, worker, dependency declarations, relevant app wiring, photogrammetry documentation and predecessor plan.
Frontend research inspected workspace, panels, import, measurement/tape, overlay, API clients, styles and direct
consumers. Git history contains the initial photogrammetry idea; most current scan implementation is untracked, so no
committed implementation rationale is available. Repository instructions explicitly prohibit test inspection through
execution or creating replacement tests. No tests/services/browser interactions were run.

One WAI error-identification URL and a GTSAM rangefactor URL failed retrieval; neither is relied on. The accessible
GOV.UK field-error guidance covers the relevant UX decision. One read-only research subagent inspected frontend reuse
under the invoked planning/research skills; the required six specification reviews have not run yet.
