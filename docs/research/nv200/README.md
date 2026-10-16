# Japanese 2017 NV200 body research

Research date: 2026-10-16. All dimensions are millimetres unless stated otherwise.

Follow-up: [likely curvature and reproducible pixel analysis](curvature.md) combines upper mounting dimensions,
bare-body photographs and two rear-opening traces into provisional profiles and explains integration with the arches.

## Gert's van

Owner-confirmed: Japanese 2017 Nissan NV200, right-hand drive, single upward-hinged rear door.
The ceiling was bare before insulation and 3mm plywood were fitted. Walls and doors had simple black plastic panels.
Interior width is approximately 1500; usable length to the cockpit seats is between 1860 and 2000.
Exact grade, insulation thickness, measurement endpoints and sliding-door arrangement remain unconfirmed.

The Japanese VM20 cargo van is the working reference. The trim description is consistent with a basic cargo interior;
it does not by itself establish a particular grade. Do not substitute North American long-body measurements.

## Dimensional evidence

These are catalogue measurements, not measurements of Gert's modified van. Applicability is recorded separately from
the precision printed in a brochure. None establishes the full interior surface.

| Quantity | Value | Source / applicability |
| --- | ---: | --- |
| Exterior length × width × height | 4400 × 1695 × 1855 | S1, DX 2WD; identity check |
| Wheelbase | 2725 | S1, Japanese short body |
| Cargo length × width | 1900 × 1500 | S1; consistent with owner's observations |
| Bare cargo height | 1365 | S1, DX two-seat, without optional ceiling trim |
| With optional ceiling trim | 1325 | S1 footnote 2; not Gert's custom lining |
| Loading height above ground | 520 | S1; do not use as the interior Z datum |
| Wheel-house clear separation | 1220 | S2; later Japanese corroboration |
| Rear opening width × vertical height | 1255 × 1230 | S2 diagram ② and ① |
| Rear opening inclined length | 1235 | S2 diagram ③, side view; not another width |
| Sliding opening width × height | 668 × 1169 | S2 diagram ⑤ and ④ |
| Floor length | 2040 | S2; distinct from cargo length to partition pipe |
| Hatch opening angle | 87° | S3; later Japanese hatch reference |
| Open hatch height above ground | 1927 | S3; not a hinge coordinate |
| Front / rear exterior overhang | 835 / 840 | S4, explicitly May 2009–January 2018 |

S1 is close to the vehicle year but is not an exact 2017 specification. S2 and S3 are later publications.
Original 2009 launch reporting repeats the Japanese aperture and hatch figures (S5), providing historical
corroboration; it is not a substitute for a dimensioned factory drawing.

### Sources

- **S1:** [Nissan Japan January 2019 specifications, PDF page 2][spec], including the ceiling-trim footnotes.
  [Local original](sources/nissan-japan-2019-specifications.pdf).
- **S2:** [Nissan Japan loadability][load], including its [door aperture diagram][doors]. The 1900 dimension is described
  as inside the back door to the partition pipe. The sloped 1235 arrow was checked visually.
- **S3:** [Nissan Shatai leaflet][shatai], page 1 diagrams; page 2 identifies the July 2021 update.
  [Local original](sources/nissan-shatai-2021.pdf). Its illustrated 1315 height and 1581 floor length concern other
  trim/seating configurations; do not use those as the bare two-seat cargo envelope.
- **S4:** [Nissan dimensional FAQ][faq], historical May 2009–January 2018 section.
- **S5:** [Car Watch's May 2009 launch report][launch], secondary historical corroboration only.
- [Nissan January 2016 change announcement][revision] describes equipment and seating changes, without describing a
  body redesign. Absence of a stated redesign is supporting evidence, not proof that every panel stayed identical.

[spec]: https://history.nissan.co.jp/ARCHIVES/PDF/NV200VANETTE/M20/20190117/nv200vanette_specsheet.pdf
[load]: https://www3.nissan.co.jp/vehicles/new/nv200vanette/interior/loadability.html
[doors]: https://www-asia.nissan-cdn.net/content/dam/Nissan/jp/vehicles/nv200vanette/2509/interior/loadability/nv200vanette_2509_interior_loadability_02.jpg.ximg.l_6_m.smart.jpg
[shatai]: https://www.nissan-shatai.co.jp/CAMPAIGN-PGM/pamph_NV200.pdf
[faq]: https://faq2.nissan.co.jp/faq/show/24908?site_domain=default
[launch]: https://car.watch.impress.co.jp/docs/news/169442.html
[revision]: https://global.nissannews.com/ja-JP/releases/160118-01-j

## What these sources do not establish

No verified metric wall/roof cross sections were found in the accessible material. We still need wall taper and bulge,
roof crown and rib intrusion, door-panel depth, opening positions, sill heights, hinge centres and sliding-track paths.
Wheel-house length, height, fore/aft position and crown shape also require actual-van measurements.

Do not derive internal ceiling height from external height minus loading height: 1855 − 520 = 1335, not 1365.
The published dimensions evidently use different endpoints or conditions; those differences are unresolved.
Likewise, 1235 inclined versus 1230 vertical does not establish a rear-door rake angle without matching endpoints.
Insulation and plywood do not necessarily follow the bare roof or its ribs at a constant offset.

Useful visual evidence, without transferable metric profiles:

- [Japanese DX roof-lining photographs](https://minkara.carview.co.jp/userid/876221/car/734397/2104657/note.aspx)
  show bare roof construction. Sheet-cutting sizes are not roof-section dimensions.
- [Japanese rear hatch trim removal](https://minkara.carview.co.jp/userid/2963540/car/2571881/5100939/note.aspx)
  shows the inner panel and reinforcement, without measured profiles.

Do not use the attractive [TRIMAT cross-section drawing][trimat] as a stock body section: it describes an insulated
refrigerated liner. European barn-door apertures and North American long-body manuals are also unsuitable substitutes.
The old Onshape sliding-opening values, 693 × 1171, must not be treated as Japanese measurements.

Two possible acquisition leads were found but not purchased or authenticated:

- [Japanese RHD 2009–2019 body-repair dimensions][repair]: public previews are too small to read reliably; the seller's
  claim of factory provenance was not verified.
- [Reverse-engineered NV200 CAD listing][scan]: seller claims a scan-based reconstruction, but market, body variant,
  dimensional accuracy and usable neutral CAD export are unverified.

[trimat]: https://www.trimat-kit.com/wp-content/uploads/2026/02/plan-carrossier-nissan-nv-200-ancien-modele-gb.pdf
[repair]: https://cargeometry.org/nissan/1398-nissan-nv200-vanette-2009-2019-rh-japanese-market-body-repair-manual.html
[scan]: https://www.cgtrader.com/3d-models/car/car/comprehensive-nissan-nv200-reverse-engineered-cad-model

## Adjustable reference model

The application uses the catalogue body height, cargo length and door-aperture dimensions, plus estimated smooth
wall/roof profiles. [CAD model conventions](../../cad-model.md) describes the geometry and assembly groups.
The 1860 furniture length is preserved; body length has its own control. Width remains shared at 1500.
The upper shoulder width starts at 1250, taper starts at Z = 750, and the roof crown rises 75. Only the shoulder-width
range has indirect dimensional support; the taper start and crown rise are modelling estimates. Door positions,
corner shapes and roof-bow dimensions also need measuring. These controls expose the uncertain dimensions directly.

Rear pillars, roof and floor share the same narrowing sections. Wheel houses retain their provisional Onshape
footprint and gain rounded transverse crown edges. The cabinet contours follow the estimated wall and finished
ceiling, with an adjustable fitting gap; those contours must be checked against the van before cutting plywood.

The paired sliding-door openings assume doors on both sides. No door leaf, hinge mechanism, sliding track, pressed
panel detail or cockpit geometry is represented. Three adjustable bow envelopes have roof-following tops and a
shallower underside curve. A solid 3mm plywood sheet follows their undersides, matching Gert's described installation.
Their positions, widths, depth and curvature are modelling estimates; see [roof-bow research](curvature.md#ceiling-cross-beams-roof-bows).

## Measurement-driven refinement

1. Keep furniture layout length independent of body length. `cargo_length_mm` drives the bed; `body_length_mm`
   controls the body. The shared width can be adjusted once actual endpoints are established.
2. Establish the actual rear threshold, floor plane and longitudinal centreline. Map these into the existing model's
   coordinates; retain the existing furniture placement until its offset is measured.
3. Describe the interior using a few transverse sections: rear aperture, wheel houses, sliding-door rear edge and
   cab boundary. Store explicit left/right profile points and roof heights. Add sections only where shape changes.
4. Build native build123d surfaces or solids for floor, wheel houses, side walls, roof, pillars and door openings.
   Keep door leaves and trim separate, with stable labels and existing group visibility. Do not invent material
   thickness for an envelope surface.
5. Add the rear hatch with an editable hinge axis and opening angle. Sliding doors need an outward-then-rearward path;
   aperture width alone does not determine that path. Mark any initial motion and profile approximations as such.
6. Represent the finished ceiling separately from bare metal. Use measured clear heights for furniture fit; the known
   plywood thickness is 3, but insulation/air-gap/rib offsets remain inputs.
7. Replace estimated inputs with measurements from the [measurement guide](measurements.md). Keep source, endpoints
   and confidence alongside the dimensions in this research record, without adding a provenance framework to the app.

Refine the adjustable envelope with actual transverse sections before adding door leaves and motion. A smooth
plausible shell is a useful preview but must not be described as a measured or fabrication-accurate body.
