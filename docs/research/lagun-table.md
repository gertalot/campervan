# Lagun laptop table

Gert's current top has two **600 × 200 × 18mm plywood leaves**. The second leaf folds onto the first:
200mm folded width and 400mm open width. The folded stack is 36mm thick; the flat open top is 18mm thick.
The length remains editable. The table is for use with the bed retracted; remove it for sleeping.

The tabletop uses the same 18mm Tigerply plywood stock as the bench frames. Its two leaves are grouped
with those parts for sheet layouts; no separate laminated pine or bamboo panel is required. Finish both
faces and edges, including hinge pockets. Grain follows the 600mm length.

Each leaf has 20mm plan-view corner radii and a 3mm round-over on its top and bottom perimeter edges. These
design dimensions have controls in the sidebar. The cut list carries the rounded outlines; edge round-over
is a finishing operation. Nominal blind seats show the hinge fit in CAD; fabrication dimensions and timber
pilot holes await measurements of the selected hardware.

The hinge axis follows the long seam at the upper surface of the fixed leaf. **Unfold tabletop** controls a
180° fold: 0% stacks the leaves, 100% places them flat. The open tabletop height control measures the fixed
leaf's top surface. The upper surface of the folded stack is one panel thickness higher. Fold, swivel, rotation
and mount offset all update live without regeneration. Absolute rotation tracks keep intermediate fold poses
above the fixed leaf even when a stored 180° pose uses a different Euler decomposition.

Gert selected [Homer HOM006136 folding-table hinges](https://fostersshipchandlery.co.nz/products/table-hinge-homer-pair)
on 27 October 2026. The BOM includes two hinges, supplied as **one pair at $75.67**. Fosters specifies a
dual-pin mechanism that supports the tabletop horizontally and folds over 180°. Its published dimensions
are 114mm open length, 42mm maximum width and 38mm pin width.

[Folding-table hinge research](table-hinges.md) records the selection and fitting requirements for this top.
The CAD shows two tapered, countersunk Homer hinges in both table poses, with their centres at 20% and 80%
of the tabletop length: 120mm from each end of the current 600mm top. Each half follows its timber leaf
through the existing fold animation. The 114 × 42mm open footprint and 38mm pin width follow Fosters.
The 3mm metal thickness, 4mm pivot offsets, 3mm barrel radii, taper, corner radii and hole pattern are visual
approximations from the photograph. Nominal blind seats extend 6mm below the upper face, leaving 12mm of the 18mm pine beneath them. They provide
no drilling or routing template. The centre links follow the schematic seam pivot; their motion does not
establish the physical dual-pin mechanism's clearance or required joint gap. The 36mm folded wood stack
and nominal 113mm stored assembly remain the existing preview dimensions. Final load capacity, locations,
recess geometry and fixings still need establishing on the hardware.

## Model and controls

`cad/table.py` supplies the bench-mounted table. The cabinet mounting option, its controls, plywood pieces and
additional bracket have been removed. The Stowed display group shows the folded top with its disassembled leg.

The mounting bracket faces the aisle on the long box's cab-end area. The sliding support frame ends 102mm
before the box end, at Y1178, with its integral cab-end leg relocated accordingly. The last moving-slat angle
ends at Y1170 and remains fully supported. An 18 × 97mm plywood mounting pad spans floor to box top
(currently 364mm high). The pad occupies Y1183–1280, flush with the box end and 5mm clear of the frame.
The bracket remains at Y1183–1275. The pad spaces the upright beyond the fixed slats.
The bracket origin is X638/Y1229 including the accepted 24mm inward bed offset. Its normal faces +X;
the arm orientation retains the old −90° heading so the saved swivel/tabletop directions are preserved.
The detached Stowed preview keeps its own position. The cross bench's frames are unchanged.

Before the shared 24mm bed offset, the upright body occupies X627–665. The fixed slats' aisle edge peaks at
approximately X612.97 through the fitted lift stroke, leaving about 14mm clearance to the upright.
With the saved 750mm table height, the folded top's underside is Z=732 versus the bed slat top at Z=390.
These are model envelope clearances; handles, holes and fixings still require checking against the actual hardware.
The upright occupies part of the extended bed's space; the Table checkbox leaves the selected pose unchanged
during bed conversion or storage-lid movement, so clearances are for visual inspection.

The **Table** checkbox in **Visibility** selects **Bench mount** when checked and **Stowed** when unchecked.
Selection switches visibility immediately and persists regardless of bed/couch position or reloads.
The Bench mount group has live height, arm swivel, tabletop rotation
and **Mount towards short edge** controls, plus the fold control described above. Values persist in browser storage and use the existing live-position
API and motion tracks. No pose control regenerates CAD or changes the cutting layout.

The offset ranges from −100% to +100%. Zero centres the mounting plate; either end places the plate's footprint
flush with one short tabletop edge. The 240mm plate axis follows the tabletop length, and the maximum offset
is (tabletop length − 240mm) / 2: 180mm for a 600mm top, or 230mm for a 700mm top. This previews where the plate
would be fastened; it does not add a sliding mechanism. The wood moves relative to the plate and pivot. Top
rotation still rotates both together. The mounting joints and through-fixings still need designing.

Both rotations cover 360°. Height is 620–780mm above the finished wooden floor, initially 700mm for each pose.
At the selected 18mm top thickness, that range keeps the 500mm upright engaged across the full fixed bracket
height, 180–350mm above the floor. Tabletop length, folded width and timber thickness are shared. Changing those
dimensions uses normal **Apply** and regeneration.

The **Stowed** group shows the folded tabletop, with the arm still attached to its tabletop pivot and swung
along the tabletop length. The upright is detached, turned parallel to the arm and placed beneath the mounting
plate's storage channel. The furniture bracket and plywood spacer remain installed on the bench in both modes.
Both poses use the same component builders. Only the working pose contributes wood to the cut list; selecting a
timber leaf in the stowed pose links to that same physical leaf's cutting entry.

Stowed has separate live X/Y position, bottom elevation and facing controls. Its initial
upright preview is in the aisle, at X=800/Y=450mm, with its bottom on the wooden floor. This is an adjustable
preview location; a permanent storage space and retaining hardware remain undecided. The mount offset applies
to both tabletop representations. The upright slides lengthwise with the folded wood in this preview; actual
channel engagement and clamps require checking on the kit. The stored arm automatically points towards the
offset tabletop, maximising its lengthwise overlap with the wood. It flips 180° when the offset changes sides;
a centred top uses the positive-offset direction. This updates live through a stepped rotation track on the
existing offset control. The independent stored-arm angle has been removed. Hardware can extend beyond the wood
if the tabletop is too short to cover it.

The cut list includes two timber leaves and one bench-mount spacer. The BOM has one Lagun kit and one pair
of Homer HOM006136 hinges. Visual hardware and the duplicate storage representation are excluded from cutting layouts.

### Stowed thickness

See [table-storage research and shortlist](table-storage.md) for 30 documented installations and their application
to this NV200. Gert selected the cross-bench overhang. Restrain the table with a padded cradle, a cab-end stop
and quick-release webbing attached to the fixed frame. The cabinet-end proposal obstructed sliding-door entry
and has been rejected. Cab clearance, bed-frame travel and the restraint geometry still need checking.

[Lagun USA's instructions](https://lagunusa.com/instructions/) explain that the upright stores in the tabletop
plate's dovetail channel and that the furniture bracket stays installed. Their
[installation-clearance diagram](https://lagunusa.com/product-details/) labels dimension H, underside of arm to
upper face of the standard tabletop plate, as approximately **3 inches (76.2mm)**, and identifies H plus tabletop
thickness as the storage clearance. With two 18mm leaves folded together, that gives **112.2mm**, approximately
**11.2cm**. The CAD uses the manufacturer's nominal 30mm fitting plus 47mm arm: **113mm including the timber**.
The upright lies alongside the arm, so its full length is not added to that thickness.

The [standalone standard TMP photograph](https://lagunusa.com/wp-content/uploads/2024/06/tmp.jpg) also labels
76.2mm from the tabletop face to the projecting pin tip. Separating the arm and upright therefore leaves about
112mm overall thickness for the folded top and its fixed fitting. The 30mm drawing dimension covers the extrusion
profile. The current simplified CAD assigns the tabletop pin to the arm group; it does not establish the physical
envelope of a top stored without its arm. The storage assessment retains the projecting pin.

This is a storage-depth estimate. The plate is drawn as its solid outer envelope; its undimensioned channel,
the upright cross-section and the reindexed handle shapes are illustrative. Actual handle projection, hinge
projection and channel engagement need measuring on the selected hardware before making a closely fitting slot.
The upright's published overall length including its tap is 21¾ inches (552.45mm); its aluminium body is nominally
500mm. The shared upright model now includes that overall tap length.

## Dimensions and sources

The [official general drawing, dated 9 March 2026](https://lagunofficial.com/wp-content/uploads/sites/2/2024/10/Lagun-General-Technical-drawing-with-meassurments.pdf)
gives a 500mm upright, 324mm between arm pivots, 38mm from a pivot to the arm end, a 47mm arm height, a 30mm
tabletop fitting and a standard 92 × 170mm furniture bracket. The current standard tabletop plate is
**240 × 200mm**, with **30mm overall profile depth**. The 240mm length follows from the symmetric 120mm pivot-to-end
dimension and agrees with Lagun USA's published 9 7/16 × 7 7/8 inch standard plate. The arm's 400mm length also
follows from 38 + 324 + 38mm, and the manufacturer lists the standard leg as 500mm. The leg width in front
elevation is 38mm. The mounting plate's 30mm profile depth is not its aluminium wall thickness.

The RV World image supplied in chat labels the top plate 300 × 200mm and the wall bracket 100 × 170mm. Another
supplied image labels them 240 × 200mm and 90 × 170mm. Those images conflict. The current manufacturer's drawing
supports 240 × 200mm and 92 × 170mm. No manufacturer change notice establishing the origin of the 300mm/100mm
labels was found. The exact version shipped by a retailer requires confirmation against that retailer's stock.

The tabletop mount now uses its documented 240 × 200 × 30mm overall envelope. The earlier guessed 4mm flange and
56 × 70mm centre block have been removed. The solid envelope does not reproduce its hollow/grooved section.
The overview does not fully dimension extrusion depth, arm width, clamp handles, bushings, dovetails or bolt
centres. Existing illustrative representations of those parts remain unverified and cannot establish clearance.
The overall hardware model must not be described as dimensionally exact.

[Lagun USA's product dimensions](https://lagunusa.com/product-details/) give an assembled bottom-of-leg to
tabletop-plate height of approximately 23 inches, or 584mm. Adding the 18mm fixed leaf makes 602mm; the model's
upright bottom is therefore the selected open tabletop height minus 602mm. The source explicitly describes its
installation-clearance measurements as approximate; the model's corresponding vertical joint placement is
approximate too. Another supplied promotional image rounds the under-arm-to-plate stack to 80mm.

[Lagun USA's installation instructions](https://lagunusa.com/instructions/) specify a minimum tabletop thickness
of 5/8 inch, approximately 15.9mm, for their screw-mounted arrangement. This is that supplier's installation
guidance. The current top uses two 18mm pine leaves, above that published minimum. For 18mm stock, their stated half-depth
engagement means at least 9mm into the timber; allow for the plate thickness when selecting screws.

The model helps compare reach, proportions and clearances. It does not establish the strength of either plywood
mount or prevent the table from being rotated into furniture, a person or the vehicle.
