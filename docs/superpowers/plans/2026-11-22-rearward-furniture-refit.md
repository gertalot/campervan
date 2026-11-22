# Rearward furniture refit implementation plan

**Goal:** Move both benches and the cabinet 20mm rearward while retaining their vehicle clearances and joinery.

**Architecture:** Use the existing shared furniture rear offset and existing scan-profile authoring pipeline.
Vehicle, floor and stored gear retain their positions. Regenerate cabinet fitting data at the new registration;
keep bench arch/seal cuts vehicle-fixed and refit the rear-pillar chamfer and support/hinge datums together.

**Constraints:** No tests or services. Use existing runtime constraints, focused geometry inspection and Gert's
visual inspection. Cabinet scan clearance remains 3mm; bench arch/seal clearance remains 5mm. Preserve the
cabinet backing angles, module guide lips, flush shelf joints and supported module bolts.

- [x] Inspect bench rear-pillar and connected hardware datums; adjust the existing common datum as needed.
- [x] Regenerate the five backing profiles at cabinet rear Y80 using the existing angles and scan registration.
- [x] Rebuild the cabinet and regenerate measured wood clearance profiles, including its filler and glue cleats.
- [x] Set furniture rear offset to 80mm and publish the refitted model.
- [x] Inspect runtime constraints, current cutting data, vehicle clearances and unchanged floor/gear positions.
- [x] Update model documentation with the final datums and verification limits.

## Observed result

- Model and cut data published at rear offset 80mm; cabinet rear Y80, cross-cushion rear Y1360.
- The rear-pillar plane remains fixed; rear support Y168–186, first fixed-slat chamfer 60mm, wall panel 1192mm.
- Ten cabinet wood profiles and five backing profiles regenerated. Published inspection of 42 cabinet parts
  found no scan samples below 3mm (minimum 3.023mm). Bench arch/seal checks found no samples below 5mm
  (minimum 5.513mm); all cross-bench wood passed 5mm (minimum 6.245mm).
- Final cross-bench slat has a square pillar-clearing wall end at construction X100, with full wall-frame bearing;
  its finished dimensions are 994 × 80 × 18mm.
- Module bolt support constraints passed. Floor and gear positions stayed unchanged; solar-bag gap is 7mm.
- No tests or services were started. These are scan-relative sampled clearances; physical fitting and Gert's
  visual inspection remain the acceptance checks.

The final cabinet inset is zero: published rear faces of the sliding frame and both cabinet modules all measure
Y80. The former 10mm cabinet-only inset was removed and its backing/scribe profiles regenerated at that position.
The separate 6mm across-van hinge-barrel clearance remains intentional.
