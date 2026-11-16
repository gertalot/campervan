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
Both upper rails and their flanges are trimmed 18mm at the gas-spring end, from 600mm to 582mm.
All pivots remain in their original positions; the photo-estimated 75mm end overhang becomes 57mm.

`cad/bed_lift.py` intersects the arm circles at each lid angle. The same poses build the CAD and generate browser
tracks for the lid, both arms, upper rails and telescoping gas springs. Tracks sample each percentage point; the
browser interpolates between samples. Dragging uses all tracks for the picked component, including translation.

Using D340 as the opening stop gives about 34.1 degrees. For a closed lid underside at X22/Z354, its rear edge
moves 79.6mm aisleward and finishes 7.3mm higher. It stays at or above its closed height throughout the fitted stroke.
The spring spans approximately 208–340mm. These results describe the fitted model, not verified product tolerances.
Fixed pivots are approximately X113.3/X463.3 at Z265.9, on the two end-panel inside faces (Y173/Y1262).
All coordinates precede the shared bed offset and vehicle mirroring.

The rear end panel moves forward to local Y155–173 (world Y255–273), 30mm beyond the modelled rear corner's
Y225 extent. Its rear lift moves with the panel. The upper mounting rail spans Y173–203, beneath the solid lid
rib Y155–275, giving continuous plywood for its fixings. These positions follow the first suitable complete rib
ahead of the modelled corner, using the same slot bounds as the lid. Scanned-mesh clearance needs visual confirmation.
The wall-side longitudinal panel starts flush with the rear end panel at Y155, shortening it to 1125mm.
The centre divider and aisle-side panel retain their positions; the two storage bays are no longer equal.
Both longitudinal panels have two open-top notches: local Y168–208 and Y1227–1267, each 40mm wide and 40mm deep.
The 30mm upper rail has 5mm clearance on each side; depth is 10mm greater than the previous 30mm notches.
The flange and rear-arm sweep stay above Z326; notch floors are Z314. These are clearances for the current
photo-derived hardware model, not measured installation tolerances.

The lid has seven 400 × 50mm through-slots. Its aisle edge is recessed 18mm to X604, making the main body
582 × 1280 × 18mm with an 82mm aisle band and 100mm wall-side band. Its former full-width hinge tabs are removed:
the shortened 582mm upper rails now fit entirely beneath the recessed lid.
The stationary 100mm strip and its short fixed-slat ends are removed. Fixed slats are 567mm long, shortened
10mm at the aisle end and a further 18mm at the wall end: X45–612 retracted. Moving slats are 559mm (X45–604),
butting against the raised support frame. Both sets have square ends and retain the 5mm wall-end trim.
`bed_slat_rear_setback_mm` is zero.
A wall-side cushion rail is 18 × 1212 × 50mm after the rear corner trim, spanning X22–40, Y68–1280 and Z372–422.
It matches the sliding frame's upper height, leaves the existing 5mm gap to the shortened slats, and follows
the lid as a fixed cushion-retaining edge. Slat aisle ends, bracket positions and fixed-slat groove engagement stay unchanged.
Extension travel is 448mm, preserving the 1070mm extended bed width. The box-wall positions are unchanged.
The moving support is one 18mm plywood frame at X604–622 alongside the recessed lid edge, without spacer blocks
or metal table legs. It reaches from the floor to Z422, including a continuous 50mm rise above the slat undersides.
The lower top rail is 50mm high (Z322–372), with 60mm-wide integral legs and a rounded open-bottom cutout using the existing
cross-bench frame helper and 25mm radius. Leg width/radius follow `member_width_mm` and `inside_radius_mm`;
`bed_moving_rail_height_mm` controls the lower top member's height. The frame spans the full bench length,
Y0–1280. The metal-leg parameter and purchasing role are retired.
It has no hinge notches. The stationary box walls retain their 40 × 40mm notches and 5mm side clearances.
The former teeth are replaced by the smooth, continuous outer face. Eight rounded inside-face router grooves
are 84 × 22mm and 8mm deep, at Z370–392, leaving 10mm of outer plywood intact. The fixed slats enter these
grooves by 8mm when retracted; 2mm clearance is provided above, below and at either side. Their ends meet the
groove backs, so the 8mm depth does not include additional end clearance. The groove ceilings pick up the fixed
slats after 2mm of relative vertical movement, retaining the sliding frame when lifting the lid. This is geometric
engagement, not a load rating; the animation carries the retracted frame with the lid without modelling take-up.
Nominal internal groove corner radius is 2mm. First/last grooves retain 3mm end margins and the continuous outer skin.
Angles remain face-mounted beneath the shortened moving slat ends, in their original positions. The rail's
lower edge is raised 20mm to align with the bracket bottoms; no bracket pockets are cut in the rail.
Seven existing-catalogue [Carinya 50 × 50 × 40 × 2mm angles](https://www.bunnings.co.nz/carinya-50-x-50-x-40-x-2mm-galvanised-reinforcing-angle-bracket-8-pack_p3962402)
tie each moving slat underside to the frame's wall-side face. Their 50mm vertical flanges match the lower top member.
Each angle has a 51 × 42mm top rebate, just 3mm deep (2mm steel plus 1mm clearance), retaining 15mm plywood below.
The vertical flange alone needs a narrow 3mm-wide through-relief at the aisle edge. The rebates span X553–604,
leaving 31mm of plywood before the ventilation slots at X522; the edge relief spans X601–604.
They move out through the open notches with the sliding frame. The lower flanges clear the stationary aisle wall
by 4mm, and the horizontal flanges sit 16mm above the box tops. Hole positions in CAD are illustrative; actual
bracket holes and short screw lengths need matching to the supplied hardware. No quantified stiffness/load rating
is established by the geometry. The BOM counts the bracket leaves, so seven pieces require one existing eight-pack.
Cushion storage placement uses the linkage delta for blue. The display fits its width uniformly between
the rails and allows at most 3mm thickness compression during lifting. Orange remains upright, lifts as a
whole and compresses at most 3mm at its lower edge. Its vertices stay above blue's final top plane with
0.5mm clearance, separating triangle interiors too. This is one direct pose update, with no physics,
iterations, gravity or settling. Manufactured dimensions stay unchanged. Storage transforms remain on
the `Foam` children and conversion transforms on their parents.

The existing running model regeneration and logs are the validation route. No tests or extra check processes are run.

The first animation incorrectly overwrote only Euler Y after Three.js decomposed rotations above 90 degrees into
X/Z half-turns. Bed-member tracks now explicitly set X and Z to zero as well as Y, retaining the calculated arm
directions. The gas spring is outboard of the arm layers, with estimated through-pins connecting both attachment
points and the upper arm pivots to the mounting flange. Pin/section dimensions remain illustrative.
