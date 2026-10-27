# CAD direct manipulation implementation plan

**Goal:** Drag the bed support, drawer, individual cabinet doors and mounted table, with live animation,
temporary cyan feedback and direct joint-constrained movement.

**Design:** [Interaction and research decisions](../../research/cad-direct-manipulation.md).

**Architecture:** Reuse the controller's live position state, viewer motion tracks and existing picker.
Keep direct manipulation inside the viewer subsystem. The existing position PATCH saves a
coherent pose in one request. Picking and highlighting use the existing shared Three.js runtime.

**Project constraints:** No tests, builds, typechecks, automated browser interactions, service starts,
extra app tabs or delegated reviews. Preserve unrelated edits. Use the existing app's runtime diagnostics
and Gert's manual acceptance. Do not introduce a physics framework or change geometry ownership.

## Latest decision: collision detection removed

Gert requested complete removal after browser freezes. Collision modules, dependency, lifecycle preparation,
blocking feedback and solver diagnostics are deleted. Inputs directly update the existing joint positions.
Release drops queued drag input and saves the last accepted pose. Escape restores the initial pose.
No workers, tests, builds or automated browser interactions are introduced.

**Bed gesture decision:** Gert chose continuous dragging through the existing conversion stages. Continued
outward pointer movement after full frame extension moves the cushions and lowers the backrests; reversing
retraces those stages before retracting the frame. Release pauses and re-grabbing resumes. No timed completion.

**Implementation status:** Code and documentation are in the working tree. Read-only runtime inspection confirmed
Ready status, a rendered model, the nine door controls and no browser warnings/errors. The checked items below
record implementation; Gert's hands-on acceptance of gestures, collisions and persistence remains outstanding.
See the research document's acceptance sequence. No tests, builds, typechecks or interaction automation were run.

## 1. Independent door positions

Files: `src/campervan/parameters.py`, `src/campervan/api.py`, `src/campervan/cad/cabinet_doors.py`,
`frontend/src/controller.ts`, and the generated field grouping in `frontend/src/main.ts`.

- [x] Add four independent upper-flap controls and two independent bottom-storage controls. Reuse the
  three existing controls that already affect a single door. Remove the two superseded grouped controls.
- [x] Keep each door's existing hinge origin, axis, sign and maximum angle. Generate one motion entry
  per door and preserve mirroring through `mirror_motion_tracks`.
- [x] Migrate legacy grouped values before dropping retired fields in Python. In browser positions,
  prefer an explicit new value, then the legacy group value, then the server's initial position.
- [x] Group the individual controls under their corresponding cabinet-door sections with recognisable
  labels. Avoid adding six more unrelated controls to the global slider strip.
- [x] Inspect the existing runtime's door metadata and logs after its normal source reload.
- [ ] Gert checks that a single door moves independently and saved positions survive reload.

## 2. Shared pose transactions

Files: `frontend/src/controller.ts`, `frontend/src/api.ts`, `frontend/src/main.ts`, `frontend/src/viewer.ts`.

- [x] Add batch `previewPositions(patch)` and `savePositions(patch)` to the existing controller and a
  batch position PATCH in the API wrapper. Existing single-position callers delegate to these methods.
- [x] Separate deriving a candidate coupled pose from committing it. Bed/table stowing and the pending
  mounted-table return must have one owner and remain available to collision preview without side effects.
- [x] A drag snapshot includes the starting positions and pending table-return state. Cancellation
  restores both. Release persists the accepted joint values and coupled table selection together.
- [x] Expose the existing motion transform application as an internal operation that can evaluate and
  restore candidate world matrices without drawing, saving, deforming cushions or recalculating mannequins.
- [x] Render and update cushion/mannequin state only for the accepted pose through the existing scheduler.
  Preserve the frame coalescing and changed-motion filtering already present in `viewer.ts`.

## 3. Collision detection removal

- [x] Remove collision calculation, geometry preparation, dependency and diagnostics.
- [x] Keep direct dragging/sliders, physical joint limits and bed/table state coupling.
- [x] Handle release at window capture, check primary-button state and discard queued moves on release/Escape.
- [ ] Gert manually confirms dragging and stopping after removal.

## 4. Gesture ownership, feedback and linear/hinged dragging

Files: create `frontend/src/viewer-drag.ts`; modify `frontend/src/viewer.ts`,
`frontend/src/viewer-pieces.ts`, `frontend/src/main.ts`, `frontend/src/style.css` (confirm stylesheet name).

- [x] Describe drag targets using their existing paths and motion entries. Each target identifies its
  grab surfaces, moving assembly, parameter bounds and action label. Reuse the existing vehicle-aware picker.
- [x] Use one capture-phase gesture owner for movable-part presses, retaining the current 4px threshold.
  Suppress camera movement while the press is pending. A click below the threshold retains piece selection.
- [x] Add pointer capture, release, Escape and pointer-cancel handling. Geometry replacement, page/tab
  changes and lost capture restore the start pose and release camera controls. Prevent post-drag clicks
  from triggering selection, cut-list navigation or the viewer's native double-click behaviour.
- [x] Add cyan hover/drag overlays that preserve magenta selection and original materials. Keep overlays
  out of picking. Show an action hint and live amount.
- [x] Keep orbit on background/fixed parts and add the visible camera override to the existing toolbar
  and context menu, with the gesture described there. Preserve existing pan/zoom and measurement behaviour.
- [x] Implement drawer dragging along its slider axis, with the picked point anchored at the start.
  Update the intermediate and moving slider stages through the existing motion entry.
- [x] Implement each door's drag on its hinge arc. Use screen projection and pose continuity to avoid
  flips at ambiguous angles. When the movement is unobservable from the current view, preserve the last
  pose and show a view-direction hint.
- [x] Implement the bed-support gesture through all existing 0–40/40–80/80–100 stages. Keep the frame
  within its physical travel while continued dragging drives the later cushion stages. Reverse the current
  stage before previous stages, pause on release and resume from the current value on re-grab. Show the
  current stage during dragging and keep the conversion slider synchronised. Restore the full pose on cancellation.

## 5. Table steering

Files: create `frontend/src/table-drag.ts`; integrate with `viewer-drag.ts` and the existing table motion paths.

- [x] Resolve the arm's world pivot, fixed pivot spacing, current top joint and grabbed point from the
  current scene transforms. Include the tabletop offset and folded/open leaf geometry.
- [x] Track the pointer in the horizontal working plane at the initial height. Use a stable fallback
  or view hint for an almost edge-on camera; keep the table at its current height and fold.
- [x] Solve the reachable two-joint pose. Preserve world heading for a central grab and smoothly relax
  heading retention towards the perimeter. Select the nearest continuous solution and avoid angle-wrap flips.
- [x] Commit both joint values together. Restore the previous pair on Escape and synchronise both sliders.
- [ ] Gert tunes the centre-to-edge weighting by dragging from several points on the real top in the viewer.

## 6. Runtime inspection and documentation

Files: `docs/cad-model.md`, `README.md`, and the linked direct-manipulation design/research document.

- [x] Update the controls, gesture help and door migration documentation to match the
  final implementation. Record the continuation-distance mapping and removal of collision detection.
- [x] Inspect API/UI logs and the existing Chrome app's console, status and screenshot after normal reload.
  Do not create or run tests, build commands, typechecks or automated interaction checks.
- [x] Give Gert a short manual acceptance sequence: bed conversion both ways and table return; drawer
  stopping/reversing; separate doors; table centre/edge steering; Escape; camera override;
  hidden vehicle/furniture; rapid pointer motion; and saved positions after reload.
- [x] Report observed runtime results separately from manual behaviours awaiting Gert's inspection.
