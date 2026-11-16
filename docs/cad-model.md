# CAD model conventions

Use millimetres, with X running from the vehicle's left/passenger side to its right/driver side, Y from the rear doors
toward the cab, and Z upwards. The rear opening at its side pillars is Y = 0; its centre bows rearward to Y = −120 at bed height.
Z = 0 is the finished plywood floor, with the vehicle floor approximately 18mm below. Vehicle coordinates and the right-hand-drive cab stay fixed.

The CAD page can display a registered scan through `cad-scan-reference.ts`, using the shared scan asset loader.
The source scan is aligned in metres, rotated by `cad_reference.rotation`, scaled to millimetres and translated by
`cad_reference.translation_mm`, with optional per-result browser translation overrides. The reference is detached
before OCP replaces geometry and reattached afterwards, outside CAD selection and furniture mirroring.

During comparison, `vehicle-fade.ts` applies a light-pink display tint and a base vehicle opacity, including the
wheel arches. See inside fading and click-through picking still apply to nearby panels and edges. Hiding the
reference restores original material colours and opacity while retaining the See inside setting.
The same checkbox switches reference meshes between `FrontSide` and `DoubleSide` rendering in `viewer.ts`.
The corrected interior scan's triangle winding points into the cabin (checked on floor, wall and roof patches), so
front-face rendering hides the near-side shell's backs while preserving interior-facing surfaces. This is face culling,
not named-panel fading: differently oriented or mixed-winding scans may hide wanted faces. Opacity changes and model
reloads preserve the mode; scan geometry is unchanged.
The existing native checkbox remains the single control, retaining its label and keyboard behaviour
([WAI checkbox guidance](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/)); the comparison help text describes its
effect on both models. Face visibility uses [Three.js Material.side](https://threejs.org/docs/pages/Material.html#side).
The vehicle uses its pre-experiment baseline geometry; no scan-fitted rear-floor increment or progress lines are active.

## Cross sections

The [photo-based cross-section authoring agreement](cross-section-authoring.md) preserves Gert's complete pillar
description, required nine-feature XY Z=991mm construction and numerical evidence method. Consult the complete
agreement and its photographs before editing that draft. Earlier rejected blue coordinates are not measurements.

**Scan comparison → Cross sections** provides three independent families: XZ intersections move along CAD Y
(rear to front), YZ intersections move along CAD X (left to right), and XY intersections move along CAD Z
(bottom to top). Each has its own position slider, number
field and blue-section dropdown. One green/blue opacity pair controls all planes. Negative rear stations remain
selected while a scan loads. Green is the raw section,
including disconnected fragments and gaps. It uses the full-resolution mesh when the result exposes one, otherwise
the displayed reference mesh. The same saved registration and browser translation offsets apply. Three 50mm triangle
indexes share the transformed vertex buffers, making the sections independent of CAD regeneration. Coplanar triangles do not acquire invented
internal cut edges.

The YZ position control is centre-based: 0 is the vehicle centreline, left is negative, right is positive, and the
range is exactly −800 to +800mm. It initially resets to 0 when adopting this convention. The centreline comes from
`cargo_width_mm / 2`; slider offsets convert to registered CAD X by adding that value. Geometry and stored `x_mm`
remain in their existing CAD frame, preserving recorded outlines and registration. All YZ station labels, numeric
inputs and saved inspection preferences use the centred convention. Out-of-range saved stations remain retained
but cannot be selected through this fixed-range control.
The YZ raw overlay cuts the scan independently at both signed slider positions, +X and −X. It does not mirror or
average green geometry. The green opacity control applies to both cuts; coincident centreline cuts are drawn once.

Blue outlines are authored through conversation. There is no automatic cleaning, point averaging, symmetry fitting
or initial shape generation. Gert chooses the station; the assistant uses scan evidence, recorded dimensions, vehicle
construction and Gert's estimates to propose separate straight and curved segments. Refinement continues before
Gert explicitly chooses **Record this section**. Window panes are flat; formed panels, hollow pillars and beams retain
their supported straight faces, sharp junctions, local blends and returns. Curves are not forced into one global spline.

`cross_sections.py` stores `data/cross-sections.json`, separate from generated geometry and scan assets. It is local
project data and needs backing up with the rest of `data/`. GET `/api/v1/cross-sections` reads the document, initially
`{version: 1, revision: 0, sections: []}` without creating a file. PUT `/api/v1/cross-sections/{id}` accepts
`{revision, section}` for an authored draft. POST `/api/v1/cross-sections/{id}/record` accepts `{revision}` to record it.
Writes reject stale revisions. A recorded section is immutable; a later revision uses a new draft ID and preserves
the approved original. The UI picks up authored changes without a viewer reload.

Each section records `id`, `label`, `plane`, its position, `scan_key`, `centre_x_mm`, `segments`, `state` and `notes`.
A segment is `line` with `end`, or `cubic` with `control1`, `control2` and `end`. XZ sections have `y_mm`,
`floor_z_mm` and `ceiling_z_mm`. Their points are
`[distance from centreline, Z]` in millimetres, with nonnegative distances. The half-outline starts at
`[0, floor_z_mm]`; its first segment is horizontal. Its last segment returns horizontally to `[0, ceiling_z_mm]`.
The authored half is the left/passenger side. It is mirrored onto the right by default; an explicit `opposite_segments`
outline can capture a real right/driver-side difference while retaining horizontal floor/ceiling constraints.

YZ sections have `x_mm` and an explicit `start`. Their points are signed `[Y, Z]` values, including negative Y for
the rear door. These paths may be open and are never reflected front-to-back. By default `mirror_x: true` displays
the same authored profile at `x_mm` and `2 * centre_x_mm - x_mm`, matching opposite-side rear profiles. Only the
profile at the inspection station is prominent; its counterpart stays faint. `mirror_x: false` authors one station.
An explicit `opposite_segments` and optional `opposite_start` can capture local trim differences on the other side;
otherwise it uses the primary profile. An authored departure from symmetry requires explanatory `notes`. Seats and
seatbelt trim are not forced to match. **Record pair** explicitly records a shared YZ pair, including its overrides.

XY sections have `z_mm` and an explicit `start`. Their points are `[centred X, Y]`, with signed X offsets
from `centre_x_mm`. They use a full authored outline without automatic mirroring or opposite outlines; optional
`details` use the same coordinates. Horizontal stations use the registered scan Z bounds.

Legacy records default to XZ, preserving their coordinates and shape. There is no point averaging or fitting in
any plane. Cubic segments are subdivided for display to 0.25mm chord tolerance, not fitted to the scan.

Separate authored objects, such as seat outlines, use `details`: each has a `label`, explicit `start` and `segments`.
These contours are independent of the body boundary and are not joined or closed automatically. At a paired YZ
station the same details appear on both sides unless `opposite_details` explicitly supplies alternatives; departures
require notes. XZ details use the same nonnegative half-section coordinates as the body. The renderer does not
generate object outlines from the scan. Any authorized numerical summary, such as averaging measured ceiling drops,
is recorded as an authoring decision rather than a general contour-cleaning operation.

The active blue section is 3px wide at the blue slider's opacity; inactive outlines are 2px wide at 60% of that opacity.
Green is 1.5px wide. One green and one blue opacity slider apply to all three planes,
independent of scan opacity/visibility and vehicle visibility. Position controls and blue-section dropdowns are
stacked compactly; Record appears beside the dropdown label only for a selected draft. Moving green does not change recorded geometry.
Selecting an authored section returns to its station. Lines are non-pickable overlays and survive CAD replacement.
Controls use native range/number inputs with visible units, following the relevant
[WAI slider guidance](https://www.w3.org/WAI/ARIA/apg/patterns/slider/). Thickness uses the existing Three.js
[LineMaterial](https://threejs.org/docs/pages/LineMaterial.html) and
[LineSegments2](https://threejs.org/docs/pages/LineSegments2.html) addons; these references do not establish a complete
accessibility audit.

## Current vehicle-modelling constraints

Both wheel arches are set to span CAD Y=275–1035mm (760mm long), shifted together 35mm rearward from Y=310–1070.
This is a rounded positional correction from the corrected scan comparison, not a new precise tape measurement:
the near-wall cap estimates centred around Y=648–654mm, and the lower rear-door reference was about Y=−33mm.
The original 310/1070mm tape distances were from the closed door, not CAD Y=0. Arch size, height and shape are unchanged.
The shared `arch_rear_offset_mm` drives both arches, floor cutouts and adjoining furniture clearances.
The wall-side span remains 760mm. `arch_inner_length_mm` uses 720mm, the upper end of the owner's approximate
700–720mm measurement including insulation. `wheel_arch_footprint` supplies one straight-sided base to the arch
solids and both mirrored floor notches. Its inner edge spans Y295–1015; the wall edge spans Y275–1035.
Equal 20mm end setbacks are a modelling estimate, not separately measured endpoints. The clear gap is 1205mm,
using the recorded inside-face AprilTag 2–3 measurement instead of the 1220mm catalogue reference. At 1500mm body
width, each arch projects inward 147.5mm. Plywood cutouts offset all three exposed footprint edges outward by
5mm, including perpendicular offsets at the diagonal ends. This leaves 1195mm of plywood between the cutouts.
The vehicle arches and metal floor use the original footprint without that plywood allowance.
Vehicle geometry takes priority over furniture fit. Furniture dimensions remain unchanged; the existing bench-frame
clearance conflict is deliberately unresolved. Furniture-fit gating and automatic furniture adjustments are disabled
with `FURNITURE_FIT_ENABLED = False` in `parameter_fit.py`; they do not block vehicle regeneration or constrain the form.
The switch controls clearance checks and automatic fit adjustments only. The complete interior, stored gear,
furniture motions and cutting parts remain enabled, using the saved dimensions even where clearances conflict.
Checks required to construct valid geometry remain active. The cache fingerprint includes this switch's module.

The vehicle is an interior-design reference, not a reproduction of scan irregularities. Treat the metal floor as
flat and horizontal; plywood rests on its high points. Impose left/right symmetry on the fixed body, matching
pillars, windows and wheel arches. Sidewalls and arch inner longitudinal edges are parallel to the centreline.
Corresponding seat-base-to-rear distances match; front and rear references are broadly parallel. The ceiling is
broadly parallel to the floor, with maximum clearance along the centreline. Seat fore-aft positions, heights and
backrest reclines remain independent. Retain real protrusions and modest blends; neither convenient primitives
unrelated to evidence nor raw noisy mesh/section lofts are acceptable fitted vehicle geometry.

Work one step at a time: rear edge, rear pillar bases, wheel-arch base footprints, sliding-door rear pillar
projections, front pillars, then a straight front plywood edge at the carpet boundary. The metal continues beneath
the carpet and seats; the plywood working boundary is distinct. Pillar bases are predominantly angled/wedge-like,
with slight blending. Arch bases can differ from crowns and wall-side spans from inner spans.

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
`parameter_fit.py` keeps furniture clearance checks disabled while vehicle modelling continues.
The retained constraints concern the cross-bench and cabinet shelf relationship; the superseded drawer and
bracket fit chain has been removed. Shape-validity checks still reject dimensions that cannot construct geometry.

The worker publishes the OCP display payload, exact measurement geometry and motion tracks before extracting cuts.
The coordinator saves geometry atomically to `.local/model-cache.json` and publishes it immediately, then updates
the bundle with cutting outlines when extraction finishes. Cutting failures do not fail the displayed CAD model.
It replays the saved geometry when the browser connects. Reuse depends on resolved geometry dimensions,
CAD/publishing source and CAD/viewer library versions.
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
│   ├── Storage box
│   │   ├── Wall-side hinge panel
│   │   ├── Aisle-side panel
│   │   ├── Rear end panel
│   │   ├── Centre support divider
│   │   └── Cab-end panel
│   ├── Lid hinges (photo-derived gas-assisted pair)
│   ├── Hinged lid
│   │   ├── Slotted plywood lid
│   │   ├── Fixed slats
│   │   └── Sliding bed
│   │       └── Sliding assembly
│   │           ├── Moving slats
│   │           └── Moving front slat support → Moving support frame
│   └── Cushions
│       ├── Long seat
│       ├── Wall backrest
├── Cross bench
│   ├── Fixed frame
│   │   ├── Wall-side frame
│   │   ├── Aisle frame
│   │   ├── Rear mounting frame
│   │   └── Fixed slats
│   └── Cushions
│       └── Cross seat
└── Cabinet
    ├── Lower module
    │   ├── Frames → front frame, cleats, arch bridge, catch blocks, rear jamb, cab-end bridge upright
    │   │   └── Module joint → four lower side rails and eight M5 × 90mm bolt sets
    │   ├── Skin → 9mm centre/cab-end panels
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
- Rear corners remain a provisional reference for fitting the plywood floor and later furniture. Each horizontal
  diagonal is straight and both sides share the same geometry. The base stations are Y40 and Y170; the latest
  small adjustment brings the base 5mm forward without changing the upper controls. The saved project currently
  has a Y225 upper carrier from the preceding experiment. Its lower/middle stations remain independent of it.
  `rear_corner_base` supplies the Y40/Y170 stations to the pillar and floor outlines. The plywood has its own
  clean fitting cutout: left X/Y points (150,0), (140,40), (45,170), then the shared arch footprint at X45,
  mirrored on the right. Those few straight edges clear the matched Z0 corner section. The metal floor
  and pillar geometry do not acquire this plywood allowance. The cutout is a fitting-template candidate: lower
  slice intersections mix the rising floor, brace and reconstruction blending, so full-thickness physical clearance
  has not been certified. Use the intended floor fit, not the scan's tiny teeth, to assess it.
  The camera is left in the owner's view. The discrete brace, lower return and any cutting clearance still need
  to be reconciled with the physical obstructions before calling this a verified cutting boundary. Surface-noise
  agreement and disappearance of the pink overlay are not the acceptance criterion for a plywood fit.
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
  is not assigned an invented material. The plywood has a straight rear edge at Y = 0. The metal floor follows the
  current flat local rear-edge reference, separately from the plywood cut line. The remaining floor uses
  unfinished baseline boundaries beyond the wheel arches. The arch cutouts use the same straight-sided footprint
  as the wheel-house reference solids, including the shorter measured inner-side span. They are exact left/right
  mirrors, with 5mm clearance from the CAD footprint. Scan irregularities are not copied into the cutting outline;
  physical base flare remains unmeasured.
  The rear-door opening's centre bow does not change the plywood outline.
  Its front edge reaches the greater of the nominal body length and the cross-bench front including the furniture
  setback (`cargo_length_mm + furniture_rear_gap_mm`): Y = 1960 at current dimensions. This supports the cab-end
  cross-bench feet at Z = 0. The vehicle floor reference retains its nominal body boundary.
- The 3mm ceiling sheet spans Y = 240–1660. Its underside is 1290 at centre and 1270 at its wall-side edges.
  Exposed side rails, rear header and three approximate bows are separate parts. The ceiling still uses concentric
  circular profiles for real sheet thickness. The bare roof estimate is 1347 above finished floor, with 55 crown.
- Wheel arches have a 760 × 147.5mm overall footprint and reach 280mm above the fitted floor. Their base reaches
  the vehicle floor at Z = −`floor_build_up_mm`, currently −18mm, giving a total height of 298mm. Extending the base
  preserves the crown height and the furniture clearances above Z = 0. The original wall-side endpoints were
  measured at 310–1070 from the closed rear door beside the pillar; current CAD endpoints are Y275–1035 after
  the documented datum correction. The shorter inner span is represented by straight diagonal ends, shared with
  the floor notches. Furniture retains its conservative rectangular clearance envelopes. The exact
  profile and insulated height remain unmeasured. Floor and furniture cutouts follow the shared arch parameters.

The direct arch and rubber-seal measurements confirm the 140mm front arch gap. Relative to the lower opening,
the arch rear is 900mm aft and its front is 140mm aft. The closed-door reference and rear-opening datum remain
distinct; their offset and the rear pillar's local straight/flare segments still need reconciling. See the
[dimension audit](research/nv200/dimension-audit.md).

Walls, pillars, roof and floors remain translucent, with named assembly groups and visibility controls.
Measurements describe the existing bed at 390 slat-top height; the design's platform height remains independently
editable and is not automatically changed to match it.

`bench.py` builds one bottomless long-bench plywood storage box. Its two longitudinal walls, two end panels
and transverse centre support divider stand directly on the finished van floor. The divider stays centred on the
bench length; the forward-set rear end panel makes the two clear storage bays unequal. Before its independent inward offset, the wall-side panel's outer face is flush with the rear
ends of the slats. All panel tops are lowered 18mm to carry the slotted plywood lid without
raising the slat surface. The floor closes the bottom; there is no separate plywood bottom. Panels remain solid.
The old drawer, guide ledges, moving plywood aisle frame and angle brackets are removed. The separate cross bench
retains its existing geometry and wall-side arch-relative support datum.

`sliding_bed.py` builds an 18mm slotted plywood lid without the stationary wall strip. Its main body is
582 × 1280mm, with its aisle edge recessed 18mm to X604 throughout. Both upper hinge rails are shortened 18mm
at their gas-spring ends to match, so the former lid tabs are removed. Pivot positions and kinematics are unchanged.
Seven 400 × 50mm slots preserve the former comb ledges;
the wall-side band is 100mm and the aisle band is 82mm. The lid remains at Z354–372.
Seven 82 × 50mm top rebates accommodate the horizontal bracket flanges. Each matches its ventilation slot's
width and extends from that slot to the aisle edge for easier routing. They are 3mm deep, providing 1mm
clearance above 2mm steel and retaining 15mm of plywood below. Only a narrow 3mm edge relief passes through
the lid for each vertical flange, using the same 50mm width.
Both slat sets extend 100mm wallward into the space freed by the removed stationary strip. Fixed slats are
567mm long (X45–612 retracted), shortened by 10mm at the aisle end. Moving slats are 559mm (X45–604), butting
against the frame's inner face. Both sets retain the 5mm wall-end trim and square ends.
Both sets lose a further 18mm at the wall end for an 18 × 50mm cushion-retaining rail on top of the lid.
The trimmed rail spans X22–40, Y68–1280 and Z372–422, matching the sliding frame's top height and leaving a 5mm gap
before the slat ends. It belongs to `Hinged lid`, follows its motion, and uses frame plywood in the BOM.
At the rear/wall corner, the first fixed slat has a 40 × 40mm, 45° corner cut, leaving 40mm of its 80mm end.
The lid plywood follows that same cut plane (lid-local X + Y = 68mm at the saved dimensions).
The wall-side rail has a square rear end at Y68 across its full 18mm thickness, avoiding a sharp angled point.
Both side rails have 10mm-radius top end corners, rounded through their 18mm thickness: four corners in total.
`bed_slat_rear_setback_mm` is zero; extension travel is
448mm to preserve the 1070mm bed width. The box walls keep their existing positions.
The rear end panel is placed at local Y155–173 beneath the first complete solid lid rib beyond the rear corner;
its linkage follows, with the upper rail at Y173–203 beneath the solid Y155–275 band. The panel's world rear face
is Y255, 30mm beyond the modelled rear pillar. Slot bounds drive both lid cutting and this mounting position.
The wall-side longitudinal panel also starts at Y155, flush with that rear end panel, and is 1125mm long.
Both longitudinal walls have two 40mm-wide, 40mm-deep top notches, with 5mm clearance on each side of the
lift rails and 10mm extra depth over the previous cuts. They follow the linkage mounts at Y168–208 and Y1227–1267.

`bed_lift.py` builds two gas-assisted four-bar mechanisms on the end-panel inside faces, replacing the three
schematic barrels. Published A600/C270/D340/E420 dimensions and photo-estimated pivots define a rigid-link
circle-intersection solver shared by CAD and browser animation. Using D340 as the inferred opening stop gives
approximately 34.1 degrees, 79.6mm aisleward rear-edge movement and 7.3mm final rear-edge lift. The rear edge
does not descend below its closed height along this fitted path. This is a photo-derived working model; actual
pivots, mounting holes, spring stroke, capacity and stops need checking against the hardware. See the
[dimension record and current limits](research/bed-lift-photo-model.md).

`bed_inward_offset_mm` is a shared assembly placement for both benches. The accepted 24mm aisleward offset
moves the box, fixed and moving slats, moving front rail, legs, hinge preview and both benches' cushions together.
The table's mounting bracket and working pose follow the same offset; its independent stowed pose is unchanged.
The box's wall-side outer face is local X46 (world X1454 at the 1500mm vehicle datum). The former box-only setting
migrates to this shared bed setting without changing its value. Extension travel is now 448mm,
so the complete sleeping platform retains its 1070mm width, translated towards the aisle rather than narrowed.
The cabinet front follows the bed offset to retain its former nominal face gap. The rear corner, front edge and wheel arch remain
separate fitting work; the accepted middle-pillar placement does not certify those clearances.

At the saved 390mm slat-top height, the lid underside and box rim are Z354. The moving support is a single 18mm
plywood frame, from the floor to Z422. Its lower top member is 50mm high (Z322–372),
with 60mm-wide integral legs and a 25mm-radius open-bottom cutout matching the cross-bench frame construction.
`bed_moving_rail_height_mm` controls the top member; leg width and opening radius use the existing frame parameters.
The frame spans X604–622 and Y0–1178, shortened 102mm at the cab end for the Lagun mounting area.
Its integral cab-end leg moves with the new end. It has no hinge notches.
Metal legs and spacer blocks are removed; the metal-leg purchasing role and diameter parameter are retired.
Stationary box-wall notches remain.
The frame's upper 50mm is continuous, with a smooth outer face. Seven 84 × 22mm inside-face grooves are routed
8mm deep at Z370–392, with 2mm clearance above/below and beside each fixed slat, and nominal 2mm corner radii.
They leave 10mm of outer plywood. The fixed ends enter 8mm and meet the groove backs when retracted; the groove
ceilings retain the sliding frame after 2mm of vertical take-up during lifting. This is geometric retention, not a
load rating. The lid rebates retain their positions. Blind routing is separate from the nesting outline.
One Carinya 50 × 50 × 40 × 2mm angle joins each moving slat underside to the frame's wall-side face.
The vertical flanges remain face-mounted, with no rail recesses. Their lower edges at Z322 are flush
with the narrower rail's lower edge. The rail remains 18mm plywood and the brackets retain their original positions.
The seven angle leaves share the sliding transform and use the existing eight-pack catalogue product.
`Slat angle brackets` has its own hardware material role ahead of the parent frame-plywood assignment, so the
BOM counts actual brackets and excludes them from sheet nesting. Hole centres are illustrative; match actual
fixings to the supplied hardware and 18mm timber before drilling.

`Hinged lid` owns the plywood and the retained slat/slider geometry. `Lid hinges` owns the two mechanisms,
including separately animated upper rails, arms and telescoping springs. Opening storage retracts the bed;
extending it closes the lid and stows the table. Opening storage keeps the selected table pose unless retracting
an extended bed restores a table previously stowed by conversion. The blue cushion follows the lid's linkage
transform as its placement carrier; the orange cushion stays upright and lifts just enough to clear blue.
Actual foam forces and wall/mesh clearance remain unverified.

The Lagun bracket attaches to the long box's aisle-facing wall at its cab end. An 18 × 92 × 170mm plywood pad
spaces it out from the box face; the pad and bracket occupy Y1183–1275, leaving 5mm beside the sliding frame
and 5mm before the box end. Including the shared 24mm bed offset, the bracket origin is X638/Y1229 with its
normal towards the aisle. The upright's native X627–665 envelope leaves about 14mm from the fixed slats over
the fitted lid stroke. This is an envelope check of the existing illustrative hardware, not a fabrication tolerance.
The arm's existing world heading and live controls are retained. The detached Stowed pose is unchanged.

Box panels, slotted lid and moving support frame share frame plywood. The lift pair remains a provisional
hardware requirement. Superseded leg, drawer, guide and bracket roles are retired when loading saved projects; purchase
records with ownership or spending remain available as unused stock. Obsolete controls are dropped on load.
`table_included` remains a saved purchasing choice independent of CAD visibility and live pose.
The coordinator automatically starts missing/stale cutting layouts for all sourced or confirmed stock when the current
cuts or their inputs change, and on application startup. Search ownership is independent of the selected frontend tab.
Model status includes `cutting_revision`; BOM purchase tables refresh when layouts publish new results, using the existing
draft-preserving refresh and polling. Current complete layouts are reused; unchanged paused/failed searches remain manual.
The frontend masks excluded assembly roots in the viewer without changing the saved leaf-visibility rules.
Re-including removes that mask, restoring the previous eye settings; disabled eyes retain their state while excluded.

`cross_bench.py` builds a fixed full-width platform at X = 0–1070, Y = 1280–1860 by default. Two fore/aft
18mm plywood frames have open-bottom rounded cutouts, 60mm legs and top rails. A third 18mm rear-facing frame fits
between their inner faces and retains its solid 92mm-wide aisle-side post; the Lagun mount has moved to the long box.
At the default 400mm platform height,
the frame tops are Z = 382; the 18mm slats bear directly on them. There is no divider, deck, sliding assembly,
cab-end skin, hinged lid, brackets or stop plates.

`cross_bench_overhang_mm` defaults to 200mm at the aisle slat ends. The wall-side frame retains its former
arch-relative support position, following the shared `Parameters.cross_bench_support_x_mm` datum;
the aisle frame occupies X = 852–870. Both run Y = 1280–1860. At the saved 1500mm cargo width and 1205mm arch gap,
the rear mounting frame occupies X = 175.5–852, Y = 1280–1298 from floor to rail top, with an open-bottom rounded
cutout and a 60mm wall-side leg. These are bench-local coordinates before the shared 24mm inward offset.
`cross_bench_layout.py` supplies the frame and table mounting datums. The removed rear skin's thickness parameter
and material role are retired. Toilet/tray hardware and frame joints remain unmodelled; CAD does not establish load capacity.

Four 1070mm-long 80 × 18mm stock slats run across the van, directly over both support rails, matching the previous
extended cross bench's four moving rows. The first starts at Y = 1280; the last finishes at Y = 1860. Three equal
86⅔mm ventilation gaps fill the 580mm depth. The junction to the long bench's last extended moving slat remains
90mm, with no added empty margin at either end of the cross bench. Slat count stays four; their gaps follow the shared
stock width and cross-bench depth.
The rearmost slat (nearest the long bench) is 50mm shorter at its aisle end: 1020mm at the default bed width.
Its exposed rear/aisle corner has a 40mm plan radius at the default 80mm slat width, carried through the full
18mm thickness. The other three slats remain full length; supporting frames and cushions retain their dimensions.
The cross bench has one full-width fixed cushion, combining the former blue seat and purple backrest.
Its conversion slider is removed. The former green backrests are removed; the long bench's taller orange backrest
and blue seat now fill the complete sleeping width.
Old project fields and material selections for the removed deck, divider, lid, bearers and stops are discarded on load.

`cabinet.py` builds a panel-and-cleat cabinet in two modules. Both retain Frames, Skin, Shelves and Doors
visibility groups. Skin now contains supporting 9mm Tigerply Okoume end panels and the centre divider, using the
existing Bunnings product. It is not 3mm cladding over a separate timber skeleton. The front frame, shelf cleats,
joining rails and hardware blocks use the existing 40 × 18mm pine. The arch bridge remains 90 × 18mm pine.

Middle and cab-end panels have full-depth, jigsaw-scribed profiles against the actual side, pillars and finished
ceiling. The rear upper panel follows the same contour and extends down to Z730. The lower rear timber jamb has
no plywood facing or bottom sill. Its original chair-loading target was 230 × 730mm; narrowing the cabinet
reduces the clear width, and this target is not enforced while furniture-clearance checking is disabled. There are no rear
ladders, raked rear posts, return frames or uprights inside shelf bays. No full wall-facing back or top is added.
The van closes the wall-facing back. Front edges of supporting panels butt behind the front frame; no skin
landing grooves are needed. Fix panel faces into the adjoining timber, not screws into thin plywood edges.

`cabinet_layout.py` supplies the real fitting volumes and shelf/door datums. Its lower-back datum locates only the
end uprights and arch bridge; it does not truncate the plywood or prescribe another back frame. `scribed_sheet`
intersects face/mid-plane templates and extrudes one constant-thickness outline. Each square-cut shelf cleat is
fitted across its whole height and the combined thickness of the receiving panel and timber, leaving 1mm wall
clearance. This keeps its full mating face on the supporting panel rather than sticking past the panel contour.

Five 6mm shelves retain their levels. The lowest forward shelf follows platform + foam + mattress clearance;
the middle shelf tops/interface are at storage height + frame width (770mm), and the upper level follows the
available module height. Shelves butt behind the front frame and between the 9mm panels. Both ends of each shelf
have bearing on face-mounted cleats or joining-rail shelf seats. Their wall edges remain scribed to the van.
There are no internal post cutouts. The front frame ties the panels together and stiffens the front shelf edge.

The middle panel has an open-bottom wheel-arch clearance extending to the bridge top, avoiding dangling panel
feet or a closed slot around the bridge. The bridge sits directly beneath the lowest forward shelf cleats,
supporting them and the rear portion of the divider without separate bearing blocks. Its height follows the
shelf and cleat dimensions while retaining at least 3mm wheel-arch clearance. The bridge butts between the rear
timber jamb and a floor-standing 40 × 18mm cab-end upright. The new upright sits against the cab-end panel's inner
face and ends beneath its lower shelf cleat, providing a timber attachment for the beam and bearing for the cleat.
This establishes an explicit support arrangement, not a verified complete cabinet load rating.

Four pairs of straight transverse side joining rails retain the detachable joint. Lower rails have shallow
shelf seats with solid lands around their two bolts; upper rails bear directly on those lands. Eight M5 × 90mm
countersunk screw envelopes remain side-only. There are no front/rear longitudinal joining rails. The existing
20mm lower panel guides and 0.5mm seam clearance remain at the middle/cab-end sides. The upper rear panel extends
below the joint beside the lower rear header; this is an unglued locating overlap. Keep every detachable mating
surface unglued. Module rails and fasteners remain in the Module joint subgroup under Frames.

The cabinet front face follows `bed_width_mm + bed_inward_offset_mm + 6mm` in both its frame layout and door
construction. With the accepted 24mm bed offset, its front moves 24mm towards the wall, reducing cabinet depth
while keeping the wall-side scribed profile. Panels, shelves, front framing, doors and their hardware follow the
same face position. This restores the previous 6mm nominal wood-face gap; hinge barrels consume approximately
5.7mm of it where their heights and fore–aft positions overlap the bed. The rear jamb continues to use the fitted
wall limit rather than moving outwards to preserve the former 230mm opening.

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

`cushions.py` builds three foam blocks using the shared 100mm thickness.
The long seat is 600 × 1280; the fixed cross seat is 1070 × 580.
The orange backrest is 470 × 1280, retaining its seated bottom elevation and 100mm thickness. Its height follows
the difference between sleeping width and long-seat width. The former two green backrests are removed.
At full conversion, orange fills X = 0–470 and the long seat X = 470–1070, meeting without overlap or a gap.
Both Cushions groups retain their existing +7mm X offset.
The long-bench slider moves the long seat and orange backrest; the cross seat remains flat and stationary.
Each cushion is a centred native box in its own located Compound.
Cushions hold until 40%; by 80% the seat has shifted and the backrest has turned above the seats;
the final stage lowers the backrest. CAD and live tracks use the same sampled poses.
This previews manual repositioning; real cushion fit and intermediate handling remain visual checks.
Storage-lid tracks act on a `Foam` assembly parent, while conversion tracks retain the cushion parent groups.
The `Foam / Core` mesh keeps OCP's native box-centring offset untouched; this offset must not be replaced by
absolute storage tracks, even at the closed pose. Deformation reads the core mesh, while pillow bounds use its parent.
The blue child uses the lid delta conjugated through its closed cushion pose, including the 7mm wall offset.
`cushion-foam.ts` performs one direct geometry update per pose. Blue keeps its slab shape and is uniformly
compressed in width between the two rails, with 1mm side clearance. During storage opening it follows the lid
and loses at most 3mm of thickness. Orange remains upright, rises as a whole, and compresses at most 3mm at
its lower edge. Every orange vertex is constrained above blue's planar upper surface with 0.5mm clearance;
the linear half-space condition also separates the triangle interiors. No gravity, velocities, material solver,
iterations or settling animation remain. `foam-surface.ts` supplies a rounded, seam-smoothed display mesh
with 25mm XY and 10mm Z spacing. Dimensions in CAD and purchasing data remain nominal.
The fixed cross-bench blue cushion uses the same rounded foam skin and display settings, at its existing size
and placement. It does not participate in the long bench's storage-lid fitting.
CAD child poses and browser keyframes share `lid_cushion_locations`; all XYZ rotation components are specified.
Manufactured foam dimensions and the manual bed-conversion sequence remain unchanged.

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
absolute offset from that pose. Long-bed, storage-lid and cross-cushion sliders work without an animation timeline or regeneration.
Each bench slider also repositions its own cushions. Their tracks include position/angle keyframes from the same layout used
by CAD, so regeneration at an intermediate position preserves the preview. Translation and
rotation bases are stored separately for groups that use both.
The Python model uses the same poses and travel for geometry checks and future exports. Releasing a slider or drag
saves the accepted pose together through one `PATCH /api/v1/model/position`. Preview input also saves all positions to `campervan.positions`
localStorage. On page load or API session change, the controller restores the positions to the UI and API before
requesting regeneration. New geometry receives the latest selected positions.
Slider previews are combined into one animation-frame update using the latest values. Only changed motion
tracks are applied. Mannequin fitting, seat compression and pillow deformation are recalculated for bed or
mannequin changes; table, storage-lid, door and gear sliders leave them alone. A slider frame draws once. Releasing
a slider with the same value does not repeat the geometry update; its API save still occurs.
Moving the bed extension above 0% automatically selects the Stowed table pose in the same preview frame.
Releasing the bed slider saves both positions. Reloading with an extended bed also restores the table stowed.
If extending the bed stowed a mounted table, returning the slider to 0% restores Bench mount. A table that was
already stowed stays stowed. Browser storage remembers the automatic return across reloads; explicitly selecting
a table pose cancels that pending return.
Older project files and browser storage containing only the shared bed position initialize both bench sliders to that
position. Once separate positions are saved, they remain independent.

Direct manipulation uses `viewer-drag.ts` and the existing vehicle-aware piece picker. Unmodified primary drags on
the moving bed slats/legs, storage lid, cabinet doors and mounted tabletop leaves take precedence over camera orbit.
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

`frontend/src/cushion-foam.ts` retains the original seated-preview indentation field beneath the posed
mannequin, keeping the cushion bottom fixed and capping the visual dent at 55% of thickness. Lid fitting
is a separate direct pose calculation in the same single mesh update, with no simulation or settling.
Disposal restores the CAD mesh. Picking IDs and component visibility are preserved.
These effects do not change manufactured CAD dimensions. Mannequins are hidden
during storage opening; their saved visibility preferences return when the lid closes.

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

The CAD worker builds the assembly once and returns viewer geometry before `cad/bom.py` collects cutting envelopes.
Its explicit material mapping uses assembly paths and labels; update this mapping when changing the component tree.
Local leaf envelopes ignore parent motion, so opening the lid, sliding the bed or hiding parts does not alter quantities.
The worker returns cuts separately, tagged by the same model fingerprint. The coordinator accepts them only for
the current revision and then starts layout optimisation. The BOM marks previous cuts as stale until extraction
finishes, independently of CAD readiness, and reports cutting failures separately. Local geometry wrappers are
detached before copying so extracting one piece does not copy its parent assembly.

Plywood box panels, cross-bench frames, skins, cabinet panels and shelves have sheet assignments.
All bed slats share slat stock; the moving support frame uses frame plywood. One lid-lift pair has an explicit
whole-item quantity; its schematic components do not enter the wood cut list. Metal bed legs are removed.
Product selection, fixings and hardware strength remain unresolved.

Other furniture leaves are listed as unassigned. Vehicle references and cushions are excluded.
Cut rectangles are not a nesting plan: they exclude saw kerf, grain constraints and waste. Sheet and stock-length
purchase quantities require a cutting layout; roles selecting the same product may share stock.

Bed box panels and cross-bench support frames use the selected 18mm plywood.
Cabinet front frame, cleats, joining rails and catch blocks share 40 × 18mm pine; the bridge uses 90 × 18mm pine.
The cabinet uses 9mm scribed supporting panels and 6mm door/shelf plywood. All three cross-bench frames share 18mm frame plywood.
Plywood parts retain their scribed profiles and openings in the cut list. The moving front support is cut from 18mm frame plywood.
Cabinet stock sections come from their selected timber products, with measured overrides.

The nine cabinet doors use 6mm bbi Redline plywood from Mitre 10, SKU 303849, listed at $33.47 per
1200 × 1195mm panel on 1 November 2026. The cutting stock uses the product title's 1195mm width rather than
the specification table's rounded 1200mm. Wellington branch stock remains unconfirmed. Door hinges use
through-fixings in the 6mm faces; their fixing details still depend on the physical hinges.

The former cross-bench rear skin and separate table backing are removed. Saved `skins` material selections and
`cross_bench_skin_thickness_mm` are discarded on load. The long bench has no cab-end skin. Slat and long-bench frame
positions retain their construction inset.


Sleeping pillows use the CC0 Poly Haven Throw Pillows 01 mesh (source/license beside frontend/src/pillow-mesh.json).
The viewer replaces CAD fitting envelopes with this cloth geometry, retaining the pose and visibility hierarchy.
Each measures 600 × 400 × 200mm throughout conversion.
Both lie across the cab end with centres 500mm apart. Their 600mm width envelopes overlap by 100mm
and overhang by 15mm each side at the 1070mm bed width.
The long-bench slider moves both pillows without changing their width or requiring regeneration.
The rear black pillow also follows blue's storage-lid transform and its small thickness compression.
In couch mode it clears orange's aisle face with up to 15mm of local cloth flattening; deeper overlap moves
the pillow as a whole. Both adjustments run along blue's top plane, preserving its resting clearance.
Each pose starts from the original cloth vertices, with no simulation or settling. Bed conversion and
the lying mannequins' pillow indentations retain their existing behavior.
CAD supplies visibility anchors only. Pillow geometry, support contact, rotations and conversion poses are owned by
frontend/src/pillows.ts and update in the browser without CAD regeneration.

`Laptop table` is a furniture-local assembly from `cad/table.py`, mirrored with the benches and cabinet. It contains
the `Bench mount` display group with live height, arm swivel, tabletop rotation, fold and mounting-offset controls.
The cabinet mount has been removed. The Show table selector switches between Bench mount and Stowed without
regeneration. Stowed shows the folded pine with the detached upright beside the arm beneath the tabletop.
The fixed furniture bracket remains on the cross-bench rear frame. Stowed has its own live XYZ and facing controls;
the arm automatically points towards the displaced tabletop, flipping 180° when the offset changes sides.
The default aisle position is a preview pending a storage-location decision. The two display
poses share component builders and one mount offset. The duplicate stowed geometry is excluded from the cut
list and its tabletop leaves link to the working pose's cutting entries. Nominal packed thickness is 113mm
(36mm pine + 30mm fitting + 47mm arm); actual handles and the storage channel remain unmeasured.
The bench mount attaches to the long box's aisle wall on an 18 × 92 × 170mm plywood pad. The moving frame is
shortened 102mm at its cab end, leaving 5mm beside the mounting pad throughout sideways travel. Slats stay unchanged.
The tabletop has two 600 × 200 × 18mm Specrite pine leaves with rounded corners and perimeter round-over.
It folds from 400mm open width to a 200mm-wide, 36mm-thick stack. The long-edge hinge rotates above the fixed
leaf. Two selected Homer HOM006136 hinges appear in both table poses, with centres at 20% and 80% along
the seam. Their 114 × 42mm open footprint and 38mm pin width follow the supplier; thickness, pivot spacing,
barrel section, taper and countersunk holes are photo-based approximations. Each half follows its leaf
through the existing schematic fold. Nominal blind seats prevent metal/wood overlap without changing the
cutting silhouette. The hardware groups contribute no wood or extra hinge purchases to the cut list.
Actual recesses, joint gap and fixing details remain unmeasured. The two leaves have separate cutting profiles on
1200 × 600 × 18mm pine stock; the rear mounting frame shares frame plywood. There is one Lagun kit. The current
official tabletop mount is 240 × 200mm with 30mm overall profile depth. Its 240mm axis follows the tabletop length.
Offset previews move the wood relative to the fixed mount; they do not add a sliding mechanism. Published
dimensions and unverified hardware details are recorded in [Lagun table](research/lagun-table.md).


### Perspective field of view

The installed OCP camera starts at 22° vertical FOV. `viewer-camera.ts` stores an optional `fov` with the existing
camera state; older saved poses retain 22°. The CAD Camera slider changes `pCamera.fov` and calls
`updateProjectionMatrix()` without changing position, target or orbit distance. Geometry reloads create a fresh
native camera, so the helper reapplies the stored FOV before saving the restored pose. Orthographic views retain
the perspective angle for the next switch; scan camera persistence uses the same helper.

Renderer contract: [Three.js PerspectiveCamera](https://threejs.org/docs/pages/PerspectiveCamera.html).

### Human camera navigation

`viewer-human.ts` owns the Human view toolbar toggle, context-menu command and H shortcut. It disables native
orbit input while active. In the installed renderer, orbit mode ignores the quaternion argument of
`setCameraLocationSettings`; position and an aligned look target therefore move together for translation, and the
target rotates around the stationary eye for mouse look. Perspective switching restores the eye position after
the native zoom conversion. Forward/back uses the normalized XY projection of the camera's forward direction,
preserving height and movement speed when tilted. Strafe follows the camera orientation; Shift+Up/Down uses world Z.
Movement is 500 mm/s, measured by animation-frame elapsed time. Human view requests pointer lock directly from the
button/H gesture and activates on `pointerlockchange`. Locked `mousemove` uses `movementX/Y`, allowing unlimited
turning with a hidden cursor. Escape/browser unlock, focus loss and window blur exit and clear held keys.
Geometry replacement and leaving the CAD tab exit the mode; camera persistence remains shared with orbit mode.
Pointer capture/release follows the [W3C Pointer Lock specification](https://w3c.github.io/pointerlock/).

The toggle uses a stable accessible name and `aria-pressed` following the
[WAI button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/). Controls appear while active; navigation keys
are scoped to the focused viewport, editable controls retain their normal input, and Escape exits without trapping focus.
