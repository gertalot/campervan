# Japanese NV200 cab references

Research: 2026-10-17. Vehicle: Gert's Japanese 2017 right-hand-drive NV200. The cab and cargo floor share Z = 0,
confirmed by Gert. Gert confirms integrated front headrests; the exact grade is not confirmed. Dimensions below are millimetres.

## Seat generation and grade matter

The earlier model used contemporary Nissan photographs and arbitrary rectangular cushions. That is not a reliable
reconstruction of the 2017 seats. Nissan [dates the introduction of Zero Gravity front seats to December
2025][new-seat].
The 2607 interior photographs previously cited here show that later generation.

The [January 2019 Japanese equipment matrix][spec], PDF page 1, distinguishes highback seats in DX/VX from lowback
seats with adjustable headrests in GX and the passenger wagons. Clazzio's [vehicle fitment catalogue][fitment]
explicitly
covers February 2016–June 2021 DX/VX with integrated front headrests (EN-5204-02 / EN-5206-02); its GX listing has
separate headrests. Gert confirms integrated headrests, consistent with this DX/VX seat family. The exact grade remains unconfirmed.

The [Clazzio fitting manual][seat-manual], printed pages 9–10 (PDF pages 10–11), provides useful photographs of the
integrated-headrest driver and passenger seats. These show rounded shoulders, a narrowed integrated head support,
shaped cushion and backrest bolsters, and metal rails/supports beneath the upholstery. The passenger back has a folding
work-table shell. The cover changes surface details and the photographs are perspective views: use them for shape,
not direct millimetre scaling. [Saved manual](sources/clazzio-en-5204-02-seat-fitting.pdf).

## Manufacturer dimensions

The 2107 Japanese drawings predate the 2025 seat redesign. They are not individually authenticated 2017 drawings;
the period fitment catalogue provides supporting evidence for using the older seat family.

| Quantity | Published value | Reference and interpretation |
| --- | ---: | --- |
| Front seat width | 475 | [Japanese plan drawing][plan], both front seats |
| Front cushion depth | 455 | [Japanese side drawing][side], horizontal dimension at cushion |
| Inclined seat-to-roof dimension | 1025 | Same side drawing; not a vertical cushion-to-ceiling measurement |
| Driver slide travel | 190 | [Nissan Japan comfort page][comfort]; adjustment range, not seat location |
| Seated reference height above cab floor | 373 | [Driving-position diagram][posture]; exact seat/hip endpoint not defined |
| Hip point above ground, 2WD | 849 | [Older Japanese access diagram][hip]; not the top of the cushion |
| Clearance over illustrated 177cm occupant | 142 | Same diagram; not headrest-to-roof clearance |

The driving-position diagram also labels 667 on a diagonal toward the dashboard and 41° at the steering wheel.
Neither is a seat height or backrest angle. The current comfort page's forward/rearward recline figures describe
adjustment travel, not the normal driving posture.

Do not derive cushion height by subtracting the 520 cargo loading height from the 849 hip height. These are different
reference points and potentially different measurement conditions. The hip point is a seated-body reference, not an
unloaded upholstery surface. None of this overrides the owner's common floor level.

[Saved side drawing](sources/nissan-japan-2021-cab-side.jpg),
[plan drawing](sources/nissan-japan-2021-cab-plan.jpg),
[posture diagram](sources/nissan-japan-2021-driving-position.jpg),
[access diagram](sources/nissan-japan-2021-hip-height.jpg).

## Pixel estimates and their limits

Pixel coordinates below refer to the original 750 × 535 side drawing and 750 × 500 plan drawing, origin top-left.
They are manually selected landmarks. Keep the printed dimensions authoritative; a line drawing is not a CAD section.

| Calibration | Pixels | Scale, mm/pixel |
| --- | --- | ---: |
| Side: 1900 cargo length | x = 397 to 669 | 6.99 |
| Side: 2725 wheelbase | x = 156 to 560 | 6.75 |
| Side: 455 cushion depth | x = 290 to 354 | 7.11 |
| Side: 1365 cargo height | y = 101 to 317 | 6.32 |
| Side: 1855 exterior height | y = 101 to 394 | 6.33 |
| Plan: 1500 cargo width | y = 155 to 382 | 6.61 |
| Plan: 475 seat width | y = 176 to 247 | 6.69 |

The longitudinal scales disagree by about 5%, and differ from the vertical scale. The 1025 diagonal also fails a
cross-check: its approximate endpoints (307, 253) and (354, 116) recover only about 928 using the local seat-depth
and cargo-height scales. Do not stretch the whole image until one dimension fits and then claim precise geometry.

Useful provisional deductions, rounded to reflect these limitations:

| Quantity | Working range | Derivation / limitation |
| --- | ---: | --- |
| Seat centre spacing | 740–780 | Plan seat centres near y = 212 and 325; about 750 after width calibration |
| Former seat-offset estimate (rejected) | 250–350 | Used x = 354 cushion-depth line as pivot; contradicted by owner clearance |
| Cushion top at rear above shared floor | 280–340 | Side y ≈ 267 versus cargo floor y ≈ 317; about 316 |
| Cushion top at front above shared floor | 360–420 | Side y ≈ 255 versus floor y ≈ 317; about 392 |
| Cushion rise front-to-rear | 60–100 | About 76 from the drawing; roughly 8–12° over 455 depth |

These are drawing-based estimates, not statistical confidence intervals. The vertical seat estimates deliberately use
Gert's common floor datum rather than copy the apparent cab-footwell depression in the generic drawing. Line overlap,
stylised outlines and seat adjustment limit their accuracy. Backrest/headrest height cannot be recovered confidently
from this drawing: door, pillar and seat outlines overlap. Gert confirms the integrated-headrest variant; use its fitting photographs for the contour.

The North American [2013 Nissan body-builder guide][bbg], printed pages 45–46, was also inspected. Its seating diagram
labels a 21° torso angle, 13.5° cushion angle and 730 centre spacing, which provide only a rough plausibility check.
Its 240 slide travel differs from the Japanese 190. Its 403 and 464 dimensions use seating/vehicle reference points;
464 is not a cushion depth. Do not transplant its seat coordinates, floor steps or body length into this Japanese van.

## Cab headliner: shape evidence, not another guessed ramp

A Japanese owner documented [removing and refitting the front headliner on 8 April 2017][roof], shortly after taking
delivery. Images 2 and 8 were inspected and saved:

- [Bare roof](sources/owner-2017-cab-bare-roof.jpg): broad roof panel and windscreen header structure.
- [Refitted headliner](sources/owner-2017-cab-headliner.jpg): broad central surface, moulded visor recesses,
  edge returns and termination at the windscreen header. The centre lamp was modified by the owner; do not copy it as stock trim.

This supports a shallow moulded shell with local shaping at the edges/header, not a long sheet continuing down toward
the dashboard. The photograph has no useful metric scale and does not establish an exactly level centreline.
The exterior side drawing cannot establish the inner headliner offset either.

A credible simplified model should use separate sections at the rear edge, above the seats and at the windscreen
header, with most of the longitudinal change near the header. Keep the header Y position independent of the floor's
forward extent. Retain the confirmed flat floor. The cabinet ceiling remains governed by the measured/estimated cargo
lining; it does not establish the factory cab headliner's entire profile.

No verified Japanese numerical headliner cross-section, header height, cushion foam thickness or seat-base mounting
height was found. Those remain explicit estimates pending measurement. Do not describe their defaults as researched
factory dimensions.

## Implications for the model

`cab.py` uses the owner-confirmed integrated-headrest shape: one continuous highback with lumbar fullness, rounded
shoulders and a narrower upper section. The cushion has a rounded footprint and raised nose, with open side brackets
beneath it. These are simplified lofted upholstery envelopes, not a reconstruction of seat mechanisms.

| Model input | Default | Basis |
| --- | ---: | --- |
| Cushion width × depth | 475 × 455 | Published older Japanese drawing |
| Rear cushion top Z | 300 | Within the drawing-derived estimate |
| Front cushion rise | 80 | Drawing-derived estimate; front top Z = 380 |
| Seat centre spacing | 760 | Within the plan-derived range |
| Rear cushion/backrest offset | 160 | Owner fit: 1860 mattress, 85 rear-door gap, about 10 seat clearance |
| Backrest height to shoulders | 550 | Visual estimate |
| Integrated head-support height | 180 | Visual estimate; no separate posts or gap |
| Recline from vertical | 15° | Adjustable posture estimate |
| Upholstery thickness | 90 | Visual estimate, varying along the loft |

Gert confirms an 1860-long mattress with a 70–100 gap between its rear edge and the closed rear door, occupied by a
folded solar panel standing vertically. The mattress nearly touches the front seat backrests. The bed gap is an
independent parameter, initially 85: the mattress therefore spans Y = 85–1945, and the backrest envelope must reach
approximately Y = 1955 at mattress height (Z = 400–500). This supersedes the earlier clearance calibration that
incorrectly placed the mattress at the rear-door datum.

The default seat pivot is Y = 2060 (1900 cargo reference + 160 offset), with rear support feet at Y = 2128. These are
calibrated model coordinates, not factory measurements. The side drawing's 1900 ends at the cargo/partition reference,
not the seat pivot; its 455 cushion-dimension endpoint is not a verified pivot coordinate either. The sliding-door
front edge at Y = 1840 and the remaining wall strip to Y = 1900 are provisional references whose relationship to the
actual B-pillar needs measuring. Keep the catalogue body reference independent of the owner's mattress length and gap.

Seat positions remain independent of the bed: the 160 defaults are calibrated to the owner's reported fit, not an
automatic constraint that moves the vehicle seats when furniture dimensions change. Reclined upper backrests may
project over the mattress in plan view without intersecting it; use actual 3D clearance rather than whole-seat bounds.

The floor extension remains 1100. The headliner has a broad central surface with rounded side returns, matching the
cargo lining at its rear edge. Its default centreline is level; an optional front drop is concentrated near the header.
Its sections, width and forward extent remain estimates. Upholstery section proportions and simplified support
brackets also need visual comparison with the real van. Seat width is normalised after lofting so a smooth spline's
bulge does not silently enlarge the specified envelope.

## Small measurement set to resolve the remaining uncertainty

Use rear threshold Y = 0, shared floor Z = 0, and seats in normal driving positions.

1. Integrated headrests are confirmed. Photograph the seats from the side to refine their continuous outline.
2. Measure cushion top Z at the rear sitting area and at the front lip, on both seats; record unloaded surfaces.
3. Measure cushion rear-edge Y and the rearmost backrest Y at bed height. These directly constrain furniture clearance.
4. Measure total seat top Z and backrest rearward displacement; record any adjustable headrest extension separately.
5. Measure headliner centre/side Z at its rear edge, above the seats and at the windscreen header, with each section's
Y.
   Measure the cab floor's front endpoint separately. These values resolve height and curve without guessing from
photos.

[new-seat]: https://faq2.nissan.co.jp/faq/show/24888?category_id=63&site_domain=default
[spec]: https://history.nissan.co.jp/ARCHIVES/PDF/NV200VANETTE/M20/20190117/nv200vanette_specsheet.pdf
[fitment]: https://www.11i.co.jp/store/cars?maker_id=2&page=2&seattype_id=35
[seat-manual]: https://cdn.11i.co.jp/store/files/manual/seatcover/EN-5204-02.pdf
[side]: https://www-asia.nissan-cdn.net/content/dam/Nissan/jp/vehicles/nv200vannete/2107/specifications/top/nv200vannete_2107_specifications_cs1_01.jpg
[plan]: https://www-asia.nissan-cdn.net/content/dam/Nissan/jp/vehicles/nv200vannete/2107/specifications/top/nv200vannete_2107_specifications_cs1_05.jpg
[posture]: https://www-asia.nissan-cdn.net/content/dam/Nissan/jp/vehicles/nv200vannete/2107/interior/comfort/nv200vanette_2107_interior_comfort_cs2_02.jpg
[hip]: https://www-asia.nissan-cdn.net/content/dam/Nissan/jp/vehicles/nv200vannete/2107/interior/comfort/nv200vanette_2107_interior_comfort_cs2_01.jpg
[comfort]: https://www3.nissan.co.jp/vehicles/new/nv200vanette/interior/comfort.html
[roof]: https://minkara.carview.co.jp/userid/1959393/car/2356186/4189601/note.aspx
[bbg]: https://pvsheridan.com/2013-Nissan-NV200-Cargo-Van-BBG.pdf
