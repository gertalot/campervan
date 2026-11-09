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

The sidebar's **Cabinet side · Left | Right** radio group selects the arrangement, with vehicle sides defined facing
the windscreen. It sits alongside the live controls and applies immediately. The right-side choice reflects furniture,
the table, stored gear and mannequins through the cargo centreline while leaving the vehicle and floor fixed. The side
is saved in localStorage and works in the static site; the former checkbox preference is migrated on first load.
Reflection parents preserve native named paths, local slider
tracks, picking and highlights. Hinge dragging accounts for reflected rotation axes; table steering uses the actual
parent basis. Mannequins fit and cushions deform in the original coordinates before their displays reflect together.
CAD edge ribbons render double-sided in one pass: their screen-space winding stays unchanged when the display
parent reflects, whereas Three.js reverses face culling for a negative world determinant. The GPU picker's separate
edge shader needs the same setting; otherwise visible mirrored edges disappear from its ID buffer and the picker
returns the face beneath them. `layout-mirror.ts` configures that shader just before the native pick-buffer render,
after OCP has lazily created its materials. This adapter uses the pinned renderer's `_renderPickBuffer` hook; retain
that integration when upgrading the renderer. Its depth testing and automatic vertex/edge/face priorities stay intact.
Solid face materials retain their existing sidedness.
The two door openings have different offsets, so inspect fit against the fixed vehicle on the selected side.

Cut-list galleries and whole sheet drawings use a reflected face view with readable labels. Reflecting an entire
sheet preserves the saved nesting, kerf, offcuts and cut sequence; through-cut outlines can be viewed from the reverse
face. Floor-only drawings stay unchanged. Cut-list drawings and saved SVGs identify the selected cabinet side.
Native CAD/STEP exports and Python geometry retain their saved orientation; changing the cabinet side does not
regenerate or modify the model or cutting results.
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
│   │   └── Rear hatch (Door envelope, Window glass)
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
    ├── Lower module
    │   ├── Frames → front frame, cleats, arch bridge, bearing/catch blocks, rear jamb
    │   │   └── Module joint → four lower side rails and eight M5 × 90mm bolt sets
    │   ├── Skin → 9mm centre/cab-end panels and rear loading jamb panel
    │   ├── Shelves → lower forward and both middle shelves
    │   └── Doors → lower flaps, storage pair and fixed hardware
    └── Upper module
        ├── Frames → front frame, shelf cleats and catch blocks
        │   └── Module joint → four upper side rails
        ├── Skin → 9mm centre/cab-end/rear supporting panels
        ├── Shelves → both upper shelves
        └── Doors → Rear/Cab-end upper 1/2 and fixed hardware
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
  The **Doors closed (%)** slider also raises/lowers this hatch. The `Rear hatch` group pivots about X at the
  opening crown, Y = upper forward rake and Z = opening height + sill offset. A negative 90° rotation at 0% swings
  its lower edge aft and upwards; 100% is the closed pose. The hinge location and 90° travel are visual estimates.
  CAD construction and absolute viewer rotation keyframes share `rear_hatch_angle`; slider adjustments need no regeneration.
  See inside rotates the hatch's fade direction with that hinge; the fixed surround retains its rear-facing fade.
  The existing native slider keeps its label, 0–100 range and keyboard behavior; its description now names both
  sliding doors and the rear hatch, following the [W3C slider guidance](https://www.w3.org/WAI/ARIA/apg/patterns/slider/).
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

`drawer_included` and `table_included` are saved 0/1 purchasing choices, separate from visibility and live poses.
They default to included for existing saved designs. Both assemblies always remain in the CAD model and hierarchy.
The cached bundle retains all cuts; `active_cuts` filters the manufacturing list and `active_roles` filters dedicated
stock/hardware requirements. `Coordinator.cuts` supplies the current filtered list to all local consumers; static
exports apply the same filter. Changing inclusion saves via `/api/v1/build-options` without rebuilding or republishing
geometry. Inclusion does not enter the geometry fingerprint. Existing cutting searches stop when inclusion changes,
and saved layout fingerprints determine which results still apply. All dimensions and selections remain saved;
purchases with recorded ownership or spending remain as unused stock with no future requirement.
The coordinator automatically starts missing/stale cutting layouts for all sourced or confirmed stock when the current
cuts or their inputs change, and on application startup. Search ownership is independent of the selected frontend tab.
Model status includes `cutting_revision`; BOM purchase tables refresh when layouts publish new results, using the existing
draft-preserving refresh and polling. Current complete layouts are reused; unchanged paused/failed searches remain manual.
The frontend masks excluded assembly roots in the viewer without changing the saved leaf-visibility rules.
Re-including removes that mask, restoring the previous eye settings; disabled eyes retain their state while excluded.

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

`cabinet.py` builds a panel-and-cleat cabinet in two modules. Both retain Frames, Skin, Shelves and Doors
visibility groups. Skin now contains supporting 9mm Tigerply Okoume end panels and the centre divider, using the
existing Bunnings product. It is not 3mm cladding over a separate timber skeleton. The front frame, shelf cleats,
joining rails and hardware blocks use the existing 40 × 18mm pine. The arch bridge remains 90 × 18mm pine.

Middle and cab-end panels have full-depth, jigsaw-scribed profiles against the actual side, pillars and finished
ceiling. The rear upper panel follows the same contour and extends down to Z730. A lower rear jamb panel and
reinforcing timber leave at least 230 × 730mm chair-loading clearance, without a bottom sill. There are no rear
ladders, raked rear posts, return frames or uprights inside shelf bays. No full wall-facing back or top is added.
The van closes the wall-facing back. Front edges of supporting panels butt behind the front frame; no skin
landing grooves are needed. Fix panel faces into the adjoining timber, not screws into thin plywood edges.

`cabinet_layout.py` supplies the real fitting volumes and shelf/door datums. Its lower-back datum locates only the
rear jamb and arch bridge; it does not truncate the plywood or prescribe another back frame. `scribed_sheet`
intersects face/mid-plane templates and extrudes one constant-thickness outline. Each square-cut shelf cleat is
fitted across its whole height and the combined thickness of the receiving panel and timber, leaving 1mm wall
clearance. This keeps its full mating face on the supporting panel rather than sticking past the panel contour.

Five 6mm shelves retain their levels. The lowest forward shelf follows platform + foam + mattress clearance;
the middle shelf tops/interface are at storage height + frame width (770mm), and the upper level follows the
available module height. Shelves butt behind the front frame and between the 9mm panels. Both ends of each shelf
have bearing on face-mounted cleats or joining-rail shelf seats. Their wall edges remain scribed to the van.
There are no internal post cutouts. The front frame ties the panels together and stiffens the front shelf edge.

The middle panel has an open-bottom wheel-arch clearance extending to the bridge top, avoiding dangling panel
feet or a closed slot around the bridge. Two face-mounted blocks transfer its rear portion onto the bridge.
The bridge meets the floor-supported rear timber jamb at one end and rests on a cab-end panel bearing block at
the other. Its end block and divider blocks attach through the 9mm panel faces into the timber. This establishes
an explicit support arrangement, not a verified complete cabinet load rating.

Four pairs of straight transverse side joining rails retain the detachable joint. Lower rails have shallow
shelf seats with solid lands around their two bolts; upper rails bear directly on those lands. Eight M5 × 90mm
countersunk screw envelopes remain side-only. There are no front/rear longitudinal joining rails. The existing
20mm lower panel guides and 0.5mm seam clearance remain at the middle/cab-end sides. The upper rear panel extends
below the joint beside the lower rear header; this is an unglued locating overlap. Keep every detachable mating
surface unglued. Module rails and fasteners remain in the Module joint subgroup under Frames.

`cabinet_doors.py` retains nine 6mm inset doors, two face-mounted hinge envelopes per door, finger holes and roller
catches. Six doors are drop-down flaps; the lowest rear pair and lowest forward door have vertical hinges. Fixed
hinges through-bolt to the full 18mm front frame. Moving leaves and catch keepers bolt through plywood faces.
Local front-edge shelf clearances accommodate hinge lands and nuts; no fixing goes into a 6mm plywood edge.
Catch plates mount beneath square 40 × 40 × 18mm blocks attached to the front headers. Fixed and moving hardware
follow Doors visibility; timber mounting blocks follow Frames. Door controls and motion paths remain unchanged.

The BOM retains eighteen hinges, nine catch sets, eight module screw sets, 36 M3 × 25 frame bolt sets, 54 M3 × 12
door/keeper sets, ninety backing washers and eighteen catch-block screws. Hardware geometry is still an estimated
mounting envelope, not a manufacturer drilling template. Flap chains, cleat fixing holes and vehicle anchorage
hardware remain to detail. Glue/clamp shelf cleats and supporting panels on the bench, dry-fit the module in the
van, then complete the fixed joints. The four existing visibility filters and material role IDs remain stable.

The Visibility section provides independent Cabinet shelves, Cabinet doors, Cabinet skin and Cabinet frames
checkboxes, each covering both modules. Hinges follow Doors, including their stationary leaves. These are local
viewer controls and require no server roundtrip or regeneration. Their saved preferences survive hiding/showing
the whole cabinet. Parameter-group eye buttons use the same actual component paths.

Loading an old project replaces the cabinet's obsolete 3mm skin selection with the existing 9mm Bunnings product
and discards retired cabinet ledge, overlay and module-section fields. The cut list uses the timber stock sections,
native sheet profiles and the new module structure. This initial model does not establish finished joinery,
anchorage capacity, a weight saving or a fabrication-ready cutting schedule. Check the actual model visually,
then template the vehicle and confirm physical hinge/fastener dimensions before fabrication. See
[the construction rationale](research/cabinet-redesign.md).

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
the moving bed support/slats, drawer, cabinet doors and mounted tabletop leaves take precedence over camera orbit.
The 4px threshold preserves ordinary clicks and double-click cut-list navigation. Pointer capture owns the gesture;
Escape, lost capture, page blur, tab changes and geometry replacement restore the starting pose and automatic
table-return flag. `viewer-highlight.ts` supplies the same translucent surface tint and edge outline for persistent
magenta selection and cyan drag previews. Active fill opacity is 0.42; hover opacity is 0.13. Overlay objects are
marked and excluded from ray picking, and their materials and generated edges are disposed when removed.
Alt-drag and the toolbar/context-menu orbit override (O) retain camera access on movable parts.

The renderer's existing `activeTool` state owns measurement mode. A state subscription cancels pending drags and
selection clicks, removes our magenta/cyan overlays, closes the piece menu and disables the piece-action buttons.
This removes only our selection; it does not call the renderer's measurement-selection reset. While a tool is active,
our click, double-click, context-menu, Escape and drag handlers yield to the renderer. Camera navigation remains
available. Ending measurement restores normal piece actions with no selected piece or pending click suppression.
Entering measurement resets the renderer's topology filter to All. The existing picker chooses vertices, edges and
faces from cursor proximity; no shape-type menu or mode-specific filter shortcuts are needed.
Unavailable toolbar actions use native disabled buttons, following the
[WAI-ARIA button guidance](https://www.w3.org/WAI/ARIA/apg/patterns/button/). The event guards leave measurement events
untouched: [event propagation](https://developer.mozilla.org/en-US/docs/Web/API/Event/stopPropagation) and
[pointer capture](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events#pointer_capture) apply only to gestures
owned by our direct-manipulation handlers.

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

Landmark resizing continues the nearest end interval for points outside the measured height range. Float rounding
can put crown vertices just above the measured maximum; those vertices retain the upper-body scale instead of
falling through to the lower-leg scale and denting the head.

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
The mannequin checkbox lives alongside the other switches in **Visibility**. All three poses, their individual
visibility and the group checkbox save under `mannequins` in `data/project.json`. The API returns that configuration
with the parameters, and `PUT /api/v1/model/mannequins` updates it without regenerating geometry. Existing browser
poses migrate into projects without saved mannequin settings. Metadata refreshes reattach the same controls.
Lying sliders adjust pillow-relative X/Y/Z offsets, body rotation, back lift/curvature, head tilt, hip/knee bend and
hand position above/along the belly. Reset posture restores only that instance.
Static snapshots include the saved configuration. Static startup applies it before loading the model; visitor changes
stay in browser storage, scoped to the published configuration so a later configuration replaces old starting poses.
Controls act directly on viewer geometry and do not regenerate CAD. The rig is detached
before OCP disposes its old scene and reattached afterwards. OCP bundles Three.js r184. FastAPI's
`/viewer-assets/js/shared-renderer.js` serves that locked bundle with its existing `THREE` namespace exported.
`frontend/src/renderer.ts` loads it once and supplies the app's Three.js constructors. Vite aliases bare `three`
imports to this module, including those inside the matching npm GLTFLoader and its utilities; dependency optimisation
excludes `three` so it cannot embed another runtime. The npm package supplies addon sources and TypeScript types.
The local Chrome build targets ES2022 for the renderer module's top-level await. App and OCP objects share constructors
and resource IDs. No second canvas or render loop is used. The mannequin is outside the CAD assembly and cutting list;
static sites bundle the GLB and saved poses for display.

## Materials and bill of materials

The CAD and Bill of materials tabs share the same model. Switching tabs leaves the viewer mounted at its existing
size so camera, visibility and live positions survive. The BOM groups uses by resolved supplier product ID,
with one price and availability record per product. Unspecified custom stock remains separate by role.
The Cut list overview draws furniture cutting parts and the floor plywood by assembly, using CAD names.
Plywood-thickness filters show material-specific layouts. `cutting_models.py` owns global algorithm/kerf/trim/grain,
per-material stock and saved results. The coordinator owns native solver subprocesses through `cutting_worker.py`,
receives improving layouts, and saves them with the project. Searches have no time limit; the page labels minimum
stock count as proven only when the solver reports it. Source fingerprints identify previous layouts after edits.
Fingerprints ignore redundant collinear profile points and wire ordering so identical CAD profiles generated on
different operating systems reuse their saved layouts, including in GitHub Pages exports. Older fingerprints are
upgraded only when the saved inputs match the current stock, settings, dimensions and sampled shapes.
Each product expands into component uses and a combined cut list grouped by dimensions. Hardware quantities are
summed across all uses before rounding up to purchase packs. Sheet and timber purchase quantities come from current,
complete saved cutting layouts. Existing unsourced slats use their modelled cut-piece count. Required includes owned
stock; ownership reduces the remaining purchase quantity. Sidebar links retain their role-based URLs and expand the
containing product, highlighting the specific use. Expanded product rows survive status refreshes during the session.

`src/campervan/materials.json` is the product catalogue: exact supplier links, variant dimensions in mm, specifications,
unit/pack prices in NZD including GST, availability notes and the date checked. Catalogue entries are candidates,
not an assertion of local stock or suitability for every part. The BOM is read-only; sourced products are the default selections and their section/thickness dimensions drive
the model. Loading a project fills missing selections from these defaults while preserving explicit choices,
custom stock and measured overrides. Updates go through catalogue edits and the existing materials API.
`materials.py` maps material roles to existing CAD parameters and resolves selected products plus optional measured
section/thickness overrides. Custom stock uses the existing parameter value. Listed sheet sizes and stock lengths
constrain cutting, not the van layout. Reused slats start as already owned custom stock.

`data/project.json` saves parameters, material selections, measured overrides, ownership, manually confirmed purchase
quantities and mannequin settings. It is versioned with the source. API reloads read it; edits through the API save it.
Browser storage retains camera, category visibility and live-control preferences. Shelf ledge width and height are separate dimensions; shelf
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
Cabinet front frame, cleats, joining rails and catch blocks share 40 × 18mm pine; the bridge uses 90 × 18mm pine.
The cabinet uses 9mm scribed supporting panels and 6mm door/shelf plywood. The cross-bench rear skin remains 9mm plywood;
the drawer uses 12mm sheets. Plywood parts retain their scribed profiles and openings in the cut list.
The bed guides stand on edge, so their bearing width is the sheet thickness (18mm); their height follows the frames.
Cabinet stock sections come from their selected timber products, with measured overrides.

The nine cabinet doors use 6mm bbi Redline plywood from Mitre 10, SKU 303849, listed at $33.47 per
1200 × 1195mm panel on 1 November 2026. The cutting stock uses the product title's 1195mm width rather than
the specification table's rounded 1200mm. Wellington branch stock remains unconfirmed. Door hinges use
through-fixings in the 6mm faces; their fixing details still depend on the physical hinges.

The cross-bench rear skin uses 9mm Tigerply Okoume-faced poplar-core plywood independently of cabinet stock. Its material
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
regeneration. Stowed shows the folded pine with the detached upright beside the arm beneath the tabletop.
The fixed furniture bracket and spacer remain on the bench. Stowed has its own live XYZ and facing controls;
the arm automatically points towards the displaced tabletop, flipping 180° when the offset changes sides.
The default aisle position is a preview pending a storage-location decision. The two display
poses share component builders and one mount offset. The duplicate stowed geometry is excluded from the cut
list and its tabletop leaves link to the working pose's cutting entries. Nominal packed thickness is 113mm
(36mm pine + 30mm fitting + 47mm arm); actual handles and the storage channel remain unmeasured.
The bench mount has a 92mm post and one 18mm spacer flush with the retracted moving frame. That moving frame is
trimmed 5mm at its cab end, leaving 3mm beside the mounting post throughout sideways travel. Slats stay unchanged.
The tabletop has two 700 × 250 × 18mm Specrite pine leaves with rounded corners and perimeter round-over.
It folds from 500mm open width to a 250mm-wide, 36mm-thick stack. The long-edge hinge rotates above the fixed
leaf. Two selected Homer HOM006136 hinges appear in both table poses, with centres at 20% and 80% along
the seam. Their 114 × 42mm open footprint and 38mm pin width follow the supplier; thickness, pivot spacing,
barrel section, taper and countersunk holes are photo-based approximations. Each half follows its leaf
through the existing schematic fold. Nominal blind seats prevent metal/wood overlap without changing the
cutting silhouette. The hardware groups contribute no wood or extra hinge purchases to the cut list.
Actual recesses, joint gap and fixing details remain unmeasured. The two leaves have separate cutting profiles on
1200 × 600 × 18mm pine stock; the single mount spacer remains frame plywood. There is one Lagun kit. The current
official tabletop mount is 240 × 200mm with 30mm overall profile depth. Its 240mm axis follows the tabletop length.
Offset previews move the wood relative to the fixed mount; they do not add a sliding mechanism. Published
dimensions and unverified hardware details are recorded in [Lagun table](research/lagun-table.md).
