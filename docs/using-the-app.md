# Using the application

The project tabs share one saved project. Switching tabs keeps the camera and visibility settings.

The Scan tab remains removed; scan comparison is available in the CAD sidebar. Existing tabs retain their relative order,
following [W3C guidance on consistent navigation](https://www.w3.org/WAI/WCAG22/Understanding/consistent-navigation).
Saved scans and the scan-processing backend are retained.

## CAD

### Camera and visibility

The finished-floor elevation is shared by the benches, cabinet, table and stored gear. Their height controls are
relative to the finished floor; the van, scan and ceiling remain fixed. The current floor top is 20mm above the
registered Z0 datum. The cabinet roof profiles reference the registered van ceiling.

- Drag fixed parts or the background to orbit. Use the ViewCube for a face, edge or corner view.
- **Visibility** starts with six rows. Select a triangle to expand a group. Select its eye to hide or show it.
  A hidden parent dims its children's eyes. Each child keeps its setting. A slash means its own setting is off.
- Under **Camera**, **See inside** fades obstructing vehicle surfaces. Turn it off to view the opaque body; windows remain transparent.
- **Vehicle** controls the body, wheel arches and scan. **Wheel arches** and **Scan comparison** keep their own settings.
- **Bed/couch** controls both benches, their cushions and slats, and the mannequin.
- **Long bench** also controls the table's fixed mounting bracket and backing plate.
- **Table** hides or shows the table in either pose. Choose **Table position → Bench mount / Stowed** in the table
  settings to change its pose; changing pose does not override the Table visibility switch.
- Expand **Cabinet** to set **Shelves**, **Doors**, **Skin** and **Frames** across both cabinet modules.
  Hinges and folding stays follow Doors. These switches act immediately without regeneration and retain their choices while Cabinet is hidden.
- Pull **Box 5 flap** or **Box 7 flap** down to close it from any position, including fully open.
  You can also set its position with the flap slider. At 100% the flap sits slightly below horizontal.
  Hide **Cabinet → Skin** to see the wall-side view of the linkage.
- Resize the sidebar by dragging its right edge. Collapse groups by clicking their headings.

The browser remembers the camera, visibility and sidebar choices. Use the viewer toolbar to reset or refit the camera.

**Camera → Field of view** widens the perspective view without moving the camera. The slider controls the vertical
angle from 20° to 100°; 22° preserves the original CAD view, while 60° is a useful starting point inside the van.
The chosen angle is saved in this browser and reapplied after model reloads. It is retained when switching between
perspective and orthographic projection, but only changes the perspective view. Wider angles introduce stronger
perspective distortion; they are not a calibrated reproduction of human vision.

The control reuses a labelled native range input, keyboard interaction and a degree value, following
[WAI form labels](https://www.w3.org/WAI/tutorials/forms/labels/) and
[slider guidance](https://www.w3.org/WAI/ARIA/apg/patterns/slider/). This does not establish full accessibility compliance.

The triangle and eye have separate keyboard controls. Tab to either control and press Enter or Space.
Each eye has a fixed accessible name and reports its saved state. [W3C disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/), [W3C toggle button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/).

### Scan comparison

Select a registered reconstruction in **Scan comparison**, then use **Show scan reference**.
**Scan opacity** controls the reference mesh; **Vehicle opacity** controls the light-pink vehicle CAD.
Vehicle opacity sets the base transparency. **See inside** continues to fade nearby vehicle surfaces and their edges
as you orbit, including click-through picking of faded panels. Furniture colours and visibility switches are unchanged.
It also hides the backs of scan triangles, opening the near-side scan shell while retaining inward-facing surfaces.
Turn **See inside** off to display both sides of the scan again. Scan opacity applies in either mode.
Hiding the reference restores normal vehicle colours and opacity while preserving the See inside setting.
Wheel arches participate in the comparison opacity too. No progress outlines or experimental floor lines are shown.

The selected result and both opacity settings are remembered in this browser.
**Refresh references** reloads the list. The scan uses its saved CAD registration directly.
These controls do not change the scan, vehicle dimensions, pillar angles or manufacturing geometry.
The scan remains outside CAD picking and furniture mirroring.

Controls have visible native labels, following [WAI labelling guidance](https://www.w3.org/WAI/tutorials/forms/labels/).
The legend identifies the pink surfaces as vehicle CAD and the visibility toggle allows checking each model alone,
following [WAI guidance on use of colour](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).
These are focused design decisions, not a claim of full accessibility compliance.

### Cross sections

Under **Scan comparison → Cross sections**, **XZ · transverse** moves along Y from rear to front;
**YZ · longitudinal** moves along X from left to right; **XY · horizontal** moves along Z from bottom to top.
All three can be visible together. Each number field sets an
exact position in millimetres; each slider's arrow keys move it by 1mm. The green line
is the raw mesh intersection, with scan gaps and fragments retained. It remains available when the scan mesh is hidden.
The YZ control uses X=0 at the vehicle centreline, negative on the left and positive on the right. Its range is fixed
at −800 to +800mm, and it initially opens at 0. Scan bounds do not change this range.
The YZ green control shows both +X and −X sections together, each cut independently from the scan so real left/right
differences remain visible. The shared green opacity slider controls both. At X=0 there is only one centreline section.

Ask the assistant to create a blue draft at the chosen position. Blue is an authored interpretation based on the scan,
vehicle construction, measurements and your estimates. There is no point averaging or automatic blue generation.
Refine it through conversation, then press **Record** beside Blue sections when satisfied.
The button appears only when a draft is selected. Choose the next position yourself;
moving the green section does not change any blue geometry.

**Blue sections** returns to an authored station. The active outline is thicker and prominent; other outlines remain
faint. The single **Section opacity** group controls green raw lines and blue authored lines across all planes: 0% hides
that colour. Position and opacity choices survive a
reload. Authored outlines and recorded sections are retained in `data/cross-sections.json`; back it up with your
project data. Revising a recorded outline creates a new draft and keeps the original.

Opposite-side YZ profiles normally share the same rear-door shape. An authored YZ pair appears at matching distances
from the centreline; choosing either station makes that side prominent. Explicitly authored differences can retain
larger driver-side seatbelt trim or other local asymmetry. **Record pair** records both stations together. Longitudinal profiles are never mirrored front-to-back.

The compact layout retains native labelled sliders and numeric fields. Names identify the plane/axis and slider
value text includes millimetres, following [WAI labels](https://www.w3.org/WAI/tutorials/forms/labels/) and
[slider guidance](https://www.w3.org/WAI/ARIA/apg/patterns/slider/). Shared opacity labels include both colour and
meaning. These choices do not establish full accessibility compliance.

### Included in build

The separate **Included in build** section below Visibility controls the **Lagun table**.
Untick an item to omit it from cut lists and active BOM requirements. Choices save automatically, with an explicit
**Saving… / Saved** message. They do not require Apply or CAD regeneration. Tick an item to include its requirements again.
The design, hierarchy, dimensions, motion controls and product selections remain available throughout.
Excluded items are hidden immediately, without changing their saved eye settings. Re-including an item restores
its previous visibility, including any hidden subcomponents and table pose. Its eye buttons are disabled while
excluded. A failed save restores the prior inclusion.

The table option excludes both tabletop leaves, Lagun kit and hinges from manufacturing
and purchasing. The storage box remains required. The old rear drawer and its purchasing option have been removed.
Saved purchases with ownership, bought quantities or recorded spending remain as **Unused stock**, with zero future
requirement. Notes and quantity overrides are retained even when their inactive row is hidden.
Any previous cutting layouts are used only if they still match the included parts; rearrange affected stock as needed.

These native labelled checkboxes sit outside the model-parameter form in a separate `fieldset` and `legend`, following W3C guidance on
[grouping controls](https://www.w3.org/WAI/tutorials/forms/grouping/). Static exports show the saved choices read only.

### Dimensions and moving parts

Change dimensions in the sidebar and apply them. The app reports invalid values and explains dependent limits.
**Regenerate** forces a fresh geometry build. Matching saved geometry loads without rebuilding.
If the saved geometry is stale, the app shows it and starts an update automatically.
The status reads **Regenerating… · Previous model** until the new geometry is ready.
The status message leaves keyboard focus in place. [W3C guidance on status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)

Live sliders and direct dragging operate the sliding bed, storage lid, individual cabinet doors and mounted table.
Movable parts show a hint under the pointer. They glow cyan during a drag. Motion follows the joint limits; there is no collision detection.

| Control | Behaviour |
| --- | --- |
| Long bench conversion | Extends the moving slats and legs, moves the blue seat sideways, then lowers the orange backrest alongside it. Reverse to undo the sequence. |
| Open storage lid | Retracts the slats and lifts the whole lid up to 75 degrees. Extending the bed closes it. |
| Doors closed | Closes both sliding doors and lowers the rear hatch. At 0%, the hatch is raised 90°; at 100%, all doors are closed. |
| Cabinet door sliders | Open individual doors; find them under Cabinet → Doors. The model hierarchy places each door in its Lower or Upper module. |
| Unfold tabletop | Top-level slider: 0% folded, 100% flat. |
| Laptop table | Adjust mounting/stowed pose, height, arm swivel, tabletop rotation and offset. |

When dragging the bed, continue pulling after the frame stops to reposition the cushions. Reverse to put the cushions
back before retracting the frame. Release pauses and saves the pose. **Escape** restores the drag's starting pose.
Dragging near the tabletop centre keeps its heading; dragging near an edge steers both swivel joints.
Extending the bed stows a mounted table; retracting the bed restores it when the bed caused the stow.

Use **Alt-drag** to orbit over draggable objects. Rotate the camera if a part's allowed motion is edge-on.

The **Paint bucket** sits to the right of the person icon. Click it or press **B** in the CAD view.
Click the adjacent swatch to open the colour picker. Choose **RGB** or **HSV**.
In **Choose paint**, click the pipette beside the colour preview. Click a surface in the model.
The picker returns to the same tab with the surface colour, texture and opacity. Press **Esc** during sampling to cancel.
On the raw scan, the pipette takes the colour at the clicked point.
Select a letter under **Slider channel** to choose the vertical slider. The arrows above the square identify its two axes.
RGB starts with red on the slider, blue across the square and green up the square.
HSV starts with hue on the slider, saturation across the square and value up the square.
Each channel also has a horizontal slider and a numeric field. Both tabs accept a **Hex code** beside the colour preview.
Use the checkerboard slider to adjust opacity. Use **Tab** to reach each control. Use the arrow keys to adjust a slider.
Choose a surface finish from **Textures**.
Pine timber and bed slats show wood grain by default. Choose **Dressed pine** for the grain and its natural pine colour.
To tint the pine, choose a colour in **RGB** or **HSV** after you select the texture.
**Favourites** stores swatches for later. **Currently used** shows finishes on the visible, paintable parts.
Hover over a part to see a light cyan tint on the exposed surfaces of its paint group.
A thin outline shows the group edges through other parts.
Click to apply the swatch to the group. Press **Esc** to put the bucket away.
Use **Undo paint** beside the swatch or press **⌘Z** on Mac (**Ctrl+Z** elsewhere).
Use **Redo paint** or press **⇧⌘Z** (**Ctrl+Shift+Z** elsewhere) to reapply it.
Each paint change on a group counts as one step. The project saves each step with the new finish.
A new paint change clears redo. Existing finishes in an older project form the starting point.
Skins, shelves, slats, cabinet frames, doors and bench frames each share a finish.
The door finish covers the plywood flaps and fixed fronts. Hinges, stays, chains, catches and their fasteners keep their metal finish.
Click the long seat, wall backrest, or cross seat to paint all three cushions in one step.
To paint a photographed trim panel, show the colour scan and click the panel with the paint bucket.
Each of the five panels has its own finish. Undo the first paint change on a panel to see its original scan colour.
With the colour scan visible, click the timber ceiling to apply one colour or texture across its curved surface.
Undo the first ceiling paint change to restore its timber colour.
Paint choices and favourite swatches are saved with the project.

The toolbar's person icon enables **Human view** (**H**, also in the right-click menu). It switches to perspective,
preserving your position and field of view. It captures and hides the pointer; move the mouse to look around without
holding a button or reaching a window edge.
**Up/Down** moves forward/back along your view's horizontal heading, keeping the current height even when looking
up or down; **Left/Right** moves sideways relative to your view.
**Shift+Up/Down** moves vertically along world Z. Hold an arrow for continuous movement. **Escape** or the person icon
leaves Human view and releases the pointer. Losing viewport focus also exits, so fields and menus retain their normal keys.
Leaving Human view keeps your current position, viewing direction and perspective. The orbit pivot is set on the
point ahead of you, without moving the camera. This view is saved across reloads; Human view itself starts off.

Use the toolbar's icon-only **Reset view** button, the right-click menu, or **R** with the viewport focused.
Reset centres the rotation pivot on the van and fits it to the viewport, preserving viewing direction.

### Mannequins and gear

Expand **Mannequin** to adjust seated and lying poses. The eye under **Bed/couch → Mannequin** controls all three poses.
Each pose also has its own eye. The lying mannequins follow the bed conversion. Pose, body shape and foam compression
are visual fit references.

The local app saves all three poses and their visibility choices in `data/project.json` without regenerating CAD.
Static exports include that configuration. Visitors can adjust the mannequins in their browser; a newly published
configuration replaces the previous export's starting poses.

**Stored gear** contains the folded chairs, solar bag and chilly bin. Use their group eyes and live controls to explore
positions. Reference geometry and hardware envelopes still need comparison with the physical van and equipment.

### Finding a piece

Double-click wood in CAD to find it in the cut list. Double-click a cutting piece to frame it in CAD.
Modified double-clicks do not hide or isolate parts; use the sidebar visibility controls to show or hide geometry.
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

### Template-fitting allowance

Plywood and timber edges fitted against the van's sidewalls or ceiling start with **50mm extra on those edges**.
Floor contact does not add an allowance. Furniture joints, slots, rebates and rounded corners do not qualify by shape.
The registered scan is sampled within a 10mm contact band, including the deliberate 3–5mm design clearances and
rounded cutting envelopes. Cuts use the fixed construction pose, independent of the current door or bed animation.
A vehicle-fitting notch inside the stock envelope keeps a rectangular template blank without enlarging unrelated edges.
The CAD model itself stays unchanged.
In **Cutting settings**, change the shared template-fitting allowance if needed. Select a piece to adjust its four
edge allowances or restore its defaults. Explicit per-piece values, including zero, override automatic defaults.
The details preview is deliberately unmirrored and labels the drawing edges; roof/wall names identify known fitting edges.
Timber uses the same labelled allowance fields. If a side allowance exceeds its stock width, choose wider stock;
the optimiser reports the required width rather than discarding the allowance. The existing labelled fields and
fieldset grouping follow [W3C's labels and instructions guidance](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html).

**Cut blank** is the rough rectangle to cut from the sheet. **CAD reference** is the modelled size, not a surveyed
final fitting contour. Solid blank outlines and dashed CAD profiles distinguish them, with hatching for retained
stock and blue marks on unchanged datum edges. Leave irregular vehicle contours/notches uncut until templated.
The optimiser reserves the complete larger blank in both modes, so nested pieces cannot consume fitting stock.
Changing an allowance makes previous layouts stale and updates the rough dimensions in the cut list and exports.

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

Straight-cut plywood candidates rank by sheet count, then a middle-third handling crosscut on each full sheet,
then smaller occupied crosscut sections, then largest rectangular offcut area. The search includes crosscut-first
bands: break the sheet into sections, rip those into parts, then make any final trims. Empty waste strips do not
earn a handling reward. Offcut shape and the number of blank-separating cuts break later ties.
A proven minimum sheet count does not prove the best possible offcut or cut
count. The search uses lower CPU priority and alternates running and paused intervals.

Numbered dashed saw-cut lines with solid numbered badges are visible on sheet drawings and saved drawings; their
numbers match the expandable cut sequence. Teal lines create fresh reference edges; red lines separate blanks or
trim opposite edges. With a nonzero edge-trim allowance, straight sheet layouts include the initial short-end trim,
parallel full-width breakdown cuts, then each occupied section's perpendicular reference cut and remaining cuts
before proceeding to the next section. Opposite-edge trims are included only where a blank reaches that edge.
Reference cuts discard material towards the outer stock edge. These operations use the reserved edge trim without
changing the packing. Zero trim reserves no fresh reference cuts. Straight saw cuts produce rectangular blanks.
Cut curves, notches, holes and finishing features afterwards. Nested shapes use the sampled profiles; cut pieces
inside holes before the surrounding frames.
Timber uses crosscuts in either mode. Its cut-number badges sit above the timber with leader lines, staggered
where cuts are close together; saved SVGs include the same spacing. Hardware does not appear in the cutting list.
This preserves visible cut locations and part outlines, following the distinguishable-graphics guidance in
[WCAG 2.2 SC 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
(consulted 22 November 2026); this is a layout decision, not a claim of overall accessibility compliance.

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

The removable upper cabinet sits directly on the lower cabinet's rear, middle and cab-end cross rails.
Slide the upper cabinet into position, clamp the matching rails together and match-drill two vertical
6.5mm holes per pair. Fit six M6 × 90mm bolts from underneath, with a 16mm washer under each head and nut.
Keep the mating faces unglued. The fasteners appear under Lower module → Frames → Module fasteners.
The drilling positions are in the [CAD model notes](cad-model.md).


## Hinged storage bed

The long bench is one bottomless plywood box with a centre divider and a 600mm-wide slotted lifting lid.
The stationary wall-side strip is removed. Seven 50mm-wide ventilation slots have a 100mm wall band and an 82mm aisle band;
**Long bench → Hinged lid → Slotted plywood lid → Solid end band width** adjusts both bands.
The rear end panel and its lift are set forward beneath a complete solid lid rib to clear the modelled rear pillar.

**Open storage lid (%)** moves a photo-derived pair of Instant Panel gas-assisted four-bar linkages. The lid
translates towards the aisle while opening approximately 34 degrees. Both arms, mounting rails and telescoping
springs follow the same fitted geometry. Missing pivot and mounting dimensions are inferred from the product
photograph; this is not a drilling template or a verified load rating.

Both slat sets extend across the former hinge strip. Fixed slats are 567mm long; moving slats are 559mm long,
ending against the support frame. The frame is full bench length, with a smooth 50mm rise above the slat undersides.
Eight inside-face grooves, 84 × 22mm and 8mm deep, accept the fixed slat ends with 2mm side/vertical clearance.
The continuous 10mm outer face hides the grooves; their ceilings retain the retracted sliding frame during lifting.
An 18 × 50mm rail on the lid's wall-side edge provides a cushion stop when lifting. Its top matches
the sliding frame, and both slat sets are shortened 18mm at that end to leave room for it and the existing 5mm gap.
The lid's aisle edge is recessed 18mm throughout. The hinges' upper rails are shortened 18mm at the gas-spring end,
preserving all pivot positions. The moving support is one 18mm plywood frame with a 50mm lower top member and integral
60mm-wide legs at both ends, using the same rounded cutout as the cross-bench frames. It reaches the floor and
supports the slats directly, without spacer blocks, metal legs or hinge notches.
The blue cushion fits between the side rails and rides the lid during storage opening. Orange stays upright
and rises enough to clear it; both allow at most 3mm of visual compression during opening. Each pose updates
directly, without gravity, sliding, bouncing or settling. The existing seated-mannequin indentation is retained.
The rear black pillow rides with blue, flattening slightly against orange when needed.
Cutting dimensions and manual bed conversion are unchanged. The mannequin
preview is hidden while storage is open and returns to its saved visibility preference on closing.
Each moving slat has a metal angle fastening it to the support frame. Small aisle-edge lid recesses clear the
angles as the bed slides in: 3mm-deep top rebates retain 15mm of plywood, with 1mm clearance around the steel.
Only a narrow 3mm edge relief goes through the lid for the vertical flange. The BOM uses the existing Carinya
50 × 50 × 40 × 2mm eight-pack.
Opening storage retracts the bed; extending it closes the lid and stows the table. Opening storage does not
independently stow the table. See [working dimensions and limits](research/bed-lift-photo-model.md).

The **Long bench → Bed inward offset** dimension moves the complete bed towards the aisle. The accepted 24mm
middle-pillar offset now applies to both benches, all slats and cushions, the moving support and legs, the hinge
preview and the table's mounted bracket/working pose. The sleeping width stays 1070mm; extension travel is 448mm.
The separately positioned stowed table does not move. The earlier box-only setting is preserved as this shared offset.
The cabinet front now follows the bed offset, reducing its depth by 24mm at the accepted setting. Wheel-arch fitting remains separate.
