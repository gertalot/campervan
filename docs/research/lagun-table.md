# Lagun laptop table

Gert's current top is solid 600 × 360 × 18mm plywood. The earlier 9mm top and underside rim have been superseded.
It shares the existing 18mm sheet stock. The table is for use with the bed retracted; remove it for sleeping.

## Model and controls

`cad/table.py` supplies two complete display poses of one physical table:

- The fixed aisle frame's solid cab-end post, beside the shortened moving frame.
- The cabinet's outward-facing cab-end panel, near its aisle edge.

The drawer-frame mounting post is 92mm wide along the van, ending at the cross-bench skin. One matching
92 × 372 × 18mm spacer brings its outer face flush with the retracted moving frame's outer face. The fixed
frame's middle post and all slats retain their positions. The moving frame is shortened a further 5mm at its
cab end, leaving a 5mm overhang beneath the last moving slat.

At the current dimensions, the mounting post and spacer occupy Y=1188–1280mm in furniture coordinates. The
moving frame ends at Y=1185mm, leaving 3mm clearance throughout its 452mm sideways travel. The plate occupies
the same 92mm fore/aft span as the spacer. The illustrative height-clamp handle points vertically so its
envelope also stays within that span. The tie strip stays inside the fixed frame; the moving slats pass above
the spacer at the slat bearing height. The existing runtime dimensional check rejects a frame end reaching
the mounting post. These separations do not certify the unmeasured handle envelope or physical fixings.

The cabinet has its own arrangement: one 18mm and one 9mm spacer, 92 × 190mm, give 27mm of external stand-off.
A 120 × 190 × 18mm backing panel sits inside the cabinet, against the back of its 12mm end panel. The external
stand-off follows [Lagun USA's 1-inch arm-clearance guidance](https://lagunusa.com/instructions/).
The joints and through-fixings still need designing. The standard kit's bolts may need replacing with longer
bolts; drill hole centres from the actual hardware.

The sidebar's **Laptop table** group has a **Show table** selector with **Bench mount**, **Cabinet mount** and
**Stowed (TBD)** choices. Selection switches existing group visibility immediately. Each mounted pose has its own
collapsible group, eye control, arm swivel, tabletop rotation and height. The controls retain separate values in
browser storage and use the existing live-position API and motion tracks. No pose control regenerates CAD or
changes the cutting layout. The group's main eye hides the whole assembly.

Both rotations cover 360°. Height is 620–780mm above the finished wooden floor, initially 700mm for each pose.
At the modelled 18mm top thickness, that range keeps the 500mm upright engaged across the full fixed bracket
height, 180–350mm above the floor. Tabletop length, depth and plywood thickness are shared. Changing those
dimensions uses normal **Apply** and regeneration.

The **Stowed (TBD)** group reserves the third state. Its physical storage position and controls remain to be
designed. Selecting it hides both mounted versions; no storage geometry or location is implied.

The cut list includes one tabletop and the spacer/backing parts for both fixed mounting locations. The cabinet
display copy of the tabletop is excluded from cut quantities and links to the bench copy's cutting piece.
The BOM includes one Lagun kit and one additional mounting bracket, allowing the same table to move between the
two locations. Visual hardware components are excluded from wood cutting layouts. No holes or fasteners are
represented as fabrication templates.

## Dimensions and sources

The [official general drawing, dated 9 March 2026](https://lagunofficial.com/wp-content/uploads/sites/2/2024/10/Lagun-General-Technical-drawing-with-meassurments.pdf)
gives a 500mm upright, 324mm between arm pivots, 38mm from a pivot to the arm end, a 47mm arm height, a 30mm
tabletop fitting and a standard 92 × 170mm furniture bracket. The tabletop plate is approximately 240 × 200mm.
The resulting arm length is 400mm. Upright extrusion depth, grooves, clamp handles, plate profile and internal
pivot details are visual approximations.

[Lagun USA's product dimensions](https://lagunusa.com/product-details/) give an assembled bottom-of-leg to
tabletop-plate height of approximately 23 inches, or 584mm. Adding the 18mm tabletop makes 602mm; the model's
upright bottom is therefore the selected tabletop height minus 602mm.

[Lagun USA's installation instructions](https://lagunusa.com/instructions/) specify a minimum tabletop thickness
of 5/8 inch, approximately 15.9mm, for their screw-mounted arrangement. This is that supplier's installation
guidance. Other thin tabletops may use different materials, fixings or local reinforcement. It is not evidence
that every thinner tabletop is unsuitable. Gert selected an 18mm plywood top.

The model helps compare reach, proportions and clearances. It does not establish the strength of either plywood
mount or prevent the table from being rotated into furniture, a person or the vehicle.
