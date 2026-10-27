# Using the application

The four tabs share one saved project. Switching tabs keeps the camera and visibility settings.

## CAD

### Camera and visibility

- Drag fixed parts or the background to orbit. Use the ViewCube for a face, edge or corner view.
- Hide groups with their eye icons or use the category checkboxes in the sidebar.
- **See inside** fades obstructing vehicle surfaces. Turn it off to view the opaque body; windows remain transparent.
- Show **Wheel arches** independently of the rest of the vehicle.
- Resize the sidebar by dragging its right edge. Collapse groups by clicking their headings.

The browser remembers the camera, visibility and sidebar choices. Use the viewer toolbar to reset or refit the camera.

### Dimensions and moving parts

Change dimensions in the sidebar and apply them. The app reports invalid values and explains dependent limits.
**Regenerate** forces a fresh geometry build. Matching saved geometry loads without rebuilding.

Live sliders and direct dragging operate the bed, rear drawer, individual cabinet doors and mounted table.
Movable parts glow cyan on hover and during dragging. Motion follows the joint limits; there is no collision detection.

| Control | Behaviour |
| --- | --- |
| Long bench conversion | Extends the frame, repositions cushions, then lowers backrests. Reverse to undo the sequence. |
| Drawer extension | Moves the rear drawer on its sliders. |
| Doors closed | Closes both sliding doors and lowers the rear hatch. At 0%, the hatch is raised 90°; at 100%, all doors are closed. |
| Cabinet door sliders | Open individual doors; find them under Cabinet → Doors. |
| Unfold tabletop | Top-level slider: 0% folded, 100% flat. |
| Laptop table | Adjust mounting/stowed pose, height, arm swivel, tabletop rotation and offset. |

When dragging the bed, continue pulling after the frame stops to reposition the cushions. Reverse to put the cushions
back before retracting the frame. Release pauses and saves the pose. **Escape** restores the drag's starting pose.
Dragging near the tabletop centre keeps its heading; dragging near an edge steers both swivel joints.
Extending the bed stows a mounted table; retracting the bed restores it when the bed caused the stow.

Use **Alt-drag** or the toolbar's **Orbit camera over movable parts** button (**O**) to orbit over draggable objects.
Right-click for the same camera action and its shortcut. Rotate the camera if a part's allowed motion is edge-on.

### Mannequins and gear

Expand **Mannequin** to adjust seated and lying poses. The main visibility checkbox toggles the group; each person's
eye icon controls that mannequin. The lying mannequins follow the bed conversion. Pose, body shape and foam compression
are visual fit references.

The local app saves all three poses and their visibility choices in `data/project.json` without regenerating CAD.
Static exports include that configuration. Visitors can adjust the mannequins in their browser; a newly published
configuration replaces the previous export's starting poses.

**Stored gear** contains the folded chairs, solar bag and chilly bin. Use their group eyes and live controls to explore
positions. Reference geometry and hardware envelopes still need comparison with the physical van and equipment.

### Finding a piece

Double-click wood in CAD to find it in the cut list. Double-click a cutting piece to frame it in CAD.
Both views highlight the piece in magenta until you select another or press **Escape**. Clicking empty CAD space clears
selection. The CAD toolbar and right-click menu also offer **Show in cut list** and **Clear selection**.
Faded near-side vehicle surfaces do not intercept interior piece picking in **See inside** mode.

## Bill of materials

Track categories, tags, quantities, bought items and costs in the purchase grid. Use filters to narrow the list;
the totals show the filtered items and whole project. Shared stock appears once across its uses.

Expand **CAD stock and cutting details** for supplier links, specifications, availability, component uses and grouped
cut sizes. Material links in the CAD sidebar open and highlight the corresponding stock entry.
Selected material dimensions drive the model; measured overrides account for the stock purchased.

## Plan

Write multiline notes, nested numbered tasks, tables and linked purchases in the rich editor.
Use the toolbar, slash commands and contextual menu for actions and their shortcuts.
**Enter** continues text within a task; **Cmd/Ctrl+Shift+Enter** adds a task.

See [planner and purchase details](planner.md) for editing, saving and recovery controls, and
[the cushion guide](squabs-guide.md) for the squab instructions.

## Cut list

**All pieces** shows named flat drawings grouped by assembly. Select a plywood thickness for sheet layouts, or select
timber and other sheet materials. Each sheet heading identifies the material, thickness, size and sheet number.
Single-click a piece for its details; double-click to show it in CAD.

**Cutting settings** applies to the whole project. Choose straight saw cuts or nested shapes, set kerf/tool width,
edge trim and grain direction. Set stock sizes, available offcuts and individual grain overrides under each material.
Custom stock needs confirmed dimensions before arranging it.

Selecting a thickness starts a background layout search. It publishes improvements and saves the best layout.
**Stop optimisation** keeps that result. Design or cutting-setting changes stop old searches and mark previous layouts.

Straight-cut plywood candidates rank by sheet count, then the largest rectangular offcut's area/perimeter ratio,
then the number of blank-separating cuts. A proven minimum sheet count does not prove the best possible offcut or cut
count. The search uses lower CPU priority and alternates running and paused intervals.

Straight saw cuts produce rectangular blanks and an expandable cut sequence. Cut curves, notches, holes and finishing
features afterwards. Nested shapes use the sampled profiles; cut pieces inside holes before the surrounding frames.
Timber uses crosscuts in either mode. Hardware does not appear in the cutting list.

Use **Save drawing** for sheet SVGs, **Export cut list** for CSV and **Print** for the current view.
