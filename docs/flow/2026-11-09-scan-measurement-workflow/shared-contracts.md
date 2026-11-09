# Shared ownership and interchange for the three scan scopes

Status: split draft preserving approved contracts; boundary review pending. See the [scope index](README.md) and
[approved combined baseline](approved-combined-spec.md). This is a common specification reference, not a fourth
deliverable or a new platform mechanism. Each implementing scope has its own spec/plan and completion evidence.

## One owner for each responsibility

| Responsibility | Delivery owner | Existing mechanism / consumer obligation |
| --- | --- | --- |
| Native decoding/session reprocessing | Embedded RTAB-Map | Replace exporter/reprocessor calls through one adapter; preserve downstream inputs |
| Four-stage composition and workflow state | Measurement workflow | Evolve `scan-measure-panel.ts`; scene review contributes content to its Review capture/cleanup views |
| Side-panel shell | Measurement workflow | Reuse `side-panel.ts` for stages and scan library; scene content never creates another shell |
| Measurement mutation sequencing and pair editor | Measurement workflow | One session over the existing measurement store, shared by tape, rows, precision and exclusions |
| Job/status/log presentation | Measurement workflow | Shared view over existing `ProcessingJob`; every domain uses existing `ScanProcessing.start_action` |
| Workflow/profile/review persistence schema and atomic writes | Measurement workflow | One `ScanWorkflowStore` beside existing layouts/measurement storage; scene code owns interpretation content through this store |
| Artifact dependencies/freshness | Measurement workflow | One kind-based content-fingerprint policy, consumed by all backend eligibility and UI status |
| Semantic proposals/masks/3D associations and review decisions | Scene review | Produce source-bound context artifacts; preserve user edits and original evidence |
| Region editor and knowledge-authoring content | Scene review | One linked label/boundary editor reused for automatic/manual/correction/cleanup contexts |
| Tag projection/camera/reference transform | Existing owners, extended by the consuming scope | Keep one scene/reference-transform owner; region overlays follow the same camera/reference frame |
| Physical-network fit, pair scoring and placement comparison | Measurement workflow | Reuse GTSAM range factors and existing scoring/visibility owners; consume semantic context optionally |
| Graph correction, fusion, cleanup application and textures | Measurement workflow | Existing `scan_analysis.py`, `scan_rebuild.py`, `scans.py` publication path; scene review supplies reviewed source masks/context |

These are scan-local ownership assignments. They do not introduce a plugin registry, generic workflow framework,
new service or unrelated consumers. Exact module extraction/signatures are implementation-plan work; those choices
must preserve this single ownership and the typed data invariants below.

## C1. Imported capture interchange

The native producer retains frame/node/session identity, original RGB/depth/confidence, calibration, depth units,
sensor-to-node transforms, saved camera-to-world optical poses in metres, landmark observations and native graph
links/information. It preserves source hashes, settings and source-copy lineage. Measurement and scene consumers
use the existing run/assets/manifests; neither consumes a native package's private memory layout or executable path.

Existing saved runs remain valid inputs. Native package delivery does not require reimporting existing runs, changing
physical measurements or producing scene artifacts. Conversely, the other scopes can use runs imported by the
current tools. No extra interchange export/import pipeline or mandatory source migration is introduced.

## C2. Reusable knowledge and source-bound interpretation

The shared store distinguishes reusable, versioned textual model context/structured classes, relationships,
tolerances and tag references from source/workflow bindings. Bindings identify the source run, profile revision,
feature IDs, supporting frame/pixel masks, observed 3D associations, reviewed label/boundary decisions and enabled
relationships/cleanup masks. Scene code writes these through the same revision/atomic-write owner.

No old mask/world coordinate is implicitly valid in a new capture. Saved user corrections are retained on reanalysis;
new profile versions do not retroactively replace earlier workflows' bindings. Explicit profile promotion remains
separate from correcting a captured region. Features missing depth may stay image-only and cannot become measured
surfaces/occluders. All actual tag roles, layout IDs, dimensions and paths are data passed into reusable code.

## C3. Optional context into placement/correction

Placement, visibility and correction consume the current reviewed source-bound context artifact, or its explicit
absence. Missing/uncertain scene analysis does not block checklist entry, physical-network analysis or best-effort
correction. It cannot be silently replaced with hardcoded vehicle geometry, fabricated certainty or another manual
scene pipeline. UI states explain unavailable context rather than claim it exists.

Context supplied to correction includes source association, relationship kind/tolerance, enable state, revision and
observed support. Cleanup supplies reviewed source pixel/element exclusions. Reconstruction reprojects these with
corrected optical poses before original RGB-D fusion. Scene interpretation is never added to independent physical
measurement uncertainty or counted as a second independent observation of the same scan surface.

The measurement scope implements these optional-input consumer seams and skipped-input explanations. The scene
scope implements the producing/editor side and owns final verification of scene-informed axes/cleanup integration.
Shared schema changes needed for that producer extend the existing store/contracts, not architectural ownership.

## C4. Artifact kinds and freshness

Retain explicit artifact kinds: `measurement_network`, `measurement_plan`, `placement_review`, `context_review` and
`scan_correction`. Measurement delivery owns the first, second, third and fifth producers; scene delivery owns the
fourth. No consumer assumes every artifact includes camera poses, covariance or captured-to-fitted movements.

Each artifact records source/layout/profile/review references, relevant content fingerprints, algorithm/model
versions, settings/assumptions, producing job and provenance revisions. Revisions still protect writes; one shared
dependency policy decides which content changes invalidate which artifact. Historical artifacts remain inspectable
with reasons, while stale correction application is forbidden. Scene additions extend that policy, never duplicate it.

## C5. Shared interaction and operations

Preserve the one renderer, existing camera/navigation, selection, normal writing/IME and keyboard focus. Overlay
panels never resize the canvas; stage/result updates do not move the camera or interrupt active edits. Shared action
definitions serve toolbar/menu/shortcut entry points. Named actions expose purpose; invalid/save/error states are
visible beside the affected controls. Scene review uses the same source assets and overlay/reference frame.

Keep one active expensive processing worker. Reuse current job failures/logs and explicitly requested retry; do not
add queues, readiness protocols, model servers or another scheduler. User data remains local and originals survive
failures. Do not create/run tests, start services, automate browser interactions or resume experiments in planning.
Gert's manual inspection in the existing app remains acceptance; each scope names its focused evidence owner.

## Delivery order and independent completion

1. Embedded RTAB-Map can be completed against the current importer without either new UX scope.
2. The measurement workflow establishes the shared UI/store/freshness and optional context consumer contracts. It can
   complete its physical measurement/correction loop using existing saved runs, without native packaging or recognition.
3. Scene review lands its producer/editor against those shared contracts and completes its own recognition/review and
   context-integration acceptance. It uses existing runs and does not require a new native import or a complete tape network.

This order avoids a temporary duplicate scene panel/store. Measurement's ownership of common foundations is enabling
work for its own workflow, not a separate fourth platform project. The native deliverable is not a scheduling gate
for the measurement scope; the recommended order simply addresses the Homebrew/disk requirement first.
