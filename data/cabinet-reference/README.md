# Cabinet before the box-based redesign

Saved on 23 November 2026 before removing the existing cabinet from the live assembly.
The checkpoint commit containing this reference preserves the complete original implementation.

| Datum | mm |
| --- | ---: |
| Overall length | 980 |
| Maximum body depth | 360 |
| Maximum height above finished floor, including ceiling filler | 1290.677 |
| Rear position in vehicle Y | 80 |
| Cab-end position in vehicle Y | 1060 |
| Finished floor in vehicle Z | 10 |
| Lower shelf top above finished floor | 510 |
| Module split above finished floor | 770 |
| Upper shelf top above finished floor | 1033.245 |
| Frame top above finished floor | 1256.490 |
| Nominal rear bay length | 550 |
| Nominal van clearance | 3 |

The bounding dimensions are not a rectangular replacement design. Preserve the fitted side, pillar,
wheel-arch and ceiling envelope. The body bounds exclude moving door assemblies; individual part bounds
include the closed doors and hardware. Module bounds include guide lips and hardware across the split.

`dimensions.json` records all resolved construction parameters, per-part bounds, backing profiles and
source hashes. `fitted-envelope.brep` preserves the fitted skins, shelves, doors and ceiling filler as
reference geometry. It is not included in the active model.

Both files use floor-relative construction coordinates before the assembly mirror and vehicle placement:

- Vehicle X = cargo width (1500mm) minus construction X.
- Vehicle Y = local Y + 80mm.
- Vehicle Z = local Z + 10mm.

The agreed replacement comprises two independently removable permanent carcasses: lower boxes 1–3 and
upper boxes 4–8 from Gert's sketch. New framing and box dimensions remain to be designed. The current
copied wall-frame draft is a reference checkpoint, not an approved construction design.
