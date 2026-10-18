# Vehicle dimension audit — 2026-10-18

Compared the running project's parameters and generated geometry with
[Gert's measurements and photographs](measurements.md). This records the model before resolving the longitudinal
datum conflict; it does not certify the vehicle dimensions. Cabinet dimensions have not been changed.

## Longitudinal measurement chain

The owner confirmed the new opening endpoints are the **rubber seals**, not the parked sliding-door edge.
Use these approximate measurements parallel to the centreline from the closed rear door beside the pillar:

| Reference | Position / length (mm) |
| --- | ---: |
| Wall-side arch rear / front | 310 / 1070 |
| Wall-side arch length | 760 |
| Lower sliding-opening rear / front rubber seal | 1210 / 1890 |
| Lower opening width | 680 |
| Arch front to lower opening | 140 |
| Aft sliding-door pillar fore–aft width at mattress height | 180 |

Both modelled openings use these positions. The upper width is estimated at 760mm, preserving the original
80mm rearward transition (820 − 740) with the revised 680mm lower opening. This gives an upper rear edge at 1130
and a 100mm upper pillar width, versus 180mm below. Keeping the old absolute 820mm upper width had incorrectly
increased the transition to 140mm and reduced the upper pillar to 40mm; the owner flagged that shape visually.
Comparison with the owner's close interior photo also showed that a vertical upper edge and concentrated S-bend
made the shape look too abrupt. A 20mm adjustable upper lean now distributes part of the same 80mm change above
the lower curve, with tangent joins: pillar width 180 below, 120 at Z = 770, 100 at Z = 1110 before the roof return.
This lean is a visual estimate, not a dimension extracted from the oblique photograph.
The upper width remains an estimate. The 1210/1890 seal measurements supersede the earlier 1100 rear
position and 740 lower width. The 140mm front arch gap is now consistent with the direct measurements.
Cabinet dimensions remain unchanged; its arch cutouts follow the updated arch parameters.

The rear-corner geometry is still unresolved. The owner described 60mm straight plus 200mm flared local lengths;
the model retains 200mm total extent. The earlier 900mm wall-junction-to-opening span combined with the revised
1210 endpoint implies a junction at 310, coinciding longitudinally with the arch rear. That differs from the
previously inferred 200 junction and earlier 140 rear gap. Do not move the rear corner solely to absorb this
conflict. The closed-door reference also remains distinct from the rear-opening datum used by the floor and bed.

The seats have not been moved: their measured bed-to-seat distance is still preserved. Moving the front opening
from 1840 to 1890 reduces the model's opening-to-seat clearance by 50mm, so it no longer matches the earlier
150/80mm seat-clearance measurements. This remaining reference conflict is recorded rather than shifting the
seats and breaking the bed-to-seat measurement.

## Other measurements

| Reference | Owner measurement (mm) | Generated model / status |
| --- | ---: | --- |
| Wheelbase | 2700 | Not represented: no front axle or wheels in the interior model. Catalogue 2725 is recorded separately. |
| Wheel-arch inner-side length | 700–720 | Uniform 760mm base footprint remains a clearance approximation; shorter inner side has not been represented. |
| Wheel-arch wall-side length | About 760, derived from 310–1070 endpoints | 760; both arches placed at Y = 310–1070. |
| Wheel-arch height / intrusion | Unmeasured | 280 high × 140 intrusion, estimates. Clear separation 1220 is a catalogue reference. |
| Bed rear to seat back at mattress height | 1890 | 1892.6, both seats. |
| Front opening edge to seat back at mattress height | 150 | About 102.6 after revised opening position; reference conflict above. |
| Front opening edge to seat back at headrest-base height | 80 | About 37.6 after revised opening position; reference conflict above. |
| Headrest-base reference height | 870 | Nominal shoulder station about 870; upholstery remains approximate. |
| Lower / upper sliding opening width | 680 / earlier 820 paired with 740 lower | 680 / 760; lower measured, upper estimated to preserve the original 80mm transition. |
| Sliding opening centre height above fitted floor | 1170 | 1170. |
| Rear pillar opening transition heights | 630–770 | 630–770. |
| Side-panel width at mattress height | 1500 | 1500. |
| Clear width between rear sliding pillars at mattress height | 1420 | 1420 (inner faces at X = 40 and 1460). |
| Rear sliding-pillar centre spacing at ceiling height | 1220 | Not explicitly fitted. Pillar solids end at Z = 1170 and meet approximate roof rails. |
| Rear opening width at floor | 1250 | 1250. |
| Rear opening width at Z = 390 | 1265 | 1265. |
| Rear opening width 60 below top | 1115 | 1115 at Z = 1220. |
| Rear opening seal-to-seal centre height | 1280 | 1280; bottom seal elevation relative to finished floor is still assumed zero. |
| Bed rear to opening, at pillar / centre | 100 / 220 | 100 / 220 at Z = 390. |
| Bed rear to closed hatch inside, centre | 130 | Surface constrained to 130 at Z = 390; remaining hatch shape estimated. |
| Floor plywood / total floor build-up | 11–12 / about 18 | 12 / 18, finished floor at Z = 0. |
| Floor rear edge and wheel-arch cutouts | Straight / cutouts present | Implemented; arch cutouts follow the approximate base footprints. |
| Ceiling plywood rear position / length | 240 / 1420 | Y = 240–1660; rear-opening datum interpretation remains provisional. |
| Ceiling underside above fitted floor, wall / centre | 1270 / 1290, derived from mattress clearances | 1269.994 / 1290. |
| Ceiling plywood thickness | 3 | 3, normal to its curved surface. |
| Open door edge from front pillar | 680 | 680 when fully open. |
| Open door inside / outside relative to outer pillar | 60 / 160, derived from 170/270 minus 110 | 60 / 160 at the lower straight body profile; door shape and thickness remain approximate. |

The rear corner also has a separate modelling error: its linear forward roof rake moves the rear section
23.2mm forward at Z = 390, while the opening at that height is still at Y = 0. Correct this connection when the
longitudinal layout is resolved rather than preserving the offset as a measurement.

The 1900mm `body_length_mm` is a catalogue-derived cargo/cab modelling boundary, **not** a measured rear-to-seat
clearance. The extra 1100mm cab floor, front floor width, seat widths/depths/heights, roof bow locations/depths,
roof side rails, headliner contours, and unmeasured fillet radii remain approximations. The hidden 1860mm floor
rectangle is a furniture-layout guide, not a vehicle-length measurement.
