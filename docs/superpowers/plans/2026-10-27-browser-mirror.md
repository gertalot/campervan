# Browser mirror implementation plan

Goal: switch between the current and reflected interior instantly in the local app and static site.

Keep the vehicle, floor and camera fixed. Reflect furniture, stored gear and people through the van centreline.
Retain the original CAD geometry, motion coordinates, source fingerprints and saved cutting layouts.

- [x] Add a saved Cabinet side radio group alongside the live controls, preserving the former checkbox preference.
- [x] Wrap the existing furniture groups with a reflection transform, retaining named CAD paths and local motions.
- [x] Fit mannequins and deform cushions in the original coordinates before reflecting their display together.
- [x] Account for reflected handedness in hinge dragging and table steering; preserve picking and highlights.
- [x] Reflect complete cutting drawings with readable labels, including saved SVGs, without rerunning optimisation.
- [x] Document preview/export semantics and the fixed vehicle's asymmetric openings.
- [x] Build the static site once and inspect the resulting changes. No tests, services or browser interaction checks.

The complete-sheet drawing reflection preserves the saved nesting, kerf and saw sequence. Views of through-cut
profiles may use the reverse face; blind pockets and edge finishing remain separate operations.
Native CAD/STEP exports retain their saved orientation. Gert's visual inspection checks fit and interaction behavior.

`make site` completed successfully. Existing missing/stale cutting-layout warnings remain; no layouts were regenerated.
