# Longitudinal sliding slats implementation plan

**Goal:** Add the approved interleaving slat mechanism to the existing NV200 feature and drive it with Day/Night.
**Architecture:** Reuse makeBlock and benchWall. Keep fixed carcasses unchanged; derive moving geometry from dimensions.
**Tech Stack:** Onshape FeatureScript 3095 and transient Onshape evaluation.
**Spec:** Current conversation and nv200-bench-design.md; fixed570, closed588, open1070, 80x18 slats, 40x18 inner strip.

## Work
- Add focused failing geometry checks to nv200-slats-validation.fs.
- Implement named slat, strip, ledge and clearance inputs in nv200-interior.fs.
- Reuse the two-bay aisle frame for the moving frame. Day retracts; night extends.
- Put the rear transverse ledge at the corner setback to clear the missing rear corner.
- Check bounds, part counts, contacts/interference, intermediate travel, altered dimensions and invalid combinations.
- Independently review; resolve findings before saving Feature Studio once and checking exact source readback.
- Update nv200-bench-design.md and nv200-onshape-model.json with actual results and remaining limits.

## Constraints and review focus
Preserve stored dimensions, cushion visibility and reference geometry. No cross-bench top added.
Fixed width remains570; moving frame adds18 in day mode. Nominal frame contacts have no extra running gap.
Ledges and strip are18ply; ledge projection25 and strip end clearance2 are editable modelling defaults.
Rear fixed slat shortened for120 corner setback. All moving slats must attach to the strip.
Tests distinguish nominal contact from solid interference. Hardware, fastening and strength are not certified.

