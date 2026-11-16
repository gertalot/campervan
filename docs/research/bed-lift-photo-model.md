# 600mm bed lift working model

Gert authorised estimating the missing pivot centres from the Instant Panel photograph on 16 November 2026.
This replaces the fixed-axis hinge experiment. It is a kinematic working model, not a drilling template.

Sources: [20kg product](https://instantpanel.co.nz/product/bed-lift-gas-struts-mechanism-frame-assembly-20kg-06m-sku-108774.html),
[dimension photograph](https://instantpanel.co.nz/product_img/OriginalPhotos/BIDX1PS26/gas-struts-frame-assembly-7.jpg),
[half-open guidance](https://instantpanel.co.nz/product_img/OriginalPhotos/BIDX1PS26/gas-struts-frame-assembly-3.jpg).
An independent photo/geometry calculation checked the parameters and circle-intersection branch.

| Dimension | Working value | Evidence |
| --- | ---: | --- |
| Upper rail overall | 600mm | Published A |
| Lower rail overall | 420mm | Published E |
| Long arm centres | 270mm | Published C interpreted as pivot spacing |
| Short arm centres | 95mm | Photograph; B110 is overall height, not arm centres |
| Fixed pivot spacing | 350mm | Photograph |
| Upper pivot spacing | 155mm | Photograph |
| Rear upper pivot from lid rear | 25mm | Photograph |
| Upper pivot below lid underside | 20mm | Photograph |
| Upper gas-spring pin from rear upper pivot | 500mm | Photograph |
| Lower gas-spring pin from front fixed pivot | 125mm along long arm | Photograph |
| Extended spring length | 340mm | Published D interpreted as working opening stop |

The photograph does not have one scale that satisfies every A–E dimension; inferred dimensions are rounded estimates.
Steel sections, shaft/body envelopes and pin diameters are also visual estimates. Capacity choice (20kg versus 30kg),
actual spring stroke, mounting holes, fasteners and stops remain unconfirmed.

`cad/bed_lift.py` intersects the arm circles at each lid angle. The same poses build the CAD and generate browser
tracks for the lid, both arms, upper rails and telescoping gas springs. Tracks sample each percentage point; the
browser interpolates between samples. Dragging uses all tracks for the picked component, including translation.

Using D340 as the opening stop gives about 34.1 degrees. For a closed lid underside at X22/Z354, its rear edge
moves 79.6mm aisleward and finishes 7.3mm higher. It stays at or above its closed height throughout the fitted stroke.
The spring spans approximately 208–340mm. These results describe the fitted model, not verified product tolerances.
Fixed pivots are approximately X113.3/X463.3 at Z265.9, on the two end-panel inside faces (Y18/Y1262).
All coordinates precede the shared bed offset and vehicle mirroring.

The lid is 600 × 1280 × 18mm with seven 400 × 50mm through-slots, retaining 100mm solid bands at both ends.
Its width follows `long_bench_width_mm`; both bands follow `bed_lid_strip_width_mm`.
The stationary 100mm strip and its short fixed-slat ends are removed. The remaining hidden slats retain their old
491mm blanks, 5mm trim and fixed-slat bevel; `bed_slat_rear_setback_mm` preserves their prior start position.
The old moving rail/spacer assembly is retained for the next slat-design step. Its spacers currently occupy part of
the new solid aisle band; this is deferred work, not a completed sliding construction. Metal legs remain provisional.
Cushions retain their separate conversion poses and do not yet ride the lid; cushion clearance remains design work.

The existing running model regeneration and logs are the validation route. No tests or extra check processes are run.

The first animation incorrectly overwrote only Euler Y after Three.js decomposed rotations above 90 degrees into
X/Z half-turns. Bed-member tracks now explicitly set X and Z to zero as well as Y, retaining the calculated arm
directions. The gas spring is outboard of the arm layers, with estimated through-pins connecting both attachment
points and the upper arm pivots to the mounting flange. Pin/section dimensions remain illustrative.
