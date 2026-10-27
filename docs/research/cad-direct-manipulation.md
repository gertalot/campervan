# Dragging moving parts in the CAD view

27 October 2026. Gert approved direct dragging of the bed support, mounted tabletop, individual cabinet
doors and drawer, with temporary highlighting. Collision detection was subsequently removed at his request. Implementation is in the current working tree;
hands-on acceptance remains with Gert.

## Interaction

Dragging drives the existing live position controls. It must preserve cushion/pillow/mannequin animation,
automatic table stowing and return, sidebar values, browser persistence and the current camera.
Moving parts follow their joints; furniture overlaps are permitted. No drag requests CAD regeneration.

Use the existing 4px click/drag threshold. An ordinary click selects; a double-click keeps the cut-list
navigation. Reserve an unmodified primary-button gesture on a movable part for manipulation. Background
and fixed-part drags keep camera orbit. Add a labelled camera-orbit override to the existing toolbar and
contextual help so the alternative is discoverable without this chat. Preserve camera pan and zoom.
Camera motion must not start while a part gesture waits to cross the threshold.

Hover shows a cyan outline and grab cursor with a short action hint. Active dragging uses a stronger cyan
highlight on the moving assembly, distinct from persistent magenta piece selection. Release restores the previous appearance and saves
the accepted pose. Escape restores the entire pre-drag pose, including coupled table state. Pointer
cancellation, lost capture, geometry replacement and tab changes cancel and release camera/pointer state.

Keep the grabbed point as the gesture anchor; avoid a jump at drag start. Capture the pointer during the
gesture. For views where an allowed movement projects to almost no screen displacement, keep the last
valid pose and explain which view direction would make it draggable. Never infer an arbitrary depth jump.
Keep sliders as an alternate input method. Both input methods apply joint positions directly.

## Allowed movements

| Grabbed part | Allowed movement |
|---|---|
| Long-bench moving support/slats | Existing sideways extension and linked conversion sequence |
| Drawer tray/front | Existing fore/aft slider travel; linked intermediate slider stage |
| One cabinet door or its latch | That door's hinge arc, from closed to its present maximum opening |
| Either mounted tabletop leaf | Coordinated arm swivel and tabletop yaw at the current height/fold |

The stowed table is a storage preview and has no working-arm drag. Tabletop dragging does not change its
mount offset, height or fold. The tabletop's grab-point weighting uses the current visible top's geometric
centre, accounting for mount offset and whether the leaf is open.

Near the top's centre, preserve its world orientation by counter-rotating the tabletop joint while the arm
swivels. Towards its edges, smoothly relax orientation retention so the grabbed point can steer both joints.
Choose the solution nearest the previous pose, unwrap angles during a gesture and normalise only when
saving. Arm length stays fixed. An unreachable target produces the nearest reachable pose without a flip.
The weighting is a proposed custom interaction that needs Gert's hands-on tuning.

Cabinet upper flaps and the two bottom storage doors have independent positions, alongside the other three
individual door controls. Existing group values migrate into the corresponding new fields in both the saved
project and browser positions.

## Bed conversion gesture

The existing frame reaches full extension at **40%** of the bed control. From 40–80%, cushions reposition;
from 80–100%, backrests lower. This follows `cad/bed_motion.py` and `parameters.py`.

Gert chose one continuous, reversible drag through all three stages. Dragging the support follows its
physical sideways travel over 0–40%. The frame stays at full extension while continued pointer movement
in the same general direction drives cushion repositioning over 40–80% and backrest lowering over 80–100%.
Reversing direction retraces the current sequence: raise the backrests, put the cushions back, then retract
the frame once progress falls below 40%. Reversing partway through a stage reverses from that current pose.

Release pauses at the current progress; a new drag resumes there. No timed completion, snapping or extra
click starts another stage. Retain pointer capture after the frame reaches its stop and show the current
stage beside the active drag, so the stationary frame does not suggest that the gesture has finished.
Keep the full slider available and synchronised with the same 0–100% conversion position.

One physical frame-travel distance maps to 40 percentage points throughout the gesture: full conversion
requires 2.5 times that distance, across one or several drags. The same pointer direction continues through
the remaining stages. If the view makes physical travel hard to project, use the common view-direction hint.
Re-grabbing permits progress across several drags when the pointer reaches the viewport edge.

Escape restores the full pre-drag conversion/table pose. Release stops the gesture, drops queued input and saves
the current accepted pose. Window-level pointer release and a primary-button state check prevent a stuck gesture.

## Collision detection removed

Gert requested complete removal after the collision searches caused browser freezes. The viewer now applies joint
positions directly. The collision modules, geometry preparation, diagnostic attributes and dependency are removed.
No worker is used. Cushions, pillows, mannequins, gear and furniture do not block interactive movement.

## Implementation territory

`frontend/src/viewer.ts` already applies motion tracks once per animation frame. `controller.ts` owns
coupled bed/table state and persistence. `viewer-pieces.ts` owns picking, selection and click navigation;
reuse it and the vehicle-aware picker. `renderer.ts` shares the OCP renderer's Three.js runtime.
`cad/cabinet_doors.py`, `parameters.py`, `api.py` and `viewer.py` own door poses, their schema and tracks.
The frontend uses the existing multi-field position PATCH for coherent pose saves.

## Manual acceptance

Check direct bed, drawer, door and table dragging; release stops movement; Escape restores the starting pose;
bed conversion still stows/returns the table; selection, double-click navigation and camera override remain available.
No tests, builds, typechecks or automated browser interactions are run under the project instructions.

## Sources


- [Onshape mates](https://cad.onshape.com/help/Content/Assembly/mates.htm): drag assemblies within their
  permitted degrees of freedom.
- [Fusion selection](https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-SELECTION.htm): component
  dragging, camera/selection interaction and an alternate gesture.
- [W3C dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements): retain an
  alternative that does not require dragging.
- [Pointer capture](https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture): continue
  the gesture after the pointer leaves the picked surface; handle release and cancellation.
- [Three.js OrbitControls](https://threejs.org/docs/pages/OrbitControls.html): existing camera gestures.
- [Three.js OBB](https://threejs.org/docs/pages/OBB.html): box intersection can prune pairs; it does not
  describe the openings in a plywood frame.

The research establishes useful mechanisms. It does not establish that the proposed table weighting feels
natural, or that a few documented input behaviours constitute universal UX/accessibility compliance.
