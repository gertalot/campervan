# Stage 1 — accumulated implementation review

Status: implementation/source review complete; Gert's visual acceptance pending. No later stage is implemented.

## Scope and execution record

- Plan/scope: [stage-1-plan.md](../stage-1-plan.md); specification: [spec.md](../spec.md), A1/A2/A9 stage-1 portions.
- Branch: `develop`; starting revision: `94392cc912b00b88f1a3b6ad8e5d44b42525b359`.
- Started: 10 November 2026, 07:08 UTC. Implementation completed within the 30–60 minute estimate.
- Main agent implemented T1–T3 sequentially. One accumulated source review replaces generic per-task/six-role loops,
  as explicitly required by the approved plan. No subagents, tests, builds, lint, services or browser automation.
- Authorised pre-existing scan work: shared tag highlight renderer and text-selection styling were preserved while
  removing confidence UI; existing modifications inside deleted workflow UI files are superseded by the clean break.
- Direct existing dependencies included unchanged: the shared panel's `closerequest` correction and capture-job
  cancellation across `scan-job-status.ts`, `scan-import-api.ts`, `scan_processing.py` and `scan_processing_api.py`.
  These were already present in the working tree and implement the plan's required dismissal/cancellation behaviour;
  including them makes the commit coherent rather than dependent on uncommitted scan fixes. No new mechanism added.
- Unrelated CAD/planner/API changes remain outside the implementation commit. Only the scan workflow imports and
  registration removals are staged from `api.py`, preserving unrelated working-tree edits.
- Old workflow progress: one record discarded from `data/scan-workflows.json`, retaining profiles and other metadata.
  No capture assets, physical measurement files or artifact directories were read/deleted for this operation.
- All edits are planned locations; no material scope expansion, admitted issues or deferred decisions.

## Implementation and source evidence

| Task / criterion | Result |
| --- | --- |
| T1 / A1 | `scan-workflow-panel.ts` uses the shared nonmodal shell and a six-item progress list; only Review capture is active. Upcoming steps have no empty screens or actions |
| T1 / A9 | Old panel, tape orchestration, sessions/rows, confidence view, frontend workflow transport and backend workflow route module removed. Independent measurement/layout/import APIs and domain algorithms retained |
| T1 / §3 | `side-panel.ts` is reused unchanged, retaining X/Escape dismissal and outside-click persistence; tag outlines/IDs and the shared emphasis renderer remain |
| T2 / A2 | `scan-library.addCaptures` passes the current result's layout to existing `scan-import.open`; missing layout needs explicit selection. Group/drop paths retain their current invocation |
| T2 / A2 | Existing cumulative database selection, upload, process request, progress and cancellation retained; completion no longer creates an old workflow |
| T3 / §3/§10 | Existing camera, result/layer persistence and generation guards retained. Import completion opens review only for the displayed completed result; user navigation takes precedence |
| T3 / A9 | Practical guide and original scope index updated to six-stage, stage-by-stage delivery; no old workflow fallback instructions |

One direct correctness fix during source review: a completed job's failed/deleted result must not open review on a
different displayed result. `scan.ts` now checks `renderedScan.key` before opening the completed capture's review.
The missing-layout path also guards `start()` itself, including the existing job-view retry invocation, rather than
depending solely on browser form validation.

## Checks and limits

- Read-only source searches for `createScanMeasure`, `createWorkflow`, `register_scan_workflows`, deleted module
  imports and `measure.*` call sites: no remaining old interface references in frontend/application source.
- Source-traced the two import entry paths and guarded completion; no native reconstruction implementation change.
- `git diff --check`: final staged implementation checked before commit; see commit result in the conversation.
- Current primary UX guidance consulted: [USWDS step indicator](https://designsystem.digital.gov/components/step-indicator/)
  and [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html). Decisions: explicit current
  stage, noninteractive upcoming labels, shared nonmodal panel, and existing polite progress without stealing focus.
- Runtime rendering, cumulative reconstruction, visual layout and camera behaviour are not claimed verified. Gert's
  visual acceptance steps are in the plan. If his running API does not reload automatically, he must restart it.
- No full Flow programme, additional review cycle, stage-2 planning or implementation is triggered by this report.

Admitted/deferred bead IDs: none. No `.beads` contents accessed. Stop here for Gert's visual feedback.

## Later capture/reconstruction revision

The 11 November 2026 revision has its own [completion and single-review evidence](05-capture-reconstruction-completeness.md).
The stage-1 shell evidence above is retained; it is not a claim that photographic processing was already present.
