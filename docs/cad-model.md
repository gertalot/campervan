# CAD model conventions

Use millimetres, with the nominal rear-left floor corner at the origin. X runs across the van from the long-bench wall
toward the cabinet wall, Y runs from the rear doors toward the cab, and Z points up. This preserves the FeatureScript
coordinates and motion directions.

`src/campervan/cad/model.py` assembles the campervan. Component modules such as `vehicle.py` construct native build123d
geometry. `src/campervan/parameters.py` owns editable dimensions, their constraints and sidebar metadata. Geometry code
does not call FastAPI or the viewer.

Use native `Compound(label=..., children=...)` assemblies. Keep each physical part separate and use named subassemblies
for parts that belong or move together. Build reusable parts at a local origin and place them using `Location`.
Keep labels consistent across regeneration. Add modules and groups as actual components arrive; do not prebuild a
component framework or a second scene graph.

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
│   └── Rear corners
│       ├── Left rear corner
│       └── Right rear corner
└── Long bench
    ├── Fixed frame
    │   ├── Wall-side frame
    │   ├── Aisle frame
    │   ├── Cab-end frame
    │   ├── Cab-end skin
    │   ├── Internal drawer-support frame
    │   └── Rear header
    └── Sliding bed
        ├── Fixed slats
        ├── Guide ledges
        └── Sliding assembly
            ├── Moving slats
            ├── Moving aisle frame
            ├── Tie strip / extension stop
            └── Angle brackets
```

These references use the provisional values in [the Onshape handover](what-we-built-in-onshape.md), backed by
`docs/fs/nv200-interior.fs`. They are not an accurate shell or manufactured parts:

- The floor is a 1500 × 1860 outline, without invented thickness.
- `wheelArchReference` becomes a local box with only the two upper longitudinal-profile corners rounded. Each arch is
  750 long and 280 high, with a 200 radius, starting 216 from the rear. Intrusion is `(cargo width - arch gap) / 2`,
  giving 140 on each side and a 1220 clear gap at the defaults.
- `rearCornerReference` becomes a quarter-circle extruded as a surface, with a 100 radius and 1228 reference height.
  That height comes from the original rear opening height plus its zero sill. There is no wall thickness or door solid.

`bench.py` ports the long-bench branch of `benchCarcass`, `wheelArchFrame`, `slideMountFrame`, `drawerRearFrame` and
the fixed mounting frame with its raised rear post from `rearDrawer`. `panels.py` builds local plywood panels and
rounded opening cutters; X runs along each panel, Y through its thickness and Z upwards. Assembly placement uses
`Location`, keeping each cut plywood piece a separate solid.

The long bench has a 600 × 1280 footprint. Its frame top is `platform height - slat thickness`, or 382 at the defaults.
The aisle frame retains its 100-high slide mounting band. Wall-side openings reach the floor and clear the wheel arch;
the rear support starts at 120, with a 36 rear arch gap. The cab end has separate 18-thick frame and 7-thick skin.
The internal support sits at X = 150–168 and reaches the rear header with an integral raised post. The header spans
X = 168–582, Y = 0–18, Z = 322–382, leaving the drawer exit open.

`sliding_bed.py` ports `longSlatDimensions`, the long-bench branch of `slidingSlatAssembly`, `slidingBracketDimensions`,
`slideAngleBracket` and `slidingBenchBrackets`. Eight fixed and seven moving slats alternate on an 85 pitch. Ordinary
slats are 611 long; the rear fixed slat is 468 long to clear the rear corner and bear on the internal drawer support.
The slat top is 400. The 40 × 18 tie strip sits at X = 90–130, Y = 122–1253, Z = 364–382 when retracted, supported on
two fixed 25-wide ledges. Both ledges extend down to the adjoining frame top rails' underside:
`frame top - member width`, or Z = 322. Their tops stay at Z = 364, giving a 42 vertical depth at the defaults.
These deepened ledges supersede the original flat 18-thick Onshape strips.
Three provisional 50 × 50 × 40 × 2 steel angles have a 3 inside bend radius and sit at
Y = 130, 640 and 1150. The fixed aisle frame has 42-wide reliefs: a 6-deep top notch and a face pocket 6 deep and 51 high.
Screw holes and actual installed hardware dimensions are not modelled.

`BedLayout` holds the derived spacing and travel shared by construction and relief cuts. `bed_extension_percent` moves
the entire `Sliding assembly` with one parent `Location`: 0 is retracted and 100 extends by
`bed width - long bench width - frame thickness` (452 at defaults). Full extension reaches X = 1070, retains 159 slat
overlap, and brings the tie strip against the fixed aisle frame at X = 582. Child locations stay relative to the moving
group; use `global_location` when checking individual children in world coordinates.

Dimensions rebuild geometry. Bed position also exists as a live viewer control: `viewer.py` publishes an OCP translation
track for the sliding assembly after each `show`. Its offsets account for the pose used when building the model.
The sidebar sends `set_relative_time` directly to the existing viewer iframe on slider input, and saves the selected
percentage through `PATCH /api/v1/model/position` on release. That endpoint updates the retained parameters without
creating a regeneration revision. After a new geometry publication, the browser reapplies its selected percentage.
The Python model still applies the same position when constructed for geometry checks or future exports.
This uses OCP's animation timeline for the single bed motion; independent mechanisms will need separate controls as
they are added. The sidebar is the application position control; OCP's own animation playback is a viewer preview.

Category visibility is also viewer state. The worker returns OCP's published model paths through the model status;
the frontend matches Vehicle and Slats paths and sends a batched `ui` message with `config.states` to the iframe.
Slats covers both fixed and moving slats. Browser localStorage retains each checkbox, and each new publication reapplies
those choices. These controls do not regenerate geometry or change CAD parameters.

The drawer tray/slides and cross bench belong to subsequent component increments.
The fixed-frame smoke check covers valid single-solid pieces, dimensions and unintended volume intersections between
the plywood pieces and with the left wheel arch, at the default and one adjusted bench size.
The sliding-bed check samples 0%, 50% and 100% extension for interference with stationary parts and the wheel arch;
this is a small sanity check, not a continuous motion proof.

Inspect changes in OCP. The small geometry smoke check covers named parts, valid geometry, dimensions, rounded-arch
volume and corner surface area. Add direct intersection or clearance checks only as moving or adjacent components
make them useful.
