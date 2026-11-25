# CAD model conventions

Use millimetres, with X running from the vehicle's left/passenger side to its right/driver side, Y from the rear doors
toward the cab, and Z upwards. The rear opening at its side pillars is Y = 0; its centre bows rearward to Y = −120 at bed height.
Z = 0 is the fixed scan-registration datum. The finished plywood floor is now Z20; the vehicle floor remains Z−22. Vehicle coordinates and the right-hand-drive cab stay fixed.

The CAD page can display a registered scan through `cad-scan-reference.ts`, using the shared scan asset loader.
The source scan is aligned in metres, rotated by `cad_reference.rotation`, scaled to millimetres and translated by
`cad_reference.translation_mm`. The reference is detached
before OCP replaces geometry and reattached afterwards, outside CAD selection and furniture mirroring.

The active reference `nv200-photo-20261120` uses the 249,842-triangle export from
`data/scanruler/nv200-250k-doors-colour.scanruler`. The rear and left sliding door panels were repaired before
reduction. The PLY stores the recovered photographic texture as RGB on its 126,585 vertices.
The export converts ScanRuler millimetres to metres and preserves the inward-facing triangle order used by See inside.
It retains the 1205mm wheel-arch-gap calibration and the rigid registration to the earlier interior scan,
including its approximately centimetre-scale rear-datum uncertainty. The local scan run and the versioned
`data/scan-reference/` use the same mesh and pose for the live CAD viewer, fitting calculations and static exports.

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
the displayed reference mesh. The same saved CAD registration applies. Three 50mm triangle
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
solids and vehicle metal-floor notches. The existing plywood panels have their own measured envelope. Its inner edge spans Y295–1015; the wall edge spans Y275–1035.
Equal 20mm end setbacks are a modelling estimate, not separately measured endpoints. The clear gap is 1205mm,
using the recorded inside-face AprilTag 2–3 measurement instead of the 1220mm catalogue reference. At 1500mm body
width, each arch projects inward 147.5mm. The existing rear plywood panel is 1200mm wide, centred in the 1205mm gap.
Its 2.5mm nominal clearance on each side comes from the owner’s measured panel width, not a new scan scribe.
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
drawer, bracket and cushion geometry is mirrored with them. The shared rear setback is 80mm from the opening at the pillars after the 20mm rearward furniture refit.
The closed hatch has 110mm centreline clearance behind that bed edge.

The cabinet adds `cabinet_rear_inset_mm` to that shared setback; its fitting envelopes and roof landmarks use the
same resulting `cabinet_rear_y_mm` datum. The cabinet inset is zero, aligning its rear face with the bed sliding frame at Y80. Its 980mm length puts
the cab end at Y1060; the 550mm rear bay keeps the middle divider at Y630. Other furniture retains the shared setback.

Ten wooden cabinet parts have additional square-edged scan scribes. `scan_scribe_data.py` records the
measured cut regions from the registered photographic scan at this placement; `scan_scribing.py` applies them
after the original rebates and bores. Assembly placements are captured before reparenting children, preserving
the hinge origins of the cabinet doors. The scan triangles spanning each complete stock thickness are projected and
buffered, leaving at least 3mm to the observed surface. Wall-side/roof offcuts are removed while retaining the
inboard joint land. Hardware and the van mesh are unchanged. Cutting outlines include the scribed timber as well
as plywood. These profiles are tied to this scan, registration and panel placement; regenerate them if those change.
The gap is relative to the reconstructed surface, not a claim of 3mm real-world positioning accuracy.
The owner identified the hanging ceiling feature above the middle front stile as a removable Velcro strap. It is
excluded from structural fitting, restoring the straight stile/rail tops and removing its cut from the divider.

The upper front frame carries a separate scribed ceiling filler above its long top rail, between world Y325 and
Y1060. It uses the cabinet-frame material and 40×18mm stock, with its bottom on the flat rail and its top following
the plywood ceiling with at least 3mm nominal scan clearance. The plywood profile is continued across the removable
strap. The existing rear roof-beam infill stays separate. The filler is included in the frame BOM and cutting outline.

The reflection preserves native named assemblies, colours and visibility paths. Local translations reflect in X;
rotations retain their X angle and reverse their Y/Z angles. `viewer.py` applies the same conversion to every live
motion track, including absolute cushion keyframes, so live poses and regenerated CAD agree. This is native CAD
geometry, not a display-only reflection. The coordinate examples in the furniture construction sections below refer
to the generators' floor-relative local coordinates, before this shared reflection and placement. Add the shared
`floor_surface_z_mm` (currently 20mm) for vehicle/world heights.

The floor, both benches, the table (including its fixed mount) and stored gear share `floor_surface_z_mm`.
Floor-relative furniture and gear heights keep their meaning; the registered vehicle, ceiling and scan stay fixed.
Cabinet body/ceiling fitting volumes and scan cutters are translated into that raised-floor construction frame.
The 20mm subfloor raises the furniture by 10mm relative to the previous 10mm ribs. The square tops of
boxes 5 and 7 stay at world Z1258. The wheel-arch rails and the rear roof and pillar scribe curves also use
vehicle heights. The upper shelf rises 5mm in the van and the joint between modules rises 10mm.
The seated mannequin solves its feet and hip height in the floor frame, then returns to world coordinates; lying
mannequins and live furniture/gear motion inherit their parents' floor placement. The camera stays unchanged.

The bench converts wheel-arch and rear-corner positions to furniture-local coordinates before constructing supports.
The long bench's wall-side hinge panel and centre divider have simple rectangular wheel-arch notches with
at least 5mm nominal clearance. The wall notch spans world Y259–1040 up to Z293; the divider notch reaches
world X158 and Z293. Below Z136, the wall notch follows a smooth door-seal relief, replacing the rectangular Y1165 step. The
quadratic profile follows the seal and adjacent black trim across the full panel thickness, with at least 5mm
nominal clearance; it is sampled at 5mm height intervals (less than 0.01mm curve deviation). The wheel-arch and
upper trim edges retain their 90° corners; no wavy scan contours or
extra holes are transferred. The scan is unchanged. The rear end panel remains rectangular. Its rear face aligns with the end of the angled lid corner cut
(currently world Y168–186, 81mm rearwards of its previous position). The wall-side panel extends to meet it;
the rear lift and its matching clearances follow this shared datum. The central lid ventilation slots leave a solid
rib over the rear wall and the complete lift rail. The original aisle-edge bracket rebates remain full width
so the moving brackets are not obstructed.
`scan_scribing.py` applies the same full-thickness projection cuts to both furniture assemblies, with their own
placement offsets and opposite inboard joint lands. Cutting profiles and automatic fitting margins use these shapes.

The cabinet reflects and translates body/ceiling fitting volumes into that coordinate system before scribing,
so its mirrored placement fits the actual left side. Wheel-arch cutouts remain symmetric.
A perfect furniture reflection does not imply an asymmetric vehicle is mirrored.

The sidebar's **Cabinet side · Left | Right** radio group selects the arrangement, with vehicle sides defined facing
the windscreen. It sits alongside the live controls and applies immediately. The right-side choice reflects furniture,
the table, stored gear and mannequins through the cargo centreline. The fitted floor uses the cabinet-right
arrangement. Its seam follows the left rib beneath the benches. Its hatch stays over the pump. The side
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
│   ├── Bench-side panel
│   ├── Aisle panel
│   ├── Pine rib frame
│   ├── Floor insulation (twelve fixed infill pieces)
│   └── Fuel pump hatch → Lift-out plywood lid, Lift-out EPS
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
│   │   ├── Front support frame
│   │   └── Fixed slats
│   └── Cushions
│       └── Cross seat
└── Cabinet
    ├── Lower module
    │   ├── Frames → posts, rails, cleats and catch blocks
    │   │   └── Module fasteners → six M6 × 90mm hex bolt sets
    │   ├── Skin → 4mm backs, centre divider and cab-end panel
    │   ├── Shelves → two cab-end shelves
    │   └── Doors → three doors, fixed cover and hardware
    └── Upper module
        ├── Frames → posts, rails, cleats, divider stops and catch blocks
        ├── Skin → 4mm backs, centre dividers and end panels
        ├── Shelves → inset shelves
        └── Doors → four flaps, fixed front and hardware
```

The [Japanese 2017 NV200 body research](research/nv200/README.md) records the actual van variant, Nissan dimensions,
source limitations and a measurement plan. `body.py` builds an adjustable interior envelope using native edges, faces
and lofted shells. These are reference surfaces without invented material thickness, not fabrication-ready bodywork.

`cab.py` extends the vehicle floor forward from `body_length_mm` at Z = −`floor_build_up_mm` (currently −22mm),
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
  `rear_corner_base` supplies the Y40/Y170 stations to the pillar and floor outlines. The two plywood panels follow a separate symmetric profile fitted
  to the registered scan at Z8–20. The rear pockets widen around each pillar, reach X45 on the left
  and X1455 on the right, then narrow around the rear of each wheel arch. Template these edges
  against the van before cutting.
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
- The two lengthwise 12mm plywood floor panels occupy Z8…20 and Y−15…2015. Their joint follows the
  bench-side longitudinal rib. The shared 45 × 20mm pine frame occupies Z−12…8, giving 10mm clearance
  above the vehicle-floor reference at Z−22. The top panels retain the 1450mm door wings and widen
  behind the wheel arches. Furniture and stored gear share the finished-floor plane.

- The 3mm ceiling sheet spans Y = 240–1660. Its underside is 1290 at centre and 1270 at its wall-side edges.
  Exposed side rails, rear header and three approximate bows are separate parts. The ceiling still uses concentric
  circular profiles for real sheet thickness. The bare roof estimate is 1347 above finished floor, with 55 crown.
- Wheel arches have a 760 × 147.5mm overall footprint and reach 280mm above the fitted floor. Their base reaches
  the vehicle floor at Z = −`floor_build_up_mm`, currently −22mm, giving a total height of 302mm. Extending the base
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
The trimmed rail spans X22–40, Y88–1280 and Z372–422, matching the sliding frame's top height and leaving a 5mm gap
before the slat ends. It belongs to `Hinged lid`, follows its motion, and uses frame plywood in the BOM.
At the rear/wall corner, the first fixed slat has a 60 × 60mm, 45° corner cut, leaving 20mm of its 80mm end.
The lid plywood follows that same cut plane (lid-local X + Y = 88mm at the saved dimensions).
The wall-side rail has a square rear end at Y88 across its full 18mm thickness, avoiding a sharp angled point.
Both side rails have 10mm-radius top end corners, rounded through their 18mm thickness: four corners in total.
`bed_slat_rear_setback_mm` is zero; extension travel is
470mm: the outside rail faces span X22–1092, giving 1070mm overall and 1034mm between their 18mm faces.
The rear end panel spans local Y88–106, aligning its rear face with the end of the angled lid cut. The rear lift's
upper rail follows at Y106–136. Central ventilation slots retain the complete Y88–136 rib (the first slot now starts
at Y136), keeping its bolt seats solid. The original aisle-edge bracket rebates retain their nominal bounds.
The wall-side longitudinal panel also starts at Y88, flush with the rear panel, and is 1192mm long.
At the current placement the rear panel spans world Y168–186, 81mm rearwards of its previous position. The scan
clearance is checked against the actual pillar rather than the nominal rear-corner radius. The common pillar
chamfer is vehicle-fixed at construction X+Y=214mm; moving the furniture changes its local depth and all attached
support, hinge, retainer and access-hole datums together. Arch and seal contours retain their vehicle coordinates;
the centre-divider cutter's thin Y band follows its new world Y711–729 position. Both benches move 20mm rearward,
with cross-cushion rear Y1360. The cabinet moves by the same amount, leaving a 300mm corner gap. Floor, scan,
solar bag, chairs and chilly bin remain fixed. The solar bag has 7mm to the nearest rear bench edge and 95mm to
the inset rear panel. Stowed table world position stays explicit; the bench-mounted bracket follows the bench.
Both longitudinal walls have two 40mm-wide, 40mm-deep top notches, with 5mm clearance on each side of the
lift rails and 10mm extra depth over the previous cuts. They follow the linkage mounts at Y101–141 and Y1227–1267.

`bed_lift.py` builds two gas-assisted four-bar mechanisms on the end-panel inside faces, replacing the three
schematic barrels. Published A600/C270/D340/E420 dimensions and photo-estimated pivots define a rigid-link
circle-intersection solver shared by CAD and browser animation. Using D340 as the inferred opening stop gives
approximately 34.1 degrees, 79.6mm aisleward rear-edge movement and 7.3mm final rear-edge lift. The rear edge
does not descend below its closed height along this fitted path. This is a photo-derived working model; actual
pivots, mounting holes, spring stroke, capacity and stops need checking against the hardware. See the
[dimension record and current limits](research/bed-lift-photo-model.md).

Each lift has seven illustrative M6 through-bolts, spaced clear of the modelled pivots: four 40mm zinc-plated
coach bolts in the fixed rail and three 35mm Pinnacle Black Ruspert Allen-drive round-head bolts through the
solid plywood lid and moving rail. The mounting steel is 6.7mm thick. Six lid counterbores are provisionally
18mm diameter × 6mm deep, leaving 12mm of the 18mm lid. A 16 × 1.6mm washer sits beneath each head. The fixed
slats have full-depth access openings, including edge openings where necessary; they do not carry the bolt heads
and need independent attachment to the lid. Their positions and sliding grooves are unchanged.
The model uses provisional 10.5mm-diameter, 3.3mm-high heads with a 4mm Allen socket. Measure the actual bolt heads,
washers and Nylocs before machining. Nominal grip through the recessed lid, steel, two washers and nut is 27.9mm;
35mm bolts replace the former 50mm bolts. Counterbores and fasteners follow the existing `Upper rail` motion.
Placement is illustrative; M6 shaft holes are not modelled. The lid counterbores and full-depth slat access openings
are modelled.
Match-drill the physical hardware and confirm bearing area and moving-part clearance before construction.
The BOM counts eight 40mm coach bolts, one six-pack of 35mm Allen bolts, twenty washers and fourteen Nylocs;
the Nylocs replace the bolts' supplied plain nuts and require two twelve-packs.

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
extending it closes the lid. The Table visibility checkbox hides both table poses independently of bed motion. The Table position selector
chooses Bench mount or Stowed, including after reloading. The fixed mount and backing follow Long bench. The blue cushion follows the lid's linkage
transform as its placement carrier; the orange cushion stays upright and lifts just enough to clear blue.
Actual foam forces and wall/mesh clearance remain unverified.

The Lagun bracket attaches to the long box's aisle-facing wall at its cab end. An 18 × 97mm plywood pad
spans floor to box top (currently 364mm high) and spaces it out from the box face. The pad occupies Y1183–1280,
flush with the box end and 5mm clear of the sliding frame; the bracket stays at Y1183–1275. Including the shared
24mm bed offset, the bracket origin is X638/Y1229 with its normal towards the aisle. The upright's native X627–665 envelope leaves about 14mm from the fixed slats over
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

`cross_bench.py` builds a fixed full-width platform at X = 22–1092, Y = 1280–1860 by default. Two fore/aft
18mm plywood frames have open-bottom rounded cutouts, 60mm legs and top rails. Matching rear and front 18mm frames
fit between their inner faces, each with two legs using the same `member_width_mm` (60mm by default).
The front frame finishes flush with the cab-facing ends of the side frames. The obsolete wider Lagun mounting post
is removed; the table mount remains on the long box.
At the default 400mm platform height,
the frame tops are Z = 382; the 18mm slats bear directly on them. There is no divider, deck, sliding assembly,
cab-end skin, hinged lid, brackets or stop plates.

`cross_bench_overhang_mm` defaults to 200mm at the aisle slat ends. The wall-side frame retains its former
arch-relative support position, following the shared `Parameters.cross_bench_support_x_mm` datum;
the aisle frame occupies X = 852–870. Both run Y = 1280–1860. At the saved 1500mm cargo width and 1205mm arch gap,
the rear mounting frame occupies X = 175.5–852, Y = 1280–1298 from floor to rail top, with an open-bottom rounded
cutout and two 60mm legs. Its matching front frame occupies Y = 1842–1860. These are bench-local coordinates
before the shared 24mm inward offset.
`cross_bench_layout.py` supplies the frame and table mounting datums. The removed rear skin's thickness parameter
and material role are retired. Toilet/tray hardware and frame joints remain unmodelled; CAD does not establish load capacity.

Four 1070mm-long 80 × 18mm stock slats run across the van, directly over both support rails, matching the previous
extended cross bench's four moving rows. The first starts at Y = 1280; the last finishes at Y = 1860. Three equal
86⅔mm ventilation gaps fill the 580mm depth. The junction to the long bench's last extended moving slat remains
90mm, with no added empty margin at either end of the cross bench. Slat count stays four; their gaps follow the shared
stock width and cross-bench depth.
The rearmost slat (nearest the long bench) is 50mm shorter at its aisle end: 1020mm at the default bed width.
Its exposed rear/aisle corner has a 40mm plan radius at the default 80mm slat width, carried through the full
18mm thickness. The two middle slats remain full length. The cab-end slat has a square wall end at construction
X100, shortening it by 76mm to 994 × 80 × 18mm. This clears the registered front-pillar scan by at least 5mm across
its full width and thickness, while retaining full bearing on the wall-side frame. Supporting frames and cushions
retain their dimensions. The cut list records the shortened rectangular piece.
The cross bench has one full-width fixed cushion, combining the former blue seat and purple backrest.
Its conversion slider is removed. The former green backrests are removed; the long bench's taller orange backrest
and blue seat now fill the complete sleeping width.
Old project fields and material selections for the removed deck, divider, lid, bearers and stops are discarded on load.

The lower cabinet is one timber carcass with a rear bay, a shallow front bottom bay and two full-depth front bays.
The removable upper module contains **boxes 4 and 5** above the cab-end bay and **boxes 6 and 7** above the rear bay.
They share the middle transverse frame and use the lower cabinet’s 40 × 18mm pine.
Box 4 has a square-ended frame, 328mm deep from the aisle face at X1116 to the timber face at X1444.
Its floor and cab-end cross rails reach the same depth as the deep section of box 6.
One 4mm plywood sheet backs box 4 and the deep section of box 6. Its outer face sits at X1448.
At box 4, a curved cut in the top edge clears the cab-side pillar. The cut follows the registered right-side scan.
The cab-end wall upright fits between the floor and top cross rails with its full 40 × 18mm end on timber.
At the middle, the wall rails butt into the shared cross rails. The 6mm floor and top shelf sit on
18 × 18mm ledgers, level with box 6.
At the top of box 4 the longitudinal rail is flush with the wall-facing sides of both box 5 uprights
at X1355, 89mm inboard of the box 4 wall frame.
The rail is full 40 × 18mm stock. The 6mm shelf and its two transverse ledgers end at its aisle-facing side.
Box 5 shares the box 4 shelf as its floor. Its straight wall frame steps in 89mm to X1355,
giving it 239mm frame depth and a level top 1238mm above the finished floor. Its two wall uprights seat
on the existing transverse rails. The two aisle posts run the full height of the stacked bays.
Boxes 5 and 7 are open at the top. Check for 3mm clearance between the
outside face of the 4mm backing and the fixed metal roof shoulder along the full rail during fitting.

Box 6 has two rectangular bays in one removable frame. The rear bay reaches construction X1319,
and the bay towards the cab reaches X1444. The upper step and middle cross rails run 310mm from the
aisle rail to the inside face of the deep backing. Each rests on the full 40 × 18mm end of its wall post.
At floor level the two cross rails butt into the sides of those posts.
The pillar return starts 157mm forward of the cabinet rear. Its cross frame starts at 161mm. Its plumb corner post and square-ended rails
form a 125mm step in frame depth around the rear pillar.
The three box 6 wall posts and the two lower deep wall posts have their 40mm faces across the van.
Each is flush with its cross rail. The longitudinal wall rails fit between the posts.

The two deep wall posts start at 770mm and finish beneath the cross rails at 988.245mm above the finished floor.
The rail tops are at 1028.245mm. The shared middle aisle post continues up to box 5.
The box 6 floor has two 6mm ply panels, one on either side of the step cross rail.
Both sit on perimeter ledgers and finish flush with the rail at 810mm. The step cross rails and
shallow wall rails use full 40 × 18mm stock at both levels. Three rectangular 6mm ply shelves sit flush
with the top of this frame. From the rear, box 8 has one shelf between the rear rail and the step and
another between the step and the box 7 bearer. The box 7 shelf spans from the bearer to the middle rail.
At the top, 18 × 18mm ledgers run inside the shallow wall rail and on both shelf-facing sides of the
step cross rail and box 7 bearer. Each step ledger ends at the inside wall rail of its own bay.
The rear bearer ledger stops against the door catch block at the aisle end.
The lower cabinet has an open top frame.
Lift the assembled upper carcass level with that frame, then slide it 329mm wallward from the aisle
at its final fore–aft position.
Box 7 occupies the forward part of the space above box 6. Its 239mm frame depth and 1238mm top elevation
match box 5. The two rooms share their middle posts, cross rail and plywood divider. The box 7 rear aisle
post sits 235mm from the cabinet rear, giving a 262mm clear opening. The wall-side rear post and transverse
roof rail sit 308.5mm from the cabinet rear. The rear end of box 7 opens into box 8.
At this level the longitudinal rail in the deep part of box 6 aligns with box 4's rail at X1355,
89mm inboard of the deep frame. The 203mm cross support butts against its aisle face.
The rail and cross support use full 40 × 18mm stock. Their top faces finish level with the box 6
frame and support the full square-cut foot of the box 7 rear wall post.
Box 8 has a fixed 6mm aisle front in 10 × 6mm rebates in both jambs.
The 211mm panel spans the 195mm opening with 8mm of bearing at each side.
Its bottom edge aligns with the box 7 flap, 2mm above the square sill. A 195 × 18 × 18mm pine batten
sits on the sill between the jambs and bears against the back of the plywood for fixing.
The rear post has a square top at world Z1201. The front sits flush with the aisle face and its jigsaw
edge follows the scanned roof up to the box 7 jamb. The profile allows for the full 329mm slide on
either side of the van. Boxes 4–7 each have one bottom-hinged aisle flap.
The centre dividers and wall-side backs are 4mm Bunnings TigerPly Okoume. Box 3 is open on the wall side for chair storage.
The box 1 back sits on the inside faces of the shallow wall rails and attaches
to two square-cut end cleats. One deep back covers both levels of box 2. Box 6 uses two flat backs and
a square return at the rear pillar. The shared boxes 5 and 7 back extends down to the undersides of
the three cross beams. Its bottom edge has square notches at the pillar step, middle and cab end.
The middle notch also clears the 4mm centre divider attached to the beam. The back extends aft to the pillar step.
There it turns 36mm aisleward and continues to the cabinet rear on the box 6 shallow wall.
An 18 × 18mm vertical pine cleat joins the shallow back to the step return on the pillar side.
Cut the shallow back and the stepped return as full-height pieces. Jigsaw the two long panel edges
to their individual curves from the installed-side scan. The shallow back dips over the rear pillar
and rises towards the step. The long back follows the shoulder below the roof beam and levels out
at cabinet height 290mm forward of the cabinet rear. The short return joins the curves with a 19mm rise.
A 40 × 18mm upright sits on the upper step cross rail against the cab-facing surface of this return.
Its wall-side edge backs the adjoining skin. A single bevel ends at the skin height on the aisle side
and 2mm below the skin on the wall side to clear the roof on insertion.
Each removable module owns its backs. In the lower module the 198 × 770mm
main panel and 94 × 503mm above-arch extension meet edge to edge on the box 3 faces of the middle cross rails.
An 18 × 40mm notch at the top of the extension clears the rear longitudinal rail. The 292 × 194.25mm upper panel sits in the same plane on the box 6 face of the shared frame
and meets the underside of the top shelf ledger. A square notch in its top edge clears the box 6 wall rail.
The box 4 divider has a full-width head stop and a 160mm sill stop between the two module bolts.
Both stops are 18 × 18mm. The box 5 divider
aligns with it and fixes to the top rail, wall upright and sill stop.
The lower cabinet includes shelves, three front doors and a fixed cover
for cabinet 3; other skins and flap stays are still to design.
The original fitted envelope, dimensions and construction parameters remain in
[`data/cabinet-reference`](../data/cabinet-reference/README.md).

Both modules have a 4mm cab-end skin. The upper module also has a 4mm rear skin. The skins butt against the
inside faces of the aisle stiles, hiding the plywood edges from the aisle. The upper rear skin occupies
local Y0–4 and finishes flush with the bed.
The cab-end skin occupies Y973–977. The cab-end cross framing finishes at Y973 and the aisle stile at Y977.
The chair-facing side of the centre divider stays at local Y544. The divider extends towards the cab to Y548,
where the middle cross frame supports it. The extra millimetre comes from the cab-end bay.
The lower rear frame is open for chair loading. The upper rear skin follows the roof beam down towards
the pillar and extends past the shallow backing to follow the wall contour. The two cab-end sheets share one
outline taken on the fitted cab-end face, now covering world Y1053–1057. It follows the sidewall from the
flat floor to the roof and bridges the window recess. The cut passes continuously across the module joint.
The middle and cab-end shallow wall posts stand 277mm tall with their 40mm faces across the van.
Each runs from the floor to the underside of a continuous arch-level cross rail. The shallow wall
frame's wall-facing edge is aligned to the measured 1200mm floor edge at construction X1350 (display X150).
The aisle face is at construction X1116, aligned with the fully extended bed. The rear shallow wall post
also has its 40mm face across the van. The chair loading opening runs from the floor to the rear top
cross rail and measures 176mm wide by 730mm high. The actual
floor's known fit is the alignment datum. The remaining few-millimetre scan interference is recorded rather
than used to thin the framing; 3mm scanned clearance is not claimed for these lower wall members.
At the saved chair positions, chair 1's folded leg and seat fabric intersect the rear shallow wall post in CAD.
The same overlaps were present with the 3mm lining. The opening dimensions alone do not verify the chair fit.
The two deeper front compartments share a vertical wall frame at construction X1444. Clipping the registered scan to the full frame/backing region found the nearest wall
at X1454.492. The 4mm deep backing finishes at X1448; overall depth stays
within the saved X1460 exterior limit.
Square reinforced butt joints connect rails to posts; use glue and dowels or screws, with drilling to be detailed.

The lowest deep-compartment frame level is Z307: its 40mm bottom rails start at Z267, at least 3mm above
the measured arch crown (rounded up to Z264 above the floor). Both compartments above this extend to the
deep wall frame. The extra level retains the original mattress-access door datum at Z510; the module interface
remains Z770. Centre transverse rails are centred on their posts; end transverse rails are flush with the
outside post faces for the end skins. The tall rear bay has only bottom and top longitudinal rails, with no
intermediate rails across its aisle or wall face. The two cab-end shelves at Z307 and Z510 rest on
18 × 18mm pine ledgers on all four edges. The long ledgers meet the side ledgers at the corners.
At both levels the middle and cab-end side ledgers run continuously between the aisle and wall ledgers.
The Z770 frame carries the upper module directly. Two M6 × 90mm hex bolts pass vertically through each
stacked transverse rail pair. Match-drill 6.5mm holes through the 80mm timber stack on the 18mm rail centreline.
Measure from each cross rail's aisle end towards the wall. The hole centres are 40 and 105mm at the rear,
and 40 and 230mm at both the middle and cab end. Fit a 16mm washer under each head and nut,
with the heads underneath. The middle sill stop finishes 15mm from each bolt centre.
Glue and screw the ledgers to the frame; keep screws clear of the frame-joint dowels.
Both 6mm plywood panels are 292 × 389mm rectangles and finish flush with their frame rails. Panels fit inside the framing
and are not sandwiched between members. Cabinet shelves visibility controls the Lower module / Shelves group. Ledger cuts share the existing 18 × 18mm pine stock through their shelf-ledger role.
The shallow wall-side infill stays inboard of the shallow frame to preserve the measured floor-width envelope.
The existing Cabinet / Lower module / Frames visibility and timber-cutting paths are reused.
The frame is a construction layout, not a load rating; panels and vehicle attachments are still to design.

The cabinet 3 fixed cover and three front doors share Lower module / Doors, so Cabinet doors controls all
front closures. The fixed cover shares the door plywood material in the BOM. All are 6mm
plywood, flush with the aisle face. Front-frame
rebates are 10mm wide and 6mm deep, leaving 12mm of timber behind. With 2mm perimeter clearance, panels
overlap each rebated opening edge by 8mm. The fixed cover is rebated on all four sides.
All three cab-end lower doors are 376mm wide. Each piano hinge runs along the bottom edge and fixes
to the square sill. Both jambs and the head have 10 × 6mm rebates. The fixed cover is 513 × 706mm.
The lower doors are 233, 169 and 226mm high from bottom to top. Boxes 4 and 6 also drop down. Boxes 5 and 7 lift up.
The flap sizes are 376 × 184.25mm for box 4, 376 × 175.75mm for box 5, 513 × 184.25mm for box 6
and 278 × 175.75mm for box 7. Moving doors have 30mm finger
holes and 18 × 18mm glued pine hinge backing. Piano hinges use the existing nominal 27mm section;
actual screw patterns, leaf thickness and mortises still need checking against the physical hardware.
Each door has an independent opening control. Each of the seven doors has a Taskmaster
double roller catch on a 30mm length of 40 × 18mm pine behind the frame.
Each bottom-hinged flap catches at the centre of its header, directly above the finger hole. Where a shelf
ledger shares that header, two square-cut lengths butt against the block. The 30mm projection supports
the nominal 25mm-deep base. Glue each block to the frame and drive two countersunk 6g × 40mm screws from
the back of the block into blind pilot holes in the frame. The screws enter the 18mm frame by 10mm,
leaving 8mm to the aisle face. Fit the blocks before installing the shelves for driver access. The keeper is
through-bolted to the 6mm door with two M3 × 12mm bolts, nuts and backing washers. Local rear-lip relief
clears the keeper without changing the front rebate outline. Mounts are in Frames; fixed catch bodies and
moving keepers follow Cabinet doors. The BOM counts seven sets (two four-packs), fourteen keeper bolts/washers
and fourteen block screws; catch-base screws come with the product. Geometry and drill patterns remain nominal
until checked against the physical catches. The catch holding force is unpublished.

#### Top-row folding stays

The Box 5 and Box 7 sliders raise the top-row flaps. Each 6mm door has a top
piano hinge with an 18mm pine backing strip and a low, centred finger pull.
The box 5 roller catch attaches to the cab-end aisle post. The box 7 catch attaches to the post beside box 8.
Each block stands vertically behind the post. Its bottom clears the shelf by the door gap (2mm).
The hinge and backing stop 20mm from the stay-side door edge
and 10mm from the opposite end. This leaves space for the door arm beside the hinge when open.

Each flap uses one Penn Elcom P1240 beside the centre stile. Each fixed pivot screws into the opening-side
face of the stile through a 10mm tubular spacer. Its centre is 13mm behind the cabinet face with 18mm stock.
The fixed eye has 1mm nominal clearance behind the closed 6mm flap. The pilot centre is 5mm from the back of the stile.
Both links fold towards the stile. Each door pivot screws into the stile-facing side of a 50mm long,
18mm square pine pad glued to the inside of its flap. The divider has a straight front edge.
The model uses nominal 25mm stile screws, 12mm pad screws and 8mm outside diameter spacers.
Confirm the free pivot action, screw fit and edge clearance on an offcut before drilling the cabinet.

The drawing places the elbow pin 80mm along and 18mm across from each fixing eye.
The straps are 12mm wide and the fixing eyes are 4.2mm in diameter.
The assumed physical stop puts the fixing eyes 160mm apart and the flap about 3° below horizontal.
The preview uses that flap angle at 100%. The elbow stays on the folding side of the line between the eyes.
This lets the flap close immediately from any position. The slider provides an alternative to dragging the flap.
See the [W3C guidance on dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html).
The P1240 drawing gives the arm dimensions but does not specify the stop contact angle.
Check the stop and release with the actual stays before drilling the cabinet. Bend radii, forming details
and screw patterns are approximate.

Sources: [Penn Elcom specifications](https://www.penn-elcom.com/200mm-chrome-locking-lid-stay-p1240),
[Penn Elcom catalogue, printed page 205](https://www.penn-elcom.com/global-product-catalogue-download),
[P1240 dimensioned drawing](https://www.flightcasefittings.co.uk/media/catalog/product/p/1/p1240-dwg.jpg),
[Roadcases NZ product photo](https://roadcases.co.nz/products/penn-elcom-p1240-locking-lid-stay).

The following describes the checkpointed cabinet, not the active assembly.

`cabinet.py` builds two modules, with a copied box frame in the lower cabinet. Both retain Frames, Skin, Shelves and Doors
visibility groups. Skin now contains supporting 6mm Tigerply Okoume end panels and the centre divider, using the
existing Bunnings product. It is not 3mm cladding over a separate timber skeleton. The front frame, shelf cleats,
joining rails and hardware blocks use the existing 40 × 18mm pine. The lower wall frame now copies that same
40 × 18mm stock; the old 90 × 18mm arch beam is removed.
The 6mm supporting-panel choice was approved on 17 November 2026 after comparing gravity compression and
panel bending at an assumed 12kg per shelf. Existing cleats and framing remain; the comparison is not a verified
cabinet load rating or a capacity check of its joints and vehicle attachments.

Middle and cab-end panels have full-depth, jigsaw-scribed profiles against the actual side, pillars and finished
ceiling. The rear upper panel follows the same contour and extends down to Z730. The lower rear loading opening
has no plywood facing or bottom sill. Its original chair-loading target was 230 × 730mm; narrowing the cabinet
reduces the clear width, and this target is not enforced while furniture-clearance checking is disabled. The lower
wall frame repeats the aisle-side box layout inside the fixed skins: two straight floor-standing end stiles,
a continuous rail at Z470–510, two top rails at Z730–770 and a centre stile above the raised rail. The top
rails meet the centre stile/divider without crossing the plywood. The lower wall
bottom rails and centre leg are omitted over the wheel arch. The frame uses its existing wall-side datum,
without changing the cabinet placement, outer skins, backing planes, door openings or shelf levels. The centre
stile sits beside the centre lining; transverse crossings have half-laps. No floor sill blocks rear loading.
The van closes the wall-facing back. Front edges of supporting panels butt behind the front frame; no skin
landing grooves are needed. Fix panel faces into the adjoining timber, not screws into thin plywood edges.

`cabinet_layout.py` supplies the real fitting volumes and shelf/door datums. Its lower-back datum locates only the
copied wall frame; it does not truncate the fitted plywood profiles. `scribed_sheet`
intersects face/mid-plane templates and extrudes one constant-thickness outline. Shelf cleats are fitted individually to the backing envelope with bevelled wall ends. Module joining rails
retain their original common square-ended footprint across both halves, preserving their bolt positions.
The backing glue cleats meet the horizontal shelf/rail faces with matching bevels rather than edge-only contact.

Five 6mm shelves retain their levels. The lowest forward shelf follows platform + foam + mattress clearance;
the middle shelf tops/interface are at storage height + frame width (770mm), and the upper level follows the
available module height. Shelves butt behind the front frame and between the 6mm panels. Both ends of each shelf
have bearing on face-mounted cleats or joining-rail shelf seats. Their wall edges meet the backing planes.
The two rear shelves use a short straight rear return followed by one straight angled pillar edge, replacing
scan waviness while retaining at least the existing 3mm clearance. The upper rear shelf support is trimmed to
the same plan profile. Lower module bolt lands and shelf fixing holes stay intact.
There are no internal post cutouts. The front frame ties the panels together and stiffens the front shelf edge.

The lower middle panel reaches the wall above the wheel-arch bridge, following the existing 3mm scan-clearance
scribe. An open rectangular cut replaces the enclosed bridge slot and removes the lower wall-side tail. Its
horizontal edge follows the beam top and its aisle-side edge runs straight down to the floor, retaining the
module fitting clearance around the beam. That straight relief now follows the replacement rail’s Z510 top.

Five flat 6mm backing sheets close the four upper cupboards and the lower cab-end upper cupboard. All backs run
parallel to Y, with no rotation around Z. The front/rear top pair share one lean about Y; the front/rear bottom pair
share another. The top and bottom rows meet at their common shelf height, world Z1043.245mm at the raised floor, with different lean angles.
The lower cab-end backing continues the bottom-row lean below the module joint. Front and rear backs are coplanar
within each row. The bottom row leans about 5.6° and the top row about 19.8°; the whole cabinet is not in one plane.
The cab-end bay is the left/wheel-arch column in the owner's front-view photographs. Its backs span the full bay,
pass in front of the front pillar and meet the existing cab-facing skin/frame. The rear backs reach the rear corner
pillar: their rear edges follow its boundary with 3mm clearance, leaving a small patch of metal exposed. There are
no arbitrary stops halfway across either bay. The wheel-arch and chair bays remain open-backed.
`cabinet_backing.py` fits shelves, middle panels, cleats and joining rails to the corresponding backing planes;
joining-rail shelf seats follow the shelf outline. Pillar regions beyond the rear backing edge retain their contours.
18 × 18mm pine glue cleats follow the inside face of each backing at its middle/cab-end skin joints. Rear
backs stop at the pillar, so only their middle edges receive cleats. Cleat ends are bevelled at the horizontal shelf/rail planes. Shelf-support ends follow the backing planes;
module joining rails retain their shared original end positions. The lower module’s two slanted 18 × 18mm
backing cleats are removed pending the next backing-support decision; the upper module retains its cleats.
Pieces stop at upper-skin guide gaps; glue joins stay within each detachable module. The dedicated backing-cleat role
shares the existing 18 × 18mm pine product and stock layout with the door hinge backing strips.
The outer end panels retain their contoured outlines. The measured flat-sheet profiles in `scan_scribe_data.py`
have at least 3mm nominal scan clearance and use the existing cabinet-partition plywood material. The cutting pipeline
uses `fitting.py` to sample the registered scan near plywood and timber boundaries in the construction pose.
Only edges near sidewalls or ceiling receive the shared fitting allowance; the flat floor is excluded. Intentional
slots, rebates and rounded corners alone never qualify. Interior vehicle notches retain rectangular fitting blanks
without extending unrelated outer edges. Models can mark fixed local datum axes with `set_fitting_datums` in
`cut_profiles.py`; mirroring and scan scribing preserve those declarations. They protect only outer stock edges,
so internal wheel-arch/notch fitting remains active. Long-bench box heights and the cushion-rail upstand are such
assembly datums. Scan points below the finished-floor height are excluded regardless of the board-edge direction.
Explicit per-piece margins override these defaults. Lower/upper modules
retain their floor-relative Z770/770.5 backing seam (world Z780/780.5), independently of the taller side-panel guide seam. Physical fit and backing
fixings remain to be confirmed during the build.
The bridge sits directly beneath the lowest forward shelf cleats,
supporting them and the rear portion of the divider without separate bearing blocks. Its height follows the
shelf and cleat dimensions while retaining at least 3mm wheel-arch clearance. The bridge butts between the rear
timber jamb and a floor-standing 40 × 18mm cab-end upright. The new upright sits against the cab-end panel's inner
face and ends beneath its lower shelf cleat, providing a timber attachment for the beam and bearing for the cleat.
This establishes an explicit support arrangement, not a verified complete cabinet load rating.

Four pairs of straight transverse side joining rails retain the detachable joint. Lower rails have shallow
continuous shelf seats. The joint shelves belong to the lower module and finish flush with its rail tops;
upper rails bear on the plywood, with the module bolts passing through 6.5mm holes in the shelves. There are no
bolt-pad notches in the shelf edges or interrupted rail seats. Eight ordinary
zinc-plated M6 × 90mm hex bolt-and-nut sets remain side-only, with 6.5mm clearance holes and no countersinks.
M6 × 16mm washers sit under both heads and nuts. The lower head and washer project about 5.6mm below the rail;
head/nut sizes and washer thickness remain nominal envelopes. There are no front/rear longitudinal joining rails. The existing
20mm lower panel guides and 0.5mm seam clearance apply at the middle, cab-end and rear sides. The lower rear skin
starts above the chair-loading opening and rises 20mm past the joint; the upper rear skin starts 0.5mm above it.
Both rear pieces retain the same measured wall contour. Keep every detachable mating
surface unglued. Module rails and fasteners remain in the Module joint subgroup under Frames.

The cabinet front face follows the extended bed rail plus `bed_inward_offset_mm`, with no additional gap, shared through
`cabinet_front`, in both its frame layout and door
construction. With the accepted 24mm bed offset, its front moves 24mm towards the wall, reducing cabinet depth
while keeping the wall-side scribed profile. Panels, shelves, front framing, doors and their hardware follow the
same face position. The current cabinet face is flush with the extended bed; hinge barrels project approximately
5.7mm of it where their heights and fore–aft positions overlap the bed. The rear jamb continues to use the fitted
wall limit rather than moving outwards to preserve the former 230mm opening.

`cabinet_doors.py` builds five bottom-hinged flaps, two top-hinged flaps and two fixed covers.
Each moving door carries a glued 18 × 18mm pine strip behind its hinged edge, with 10mm end clearance, increased to 20mm on the stay side of boxes 5 and 7. The hinge has the same cut length as that strip. Leaves sit on opposing door and frame edges;
only the knuckle shows. The other three door edges overlap front rebates. Old exposed butt hinges, hinge bolts,
drilled hinge holes, shelf hinge notches and vertical staggering are removed.
`cabinet_piano.py` previews the Taskmaster 610 × 27mm hinge with a nominal 0.8mm leaf, 2mm pin and 3.6mm barrel.
These section dimensions, the 2mm hinge gap and any mortices require physical confirmation. No unverified hinge
fixing holes or screws are modelled. Catch keepers retain their through-face plywood bolts.
Catch plates mount on 30 × 40 × 18mm blocks at the free edge of each flap. Fixed and moving hardware
follow Doors visibility; timber mounting blocks follow Frames. Door controls and motion paths remain unchanged.

The BOM allows seven 610mm Taskmaster stainless piano-hinge lengths (one per flap before offcut optimisation),
18 × 18mm pine backing stock and seven roller catch sets. The seven keepers use fourteen M3 × 12mm bolts
and washers, and the mounting blocks use fourteen screws. Hinge fixings remain unspecified. Hardware geometry
uses nominal mounting dimensions. Each of the five bottom-hinged flaps has one 2mm Pinnacle jack chain.
The two mounting pins sit 125mm above the hinge axis with the flap closed. The fixed lug attaches to the back
of the outer aisle post in each bay. The four cab-end chains use the cab-end posts. The box 6 chain uses the rear post.
The moving lug bolts through the plywood. Its bolts sit 11mm inside the opening, at the same inset as the upper side catches.
At 90° the pin centres are about 188mm apart.
One 3m pack covers all five doors. With the flap horizontal, check the actual link length before drilling.
The CAD approximates the link shape and the slack with two runs. The lug and pin sizes are nominal.
Boxes 5 and 7 use their folding stays. Cleat fixing holes and vehicle anchorage remain to detail. Pine backing strips follow the moving doors and appear in the cut list.

The Visibility section provides independent Cabinet shelves, Cabinet doors, Cabinet skin and Cabinet frames
checkboxes, each covering both modules. Hinges follow Doors, including their stationary leaves. These are local
viewer controls and require no server roundtrip or regeneration. Their saved preferences survive hiding/showing
the whole cabinet. Top cabinet and Bottom cabinet use the same checkbox mechanism to control Upper module and
Lower module respectively. They mask the complete module without clearing its category filters or individual
component-eye choices; restoring either module restores those choices. The Cabinet checkbox still gates both.
The controls retain the existing native labelled-checkbox pattern, following
[WAI's label guidance](https://www.w3.org/WAI/tutorials/forms/labels/).
Parameter-group eye buttons use the same actual component paths.

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
At full conversion, nominal orange fills X22–492 and the long seat X492–1092, meeting without a gap.
Both Cushions groups use the wall-side rail datum X22, centring the nominal 1070mm mattress on the rails.
The cross-bench slats and frames share that datum; the frontmost slat still stops at vehicle X100.
The long-bed extension is 22mm wider than before. The cabinet aisle face is consequently 16mm wallward from the former narrow-bed design
(the initial 6mm bed gap was removed, widening the cabinet by 6mm),
with its wall-side frame fixed; shelf and cross-rail depths follow the reduced cabinet depth.
The long-bench slider moves the long seat and orange backrest; the cross seat remains flat and stationary.
Each cushion is a centred native box in its own located Compound.
Cushions hold until 40%; by 80% the seat has shifted and the backrest has turned above the seats;
the final stage lowers the backrest. CAD and live tracks use the same sampled poses.
This previews manual repositioning; real cushion fit and intermediate handling remain visual checks.
Storage-lid tracks act on a `Foam` assembly parent, while conversion tracks retain the cushion parent groups.
The `Foam / Core` mesh keeps OCP's native box-centring offset untouched; this offset must not be replaced by
absolute storage tracks, even at the closed pose. Deformation reads the core mesh, while pillow bounds use its parent.
The blue child uses the lid delta conjugated through its closed cushion pose, including the shared wall-side rail offset.
`cushion-foam.ts` performs one direct geometry update per pose. Blue and orange retain their full manufactured widths in the viewer: 600mm and 470mm. At full conversion,
these form a centred 1070mm mattress, intentionally overlapping each 18mm retaining rail. No rail-based
width scaling or clipping is applied. These dimensions are the foam cut sizes, not upholstery patterns or
seam allowances. During storage opening it follows the lid
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
The labelled Table checkbox in Visibility hides or shows both poses; the Table position selector chooses the pose,
using the existing table_mount values 0 and 2. Bed extension and lid movement never change that selection.
It persists through browser storage and pose saves, including when reloading an extended bed. The checkbox
retains native label activation and Space-key toggling, following the
[WAI checkbox guidance](https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/).
Older project files and browser storage containing only the shared bed position initialize both bench sliders to that
position. Once separate positions are saved, they remain independent.

Clicking an unselected CAD piece highlights it in magenta and clears any other highlights. Clicking a selected
piece removes its highlight. Shift-click adds or removes one piece while keeping the others selected. An empty
click or Escape clears the selection. Double-clicking a wooden piece opens its cut-list entry.
The **Piece actions** menu shows the gestures and supports adding or removing the piece under a right-click.
Selection happens on click release so a drag can move the camera or the piece without changing the selection.
See [W3C's pointer cancellation guidance](https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation.html).

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
Wooden floor controls the top-level Finished floor plywood assembly, outside Vehicle references. It contains the
two 2030mm-long panels cut from separate 2400 × 1200 × 12mm sheets. Timber supports the straight joint
along its full length at X557.5, 64.5mm inside the aisle face of the long bench in the cabinet-right layout.
The bench-side blank is 532.5mm wide and the
aisle blank is 917.5mm wide. Both retain the original door-wing steps and chamfers at the sliding doors.
Behind each wheel arch a flush-trimmed pine block supports the 105mm plywood extension.
The shared seam lies under the benches between Y80 and Y1940. It continues a further 95mm to the rear
threshold and 75mm towards the cab. Both panels have separate cut outlines. Their tops are at Z20,
driven by the shared `floor_surface_z_mm` parameter.

One shared frame of 45 × 20mm Red Stag pine battens (Bunnings I/N 0605227, 5.4m lengths) sits beneath
both panels. The front and rear rails each span the full 1200mm floor width.
The four side rails have square ends and fit between the end rails and the routed door shoulders.
The middle cross rib includes the first strip of both rear door shoulders. Cut it from one 1300mm blank.
Use the floor plywood as a guide to trim both ends. Add two 170mm offcuts per shoulder beside the rib.
At each cab-side shoulder, use one
157.5 × 45 × 20mm crosspiece. Extend the long wing rail 5mm into the taper and butt it against the crosspiece.
Flush-trim the rail tip and crosspiece together to the plywood. The square joint has 32.5mm of contact.
Use three 330mm offcuts for each rear pocket.
Jigsaw the glue-ups close to the fitted plywood outline, then use the plywood edge as the flush-trim guide.
The rear cross rib is 1110mm long. The clear bays from the rear end rail to the hatch cross rib
measure 468⅓mm, 491⅔mm and 445mm.
The 1360mm cross rib spans the door wings at Y1547.5 and forms the rear edge of the pump hatch.
Square-cut lengthwise ribs at X557.5 and X902.5 butt against each cross rib.
The clear spans across the 1200mm core are 340, 300 and 380mm from left to right.
The lengthwise rib at X902.5 forms the aisle side of the hatch. Two short rails close its wall and cab sides.
The ribs occupy Z−12…8. The complete floor is 32mm thick on the assumed flat floor.
The twelve fixed infill pieces and the removable insert use 20mm Expol S Grade ThermaSlab (Bunnings I/N 0717186).

The registered scan places the pump cover near X1075, Y1720. Check the tab positions in the van before cutting.
The timber frame leaves a 300 × 300mm clear opening. The aisle sheet contains the entire 345 × 345mm cutout.
Cut the 343 × 343mm lid from one plywood offcut. Attach the 298 × 298mm EPS insert to its underside.
The insert has a recess below the finger hole. Two countersunk screws secure the lid to the side rails.
The finger hole and both screws are at the same fore-aft position as removable slat 03.
Drill the pilot holes into the timber during assembly. Keep the screw tips inside the timber.

Remove the cross-bench cushion. Unscrew slat 03 from its two support frames. Remove the two lid screws.
Use the finger hole to lift the lid. Turn it edge-on to pass it between slats 02 and 04.

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
The cabinet uses 6mm scribed supporting panels and 6mm door/shelf plywood. All four cross-bench frames share 18mm frame plywood.

The rear bay's top opening has a relocated 40 × 18mm stile at vehicle Y325 (cabinet-local Y245 at the current
80mm shared rear setback and zero cabinet inset). Only its top flap narrows; the tier below and lower post retain their layout.
A fixed 6mm inset panel closes the rear portion, with no interior divider or upper crosspiece.
It uses the doors' face plane, perimeter reveal and edge treatment, with no hinges, catch or finger hole.
Doors and the fixed panel overlap the through-openings by 8mm at the current 2mm reveal. The frame has
10mm-wide front rebates whose depth matches the panel thickness (6mm, leaving 12mm rear bearing lands).
The rebate cutters use closed poses independently of live door angles. Enlarged doors retain their
outward hinge axes; catches follow the header edges, with local rear-land relief for their keepers. The bottom storage pair retains its
2mm centre seam: there is no centre frame to rebate. Rebates are routing operations on the timber
stock; door and fixed-panel cut outlines include their enlarged dimensions.
Piano hinges run along the unrebated hinged edges; there are no exposed opposing leaves or staggered hinges.
The rear upright extends to the scribed beam-clearance profile. The infill uses the existing cabinet-door plywood
stock but belongs to Skin visibility. `cad/cabinet_upper.py` records provisional registered-scan roof
landmarks for the infill and the rear supporting panel, with approximately 5mm fitting clearance.
These profiles require visual/physical fitting; they are not a verified complete scan collision envelope.
Plywood parts retain their scribed profiles and openings in the cut list. The moving front support is cut from 18mm frame plywood.
Cabinet stock sections come from their selected timber products, with measured overrides.

The nine cabinet doors, shelves and supporting panels share 2400 × 1200 × 6mm Tigerply Okoume stock
from Bunnings, item 0345103. Their parts share one cutting-stock group. Saved selections of the retired
Redline product migrate to Tigerply. Piano-hinge fixing details still depend on the physical hinges.

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
The cabinet mount has been removed. The Table position selector switches between Bench mount and Stowed without
regeneration. Stowed shows the folded pine with the detached upright beside the arm beneath the tabletop.
The fixed bracket and plywood backing follow the Long bench visibility switch. Stowed has its own live XYZ and facing controls;
the arm automatically points towards the displaced tabletop, flipping 180° when the offset changes sides.
The default aisle position is a preview pending a storage-location decision. The two display
poses share component builders and one mount offset. The duplicate stowed geometry is excluded from the cut
list and its tabletop leaves link to the working pose's cutting entries. Nominal packed thickness is 113mm
(36mm pine + 30mm fitting + 47mm arm); actual handles and the storage channel remain unmeasured.
The bench mount attaches to the long box's aisle wall on an 18 × 97mm plywood pad spanning floor to box top
(currently 364mm high). The moving frame is shortened 102mm at its cab end, leaving 5mm beside the mounting pad throughout sideways travel. Slats stay unchanged.
The tabletop has two 600 × 200 × 18mm plywood leaves with rounded corners and perimeter round-over.
It folds from 400mm open width to a 200mm-wide, 36mm-thick stack. The long-edge hinge rotates above the fixed
leaf. Two selected Homer HOM006136 hinges appear in both table poses, with centres at 20% and 80% along
the seam. Their 114 × 42mm open footprint and 38mm pin width follow the supplier; thickness, pivot spacing,
barrel section, taper and countersunk holes are photo-based approximations. Each half follows its leaf
through the existing schematic fold. Nominal blind seats prevent metal/wood overlap without changing the
cutting silhouette. The hardware groups contribute no wood or extra hinge purchases to the cut list.
Actual recesses, joint gap and fixing details remain unmeasured. The two leaves have separate cutting profiles on
the same 18mm plywood stock as the bench frames, so their pieces share sheet layouts. There is one Lagun kit. The current
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
Leaving Human view preserves its current eye, viewing direction and perspective. Its exit target uses the existing
centre-screen CAD picker, falling back to the current look ray’s intersection with the fixed cargo bounds. An eye
outside the van looking away gets a finite look-ray distance based on the cargo size; it is not moved or turned.
Camera persistence skips transient Human-view poses and saves the rebased orbit target on exit. Geometry replacement
cancels Human view before capturing the camera to preserve, so regeneration cannot restore a distant look target.

`viewer-pieces.ts` owns one **Reset view** command, used by the icon-only toolbar button, context menu and **R**
while the viewport is focused. The old separate resize/recenter buttons are absent. Reset centres on the fixed
cargo-floor and roof bounds, excluding the cab, moving doors and scan outliers, and computes camera distance/orthographic zoom from their
projected corners and the current field of view/aspect ratio. It keeps viewing direction and saves the new pose.
The renderer's Reset entry point delegates to this same command rather than restoring a stale saved target.
The native button name and activation follow [WAI-ARIA button guidance](https://www.w3.org/WAI/ARIA/apg/patterns/button/).
Shortcut focus follows [WCAG character-key guidance](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html);
R is limited to the focused viewport, preserving menu and text-field navigation.
Pointer capture/release follows the [W3C Pointer Lock specification](https://w3c.github.io/pointerlock/).

The toggle uses a stable accessible name and `aria-pressed` following the
[WAI button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/). Controls appear while active; navigation keys
are scoped to the focused viewport, editable controls retain their normal input, and Escape exits without trapping focus.
