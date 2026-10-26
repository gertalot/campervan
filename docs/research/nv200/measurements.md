# Measuring Gert's NV200

The goal is an interior envelope for furniture clearance, including the finished ceiling and existing trim.
Start with the easy measurements below; no trim removal is needed. Record millimetres and photograph endpoints.
Leave inaccessible measurements blank rather than estimating them silently.

## Photographs of Gert's van — 2026-10-18

These photographs show the measured van. Use the owner measurements below for scale and the photographs for shape;
perspective, occlusion and different depth planes prevent direct global pixel-to-millimetre conversion.

| Photo | Owner caption and geometry evidence |
| --- | --- |
| [1. Exterior side](sources/gert-2026-10-18/01-exterior-side.png) | Side of van. Overall roof, window and door outlines, wheel positions and external sliding track are visible. Exterior panel seams are not interior aperture boundaries. |
| [2. Rear opening](sources/gert-2026-10-18/02-rear-opening-bed-extended.png) | Rear door open, bed extended. Owner notes objects beneath the mattress raise its centre: do not infer bed or mattress curvature from that bulge. Shows opening taper, rounded upper corners, rear pillars, fitted floor and insulated wheel arches, partly obscured by storage. |
| [3. Right rear interior](sources/gert-2026-10-18/03-right-rear-interior.png) | Sliding-door rear pillar with its curved transition; rear side window covering and black liner; broad, roughly triangular rear corner pillar. Owner identifies the rear opening moving forward toward the ceiling, shortening the cargo space at the top. Rear cross beam blends into pillars and roof. |
| [4. Open left sliding door](sources/gert-2026-10-18/04-left-sliding-door-open.png) | Open door sits outside the body and overlaps the opening's rear portion. Shows rounded lower opening corners, fitted floor edge and external recessed step/track. The step is distinct from the interior floor datum. |
| [5. Folded chair](sources/gert-2026-10-18/05-folded-chair.png) | Folded tubular-frame chair with wooden armrests and projecting hinge fittings. Storage clearance must include these extremities, not just the fabric rectangle. Use the measured 600 × 700 × approximately 100mm envelope per chair. |
| [6. Cab and ceiling junction](sources/gert-2026-10-18/06-cab-seats-headliner.png) | Backs of both integrated-headrest front seats and dash. Plywood ceiling meets shaped cab headliner; exposed metal side roof rails remain visible. Headliner flares at the sides rather than forming a uniform transverse strip. Seat shoulders and head supports are rounded; passenger seat has a hard rear panel. |
| [7. Right sliding-door interior](sources/gert-2026-10-18/07-right-sliding-door-interior.png) | Clear view of rear opening edge's smooth S-shaped offset, upper roof rail, cab-headliner junction and driver's seat rear. Door/window recesses, seals and pillar surfaces are distinct boundaries. |

Geometry implications: fit the rear pillars and header as connected shapes, including the rear opening's forward rake
toward the ceiling; use the 60mm straight section plus 200mm flared section for its plan profile. Fit the sliding-door rear edge
with a smooth transition through the measured 630–770mm height band. Keep the shallow plywood ceiling crown
(20mm wall-to-centre rise at the measured station) distinct from the deeper roof rails and shaped cab headliner.
These photographs do not expose complete wheel-house profiles or hidden ceiling bows and do not establish exact
fillet radii, rear-opening rake or door travel. These photographs and measurements inform the vehicle model; see [CAD conventions](../../cad-model.md) for applied
values, approximations and the unresolved longitudinal measurement chain.

## Owner measurements — 2026-10-18

See the [generated-model dimension audit](dimension-audit.md) for measured matches, unapplied measurements and
the unresolved longitudinal measurement chain. Do not adjust furniture to compensate for that conflict.

| Measurement | Value (mm) | Reference / certainty |
| --- | ---: | --- |
| Wheel centres, front to rear | 2700 | Owner measurement; catalogue wheelbase is 2725; retain both separately |
| Existing bed slat top | 390 | Above the fitted cargo floor; excludes cushions |
| Existing bed rear edge forward of rear opening at pillar | About 100 | Fore–aft distance measured at slat height, Z = 390 above fitted floor; opening/pillar reference, not closed hatch inner surface |
| Existing bed rear edge forward of rear opening at van centreline | About 220 | Same slat-height measurement, Z = 390 above fitted floor; opening curves outward/rearward at the centre |
| Existing bed rear edge to closed rear-door inner panel at centreline | 130 | Clear fore–aft gap with rear door closed; continuing the slat-height measurement context (Z = 390 above fitted floor) |
| Existing mattress thickness | 100 | Owner-confirmed; mattress top is 490mm above fitted floor (390 + 100) |
| Mattress rear edge to front-seat backs at mattress height | 1890 | At Z = 490 above fitted floor, with seats in their measured positions; seat adjustment/recline, lateral measurement position and mattress-to-bed rear-edge alignment not recorded |
| Front-seat back to sliding-door opening at mattress height | 150 | At Z = 490 above fitted floor; interpreted as fore–aft distance to the opening's front edge beside the seats; signed direction not explicitly stated |
| Front-seat back to sliding-door opening at headrest base | 80 | At Z = 870 above fitted floor; same opening-edge interpretation as the mattress-height measurement |
| Headrest base above mattress top | 380 | Headrest base is Z = 870 above fitted floor (490 + 380); measured seat/headrest adjustment applies |
| Rear width between pillars at floor height | 1250 | Floor interpreted as fitted floor (Z = 0); between pillar surfaces, not explicitly between rubber seals |
| Rear-door opening width at existing slat-top height | About 1265 | At Z = 390 above fitted floor (about 408 above vehicle floor); interpreted as clear opening, exact endpoints unconfirmed |
| Rear-door opening centre height, seal to seal | 1280 | Between the top and bottom rubber seals at the centre; bottom seal height relative to fitted floor not yet measured |
| Rear-door opening width 60mm below its maximum height | About 1115 | Interpreting maximum height as the previously measured top seal at centre: 1220mm above the bottom seal; lateral endpoints unconfirmed |
| Fitted floor plywood thickness | 11–12 | Owner uncertain between these thicknesses |
| Fitted floor surface above vehicle floor | About 18 | Total build-up, including the plywood; underlying surface details unconfirmed |
| Ceiling plywood fore–aft length | 1420 | From the inside face of the rear cross beam to the cab headliner; endpoints not yet located against the rear-threshold Y datum |
| Plywood ceiling to mattress top at wall | 780 | Interpreted as vertical clearance to ceiling underside; ceiling is Z = 1270 above fitted floor (490 + 780); fore–aft position and vehicle side not specified |
| Plywood ceiling to mattress top at centreline | 800 | In response to the same-station comparison with the wall measurement; ceiling underside is Z = 1290 above fitted floor (490 + 800), 20mm higher than at the wall |
| Rear door opening to ceiling plywood rear edge | 240 | Interpreted as fore–aft distance, with the plywood edge forward of the opening; opening reference relative to floor threshold unconfirmed |
| Width between rear sliding-door pillar centres at ceiling height | 1220 | Pillars at the rear edges of the sliding-door openings; transverse centre-to-centre measurement, not clear width between inner faces; exact ceiling height remains unspecified |
| Width between rear sliding-door pillars at existing mattress-top height | 1420 | At Z = 490 above fitted floor; same rear-edge pillar pair as the ceiling measurement; whether endpoints match the ceiling centre references remains unconfirmed |
| Clear width between inner side panels below rear side windows | 1500 | At existing mattress-top height, Z = 490 above fitted floor; between panel surfaces; exact fore–aft measurement position not recorded |
| Sliding-door rear pillar rearward curve: lower height | About 630 | 140mm above existing mattress top; start of the transition to the wider upper opening |
| Sliding-door rear pillar rearward curve: upper height | About 770 | 280mm above existing mattress top; end of the transition to the wider upper opening |
| Sliding-door opening fore–aft width, narrower part | 740 | Earlier measurement, superseded by 680mm between the later 1210/1890 rubber-seal endpoints |
| Sliding-door opening fore–aft width, wider part | 820 | Earlier measurement paired with 740 lower width; model uses their 80mm difference with the revised 680 lower width, giving an estimated 760 upper width |
| Sliding-door opening centre height above fitted plywood floor | 1170 | From plywood floor top to the top of the opening at its centre; floor-based measurement, not a sill-to-top aperture height |
| Front sliding-door pillar to open door edge | About 680 | Fore–aft distance with door open; door edge sits forward of the opening's rear edge, reducing access; exact pillar face, height and full-open stop position not confirmed |
| Mattress edge to outside of open sliding door | 270 | Interpreted as transverse distance outward from mattress side edge; door open, measurement height unspecified |
| Mattress edge to inside of open sliding door | 170 | Same mattress-edge interpretation and open-door position as outside measurement |
| Mattress edge to outside of side pillar | About 110 | Same transverse mattress-edge reference assumed; exact pillar face and height unspecified |

| Rear corner pillar constant-width section, fore–aft length | About 60 | Owner clarified: local length of the straight section beside the pillar, measured parallel to the vehicle centreline |
| Rear corner pillar flared triangular section, fore–aft length | About 200 | Owner clarified: length of the flared section itself, parallel to the centreline; not an endpoint coordinate. Straight plus flared length is about 260 |
| Rear pillar flare/side-wall junction to sliding-door opening | 900 | Parallel to the centreline, at existing mattress-top height Z = 490 |
| Closed rear door beside rear pillar to sliding-door opening | 1100 | Earlier rear-opening position, superseded by 1210mm to the rubber seal |
| Aft sliding-door sidewall/pillar fore–aft width | 180 | Section blending into the rear side panel, measured at Z = 490 |
| Rear pillar corner to rear edge of wheel arch, along side panel | 140 | Earlier measurement; superseded for longitudinal placement by the direct rear-door-to-arch measurements below |
| Wheel-arch fore–aft length on inner (aisle-facing) side, including insulation | About 700–720 | Includes neoprene/aluminium insulation, not bare metal; insulation thickness unmeasured |
| Front edge of wheel arch to rear edge of sliding-door opening, along wall | 140 | Earlier measurement; superseded for longitudinal placement by the direct rear-door-to-arch measurements below |
| Closed rear door beside pillar to rear of wheel arch | About 310 | Parallel to centreline, using wall-side arch endpoint; owner notes measurement difficulty and possible small errors |
| Closed rear door beside pillar to front of wheel arch | About 1070 | Same reference and wall-side measurement as rear endpoint |
| Wheel-arch wall-side fore–aft length | About 760 | Derived: 1070 − 310; consistent with wall side being longer than the 700–720 inner side |
| Closed rear door beside pillar to rear sliding-door opening endpoint, later measurement | About 1210 | Owner confirmed rubber seal of the body opening, not parked sliding-door edge |
| Closed rear door beside pillar to front sliding-door opening endpoint, later measurement | About 1890 | Same reference as the later 1210 rear endpoint; measurements approximate |

The owner confirmed the later endpoints are the rubber seals. They give a 680mm lower opening (1890 − 1210)
and a 140mm gap ahead of the wall-side wheel arch (1210 − 1070). Use these direct endpoints instead of the
previous 1100 rear-opening position and 740 lower width. The earlier 680mm open-door access remains recorded;
the measurements no longer imply a 60mm overlap at mattress height.

On 2026-10-26, Gert reconfirmed that the fully open sliding doors overlap the rear of the openings and requested this
in the drawing. The CAD uses a provisional 60mm overlap at the lower opening, giving 620mm open access across its
680mm width. **Open clear width** controls the open-door position. The overlap amount needs a direct measurement.

The 900mm rear pillar/side-wall junction to opening measurement now implies a junction at 310 relative to the
closed-door reference, rather than the earlier inferred 200. This conflicts with the previous rear arch gap
and is not used to relocate the rear corner without reconciling the surfaces. The direct arch measurements
establish its wall-side length as approximately 760mm. Measurements are approximate due to access difficulty.

The lateral offsets place the open door's inner face about 60mm
outside the pillar's outer face (170 minus 110), with a 100mm span between the measured inner and outer door surfaces
(270 minus 170). These are conditional differences between measured surfaces, not established uniform door thickness
or clearance along its entire travel. The mattress side-edge position relative to the van centreline remains unmeasured.
The owner subsequently confirmed that closed doors are flush with the body outside and the pillars inside.
On 2026-10-19 the owner confirmed approximately 100mm sliding-door thickness and requested exterior body surfaces
outside the measured interior walls. The model now uses 100mm door depth: 40mm inward pillar intrusion plus 60mm
outward body depth. Closed doors align with the pillars inside and the new body exterior outside. This depth is a
transverse approximation; its variation along the door remains unmeasured. Open inner-face standoff remains 60mm
from the exterior, giving 160mm to the open outer face.
The later interior door photo shows a wide, shallow window and the inner metal sloping outward to meet the glass.
The model uses a provisional 560 × 280mm glass opening, 80mm below the header, with a 30mm surround. These are
visual estimates, not measurements from a rectified photo. The glass sits near the outside skin; the inner metal
is recessed around it rather than maintaining full pillar-depth thickness up to the opening.
The subsequent photo showing both side windows, with insulation covering the rear glass, shows a similar rear
window profile. The owner explicitly corrected the height comparison to **slightly taller**. Rear glass is modelled
at an estimated 600 × 300mm versus 560 × 280mm in the sliding door, with a 30mm recess from the inner surround.
The glass is 8mm inside the existing exterior profile; the local surround extends 38mm inward. These depth
estimates keep both glass and metal within the exterior, rather than projecting them outside a zero-thickness wall.
The owner also noted the higher rear-window top. The rear glass is therefore placed 20mm higher at its top
(Z = 1110 versus 1090), keeping the bottoms approximately aligned at Z = 810. This offset is a photo estimate,
adjustable independently through the rear window's 60mm top-gap setting.
The insulation conceals the exact glass boundary; none of these rear-window dimensions are direct measurements.
The subsequent interior rear-corner and exterior closed-hatch photos show broad rear-door glass, rounded corners,
a slightly narrower top, and a substantial lower metal panel. Provisional hatch glass dimensions are 1000mm at
the bottom, 940mm at the top, 450mm high, with a 100mm top gap. The 30mm glass recess and 38mm total door depth
are estimates. The existing measured inner-panel position is retained; door depth extends outward from it.
Assuming the existing bed's rear edge is straight across the van, the rear-opening reference at the centreline lies
about 120mm farther aft than at the pillar (220 minus 100). The opening therefore must not be represented as a
single transverse plane at slat height. Keep the pillar-based fore–aft distances separate from this centreline
reference; neither opening measurement establishes the curve at other heights. The separately measured closed-door
clearance is 130mm at the centreline. At the same height and bed endpoint, this places the inner door panel 90mm
forward of the centreline opening reference (220 minus 130); this is a reference offset, not door-panel thickness.

In plan view, the rear corner pillars have an approximately triangular profile: maintain the rear opening width
for 60mm, then flare outward over a further 200mm: 260mm combined longitudinal extent. These are local section
lengths beside the pillar, not offsets from the bowed centre of the rear opening. The side-panel clear width is 1500mm at mattress height (Z = 490 above fitted floor).
The height of this observed corner profile was not specified; do not assume the same cross-section at every height
or combine the 1265mm opening width at Z = 390 with the side-panel width at Z = 490 as a measured same-height taper.

The original opening widths imply an 80mm fore–aft change, with the lower rear-pillar curve observed between
approximately Z = 630 and 770mm above the fitted floor. The intermediate shape has not been measured. Following
the owner's later photo comparison, the model distributes an estimated 20mm of that change into a gently inclined
upper edge, leaving 60mm in the lower curve. Assigning the change to the rear pillar assumes the front edge stays
at the same fore–aft position. The lean is an adjustable photo-based approximation, not another measured constraint.

The owner's close photo of the lower sliding-door pillar and insulated wheel arch shows the pillar trim meeting
the curved arch. Their longitudinal extents can overlap in projection, but the interior envelopes must not occupy
the same volume. The model trims the lower pillar against its shared rounded wheel-house envelope; the junction
remains approximate because the insulation and pressed trim profiles have not been measured.

Together, the ceiling measurements place the plywood rear edge 240mm and its cab-headliner junction 1660mm forward
of the rear door opening, assuming both distances are fore–aft and share the same plywood endpoint. This opening
reference is not yet established as identical to the floor threshold or the model's closed rear-door plane.

The existing bed slat top is therefore about 408mm above the vehicle floor. The remaining 6–7mm below the plywood
is inferred from the total build-up; its construction is unknown. These describe the existing van, not a decision
about the new bed height. Record subsequent interior heights above the fitted floor unless explicitly noted otherwise.
The CAD model uses the fitted floor as Z = 0, with 12mm plywood and a vehicle-floor reference 18mm below it.
The owner confirms that the floor's rear edge is straight and the plywood has cutouts around both wheel arches.
The curved rear-door opening is a separate reference, not the outline of the floor sheet.

## Items to accommodate

| Item | Width (mm) | Height (mm) | Depth (mm) | Storage intent |
| --- | ---: | ---: | ---: | --- |
| Folded solar panel | 830 | 760 | About 80 | Upright between the bed rear edge and closed rear door; owner-measured folded dimensions |
| Folding chairs (2) | 600 each | 700 each | About 100 each | Owner-measured folded dimensions; storage location undecided; allow about 200mm combined depth when stacked without nesting |

The owner confirmed on 2026-10-19 that the folded solar panel bag fits the **existing** interior behind the bed
with about 20–30mm spare clearance. This observed fit constrains the hatch shape; do not shrink the bag or move
furniture to compensate for a collision with the estimated vehicle geometry. The 130mm centreline gap alone
does not describe clearance across the bag's full width and height. The current provisional hatch curves into
the upright bag reference above roughly Z=550; reconcile that vehicle-model discrepancy separately.

## Establish repeatable references

- Use the flat cargo floor as Z = 0. Note whether this is metal, an existing covering or a fitted floor.
- Mark a transverse line at the cargo-floor rear threshold; this is the measurement Y = 0. Positive Y goes toward cab.
- Mark a longitudinal centreline, with a square or equal offsets from matching body features.
- Measure left and right distances from that line separately. These can be mapped to the model's X coordinates later.
- Record the offset between the threshold and the closed hatch's innermost surface. They are not the same datum.

Use a tape, straightedge, square and masking tape. A plumb line helps transfer high points to the floor.
Keep normal driving seat positions fixed while measuring. Note seat recline, floor covering and whether doors are shut.
For the cab floor, seats and headliner, follow the [cab measurement sequence](cab.md#small-measurement-set-to-resolve-the-remaining-uncertainty)
using these same datums.

## First visit: the measurements that resolve most uncertainty

| Measurement | How to record it |
| --- | --- |
| Bed rear gap to closed hatch | Measured centreline clearance is 130 at slat height; measure across the upright solar panel's footprint and height if checking its fit |
| Usable length | Threshold to seat backs at floor, bed-top and cabinet-top heights; both sides |
| Width | At floor, 400, 800 and 1200 above floor, at the stations below |
| Finished ceiling | Height at centreline and 300 / 600 to each side, at each station |
| Wheel houses | Rear and front Y, maximum Z, inward-most X on each side |
| Rear aperture | Clear width at sill, middle and top; height at centre and both sides; sill Z |
| Sliding openings | Each opening's front/rear Y, sill Z, width and height; record rounded corners |
| Existing trim | Largest intrusion where furniture approaches panels, handles or pillars |

Choose stations at the rear aperture, wheel-house centre, rear edge of the sliding opening, and just behind the seats.
Record their actual Y distances; do not force them onto presumed brochure positions. At a pillar or bulge, add a
nearby station on each side of the obstruction. Width should be measured horizontally, not along a sloping panel.

Use this repeatable record for each section:

| Y from threshold | Z above floor | Left distance from centreline | Right distance from centreline | Surface / note |
| --- | --- | --- | --- | --- |
| | | | | |

For roof points, record Y, sideways distance from centreline and ceiling Z. Record the underside of ribs or lining
where that is the actual clearance limit. The lining should not be inferred by subtracting 3mm from catalogue height.

## Ceiling bows

Number the visible bows from rear to front. Include the rear header and cab header separately.
For each accessible member, measure:

- Rear and front edges from the same rear-threshold Y datum; centre position is their average.
- Fore–aft width including flanges, and width of the lower face if different.
- Floor-to-underside height at the centreline and 300 / 600mm to either side.
- Drop below the adjacent roof skin at those same points, where exposed.
- End positions where the bow meets the side roof rails, and any brackets projecting below it.

Also record whether the fitted plywood passes below the bows or fits between them. Do not remove lining just to
complete the table; mark hidden dimensions unknown. A photo showing the whole ceiling establishes the bow count
and distinguishes any seat-belt reinforcement from the narrow bows.

| Member | Rear Y | Front Y | Underside Z at centre | Drop below roof | Notes |
| --- | --- | --- | --- | --- | --- |
| Rear header | | | | | |
| Rear bow | | | | | |
| Middle bow | | | | | |
| Front bow | | | | | |
| Cab header | | | | | |

## Second pass: curves and door motion

For a curved wall, hold a vertical straightedge at a recorded sideways offset and measure horizontal gaps to the
surface at several heights. For the roof, use a horizontal straightedge and measure upward gaps across its width.
A cardboard contour template can help at a tight corner; include a ruler in a square-on photograph.

For the tailgate, record hinge-axis height and Y if accessible, closed inner-panel depth, and lowest open-door height
above the cargo floor. Photograph the hinge area and door side-on, closed and fully open. The gas struts and handle can
intrude farther than the broad door panel. We can approximate the leaf first and add those obstacles where relevant.

For each sliding door, photograph closed, just clear of the opening and fully open. Measure outward displacement and
rearward travel of the same marked point. Also record the gap between the open door and van side. This gives a useful
motion envelope without reverse-engineering the complete roller mechanism.

Measure wheel-house longitudinal profiles at the wall and inner edge if the furniture needs a close fit. A single
rounded box cannot capture taper or asymmetric front/rear shoulders reliably.

## Using the results

The main editable controls under **Vehicle references** map to these measurements:

| Measurement | Sidebar control |
| --- | --- |
| Main cargo width, with endpoints recorded | Floor outline → Width (body and layout) |
| Rear datum to chosen cab boundary | Body length; keep Furniture layout length separate |
| Bare roof centre height, if accessible | Bare roof height |
| Width where wall turns into roof | Side walls → Roof shoulder width |
| Height where the lower wall starts leaning inward | Side walls → Taper starts above floor |
| Centre roof height minus shoulder height | Roof → Bare roof → Crown rise |
| Bow centre positions and fore–aft widths | Roof → Roof bows → Position / Fore–aft width |
| Roof-to-bow underside distance at centre | Roof → Roof bows → Centre depth |
| Bow underside centre height minus height at roof shoulders | Roof → Roof bows → Underside crown rise |
| Actual lining sheet thickness | Roof → Finished ceiling → Plywood thickness |
| Front edge of each side aperture relative to body front | Side walls → Left wall / Right wall → Door setback |
| Rear aperture widths, height and corner extent | Rear opening controls |
| Wheel-house bounds and rounded crown | Wheel arches controls |

Measure wall width at cabinet-top and roof-shoulder heights before using the scribed cabinet outlines for fabrication.
Its contours follow the estimated body and ceiling. If measured left/right or front/rear profiles differ, retain
those readings; they are evidence to add another section, not values to average away to fit the symmetric model.

Record whether a value is measured, taken from Nissan documentation or estimated. Keep approximate readings rounded
to the precision actually achieved. Owner measurements with clear endpoints take precedence for this van's fit.
Once the broad envelope is fitted, remeasure only locations where the furniture is close to an obstruction.
