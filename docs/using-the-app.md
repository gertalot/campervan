# Using the application

The project tabs share one saved project. Switching tabs keeps the camera and visibility settings.

## CAD

### Camera and visibility

- Drag fixed parts or the background to orbit. Use the ViewCube for a face, edge or corner view.
- Hide groups with their eye icons or use the category checkboxes in the sidebar.
- **See inside** fades obstructing vehicle surfaces. Turn it off to view the opaque body; windows remain transparent.
- Show **Wheel arches** independently of the rest of the vehicle.
- Filter **Cabinet shelves**, **Cabinet doors**, **Cabinet skin** and **Cabinet frames** independently.
  Hinges follow Doors. These switches act immediately without regeneration and retain their choices while Cabinet is hidden.
- Resize the sidebar by dragging its right edge. Collapse groups by clicking their headings.

The browser remembers the camera, visibility and sidebar choices. Use the viewer toolbar to reset or refit the camera.
The cabinet filters reuse native labelled checkboxes, Space-key activation and the existing mixed state when the two
modules differ, following the relevant [WAI checkbox guidance](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/).
This is a focused interaction choice, not a claim of full accessibility conformance.

### Included in build

The separate **Included in build** section below Visibility controls the **Rear drawer** and **Lagun table**.
Untick an item to omit it from cut lists and active BOM requirements. Choices save automatically, with an explicit
**Saving… / Saved** message. They do not require Apply or CAD regeneration. Tick an item to include its requirements again.
The design, hierarchy, dimensions, motion controls and product selections remain available throughout.
Excluded items are hidden immediately, without changing their saved eye settings. Re-including an item restores
its previous visibility, including any hidden subcomponents and table pose. Its eye buttons are disabled while
excluded. The Visibility checkboxes retain their saved choices as well. A failed save restores the prior inclusion.

The drawer option excludes its tray and sliders from manufacturing and purchasing. The stationary bench support
remains required because it also supports the bed. The table option excludes both tabletop leaves, its mounting
spacer, Lagun kit and hinges from manufacturing and purchasing; existing bench-frame requirements stay.
Saved purchases with ownership, bought quantities or recorded spending remain as **Unused stock**, with zero future
requirement. Notes and quantity overrides are retained even when their inactive row is hidden.
Any previous cutting layouts are used only if they still match the included parts; rearrange affected stock as needed.

These native labelled checkboxes sit outside the model-parameter form in a separate `fieldset` and `legend`, following W3C guidance on
[grouping controls](https://www.w3.org/WAI/tutorials/forms/grouping/). Static exports show the saved choices read only.

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
| Cabinet door sliders | Open individual doors; find them under Cabinet → Doors. The model hierarchy places each door in its Lower or Upper module. |
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

The cost summary shows project spending and the remaining estimate, with missing prices or quantities flagged.
Search or filter the shopping list by category, tag, supplier or status. Filtered costs appear above the table;
the project summary keeps its scope. Shared stock appears once across its uses.
Missing information has amber labels on the item and affected quantity/price fields. Click the summary's
**items need details** link or tick **Needs details** to show those items.

Required quantities include owned and bought materials. Current, complete saved cutting layouts supply sheet and
timber-stock counts. Existing unsourced bed slats use the number of modelled pieces; their owned count covers that
requirement. Incomplete or outdated layouts leave the stock requirement unknown.

Edit quantities, including Bought, and unit prices directly in the table. The **pencil** opens the item's name,
supplier, URL, category, tags, purchase unit, optional actual spending and notes. **Save** commits those detail fields
and closes the form. **Cancel** discards the detail edits and closes the form. Table quantity and price cells autosave
when you leave them. The Total price column emphasises the remaining cost, with the quantity below it.
Click a column heading to sort ascending, then click again to reverse it. Arrows show the sort direction;
unknown values stay at the bottom. **Total price** sorts by remaining cost. Filters and edits retain the selected sort.
The column and direction are saved in this browser across page reloads. Each embedded Plan purchase table remembers
its own sort separately from the Bill of materials.
Supplier names link directly to the product. The static site shows the same information read only.

Use **Model stock** at the top of the page to jump to specifications, availability, component uses and grouped cut
sizes. Expand individual stock entries for their details. **Cut list** opens the sheet layouts.
Material links in the CAD sidebar open and highlight the corresponding stock entry.
Selected material dimensions drive the model; measured overrides account for the stock purchased.

## Plan

Write multiline notes, nested numbered tasks, tables and linked purchases in the rich editor.
Use the toolbar, slash commands and contextual menu for actions and their shortcuts.
**Enter** continues text within a task; **Cmd/Ctrl+Shift+Enter** adds a task.
From an expanded item with subitems, the new task becomes its first subitem. Otherwise it follows at the same level.
Use **Actions → Add subitem / Add item at same level** to choose explicitly; **Shift+Tab** promotes an item one level.

See [planner and purchase details](planner.md) for editing, saving and recovery controls, and
[the cushion guide](squabs-guide.md) for the squab instructions.

## Cut list

**All pieces** shows named flat drawings grouped by assembly. Select a plywood thickness for sheet layouts, or select
timber and other sheet materials. Each sheet heading identifies the material, thickness, size and sheet number.
Single-click a piece for its details; double-click to show it in CAD.

**Cutting settings** applies to the whole project. Choose straight saw cuts or nested shapes, set kerf/tool width,
edge trim and grain direction. Set stock sizes, available offcuts and individual grain overrides under each material.
Custom stock needs confirmed dimensions before arranging it.

The application starts background layout searches automatically for every material with missing, outdated or incomplete
layouts, once the current CAD cut list is available. This runs on startup and after changes to the design, included
components, selected materials, stock sizes or cutting settings. Selecting a cut-list tab only chooses what to display.
Unsourced stock still needs its available dimensions confirmed before calculation can start.
Each search publishes improvements and saves the best layout; the BOM updates its quantities and costs as results arrive.
Each search pauses after at most 20 seconds of elapsed time. **Arrange sheets** (or **Arrange timber lengths**) resumes
that search for another 20 seconds. **Stop optimisation** pauses it early and keeps the best layout. Paused searches
use no CPU and retain their search state while the backend stays running. Automatic calculation keeps a current, complete
saved layout without restarting its search. Use Arrange to improve it further. Paused or failed searches do not restart
for unchanged inputs while the application stays running; Arrange resumes or restarts them.
Design or cutting-setting changes replace affected searches.

Straight-cut plywood candidates rank by sheet count, then the largest rectangular offcut's area/perimeter ratio,
then the number of blank-separating cuts. A proven minimum sheet count does not prove the best possible offcut or cut
count. The search uses lower CPU priority and alternates running and paused intervals.

Straight saw cuts produce rectangular blanks and an expandable cut sequence. Cut curves, notches, holes and finishing
features afterwards. Nested shapes use the sampled profiles; cut pieces inside holes before the surrounding frames.
Timber uses crosscuts in either mode. Hardware does not appear in the cutting list.

Use **Save drawing** for sheet SVGs, **Export cut list** for CSV and **Print** for the current view.

## AprilTags

Choose the complete printed tag width **including the white border**, quantity, starting ID, paper dimensions,
page margin and gap. The app calculates the rows, columns and pages automatically without scaling the tags.
The defaults produce forty unique 36h11 tags (IDs 1–40), 100 mm wide, four per A4 sheet across ten pages.
Each tag has a separate 6 mm ID label strip below its full white border; cut lines enclose both.

**Generate PDF** downloads a vector PDF. Print at **100% / actual size**, with any fit-to-page option disabled.
Measure a printed tag before using it. The form and page footer show the RTAB-Map `Marker/Length`: the black square
is 80% of the complete width, so a 100 mm print uses **0.08 m**. IDs are the actual dictionary IDs, not separate labels.
The thin grey centre circle and cross default to 10 mm diameter. Adjust the diameter or turn the mark off;
it overlays encoded cells and may affect detection. Tags are generated in OpenCV's orientation convention
(`MarkerAprilTag/Upright=0` in RTAB-Map versions exposing that setting).

This generator requires the local Python API and is excluded from static exports.

The form uses visible labels with explicit units, native number constraints and textual error/status feedback,
following W3C guidance on [labels](https://www.w3.org/WAI/tutorials/forms/labels/) and
[validation](https://www.w3.org/WAI/tutorials/forms/validation/). Tab navigation reuses the app's shared keyboard controls.
Patterns come from OpenCV's [predefined dictionary and marker generator](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html);
tag measurement follows the [AprilTag pose convention](https://github.com/AprilRobotics/apriltag#pose-estimation).

### Cabinet module joint

The replacement cabinet contains Lower module and Upper module. Each has Frames, Skin, Shelves and Doors.
Frames includes the side joining rails and module fasteners. Cabinet → Frames controls the 40 × 18mm pine section;
the wheel-arch bridge uses 90 × 18mm pine. The rear corner uses ordinary 40 × 18mm posts; the former wide return pieces and short rails are removed.
The rear end frame clears the pillar independently of the main back frame. Shelves and fixed middle/end skins extend past the timber
and are jigsaw-scribed to the actual van side and finished ceiling. The van side closes the open back.
Doors and shelves are 6mm plywood; fixed skins are 3mm birch.
Cabinet → Module joint sets the 20mm guide lip and 0.5mm fitting clearance. The split follows the middle shelf tops.

Eight estimated M5 × 90mm countersunk fixing sets join the side rails; there are no front or rear rail bolts.
Keep the interface unglued. Slide the upper module into alignment before fitting bolts. Hardware envelopes and
joint machining need confirmation before cutting. The earlier plywood-cabinet module notes describe the superseded
construction; use [the replacement construction rationale](research/cabinet-redesign.md) for this model.
