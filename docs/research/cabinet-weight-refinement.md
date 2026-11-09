# Weight refinement of the new timber cabinet

7 November 2026. Refines [the construction proposal](cabinet-redesign.md), not the old live CAD model.
The original illustration remains the all-40mm baseline. No CAD, saved project or purchasing selections changed.

**Sourcing correction:** 30 × 18mm rectangular untreated timber has not been verified as a purchasable NZ stock
product. The recommendation below was premature. The 30mm-section calculations remain a hypothetical machining
study, not a sourced design or an achieved weight saving. Making this section from larger stock would require
explicit allowance for ripping, equipment, waste and cost; that fabrication route has not been assessed here.
The approximately 15kg combined target must not be used as the expected weight of a currently sourced cabinet.
Searches found an Australian Bunnings rectangular product and NZ decorative profiles, neither of which establishes
suitable NZ stock. A category search snippet suggested a NZ primed dressed product, but no matching product page,
SKU, price or local availability was verified; it is not accepted as a material selection.

## Recommendation

Keep the bonded-skin construction, complete back, 6mm doors/shelves and two-module arrangement. Develop a
mixed-section frame: retain 40 × 18mm long shelf rails and interface members, with 30 × 18mm braced stiles and
shorter rails where their joints and attachments fit. Keep full-width pads at vehicle fixings and interface bores.
Investigate a lighter 3mm skin product without assuming all products sold as caravan ply weigh the same.

The screening target is approximately **15kg wood** with the currently documented white lightweight skin, or
approximately **14.7kg** if a suitably priced raw 3mm skin at 450kg/m³ can be sourced. These compare with the
16.76kg all-40mm/birch allowance, not with a measured finished cabinet. Hardware and finishes remain additional.
The target does not establish a saving against the old approximately 13kg plywood cabinet.

## 1. Give the members different jobs

| Member | Lightweight proposal | Reason |
|---|---|---|
| Long front/rear shelf rails, up to about 520mm clear span | Keep 40mm vertical × 18mm thick | Rail bending stiffness depends strongly on vertical depth |
| Module bearing/bolting rails | Keep 40 × 18mm, solid at bores | Preserve washer landings, bearing surfaces and bore geometry |
| Stiles braced by the assembled frames/skins | Assess 30mm face × 18mm thick | Reduce face width while retaining thickness for hardware and joinery |
| Non-interface transverse rails, clear span no more than 350mm | Assess 30mm vertical × 18mm thick | Much shorter span permits a shallower member; calculate the rebated section |
| Vehicle fixing locations and joint corners needing more room | Local full-width timber | Do not shrink fixing or mortise landings indiscriminately |
| Doors and shelves | Keep 6mm | Further thinning gives a small saving while reopening the attachment and sag design |
| Fixed skins/back | Keep 3mm and continuous bonded bracing | Avoid losing the bracing mechanism merely to reduce panel area |

These are role-based dimensions, not a claim that 30 × 18mm is a universal cabinetry standard. Canadian
Woodworking's base cabinet example uses approximately 25mm-wide stiles with approximately 38mm-high rails:
[Building base cabinets, part 3](https://canadianwoodworking.com/techniques_and_tips/building-base-cabinets-part-3/).
That establishes that the rail/stile widths need not match. Its thick sheet carcass does not rate our thin-skinned case.

Reducing the stile face to 30mm does not reduce an 18mm-deep face screw's available embedment. It does reduce
the room around holes and joints. The old paired-dowel geometry must not be copied into it without checking.
For narrow frame joints, use a proportioned mortise-and-tenon detail as the starting alternative: an approximately
6mm-thick tenon in 18mm stock follows the conventional one-third proportion. Joint length, height, shoulders,
intersection with skin grooves and distance from hinge screws remain specific to the corner. Where a shallow
receiving face or intersecting joints cannot accommodate it, retain the 40mm member instead of thinning its walls.
This increases machining effort compared with the initial dowelled-frame proposal.

References: [Fine Woodworking, Mortise and tenon](https://www.finewoodworking.com/project-guides/joinery/mortise-and-tenon),
[WOOD, Tune up a tenon](https://www.woodmagazine.com/tune-up-a-tenon-11834098).

## 2. Short-rail calculation

Use the baseline's assumed E=8000MPa, 12.5kg loaded shelf and 3g sensitivity case. Assign half that shelf load
to one simply supported transverse rail, F=184N, at a conservative 350mm clear span. Include a 9 × 6mm timber
shelf rebate. Do not carry a bolt hole through the critical reduced section.

| Section, thickness × vertical depth | Net I | Static sag | 3g sag | 3g bending stress |
|---|---:|---:|---:|---:|
| 18 × 40mm | 78,967mm⁴ | 0.054mm | 0.163mm | 2.18MPa |
| 18 × 30mm | 31,698mm⁴ | 0.135mm | 0.405mm | 4.15MPa |

The proposed change increases short-rail movement by approximately 0.08mm at static gravity in this model.
That is a reasonable candidate to develop; the calculated stress is demand, not an allowable capacity of the
appearance-grade pine. If the whole 3g shelf load went onto that rail, both results would double. Longer spans,
point loads, joint rotation and holes require their own assessment. Keeping long rails at 40mm avoids imposing
this approximately 2.5-fold deflection increase on the more demanding spans.

## 3. Skin sourcing and real product weights

The baseline used an assumed 650kg/m³ for its 3mm birch, giving 1.95kg/m² and 4.095kg over 2.1m² of installed
skin. That birch density was an assumption, not a measured value for the $55 sheet. Confirm the baseline sheet's
weight before treating a supplier-to-supplier difference as an achieved saving.

### Raw poplar: useful target, not a confirmed purchase

[Plymasters' older Euro Poplar sheet](https://plymasters.co.nz/assets/Uploads/Plymasters-Spec-Sheet-Euro-Poplar-2024.pdf)
lists 3mm E1003 at 3.8kg for 2500 × 1220mm. That would put 2.1m² at 2.62kg, saving 1.48kg versus the assumed
birch. However, the [2026 sheet](https://plymasters.co.nz/assets/Uploads/Plymasters-Spec-Sheet-Euro-Poplar-2026.pdf)
omits 3mm, and the current product page does not confirm its price or stock. Do not count this as an available
$55 replacement. A target density of 450kg/m³ would save 1.26kg, conditional on finding the appropriate product.

### Currently documented white panel

[Plymasters Caravan Ply](https://plymasters.co.nz/categories/products/transport-construction/caravan-ply),
E1003-P50, is currently listed as 3mm and in stock at $89.37 excluding GST/freight: $102.78 including GST.
Its [2026 specification](https://plymasters.co.nz/assets/Uploads/Plymasters-Caravan-Ply-Spec-Sheet-2026.pdf)
lists 4.5kg for 2440 × 1220mm. Installed skin weight would be approximately 3.175kg, a 0.92kg saving versus
the baseline allowance. The extra sheet cost is approximately $47.78 before freight.

It has a white finished face. A timber bond needs an appropriate unfinished bonding surface and adhesive;
do not assume ordinary furniture PVA bonds to the finished face. It is sold for cabinet backing and vehicle
interiors, but its sheet weight supplies no cabinet racking capacity or allowable glue stress. Its documentation
also excludes structural use in building walls/ceilings. The cabinet application still needs its own joint/bracing
assessment, just as the baseline non-rated birch does.

A [Three Brothers supplier listing](https://www.trademe.co.nz/a/marketplace/building-renovation/building-supplies/panels-boards/plywood/listing/6123558695)
advertises plain 3mm pine-face/poplar-core caravan plywood at $39.90. It publishes no weight and its stated
freight minimum is $500 plus packing. It is a price/sourcing lead, not evidence of weight saving or a practical
single-sheet delivered purchase for this project. Do not substitute a generic poplar density for its actual weight.

## 4. Weight arithmetic, including offsets

Use the baseline's member allocations and 500kg/m³ pine density. The allocations are not an extracted cut list.

| Change | Calculation | Estimated saving |
|---|---|---:|
| Stiles 40 → 30mm face, 18mm thickness retained | 7.62m × 0.010 × 0.018 × 500 | 0.686kg gross |
| Longer front rails between narrower stiles | Additional 0.18m × 0.040 × 0.018 × 500 | **−0.065kg** |
| Full-width pads and joint-detail allowance | Added timber allowance | **−0.100kg** |
| Short transverse rails, excluding 1.32m of interface stock | 3.38m × 0.010 × 0.018 × 500 | 0.304kg gross |
| **Net timber target** | Before final cut-profile and joint-volume corrections | **0.825kg** |
| Current white lightweight skin | Product sheet weight applied to 2.1m² | **0.920kg** |
| **Combined current-product screening target** | 16.762 − 0.825 − 0.920 | **15.02kg wood** |
| Raw 450kg/m³ skin, if sourced instead | 16.762 − 0.825 − 1.260 | **14.68kg wood** |

The longer-rail correction is important: narrower posts do not save their full removed weight when adjoining
members must become longer. Existing rebates remove less wood from smaller sections as well, and actual corner
details may retain additional full-width stock. These figures warrant a roughly 15kg target, not a claim of an
exact 15.02kg manufactured cabinet. Allowance uncertainty alone is greater than tens of grams.

## What stays unchanged in this refinement

Keep the full bracing back, module bolts/bearing members, 6mm shelves/doors, chair loading route and ceiling/floor
attachments. Do not pocket the 6mm doors, drill large lightening holes in bracing panels, or remove rails because
the cabinet is attached to the van. Those would need a different load-path design. Carbon panels and specialised
honeycomb are not justified by this project's budget.

## Status

Recommend developing the mixed-section frame and sourcing the lighter skin. The timber calculation and price/
weight comparison are complete screening work; the narrower joints, product bracing properties, precise member
layout, final weight and purchase optimisation are not verified. No product has been ordered or substituted in
the live BOM. The structural and hinge details of the baseline proposal otherwise remain under review.
