# Table storage in this NV200

Research and current-design assessment, 27 October 2026. Basis: working tree based on `87d8abb`, live parameters,
existing exported model geometry, and the sources below. This document proposes storage; it changes no CAD geometry.

[Plan and storage-position drawing](table-storage-layout.svg)

## Recommendation

**Use the cross-bench overhang for storage. Gert rejected the cabinet-end rack because it obstructs the route
from the sliding door into the aisle.** The earlier assessment checked bed clearance but failed to assess that
entry route. Cabinet-end storage does not meet the requirement to keep the table out of the way.

Keep the folded table on its long edge beneath the overhang, where Gert has positioned the preview. Secure it
to the fixed cross-bench frame with a padded bottom cradle, a cab-end stop, and a quick-release webbing restraint
that captures the table's rear end and holds its folded leaves together. Retain the inside rearward retrieval route.
The moving-frame clearance and cab-end projection described below still need resolving before fixing the cradle.

### Restraining the package

- Rest a shallow padded wooden cradle on the floor and bolt its brackets to the cross-bench frame's solid end
  posts. Locate its bottom supports beneath the folded 50mm wooden edge; leave room beside them for the Lagun
  hardware. Low side lips prevent the bottom moving sideways. Size the clearance from the actual folded wood
  and padding, rather than making a nominal 50mm slot.
- Fit a padded stop at the cab end of the cradle to prevent forward sliding.
- Anchor a 25mm cam-buckle webbing restraint to the fixed frame. Route it around the rear end of the folded wood
  so tightening pulls the package forward against the stop and sideways against padded frame contact points.
  Capture both leaves, and keep the strap off the Lagun clamp handles. A strap bearing only on the large side
  face would rely on friction to resist longitudinal movement; the proposed route captures the rear edge.
- Keep the buckle at the aisle/rear end. Releasing it should let the table pull rearward into the aisle without
  moving the chilly bin. The cradle carries the weight; the restraint limits tipping, lifting and rearward movement.

The end-post anchors, strap path and stops require dimensioning in CAD around the actual assembly. This proposal
establishes how to restrain each direction of movement; it is not a completed fixing or crash-load design.

## Requirements and assumptions

Gert's requirements:

- The stowed table must leave useful daytime living space, including the route from either sliding door into the aisle.
- One person must be able to stow it and extend/make the bed from inside, with the vehicle doors shut.
- Restraints must limit movement while driving.
- Storage should consume little useful space.

I have kept the existing 700 × 500mm open tabletop, its two 25mm bamboo leaves and the standard Lagun hardware.
The assessment includes the upright and arm. It also considers the chilly bin, chairs, solar bag, cabinet access
and the moving bed frame. The task is to choose a storage arrangement; fixing sizes and anchor details follow the
actual hardware measurements and a physical mock-up.

## Package dimensions: an important correction

| Item | Size used here | Evidence and limit |
|---|---|---|
| Open bamboo tabletop | 700 × 500 × 25mm | Current live model |
| Folded bamboo leaves | 700 × 250 × 50mm | Current live model |
| Standard Lagun mounting-plate extrusion | 240 × 200mm footprint, 30mm profile depth | [Manufacturer drawing](https://lagunofficial.com/wp-content/uploads/sites/2/2024/10/Lagun-General-Technical-drawing-with-meassurments.pdf) |
| Standard plate including projecting pivot pin | Approximately 76mm below the wood | [Lagun USA's standalone TMP photograph](https://lagunusa.com/wp-content/uploads/2024/06/tmp.jpg) labels this 3 inches; measurements are approximate |
| Folded top with its fixed plate and pin | Approximately 126–127mm thick overall | 50mm bamboo plus approximately 76mm hardware |
| Upright | 500mm body; approximately 552mm including its pin | [Lagun USA dimensions](https://lagunusa.com/product-details/) |
| Arm | Nominally 400mm overall | Manufacturer drawing |

**Removing the arm and upright does not give an 80mm-thick folded top.** The tabletop's pivot pin remains attached
to the mounting plate. The 30mm dimension describes the extrusion profile. It excludes the pin that enters the arm.
Routine storage should retain that pin. I have found no manufacturer instruction for removing it each time.

At the current mount offset, −53.7%, the modeled packed arm and upright fit within the 700 × 250mm wood outline.
At a centred mounting position the arm can project slightly beyond a 700mm top. A rack needs clearance for the
actual knobs, hinge fittings, padding and hand grip; 127mm is a nominal package depth, not a finished slot size.
The model's hardware details remain illustrative. In particular, its simplified pivot belongs geometrically to
the arm group even though the physical tabletop pin stays with the plate when the arm is detached.

[Lagun's storage procedure](https://lagunusa.com/faqs/) detaches the table from the furniture bracket, separates
the upright from the arm, and slides the upright into the tabletop plate's storage channel. Handles must secure
the components. This supports the packed arrangement already shown in the model.

## What the current van gives us

Coordinates below use the displayed van: X across the floor, Y forward from the rear opening, Z above the wooden
floor. These are reference coordinates for the proposals, not an instruction to measure a real van to this precision.

| Feature | Current position or clearance | Consequence |
|---|---|---|
| Cabinet cab-facing panel | Y=1088–1100mm; face extends to X=407mm | Existing solid 12mm plywood panel for a cradle |
| Cabinet panel at Z=720mm | X≈51–407mm in the exported surface mesh | A 250mm-wide top at X=120–370mm fits on the face |
| Left edge of extended bed | X=430mm | Keep the cabinet-end rack and straps below X=430mm |
| Cabinet end to cross-bench rear | Y=1100 to 1380mm | 280mm of length between these furniture ends |
| Cross bench | Y=1380–1960mm | 580mm long; table is 700mm long |
| Cross-bench aisle-side frame | X=630–648mm | Slats overhang into X=430–630mm |
| Cross-bench slat underside | Z=372mm | A 250mm-high upright package fits below the slats |
| Moving long-bed frame | Y=190–1285mm throughout sideways travel | A stored table extending rearward into this span can obstruct bed extension |
| Wooden floor front | Y=1960mm | Any rack extending farther forward bridges onto the lower cab-floor area |
| Cross-bench inner bay | Approximately 684 × 571mm below the top | A 700mm table requires diagonal placement or another orientation |
| Current chilly-bin body | Approx. X=136–416mm, Y=1504–1974mm, height 410mm | Obstructs sideways extraction from beneath the overhang |
| Long-bench drawer top | Z=300mm | Only 72mm remains to the slat underside; the packed top cannot sit flat above it |

I read the furniture dimensions in `cad/bench.py`, `cad/cross_bench.py`, `cad/sliding_bed.py`, `cad/drawer.py`,
`cad/cabinet.py` and `cad/cabinet_doors.py`, and inspected the saved exported surfaces for the fixed panels.
The cab source describes its seats as estimated reference geometry. The gear sources give measured outer sizes
with approximate details. The live mannequin sits on the long bench at Y≈928mm; another sitting position can
change the foot-space assessment.

## Shortlist applied to this van

### Rejected: padded cradle on the cabinet's cab-facing end

Gert rejected this location because it obstructs sliding-door entry into the aisle. The dimensional analysis below
records the earlier candidate; bed clearance alone did not establish usability.

**Proposed wood position:** X=120–370mm, Z=20–720mm. Put its flat folded face against pads on the panel, with
the Lagun components facing forward. Allocate roughly 145mm from the cabinet face for the complete package,
padding and restraint, ending near Y=1245mm. Final dimensions depend on measured fittings.

| Requirement | Assessment |
|---|---|
| Daytime space | Main aisle and cupboard doors stay clear. The package occupies a 250 × roughly 145mm floor projection beside the cabinet end. It reaches about 35mm into the rearward end of the modeled left sliding-door opening, reducing that opening's usable length there. |
| Closed-door conversion | Release the strap, lift the top roughly 15–20mm from its bottom supports, then move it towards the aisle. The top remains below about 740mm during release. Neither a vehicle door nor a seat cushion needs opening for the rack itself. |
| Bed movement | Proposed rack edge X≤380–400mm, bed starts at X=430mm. There is room for restraint hardware without entering the bed's footprint. |
| Driving | Bottom shoes carry the mass; side stops and a tightened strap restrain movement. Through-fix the anchors to the panel with accessible backing plates or broad washers. The complete anchor arrangement still needs detailing. |
| Lost storage | No cupboard compartment or drawer volume. The cost is the external projection and the small reduction at the back edge of the left door opening. |
| Simplicity | Two padded bottom shoes, locating pads and one accessible retaining strap. No telescopic mechanism or special-order storage cassette. |

Use shoes sized for the folded 50mm wooden edge. Many commercial tabletop clips target thinner single panels;
their compatibility with a 50mm stack must be checked before purchase. Keep the retaining strap's buckle near the
aisle-facing edge. The strap must also hold the folding leaf shut. A padded loop can provide a carry grip without
loading a hinge.

**Inside transition to bed:** fold the tabletop while it is supported; detach and pack the Lagun parts using the
bench as a temporary support surface; stand the package in the cradle and secure the strap; then extend the bed
and arrange the cushions. The temporary package needs 700 × 250mm of bench surface during packing. This sequence
preserves the aisle until the table has reached its rack.

The reference dimensions leave room for a vertical release and a sideways move towards the aisle. I have not
demonstrated the full handling sweep with an animated CAD sequence or a person handling a physical
weighted mock-up. The physical handling trial remains part of choosing the final rack.

**Closest precedents:** Bilbo's stores its table on the kitchen-pod end; GB Camper Conversions uses the front of
its Berlingo cabinet; Outside Van's Parks manual specifies brackets on the forward galley face and removal towards
the van centre. Ovano documents bottom supports with upper retaining clips. These establish the storage method.
Our dimensions come from this van.

### Selected location: lengthwise rack beneath the cross-bench overhang

Stand the 700 × 250mm package on its long edge, parallel to the van. Keep the hardware beneath the top as in the
current stowed representation. Allow roughly 150mm of the 200mm overhang for a padded rack and its retainers.

**Provisional package envelope:** X≈480–607mm, Y≈1305–2005mm, Z≈10–260mm. A surrounding rack will extend beyond
that envelope. Its rear retainer must also clear the moving frame's Y=1285mm end.

The cross bench's rear skin begins at X=630mm, so it does not close this overhang from the rear. A table can slide
forward into the space from the aisle before the bed extends. It needs no cut through the cross-bench skin.

The current storage preview places the wood at approximately Y=1257–1957mm. **That position overlaps the moving
frame's Y span by roughly 28mm.** Moving the package forward by about 49mm gives roughly 20mm clearance behind
its rear edge, at the cost of 45mm projection beyond the wooden floor. Padding and stops require more room.

| Requirement | Assessment |
|---|---|
| Daytime space | Hidden below the cross bench. It occupies most of the overhang's toe space; assess sitting nearer that edge as well as the present mannequin position. |
| Closed-door conversion | Slide it forward from the main aisle before extending the bed. Pull it rearward into the aisle for retrieval. The closed rear doors do not lie on this route. |
| Bed movement | A forward position clears the moving frame. The present preview position does not provide that clearance. |
| Driving | A bottom cradle, upper guide, forward stop and releasable rear retainer can locate it. The retainer must prevent both rearward sliding and tipping. |
| Lost storage | Uses the overhang rather than the cross-bench inner bay. Preserves its central storage and the rear drawer. |
| Main unresolved point | The front projection enters estimated cab geometry. Measure the actual seat/rail/trim clearance at the package's full height, plus the rack and hands. |

**Retrieval constraint:** the chilly bin finishes around X=416mm and sits alongside much of this rack. There is
insufficient space to move the whole package sideways clear of the bench and then lift it over the bin. A design
that assumes sideways removal would require moving the bin. The intended rearward route avoids that step.

Mount a rack to the fixed cross-bench frame. Its forward end would bridge beyond the wooden floor onto the cab
floor's 18mm lower level. Detail a supported end stop rather than assuming the floor stays level. Keep the release
at the rear end where you can reach it from the aisle.

This is the selected storage location. Resolve the cab gap, moving-frame clearance and rearward retrieval route
with the cradle and restraints included before fixing their positions.

### 3. Diagonal storage inside the cross-bench bay

The inner bay has about 684mm across the van, 571mm fore/aft and 372mm below the slats. Standing the packed table
on its long edge and turning it about 28° gives a bare plan envelope of roughly **678 × 441mm**, height 250mm.
That is a possible resting position.

The aisle-frame opening is about 451mm long below its upper band. The bare 441mm projection leaves about 10mm
total for passing through it. Padding, fittings and a useful grip consume that allowance. Rotation after partial
insertion may offer another route, but I have not established one. A rack would also obstruct a large part of the
central storage bay. I would not choose this over the first two positions.

### Other locations eliminated or deferred

| Location | Reason in this design |
|---|---|
| On top of the drawer, below the slats | Gross clearance is 72mm; retained tabletop fittings need about 127mm overall. |
| Inside the rear drawer | A 700mm top can consume drawer space, but the drawer's normal opening requires the rear doors open. It fails the night-conversion requirement. |
| Front cabinet compartment | The lower shelf interrupts the required 700mm vertical slot. Lying the table flat also exceeds its available plan dimensions. Creating a slot would change the shelves. |
| Rear cabinet's lower compartment | This is the existing chair bay. Storing the top there requires reallocating the chairs or their access route. |
| Against the cabinet's aisle face below the mattress | A 127mm projection enters the extended bed's space. |
| Against rear hatch/doors | Solar bag and rear furniture already occupy the useful region. Inside access would need resolving around them. |
| Behind the front seats | Commercial microcampers use this, but our cab-seat clearances are estimates and the cross bench reaches forward. No measured 127mm pocket is established. |
| On a front seat at night | Reachable inside, but needs relocation for driving and uses the cab as a temporary storage pile. A fixed rack gives one location for both modes. |
| Under a seat cushion | 50mm bamboo plus fixed fittings changes the support height or needs a recess through existing slats. |
| Ceiling or overhead cab shelf | Adds roughly 127mm below a low roof, requires lifting the bamboo overhead, and needs a new rack and anchors. No clear advantage over available low locations. |
| Leave the upright mounted and swing the arm aside | The bench-mounted upright still passes through the extended mattress area. It must come off for bed use. |
| Replace bed slats with the tabletop | The existing comb-bed slats already form the surface. A new infill role would redesign that system. |
| Change the tabletop's fold direction | Two 350 × 500mm leaves would change the storage shape, but the 552mm leg and mounting-plate direction need repacking, and the mount's usable offset/reach changes. Consider only if the existing-top locations prove unsatisfactory. |

## Thirty documented examples

These are 30 separate installations, grouped by their storage arrangements. Several use the same method.
Their descriptions establish where the owner or builder stores a table. They do not prove that our thicker
folded bamboo/Lagun package fits there. “Unknown” identifies a detail the source does not establish.

| # | Actual installation and source | Storage and evidence limits |
|---|---|---|
| 1 | [TekyInBlack self-built motorhome](https://www.tekyinblack.com/motorhome/changes-since-we-finished/lagun-table/) | Owner built a slotted box at the front of the van; the Lagun leg stores beneath the tabletop. Box opening and travel latch unknown. |
| 2 | [Ovano Switch](https://ovano.co.uk/pages/table-storage-bracket-set-installation) | Manufacturer fits two lower brackets and two opening upper clips to its back panel. Table thickness differs from ours. |
| 3 | [Terry Fleming's Adventurer 80RB](https://www.truckcampermagazine.com/camper-mods/contests/small-table-lagun-mod/) | Owner stores top/mount beside the couch in a custom bracket. He reduced the top and changed the arm; standard-package fit is unproven. |
| 4 | [CAB's Leisuredrive Vivante, post 5](https://www.t6forum.com/threads/leisuredrive-vivante-review-and-photos.19116/) | Owner relocated the table from an awkward seatback position into brackets between toilet cupboard and rear door. He reports retrieval with doors closed. |
| 5 | [ICS Loc8 door-table installation](https://www.icampersolutions.co.uk/wp-content/uploads/2018/10/ICS_InstructionFlyer_web.pdf) | Manufacturer retains its folded table in four door-card slots. It specifies fitting with the door closed and checking engagement before sliding the door. Different vehicle and product thickness. |
| 6 | [Pleasure-Way Ford Pursuit manual, p.41](https://static.nhtsa.gov/odi/tsbs/2017/MC-10117787-9999.pdf) | Tabletop behind driver seat against front closet, held by a thumb latch; pole in closet C-clips. Shows separate storage with positive retainers. |
| 7 | [Bilbo's Space](https://www.bilbos.com/bilbos-campervans/space/) | Manufacturer stores the removable table on the kitchen-pod end. Retaining hardware and removal clearance unspecified. |
| 8 | [CrabTab's T@B 320, owner discussion](https://tab-rv.vanillacommunity.com/discussion/comment/162108) | Leg inside passenger bench; top/arm on wheel fender in the same bench. Lid access and dedicated restraint remain unconfirmed. |
| 9 | [Slackers' T@B 320 CS-S, same discussion](https://tab-rv.vanillacommunity.com/discussion/comment/162108) | Table becomes front locker lid; plywood and doorstop locating pieces support it. Upright storage and driving restraint unknown. |
| 10 | [Backroad Buddies' VanDOit](https://www.redtaillodge.com/blog/campervan-lessons-learned-from-season-two-2020) | Owner sewed a protective Velcro-closing cover for the folded top; leaves hardware mounted and swings it aside. At night the mounted top can sit over a bench. Covered-top parking location unspecified. |
| 11 | [Northwood Arctic Fox storage sofa](https://www.truckcampermagazine.com/news/2026-arctic-fox-and-wolf-creek-updates/) | Manufacturer interview describes storing two Lagun tables and legs inside the sofa. Much larger furniture; retaining rack unspecified. |
| 12 | [rachelemily's Mk6 Transit build](https://fordtransit.org/forum/viewtopic.php?f=58&start=15&t=59300) | Owner stores the tabletop on the cupboard side behind driver and leg on bed kickboard. Older external photographs may be unavailable. |
| 13 | [Les Sage's Lance 855S, project 4](https://www.truckcampermagazine.com/camper-mods/projects/8-lagun-table-system-projects/) | Large top stores upright against exterior wall beneath a smaller mounted drinks table. Restraint unspecified. |
| 14 | [Doug Henschen's Albin Ballad sailboat](https://www.practical-sailor.com/sailboat-reviews/sailboats-21-30ft/albin-ballad-used-boat-review/) | Owner stores a removable lightweight top and original leg at the back of a hanging locker. Access around stored clothes and retaining clips unknown. |
| 15 | [Jack's Leisure Travel Vans Unity TB](https://www.ltvforum.com/index.php?topic=595.0) | Owner parks folding/swivelling tops behind cab seats on their mounts, and removes one under a bed when carrying passengers. Larger vehicle and tight swing clearance. |
| 16 | [Reimo Caddy Camp, earlier model road review](https://www.caravanclub.co.uk/blog/product-and-outfit-reviews/campervan-reviews/reimo-caddy-camp-review/) | Reviewer describes a 700 × 440mm top and clip-in leg strapped beneath a seat cushion. Stored thickness unspecified. |
| 17 | [Reimo Caddy Camp 2 / Weekender 2](https://www.reimo.com/us/campervan-conversions/vw-caddy-conversion-br-vw-caddy-camper-conversion/vw-caddy-weekender-2-caddy-5-maxi-lr/65790/table-system-camp/camp2-and-weekender-2-for-caddy-maxi-and-ford-connect) | Manufacturer stores the top on a single-seat backrest, where it supports the bed. Leg storage and fastener details unspecified. |
| 18 | [Wilderness West Coast Mini brochure, pp.6–7](https://www.wildernessvans.com/wp-content/uploads/2022/09/WV-Compact-Conversions-2023.pdf) | Transit Connect builder labels a table-storage slot beside the galley, plus removable top and folding leg. I downloaded/read the PDF; latch details need its hardware specification. |
| 19 | [VW Caddy California](https://www.volkswagen-vans.co.uk/en/new-vehicles/caddy-california.html/__layer/layers/content_slider/caddy_california/camping_and_equipmen/living-and-sleeping/master.layer), [VW training document SSP719](https://esperformance.net/ssp/vwn/SSP_719_EN.pdf) | Table/chairs occupy separate sections in a bag strapped beneath rear bed frame. Training text describes belts, zips and Velcro. Inside retrieval from the rear-facing location is doubtful; repeat PDF access became restricted. |
| 20 | [Claire's Mazda Bongo, Betsy](https://theladybirdsadventures.co.uk/mazda-bongo-campervan/) | Owner slides dining and camping tables into the gap between reversed middle bench and front seats, alongside bedding. No positive restraint described. |
| 21 | [GB Camper Conversions Berlingo](https://gbcamperconversions.com/campervans-for-sale/2007-citroen-berlingo-multispace-micro-camper/) | Builder stores removable table at front of main storage unit. Inside and outside working mounts; storage-retainer detail unknown. |
| 22 | [Calder Hiace, actual vehicle listing](https://www.motorhomedepot.com/vehicle/20240815050329) | Listing describes table storage in a side compartment. Opening and restraint unspecified. |
| 23 | [Frontline Hiace Adventurer](https://wanderer.cmca.au/reviews/frontline-hiace-hi-top-camper) | Road reviewer identifies tabletop and pole behind driver seat. A larger van; retainers unspecified. |
| 24 | [ANNEX Canelé NV200, 2026 brochure](https://www.annex-rv.co.jp/catalog/pdf/CaneleSeries_brochure_202601.pdf) | Manufacturer relocates the table to a rear position as a bedside drinks/phone shelf. This establishes a secondary parking role; driving restraint remains unknown. |
| 25 | [Outside Van Parks, manual section 5-8](https://outsidevan.com/wp-content/uploads/2025/09/OutsideVan-Parks-Owners-Manual.pdf) | Manufacturer stores the Lagun table in brackets on the forward galley face. It slides towards the van centre for removal. The manual requires this storage state for driving. PDF downloaded and read. |
| 26 | [Amdro Boot Jump design history](https://www.amdro.co.uk/where-did-that-name-boot-jump-come-from/) | Builder uses the removable table as bed-platform infill. Indexed manufacturer text establishes the method; direct page access returned 403. |
| 27 | [Vangear Caddy-Pod 2.0](https://vangear-eu.com/products/new-caddy-pod-sliding-campervan-kitchen?variant=51701433991507) | Sink/stove lids become side tables, then return as covers. Would require a different tabletop role here. |
| 28 | [Camperlove Supercompact](https://www.camperlove.eu/en/product/supercompact/) | Manufacturer describes two table leaves sliding beneath the main storage drawer; NV200 listed compatible. Repeat access timed out. Rear access does not establish closed-door retrieval. |
| 29 | [Campal Slimline](https://campal.co.uk/campal-slimline/) | Maker's compact-car examples use a pull-out table within the boot bed box. Rear extraction conflicts with closed-door conversion here. |
| 30 | [Mishima Daihatsu Quokka](https://www.mishimadaihatsu.com/camper/quokka/) | Builder removes table leg and places top into the seating/bed arrangement as infill. Leg-storage restraint unspecified. |

Additional useful primary evidence: [Outside Van Parks manual](https://outsidevan.com/wp-content/uploads/2025/09/OutsideVan-Parks-Owners-Manual.pdf),
section 5-8, specifies galley-face storage brackets, inward removal and storage before driving. I downloaded and
read this PDF after web extraction timed out. [Tiffin's GT1 manual](https://knowledge.tiffinmotorhomes.com/Owner_Hub/Tiffin_Motorhome_Units/GT_Series/GT_1_Series_Owner's_Manuals/2026_GT_1_Series_Manual/04_2026_GT_1_Series_Cabinets_and_Furniture)
also identifies a dedicated Lagun top/leg compartment behind the driver.

I excluded FarOutRide as an implemented-storage example: its Lagun article leaves the eventual storage location
undecided. I found no adequately verified primary ceiling/pulley installation suitable for this assessment.

## Practical hardware and remaining work

The overhang cradle can use timber/plywood offcuts for its padded supports and stops, ordinary through-fixings and a
25mm cam-buckle strap. These do not require special-order hardware. For NZ availability, Burnsco lists
[25mm cam-buckle tie-down pairs](https://www.burnsco.co.nz/tiedown-set-316ss-4m-webbing) at $69.99 and in stock
online when checked; a selected Wellington store's stock was not established. This is a sourcing example, not a
selected purchase. Check strap length, buckle position and fixing capacity before buying. A supplier's strap
rating does not establish the strength of its anchors in 12mm plywood.

Before making a permanent rack:

1. Measure the actual folded assembly, including reindexed handles, hinges and the retained tabletop pin.
2. Check moving-frame clearance and the cab gap above the floor step in the overhang position. Include the cradle,
   stops and padding beyond the nominal 700 × 250 × 127mm package.
3. Verify inside rearward retrieval with the chilly bin in place and a representative package weight.
4. Size the cradle, restraint and anchors from those measurements. Show the retained state and removal path in CAD
   before cutting permanent pieces.

I inspected source, current parameters, the saved surface geometry and the existing browser view. I did not
change the displayed model, drive the UI, run tests, build the project, start services or simulate a person
carrying the table. The comparison establishes candidates and dimensional conflicts; the physical handling trial
remains the acceptance check.
