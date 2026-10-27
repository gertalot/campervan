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

The worker captures a complete OCP display payload, exact measurement geometry, motion tracks and cut list in one
bundle. The coordinator saves it atomically to `.local/model-cache.json` after construction and replays it when the
browser connects. Reuse depends on resolved geometry dimensions, CAD/publishing source and CAD/viewer library versions.
Pose controls are excluded from that fingerprint; recorded motion tracks retain the bundle's construction pose so
the browser can apply current slider positions. Unchanged Apply reuses the bundle; explicit Regenerate forces a build.
Failed construction retains the previous bundle, with status and cut-list revisions indicating that it is older.

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
├── Finished floor plywood
├── Long bench
│   ├── Fixed frame
│   │   ├── Wall-side frame
│   │   ├── Aisle frame
│   │   ├── Cab-end frame
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
│   │   └── Drawer sliders
│   │       ├── Fixed (left and right)
│   │       ├── Intermediate (left and right)
│   │       └── Moving (left and right)
│   └── Cushions
│       ├── Long seat
│       ├── Wall backrest
├── Cross bench
│   ├── Fixed frame
│   │   ├── Wall-side frame
│   │   ├── Aisle frame
│   │   ├── Rear skin
│   │   └── Fixed slats
│   └── Cushions
│       └── Cross seat
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

`cab.py` extends the vehicle floor forward from `body_length_mm` at Z = −`floor_build_up_mm` (currently −18mm),
level with the cargo vehicle floor below the fitted plywood. Seat and headliner dimensions use the Z = 0 datum.
Seat supports extend down to the vehicle floor. Its headliner starts at the cargo ceiling plywood's front edge
(Y = 1660), then widens into rounded side returns over the cab. The centre
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
  Their inward depth is separately adjustable (40mm estimate). **Front pillar fore–aft width** extends them 100mm
  toward the cab from the front edge of each sliding opening, including beyond the cargo-body boundary. Their
  exterior follows the same closed-door outer wall profile; rounded opening returns remain behind that front edge.
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
- Rear corners retain a 60mm straight interior section followed by an angled interior transition ending at Y = 200.
  Their separate exterior is a smooth cubic surface, tangent to the rear face and straight side wall. The closed
  solid joins that rounded skin to the angular inner faces and keeps the rear seal and cabinet-fitting volume.
  The original
  `rear_corner_radius_mm` identifier is retained for saved parameters, but its control is **Corner transition depth**.
  This implemented extent still needs reconciling with the owner's clarification of 60 straight plus 200 flared;
  see the [dimension audit](research/nv200/dimension-audit.md) for the distinct rear-door/opening references.
  Their rear side/header edges now come directly from the measured aperture used by the hatch, rather than a
  separate scaled wall profile. Both visible surfaces and the cabinet-fitting volume use these same sections.
  The curved rear end of the fitting solid is explicitly capped; a planar-ended solid loft cannot represent it.
- The bare roof is a closed solid with **Roof thickness** defaulting to 10mm vertically above its existing inner
  profile. Main and rear roof skins are joined; bow, plywood ceiling and cabinet clearances retain their inner datums.
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
  Open-door envelopes leave a provisional 620mm to the front pillars, retaining 60mm overlap across the rear of the
  680mm lower openings at 0% closed. **Open clear width** controls this distance for both doors. The owner confirmed
  the overlap; its amount needs measuring. Their inner faces sit approximately 60mm outside the body.
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
  Its front edge reaches the greater of the nominal body length and the cross-bench front including the furniture
  setback (`cargo_length_mm + furniture_rear_gap_mm`): Y = 1960 at current dimensions. This supports the cab-end
  cross-bench feet at Z = 0. The vehicle floor reference retains its nominal body boundary.
- The 3mm ceiling sheet spans Y = 240–1660. Its underside is 1290 at centre and 1270 at its wall-side edges.
  Exposed side rails, rear header and three approximate bows are separate parts. The ceiling still uses concentric
  circular profiles for real sheet thickness. The bare roof estimate is 1347 above finished floor, with 55 crown.
- Wheel arches have an approximate 760 × 140 footprint and reach 280mm above the fitted floor. Their base reaches
  the vehicle floor at Z = −`floor_build_up_mm`, currently −18mm, giving a total height of 298mm. Extending the base
  preserves the crown profile and the furniture clearances above Z = 0. Wall-side endpoints are at Y = 310–1070,
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
the rear support starts at bed-local Y = 35 (vehicle Y = 120), with a 36 rear arch gap. The cab end has an 18mm frame
and no skin. The retained 4mm `long_bench_inset_mm` construction allowance preserves the wall-frame, guide and slat
positions independently of the cross-bench skin thickness. Saved `wall_thickness_mm` values migrate to this inset.
The internal support sits at X = 150–168 and reaches the rear header with an integral raised post. Its lower profile
retains the independent 300mm frame height and now spans the full 1280mm bench length, matching the other supports'
fore/aft endpoints. The guide ledges and tie strip retain their positions and need no additional cutouts. The header spans
X = 168–582, bed-local Y = 0–18, Z = 322–382, leaving the drawer exit open.
The long bench's cab-end frame fits between the inner and aisle support frames, X = 168–582, and occupies local
Y = 1262–1280. Its front face and the support endpoints sit flush against the cross-bench rear skin at Y = 1280.
This moves the transverse frame 4mm forward and narrows it by 18mm to avoid overlapping the extended inner support.
`drawer.drawer_support_x` shares the inner support alignment with the drawer placement; it follows wheel-arch width
and drawer clearance. The fixed cross bench has separate recessed frames.

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
(100mm at defaults), with the same rounded openings. Its fore/aft ends align with the first and last moving slats:
Y = 90–1190, giving a 1100mm-long frame with the current 1280mm bench and 80mm slats. These bounds derive from
the slat layout; both 60mm end posts remain beneath the outer angle brackets. The fixed aisle frame remains full length.
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

`drawer.py` adds the five-part 12mm plywood tray: 376 × 1224 × 290mm, X = 187–563, Y = 0–1224, Z = 10–300.
Both 1200 × 290mm sides run Y=12–1212. The 376 × 290mm end panels cap their ends at Y=0–12 and Y=1212–1224;
the 1200 × 352mm bottom fits between the panels, flush underneath. Internal length is 1200mm, 26mm shorter than
the previous drawer. The open sides retain a 90mm lower band and 60mm end uprights.
The rear face is flush with Y = 0. The tray travels 1215mm toward negative Y. Each 19mm mounting gap contains three
simplified 1200 × 53mm drawer-slider envelopes aligned at Y=12–1212; intermediate stages move half the tray distance.
The selected Instant Panel SKU 10632 drawer sliders lock fully closed and fully open. Their 45mm levers project
toward the rear doors; reserve 50mm operating clearance from the slider front. Lever geometry remains outside the
simplified envelopes. The former `drawer_rear_setback_mm` parameter is retired when loading saved projects.
Rear drawer contains the tray and the `Drawer sliders` assembly. Its stationary internal support belongs to the
bed's Fixed frame alongside the aisle frame and rear header,
so hiding or omitting the drawer leaves the bed supports in place.

`cross_bench.py` builds a fixed full-width platform at X = 0–1070, Y = 1280–1860 by default. Two fore/aft
18mm plywood frames have open-bottom rounded cutouts, 60mm legs and top rails. At the default 400mm platform height,
the frame tops are Z = 382; the 18mm slats bear directly on them. There is no divider, deck, sliding assembly,
cab-end skin, hinged lid, brackets or stop plates.

`cross_bench_overhang_mm` defaults to 200mm at the aisle slat ends. The wall-side frame aligns with the internal
drawer-support frame at X = 150–168, following the shared `Parameters.drawer_support_x_mm` datum;
the aisle frame occupies X = 852–870. Both run Y = 1289–1860. The aft 9mm skin bridges between the two rear legs,
covering X = 150–870, Y = 1280–1289 from floor to rail top. Its thickness uses the independent
`cross_bench_skin_thickness_mm` parameter. The space between frames is unobstructed;
toilet/tray hardware and slat/frame fixing details remain unmodelled. The skin is intended to brace the two rear legs
when properly attached; the CAD geometry does not establish load capacity.

Four 1070mm-long 80 × 18mm stock slats run across the van, directly over both support rails, matching the previous
extended cross bench's four moving rows. The first starts at Y = 1280; the last finishes at Y = 1860. Three equal
86⅔mm ventilation gaps fill the 580mm depth. The junction to the long bench's last extended moving slat remains
90mm, with no added empty margin at either end of the cross bench. Slat count stays four; their gaps follow the shared
stock width and cross-bench depth.
The cross bench has one full-width fixed cushion, combining the former blue seat and purple backrest.
Its conversion slider is removed. The green backrests sit along the cross bench’s right side and front,
then move with the long-bench control into the outer bed strip.
Old project fields and material selections for the removed deck, divider, lid, bearers and stops are discarded on load.

`cabinet.py` builds the left-side cabinet in furniture-local coordinates, before the common mirror/placement.
Its closed-door footprint starts at X = 1070, Y = 0–1000, narrowed by the vehicle envelope and wall support. With the
100mm rear gap it spans vehicle Y = 100–1100, restoring the original cabinet length. Length changes preserve the
rear end. The centre partition starts at `cabinet_rear_bay_length_mm` (560mm), measured from the open rear end,
following the requested 90mm rearward move. The owned folded chairs measure 600 × 700 × 100mm; their placement is
shown by the Stored gear live positions, with an open rear entrance. The forward bay uses the remaining space.
Rear upper shelves have 548mm clear length between panels, and the forward bay has 416mm clear length.
The cab end's outer face is at local Y = 1000, vehicle Y = 1100.

`cabinet_frame_thickness_mm` supplies the solid partitions, aisle frame, rear rails and rear upright from the same
sourced 12mm Tigerply stock; the bed retains its 18mm stock. The aisle frame retains its rounded openings and door
mounting posts. The centre and cab-end partitions are solid, scribed against the lining and vehicle fitting volume.
The aisle frame's top rail extends to the finished plywood underside, following its curve across the frame thickness.
It has no ceiling gap. Door openings and hinge elevations retain their existing heights; the top rail grows upward.
The centre panel has the wheel-arch notch with 3mm clearance and reaches the floor inside the arch. The cab-end
panel follows the plywood ceiling with the selected 3mm fitting gap. The `Rear upper panel` uses the same 12mm
stock at Y = 0–12, starting at `cabinet_rear_storage_height_mm` (730mm). Its outline is taken at the restrictive
rear face of the body/ceiling fitting volume and extruded square through the plywood thickness. Both faces have
the same outline: template and jigsaw the curves, without a compound bevel or sculpted edge. The opening widens
toward the cab, leaving fitting clearance behind the wall-side edge.
It closes the two upper rear compartments while leaving the full lower chair entrance open. Rear shelves start
at its inner face, Y = 12; they have rear-panel ledges with their outer ends scribed around the rear pillar.
There are no cabinet skins, full-height transverse rear frame, bottom threshold or lower rear crossbar.
The van floor is the bottom.

The lowest rear shelf supports start at `cabinet_rear_storage_height_mm` (730mm); shelf underside/top remain at
748/760mm. The forward middle shelf shares this elevation, so both bays' middle beams run at 730–790mm.
The upper rear shelf and three forward shelves remain. Shelf and door heights, front rail retaining lips and the
closed doors' 1070mm bed envelope are unchanged by the partition conversion.

The wall-side support is a separate `Wall supports` group: eight straight 12 × 60mm plywood rails and one narrow
transverse rear upright. Each bay has a top rail and matching lower, middle and upper rails.
Rails butt into the centre/cab-end partitions and rear upright rather than fastening to the vehicle. Each rail
is vertical rectangular stock, set inboard of the lining over its full height; higher rails sit further inward.
The rear lower crossbeam joins the rear upright to the centre partition at the forward bay's lower-rail height.
The rear chair compartment has no shelf at this level.
The lowest forward rail follows the raised shelf and clears the wheel arch by at least 3mm.
Its top is `cabinet_lower_rail_top_mm`: platform + foam + shelf clearance + member width − ledge height − shelf thickness.
The rear aisle frame has the same extra crossbeam; the wall-side rail now matches its height.

The rear upright stands on the floor immediately ahead of the rear pillar, at the start of the back lining.
It is a 12mm transverse plywood strip, nominally 60mm wide across X at each height, with its profile approximating
the wall. The rear shelf edges are notched around it. It leaves the rear chair-loading route clear.
The solid partitions are bounded by the lining/vehicle fitting volume; shelves end at their own rail's inboard face.
The old `cabinet_frame_step_height_mm` parameter is retained for saved projects, now labelled **Upper shelf reference
height**: the upper shelf rail remains halfway between this reference and the cabinet top.

The five 12mm shelves form a bonded assembly: glue shelves onto their ledges and glue ledges continuously to the
partitions, aisle frame and rear rails. The separate `Rail joint blocks` group contains sixteen vertical pine
blocks, one at each rail end, with a full rail-height face against the rail and an adjacent face against the
upright or partition. They use the same ready-made 18 × 18mm stock and are 60mm tall at defaults. Glue both faces;
predrill assembly screws through the plywood faces into the blocks, staggering perpendicular screws.
The five shelves have local corner notches around the blocks; transverse ledges stop 18mm short of the rail
face and wall ledges fit between the blocks. The blocks replace the two former 30mm wall corner cleats.
Two 60mm-high aisle cleats remain above the lowest forward shelf. The rear lower rail has matching end blocks;
the other rear rail blocks remain above the chair bay's 730mm clear height. Glue layers and assembly screws are not
modelled. The BoM includes an initial 250ml bottle
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
Cabinet shelves independently filters `/Campervan/Cabinet/Shelves`, covering all five shelf panels without their
support ledges. Like Cabinet backing, its saved setting survives Cabinet toggles; hiding Cabinet hides both.
It uses the same native labelled checkbox and keyboard behaviour described in the visibility guidance below.
The BOM records the sheet separately from plywood and uses its developed centre-curve length for the cut rectangle,
not the curved part's bounding-box depth. Confirm flute orientation and physical fit before cutting.
There is no top panel. Shelf fasteners are not modelled.

`cabinet_doors.py` makes nine 9mm plywood overlay doors. The four upper shelf openings each have a
bottom-hinged flap, intended to stop horizontally on two short chain restraints. The front bottom door retains its vertical hinge; its above-bed neighbour is bottom-hinged, with separate live controls. All edges overlap the openings by
15mm, with 12mm plan corner radii and 2mm face roundovers. The four upper flaps follow their respective bay widths.
The rear storage has an opposed bottom pair and one full-width bottom-hinged flap above the raised shelf rail. The aisle crossbeam divides
access without adding a shelf or rear crossbar. The rear chair-loading entrance remains 730mm high.

`cabinet_mattress_clearance_mm` places the front lower shelf top 10mm above the uncompressed mattress. At the
saved platform height 390mm and foam thickness 100mm, the shelf top is 500mm, the beam spans 470–530mm, and the
above-bed doors begin at 515mm. Clear access openings above that beam are 200mm high. The two front lower doors
are 374 × 440mm and 374 × 230mm; the bottom rear storage leaves are 252 × 440mm and the merged above-bed flap is
506 × 230mm.
These dimensions follow bed height, foam, clearance, stock sizes and overlay instead of fixed elevations.

The closed door fronts stay at X = `bed_width_mm` (1070mm), and backs at X = 1079. The aisle frame starts at
X = 1081, giving a 2mm gap for folded surface-mounted hinge leaves. `cabinet_aisle_x` is this actual front-face
coordinate, independent of bench skin thickness. Shelf and partition depths derive from it; the wall-side
support and flute-board lining retain their existing contour and position.

Door groups have hinge-centred origins and native plywood children, keeping cutting sizes independent of pose.
The four upper flaps have independent `cabinet_rear_upper_1_open_percent`, `cabinet_rear_upper_2_open_percent`,
`cabinet_cab_end_upper_1_open_percent` and `cabinet_cab_end_upper_2_open_percent` controls. Each rotates about Y
from 0 to −90 degrees before mirroring. The bottom rear pair has independent `cabinet_storage_aft_open_percent`
and `cabinet_storage_fore_open_percent` controls, rotating about Z by +90 and −90 degrees before mirroring.
The viewer reuses these tracks through the existing mirrored motion mechanism, without regeneration.
`cabinet_storage_upper_doors_open_percent` independently drops the above-bed rear flap about Y through −90 degrees before mirroring. The front bottom door
uses `cabinet_lower_doors_open_percent`; its raised neighbour uses `cabinet_front_upper_door_open_percent`.
The two above-bed drop-down flaps clear the flat uncompressed mattress in the fully made-up bed.
Bottom doors still require the bed stowed for physical access; the preview permits overlapping furniture.
Python saved-parameter loading and browser position loading migrate the former grouped upper/storage values to
their individual doors. Explicit individual values take precedence. Controls are grouped under Cabinet → Doors;
the subgroup headings describe controls rather than introducing extra assembly visibility paths.

The BoM includes eighteen Zenith 35mm fixed-pin butt hinges, nine Vanlifer Point push latches and two 3m packs of
Pinnacle 2mm double jack chain. The six drop-down flaps each require two chain restraints; cut lengths depend
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

`gear.py` adds a separate Stored gear assembly for the owner's folded solar-panel bag (830 × 760 × 80mm),
two folding chairs (600 × 700 × 100mm each), and a red-and-white chilly bin. These are owned reference objects, excluded from the cut list
and material purchases. The chair shapes approximate the supplied photograph: bent tubular frames, blue fabric,
wooden armrests and hinge fittings. All details stay inside the measured envelope; the bag's handle and webbing
are illustrative. No unfolded chair mechanism is modelled.

The chilly bin's measured closed envelope is 470mm wide × 280mm deep × 410mm high, excluding its handle. Rounded
loft sections taper the red body towards four corner feet. Blind side handgrips and a recessed front panel follow
the two owner photographs. A white rim, narrow lid seam, sloping rounded lid and raised top panel complete the
closed bin. The pivot discs and arched carry handle project beyond the measured envelope; their dimensions are
photo estimates. No internal capacity or lid-opening mechanism is modelled.

Under Stored gear → Chilly bin, width/depth/height are editable dimensions. Footprint-centre X/Y, bottom elevation
and yaw use the existing live pose controls. Handle → Handle folded rotates the handle around its side pivots:
0° upright to an estimated 135° folded forward. The default centre is X=750, Y=1050, Z=0 with 90° yaw, for initial
aisle placement. Native named groups provide individual visibility eyes and retain the Stored gear filter. These
position and handle controls save with the project and move without regeneration; size edits regenerate normally.

The bag starts upright across the rear gap, centred at X=750, Y=45, with its bottom at Z=0.
The chairs start edge-on in the aisle, centred at X=520/640, Y=600, with their feet at Z=0; these are temporary
comparison positions, not an approved storage arrangement. Each object has independent footprint-centre X/Y,
bottom elevation and rotation sliders under Stored gear, plus group visibility eyes and a Stored gear checkbox.
These use the existing live motion tracks: dragging moves geometry immediately, releasing saves the pose without
regeneration, and browser storage restores it after reloads. Translation sliders step by 1mm and rotation by 1°.
The cabinet and bed are unchanged. The owner confirms the real bag fits behind the existing bed with 20–30mm
spare clearance; the current estimated hatch shape conflicts with that reference above about Z=550 and remains
to be reconciled. This discrepancy is not evidence that the real bag needs more space.

`cushions.py` builds five foam blocks using the shared 100mm thickness.
The long seat is 600 × 1280; the fixed cross seat is 1070 × 580.
The orange backrest is 235 × 1280. Green is split into 235 × 580 along the cross-bench right side
and 235 × 700 along its front, upright in day mode. The split follows cross-bench depth as dimensions change.
At full conversion, orange fills X = 0–235, the long seat X = 235–835, and green X = 835–1070.
Both Cushions groups retain their existing +7mm X offset.
The long-bench slider moves the long seat and both backrests; the cross seat remains flat and stationary.
Each cushion is a centred native box in its own located Compound.
Cushions hold until 40%; by 80% the seat has shifted and the backrests have turned above the seats;
the final stage lowers the backrests. CAD and live tracks use the same sampled poses.
This previews manual repositioning; real cushion fit and intermediate handling remain visual checks.

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
absolute offset from that pose. Long-bed, cross-cushion and drawer sliders work without an animation timeline or regeneration.
Each bench slider also repositions its own cushions. Their tracks include position/angle keyframes from the same layout used
by CAD, so regeneration at an intermediate position preserves the preview. Translation and
rotation bases are stored separately for groups that use both.
The Python model uses the same poses and travel for geometry checks and future exports. Releasing a slider or drag
saves the accepted pose together through one `PATCH /api/v1/model/position`. Preview input also saves all positions to `campervan.positions`
localStorage. On page load or API session change, the controller restores the positions to the UI and API before
requesting regeneration. New geometry receives the latest selected positions.
Slider previews are combined into one animation-frame update using the latest values. Only changed motion
tracks are applied. Mannequin fitting, seat compression and pillow deformation are recalculated for bed or
mannequin changes; table, drawer, door and gear sliders leave them alone. A slider frame draws once. Releasing
a slider with the same value does not repeat the geometry update; its API save still occurs.
Moving the bed extension above 0% automatically selects the Stowed table pose in the same preview frame.
Releasing the bed slider saves both positions. Reloading with an extended bed also restores the table stowed.
If extending the bed stowed a mounted table, returning the slider to 0% restores Bench mount. A table that was
already stowed stays stowed. Browser storage remembers the automatic return across reloads; explicitly selecting
a table pose cancels that pending return.
Older project files and browser storage containing only the shared bed position initialize both bench sliders to that
position. Once separate positions are saved, they remain independent.

Direct manipulation uses `viewer-drag.ts` and the existing vehicle-aware piece picker. Unmodified primary drags on
the moving bed support/slats, drawer, cabinet doors and mounted bamboo leaves take precedence over camera orbit.
The 4px threshold preserves ordinary clicks and double-click cut-list navigation. Pointer capture owns the gesture;
Escape, lost capture, page blur, tab changes and geometry replacement restore the starting pose and automatic
table-return flag. Cyan surface/edge overlays are separate from persistent magenta selection and do not enter picking
queries. Alt-drag and the toolbar/context-menu orbit override (O) retain camera access on movable parts.

Bed dragging maps one full frame-travel distance to 40 percentage points. Completing all stages takes 2.5 times that
distance, across one or several drags. Release pauses; reversal retraces the existing keyframes. Drawer dragging follows
its world slider axis; hinged doors follow their projected hinge arc. Edge-on views hold the pose with a direction hint.
`table-drag.ts` resolves the actual arm pivots, offset and current tabletop envelope. The central 15% of either half-extent
retains world heading; heading freedom increases smoothly to full two-joint steering at 90%. Angles stay continuous during
dragging and normalise on release. The table stays at its current height and fold. A near-horizontal view holds the pose.

Gert removed interactive collision detection after it caused browser freezes. Dragging and sliders apply their
requested joint positions directly through the controller. No collision geometry, solver, acceleration dependency
or worker is loaded. Physical overlaps remain visible in the model. Releasing the primary button discards queued
drag input and saves the last accepted pose. Escape discards queued input and restores the pre-drag pose, including
the automatic table-return flag. The release listener uses window capture and movement also checks the button state.

Category visibility uses the viewer's actual leaf paths and `setStates`. Vehicle, Wooden floor, Slats, Cushions and
Cabinet preferences live in browser localStorage and are reapplied when geometry arrives. Slats covers the long bench's
fixed/moving slats and the fixed cross-bench slats.
Cushions covers both benches' foam groups; their sidebar eyes also work independently.
Wheel arches has its own checkbox beside Vehicle. Its visibility is independent of the containing Vehicle references
switch, so hiding Vehicle leaves the arches controlled by Wheel arches. Both arches' individual eye controls still
work; changing Vehicle preserves their settings. The checkbox preference uses the existing saved visibility paths.
Visible wheel arches have opaque faces and outlines and are excluded from See inside fading and click-through picking.
Wooden floor controls the top-level Finished floor plywood part, outside Vehicle references. Its thickness parameter
lives in its own matching group. The metal body floor and cab floor remain vehicle references; the plywood retains
its existing See inside fade and remains excluded from the cutting list.
The native labelled checkbox follows the [WAI-ARIA checkbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/)
(consulted 26 October 2026): a visible label and standard Space-key toggling, using the existing Visibility fieldset.

**See inside** adjusts vehicle opacity in the browser before the existing viewer paints each frame. Assembly paths
assign walls, doors, pillars and rear corners to their vehicle side; roofs and floors have vertical directions.
Perspective views calculate facing from each panel's transformed centre to the camera position. Orthographic views
use the camera orientation because their rays are parallel. Using orientation for perspective views incorrectly began
fading the ceiling when looking slightly down while the camera was still below it, switching off depth writing at
almost full opacity and exposing the roof bows abruptly.
Roof rails fade when either adjoining side faces the camera. `frontend/src/vehicle-fade.ts` keeps far-facing and
edge-on panels opaque, then smoothly fades faces to 5% opacity as their side turns toward the camera, and outlines
from 50% to 2%. Driver and passenger seats, including their supports, stay opaque from the sides, rear and above;
they fade to 25% opacity only when viewed from the front. Fully opaque panels use the opaque render pass and write
depth so their interior surfaces hide exterior faces. Fading panels use the transparent pass without writing depth;
opaque panels stay out of its camera-dependent sorting. This follows Three.js's
[opaque/transparent rendering behaviour](https://threejs.org/docs/pages/Material.html).
Side-window glass is tinted with 30% opacity (70% transparency), and the rear hatch glass is fully
transparent. See inside further fades the side glass on the near side. Visibility states and furniture materials
remain unchanged. The toggle defaults on and persists as `campervan.see-inside` in localStorage.
New geometry reattaches the effect. Turning it off makes the vehicle body and outlines 100% opaque while preserving
the side-window tint and clear rear glass; solid faces write depth. This is reapplied before each render so refreshes,
regenerated geometry and the OCP transparency control retain the selected See inside behaviour. Camera movement requires no regeneration,
API request or separate animation loop for this effect.

The cushion check verifies the five daytime bounds, full-bed coverage and no foam overlap at either endpoint.
It samples backrest turning and descent and compares live poses with regenerated CAD.
The cross-bench smoke check covers support alignment, the aft skin, slat spacing and cutting-list materials.
Long-bench conversion leaves the complete cross bench unchanged.

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

**Seated mannequin → Reset posture** fits a seated pose to the displayed long-seat cushion, allows estimated foam compression and clears
the calves past the bench edge. XYZ hip position, facing and joints remain adjustable with sliders. Ankle rotation
maintains the flat-foot orientation independently of the calves. Joint edits retain the chosen angles and adjust hip
height to put the soles on the floor; hip-height edits solve the legs instead. Recline sets the mean torso lean;
curvature sets the total bend along the arc, starting at the sacrum. The arc deforms the mesh's existing anatomical
shape. Leg and ankle posing compensates for pelvis rotation to retain floor contact. **Seated mannequin → Reset posture** starts with
20° recline and 35° curvature; saved manual poses remain unchanged.
Gaze compensation is shared between neck and head, maintaining
a downward laptop gaze without forcing the skull to counter-rotate against a backward-pointing neck.
Manual poses can exceed furniture clearances or available foam compression; the sidebar reports the detected limits.

`frontend/src/seat-cushion.ts` subdivides the displayed seat foam and dents its top beneath the posed skin, keeping the
bottom fixed. Compression is a visual approximation, capped at 55% of foam thickness. Hiding the person restores the
original geometry. This does not change the manufactured CAD cushion or simulate foam stiffness. The seated preview
is hidden during bed extension because it is not a lying-down pose.

The **Mannequin** group contains **Seated mannequin**, **Lying mannequin** and **Second lying mannequin** controls
and independent rig instances. Both lying people use the same measured body size, each fitted to its own pillow.
Each heading has the same eye control as CAD groups, with its own saved visibility preference. The main visibility
checkbox gates all three while preserving those preferences. Reset posture preserves the instance's visibility.
The seated instance shows only at 0% bed extension, enabled lying instances only at 100%; none show during travel.
Hidden lying instances do not deform their pillow or contribute feet-outside warnings. The lying posture uses the measured rig,
with extended legs, lightly crossed ankles and hands over the belly. It is visible at full bed extension only.
Head position follows the front pillow; adjustable pillow compression deforms its displayed mesh and restores it when
the person is hidden or seated. Contact fitting is approximate and needs visual inspection.
The pose reference is [PoseMyArt's lying crossed-legs pose](https://posemy.art/crossed-legs-poses/lying-crossed-legs-male-pose/666/).
The mannequin checkbox
lives alongside the other switches in **Visibility**. Pose and visibility retain the existing browser-storage key;
the lying posture uses its own storage key. Metadata refreshes reattach the same controls without resetting them.
Lying sliders adjust pillow-relative X/Y/Z offsets, body rotation, back lift/curvature, head tilt, hip/knee bend and
hand position above/along the belly. Reset posture restores only that instance.
Controls act directly on viewer geometry, persist in browser storage and do not regenerate CAD. The rig is detached
before OCP disposes its old scene and reattached afterwards. OCP bundles Three.js r184. FastAPI's
`/viewer-assets/js/shared-renderer.js` serves that locked bundle with its existing `THREE` namespace exported.
`frontend/src/renderer.ts` loads it once and supplies the app's Three.js constructors. Vite aliases bare `three`
imports to this module, including those inside the matching npm GLTFLoader and its utilities; dependency optimisation
excludes `three` so it cannot embed another runtime. The npm package supplies addon sources and TypeScript types.
The local Chrome build targets ES2022 for the renderer module's top-level await. App and OCP objects share constructors
and resource IDs. No second canvas or render loop is used. The mannequin is not included in CAD assemblies or exports.

## Materials and bill of materials

The CAD and Bill of materials tabs share the same model. Switching tabs leaves the viewer mounted at its existing
size so camera, visibility and live positions survive. The BOM groups uses by resolved supplier product ID,
with one price and availability record per product. Unspecified custom stock remains separate by role.
The Cut list overview draws furniture cutting parts and the floor plywood by assembly, using CAD names.
Plywood-thickness filters show material-specific layouts. `cutting_models.py` owns global algorithm/kerf/trim/grain,
per-material stock and saved results. The coordinator owns native solver subprocesses through `cutting_worker.py`,
receives improving layouts, and saves them with the project. Searches have no time limit; the page labels minimum
stock count as proven only when the solver reports it. Source fingerprints identify previous layouts after edits.
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

`data/project.json` saves parameters, material selections, measured overrides, ownership and manually confirmed
purchase quantities. It is versioned with the source. API reloads read it; edits through the API save it. Browser storage continues
owning camera, visibility and live-control preferences. Shelf ledge width and height are separate dimensions; shelf
bottoms remain on top of the ledges, whose bottoms stay aligned with the support-frame cross-beams.

The CAD worker builds the assembly once, then `cad/bom.py` collects local leaf cutting envelopes before publication.
Its explicit material mapping uses assembly paths and labels; update this mapping when changing the component tree.
Local leaf envelopes ignore parent motion, so opening the lid, sliding the bed or hiding parts does not alter quantities.
The worker returns cuts to the coordinator alongside successful regeneration. The BOM marks previous cuts as stale
while a new revision is pending or failed, and displays regeneration errors.

Plywood frames, skins, shelves and drawer panels, plus shelf ledges, guide ledges and slats,
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
Cabinet partitions and frames use their own 12mm role, sharing sheets with shelves and drawer.
The bed guides stand on edge, so their bearing width is the sheet thickness (18mm); their height follows the frames.
Both cabinet batten section dimensions come from the selected timber product, with measured overrides.

The cross-bench rear skin shares 9mm Tigerply Okoume-faced poplar-core plywood with the cabinet doors. Its material
role retains the `skins` ID and sets `cross_bench_skin_thickness_mm`. Projects selecting the former 4mm special-order
skin product migrate to the 9mm product. The long bench has no cab-end skin. Slat and long-bench frame positions use
their retained construction inset rather than skin thickness.


Sleeping pillows use the CC0 Poly Haven Throw Pillows 01 mesh (source/license beside frontend/src/pillow-mesh.json).
The viewer replaces CAD fitting envelopes with this cloth geometry, retaining the pose and visibility hierarchy.
Each measures 600 × 400 × 200mm throughout conversion.
Both lie across the cab end with centres 500mm apart. Their 600mm width envelopes overlap by 100mm
and overhang by 15mm each side at the 1070mm bed width.
The long-bench slider moves both pillows without changing their width or requiring regeneration.
CAD supplies visibility anchors only. Pillow geometry, support contact, rotations and conversion poses are owned by
frontend/src/pillows.ts and update in the browser without CAD regeneration.

`Laptop table` is a furniture-local assembly from `cad/table.py`, mirrored with the benches and cabinet. It contains
the `Bench mount` display group with live height, arm swivel, tabletop rotation, fold and mounting-offset controls.
The cabinet mount has been removed. The Show table selector switches between Bench mount and Stowed without
regeneration. Stowed shows the folded bamboo with the detached upright beside the arm beneath the tabletop.
The fixed furniture bracket and spacer remain on the bench. Stowed has its own live XYZ and facing controls;
the arm automatically points towards the displaced tabletop, flipping 180° when the offset changes sides.
The default aisle position is a preview pending a storage-location decision. The two display
poses share component builders and one mount offset. The duplicate stowed geometry is excluded from the cut
list and its bamboo leaves link to the working pose's cutting entries. Nominal packed thickness is 127mm
(50mm bamboo + 30mm fitting + 47mm arm); actual handles and the storage channel remain unmeasured.
The bench mount has a 92mm post and one 18mm spacer flush with the retracted moving frame. That moving frame is
trimmed 5mm at its cab end, leaving 3mm beside the mounting post throughout sideways travel. Slats stay unchanged.
The tabletop has two 700 × 250 × 25mm Prempanel bamboo leaves with rounded corners and perimeter round-over.
It folds from 500mm open width to a 250mm-wide, 50mm-thick stack. The long-edge hinge rotates above the fixed
leaf. Two selected Homer HOM006136 hinges appear in both table poses, with centres at 20% and 80% along
the seam. Their 114 × 42mm open footprint and 38mm pin width follow the supplier; thickness, pivot spacing,
barrel section, taper and countersunk holes are photo-based approximations. Each half follows its leaf
through the existing schematic fold. Nominal blind seats prevent metal/wood overlap without changing the
cutting silhouette. The hardware groups contribute no wood or extra hinge purchases to the cut list.
Actual recesses, joint gap and fixing details remain unmeasured. The two leaves have separate cutting profiles on
2200 × 600 × 25mm bamboo stock; the single mount spacer remains frame plywood. There is one Lagun kit. The current
official tabletop mount is 240 × 200mm with 30mm overall profile depth. Its 240mm axis follows the tabletop length.
Offset previews move the wood relative to the fixed mount; they do not add a sliding mechanism. Published
dimensions and unverified hardware details are recorded in [Lagun table](research/lagun-table.md).
