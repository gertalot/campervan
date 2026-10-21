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
The cabinet reflects and translates body/ceiling fitting volumes into that coordinate system before scribing,
so its mirrored placement fits the actual left side. Wheel-arch cutouts remain symmetric.
A perfect furniture reflection does not imply an asymmetric vehicle is mirrored.
`src/campervan/parameters.py` owns dimensions, basic validation and sidebar metadata.
`parameter_fit.py` checks the bed-height dependency chain before saving or regenerating: wheel-arch/top-rail clearance,
rounded frame openings, slide mounting bands and the mattress-following cabinet divider.
The lower shelf height follows platform + uncompressed foam + shelf clearance. Mattress thickness and shelf-clearance
inputs have bounds that preserve the opening above the divider; platform maximum follows the same relationship. It supplies current input bounds and
plain-language reasons. The tray and drawer-support frame reduce in height when necessary, retaining 1mm clearance;
these adjustments are shown in the sidebar and saved on Apply. Raising the bed does not enlarge them again.
Stock thicknesses, member widths, opening radii and vehicle measurements never change automatically.
The draft preview endpoint performs these checks without saving or running CAD. The UI updates numeric limits,
shows errors beside the affected input and disables Apply for an invalid draft; the API also checks before saving.
This covers the platform-height dependency chain, not every possible geometry constraint. Geometry checks remain
necessary for other combinations. Geometry code does not call the API or viewer.

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
│   │   │   ├── Side panel
│   │   │   ├── Rear window (Metal surround, Window glass)
│   │   │   ├── Rear pillar
│   │   │   └── Front pillar
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
│   │   ├── Clear opening
│   │   └── Closed hatch (Door envelope, Window glass)
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
    ├── Middle panel
    ├── Cab-end panel
    ├── Wall lower frame
    ├── Wall upper frame
    ├── Back lining
    ├── Doors
    │   ├── Rear upper 1/2 → Plywood door + Point latch
    │   ├── Cab-end upper 1/2 → Plywood door + Point latch
    │   ├── Cab-end lower 1/2 → Plywood door + Point latch
    │   ├── Rear storage aft/fore → Plywood door + Point latch
    │   └── Rear storage upper aft/fore → Plywood door + Point latch
    ├── Latch strikes
    ├── Latch strike blocks
    ├── Corner cleats
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
  Roof-side rails follow this curved wall with an adjustable 20mm inward-depth estimate, capped at the ceiling's
  lateral edge. They do not fill the entire shoulder-width box: that former shape projected too far inward at its
  lower edge compared with the owner's photographs. The 20mm depth remains an estimate, not a new measurement.
  `body_section` describes the inner wall, not the exterior. Side panels and rear corners have closed solid envelopes
  extending outward by door thickness minus rear-pillar intrusion: 100 − 40 = 60mm at defaults. This leaves the
  measured interior unchanged and aligns exterior walls with the closed doors. The outer shape is an estimate
  following the inner curvature, not a measured exterior scan; these solids represent body cavities, not solid steel.
- Fixed rear side windows have separate glass and metal-surround parts within each wall. The initial glass estimate
  is 600 × 300mm, only 20mm taller than the sliding-door glass, with the extra height above it: rear glass spans
  Z = 810–1110 versus door glass at 810–1090. Its separate top-gap control defaults to 60mm. They sit midway between
  the rear corner transition and sliding-door pillar. Glass follows the curved wall 30mm outward from the interior,
  within the 60mm wall depth. The surround starts flush with the inner wall and slopes outward to the glass;
  no raised band projects into the cabin. Its outer surface shares the rest of the side panel's exterior profile.
  Width, height and recess depth are adjustable under Side walls. Both window types share `window_recess`,
  rounded-corner cutters and the surround-width setting. Furniture fitting continues to use the measured inner wall.
- Rear corners have a 60mm straight section followed by an angled transition ending at Y = 200. The original
  `rear_corner_radius_mm` identifier is retained for saved parameters, but its control is **Corner transition depth**.
  This implemented extent still needs reconciling with the owner's clarification of 60 straight plus 200 flared;
  see the [dimension audit](research/nv200/dimension-audit.md) for the distinct rear-door/opening references.
  Their rear side/header edges now come directly from the measured aperture used by the hatch, rather than a
  separate scaled wall profile. Both visible surfaces and the cabinet-fitting volume use these same sections.
  The curved rear end of the fitting solid is explicitly capped; a planar-ended solid loft cannot represent it.
- The closed rear hatch retains its measured inner surface (130mm behind the bed at the centreline, Z = 390).
  Its estimated 38mm depth extends outward from that surface. Rounded trapezoidal glass is estimated at 1000mm
  bottom width, 940mm top width and 450mm height, with its top 100mm below the opening crown. The glass follows
  the hatch curvature, recessed 30mm outward from the inner panel and remaining 8mm inside the exterior.
  The tapered metal return follows both curved window boundaries. Width, taper, height, top gap and recess
  are adjustable under Rear opening; the surround width is shared with the side windows.
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
  Open-door envelopes leave 680 to the front pillars and their inner faces sit approximately 60 outside the body.
  Door thickness is owner-measured at approximately 100mm: closed outer faces follow the new exterior wall profile,
  and closed inner faces follow the pillars. The complete curved
  envelopes fit the aperture outline and retain the body taper throughout their travel. The shared door-closing
  slider moves both forward over 0–85%, then inward with the last 30mm of forward travel over 85–100%.
  CAD placement and viewer keyframes share `sliding_door_offset`; the controls need no regeneration.
  These remain approximate clearance envelopes, without detailed rollers, tracks, seals or door construction.
  The sliding-door glass is a wide, shallow 560 × 280mm reference surface at defaults, with its top 80mm below
  the opening header. These are photo estimates. A 30mm sloping metal surround recesses from the inner panel to
  a glass seat 8mm inward of the outer wall. The pocket joins the actual curved inner and glass boundaries;
  the glass follows the curved wall. Window height, top gap and surround width are
  adjustable. See inside also fades the glass but preserves its low opacity on the far side.
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
extension. The shortened deck clears the moving supports without bracket relief pockets. The long bench uses
`bed_extension_percent`; the cross bench independently uses `cross_bed_extension_percent`. Their default travels are
452mm and 217mm respectively, each ending at X = 1070 when fully extended.

The 358 × 576 × 12 plywood storage lid carries three wall-side slat sections aligned with the fixed toilet-side rows.
These strips retain their full 80mm width. The 25mm finger hole sits in a gap between them.
Its group origin is the cab-side hinge at Y = 1858, Z = 400. Children use coordinates relative to that hinge.
`cross_lid_open_percent` rotates the group from 0 to −70 degrees about X, lifting the rear edge toward the cab.
The lid moves independently of the beds and drawer. Hinge hardware and toilet hardware are not modelled.

`cabinet.py` builds the left-side cabinet in furniture-local coordinates, before the common mirror/placement.
Its closed-door footprint starts at X = 1070, Y = 0–1000, narrowed by the vehicle envelope and wall support. With the
100mm rear gap it spans vehicle Y = 100–1100. Length changes preserve the rear end. The centre partition starts at
`cabinet_rear_bay_length_mm` (650mm), measured directly from the open rear end; the forward bay is 326mm clear
at defaults, between the single 12mm centre and cab-end panels. The cab end's outer face stays at Y = 1000.

`cabinet_frame_thickness_mm` supplies the solid partitions, aisle frame, rear rails and rear upright from the same
sourced 12mm Tigerply stock; the bed retains its 18mm stock. The aisle frame retains its rounded openings and door
mounting posts. The centre and cab-end partitions are solid, scribed against the lining and vehicle fitting volume.
The aisle frame's top rail extends to the finished plywood underside, following its curve across the frame thickness.
It has no ceiling gap. Door openings and hinge elevations retain their existing heights; the top rail grows upward.
The centre panel has the wheel-arch notch with 3mm clearance and reaches the floor inside the arch. The cab-end
panel follows the plywood ceiling with the selected 3mm fitting gap. The `Rear upper panel` uses the same 12mm
stock at Y = 0–12, starting at `cabinet_rear_storage_height_mm` (730mm) and following the body/ceiling fitting volume.
It closes the two upper rear compartments while leaving the full lower chair entrance open. Rear shelves start
at its inner face, Y = 12; they have rear-panel ledges with their outer ends scribed around the rear pillar.
There are no cabinet skins, full-height transverse rear frame, bottom threshold or lower rear crossbar.
The van floor is the bottom.

The lowest rear shelf supports start at `cabinet_rear_storage_height_mm` (730mm); shelf underside/top remain at
748/760mm. The forward middle shelf shares this elevation, so both bays' middle beams run at 730–790mm.
The upper rear shelf and three forward shelves remain. Shelf and door heights, front rail retaining lips and the
closed doors' 1070mm bed envelope are unchanged by the partition conversion.

The wall-side support is a separate `Wall supports` group: seven straight 12 × 60mm plywood rails and one narrow
transverse rear upright. Each bay has a top rail; the rear bay has two shelf rails and the forward bay three.
Rails butt into the centre/cab-end partitions and rear upright rather than fastening to the vehicle. Each rail
is vertical rectangular stock, set inboard of the lining over its full height; higher rails sit further inward.
There is no low rail through the rear chair compartment and no broad wall-side frame or continuous support plane.
The lowest forward rail follows the raised shelf and clears the wheel arch by at least 3mm.
Its top is `cabinet_lower_rail_top_mm`: platform + foam + shelf clearance + member width − ledge height − shelf thickness.
The rear aisle frame has the same extra crossbeam but no matching shelf or wall rail inside the chair compartment.

The rear upright stands on the floor immediately ahead of the rear pillar, at the start of the back lining.
It is a 12mm transverse plywood strip, nominally 60mm wide across X at each height, with its profile approximating
the wall. The rear shelf edges are notched around it. It leaves the rear chair-loading route clear.
The solid partitions are bounded by the lining/vehicle fitting volume; shelves end at their own rail's inboard face.
The old `cabinet_frame_step_height_mm` parameter is retained for saved projects, now labelled **Upper shelf reference
height**: the upper shelf rail remains halfway between this reference and the cabinet top.

The five 12mm shelves form a bonded assembly: glue shelves onto their ledges and glue ledges continuously to the
partitions, aisle frame and rear rails. The separate `Rail joint blocks` group contains fourteen vertical pine
blocks, one at each rail end, with a full rail-height face against the rail and an adjacent face against the
upright or partition. They use the same ready-made 18 × 18mm stock and are 60mm tall at defaults. Glue both faces;
predrill assembly screws through the plywood faces into the blocks, staggering perpendicular screws.
The five shelves have local corner notches around the blocks; transverse ledges stop 18mm short of the rail
face and wall ledges fit between the blocks. The blocks replace the two former 30mm wall corner cleats.
Two 60mm-high aisle cleats remain above the lowest forward shelf. The rear rail joint blocks remain above the chair bay's 730mm clear height. Glue layers and assembly screws are not modelled. The BoM includes an initial 250ml bottle
of Selleys Aquadhere Exterior PVA from Bunnings NZ. Use close-fitting bare-wood joints and clamp while curing;
leave unstressed for 24 hours. This adhesive is for furniture joints, not vehicle anchorage.

This is a visual construction proposal, not a fabrication template or load rating. Template the rear upright
and partition profiles in the real van and establish fitting clearance along each rail before cutting finished
parts. The vehicle model is approximate. The flute board carries no structural load, and vehicle restraint must
be designed separately using existing mounting points only; no new vehicle holes or wall attachments are modelled.

The rear bay loads from the rear and through its paired aisle doors. A 230 × 730mm loading envelope, starting
3mm behind the latch bodies, extends from the rear aperture through the 650mm bay. Geometry checks include the
rear corner pillar and wheel arch. Stored chair and solar-panel poses are unchanged.
Both rear and forward shelves have aisle/wall and two transverse ledges. The rear-panel ledges remain at or above
the storage clear height; nothing crosses the lower rear entrance. The 20 shelf ledges use ready-made 18 × 18mm untreated
clear pine; ledge bottoms align with their rail bottoms, leaving a 30mm retaining lip at defaults. All ledges and
corner cleats are rectangular crosscuts; no wall-facing bevels are needed.
The BOM records the purchased rectangular section and crosscut lengths, including the two 70mm latch blocks.
The selected Bunnings product is Pinetrim 18 × 18 × 2400mm D4S untreated clear pine (0293156), listed at $12.27
per length on 2026-10-20; Lyall Bay stock is unconfirmed. No table-saw ripping is required for these battens.
Vehicle mounting hardware remains unmodelled; glue joints and material volume checks do not establish load capacity.

At the owner's saved 390mm platform height, the compared centre/cab-end frame-plus-skin construction contained
8.687 litres of plywood versus 9.596 litres in the solid 12mm partitions. Enlarging the forward shelves and ledges
added 0.111 litres, for a 1.020-litre increase before corner cleats and extending the wall supports to the cab end.
This is a material-volume comparison, not a measured weight saving. The forward clear length increases 318→326mm.
The initial all-plywood implementation added 1.159 litres, including corner cleats and the wall supports extended
to the cab end. The ledges, corner cleats and latch blocks have since changed to ready-made pine; that historical
volume comparison is not a weight comparison for the mixed-material assembly.

The wall-facing back lining is Bunnings Tunnelcore 3mm white polypropylene flute board
(2440 × 1220mm, item 0999179). It bends across its height, follows the general wall curvature, and bridges the
window recess. The most projecting side-pillar profile within the cabinet span determines its position, with
1mm normal clearance. Its top meets the plywood ceiling; it stops 1mm ahead of the rear corner transition,
never wrapping around that pillar. Its cab end follows the cabinet end. A bottom notch uses the cabinet's
existing wheel-arch cutout and 3mm allowance. At defaults it spans Y = 201–1100 in the vehicle.
The rear rails and upright fit inside the backing's inner face; shelf depths meet their individual rails.
The partitions follow the fitting volume rather than the former two broad support planes. The space behind the
sheet is excluded from the carcass fitting volume.
Thickness comes from the selected product; clearance has its own Cabinet / Back lining control and visibility eye.
The Visibility section also has a Cabinet backing checkbox; its saved preference survives hiding/showing the cabinet.
The BOM records the sheet separately from plywood and uses its developed centre-curve length for the cut rectangle,
not the curved part's bounding-box depth. Confirm flute orientation and physical fit before cutting.
There is no top panel. Shelf fasteners are not modelled.

`cabinet_doors.py` makes ten 9mm plywood overlay doors. The four upper shelf openings each have a
bottom-hinged flap, intended to stop horizontally on two short chain restraints. The two front lower openings
retain vertical hinges, with separate live controls above/below the mattress. All edges overlap the openings by
15mm, with 12mm plan corner radii and 2mm face roundovers. The four original upper flaps retain their dimensions.
The rear storage doors have two opposed pairs, split at the raised front shelf's rail. The aisle crossbeam divides
access without adding a shelf or rear crossbar. The rear chair-loading entrance remains 730mm high.

`cabinet_mattress_clearance_mm` places the front lower shelf top 10mm above the uncompressed mattress. At the
saved platform height 390mm and foam thickness 100mm, the shelf top is 500mm, the beam spans 470–530mm, and the
above-bed doors begin at 515mm. Clear access openings above that beam are 200mm high. The two front lower doors
are 284 × 440mm and 284 × 230mm; the four rear storage leaves are 297mm wide with heights 440/230mm.
These dimensions follow bed height, foam, clearance, stock sizes and overlay instead of fixed elevations.

The closed door fronts stay at X = `bed_width_mm` (1070mm), and backs at X = 1079. The aisle frame starts at
X = 1081, giving a 2mm gap for folded surface-mounted hinge leaves. `cabinet_aisle_x` is this actual front-face
coordinate, independent of bench skin thickness. Shelf and partition depths derive from it; the wall-side
support and flute-board lining retain their existing contour and position.

Door groups have hinge-centred origins and native plywood children, keeping cutting sizes independent of pose.
`cabinet_upper_doors_open_percent` rotates the four upper groups about Y from 0 to −90 degrees, and
`cabinet_lower_doors_open_percent` rotates the lower groups about Z from 0 to 90 degrees. The viewer reuses
these tracks through the existing mirrored motion mechanism, without regeneration.
`cabinet_storage_doors_open_percent` turns the bottom rear pair about Z by +90 and −90 degrees before mirroring.
`cabinet_storage_upper_doors_open_percent` independently turns the above-bed rear pair. The front bottom door
uses `cabinet_lower_doors_open_percent`; its raised neighbour uses `cabinet_front_upper_door_open_percent`.
The three above-bed side-hinged leaves clear the flat uncompressed mattress in the fully made-up bed.
Bottom doors still require the bed stowed; sliders do not enforce furniture operating sequences.

The BoM includes twenty Zenith 35mm fixed-pin butt hinges, ten Vanlifer Point push latches and one 3m pack of
Pinnacle 2mm double jack chain. The four drop-down flaps each require two chain restraints; cut lengths depend
on actual anchor positions (roughly 240–300mm each as an initial allowance).

All doors use Vanlifer NZ Point LL016 positive push latches (NZ$16 each including GST), each with its supplied striker.
The supplier drawing specifies 5–25mm panels, a 27mm bore with 23.5mm flats, 32mm flange and 50mm depth from the
door front face: 41mm projects behind the 9mm door. The catch station is 35.5mm behind the door face and 20mm above
the bore axis. Storage latches sit near the inner upper corners; flap latches are centred near the top and the lower
side-hinged doors latch near their free upper corners. Six strike under the aisle shelf ledges. Four 70mm blocks cut from the same 18 × 18mm pine support
the topmost strikers and bottom storage-door strikers behind the aisle frame/crossbeam.
The CAD shows body envelopes and door bores. Striker overall dimensions (reserved 15 × 70 × 8mm) and flange
thickness (1.5mm) are estimates; the cam, nut, fixing holes and released knob are not modelled. Confirm these details
on the physical product before machining. Closed flange envelopes extend 1.5mm into the aisle.
Strikes are included with the latches and excluded from separate BOM purchasing counts. The single shared catch
role counts the ten modelled latch bodies; old saved roller-catch selections migrate to this product.
Other hardware bodies, chain restraints, anchors and fasteners are not modelled.
Hinge leaves are intended to face-mount in the closing gap, avoiding screws
into the 9mm plywood edge. Through-fix the door-side hardware with flush countersunk heads. Check the actual
leaf thickness/holes and select fixings before drilling. Fasten chain anchors into frame members and through-fix
door anchors rather than relying on the 4mm skin or screws into a 9mm plywood edge. Check that slack chain
stows inside the opening without being pinched when the door closes. The hinge-centred preview stops at
90 degrees; it does not simulate flexible chain or verify the final anchor/load capacity.

Bunnings product pages were checked on 20 October 2026: door plywood item 0345104 ($58/sheet), hinges
4161393 ($1.45 each), catches 0035579 ($4.73/4-pack) and
[chain 0581686](https://www.bunnings.co.nz/pinnacle-2mm-x-3m-zinc-plated-double-jack-chain_p0581686)
($7.91/3m pack). These are Bunnings New Zealand listings; local Lyall Bay stock is unconfirmed. No overseas-only
stay remains in the purchase list. Loading a project removes the superseded `cabinet-stays` selection and adds
the `cabinet-chains` default, preventing the rejected stays from returning with saved project data.

`gear.py` adds a separate Stored gear assembly for the owner's folded solar-panel bag (830 × 760 × 80mm)
and two folding chairs (600 × 700 × 100mm each). These are owned reference objects, excluded from the cut list
and material purchases. The chair shapes approximate the supplied photograph: bent tubular frames, blue fabric,
wooden armrests and hinge fittings. All details stay inside the measured envelope; the bag's handle and webbing
are illustrative. No unfolded chair mechanism is modelled.

The bag starts upright across the rear gap, centred at X=750, Y=45, with its bottom at Z=0.
The chairs start edge-on in the aisle, centred at X=520/640, Y=600, with their feet at Z=0; these are temporary
comparison positions, not an approved storage arrangement. Each object has independent footprint-centre X/Y,
bottom elevation and rotation sliders under Stored gear, plus group visibility eyes and a Stored gear checkbox.
These use the existing live motion tracks: dragging moves geometry immediately, releasing saves the pose without
regeneration, and browser storage restores it after reloads. Translation sliders step by 1mm and rotation by 1°.
The cabinet and bed are unchanged. The owner confirms the real bag fits behind the existing bed with 20–30mm
spare clearance; the current estimated hatch shape conflicts with that reference above about Z=550 and remains
to be reconciled. This discrepancy is not evidence that the real bag needs more space.

`cushions.py` ports the six foam blocks and their day/night placements from `nv200-interior.fs`.
Seats are 600 × 1280 and 835 × 580; the four backrests are 235 wide by 1280, 530, 750 and 580 long.
All six use the shared 100mm foam thickness. They belong to their daytime bench's Cushions group.
Both Cushions groups have a fixed +7mm X offset for wall clearance, retained throughout the animation.
Each cushion is a centred native box in its own located Compound, so its live rotation uses the same origin as CAD.
Each bench's conversion slider moves its seat and wall backrest. The green rear-end and cab-facing cushions remain
upright at their seated positions, with no live motion tracks. At 100 the moving cushions lie at Z = 400–500;
the green cushions remain above them, so this preview no longer tiles the entire bed with flat foam.
The orange and purple wall backrests fold toward the wall without changing their day/night positions.
Each bench's cushions remain in their daytime positions until its frame finishes extending at 40%.
The two wall backrests finish turning and moving horizontally at 80%. During the turn their lowest corner
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
Each bench slider also repositions its own cushions. Their tracks include position/angle keyframes from the same layout used
by CAD, so regeneration at an intermediate position preserves the preview. Translation and
rotation bases are stored separately for groups that use both.
The Python model uses the same poses and travel for geometry checks and future exports. Releasing a slider saves only
that position through `PATCH /api/v1/model/position`. Slider input also saves all positions to `campervan.positions`
localStorage. On page load or API session change, the controller restores the positions to the UI and API before
requesting regeneration. New geometry receives the latest selected positions.
Older project files and browser storage containing only the shared bed position initialize both bench sliders to that
position. Once separate positions are saved, they remain independent.

Category visibility uses the viewer's actual leaf paths and `setStates`. Vehicle, Slats, Cushions and Cabinet preferences
live in browser localStorage and are reapplied when geometry arrives. Slats covers both beds' fixed and moving slats, the cross-bench
fixed plywood deck, the complete storage lid including its attached slats, and the cross-bed plate stops.
Cushions covers both benches' foam groups; their sidebar eyes also work independently.

**See inside** adjusts vehicle opacity in the browser before the existing viewer paints each frame. Assembly paths
assign walls, doors, pillars, rear corners and arches to their vehicle side; roofs and floors have vertical directions.
Roof rails fade when either adjoining side faces the camera. `frontend/src/vehicle-fade.ts` keeps far-facing and
edge-on panels opaque, then smoothly fades faces to 5% opacity as their side turns toward the camera, and outlines
from 50% to 2%. Driver and passenger seats, including their supports, stay opaque from the sides, rear and above;
they fade to 25% opacity only when viewed from the front. Opaque panels write depth so their interior surfaces hide
exterior faces; window glass retains its original low opacity on the far side. Visibility states and furniture materials
remain unchanged. The toggle defaults on and persists as `campervan.see-inside` in localStorage.
New geometry reattaches the effect; turning it off restores ordinary OCP transparency. Camera movement requires
no regeneration, API request or separate animation loop for this effect.

The cushion check compares the six daytime bounds with the source layout and checks flat bed coverage and no foam
overlaps at either endpoint. Intermediate poses and physical cushion handling remain visual checks.
It also samples all four backrests' turn and descent to check clearance above/beside the blue seats.

The cross-bench smoke check covers part validity, baseline dimensions, the divider's open centre and beam recesses,
and retracted/halfway/extended clearance of the sliding assembly and lid. It also checks that both extended beds align,
and that the plate stops clear their mounting pockets but meet the guide ends when pushed beyond either travel limit.
The fixed-frame smoke check covers valid single-solid pieces, dimensions and unintended volume intersections between
the plywood pieces and with the left wheel arch, at the default and one adjusted bench size.
The cabinet check covers valid flat-stock parts, five recessed shelves and contact with their supporting ledges,
containment within the body/ceiling, the ceiling-following cab-end panel, corner-cleat contact and clearance between all pieces and the wheel arch.
It also checks the continuous rear chair loading envelope against the cabinet, rear corner and arch.
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

The geometry-control hierarchy contains **Mannequin → Seated mannequin**, with room for additional poses. Its checkbox
lives alongside the other switches in **Visibility**. Pose and visibility retain the existing browser-storage key;
metadata refreshes reattach the same controls without resetting them.
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

Bed frame supports, cross-bench support rails and bed guide ledges use the selected 18mm plywood.
Cabinet ledges, corner cleats and strike blocks share ready-made 18 × 18mm untreated pine.
Cabinet partitions and frames use their own 12mm role, sharing sheets with shelves, drawer and deck/lid.
The bed guides stand on edge, so their bearing width is the sheet thickness (18mm); their height follows the frames.
Both cabinet batten section dimensions come from the selected timber product, with measured overrides.

Skin panels use 4mm Tigerply Okoume-faced poplar-core plywood (Bunnings special order). The selected sheet thickness
sets `wall_thickness_mm` for the bed and bench partition skins; shelves, lids and frames keep their own stock.
