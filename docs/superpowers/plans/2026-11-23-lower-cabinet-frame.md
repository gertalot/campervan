# Lower cabinet shared frame implementation plan

Goal: model compartments 1, 2 and 3 as one lower timber carcass, for visual inspection before adding plywood.
The approved design is the conversation's shared lower-frame proposal; the fitted reference is
[data/cabinet-reference](../../../data/cabinet-reference/README.md).

Use the existing Python/build123d cabinet entry point, assembly placement, timber material and visibility paths.
Do not build the upper cabinet, doors, shelves, skins or hardware in this step. Do not create or run tests,
start services or change unrelated furniture. Preserve the checkpoint and saved envelope.

- [x] Replace the legacy cabinet builder with the shared lower frame. Reuse `cabinet_layout` for the aisle,
  bay and height datums, and `backing_profiles` for the deeper wall limit. Keep the existing 40 × 18mm pine.
- [x] Build matching aisle and shallow wall ladders, sharing the centre posts. Reserve 6mm end skins.
  Keep the rear loading end free of bottom and intermediate transverse rails.
- [x] Connect the deeper front upper compartment with depthwise members at its bottom and top. Its wall
  posts bear on the bottom frame; the end joints connect back to the floor-standing shallow frame.
  Reserve flush shelves on face-mounted ledgers; no shelf is trapped between stacked frame members.
- [x] Restore only this frame to the existing Cabinet / Lower module / Frames path. Document the construction
  and limits, regenerate through the running app and use native geometry checks plus Gert's visual inspection.

## Evidence and modelling decisions

Native construction coordinates; floor-relative Z. Keep aisle X1100, local length980, first shelf top510 and
module split770. The frame occupies local Y6–974, allowing the existing 6mm end skins to retain overall Y0–980.
Middle posts remain Y533–573 on both ladders; future partitions are infill panels meeting frame faces, not
complete sheets passing through the timber. Shared rails/posts are modelled once.

Direct inspection of registered scan vertices found the arch at X1346.640 within local Y46–533, Z5–300.
The old X1354.698 wall datum was only verified for end posts and high rails; a new floor-standing middle post
there would cross the arch. Use a straight shallow wall outer face X1343, with the 3mm nominal scan clearance
checked against the actual mesh. This moves framing inward, not the saved exterior skin envelope.

The deeper upper wall frame is vertical, parallel to Y. Its maximum X comes from the existing lower backing's
inner face at Z770 (about1425), preserving space for 6mm plywood outside. No yaw or slanted 18mm posts.

Rails meet posts with glued reinforced butt joints (dowels or screws, as selected by Gert). Square stock end
lands are retained; drilling details remain to choose. The wall-side depth extension transfers load through
its connected transverse members into the shallow floor-standing posts. This is a geometric frame proposal,
not a capacity calculation. Later plywood provides racking restraint and needs deliberate face attachments.

## Completion evidence

Native construction after the user correction: 36 valid single-solid members, one connected frame and no
member overlaps. Clipping registered scan triangles against every member’s 3mm-expanded bounds found no
contacts, excluding the assumed flat floor. Existing-app regeneration is recorded below. No tests or new services.

## User correction: aligned frame and extra level

The depth-step supports do not require an offset. Centre all 18mm transverse rails on the 40mm post faces.
Divide the former box 2 into two full-depth compartments: one immediately above the arch, the other above
the preserved Z510 mattress-access door datum. The measured arch crown reaches world Z283.485 in the
future wall-facing infill band. Round up to284, add3mm clearance and the40mm on-edge rail: lowest deep-frame
level is Z317 above the floor. Deep wall posts start at the rail underside Z277 and connect with centred
reinforced butt joints, rather than relying on an offset bearing arrangement. The shelves remain future infill.

Existing Chrome app: model revision9 published and ready without error; cutting revision9 contains36 cabinet
frame members. Gert's visual inspection and the later joint/panel design remain the acceptance steps.

## Deeper wall frame

Gert requested more wallward depth. Clipping the registered scan triangles to local Y530–977, Z274–773
(the full frame plus3mm clearance) found minimum wall X1454.492, including the front pillar. Set the vertical
wall timber face to X1445, allowing6mm future backing plus at least3mm gap. This adds20mm depth to both
above-arch compartments and stays within the saved maximum exterior X1460. Existing connecting members
lengthen from the same datum; the centred joints, shelf heights and placement are unchanged.

## Rear opening and skin attachment faces

Remove the two Z510 longitudinal rails from the tall rear bay, retaining its top and bottom rails.
Keep the middle transverse rails centred, but make rear/end transverse rails flush with the exposed
post faces: rear rail Y6–24, cab-end rails Y956–974. This provides coplanar end-skin attachment faces.

## Shelf supports

Add four361mm-long18×18mm ledgers: aisle/wall pairs with tops Z311 and504 for future6mm shelves.
Lower only the internal cab-end shallow wall rail beneath the arch-level shelf from317 to311.
Shelf ledgers belong to Lower module / Frames / Shelf ledges and share the existing18mm pine product
through the material/cutting mechanism. Shelf panels and joint drilling are not added in this step.

## Complete shelf-edge supports

Add side ledgers and supports for both top shelves at Z770. All four edges of each front shelf at317,510,770
and the rear top shelf now have18×18mm support. Side pieces stop at retained posts and butt between long
ledgers without overlap. There are20 pieces total:6+5+5 for front levels and4 for the rear top. Shelf outlines
remain to fit; no plywood or extra shelves are added across the chair-loading opening.

## Close ledger corners

The long ledgers wrongly stopped at post edges while the side ledgers followed transverse frame faces.
Extend the front long ledgers to Y562–956 (394mm), and rear ledgers to Y24–544 (520mm). Use one middle
side strip per front shelf, notched11mm deep around the post, retaining its7mm bridge. The lowest cab-end
side support remains two pieces because its post fills the full width. Verify the shelf-edge support rim
against the ledger and post geometry, not merely the whole frame’s connectivity.

The Z317 middle support keeps two pieces: its post plus the lowered internal rail fill the gap completely.
The notched single strips apply only at Z510 and Z770, where no internal rail occupies the7mm bridge.

## Straight middle ledger pieces

At Gert's request, replace the two notched middle side supports (Z510/Z770) with pairs of square-ended
straight pieces stopping against the upright. Remove the notch code. The20 ledger pieces retain closed
outer corners; the7mm recess behind the middle post no longer has a narrow timber bridge.

## Add shelf panels

Four6mm sheets share the ledger layout: front309×394mm blanks at317/510/770, rear207×520mm at770.
Subtract only existing frame timber from each blank to form open post cutouts while retaining constant
thickness. The front middle cutout is18×11mm, with an additional18×22mm at the lowest cab end.
Use Lower module / Shelves and the existing shelf material/visibility mechanisms.

## Rebated front panels

Add cabinet3 fixedcover and threefrontdoors,6mmply,10×6mmfrontframerebates,2mmclearance and8mmoverlap.
Reuse panel_rebate, piano_leaves and the previousdoor/backingconstruction, replacing obsoleteopening
layout. One side-hingedbottomdoor; two bottom-hingedflaps. Addmiddleflapcontrol, retirethreereardoor
controls becausecabinet3isfixed. KeepauthoritativeDoorControls shared bygeometryandlivemotion.
Oldcatchblocksandkeeperreliefsare omittedbecausetheyconflictwithnewledgers; catch/stayplacementremains.

Door authoring checks: all71 native leaves valid; moving plywood/backing checked at0,15,30,45,60,75,90°
against rebated frame, shelves and fixed cover with no solid collisions. Above-bed flap checked against
fully extended nominal foam: no sampled collisions, minimum12mm gap. Existing app published revision2
and its matching cut list with three doors, three18mm backing strips and the fixed cover. These checks
exclude actual hinge screw patterns and soft furnishings beyond the nominal foam geometry.

## Door roller catches

Use the existing Taskmaster catch product and earlier nominal hardware sections, rotated for side mounting.
Place 40×18×40mm pine blocks behind the free upright at X1118–1158,Y944–962. Bottom-door centre Z158.5;
flap centres Z450/710 put block tops flush below the cross rails. Two countersunk6g×40 frame fixings and
glue attach each block. Two M3×12 bolts and backing washers attach each moving keeper. Local back-lip
relief clears the keeper; no ledger notches or door/front outline changes. Blocks follow Frames, fixed
catch bodies follow Doors, and each keeper/fixing assembly follows its moving door. Physical catch size,
drill patterns and holding force remain unverified; flap stays are not part of this step.

Catch authoring checks: all104 native leaves valid, no static timber overlaps. Moving panels, backing
strips and keepers checked at0,5,15,30,45,60,75,90° against the frame, shelves and blocks: no collisions.
Plywood/backing clear the fixed catch bodies; the above-bed assembly clears nominal extended-bed foam.
Existing app published matching model/cut revision2, with three catch sets and three40×18×40mm blocks;
keeper bolts, washers and block screws each total six. These are geometry checks, not retention testing.
## Shorter catch mounting blocks

Reduce the mounting-block projection from40 to30mm, retaining the40×18mm stock section and all fixing
positions. The nominal25mm base retains5mm backing margin; frame screws embed22mm into the block,
leaving8mm beyond their tips. Native geometry remains one valid solid; the cut length is30mm.

## Align the shallow wall frame with the physical floor

Gert confirmed the real1200mm floor fits between the wheel arches. Use that physical datum for the shallow
wall frame: nativeX1350/displayX150, a7mm move wallward, with aisleX1100, deepwallX1445 and heights unchanged.
Share FLOOR_BASE_WIDTH_MM from the existing floor builder; dependent rails, ledgers and shelf cutouts follow
the datum. Rear clear width/top shelf depth becomes214mm. Keep full timber sections; do not introduce an
arch notch based on a few millimetres of scan disagreement. Three-millimetre scan clearance is not claimed
for the affected lower members; higher-up fit remains to confirm against the vehicle.
