# What we built in Onshape

This document records the NV200 campervan model to carry into build123d. It describes the implemented geometry,
the decisions behind it, its parameters and moving assemblies, and the work still outstanding. Read it alongside
[the target architecture](ARCHTECTURE.md), which describes the planned build123d, Codex and Python FastAPI system.

The priorities are **low weight, maximum usable storage, simple construction and affordable, available materials**.
Preserve those priorities during migration. The existing model contains substantial furniture detail, but still needs
measured vehicle dimensions, construction joints, hardware confirmation and a completed toilet installation.

## 1. Evidence and scope

This account was checked against the local source on **15 October 2026**:

- [nv200-interior.fs](fs/nv200-interior.fs): current FeatureScript, version 3095, with the geometry and parameter rules.
- [Design notes](ideas/nv200-bench-design.md): chronological decisions and historical verification reports.
- [Conversation transcript](onshape-chatgpt-transcript.md): design rationale, corrections and the latest toilet proposal.
- [Historical model metadata](ideas/nv200-onshape-model.json): useful background, with obsolete values mixed into it.
- [Original layout research](ideas/nv200-layout-research.md) and
  [self-containment exploration](ideas/nz-self-containment-exploration.md): research history.

Source SHA-256 at documentation time:

```text
27381538d8cc98236f059a7fe7e7b2a231bb95dcd612f62be644c215c10e9bc2
```

The Onshape document is
[NV200 interior](https://cad.onshape.com/documents/535730a6c26cda879ebea159/w/31ddbbf51dc8fc8f86781813/e/d73ad7d18ebfd2716526b356).
Its live saved feature inputs and displayed geometry were **not retrieved or regenerated for this document**.
Unless stated otherwise, numbers below are calculated from the local source defaults. A saved Onshape instance can
override those defaults.

Use the current source for implemented behavior and the latest user decisions for pending work. Earlier proposals,
`nv200-before-*` backups, generated test snapshots and JSON metadata must not silently replace the current model.
For example, the JSON contains older 528mm moving slats, 593mm fixed slats and a superseded cross-cushion arrangement.
Its top-level layout units are centimetres, while many nested construction values are millimetres.

### What exists today

| Area | Implemented extent |
|---|---|
| Vehicle | Simplified cargo boundary, rounded wheel-arch solids, rear-corner surfaces and door-opening outlines |
| Long bench | Plywood frames, interleaving slats, moving aisle frame, guide ledges, tie/stop strip and steel angles |
| Cross bench | Frames, toilet/storage partition, fixed deck, sliding slats, plate stops and opening storage lid |
| Rear storage drawer | Five plywood pieces, mounting frame, rear opening and simplified telescopic slide envelopes |
| Cabinet | Rectangular plywood carcass and wheel-arch frame |
| Cushions | Six separate foam blocks with daytime and nighttime placements |
| Controls | Daytime, visibility, drawer extension and storage-lid opening checkboxes |
| Toilet | Compartment based on an old assumed footprint; selected toilet and tray still to be designed |

There is no complete vehicle shell, detailed door mechanism, manufactured joint system, certified load analysis,
manufacture-ready cut list or completed self-containment installation in this model.

## 2. Design principles we settled on

### Furniture construction

The agreed baseline is **7mm plywood enclosure panels and 18mm plywood frames with 60mm-wide beams and posts**.
Internal opening corners use a **25mm radius**. Frames are cut from sheet material with the interior removed; the
model keeps each physical panel or frame as a separate part where practical.

The 7mm sheet selected during research was iBuilt untreated CD structural plywood, 2400 × 1200 × 7mm, from Bunnings NZ.
The 18mm frame material is parameterised by thickness; the model does not establish a final supplier or strength grade.
The rear drawer has a separate, deliberate **12mm birch plywood** construction.

We removed 7mm panels where they merely repeated the outline of an exposed 18mm access frame. We also removed the
wall-facing enclosure panels behind the long bench and cabinet. Keeping these skins would consume material and storage
width without serving the intended enclosure function. Retain skins where separation or enclosure is useful, notably
the cross-bench toilet/storage divider.

The user already owns a very strong slatted bed using approximately 80 × 18mm slats on a 45 × 45mm timber frame.
The new model reuses that slat size. Earlier discussions of much deeper plywood beams, multiple competing frame systems
and 470mm-high/doubled backrests were rejected. Do not restart those choices during a geometry port.

### Loads and practical limits

The occupants were assumed to be two people of about 85kg. During simplified edge-panel discussion, the user selected
**150kg distributed across 400mm** as the maximum design case. That is a recorded design assumption; the current source
does not calculate stress, deflection, joint strength or a rated capacity from it.

The bed should remain light and accessible. Hardware, joints and vehicle fixings still need checks appropriate to their
actual loads. Geometry regression tests cannot establish those capacities.

## 3. Coordinates, dimensions and dependencies

### Coordinate convention

The FeatureScript uses a right-handed coordinate system:

- **X:** across the van, from the long-bench wall toward the cabinet wall.
- **Y:** along the van, from the rear doors toward the cab.
- **Z:** upwards from the floor.

The nominal rear-left floor corner is `(0, 0, 0)`. The simplified cargo rectangle is X = 0–1500 and Y = 0–1860.
“Rear” means the vehicle's rear-door end. “Cab end” means the opposite end. The aisle is toward increasing X from the beds.

**All dimensions in this document are millimetres.** FeatureScript uses explicit unitful values, including some
centimetre expressions. Convert them once into the Python model's chosen millimetre convention.

The target architecture currently suggests X longitudinal and Y transverse. Resolve this difference explicitly before
porting placements. Preserving the current axes initially makes comparisons easier. If changing axes, define and test
one transform, including handedness, hinge directions and drawer motion; a bare X/Y swap changes handedness.

### Baseline parameters

| Parameter | Value | Meaning |
|---|---:|---|
| `cargoWidth`, `cargoLength` | 1500, 1860 | Provisional layout envelope |
| `bedWidth` | 1070 | Full nighttime width |
| `longBenchWidth`, `seatLength` | 600, 1280 | Fixed long-bench footprint |
| `platformHeight` | 400 | Top of the slats |
| `foamThickness` | 100 | Foam top is 500 above the floor |
| `wallThickness`, `frameThickness` | 7, 18 | Enclosure skin and structural frame |
| `memberWidth`, `insideRadius` | 60, 25 | Frame bands/posts and opening radii |
| `slatWidth`, `slatThickness`, `slatSideGap` | 80, 18, 5 | Slats lie flat; 5mm between adjacent slats |
| `crossDeckThickness` | 12 | Deck below the cross-bench slats |
| `cabinetOuterLength` | 1190 | Rectangular cabinet length |
| `cabBackrestLength` | 750 | One of the two end backrests |

**Cabinet-height discrepancy:** current source and UI defaults specify `cabinetHeight = 1300`. Earlier screenshots and
several test scenarios use 400. Retrieve the live instance value before choosing the migration's displayed baseline.
Keep this parameter independent of the 400mm bed height.

The main derived relationships are intentional:

```text
backrest / infill width = (bedWidth - longBenchWidth) / 2 = 235
cross-bench fixed width = bedWidth - infill width       = 835
cross-bench depth       = cargoLength - seatLength     = 580
rear end backrest length = seatLength - 750             = 530
cabinet depth           = cargoWidth - bedWidth        = 430
closed long-bed width   = longBenchWidth + 18           = 618
daytime aisle width     = bedWidth - closed width       = 452
```

The long bench occupies X = 0–600, Y = 0–1280. The cross bench occupies X = 0–835, Y = 1280–1860.
The cabinet occupies X = 1070–1500, Y = 0–1190. The 90mm gap between cabinet end and cross-bench start follows those lengths.

The 235mm cushion infill and the cross-bed's **217mm mechanical travel** are different quantities. The moving frame adds
18mm to the closed carcass width before extension. Preserve this distinction in parameter names and UI labels.

## 4. Fixed frames and vehicle accommodation

### Long bench and cabinet

The long-bench carcass reaches Z = 382, leaving 18mm for the slats. Its fixed aisle frame is at X = 582–600 and has two
access openings. Each is nominally 550mm wide and 222mm high, between the 60mm top band and the 100mm slide mounting band.
The centre post is 60mm wide. The moving aisle frame has open-bottom cutouts.

The cabinet uses the same construction mechanism, with a rectangular 430 × 1190 footprint. Its aisle frame has two
openings and its wall frame clears the other wheel arch. Cabinet top, shelves, doors, bottom and their hardware remain
undesignated.

The wall-side frames avoid the wheel arches. Their rear ends start 120mm forward of the rear datum to clear the rounded
body corners: 100mm corner radius plus 20mm allowance. The rear wall support consequently occupies Y = 120–180 at baseline.
The provisional arch starts at Y = 216, leaving **36mm** behind the arch. Although `archClearance` is 50mm, the rear-corner
constraint takes precedence here; do not document 50mm clearance everywhere.

The long bench has a post at Y = 1016–1076 ahead of the arch and an end post at Y = 1220–1280. On the shorter cabinet,
two adjacent 60mm supports are combined into a 120mm-wide support at Y = 1070–1190. The user's instruction was to move the
supports together and retain their combined width.

The long bench's original rear enclosure panel has been replaced by the drawer opening. Its header occupies
X = 168–582, Y = 0–18, Z = 322–382. An internal drawer-frame post supports its wall-side end.

### Vehicle references

| Reference | Current default geometry | Confidence |
|---|---|---|
| Wheel arches | Y = 216–966; 750 long, 280 high; 200 upper-corner radius | Provisional approximation |
| Arch intrusion | 140 from each side; 1220 clear between arches | Derived from 1500 cargo width and 1220 gap |
| Rear corners | 100mm-radius curved reference surfaces | Approximate body obstruction |
| Rear door opening | 1262 wide × 1228 high, centred at Y = 0 | Provisional opening outline |
| Side door openings | 693 along Y × 1171 high; Y = 1167–1860 | Provisional outlines on both sides |
| Floor boundary | 1500 × 1860 construction outline | Layout reference only |

The wheel arches were estimated from drawings/photos; one referenced drawing was for a different wheelbase variant.
The user challenged the visual proportions and requested rounded arches. Actual van measurements are still needed.
Treat the arch as part of the vehicle: adjust furniture around it, and change its position only when measurement warrants it.

There is no floor solid, full body lining, roof, accurate pillar model, door leaf, door sweep or weather-seal geometry.
Hiding a vehicle reference does not remove its dimensional influence on the furniture.

## 5. Long-bench sliding bed

### Slat arrangement and travel

Fifteen slats run across the van: eight fixed and seven moving, alternating along the 1280mm bench length.
Their pitch is 85mm, with 5mm end margins. The gap between successive fixed slats is 90mm, accommodating an 80mm moving
slat with 5mm clearance on each side.

The moving slats attach to an 18mm plywood aisle support frame. This frame sits immediately outside the fixed frame
when retracted. Both sets of slat tips align at X = 618 in daytime. The moving set travels **452mm** toward the aisle,
ending at X = 1070 at night.

| Part / relationship | Baseline |
|---|---:|
| Ordinary fixed slat length | 611; X = 7–618 |
| Moving slat length | 611; X = 7–618 closed, 459–1070 extended |
| Rearmost fixed slat length | 468; X = 150–618 |
| Fully extended slat overlap | 159 |
| Moving frame thickness | 18 |

The shorter rear fixed slat clears the rounded rear corner and begins over the internal drawer support. Earlier proposed
short returns and assumptions about the original rear panel were superseded by the drawer-support arrangement.

### Tie strip and ledges

A flat **40 × 18mm plywood strip** runs along the inner ends of the moving slats. Its bounds are:

- Closed: X = 90–130; extended: X = 542–582.
- Y = 122–1253; Z = 364–382.

It ties the moving slats together and forms the extension stop against the inside of the fixed aisle frame.
It remains within the bench cavity throughout travel. The slats extend past this strip, as explicitly requested.

Two fixed 25mm-wide guide ledges support the strip ends. Their top is Z = 364; their Y ranges are 120–145 and 1230–1255.
The strip has 2mm end clearance. The rear ledge is set forward because of the body corner.

Do not replace this with a continuous passage cut through the fixed support: that earlier proposal would remove the
support under the other slats. The present geometry keeps the strip between the frames and supported on ledges.

### Angle brackets and clearance cuts

Three steel reinforcing angles brace the moving frame-to-slat connections, addressing the long lever arms acting on an
18mm-wide glue/screw joint. The reference product is the
[Carinya 50 × 50 × 40 × 2mm reinforcing angle](https://www.bunnings.co.nz/carinya-50-x-50-x-40-x-2mm-galvanised-reinforcing-angle-bracket-8-pack_p3962402).
Their centres are at Y = 130, 640 and 1150.

The model includes simplified steel geometry plus provisional bend and screw-head allowances. Fixed-frame reliefs are
42mm wide, with a 6mm top notch and a 6mm-deep face pocket extending 51mm down. These permit sliding without requiring
complex guides. Hole patterns, screws and installed hardware dimensions still need confirmation.

## 6. Cross bench, storage lid and extension

### Fixed deck and moving slats

The cross bench encloses the toilet area beneath a **12mm deck**. Slats sit on the deck, and the moving slats slide over it.
The frame top is Z = 370, deck top Z = 382, and slat top Z = 400, matching the long bench.

The seven alternating slat positions comprise four fixed and three moving positions. Both fixed end slats are trimmed
to 75mm; the others are 80mm wide, with 5mm gaps. The wall-side portions of the four fixed slats belong to the storage lid.

The moving frame sits at the aisle edge. Closed slat tips align at X = 853; extended tips reach X = 1070 after **217mm**
travel. The moving slats are only **376mm long**: X = 477–853 closed and 694–1070 extended. This retains the long bench's
159mm overlap while freeing the wall-side top for storage access. Bearing over the actual deck at full extension is 141mm.

Three reinforcing angles use the shared bracket mechanism, with reliefs in the fixed frame and deck. The cross bench
uses the deck for support, so it has no longitudinal bench-style tie strip and end ledges.

### Recessed plate stops

Two recessed mending plates limit extension, replacing the earlier through-deck bolts-in-slots proposal. The reference is
the [Zenith 100 × 22mm mending plate](https://www.bunnings.co.nz/zenith-mending-plate-100x22mm-4pk-zp_p0821317).

Each plate attaches underneath a moving slat and projects sideways across the 5mm gap into a closed-ended underside
rebate in the adjacent fixed slat. Of its 100mm length, 50mm lies under the moving slat, 5mm crosses the gap and 45mm
engages the neighbour. Its 22mm width lies along the direction of travel.

The guide length is 239mm: 217mm travel plus 22mm plate width. Defaults assume 2mm plate thickness, a 4mm fixed rebate,
0.5mm running clearance and 1mm screw-head allowance. These hardware thickness/head assumptions need physical confirmation.
The closed rebate ends stop travel. This arrangement does not provide vertical capture against lifting the moving slats.

### Toilet/storage divider

The current divider is a **7mm separating panel plus an 18mm rectangular frame**, with the centre of the 18mm piece cut
away. It retains a bottom rail. Both pieces have top-corner recesses around the cross beams. This was the accepted
alternative to wasting almost a whole additional 18mm sheet behind the 7mm panel.

At baseline:

| Item | Geometry |
|---|---|
| Divider frame | X = 352–370; 566 along Y × 370 high |
| Separating skin | X = 370–377; same outer profile |
| Frame centre opening | 446 × 250, R25 |
| Top-corner recesses | 18 along Y × 60 deep |
| Wall-side storage clear plan | 327 across X × 530 along Y |
| Toilet bay | X = 377–817; 440 across X |
| Fixed aisle opening | 460 along Y × 310 high, with rounded upper corners |

These compartment dimensions still derive from the old assumed 420mm toilet depth plus 20mm allowance. The latest
forward-facing toilet choice has not yet been applied. Its changes will affect this partition and its openings.

### Storage lid

The wall-side 12mm lid is approximately **358 × 576mm**, X = 2–360 and Y = 1282–1858. A 2mm seam separates it from the fixed
deck, centred over the divider frame. Each leaf has 8mm nominal bearing there. The lid carries its four attached slat
sections and has a 25mm finger hole.

The `openStorageLid` checkbox raises this five-part group through 70 degrees. The hinge axis is parallel to X at the
**cab-side edge**, Y = 1858, Z = 400. In the present coordinate system, the applied rotation is **−70 degrees about +X**.
The rear/free edge rises.

The part names still say “removable lid”; the later opening preview added the hinge motion. Hinge hardware, retention,
opening support and the final removable-versus-hinged construction are unfinished. Foam is not included in the lid
clearance tests; cushions need separate handling and clearance consideration.

## 7. Rear pull-out storage drawer

The drawer runs lengthwise under the long bench and exits through the rear doors. Daytime access through the aisle-side
frame openings remains useful for contents. The extended bed obstructs that aisle access at night, which informed the
discussion of camping gear, containers and a wetsuit as likely contents.

### Tray and fixed support

The tray consists of five separate 12mm plywood pieces: two open-top U-shaped sides, two full-height ends and a bottom.
The bottom fits **inside the sides and ends, flush with their undersides**, with glued/screwed construction intended.
There is no raised groove consuming internal height. Fastener layout and joint capacity are unfinished.

| Dimension | Baseline |
|---|---:|
| Tray outside width × length × height | 376 × 1250 × 290 |
| Tray inside width × length × height | 352 × 1226 × 278 |
| Floor clearance | 10 |
| Tray bottom top | Z = 22 |
| Tray top | Z = 300 |
| Rear header underside | Z = 322; 22mm clearance above tray |
| Side lower bands / end uprights | 90 / 60 |

The closed tray bounds are X = 187–563, Y = 0–1250, Z = 10–300. Its **rear face is flush at Y = 0** with the bench rear.
The 10mm gap below the tray was repeatedly mistaken for a recess in perspective views; the user subsequently confirmed
that vertical floor clearance explained the appearance. Preserve both the flush rear plane and this floor clearance.

An 18mm fixed mounting frame sits immediately inside the wheel arch at X = 150–168, with 10mm clearance from the arch's
inner face. It reaches 300mm high and has a rear post raised to Z = 382 for the rear slat/header support. Its lower slide
mounting band is 100mm high. The opposing slide mounts on the long bench's fixed aisle frame.

The proposed 330 × 460 × 267mm plastic containers fit with 330 across the drawer and 460 along it. Two fit lengthwise.
The 267mm height leaves 33mm beneath the rear header when standing on the Z = 22 bottom. Containers are not modelled parts;
handle/lid protrusions and actual purchased dimensions still matter.

### Drawer slides

The model uses the earlier researched long-slide envelope:

- 1200mm closed rail length; 1215mm travel.
- 19mm mounting gap on each side; 53mm profile height.
- 50mm rear allowance for the release lever.
- Three simplified telescoping bodies per side, occupying the entire 19mm gap together.

`drawerLength` means the closed **rail** length. Tray length is `drawerLength + drawerRearSetback = 1250`.
`drawerExtended` translates the tray toward negative Y by 1215mm; 35mm remains under the bench at full extension.

Earlier research discussed a 61kg slide-pair capacity and a roughly 40kg working-load target. These are historical design
inputs, with no fresh product verification in this document. The six rail solids represent clearance and motion; they
omit actual races, mounting holes, release levers and fasteners. Confirm the exact product and its mounting conditions
before manufacture. Keep this storage-drawer hardware separate from the pending toilet-slide choice.

## 8. Cushion layout

The model has **six physical cushions**, all 100mm thick:

| Piece | Face dimensions | Purpose |
|---|---:|---|
| Long seat | 600 × 1280 | Seat and main longitudinal bed area |
| Cross seat | 835 × 580 | Cross-bench seat and front bed area |
| Long wall backrest | 235 × 1280 | Outer/wall-side bed infill |
| Rear end backrest | 235 × 530 | Part of the longitudinal aisle infill |
| Cab-facing backrest | 235 × 750 | Remaining longitudinal aisle infill |
| Short wall backrest | 235 × 580 | Cross-bench bed infill |

Daytime seats occupy their bench footprints at Z = 400–500. Backrests stand above them at Z = 500–735.
The two wall backrests are 100mm deep along X. End backrests are 100mm deep along Y. The rear end backrest reaches
X = 630, a 30mm seat overhang; the cab-facing one reaches X = 850, 15mm beyond the cross-seat width.

At night all six pieces lie at Z = 400–500:

| Region | X range | Y range | Piece |
|---|---|---|---|
| Long bed, wall side | 0–235 | 0–1280 | Long wall backrest |
| Long bed, middle | 235–835 | 0–1280 | Long seat |
| Long bed, aisle/rear | 835–1070 | 0–530 | Rear end backrest |
| Long bed, aisle/cab end | 835–1070 | 530–1280 | Cab-facing backrest |
| Cross bed, wall side | 0–235 | 1280–1860 | Short wall backrest |
| Cross bed, remaining width | 235–1070 | 1280–1860 | Cross seat |

This tiles a 1070 × 1860 rectangle. The latest cross-cushion swap deliberately puts the large cushion toward the aisle
to bridge the small front-side area with less slat support. Cushion coverage alone does not prove support beneath it.

The user cancelled proposed shortening/repositioning of the long orange backrest to clear the rear corner. The current
1280mm piece remains full length. Rear-corner foam fit and foam retention remain physical-layout questions; do not apply
those cancelled changes during migration.

## 9. Controls and assembly states

| Current control | Behavior to preserve |
|---|---|
| `daytime` | Checked: seats/backrests upright and both beds retracted. Unchecked: cushions flat and both beds extended. |
| `showCushions` | Shows/hides all six cushions independently of bed position. |
| `showSlats` | Shows/hides both benches' slats, cross deck/lid and mending-plate stops. |
| `drawerExtended` | Extends the rear storage drawer independently of daytime. |
| `openStorageLid` | Opens the lid and its four slat sections to 70 degrees, independently of daytime. |
| `showWheelArches` | Displays provisional arch solids. |
| `showRearCorners` | Displays the curved corner references. |
| `showDoors` | Displays opening outlines; left/right side outlines have separate controls. |

Hiding slats leaves the moving support frames, reinforcing angles, long-bench strip and ledges visible. Fixed-frame
bracket cuts remain identical in both visibility states. This is useful for inspecting the underlying mechanism.

FeatureScript represents these as regenerated endpoint configurations, with no assembly mates or interactive physical
simulation. The application may later expose continuous motion, but its endpoint placements and motion envelopes must
remain consistent with these assemblies. Visibility and geometry regeneration should be deliberately separated in the
new system while preserving the existing visible groups and cutouts.

## 10. How the FeatureScript constructs the model

One custom feature, `nv200Interior`, owns the model. Its `precondition` defines the grouped settings dialog, `DEFAULTS`
supplies runtime defaults, and the feature body generates the parts. There should be one intended feature instance in
the Part Studio; a duplicate `NV200Interior 1` was an earlier editing mistake.

The source is procedural CAD using cuboids, sketches, extrusions, boolean subtraction/union and transforms. Opening
profiles create the plywood frames. `nameAndColor` assigns readable part names and display colours. Colours help
inspection; they are not a material specification or structural calculation.

| Source functions | Responsibility to carry over |
|---|---|
| `layoutDimensions` | Shared layout dependencies and input validity |
| `makeBlock`, `openingTool`, `benchWall` | Reusable panel and rounded-opening construction |
| `benchCarcass`, `wheelArchFrame` | Fixed furniture, skins, end frames and arch/corner accommodation |
| `longSlatDimensions`, `crossSlatDimensions` | Slat count, spacing, travel and overlap |
| `slidingSlatAssembly` | Common fixed/moving slats and moving support frame; long-bed strip/ledges |
| `slidingBracketDimensions`, `slidingBenchBrackets` | Angles and their motion-clearance cuts |
| `crossStorageDimensions`, `crossBenchPartition` | Compartment split, divider frame/skin and lid bearing |
| `crossBenchSlats`, `crossBenchStops` | Cross deck, lid group/rotation and recessed stop mechanism |
| `drawerDimensions`, `slideMountFrame`, `drawerRearFrame`, `rearDrawer` | Tray, mounting structure and rail envelopes |
| `rearFaceY`, `verifyRearAlignment` | Checks of actual generated rear faces |
| `wheelArchReference`, `rearCornerReference`, `doorOutline` | Provisional vehicle references |

Generation order matters where cutters and dependent parts interact. The feature builds carcasses, long slats/brackets,
partition, cross deck/slats/lid, cross bracket reliefs and stops, then drawer, cushions, cabinet and vehicle references.
When slats are hidden, it still creates the cross deck temporarily to complete bracket cuts, then deletes the deck.

Operation IDs identify generated bodies for later cutting, transforming and checking. The port needs stable semantic
component identities and assembly membership; it does not need to reproduce FeatureScript's concatenated IDs literally.
Retain separate physical plywood pieces and hardware instances rather than fusing all furniture into one solid.

`setVariable` publishes many derived `nv200_*` values for downstream Onshape expressions. These are calculated outputs.
Some names are historical: `nv200_crossExtension` is the 235mm infill width, while `nv200_crossSlideTravel` is the actual
217mm travel. Give the new API unambiguous names and preserve a mapping where useful.

The runtime guards check viable openings, strip/ledge placement, wheel-arch clearance, drawer fit and cushion dimensions.
Port these constraints with the geometry, including their parameter dependencies. They should produce useful validation
errors rather than silently resize parts to make an invalid configuration appear workable.

## 11. Verification evidence and lessons

### Existing checks

The project contains generated `nv200-*-validation.fs` evaluators and JavaScript generators. The generators adapt the
production source into transient Onshape evaluation functions. **Generating an evaluator file does not execute CAD tests.**
Historical pass reports in the design notes describe the following coverage:

- Drawer geometry, rear-plane alignment, contact, multiple extension positions, invalid inputs and deliberately displaced
  header/post mutations.
- Slat counts, gaps, end alignment, travel, overlap and cushion coverage in day/night configurations.
- Bracket steel, bend and screw-head clearance envelopes across translation; mutations removing necessary reliefs.
- Cross-compartment separation, divider volume, empty centre and retained bottom rail; lid support and visibility.
- Plate-stop end contact, full travel and rejection of overtravel.
- Lid opening in 10-degree samples through 70 degrees, plus endpoint placement and hidden-state checks.
- ASCII checking of FeatureScript annotations after a non-ASCII description broke the settings dialog.

Relevant sources include [drawer checks](fs/nv200-drawer-checks.fs),
[general validator generator](ideas/validate-nv200.mjs),
[bracket generator](ideas/validate-nv200-brackets.mjs),
[cross-bed generator](ideas/validate-nv200-cross-slats.mjs) and
[lid generator](ideas/validate-nv200-lid-open.mjs).

There is a current tooling relocation issue: `docs/ideas/validate-nv200.mjs` resolves its production source and drawer
checks beside itself, although those files now live in `docs/fs/`. The other three generators still use root-relative
working-directory paths and also need updating for this location. Existing generated evaluators also embed source snapshots. Account for this before attempting
fresh Onshape validation; no validator was regenerated or executed as part of writing this document.

### Failures the migration should prevent

1. **Wrong units and saved defaults.** A 60mm saved bench width was mistaken for the intended 600mm. The source now uses
   the distinct `longBenchWidth` field with explicit millimetre defaults. Test parameter loading as well as geometry.
2. **Formula-only alignment checks.** Shared calculated values did not prove generated faces were flush. Current
   `verifyRearAlignment` measures actual planar faces, including the drawer's extension offset, at a 0.001mm tolerance.
3. **Bounding boxes missing a failed cut.** A divider could have correct outer bounds while retaining an unwanted solid
   centre. Check occupied volume and probe the intended hole as well as the outer dimensions.
4. **Sketch orientation.** Reversing a sketch normal changed its vertical direction and cut the wrong region. Explicitly
   test plane bases and transformed openings in build123d.
5. **Geometry passes with broken UI.** An invalid annotation prevented the Onshape settings dialog from opening despite
   successful geometry evaluation. The new parameter API and UI need their own validation.
6. **Source publication versus displayed state.** Source readback did not prove that the visible Part Studio used the right
   instance or saved values. Verify the displayed model/configuration after regeneration.

Translation sweeps and sampled rotation tests have different coverage. Current lid checks exclude cushions. Hardware
envelopes simplify real parts. No existing test proves furniture strength, real-vehicle fit or certification eligibility.

## 12. Latest unfinished work: toilet and sliding tray

The user's requirement is a **Green Sticker self-contained installation**. The toilet is being installed primarily for
that purpose and is expected to be used rarely. Certification remains a separate acceptance requirement for the completed
installation; the current model establishes no compliance result. Recheck the current official requirements and proposed
installation with an authorised certification provider during detailed design.

The selected baseline is the
[SCNZ 10L toilet with fixing bracket](https://selfcontained.co.nz/products/10l-portable-toilet-with-bracket),
recorded during research as **365 wide × 415 deep × 300 high**. The user chose it and confirmed that it should **face
forwards toward the cab**. In the model's axes, its body width would be 365 along X and depth 415 along Y; the tray would
slide sideways toward increasing X.

This choice is ahead of the geometry. Current FeatureScript still assumes 370 along Y and 420 along X to size the bay;
it has no toilet solid, tray, slide installation or occupied-use envelope.

The latest proposal, recorded in the transcript, was:

| Item | Proposed value / status |
|---|---|
| Clearance above closed toilet | 20mm extra |
| Tray bottom / floor gap | Tentative 12mm / 5mm |
| Required opening height | 300 + 20 + 12 + 5 = 337; proposed 340 |
| Extension | Approximately 650mm to clear the extended cross bed |
| Heavy slide candidate | UES DSCHHD650MML; recorded 650 closed/travel, 75.4 high, 19.5 side gap |
| Historical published capacity / mass | 227kg per pair / 6.24kg per pair |
| Indicative loaded estimate | About 115kg: 85kg occupant, up to 20kg liquid, 10kg toilet/tray/bracket allowance |

The [UES slide candidate](https://www.ues-hardware.co.nz/drawer-slides/drawer-slides/heavy-duty-lockable/drawer-slides-heavy-duty-650mm-locking-227kg-pair-dschhd650mml)
and these specifications come from prior research, without a new price, stock or rating check here. It has not been
selected for purchase or incorporated into the model. Research also found a rating discrepancy in the lighter slide
range at 650mm length; do not carry over the shorter rail's capacity to a longer rail.

The proposal exposes real space and weight costs:

- 650mm rails would extend about 210mm into the storage compartment, requiring divider passages and supporting structure.
- A conventional tray with 12mm sides and these slides was estimated to need about 490mm along-Y opening width, exceeding
  the current 460mm opening.
- The current fixed opening is only 310mm high, so the proposed 340mm requires frame changes while retaining the 400mm bed.
- Prior placement reasoning estimated only about 27mm body clearance from the extended bed and 38mm from the nominal side
  boundary. These are preliminary estimates requiring a full geometry check, including the human-use space.

The next design task is to fit the toilet, fixation, tray and rail supports through both fixed and moving cross-bench
frames, verify use with the bed extended, and retain useful storage. Confirm lid/valve access, waste-tank removal,
locking/retention, mounting strength and applicable certification requirements. The forward orientation is settled;
the detailed tray and slide solution remains open.

## 13. Other work still to come

| Work | Why it remains necessary |
|---|---|
| Measure the actual van | Confirm floor envelope, lining, arches, corners, door openings and occupied clearances |
| Resolve cabinet height | Source default and earlier displayed/test configurations differ |
| Finish cabinet internals | Top, shelves, doors, bottom, access and hardware are absent |
| Detail furniture joints | Glue areas, screws/bolts, grain direction, tolerances and assembly sequence are incomplete |
| Detail vehicle anchoring | The model does not show an approved load path into the vehicle |
| Confirm real hardware | Angle bend/head sizes, mending plates, slide holes/locks and hinge geometry are simplified |
| Finish bed retention | Extension stops exist; retracted retention and resistance to lifting need construction details |
| Finish lid hardware | Hinge axis is previewed; hinge, catch, support and cushion handling are unresolved |
| Check support and usability | Short rear slat, front cross-bed edge, corners, foam restraint and nighttime access |
| Produce fabrication outputs | Materials, masses, hardware schedule, cut drawings/nesting and assembly instructions |

## 14. Carrying the model into build123d

The architecture document owns the target runtime and API design. This document supplies the model-specific migration
contract. Its example dimensions must not replace the values above without an explicit design change.

A practical transfer sequence is:

1. **Capture the Onshape baseline.** Retrieve saved feature parameters and feature identity; save day/night and useful
   hidden/open screenshots and, where available, STEP exports. No STEP exports were found in the inspected project files.
2. **Establish units, axes and parameters.** Map inputs and derived outputs, resolving the cabinet-height discrepancy and
   historical parameter names. Keep provisional vehicle measurements editable and clearly identified.
3. **Port reusable construction.** Build panels, rounded frame openings and component naming, then the fixed carcasses and
   reference geometry. Preserve separate pieces and material thicknesses.
4. **Port moving assemblies.** Long slats/frame/strip/brackets, rear drawer/slides, cross slats/deck/stops/lid and cushions.
   Attach each part to the correct moving group and compare endpoint coordinates before adding UI behavior.
5. **Port meaningful verification.** Check generated geometry, contacts, intended holes, height stacks, translation sweeps
   and sampled lid opening. Include the known unit, alignment and missed-cut regressions.
6. **Connect the interactive application.** Preserve independent visibility and configuration controls. Follow the target
   architecture's regeneration/error handling so a failed edit leaves the last successful model available.
7. **Resume design work.** Add the forward-facing toilet installation after achieving a recognisable, checked baseline.

The minimum parity checks are: 400mm slat-top height on both benches; correct six-cushion tiling; 452/217mm bed travel;
159mm slat overlap; bracket and plate-stop clearance; flush drawer rear at Y = 0 with 10mm floor clearance; a genuinely
open divider frame; and the five-part lid rotating together about its cab-side edge. Check day/night, drawer extended,
lid open and hidden-slat states, including combinations.

Native build123d geometry should become the editable model. Reference exports and screenshots help compare the result.
Preserve the reasons and constraints above while replacing the FeatureScript implementation, and keep new design
decisions distinguishable from migration fixes.
