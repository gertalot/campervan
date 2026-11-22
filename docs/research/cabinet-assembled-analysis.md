# Assembled cabinet: 6mm versus 3mm skins and backings

Calculated 22 November 2026 from the current CAD, including the rearward furniture refit and raised floor. This
supersedes the isolated-shelf calculations for assessing assembled-cabinet movement. The CAD design and selected
materials were not changed.

## Results

Both variants carry **12kg distributed on each of five shelves**, plus a **20kg equivalent empty-cabinet mass**. The
empty mass is distributed over the structural wood in proportion to its density-weighted volume; it includes an
allowance for doors, hardware and finishes, rather than resolving their individual inertial attachment loads. All five
shelves remain **6mm plywood**. Only supporting skins and backings change to 3mm.

Shelf values are maximum instantaneous downward displacement including movement of their supports, under gravity. Sway
is the additional maximum timber-frame displacement along the applied 0.5g direction, after subtracting gravity. It
excludes local backing bow. The lateral cases also include gravity.

| Response | 6mm skins/backs, mm | 3mm skins/backs, mm |
|---|---:|---:|
| Rear, middle shelf | 2.474 | 2.559 |
| Cab-end, lowest shelf | 0.442 | 0.465 |
| Cab-end, middle shelf | 1.011 | 1.075 |
| Rear, upper shelf | 0.477 | 0.501 |
| Cab-end, upper shelf | 0.384 | 0.402 |
| Frame sway across van, 0.5g | 0.090 | 0.123 |
| Frame sway along van, 0.5g | 0.235 | 0.269 |
| Supporting-panel local lateral flex along van, 0.5g | 0.237 | 0.435 |

Displayed digits document the numerical output; they are not the accuracy of the scan, material data or construction.
The two modeled assemblies save approximately 1.80kg of structural wood at the assumed densities, before redistributing
the standardized 20kg empty-cabinet load for the comparison.

## What was actually modeled

Each variant uses 70 actual CAD wood solids: shelves, supporting panels, leaning backings, frame members, bridge,
joining rails and glue cleats. Doors, hardware and the removable upper infill do not provide bracing stiffness. The 3mm
variant is rebuilt through the existing thickness parameter. Receiving backing ends are extended/trimmed by 3mm where
required to meet the thinner skins without gaps or overlapping sheets. Bay and shelf dimensions follow the existing CAD
parameter dependencies. Material stiffness is not halved in a 6mm solid as a thickness substitute.

The assumed connections are consequential:

- All touching wood faces within each module are bonded, including shelf/front-frame and shelf/backing contacts.
- The four side-rail/shelf interfaces are locked in three directions, representing tightened module bolts without slip.
  The modules' front uprights are **not** welded: their butt joints carry compression only, open when required,
  and transfer no tangential force across the seam.
- Floor-standing timber feet are fixed in three directions; supporting-plywood floor edges are restrained vertically.
  This is a rigid attached-floor approximation, not a deformable plywood/van-floor model.
- Four upper front-frame locations are restrained laterally over their upper 10mm, with rigid attachment/packers
  assumed to connect them to the ceiling timber. Vertical ceiling restraint is omitted.

Plywood is assigned effective isotropic E = 3,000MPa, pine E = 8,000MPa, and Poisson ratio 0.3 for both. Density
assumptions are 450kg/m³ plywood and 500kg/m³ pine. These are comparative engineering assumptions, **not measured
properties or rated design values of the selected Tigerply or an identified 3mm product**.

## Calculation and numerical checks

Gmsh 4.15.2 generated conformal tetrahedral meshes from the CAD BReps. The detachable interface nodes were then
separated and only the specified joint constraints/contact were applied. scikit-fem 12.0.2 solved coupled 3D linear
elasticity using quadratic tetrahedra. Compression-only contact was solved through the interface compliance matrix and a
nonnegative least-squares complementarity formulation. NumPy 2.5.4 and SciPy 1.18.1 were used.

The final meshes contain 418,878 and 426,519 displacement degrees of freedom. The 35mm and 25mm nominal mesh-size
targets were compared: the largest change in any reported shelf displacement was 0.081mm; the largest frame-sway change
was 0.0056mm. This supports rounded screening values, not thousandths-of-a-millimetre predictions. Local 3mm
supporting-panel flex changes by approximately 0.10mm between these meshes and is less converged than the main-frame
values. Negligible scan/boolean sliver tetrahedra below 0.001mm³ were removed before assembly; fewer than 0.02mm³ were
removed from each approximately 24 million mm³ assembly. Both assemblies have one connected structural component after
applying the module joints. Maximum force imbalance was 2.5e-07N and moment imbalance 0.00032Nmm. Contact gaps and
compressive reactions satisfy complementarity within numerical precision. No project tests or application services were
started; these checks are intrinsic to the numerical calculation.

This answers **conditional assembled stiffness**, not failure capacity. Orthotropic layup, plywood buckling, creep, glue
peel/failure, bolt slip and actual vehicle-anchor compliance are not established by this solve. The small computed
sag/sway penalty therefore cannot, by itself, certify 3mm supporting skins as adequate.

## Evidence and reproduction

- Geometry: [cabinet construction notes](../cad-model.md), `cabinet.py`, `cabinet_backing.py`,
  `cabinet_layout.py`, `cabinet_modules.py` and the current `scan_scribe_data.py`.
- [Model parameters, source fingerprints and assumptions](cabinet-assembled-analysis/provenance.json).
- [6mm final raw results](cabinet-assembled-analysis/6mm-results-25.json),
  [3mm final raw results](cabinet-assembled-analysis/3mm-results-25.json),
  [comparison CSV](cabinet-assembled-analysis/comparison.csv).
- Numerical formulation: [scikit-fem 3D elasticity example](https://github.com/kinnala/scikit-fem/blob/master/docs/examples/ex11.py)
  and [Gmsh's official documentation](https://gmsh.info/doc/texinfo/).
- Calculation scripts and exported CAD/meshes are retained in `.local/cabinet-deflection/full/`:
  `export_geometry.py`, `mesh_geometry.py`, `solve.py`, and `report.py`.

From the repository root, repeat each command with thickness arguments `6` and `3`:

```sh
uv run --locked python .local/cabinet-deflection/full/export_geometry.py 6
uv run --locked --with gmsh==4.15.2 --with scikit-fem==12.0.2 python .local/cabinet-deflection/full/mesh_geometry.py 6 25
uv run --locked --with gmsh==4.15.2 --with scikit-fem==12.0.2 python .local/cabinet-deflection/full/solve.py 6 25
```

No project dependency was added. Run the 6mm and 3mm solves sequentially on this 16GB computer. Use mesh-size argument
`35` instead of `25` to reproduce the refinement comparison.


