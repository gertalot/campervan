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

The reference assembly is:

```text
Campervan
└── Vehicle references
    ├── Floor outline
    ├── Wheel arches
    │   ├── Left wheel arch
    │   └── Right wheel arch
    └── Rear corners
        ├── Left rear corner
        └── Right rear corner
```

These references use the provisional values in [the Onshape handover](what-we-built-in-onshape.md), backed by
`docs/fs/nv200-interior.fs`. They are not an accurate shell or manufactured parts:

- The floor is a 1500 × 1860 outline, without invented thickness.
- `wheelArchReference` becomes a local box with only the two upper longitudinal-profile corners rounded. Each arch is
  750 long and 280 high, with a 200 radius, starting 216 from the rear. Intrusion is `(cargo width - arch gap) / 2`,
  giving 140 on each side and a 1220 clear gap at the defaults.
- `rearCornerReference` becomes a quarter-circle extruded as a surface, with a 100 radius and 1228 reference height.
  That height comes from the original rear opening height plus its zero sill. There is no wall thickness or door solid.

Inspect changes in OCP. The small geometry smoke check covers named parts, valid geometry, dimensions, rounded-arch
volume and corner surface area. Add direct intersection or clearance checks only as moving or adjacent components
make them useful.
