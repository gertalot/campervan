# Rear pillar/floor surface-fitting trial — 2026-11-11

Historical trial, superseded by the feature-by-feature floor modelling recorded in
[CAD model conventions](../cad-model.md). Its proposed follow-up below is not the current implementation plan.

## Outcome

The installed stack can produce smooth native CAD solids from a low-complexity, robustly regularized surface fit.
The trial does not establish an accurate physical van model or a usable plywood cutting boundary. It exposes a
material discrepancy between the two reconstructed sides and between source views. The application CAD was not
changed during this trial.

## Method checked against the available tools

- [PCL's B-spline fitting tutorial](https://pointclouds.org/documentation/tutorials/bspline_fitting.html) documents
  low-complexity fitting/refinement with smoothness, and warns about folding around holes and steps. PCL was not
  installed; its documented method informed the investigation.
- [SciPy's spline design matrix](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.BSpline.design_matrix.html)
  supplies basis evaluations for fitting a tensor-product control net. Robust iterative reweighting was applied to
  data residuals while second differences of the control net received a separate quadratic fairness penalty.
- [OCCT's surface approximation](https://occt3d.com/dev/doc/refman/html/class_geom_a_p_i___points_to_b_spline_surface.html)
  and installed `build123d.Face.make_surface_from_array_of_points` provide ordered-grid approximation and optional
  variational smoothing. That interface is not a robust scattered-point estimator; simply smoothing the former grid
  would not solve the problem.
- The fitted control net can be converted directly with `OCP.Geom.Geom_BSplineSurface` and
  `BRepBuilderAPI_MakeFace`, without refitting an evaluated grid. Installed OCP 8 uses `OCP.collections.Array2_gp_Pnt`,
  `Array1_double` and `Array1_int`. `Solid.thicken` produced native 1mm closed-solid STEP trial pieces.

This is approximation of observed geometry, not arbitrary assignment of primitive shapes. Planes/cylinders should
only replace freeform patches where their residuals and physical feature evidence support that simplification.

## Data and bounded experiment

Source: `corrected-7605be9e-6933-4e0e-b64d-1c8d94c0e6e1`, full mesh and original exported depth images with corrected
camera poses. The existing saved capture-to-CAD transform was used. Region: approximately X=0–260, Y=45–230,
Z=-35–360mm around one rear pillar base; opposite-side coordinates were reflected for comparison.

A single diagonal-projection surface was tried first across the combined region. Its best spatially blocked mesh
holdout P95 was 10.5mm. That result did not justify a CAD replacement. The projection's apparent multi-height spread
also mixes local slope, side disagreement and potentially distinct surfaces; it is not itself proof of a fold.

The follow-up separated upright pillar and floor samples by orientation, height and position, then fitted each side
independently as a diagnostic. This deliberately does not assert physical left/right asymmetry. Each dataset was
spatially downsampled to 5mm. Cubic control nets of 4×4, 6×4 and 8×5 were compared at three fairness weights, with
robust residual weighting at a 3mm scale. These are bounded experiment settings, not established sensor noise or
manufacturing tolerances. The selection preferred a smaller net within 1mm of the best blocked P95.

Contiguous spatial blocks were withheld, rather than random adjacent vertices. Original depth views were also
compared, with local depth-derived normals and the same geometric masks. These views supplied the fused mesh:
they diagnose consistency, but are not independent physical ground truth. Earlier distance-filtered source-view
figures in `segmented-report.json` are superseded by `view-consistency.json`, which rejects no observations based
on fitting residual.

## Results

Distances below are first-order normal-distance estimates, not exact closest-point distances. Small residuals make
this useful for a fitting trial; they must not be quoted as certified physical accuracy.

| Patch | Mesh samples | Control net | Withheld mesh median | Withheld mesh P95 |
| --- | ---: | --- | ---: | ---: |
| Left pillar | 886 | 8×5 | 0.69mm | 2.48mm |
| Right pillar | 992 | 4×4 | 0.84mm | 3.20mm |
| Left floor | 1,069 | 4×4 | 0.33mm | 1.32mm |
| Right floor | 1,045 | 4×4 | 0.40mm | 1.35mm |

The independent fitted sides disagree in shared supported coordinates:

| Region | Median absolute coordinate difference | P95 coordinate difference |
| --- | ---: | ---: |
| Pillar, lateral X | 12.2mm | 24.2mm |
| Floor, height Z | 6.58mm | 9.05mm |

These are coordinate differences, not orthogonal fitting errors. The appropriate interpretation is unresolved
capture/registration/feature correspondence inconsistency, not a reason to model an asymmetric van or blindly
average two conflicting shapes.

Source-view signed median approximate-normal residuals span about -30 to +14mm in the pillar comparison and
-15 to +12mm for the floor. Selection by local measured normals is imperfect, so these figures require inspection
before attributing all disagreement to pose error or depth bias. They establish that a low mesh residual alone
cannot settle the physical surface. Prior depth diagnostics already show rounding and fusion changes; fitting
cannot recover missing observations or prove the true shape through smoothing.

## Artifacts

All detailed data, reproducible scripts and STEP trials are local under:
`.local/experiments/rear-pillar-surface-fit/`.

- `analyse.py`, `segmented.py`, `view_consistency.py`: extraction and bounded fitting experiment.
- `report.json`, `segmented-report.json`, `view-consistency.json`: results and limitations.
- `surface-fit-sections.png` / `.svg`: exact-Y sections; dots are mesh observations, lines are smooth fitted surfaces.
- `surface-fit-residuals.png` / `.svg`: spatial residual maps.
- `pillar-left-fit-trial.step`, `pillar-right-fit-trial.step`, `floor-left-fit-trial.step`,
  `floor-right-fit-trial.step`: native thickened B-spline patches, not meshes. Restricted rectangular trims keep
  these as local trial pieces; the rectangles are not claimed to be physical feature boundaries.
- `export_cad.py`, `native-cad-trials.json`: direct control-net conversion, closed-solid export and side comparisons.

## Required next work before making a plywood boundary

1. Identify corresponding physical regions in the discrepant source views and resolve their disagreement using
   original tag/image evidence and applicable owner measurements. Do not declare a single noisy side authoritative.
2. Fit a shared symmetric surface with physically supported patch boundaries. Preserve repeatable pressed features;
   robust weighting must not erase them merely because a coarse patch cannot represent them.
3. Fit the continuous rollover between the separate floor and pillar patches, verifying a usable parameterization
   and appropriate joins. That connection is not established by the four exported trial pieces.
4. Derive the plywood boundary from the fitted surface at its intended installed position and through its thickness.
   The earlier arbitrary height-rise toe, a mesh edge or the closed hatch contour is not a manufacturing cut line.
5. State a physical tolerance and account for unresolved systematic uncertainty before treating the result as a
   cutting template. A small numerical fitting error is only one component of that uncertainty.

No project tests, model downloads, dependency installs, services or review cycles were launched for this trial.
The only CAD generation was the standalone trial STEP export; the application's vehicle model was left unchanged.
