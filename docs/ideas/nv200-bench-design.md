# Bench and cabinet construction — current design

## Rear drawer update — 15 October 2026

This section supersedes earlier long-bench dimensions below. Fixed bench and seat width are now 600 mm.
The new `longBenchWidth` input replaces `seatWidth` and the faulty `benchWidth` field so existing instances
receive the approved width. Its first UI unit is millimetres, with an explicit default of 600 mm;
subsequent edits use the new control. Other saved dimensions and visibility inputs are preserved.
Backrest/infill widths derive as (1070 − 600)/2 = 235 mm. Existing cushion segmentation is retained.
Closed bed width including the moving 18 mm frame is 618 mm; bed extension is 452 mm.

The rear 7 mm panel is removed. A 414 mm-long, 60 mm-deep, 18 mm-thick rear header runs X168–582,
Y0–18, Z322–382. Its rear face shares the Y0 plane with the drawer panel and both supporting posts.
It meets the existing aisle post and the new internal slide-frame rear post.
That internal frame is 18 mm thick at X150–168, 10 mm inside the provisional wheel arch. Its main
height is 300 mm; its first 60 mm at the rear rises to 382 mm as one plywood part. The rearmost slat
starts at X150 and bears on that post and header. No transverse jamb obstructs the telescoping slides.

Drawer baseline: 376 × 1250 × 290 mm outside, 352 × 1226 × 278 mm inside; five separate 12 mm plywood
pieces. Bottom is inset between all four walls with a flush underside. Glue/epoxy and screws are intended;
edge screw sizes, spacing and joint load verification are unresolved. Long sides have a continuous 90 mm
lower band and 60 mm end uprights, with R25 internal corners and full-height end panels.
Both fixed slide mounting faces have continuous 100 mm lower bands. Aisle access openings are 550 × 222 mm
before corner rounding. The moving bed frame retains its original open-bottom profile.

Tray is 10 mm above floor; floor top is Z22. Closed Y range is 0–1250, flush with the rear bench datum,
leaving 5 mm to the cab-end frame. Tray length derives from slide length plus slide rear setback.
Existing saved inputs are retained: `drawerLength` now labels Slide closed length, and
`drawerRearSetback` labels Slide rear setback. Runner positions and cab-facing drawer end are unchanged.
Two 330 × 460 × 267 mm containers fit lengthwise with 22 mm combined width clearance and 33 mm below
the rear header. Contents remain accessible through the aisle openings in day mode; whole-container
removal is through the rear. Crate envelopes are dimensional checks and are not added as model parts.

`Extend rear drawer` is independent of day/night and cushion visibility. Slide envelopes use the researched
1200 mm closed length, 1215 mm travel, 53 mm height and 19 mm side gap. Three simplified telescoping
zones illustrate travel; raceways, release levers and mounting holes remain undetailed. The 50 mm rear
setback reserves space for the approximately 45 mm release lever. Actual vehicle clearance remains unmeasured.
At maximum slide travel, the cab-facing 35 mm of the tray remains within the bench footprint.

The 40 kg working-load assumption and published 61 kg slide rating carry forward from research.
This geometry does not establish joint, slide-fastener or vehicle-anchor load capacity.
Sources: [Instant Panel slides](https://instantpanel.co.nz/product/drawer-slides-1200mm-x-53mm-with-lock-heavy-duty-runners.html),
[installation instructions](https://instantpanel.co.nz/productfiles/drawer_slides/Drawer_slides_2053_Installation_Precautions_and_Instructions.pdf),
[FarOutRide tray construction](https://faroutride.com/slide-out-trays/),
[WEST System bonding](https://www.westsystem.com/instruction/epoxy-basics/bonding-and-clamping/).

Validation: run `node validate-nv200.mjs` to build `nv200-drawer-validation.fs` from the current production
source and `nv200-drawer-checks.fs`, then execute it with the Onshape evaluator. Nine geometry scenarios,
five drawer travel positions, four bed travel positions and eight invalid-input rejection cases pass.
Checks compare actual rear faces with each other and verify both crossbeam/support contacts.
Five deliberate displacements must fail; restoring each part must pass again. Separate generated
`old-header` and `raised-post` mutation probes detect the original 7 mm offset and a shifted upper post
even when the lower frame stays at Y0. The generator also checks explicit 600 mm UI and runtime defaults.
Includes migration from
570 mm legacy width plus the faulty saved 60 mm field, edited dimensions, actual cushion bounds and
tray/slide/bed interference checks. The 60 mm failure was reproduced before fixing the input identity and defaults.
Production code is adapted to a transient Onshape evaluation lambda for those tests. Independent review
completed. The feature now also checks the actual rear faces at each regeneration using that instance's
inputs, including the support faces at crossbeam height. The drawer comparison compensates for extension.
Saved Part Studio rendering, stored input values and the source reference of the visible feature instance
are not verified by transient evaluator tests or source readback. A stale/older feature reference remains
possible if the displayed geometry differs; this must be inspected in the actual Part Studio.

## Earlier design record

The agreed construction is 7 mm outer plywood and 18 mm inner plywood frames, with 60 mm top bands and posts throughout. No solid-timber header or 7+7 mm reinforcement is used.

## First modelled pass

- Fixed long bench: 570 × 1280 mm baseline.
- Fixed cross bench: 870 × 580 mm baseline (bed width minus 200 mm extension).
- Platform/slat-top height: 400 mm; 18 mm reserved for slats gives 382 mm panels.
- Two long aisle access openings: 550 × 322 mm with 25 mm inside radii.
- One cross-bench aisle opening: 460 mm wide × 322 mm maximum height, open to the floor through the retained frame, with R25 upper corners. Toilet dimensions and deployment remain to be checked.
- Closed faces retain a solid 7 mm skin and 18 mm inner frame. Aisle access faces are 18 mm frames only; their cut-out 7 mm skins have been removed. All frame cutouts reach the floor.
- Opposite long walls run full length; end panels fit between their actual frame/skin build-ups. Corners meet without overlapping solids. Butt interfaces are geometry, not specified joinery.
- Each bench is a separate carcass; adjacent bench walls currently remain separate pending the connection/detailing pass.

All dimensions regenerate from named feature inputs. Platform height replaces the old foam-top height control; foam top is platform height plus foam thickness. Existing footprint and cabinet inputs are not overwritten.

## Wall-side wheel-arch clearance

The long bench's wall-facing 7 mm skin is removed. Its 18 mm inner frame remains in the existing X=7–25 mm
plane, preserving the end-panel interfaces. The top band remains 60 mm deep.

Provisional drawing inputs, all editable in the Wheel arches feature group:
rear floor edge to arch 216 mm; arch length 750 mm; arch height 280 mm; clear width between arches 1220 mm;
post clearance 50 mm. These are drawing-based placeholders to be measured on the actual van.
Cargo length stays 1860 mm; the other drawing's 81½-inch floor length is not adopted.

At those inputs, the rear-left bench corner is left open. Both adjacent frames stop 120 mm from the
theoretical square corner, derived from 100 mm body radius plus 20 mm allowance.
The rear-end skin is shortened too; its inner frame is rebuilt with a full 60 mm end post.
The wall-side rear post occupies Y=120–180 mm, leaving 36 mm before the unchanged arch at Y=216.
The post after the arch stays at Y=1016–1076, with the front end post at Y=1220–1280.

The preferred arch clearance stays at 50 mm. Rear post end is the greater of arch offset minus preferred
clearance and corner setback plus member width. Thus actual rear clearance is derived; the vehicle arch
never moves to make room for furniture. Incompatible inputs fail rather than move or resize the arch.
The wall-side opening over the arch is now 836 mm long at baseline.
Radius stays exactly at the requested value; incompatible openings and arch/corner interference produce errors.

Toggleable concave rear-corner reference surfaces use the user-estimated 100 mm radius.
Their vertical extent follows the rear opening reference height; actual pillar contours remain unmeasured.
The cabinet now uses the mirrored frame arrangement and rear-corner setback described below.
No diagonal cover or slats have been added.

Optional wheel-arch references use the 1220 mm gap centred in the simplified 1500 mm cargo width,
giving 140 mm intrusion per side. Upper ends are rounded with an editable 200 mm default radius.
This is an approximate side profile, extruded across the intrusion, not a measured wheel-house contour.
Base footprint, maximum height and support positions remain unchanged.
The cabinet wall-side frame clears the right reference; its wheel arch occupies some of the internal storage volume.

## Rectangular cabinet carcass

Nominal footprint is 430 × 1190 mm, using cargo width minus bed width and the existing saved cabinetOuterLength.
Both lengthwise edges now end at Y=1190. The legacy cabinetInnerLength value no longer affects geometry and its
control is removed. Derived inner and outer gaps to the cross bench's Y start are both 90 mm at baseline.

Cabinet height retains the cabinetHeight input and its saved value (400 mm in the user's last screenshot;
1300 mm remains the source default). It denotes the top of the walls/frames, with no top thickness added yet.
Six separate plywood parts reuse the same carcass and wall helpers as the benches:
two solid 7 mm end skins and four 18 mm frames. Neither the aisle face nor the wall face has a 7 mm skin.
The shared 60 mm member width and R25 openings apply. The aisle has two 505 mm-wide openings,
each cabinet height minus 60 mm tall (340 mm at a 400 mm cabinet), open to the floor.

The right wall-side frame sits at X=1475–1493, matching the bench's 7 mm wall-side gap after the skin is omitted.
Its rear post is Y=120–180, leaving 36 mm before the unchanged arch. The post after the arch is combined
next to the front end post, giving a combined Y=1070–1190 support; the previous narrow slot between two uprights is removed. The rear skin/frame stop at X=1380 to leave the 120 mm rear-right corner setback.
There is no top, bottom, shelf, hatch leaf or door hardware yet.

Verification: five scenarios passed in nv200-cabinet-carcass-validation.fs: source-default height1300,
saved-style height400, nighttime with cushions, changed material/member/radius/length inputs, and an obsolete
saved inner-length value that must be ignored. Checked seven cabinet solids, total part counts, mirrored bounds,
aisle/frame volumes, corner setbacks, derived clearances and preserved bench bounds/variables.
A cabinet too short to accommodate the fixed arch and posts was rejected. Independent review completed;
cabinet failures now identify the cabinet inputs. Saved source readback exactly matched tested source.
Saved Part Studio was not visually inspected.

## Remaining design

Door-opening references are toggleable construction-line outlines, with independent left/right side controls.
Nissan UK published opening sizes are rear 1262 × 1228 mm and side 693 × 1171 mm:
https://www.nissan-cdn.net/content/dam/Nissan/gb/brochures/Vehicles/Nissan_NV200_VAN_UK.pdf
Rear position defaults to centred at Y=0; side front edges default to the simplified cargo end (Y=1860).
Both sill offsets default to Z=0. These positions are explicitly provisional and editable, not measured.
No door leaves, swing/slide paths or curved apertures are represented.
Five focused Onshape evaluation scenarios verified exact bounds, visibility, edited dimensions/offsets,
cargo-length dependence and missing-input defaults without adding solids. Saved source readback matched.
The saved Part Studio has not been visually inspected.

Sliding/interlocking 80 × 18 mm slats, moving frames and support/stop details; hatch doors, clearance and hardware; material grain/cut layouts; joints and anchoring. Old cushions remain explicitly labelled layout references while their arrangement is updated with the sliding structure. Cabinet top, shelves, doors, joints and actual vehicle contours remain undetailed.

## Verification

Seven Onshape geometry scenarios passed: baseline day, night with cushions, raised platform, altered construction
dimensions, missing new inputs, hidden arch references, and changed arch offset/length. Checked body counts,
analytic cutout volumes, bounds, removed wall skin and derived support positions.
Five invalid cases were rejected: overlapping walls, arch too long, arch too high, rounded-corner interference,
and an opening too narrow for the specified radius. Independent source review found two parameter issues;
both were fixed and covered by these checks.

Source saved without reported compilation errors and exact readback confirmed. Tests used production geometry
adapted to an evaluation lambda; the saved Part Studio and its stored parameter values were not visually inspected.

Rounded references: seven scenarios passed again, including exact volumes for both arches, unchanged bounds,
edited radius and missing-input default migration. An incompatible rounding radius was correctly rejected.
Rounded source saved and exact readback confirmed.

Rear-corner update: five geometry scenarios passed (default, edited radius/allowance, hidden references/night,
raised platform/changed allowance, and missing-input migration). Verified shortened frame bounds and volumes,
rebuilt rear-end posts, reference surface areas, unchanged wheel-arch bounds and derived rear clearance.
A setback that would reach the fixed arch was rejected. Source saved and exact readback confirmed.
Validation is geometric; saved Part Studio not visually inspected.

## Removal of redundant access skins

Removed the three cut-out 7 mm aisle skins: long bench, cross bench/toilet side, and cabinet.
The 18 mm frames retain their original positions and geometry. Solid end skins and the closed cross-bench
wall-side skin remain. No bottom strips remain in the access openings.
There are now 19 plywood parts (7 skins and 12 frames), plus the optional references and cushions.
The derived nv200_hatchHeight now reports panel height minus member width (322 mm at baseline).
Earlier validation sections record historical stages; the current focused harness is nv200-skin-removal-validation.fs.
Three Onshape scenarios passed: day at cabinet height400, night with cushions at1300, and changed plywood/member/radius
dimensions. Checked the three missing skins, exact retained frame volumes/positions, all solid end skins,
closed cross-bench skin and updated opening height. No evaluator notices. Saved source readback matched.
Saved Part Studio not visually inspected.

## Recovered aisle-side panel thickness — current geometry

Following removal of the three 7 mm access skins, their retained 18 mm frames move outward to the nominal
aisle boundary. Long bench frame X=552–570, cross bench frame X=852–870, cabinet aisle frame X=1070–1088 mm.
Each unit gains 7 mm of internal width compared with the skin-removal stage, and the main aisle returns
from 514 mm to 500 mm. The nominal furniture dimensions and all vehicle references remain unchanged.
Both end walls in each unit extend to meet the moved frame. Their posts and cutouts regenerate from
the actual left/right frame-and-skin build-ups. No skin is recreated.
This supersedes the earlier notes that the access frames remain in their original planes.

Three focused Onshape scenarios passed: daytime, nighttime with cushions, and altered material/member/radius
dimensions. Checked exact aisle-frame positions and unchanged volumes, both end-wall layers' bounds and volumes,
absent skins, part counts, restored aisle and unchanged rear arch clearance.
Source saved and read back exactly; saved Part Studio not visually inspected.
Current harness: nv200-width-recovery-validation.fs.

## Combined cabinet front support

The cabinet's two 60 mm uprights are adjacent with no gap. The moved upright spans Y=1070–1130 and
the existing end upright spans Y=1130–1190, forming one continuous 120 mm-wide support in the 18 mm frame.
Combined width is twice memberWidth, with its end fixed to cabinet length.
The arch remains Y=216–966; front clearance is 104 mm at baseline.
This corrects the previous implementation which incorrectly overlapped the uprights into only 60 mm.
Long-bench supports are unchanged.

Three Onshape scenarios passed (baseline, edited length/member width, shorter valid cabinet).
Exact frame volume and twice-memberWidth support verified; unchanged arch bounds, long bench post and part count.
An invalid cabinet length was rejected. Source saved and exact readback verified.
Saved Part Studio not visually inspected. Harness: nv200-merged-post-validation.fs.

## Longitudinal sliding platform — 2026-10-14

The fixed bench stays 570 mm wide. An 18 mm moving aisle frame sits outside it, so the closed width is588 mm
and the day aisle482 mm. Nighttime translates the moving slats, frame and inner strip482 mm, reaching1070 mm.
The existing Layout control drives this movement alongside the cushion references; Show cushions remains independent.
Cross-bench top/extension is still undetailed.

Baseline separate parts:
- Eight fixed and seven moving timber slats,80 x18 mm, alternating with5 mm side gaps. Fixed-to-fixed clear gap90 mm.
- One moving18 mm plywood frame, copying the fixed aisle frame's two openings,60 mm bands/posts and R25 corners.
- One40 x18 mm horizontal inner tie/stop strip. ClosedX30–70; extendedX512–552; Z364–382.
- Two fixed18 mm plywood ledges,25 mm wide, topZ364. RearY120–145; cab-endY1230–1255; X25–552.

The rear ledge is a transverse rail inset to the120 mm corner setback, joining the retained wall post and aisle frame.
It is not attached to the original rear end panel; that panel stops short of the corner.
The strip runsY122–1253, with2 mm end clearance and23 mm bearing on each ledge.
Moving slats runX30–588 when closed,512–1070 when extended (558 mm long).
The first fixed slat is shortened toX120–570 (450 mm); the other fixed slats runX7–570 (563 mm).
Slats remain atZ382–400. Their bearing on the fixed aisle frame is retained during extension.
The strip stops against that frame atfull extension; a separate latch to prevent retraction is not modelled.
Nominal frame contacts are zero-gap; fastener details, running finish and floor attachment remain unresolved.

New editable controls: slat width, clearance each side, flat strip width, guide ledge width and strip end clearance.
Existing slat thickness, frame thickness, platform height, fixed width, bed width and length drive the geometry.
Slat count is the largest fitting odd count and end margins are equal. Unsupported shortened rear slats are rejected,
with a prompt to adjust slat spacing/width/length; dimensions are never silently changed.
Rear corner/arch references and fixed carcasses are unchanged. Existing cushion shapes remain layout references.

Verification: nv200-slats-validation.fs evaluates the production code through Onshape's transient evaluator.
Six geometry scenarios passed: day, night, raised platform/slat thickness, altered widths/length/spacing/strip/ledges,
missing-new-input default migration, and night with cushions. Verified exact frame/strip bounds, slat dimensions/gaps,
frame profile volume, part counts, ledge bearing and moving/fixed interference. Also checked quarter, half and
three-quarter travel. Five invalid combinations correctly rejected, including an unsupported rear slat at1340 mm length.
Expected caught rejection messages are INFO notices; valid geometry cases produced no reported errors.
This is geometry verification, not a strength or fastening assessment. Saved Part Studio rendering has not been inspected.

Saved Feature Studio without reported errors; exact source readback matched the tested source. Independent review completed.

## Slat visibility control — 2026-10-15

Show slats is a default-on checkbox in Long bench sliding slats. It controls generation of the fixed and moving
timber slats only. The support frames, inner strip, guide ledges and drawer remain available for structural work.
Day/night movement and Show cushions remain independent. Missing values in existing features default to shown.
Transient Onshape evaluation passed all 12 combinations of day/night, cushions on/off, and slats on/off/missing.
No evaluator notices. Saved source readback matched. Browser verification remains unavailable.
The uncommitted local rear-slat alignment experiment was preserved separately and was not included in this update.
Drawer position and its accepted 10 mm floor clearance remain unchanged.

## Independent bench cushions — 2026-10-15

The cross seat follows the shortened fixed bench: 870 x 580 x 100 mm at baseline. Its side backrest is
580 x 200 x 100 mm and fills the cross-bench extension at night. The long seat stays 600 x 1280 x 100 mm;
two full-length 1280 x 235 x 100 mm backrests fill its remaining width at night. No cab-facing backrest remains.
During daytime the long backrests sit front-to-back along X=0–100 and X=100–200, both Y=0–1280, Z=500–735 mm.
Their height is 235 mm above the seat, combined depth 200 mm, leaving 400 mm clear seat depth.
The short backrest occupies X=0–100, Y=1280–1860, Z=500–700 mm.
At night all five cushions fill X=0–1070, Y=0–1860, Z=400–500 mm without overlaps or missing volume.
Widths derive from bed width, fixed long-bench width and cross extension; lengths follow the bench and cargo lengths.
The former cab-backrest length restriction no longer applies. Legacy named c1Length now reports the full long-bench
length; c2Length remains the cross-bench depth. frontUnbacked reports the cab-edge length beyond the side backrest.
Eight transient Onshape scenarios passed with no notices: day/night, edited dimensions, slats hidden, cushions hidden.
Checks include individual cushion volumes, exact placements, pairwise interference and complete nighttime coverage.
Cross-bench extension structure and cushion attachment remain undetailed; this update changes foam geometry only.

## Shared backrest height and cross-bench extension — 2026-10-15

The cross extension now derives from (bed width - fixed long-bench width) / 2, matching the long infill widths.
At baseline all three backrests are 235 mm high; cross fixed frame/seat width is 835 mm and short backrest
size is 580 x 235 x 100 mm. Cross frame aisle X is 817–835 mm. Seat depth remains 580 mm.
Removed the independent Cross bench extension input; an old saved 200 mm value is ignored. The derived value is
available as nv200_crossExtension. Bed and long-bench widths drive future changes without independent overrides.
Eight Onshape cushion scenarios passed with no notices, including edited bed/bench dimensions, legacy input,
exact cross-frame width, both layouts, visibility controls, cushion volumes and complete nighttime coverage.

## Four single-depth backrests — 2026-10-15

The second full-length backrest is split into 750 mm cab-facing and 530 mm rear-end pieces. All four
backrests remain 235 mm high and 100 mm thick. Cab-facing length is an editable 750 mm parameter;
rear length derives as long-bench length minus cab-facing length. Six foam parts total, including the two seats.
In daytime the long wall backrest remains X0–100,Y0–1280 and the short wall backrest X0–100,Y1280–1860.
Rear-end backrest: X100–630,Y0–100. Cab-facing backrest: X100–850,Y1760–1860. All stand at Z500–735.
The accepted overhangs beyond the fixed seats are 30 mm rear and 15 mm cab-facing. Long clear seat depth is 500 mm.
Nighttime order from wall to aisle: full-length orange backrest X0–235, blue seat X235–835,
split backrests X835–1070 (rear piece Y0–530; cab-facing piece Y530–1280).
The cross-seat and short-backrest infill still complete Y1280–1860; all foam lies at Z400–500.
No backrest shortening or corner trim was applied; that earlier request was cancelled.
Ten Onshape scenarios passed: individual volumes, exact placements, no overlaps, complete rectangle,
edited dimensions/split, hidden cushions/slats, default migration. Three invalid split lengths were rejected.

## Moving slat wall endpoints — 2026-10-15

Moving slats now start at wallThickness + layout shift, extending 83 mm beyond their previous ends.
Baseline length is 611 mm: X7–618 retracted, X459–1070 extended. Inner strip remains X90–130
retracted and X542–582 extended. Fixed slats, frames, ledges and travel are unchanged.
Four Onshape scenarios passed for actual endpoints, lengths, unchanged strip and visibility.
The rear moving slat has 6.464 mm clearance to the provisional rear corner surface.

## Daytime checkbox — 2026-10-15

Replaced Layout enum menu with Daytime boolean, default true. Checked selects seating; unchecked selects bed.
The same boolean drives sliding frame, slats, strip and cushions. Show slats and Show cushions remain independent.
Three Onshape checks passed: checked, unchecked, and absent input default; no notices.

## Fixed slat aisle endpoints — 2026-10-15

Fixed slats now end at longBenchWidth + frameThickness, aligning with the retracted moving slats.
Baseline aisle edge is X618 mm, an 18 mm extension. Wall endpoints and moving assembly are unchanged.
Four Onshape cases passed: day/night at baseline and changed bench/frame dimensions, with actual endpoint
checks and no interference against moving slats or their support frame.

## Three sliding-bed angle brackets — 2026-10-15

Three separate steel hardware envelopes follow the first, middle and last moving slats. Baseline centers:
Y130, 640 and 1150 mm. Carinya B21611 nominal arm50 x arm50 x width40 x thickness2 mm.
Brackets attach beneath slats and against the moving frame's inner face, remaining present with slats hidden.
Closed bracket X550–600,Z332–382; extended X1002–1052. Y is center +/-20 mm.
Internal bend radius3 mm and screw-head projection3 mm are PROVISIONAL editable envelopes. Hole positions,
fastener dimensions and actual outer bend profile have not been measured; no fixing holes are invented.

Fixed aisle-frame cutouts at each center: width42 mm; top notch6 mm deep through the18 mm frame;
outer-face pocket6 mm deep and51 mm high. This preserves12 mm thickness behind the face pocket,
with9 mm of the60 mm top band below its lowest edge. Running clearance1 mm.
Pocket depth follows steel thickness + max(bend radius, head projection) + running clearance.
Moving frame, slats, inner strip, drawer and bench overall dimensions are retained.
Guard rejects a bracket width beyond its slat, pockets through the frame/band, and short extension travel
that would collide with the inner strip: travel >= arm - frameThickness + clearance.

Verification: node validate-nv200-brackets.mjs generates nv200-bracket-validation.fs from production source.
Onshape transient evaluator passed eight cases (day/night; drawer closed/open; modified width, frame,
steel and allowances; slats/cushions hidden). Actual bracket bodies checked against the entire assembly.
Two conservative swept boxes per bracket encompass steel, bend and screw-head projections throughout
EVERY position along the slide path; checked against all stationary solid and sheet bodies with at least
running clearance to the fixed aisle frame. Interference and containment are rejected. Short travel rejected.
Removing the top notch or face pocket independently makes the baseline collision check fail.
Independent code review completed; short-travel finding fixed. This verifies model clearance, not joint strength.

## Cross-bench deck, sliding slats and recessed plate stops — 2026-10-15

Cross bench now uses a fixed 12 mm plywood deck at Z370–382 mm, with 18 mm slats above it at Z382–400.
The fixed carcass finishes at Z370; the moving aisle frame finishes at Z382. Its floor-level opening remains clear.
Baseline fixed width835 mm, retracted outer width853 mm, extended outer width1070 mm; slide travel217 mm.
Seven alternating slats fill the580 mm depth: two75 mm fixed end slats, five80 mm slats, six5 mm gaps.
Three moving slats carry the outer U-frame. Daytime drives both benches and cushions; cross slats have their own visibility.
Three angle brackets use the existing common geometry/allowances. Their6 mm top reliefs extend50 mm into the
12 mm deck, leaving6 mm below the reliefs; outer-face pockets also clear their vertical legs. There is no inner tie strip
or separate cross-bench guide ledge. The deck supports the moving slats throughout travel.

Two100x22 mm mending plate envelopes bridge from the first/last moving slats into the adjacent end fixed slats.
The100 mm dimension runs across the slats:50 mm attachment,5 mm gap,45 mm engagement in the fixed slat.
The22 mm dimension runs along slide travel. Both fixed underside rebates have239 mm length, giving217 mm travel.
Baseline plate center X312.5 mm closed /529.5 mm extended; fixed recess X301.5–540.5 mm.
Rear plate Y1310–1410 mm; cab-end plate Y1730–1830 mm. Matching rebates open towards the intervening slat gaps.
Closed recess ends give contact at both travel limits. The assembly can lift free; it has no vertical captive stop.

PROVISIONAL: plate thickness2 mm, fixed recess depth4 mm, running clearance0.5 mm, screw projection1 mm.
Mounting pocket depth3.5 mm, plate Z383.5–385.5; fixed guide ceiling386. This leaves0.5 mm head-to-deck clearance
and0.5 mm clearance above the free plate ends. Thickness, depth, head projection and clearance are editable.
The Zenith listing verifies100x22 mm but does not verify thickness or hole layout. No fastening hole pattern is invented.
Confirm actual hardware before cutting. These are geometric checks; attachment strength is unverified.
Product: https://www.bunnings.co.nz/zenith-mending-plate-100x22mm-4pk-zp_p0821317

The earlier rail and through-deck bolt designs were unpublished drafts and are superseded. The plate stops do not cut
through the deck. A toilet/storage partition and access hatch remain undecided and are not included in this change.

Validation: node validate-nv200-cross-slats.mjs generates tests from current production source.
Ten Onshape cases passed: day/night, rear drawer open/closed, changed widths/frame/platform,600 mm depth,
and independent slat visibility. Actual bodies and conservative full-travel sweeps check the moving slats/frame,
plates, brackets and hardware allowances against stationary geometry. Both plate endpoints contact the closed recesses;
1 mm overtravel interferes with the fixed slats. A continuous bottom-skin test verifies the lid beneath the mechanism.
A4 mm plate with unchanged4 mm recess is rejected because the head envelope would scrape the deck.
Existing long-bench regression also passed eight geometry/sweep cases plus short-travel rejection.
Independent code review found no important issues. Saved Feature Studio source was read back and matched the local source
exactly. Visible Part Studio regeneration/stored inputs were not inspected; all geometry checks used transient evaluation.

## Short cross-bench moving slats — 2026-10-15

Cross moving slats now match the longitudinal slats' extended overlap. At baseline the long fixed slats end X618,
while extended moving slats start X459, giving159 mm overlap. Cross moving slats are376 mm long:
X477–853 closed and X694–1070 extended, overlapping the fixed slat ends at X853 by159 mm.
The fixed deck ends X835, providing141 mm bearing length under extended moving slats.
This leaves the wall-side477 mm free of moving slats when closed; a future lid needs its own split in the
fixed slats and plywood deck plus construction clearance. No lid split or partition is implemented yet.
Cross lengths derive from long-bench geometry, retaining the matching overlap as inputs change.
Plate mounting centers move to X547.5 closed /764.5 extended; fixed recesses are X536.5–775.5.
Stop travel217 mm, recess length239 mm, material dimensions, support frames and existing long slats remain unchanged.
Ten cross geometry scenarios passed, including overlap matching, shortened-slat endpoints, attached stop pockets,
continuous movement, both stop contacts and overtravel rejection. Plate thickness remains provisional.
Eight longitudinal regression cases and short-travel rejection also passed. Independent bounded review found no important
issues. Saved Onshape source matches local source exactly; visible Part Studio was not inspected.

## Cross-bench nighttime cushion swap — 2026-10-15

Night order is now small purple backrest against the wall at X0–235 mm, then the large blue cross seat at
X235–1070 mm. Both retain Y1280–1860 and Z400–500. Daytime positions and all cushion sizes are unchanged.
Five transient Onshape checks passed with no notices: day/night baseline, altered bench/bed widths, and hidden cushions.
Checks confirmed actual body bounds, preserved daytime placement, complete cross-bed coverage and no foam overlap.

## Shared Show slats control — 2026-10-15

The existing Show slats checkbox now controls fixed/moving slats on BOTH benches, the cross-bench plywood lid,
and its recessed plate stops. Removed the separate cross-bench checkbox; old stored showCrossSlats values are ignored.
Frames, guides, angle brackets and rear drawer remain visible. Cushion visibility remains independent.
The deck is removed after bracket clearance cuts so frame geometry is identical whether slats are shown or hidden.
Ten generated Onshape cases passed, including both hidden day/night layouts and conflicting obsolete checkbox values.

## Cross-bench toilet partition and removable storage lid — 2026-10-15

The assumed420 mm toilet depth runs across the van towards the aisle;370 mm width runs along the van.
Toilet bay adds20 mm total depth allowance (editable), giving440 mm clear depth from divider X377 to fixed aisle
frame inner face X817. Toilet height and slide/tray allowances remain unresolved; the aisle header is310 mm high.
No toilet body, tray, slides or sealing claim is added.

Divider uses the existing7 mm skin +18 mm U-frame, with60 mm posts/header and25 mm inside radii.
Skin X370–377; frame X352–370,Y1305–1835,Z0–370. Skin tongues extend18 mm at both ends below the310 mm
header underside, reaching the existing end skins. This closes the otherwise open paths beside the end frames.
Storage clear width327 mm, depth530 mm, height370 mm below the lid away from the perimeter headers.

Top seam is centered over the divider frame at X361. A2 mm seam leaves8 mm bearing for each panel on the18 mm header.
Fixed toilet deck starts X362. Removable12 mm storage lid spans X2–360,Y1282–1858,Z370–382:358x576 mm.
Four wall-side fixed slat sections attach to this lid; all finish at Z400 and are cut within its perimeter.
The moving slats still start X477 when retracted, giving117 mm clearance to the removable lid edge.
A25 mm finger hole at X188.5,Y1570 lies in an exposed gap between lid slat sections.
Lift the lid and its slat sections together after removing obstructing cushions. No hinges/catches are modeled.
Show slats controls both deck pieces, all slats and plate stops. Divider remains visible with Show slats unchecked.

Validation: node validate-nv200-cross-slats.mjs generated12 transient Onshape scenarios, all passing.
Checked divider skin/frame thickness and closure beside end frames, material overlap against all other geometry,
four-sided lid support, plate/slat/frame full-travel clearance, finger access, cushion-removed vertical lid extraction,
400 mm surface, shared visibility, modified bay allowance/lid gap/hole size, and existing stop/overtravel behavior.
Invalid divider positions that trap the lid or consume storage are rejected, along with invalid plate thickness.
Independent source review found no important issues. No load/fastener strength calculation is implied.

## Divider correction: closed rectangular frame — 2026-10-15

The previous divider opening was accidentally cut downward: its sketch normal-X combined with along+Y gave local
vertical-Z. The frame therefore remained largely solid above the floor. A centre-volume probe reproduced this defect;
previous bounds/collision checks and review had missed it. Earlier descriptions of that divider as an open U-frame
were incorrect for the generated geometry.

Replaced the divider with the user's rectangular-frame alternative. Both layers are566x370 mm overall with18x60 mm
recesses at both top corners for existing end-frame cross beams. The18 mm frame has60 mm perimeter members, including
a continuous bottom rail, and a446x250 mm centre opening with25 mm inside corner radii. The7 mm separating panel
remains solid apart from the matching top-corner recesses. Position, lid support and compartment dimensions are retained.
The shared openingTool is used with+X normal and+Y horizontal direction, making its vertical axis+Z.

New tests verify exact remaining frame volume, an empty central probe, continuous bottom rail and skin volume.
These checks reject the previous source's solid-centre geometry. All12 current Onshape cases pass, including existing
lid extraction/support, divider closure, sliding clearances, visibility and changed dimensions. Invalid-input cases
still reject as intended. This corrects geometry; no strength certification is implied.

## Settings-dialog annotation fix — 2026-10-15

Onshape reported precondition analysis failure because the Show slats Description contained U+2019 (curly apostrophe).
Reworded the description with printable ASCII. This was the source's only non-ASCII character.
The generated geometry evaluator did not enforce the UI annotation restriction, explaining the earlier false confidence.
The validation generator now rejects non-ASCII source before making an evaluator test. This deliberately stronger
whole-source restriction prevents typographic punctuation from entering annotations. No geometry changed.

## Storage-lid open preview — 2026-10-15

Added Open storage lid checkbox under Cross bench sliding slats; default false. Checked rotates the12 mm lid and
all four attached slat sections70 degrees upward about its cab-side top edge. Baseline pivot is an X-directed line
at Y1858,Z400; rotation is-70 degrees about+X, lifting the rear/free edge. Hinge hardware remains unmodelled.
Show slats continues to control the whole top assembly; cushions remain independently visible and should be hidden
or removed when inspecting the lid opening. The fixed toilet-side deck, partition and moving bed remain unchanged.

node validate-nv200-lid-open.mjs generated seven transient Onshape cases, all passed with no notices.
Checked actual transformed bounds of every lid piece, preserved contact between slats and lid, closed/open positions
in day/night layouts, hidden slats, independent cushions, and changed platform/bench dimensions. Furniture clearance
was checked at the endpoints and intermediate10 degree positions with cushions excluded; this is a preview axis,
not validation of hinge hardware. Source remains ASCII to preserve the settings dialog.
