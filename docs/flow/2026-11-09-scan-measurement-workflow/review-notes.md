# Specification review record

Original spec: [approved combined baseline](approved-combined-spec.md). Status: six reviews, decision walkthrough
and original written-spec approval complete. The later [scope split](README.md) awaits boundary review.

## Author self-review

Checked the written design against the conversation, current scan ownership and the research dossier before
dispatching the six read-only reviews. The draft explicitly covers all four stages and the placement-assessment
addition, measurement-only sufficiency, correlated precision, additional pairs, explicit correction and persistence.
It names shared UI owners and the superseded combined-analysis behavior. It preserves local-only operation,
original data and the repository's prohibition on tests/service launches.

The staged panel approach was approved by Gert before drafting. Subsequent discussion explicitly approved
best-effort partial-network progress and the app-managed RTAB-Map direction. Gert subsequently approved the consolidated
written spec and its normative scene-review contract on 9 November 2026.

## Review boundary

Six read-only roles: gap analysis, ambiguity, scope coherence, design integrity, reuse/tool evaluation and
refactor-style documentation review. Findings must trace to the requested workflow or a direct correctness
dependency. No reviewer edits, executes project code, launches services or interacts with the browser.

All review findings will be aggregated once. Mechanical wording fixes can be applied together; substantive decisions
will be presented one at a time, recorded here, and applied to the specification in one batch after the walkthrough.
No implementation plan or application changes are part of this invocation.

On resuming the experiments, Gert authorised consolidating the amendments already discussed. D1–D4 and the native
integration direction were applied together. Following an explicit return to planning, Gert accepted the scene
review proposal and D6–D8 in ordinary chat. They are now consolidated; the six reviews are not repeated. No further
model runs, experiments or application edits took place during this final planning/consolidation work.

## Timing and execution

- Initial research estimate: 10–15 minutes; began approximately 02:47 UTC, 9 November 2026.
- Draft and parallel reviews started by 03:01 UTC. No repeated builds, installations or runtime processing.
- No tests, browser interactions, services, capture changes or measurement edits performed.

## Consolidated findings (pending decisions)

Repeated findings from different roles are consolidated. These records are not user-approved changes. The spec is
left unchanged while decisions are collected, as required by `flow:plan`.

### D1. Require a complete physical network before guided mesh correction

- Source: scope review, important.
- Evidence: spec §8.4 and §9 add a partial-network scan-assisted correction path, whereas the requested sequence
  establishes a coherent measured shape before correcting the scan.
- Risk: adds a bypass/state path and recreates the original measurement-versus-scan confusion.
- Options: require a sufficiently constrained network; or support an explicitly labelled incomplete-network mode.
- Recommendation: require sufficient physical constraints for the new guided correction, while legacy assisted
  analyses remain inspectable. Precision-target warnings are a separate decision from actual missing freedoms.
- Decision: Gert explicitly requires best-effort processing, including incomplete measurements. Do not add a
  completeness/precision gate. Show scan dependence and limitations; preserve the independent completeness status.

### D2. Define precision independently of display-origin/gauge choice

- Sources: ambiguity and reuse/tool reviews, important (duplicate reports consolidated).
- Evidence: spec §8.1/§8.2 removes global rigid motion but leaves the convention unspecified. Current analyser anchors
  a camera/root; the new network has no physically anchored reference.
- Risk: anchoring different tags changes apparent per-tag ellipsoids, pair ranking and target attainment.
- Recommendation: free-network shape covariance after equal-weight best-fit alignment of all active tags; orthogonal
  removal of rigid-motion directions. Display axes/origin do not affect the score. Reference-relative results, if
  ever provided, are separately labelled.
- Decision: assess uncertainty across the whole shape, independently of display origin. Captured tags can initialise
  and rigidly align an initial fit, but cannot supply missing physical constraints or hide free modes.

## Mechanical tightening applied after aggregation

The reuse/tool review confirmed the installed GTSAM binding already exposes `RangeFactor3` for Point3-to-Point3
ranges. Tightened §13 to require reuse of that factor instead of allowing a duplicate analytic range factor. This
does not change user-visible behavior, the factor engine or the requested independent point-range model.

## Review totals and tool evidence

All six roles completed. Twelve reported findings consolidated to nine distinct findings: one mechanical reuse
tightening and eight substantive decisions. Those decisions were pending at initial review and are now resolved
below. No out-of-scope findings were added to the specification.
The six reviews will not be repeated in this invocation.

The tool reviewer verified PyRigi's generic 3D-check contract and recorded that its required dependency footprint
also includes plotting/notebook packages (including matplotlib, ipympl, ipycanvas, ipyevents and NetworkX), not only
the existing numerical stack. Python 3.13 metadata is supported; actual runtime cost remains unmeasured. This is
evidence for the dependency trade-off, not a separate service or an installation performed during planning.

### D3. Preserve useful local pair improvements while prioritising the worst region

- Source: ambiguity review, important.
- Evidence: §8.1 prioritises worst uncertainty; §8.3's all-useful-pairs threshold could mean global-worst reduction or
  largest individual improvement. Existing `scan_suggestions.py` uses the latter across target dimensions.
- Risk: improvement from 12 mm to 3 mm in one region disappears if another remains at 20 mm.
- Recommendation: scoring returns both largest individual-tag improvement and global-worst reduction. Inclusion in
  all-useful alternatives uses local improvement; recommended batch prioritises missing modes/global worst.
- Decision: report all pairs that meaningfully improve any region, including when the global worst stays unchanged.
  Show both local and global-worst gains; recommended ordering does not filter out useful local improvements.

### D4. Compare proposed tag placements on a common target and measuring budget

- Source: gap review, important.
- Evidence: §6.3 compares best networks while additions/removals change the target set and amount of measuring.
- Risk: adding a tag appears better only because more distances were assumed; removing the weakest target appears
  to improve accuracy by ceasing to measure that region.
- Recommendation: preserve retained reference coverage as the common target, show both measuring count needed for
  target precision and precision attainable at a common measurement budget. Removed coverage is not an accuracy gain.
- Decision: compare precision at a common measuring budget and effort needed for a common target; preserve coverage.

### D5. Decide whether geometry context participates in measurement-network fitting

- Source: gap review, important.
- Evidence: §8.2 promises an optional assisted-network comparison, but surfaces/relationships have no reviewed
  tag-to-surface membership or centre-offset contract.
- Risk: an implementer invents which tags lie on ideal walls/floor, despite insulation, seats and wheel wells.
- Options: add explicit reviewed associations/offsets; or restrict geometry context to alignment, placement planning,
  cleanup and scan correction for this version, keeping the independent measurement fit as the only network fit.
- Recommendation: the latter unless Gert wants those additional physical associations.
- Decision: returned to design discussion. Gert clarified that the intended requirement is intelligent automatic
  recognition/detection of floor, ceiling, walls, wheel wells, windows and front seats from the captured space.
  The previous recommendation narrowed/misunderstood that request. The scene-analysis sections of the draft were
  corrected immediately under Flow's return-to-brainstorm exception; other decisions are still batched later.
  See [scene-understanding research](scene-understanding-research.md). Gert subsequently approved the concrete
  [scene-review design](scene-review-design.md): target-directed Qwen9B/SAM2/RGB-D/Open3D, geometric checks and bounded
  scene reconciliation, linked regions/evidence, independent relabel/boundary editing and persistent user corrections.
  The physical-network report stays independent; no separate geometry-assisted physical fit is introduced. Context
  remains available for interpretation/planning and explicitly later scan correction. Numerical recognition defaults
  were specified during consolidation and are labelled unvalidated engineering choices for final review.

### D6. Sequence saves across the whole measurement document while permitting continued typing

- Sources: gap, refactor-style and integrity reviews, important (duplicate reports consolidated).
- Evidence: §7 serialises per-row commits, but `MeasurementStore` has a single revision for distances, precision and
  exclusions. Multiple rows can submit different values with the same revision.
- Risk: normal fast keyboard entry produces artificial conflicts or dropped commits.
- Options: block committing another row until acknowledgement; or let the shared measurement session sequence all
  mutations using each acknowledged revision, retaining row drafts/states.
- Recommendation: sequence mutations in the shared session and allow continued typing. This is local input-save
  coordination, not a new expensive-job scheduler. Keep real external conflicts explicit.
- Decision: accepted. One shared session sequences all measurement-document mutations using acknowledged revisions,
  while allowing continued editing. Preserve drafts, explicit failures and genuine external conflicts.

### D7. Centralise selective artifact freshness rather than relying on document revision alone

- Source: refactor-style review, important.
- Evidence: §10 promises that access exclusions invalidate plans but not physical fits; existing settings edits
  increment the same document revision and current analysis freshness rejects every revision change.
- Risk: inconsistent checks either invalidate useful fits unnecessarily or accept changed distances as current.
- Recommendation: keep revisions for conflict detection/provenance; one artifact-kind dependency policy compares
  relevant content fingerprints. All UI stage/action eligibility consumes that policy.
- Decision: accepted. Use one artifact-kind content-dependency/fingerprint policy; revisions still handle concurrency
  and provenance. UI freshness and action eligibility use that shared policy, with inspectable older artifacts.

### D8. Separate reusable geometry definitions from per-capture bindings

- Source: integrity review, important.
- Evidence: §10 stores source frame/pixel associations in layout-scoped context, while later captures rematch them.
- Risk: reviewing another capture can replace an earlier capture's bindings or invalidate unrelated workflows.
- Recommendation: layout-scoped reusable definitions/reference roles plus source/workflow-scoped bindings/review
  decisions referencing a profile revision. Updating the reusable profile is an explicit action.
- Decision: accepted after clarification. Reusable van knowledge is saved as editable textual vision context plus
  structured geometry relationships and tag references. Per-source masks/regions/corrections stay separate. Reuse
  guides a new capture but cannot blindly copy old coordinates or rewrite another capture's interpretation.

## Final consolidation and remaining evidence limits

All eight substantive findings have dispositions. Gert also approved replacing the Homebrew executable integration
with app-managed minimal RTAB-Map libraries and a narrow Python binding, preserving upstream processing algorithms.
The spec and its normative scene-review contract name the selected recognition path, intermediate data, matching
criteria, explicit initial defaults, contradiction handling and correction UX. No extra service or semantic optimiser
is selected. Native packaging and the complete recognition chain are not implemented or proven by these documents.

The two-view target-directed 9B trial establishes useful proposals and local runtime, while retaining the wrong
floor/door-panel detection. It does not establish whole-capture quality, correspondence reliability or throughput.
The numerical defaults are engineering choices to review, not sensor calibration or measured accuracy. The native
investigation establishes source-level integration points and the broad installed linkage baseline, not a working
isolated package or guaranteed disk saving. Gert gave final written-spec approval on 9 November 2026. This completes
flow:plan; implementation planning remains a separate user-invoked phase.

## Authorised split after the implementation-plan scope check

The implementation-plan phase identified three independently deliverable outcomes in the approved combined spec.
Gert authorised returning to planning and splitting those scopes without changing the approved design.

- Embedded RTAB-Map owns the native importer replacement and runtime isolation, verified using the existing app.
- Measurement workflow owns physical fitting/planning/correction and its shared stage/store/freshness foundations.
- Scene review owns recognition, region editing, reusable-knowledge authoring and reviewed-context integration,
  consuming those shared foundations and existing captures.

The original approved text is archived unchanged. The scope index maps all 15 acceptance bullets and every source
section to an active owner. Shared contracts assign producers/consumers once; they are not another delivery project.
Native delivery does not depend on new UX. Measurement delivery does not require recognition. Scene integration
depends on the shared workflow foundation rather than implementing a duplicate panel/store and migrating it later.

The focused split self-review checked requirement coverage, ownership, data seams, dependency order and relative
references. Original tool choices, limitations and evidence remain binding. No new requirement, algorithm, runtime,
experiment or application edit is introduced. The original six reviews are not repeated. Boundary review of the
three written split specs remains pending; their semantics retain the original approval.
