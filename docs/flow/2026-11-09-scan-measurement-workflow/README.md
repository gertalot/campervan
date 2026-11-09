# Scan workflow: split specification index

The combined design was approved on 9 November 2026. Gert subsequently authorised splitting its independently
deliverable work after the implementation-plan scope check. Existing decisions and evidence remain approved;
Gert approved the split boundaries and delivery order on 9 November 2026. No implementation plan or application change is part of this split.

| Scope | Specification | Standalone completion evidence |
| --- | --- | --- |
| Embedded RTAB-Map | [native spec](../2026-11-09-embedded-rtabmap/spec.md) | Supported real databases import/reprocess without Homebrew runtime linkage, preserving downstream data |
| Measurement network and correction | [measurement spec](spec.md) | Direct physical measurement → independent fit/uncertainty → useful suggestions → explicit corrected reconstruction |
| Scene understanding and editable review | [scene spec](../2026-11-09-scan-scene-review/spec.md) | Target-directed source-supported regions, geometric conflicts, persistent user correction and reviewed context integration |

Use one implementation plan per listed Flow folder. Do not write one plan that implements all three specs. Recommended
delivery order is native → measurement/shared foundations → scene. Native can complete against the current app;
measurement can complete without recognition; scene reuses the delivered shared stage/store/freshness owners.

The [shared-contracts document](shared-contracts.md) assigns each responsibility once and defines the interchange
contracts. It is a common reference, not a fourth implementation scope. All plans inherit the repository prohibition
on tests/service launches and the requirement to preserve unrelated edits and source data.

## Coverage of the approved baseline

The [archived combined specification](approved-combined-spec.md) preserves the approved text at `5e32a66`.
Its original acceptance bullets are numbered AC1–AC15 here only for traceability; wording/requirements are not dropped.

| Original criterion | Final verification owner |
| --- | --- |
| AC1 Import/review handoff | M1 |
| AC2 Reviewed geometry/axes and placement advice | S5 geometry/axes; M2 placement comparison |
| AC3 Automatic requested feature detection | S1 |
| AC4 Independent physical-network completeness | M3 |
| AC5 Checklist/tape shared editing | M4 |
| AC6 Keyboard/input/save-state preservation | M5 |
| AC7 Shared stage/pair/job components | M6; scene must reuse them under C5 |
| AC8 Distinct report meanings and ambiguity | M7 |
| AC9 One planner and all useful pairs | M8 |
| AC10 Reload/layout safety | M9; scene profile/binding extension verified by S4 |
| AC11 Explicit reconstruction and original preservation | M10; scene cleanup integration verified by S6 |
| AC12 Existing data/library/navigation compatibility | M11; N3 preserves importer consumers; scene follows C5 |
| AC13 Homebrew-independent native processing | N1, with N2–N4 preserving detailed native requirements |
| AC14 Editable regions/evidence and scene contradictions | S2–S3 |
| AC15 Reusable knowledge, separate source bindings | S4 |

## Source-section allocation

| Approved section | Active owner |
| --- | --- |
| §1 Outcome/boundary | All inherit preservation/local-only constraints; native replacement isolated to N |
| §2–5 Shared workspace/import handoff | M; native retains existing import contract |
| §6.1 Scene interpretation/editor/knowledge | S and its existing normative scene-review contract |
| §6.2 Geometry-derived axes | S, reusing existing TagAlignment/reference-transform mechanism |
| §6.3 Placement/network comparison | M, consuming S context when present |
| §7–8 Measurement entry/planning/independent fitting | M |
| §9 Graph correction/fusion/publication | M; S supplies reviewed region/context inputs and cleanup editor |
| §10 Store/schema/freshness foundation | M; S owns interpretation/profile-editor content through that store |
| §11 Jobs/API/artifact kinds | Shared C1–C5; domain producers assigned explicitly |
| §12 Interaction/accessibility | Shared C5, implemented once through M foundation and reused by S |
| §13.1 Native library packaging | N |
| §13.2 GTSAM/PyRigi | M |
| §13.2 Semantic tooling and normative scene contract | S |
| §14 Acceptance/documentation | Criterion owners above; each scope updates only its affected factual docs |

The original six reviews and resolved decisions are retained in [review-notes.md](review-notes.md). This is a scope
reorganisation within that planning work, not a new design or a request to repeat the experiments/review passes.
Full pipeline quality, minimal native footprint and the unvalidated numerical defaults retain their recorded risks.
