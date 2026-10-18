# CAD model conventions

Use millimetres, with X running from the vehicle's left/passenger side to its right/driver side, Y from the rear doors
toward the cab, and Z upwards. The rear opening at its side pillars is Y = 0; its centre bows rearward to Y = −120 at bed height.
Z = 0 is the finished plywood floor, with the vehicle floor approximately 18mm below. Vehicle coordinates and the right-hand-drive cab stay fixed.

`src/campervan/cad/model.py` assembles the campervan. Component generators retain the original FeatureScript-oriented
construction coordinates. At the assembly boundary, `mirror.py` reflects every furniture leaf and local placement,
then `model.py` places the furniture using `x_world = cargo_width - x_local` and
`y_world = y_local + furniture_rear_gap_mm`. The cabinet is on the left, the long bench on the right, and all cross-bench,
drawer, bracket and cushion geometry is mirrored with them. The shared rear setback defaults to 100mm from the opening at the pillars. The closed hatch has 130mm
centreline clearance behind that bed edge.

The reflection preserves native named assemblies, colours and visibility paths. Local translations reflect in X;
rotations retain their X angle and reverse their Y/Z angles. `viewer.py` applies the same conversion to every live
motion track, including absolute cushion keyframes, so live poses and regenerated CAD agree. This is native CAD
geometry, not a display-only reflection. The coordinate examples in the furniture construction sections below refer
to the generators' original local coordinates, before this shared reflection and placement.

The bench converts wheel-arch and rear-corner positions to furniture-local coordinates before constructing supports.
The cabinet translates body/ceiling fitting volumes and wheel-arch cutouts into that coordinate system before scribing.
The body fitting envelope and wheel houses are symmetric at the defaults; keep checking fit if vehicle measurements
introduce side-to-side differences. A perfect furniture reflection does not imply an asymmetric vehicle is mirrored.
`src/campervan/parameters.py` owns dimensions, constraints and sidebar metadata. Geometry code does not call the API
or viewer.

Use native `Compound(label=..., children=...)` assemblies. Keep each physical part separate and use named subassemblies
for parts that belong or move together. Build reusable parts at a local origin and place them using `Location`.
Keep labels consistent across regeneration. Add modules and groups as actual components arrive; do not prebuild a
component framework or a second scene graph.
Do not put `/` in assembly or part labels: OCP uses it to separate object-path levels, including visibility lookups.

Parameter metadata uses a `group` array containing the assembly path, such as
`["Long bench", "Sliding bed", "Sliding assembly", "Angle brackets"]`. The sidebar nests collapsible sections along
these paths in model-tree order for dimensional parameters. Live position controls sit above all groups and act without
regeneration. Shared dimensions sit at the common assembly level; parts without independent controls
do not need empty sidebar sections. Each section saves its collapsed state in browser localStorage using its full path.

The assembly is:

```text
Campervan
├── Vehicle references
│   ├── Floor outline
│   ├── Wheel arches
│   │   ├── Left wheel arch
│   │   └── Right wheel arch
│   ├── Rear corners
│   │   ├── Left rear corner
│   │   └── Right rear corner
│   ├── Side walls
│   │   ├── Left wall
│   │   └── Right wall
│   ├── Roof
│   │   ├── Bare roof
│   │   ├── Roof bows
│   │   │   ├── Rear bow
│   │   │   ├── Middle bow
│   │   │   └── Front bow
│   │   └── Finished ceiling
│   ├── Rear opening
│   │   ├── Hatch surround
│   │   └── Clear opening
│   ├── Body floor
│   └── Cab
│       ├── Floor
│       ├── Seats
│       │   ├── Driver seat
│       │   └── Passenger seat
│       └── Headliner
├── Long bench
│   ├── Fixed frame
│   │   ├── Wall-side frame
│   │   ├── Aisle frame
│   │   ├── Cab-end frame
│   │   ├── Cab-end skin
│   │   ├── Internal drawer-support frame
│   │   ├── Rear header
│   │   ├── Fixed slats
│   │   └── Guide ledges
│   ├── Sliding bed
│   │   └── Sliding assembly
│   │       ├── Moving slats
│   │       ├── Moving aisle frame
│   │       ├── Tie strip (extension stop)
│   │       └── Angle brackets
│   ├── Rear drawer
│   │   ├── Tray (five plywood panels)
│   │   └── Rails
│   │       ├── Fixed (left and right)
│   │       ├── Intermediate (left and right)
│   │       └── Moving (left and right)
│   └── Cushions
│       ├── Long seat
│       ├── Wall backrest
│       └── Rear end backrest
├── Cross bench
│   ├── Fixed frame
│   │   ├── Wall-side frame
│   │   ├── Rear frame
│   │   ├── Rear skin
│   │   ├── Cab-end frame
│   │   ├── Cab-end skin
│   │   ├── Fixed bearer
│   │   ├── Toilet-storage divider
│   │   │   ├── Frame
│   │   │   └── Separating panel
│   │   ├── Fixed deck
│   │   └── Fixed slats
│   ├── Sliding assembly
│   │   ├── Moving slats
│   │   ├── Bearer
│   │   ├── Legs (rear and cab-end)
│   │   ├── Angle brackets
│   │   └── Extension stops (rear and cab-end plates)
│   ├── Storage lid
│   │   ├── Plywood lid
│   │   └── Lid slats (three separate parts)
│   └── Cushions
│       ├── Cross seat
│       ├── Wall backrest
│       └── Cab-facing backrest
└── Cabinet
    ├── Aisle frame
    ├── Rear frame
    ├── Rear skin
    ├── Middle frame
    ├── Cab-end frame
    ├── Cab-end skin
    ├── Shelf ledges
    └── Shelves
```

The [Japanese 2017 NV200 body research](research/nv200/README.md) records the actual van variant, Nissan dimensions,
source limitations and a measurement plan. `body.py` builds an adjustable interior envelope using native edges, faces
and lofted shells. These are reference surfaces without invented material thickness, not fabrication-ready bodywork.

`cab.py` extends the floor forward from `body_length_mm`, retaining a common finished-floor datum. Its headliner
starts at the cargo plywood's front edge (Y = 1660), then widens into rounded side returns over the cab. The centre
stays level unless a front drop is configured. Seat cushions retain the older Japanese 475 × 455mm reference sizes.
Continuous highbacks have integrated headrests and rounded shoulders, matching Gert's photos. The approximate
175mm pivot offsets and 10.437° reclines place the rear surface near Y = 1990 at Z = 490 and Y = 1920 at Z = 870.
The measured headrest base is Z = 870. These are approximate upholstered shapes, with separate driver/passenger controls.
No dashboard, steering wheel or seat mechanisms are modelled.

The vehicle uses [Gert's measurements and photographs](research/nv200/measurements.md). Remaining inferred values
are identified in sidebar tooltips. In particular, rear seal elevation and upper forward rake remain estimates.

- Main panel width is 1500 at mattress height. Rear sliding-door pillars intrude approximately 40 per side, following
  the wall taper and S-shaped opening. Their fore–aft width is 180 at that height, measured from the opening to
  the rear side panel. Their shapes, roof side rails and rear corners also constrain cabinet fitting.
  The lower rear-pillar return is trimmed against the same positioned wheel-house solid used for display, so
  it meets the rounded arch without overlapping it. `body.wheel_arch` owns that shared envelope.
  Front pillars behind the cab doors are solid profiles with the same wall taper and rounded opening returns.
  Their inward depth is separately adjustable (40mm estimate); their fore–aft width follows each opening's cab-end setback.
- Rear corners have a 60mm straight section followed by an angled transition ending at Y = 200. The original
  `rear_corner_radius_mm` identifier is retained for saved parameters, but its control is **Corner transition depth**.
  This implemented extent still needs reconciling with the owner's clarification of 60 straight plus 200 flared;
  see the [dimension audit](research/nv200/dimension-audit.md) for the distinct rear-door/opening references.
- Rear aperture widths are 1250 at floor, 1265 at Z = 390 and 1115 at 60 below its 1280 centre height. Its outline is
  non-planar, bowing aft by 120 at the centre near bed height and leaning forward at the roof (80mm estimate).
  The closed hatch inner surface is a separate approximate reference, constrained to Y = −30 at the centre at
  the measured 390mm slat height: 130mm behind the existing bed's rear edge at Y = 100. This is the inside panel,
  not the outer door skin; its remaining curvature is approximate.
- Sliding openings are 680 wide low down (rubber seals at Y = 1210 and 1890) and an estimated 760 above the smooth
  rear-pillar transition at Z = 630–770. Of the original 80mm rearward change, an estimated 20mm is distributed
  along the upper edge toward the roof, matching the owner's interior photo. The lower curve joins that inclined
  edge tangentially rather than forming a sharp S-step. The pillar is 180 wide below, 120 just above the lower
  curve, and 100 below the rounded roof return. Their tops
  are at 1170 above finished floor; lower sill offset is provisionally zero. Fore edges are independently adjustable.
  Open-door envelopes leave 680 to the front pillars and sit approximately 60 outside the body, with 100 depth.
  Their outer faces use the same wall-profile curves as the body in the closed position. The complete curved
  envelopes fit the aperture outline and retain the body taper throughout their travel. The shared door-closing
  slider moves both forward over 0–85%, then inward with the last 30mm of forward travel over 85–100%.
  CAD placement and viewer keyframes share `sliding_door_offset`; the controls need no regeneration.
  These remain approximate clearance envelopes, without detailed rollers, tracks, seals or door construction.
- The 12mm fitted plywood floor occupies Z = −12 to 0; the vehicle floor reference is at −18. The remaining build-up
  is not assigned an invented material. The floor has a straight rear edge at Y = 0 and cutouts following both
  wheel-arch base footprints. Its rear corners follow the pillars' straight sections and angled transitions.
  The rear-door opening's centre bow does not change the plywood outline.
- The 3mm ceiling sheet spans Y = 240–1660. Its underside is 1290 at centre and 1270 at its wall-side edges.
  Exposed side rails, rear header and three approximate bows are separate parts. The ceiling still uses concentric
  circular profiles for real sheet thickness. The bare roof estimate is 1347 above finished floor, with 55 crown.
- Wheel arches remain approximate rounded 760 × 140 × 280 envelopes. Wall-side endpoints are at Y = 310–1070,
  from direct measurements parallel to the centreline from the closed rear door beside the pillar. With the lower
  sliding opening at 1210, this leaves approximately 140mm ahead of the arch. The shorter 700–720 inner-side length
  is recorded but not separately shaped; the full footprint is a conservative clearance envelope. The exact
  profile and insulated height remain unmeasured. Floor and furniture cutouts follow the shared arch parameters.

The direct arch and rubber-seal measurements confirm the 140mm front arch gap. Relative to the lower opening,
the arch rear is 900mm aft and its front is 140mm aft. The closed-door reference and rear-opening datum remain
distinct; their offset and the rear pillar's local straight/flare segments still need reconciling. See the
[dimension audit](research/nv200/dimension-audit.md).

Walls, pillars, roof and floors remain translucent, with named assembly groups and visibility controls.
Measurements describe the existing bed at 390 slat-top height; the design's platform height remains independently
editable and is not automatically changed to match it.

`bench.py` ports the long-bench branch of `benchCarcass`, `wheelArchFrame`, `slideMountFrame` and `drawerRearFrame`.
The internal mounting frame and its raised rear post belong to the bed's Fixed frame. `panels.py` builds local panels and
rounded opening cutters; X runs along each panel, Y through its thickness and Z upwards. Assembly placement uses
`Location`, keeping each cut plywood piece a separate solid.

The long bench has a 600 × 1280 footprint. Its frame top is `platform height - slat thickness`, or 382 at the defaults.
The aisle frame retains its 100-high slide mounting band. Wall-side openings reach the floor and clear the wheel arch;
the rear support starts at bed-local Y = 35 (vehicle Y = 120), with a 36 rear arch gap. The cab end has separate 18-thick frame and 4-thick skin.
The internal support sits at X = 150–168 and reaches the rear header with an integral raised post. The header spans
X = 168–582, bed-local Y = 0–18, Z = 322–382, leaving the drawer exit open.
At the bench junction, the long bench's cab-end frame/skin and the cross bench's rear frame/skin start at that same
wall-side face, X = 150, instead of X = 25. This cuts each pair back by 125mm, opening the low storage channel beside
the drawer into the cross-bench storage area. The rounded frame openings are rebuilt at the shorter width.
`drawer.drawer_support_x` shares this alignment with the drawer placement; it follows wheel-arch width and drawer
clearance. The cross bench's far cab-end frame/skin, deck and lid retain their wall-side extent.

`sliding_bed.py` ports `longSlatDimensions`, the long-bench branch of `slidingSlatAssembly`, `slidingBracketDimensions`,
`slideAngleBracket` and `slidingBenchBrackets`. Eight fixed and seven moving slats alternate on an 85 pitch. Ordinary
slats are 611 long; the rear fixed slat is 468 long to clear the rear corner and bear on the internal drawer support.
The slat top is 400. The 40 × 18 tie strip sits at X = 90–130, bed-local Y = 62–1253, Z = 364–382 when retracted, supported on
two fixed 25-wide ledges. The rear ledge clears both the body corner and the raised drawer-support post.
Both ledges extend down to the adjoining frame top rails' underside:
`frame top - member width`, or Z = 322. Their tops stay at Z = 364, giving a 42 vertical depth at the defaults.
These deepened ledges supersede the original flat 18-thick Onshape strips.
Fixed slats and guide ledges belong to Fixed frame, so its visibility toggle includes both.
The moving aisle frame has a continuous bottom rail matching the fixed aisle frame's slide mounting band
(100mm at defaults), with the same rounded openings.
Slat thickness and stock width are shared by both benches and sit at the Long bench parameter level.
The slats are reused 80mm stock: preserve their width instead of narrowing them to fit. The slat-gap parameter controls
the long bench; cross-bench spacing is derived from its depth and the full stock width.
Three provisional 50 × 50 × 40 × 2 steel angles have a 3 inside bend radius and sit at
Y = 130, 640 and 1150. The fixed aisle frame has 42-wide reliefs: a 6-deep top notch and a face pocket 6 deep and 51 high.
Screw holes and actual installed hardware dimensions are not modelled.

`BedLayout` holds the derived spacing and travel shared by construction and relief cuts. `bed_extension_percent` moves
the entire `Sliding assembly` with one parent `Location`: 0 is retracted and 40 extends by
`bed width - long bench width - frame thickness` (452 at defaults). Full extension reaches X = 1070, retains 159 slat
overlap, and brings the tie strip against the fixed aisle frame at X = 582. Child locations stay relative to the moving
group; use `global_location` when checking individual children in world coordinates.
`bed_motion.py` supplies the shared stages and frame offsets for CAD and viewer keyframes: the frames extend over
0–40%, cushions reposition over 40–80%, and backrests lower over 80–100%. Frames stay extended through both cushion stages.

`drawer.py` adds the five-part 12mm plywood tray: 376 × 1250 × 290mm, X = 187–563, Y = 0–1250, Z = 10–300.
Its bottom fits inside the walls, flush underneath. The open sides retain a 90mm lower band and 60mm end uprights.
The rear face is flush with Y = 0. The tray travels 1215mm toward negative Y. Each 19mm rail gap contains three
simplified 1200 × 53mm envelopes; intermediate stages move half the tray distance. Rear drawer contains the tray and
rails. Its stationary internal support belongs to the bed's Fixed frame alongside the aisle frame and rear header,
so hiding or omitting the drawer leaves the bed supports in place.

`cross_bench.py` ports the cross-bench branch of `benchCarcass`, `crossBenchPartition` and the fixed deck from
`crossBenchSlats`. Width is `(bed width + long bench width) / 2`; depth is `cargo length - seat length`.
The 835 × 580 baseline sits at Y = 1280–1860. The frame top is Z = 370, with a 12mm deck up to Z = 382.
Frame thickness, skin thickness, member width and opening radius use the same parameters as the long bench.
There is no fixed aisle frame across the toilet exit. Both ends have separate solid skins; the wall-side frame has no
skin. The end frames, skins and fixed deck finish at X = 791, leaving a 2mm nesting gap beside the retracted legs/bearer.
A 60 × 566 × 18mm fixed plywood support rail runs along that deck edge, parallel to the moving bearer. It sits in shallow rebates
in the two end frames, between the end skins, with its top flush against the deck underside at Z = 370.
Its underside at Z = 352 limits toilet extraction height before allowing for a tray and running clearance.
Both end frames have continuous bottom rails for future drawer slides, using the long bench's
`drawer_mount_band_mm` setting (100mm high at defaults). Their openings retain the shared rounded corners.

The 440mm toilet bay preserves the old assumed 420mm footprint plus 20mm allowance as one clear-bay parameter.
It places the divider frame at X = 352–370 and its separating skin at X = 370–377. The frame keeps a bottom rail
around its 446 × 250, R25 opening. Both layers have 18 × 60 top-corner recesses around the end beams and
18 × 100 bottom-corner notches around the drawer-slide mounting rails; notch heights follow their respective rails.
The fixed deck starts at X = 362, reserving half the 2mm storage-lid seam over the divider frame.
`cross_bed.py` builds three fixed slats and four moving slats. A flat 60 × 580 × 18mm plywood support rail joins the moving slats,
supported by two separate 60 × 18mm legs whose broad faces run across the van. The legs occupy only 18mm each along
the toilet opening, leaving 544mm between them. Their tops meet the bearer underside at Z = 364. Two angle brackets
face inward along the van, rotated ±90° from the long-bed brackets, and join the legs to the bearer underside.
There is no middle bracket. The brackets project 2mm into the opening near its top on each side.
Both support rails are cut from the frame plywood stock. Thickness (`cross_bearer_height_mm`) is shared
by the fixed and moving rails; nesting gap
(`cross_leg_clearance_mm`) has its own control;
leg width/thickness reuse member width/frame thickness. Bed height remains the shared platform-height parameter.
The toilet, its tray and fasteners remain unmodelled; this opening does not establish toilet fit or structural capacity.
Both end slats move, continuing the alternating pattern across the junction with the long bench. The cross bench fits
the largest odd number of full-width slats that leaves positive gaps, distributed evenly with no end margins.
At the baseline, seven 80mm slats leave six gaps of 3⅓mm across the 580mm depth. The extended junction gap is 90mm.
This supersedes the Onshape arrangement with fixed, narrowed end slats. Moving slats are 376mm long and travel 217mm,
retaining 159mm overlap at full
extension. The shortened deck clears the moving supports without bracket relief pockets. Both beds use `bed_extension_percent`, so
one slider extends the long bed by 452mm and the cross bed by 217mm at the defaults, ending together at X = 1070.

The 358 × 576 × 12 plywood storage lid carries three wall-side slat sections aligned with the fixed toilet-side rows.
These strips retain their full 80mm width. The 25mm finger hole sits in a gap between them.
Its group origin is the cab-side hinge at Y = 1858, Z = 400. Children use coordinates relative to that hinge.
`cross_lid_open_percent` rotates the group from 0 to −70 degrees about X, lifting the rear edge toward the cab.
The lid moves independently of the beds and drawer. Hinge hardware and toilet hardware are not modelled.

`cabinet.py` adapts the right-hand branch of `benchCarcass` and `wheelArchFrame` to the body envelope. Its nominal
footprint is X = 1070–1500, Y = 0–1000, narrowed at the rear corners and pillars. With the 100mm rear gap, it spans vehicle
Y = 100–1100, ending 110mm behind the lower rear seal of the left sliding-door opening. Length has its own Cabinet control; changing it
keeps the rear fixed and repositions the middle support halfway along the cabinet, resizing both shelf bays.
Depth follows the space between bed and wall. The fixed-height setting is replaced by `cabinet_ceiling_gap_mm`, default 3. Height
of the skins follows the plywood underside, curving gently down toward the wall.
A zero gap brings the skins to the modelled ceiling. Platform height affects the lower shelf rail, not cabinet height.

`body.interior_limits` constructs native fitting volumes from the same sections as the visible body and ceiling.
Door aperture holes are omitted from fitting volumes, but pillar and roof-rail intrusions are subtracted.
The ceiling limit uses the plywood's inner circular profile, offset inward by the cabinet fitting gap.
The end skins and shelves are scribed against
the wall, rear-corner and ceiling curves. The support frames have straight stepped profiles, using the same
`frame_panel` primitive, member width and rounded opening radius as the benches.

Each end frame is one continuous 18mm sheet with four enclosed openings. The lower two are wide; the upper two are
narrower. A member-width bottom rail closes the lowest opening. The lower shelf rail aligns with the bed support's
top rail at `platform_height_mm - slat_thickness_mm`. The inside corner of the outer step uses the shared radius too.
`cabinet_frame_step_height_mm` sets the top of the upper shelf rail and the outer frame step, default 750.
An additional rail splits the upper opening into two equal clear heights. All four frames have a flat top below
the lowest edge of the ceiling clearance profile. Transverse-frame widths are
derived from the minimum available width across each whole height band, checking both faces of the stock and rounding inward
to whole millimetres. They are not clipped into wall curves. The skins extend above the frames to follow the roof crown.

The aisle frame has two columns of four enclosed bays. The central transverse frame aligns with its middle upright.
Any transverse frame crossing the approximate wheel arch has a narrower lowest opening, retaining a full member-width upright on the aisle side of the wheel arch, with
3mm clearance. The lower cross-beam has a straight underside extending toward the wall, with the shared rounded
inside corner where it meets that upright; no wall-side stub hangs above the arch.
All shelf rails align across the frames. The space below the
bed-height shelf is obstructed by the extended bed.
The wall-facing side is open, without a longitudinal support frame.
End frames butt against the aisle frame at X = 1088.
Frame thickness, skin thickness, member width and opening radius reuse the shared dimensions under Long bench.
Each bay has three separate shelves using `cabinet_shelf_thickness_mm` (12mm); the van floor serves as its bottom,
without bottom shelves or ledges. Ledge bottoms align with the cross-beam bottoms. Shelf surfaces sit below the
cross-beam tops by member width minus ledge size minus shelf thickness (30mm at defaults), leaving a retaining lip
and concealing small alignment differences. Plywood strip ledges (`cabinet_ledge_size_mm`,
18mm wide, cut from the same 18mm sheet stock as the frames) run along the end/centre frames and aisle cross-beams, underneath the shelves. Centre-frame ledges support
both bays. Shelf thickness and ledge height must fit within the cross-beam height. The central frame has a
rounded wheel-arch cut-out; shelves also clear the arch if adjusted heights bring them into its space.
Shelves and ledges have their own assembly groups and sidebar visibility controls. Each physical piece is a native
Part. Skin and shelf edges may need bevels where the body varies through their thickness; frames remain flat stock.
There is no wall-facing skin, top panel or door. Shelf fasteners are not modelled.

`cushions.py` ports the six foam blocks and their day/night placements from `nv200-interior.fs`.
Seats are 600 × 1280 and 835 × 580; the four backrests are 235 wide by 1280, 530, 750 and 580 long.
All six use the shared 100mm foam thickness. They belong to their daytime bench's Cushions group.
Both Cushions groups have a fixed +7mm X offset for wall clearance, retained throughout the animation.
Each cushion is a centred native box in its own located Compound, so its live rotation uses the same origin as CAD.
Bed extension 0 gives upright backrests above the seats; 100 tiles the 1070 × 1860 bed at Z = 400–500.
The orange and purple wall backrests fold toward the wall without changing their day/night positions.
All cushions remain in their daytime positions until the bed frames finish extending at 40%.
All four backrests finish turning and moving horizontally at 80%. During the turn their lowest corner
stays above the blue seats, with a small handling clearance; the remaining travel lowers them vertically into place.
The blue seats finish sliding at 80% too, clearing the wall-side infill spaces before the backrests descend.
Python generates pose samples used by both CAD and the viewer, which interpolate the same centres and intrinsic XYZ
angles. This is a hand-repositioning preview, not a physical mechanism or a general collision-free handling path.
Cushions are moved by hand and are not attached to the storage lid.
Hide them to inspect lid movement. Rear-corner foam fit and retention remain physical-layout questions.

`cross_stops.py` ports `crossStopDimensions` and `crossBenchStops`. Two 100 × 22 × 2mm plate envelopes attach under
the first and last moving slats. Each projects inward across the 3⅓mm gap, engaging 46⅔mm of the neighbouring fixed
slat's underside guide pocket. The 239mm-long guide pockets combine 217mm travel and 22mm plate width, with exact
closed end faces.
The moving mounting pockets are 3.5mm deep; fixed guides are 4mm deep. Plates sit 1.5mm above the deck, reserving
1mm for screw heads and 0.5mm running clearance. Thickness and screw allowances are provisional, and holes are not
modelled. These stops limit horizontal travel; they do not capture the slats against lifting.
Plate and pocket dimensions are under Cross bench → Sliding assembly → Extension stops.

`frontend/src/viewer.ts` owns the viewer host. It embeds the installed OCP renderer through `createPage`, using the
constructor hook to retain the viewer instance. FastAPI serves that package's JS/CSS at `/viewer-assets`; Vite proxies
that route. The existing OCP server carries geometry and measurement messages over its WebSocket. There is one viewer
connection and no iframe, splash, Tools/Info menu or animation playback bar. The toolbar retains projection, display,
reset, fit and distance controls, with the XYZ orientation marker below. `view-cube.ts` replaces the seven direction
buttons with a compact SVG ViewCube at the top right. Its face, edge and corner regions select all 26 directions;
dragging orbits with Z upright. It projects the cube using the CAD camera quaternion and updates with the renderer.
The main viewport uses the renderer's native `orbit` controls with `up: 'Z'` to prevent free trackball roll.
Selection uses the existing camera location API, retaining the target, camera distance, projection and orthographic
zoom. It uses the installed camera's own look-at calculation, with fixed plan orientations for top and bottom.
Cube clicks interpolate camera quaternions along the shortest rotation at 360°/s using Three.js slerp. Camera distance
and target remain fixed. Cube drags are immediate; pointer, wheel and keyboard input or new geometry cancel an active
transition so it cannot overwrite subsequent camera changes.
Geometry publication uses `Camera.KEEP`. The host records the actual camera position, quaternion, target, zoom and
projection in `campervan.camera` localStorage on viewer notifications and page exit. Orthographic views also retain
their visible world height. Before rendering new geometry, it supplies the live camera values, or the saved values
after a page reload. After render and resize, it restores the exact camera location: perspective framing is encoded
by camera position, while orthographic zoom is adjusted to preserve the saved world height against the new frustum.
This removes the renderer's model-bounds-dependent camera rescaling. Initial zoom is 0.65 only without a live or saved
camera. Notifications during rendering do not overwrite the saved view with intermediate camera state.

Dimensions rebuild geometry. After `show`, `viewer.py` sends `campervan_motion` with each position parameter's assembly
paths, axes, travel and published pose. The host retains each group's original translation or rotation and applies an
absolute offset from that pose. Bed, drawer and lid sliders work without an animation timeline or regeneration.
The bed slider also repositions cushions. Their tracks include position/angle keyframes from the same layout used
by CAD, so regeneration at an intermediate position preserves the preview. Translation and
rotation bases are stored separately for groups that use both.
The Python model uses the same poses and travel for geometry checks and future exports. Releasing a slider saves only
that position through `PATCH /api/v1/model/position`. Slider input also saves all positions to `campervan.positions`
localStorage. On page load or API session change, the controller restores the positions to the UI and API before
requesting regeneration. New geometry receives the latest selected positions.

Category visibility uses the viewer's actual leaf paths and `setStates`. Vehicle, Slats, Cushions and Cabinet preferences
live in browser localStorage and are reapplied when geometry arrives. Slats covers both beds' fixed and moving slats, the cross-bench
fixed plywood deck, the complete storage lid including its attached slats, and the cross-bed plate stops.
Cushions covers both benches' foam groups; their sidebar eyes also work independently.

The cushion check compares the six daytime bounds with the source layout and checks flat bed coverage and no foam
overlaps at either endpoint. Intermediate poses and physical cushion handling remain visual checks.
It also samples all four backrests' turn and descent to check clearance above/beside the blue seats.

The cross-bench smoke check covers part validity, baseline dimensions, the divider's open centre and beam recesses,
and retracted/halfway/extended clearance of the sliding assembly and lid. It also checks that both extended beds align,
and that the plate stops clear their mounting pockets but meet the guide ends when pushed beyond either travel limit.
The fixed-frame smoke check covers valid single-solid pieces, dimensions and unintended volume intersections between
the plywood pieces and with the left wheel arch, at the default and one adjusted bench size.
The cabinet check covers valid parts, six recessed shelf panels, containment within the body and ceiling limits, straight frame edges with
the shared opening radius, ceiling-following skins, and clearance between parts and the right wheel arch.
The sliding-bed check samples retracted, halfway and fully extended frames (slider 0%, 20%, 40%) for interference
with stationary parts and the wheel arch;
this is a small sanity check, not a continuous motion proof.

Inspect changes in OCP. The vehicle geometry check covers valid references, body/layout bounds, wheel-arch gap and
actual door-aperture cuts. Add direct intersection or clearance checks only as moving or adjacent components
make them useful.

## Articulated mannequin

The browser loads the CC0 human rig in `frontend/public/models/mannequin.glb`; provenance is alongside the asset.
`frontend/src/mannequin.ts` adjusts mesh and skeleton to Gert's measurements: 1780mm height, 800mm inseam,
500mm floor-to-knee pivot and 400mm knee-to-hip joint. It straightens the supplied pose, resizes at these measured
landmarks and rebinds the skeleton. Other body proportions remain estimates. `frontend/src/spine-rig.ts` adds 13 runtime
skinning joints along a continuous arc from the sacrum to the shoulders, replacing the asset's coarse trunk weights.
The pelvis follows the bottom tangent; shoulders, arms, neck and head follow the top tangent. Non-trunk skin influences
are retained, and the original GLB is unchanged.

**Sit on bench** fits a seated pose to the displayed long-seat cushion, allows estimated foam compression and clears
the calves past the bench edge. XYZ hip position, facing and joints remain adjustable with sliders. Ankle rotation
maintains the flat-foot orientation independently of the calves. Joint edits retain the chosen angles and adjust hip
height to put the soles on the floor; hip-height edits solve the legs instead. Recline sets the mean torso lean;
curvature sets the total bend along the arc, starting at the sacrum. The arc deforms the mesh's existing anatomical
shape. Leg and ankle posing compensates for pelvis rotation to retain floor contact. **Sit on bench** starts with
20° recline and 35° curvature; saved manual poses remain unchanged.
Gaze compensation is shared between neck and head, maintaining
a downward laptop gaze without forcing the skull to counter-rotate against a backward-pointing neck.
Manual poses can exceed furniture clearances or available foam compression; the sidebar reports the detected limits.

`frontend/src/seat-cushion.ts` subdivides the displayed seat foam and dents its top beneath the posed skin, keeping the
bottom fixed. Compression is a visual approximation, capped at 55% of foam thickness. Hiding the person restores the
original geometry. This does not change the manufactured CAD cushion or simulate foam stiffness. The seated preview
is hidden during bed extension because it is not a lying-down pose.

Controls act directly on viewer geometry, persist in browser storage and do not regenerate CAD. The rig is detached
before OCP disposes its old scene and reattached afterwards. OCP bundles Three.js r184; the GLTF loader uses the matching
pinned npm version. Human geometry and material are allocated through OCP's constructors to keep numeric resource IDs
unique. No second canvas or render loop is used. The mannequin is not included in build123d assemblies or CAD exports.

## Materials and bill of materials

The CAD and Bill of materials tabs share the same model. Switching tabs leaves the viewer mounted at its existing
size so camera, visibility and live positions survive. The BOM groups uses by resolved supplier product ID,
with one price and availability record per product. Unspecified custom stock remains separate by role.
Each product expands into component uses and a combined cut list grouped by dimensions. Hardware quantities are
summed across unowned uses before rounding up to purchase packs. Sheet areas and timber lengths are combined,
but purchase counts still require a cutting layout. Sidebar links retain their role-based URLs and expand the
containing product, highlighting the specific use. Expanded product rows survive status refreshes during the session.

`src/campervan/materials.json` is the product catalogue: exact supplier links, variant dimensions in mm, specifications,
unit/pack prices in NZD including GST, availability notes and the date checked. Catalogue entries are candidates,
not an assertion of local stock or suitability for every part. The BOM is read-only; sourced products are the default selections and their section/thickness dimensions drive
the model. Loading a project fills missing selections from these defaults while preserving explicit choices,
custom stock and measured overrides. Updates go through catalogue edits and the existing materials API.
`materials.py` maps material roles to existing CAD parameters and resolves selected products plus optional measured
section/thickness overrides. Custom stock uses the existing parameter value. Listed sheet sizes and stock lengths
constrain cutting, not the van layout. Reused slats start as already owned custom stock.

`.local/project.json` saves parameters, material selections, measured overrides, ownership and manually confirmed
purchase quantities. It is gitignored. API reloads read it; edits through the API save it. Browser storage continues
owning camera, visibility and live-control preferences. Shelf ledge width and height are separate dimensions; shelf
bottoms remain on top of the ledges, whose bottoms stay aligned with the support-frame cross-beams.

The CAD worker builds the assembly once, then `cad/bom.py` collects local leaf cutting envelopes before publication.
Its explicit material mapping uses assembly paths and labels; update this mapping when changing the component tree.
Local leaf envelopes ignore parent motion, so opening the lid, sliding the bed or hiding parts does not alter quantities.
The worker returns cuts to the coordinator alongside successful regeneration. The BOM marks previous cuts as stale
while a new revision is pending or failed, and displays regeneration errors.

Plywood frames, skins, shelves, drawer panels and deck/lid, plus shelf ledges, guide ledges, bearers and slats,
have material assignments. Hardware includes angle brackets, stop plates and complete drawer slides. Only the
fixed rail leaves contribute to slide quantities; intermediate and moving stages belong to those same purchased
slides. Bracket entries use arm length, width and steel thickness, not their rectangular bounding-box depth.
The hinge and bracket screws are sourcing candidates without modelled fasteners; the hinge quantity is explicitly
one and screw quantity remains unconfirmed. Their fit notes identify mounting details still to resolve.

Other furniture leaves are listed as unassigned. Vehicle references and cushions are excluded.
Cut rectangles are not a nesting plan: they exclude saw kerf, grain constraints and waste. Sheet and stock-length
purchase quantities require a cutting layout; roles selecting the same product may share stock.

Frame supports, cross-bench support rails, bed guide ledges and shelf ledges all use the selected 18mm frame plywood.
The bed guides stand on edge, so their bearing width is the sheet thickness (18mm); their height follows the frames.
Shelf ledge strip width remains a cut dimension, independent of the sheet dimensions.

Skin panels use 4mm Tigerply Okoume-faced poplar-core plywood (Bunnings special order). The selected sheet thickness
sets `wall_thickness_mm` for the bench, partition and cabinet skins; shelves, lids and frames keep their own stock.
