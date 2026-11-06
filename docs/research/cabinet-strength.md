# Cabinet strength and weight assessment

Calculated 6 November 2026 from the running app's published model, revision 3.
This is a screening calculation for lighter construction. It is not a verified capacity assessment of the complete
cabinet: the selected non-structural plywood, fasteners, joints and vehicle attachment points lack rated design data.
No CAD dimensions or material selections were changed for this assessment.

## Current construction and assumptions

- 1000mm cabinet length; nominal wall-rail height 1258mm; curved aisle frame reaches approximately 1284mm.
- Aisle frame, rear upright and eight rear rails: 12mm plywood. Nominal frame member width: 60mm.
- Solid partitions and nine doors: 9mm plywood. Five shelves: 6mm plywood.
- Ledges and joint blocks: 18 × 18mm pine. Plastic flute-board lining has no assigned structural capacity.
- User specifies continuous glue and screws, with the cabinet frame attached to the fixed floor and ceiling wood.
  The user is considering 2–4 additional angle brackets directly connecting cabinet and van.
- Load assumption: 12kg on each of five shelves, or 60kg total contents. No extra bottom-compartment load is included.
- Empty cabinet allowance for inertia calculations: 20kg, including hardware, lining, adhesive and finishes.
- Calculation modulus E = 3000MPa, Poisson ratio 0.3, effective isotropic plate approximation; wood density 450kg/m³.
  These are assumptions for comparison, not measured or guaranteed Tigerply properties. Stiffness differs by direction.
- Static gravity is 9.81m/s². Forward restraint benchmark: 1g; sideways/rearward: 0.5g.
  A separate 3g downward load is an analyst-selected bump sensitivity case, not a specified vehicle requirement.
  A 20g forward case illustrates collision demand only; it is not a selected or verified crash criterion.
- The numerical floor/ceiling restraint cases below assume rigid attachment planes. The actual route through
  plywood and its vehicle fixings has not been established, so those cases are conditional rather than predictions.
  Contact with the roof is not a restraint.

The NZ truck-loading guidance supplies the restraint benchmarks, not a declaration that this cabinet complies with
vehicle modification or collision requirements. Contents impact after moving through a gap is not included.

## Wood mass and potential savings

Mass uses net CAD cutting-profile area, subtracting holes, multiplied by thickness and assumed density.
Timber uses rectangular cutting envelopes. Small edge roundovers are not deducted.

| Part group | Current estimated wood mass | Thickness alternative | Estimated saving |
|---|---:|---|---:|
| Aisle frame, rear upright and rails | 4.25kg | 12 → 9mm | 1.06kg |
| Solid partitions | 3.96kg | 9 → 6mm | 1.32kg |
| Nine doors | 3.81kg | 9 → 6mm | 1.27kg |
| Five shelves | 2.09kg | Already changed 12 → 6mm | 2.09kg already saved |
| Pine ledges, cleats and blocks | 1.24kg | No alternative calculated | — |
| **Current total wood** | **15.35kg** | | |

Masses scale directly with actual density. The 3mm hollow plastic lining is not assigned a solid-wood density.
Frame savings assume unchanged outlines; a complete rebuilt alternative would adjust some dependent dimensions.

## Shelf sag and bending

Each shelf carries 12kg distributed contents plus estimated shelf self-weight. Conservatively, the full load is
assigned to the clear panel inside the 18mm perimeter ledges. Rectangular approximations omit small corner notches.

The plate rigidity is D = Et³ / [12(1 − ν²)]. A Navier odd-harmonic double sum gives the simply supported result.
A 25-term Ritz calculation with basis (1 − u²)²u^(2i)(1 − v²)²v^(2j), i,j = 0…4, gives the rigid-edge result.
Both assume rigid supporting ledges. Real joint rotation and supporting-frame movement are additional unknowns.

| Shelf | Overall size | 6mm sag, rigid / rotating edges | 9mm sag, rigid / rotating edges |
|---|---|---:|---:|
| Rear middle | 551 × 338mm | 0.265 / 0.982mm | 0.080 / 0.297mm |
| Rear upper | 551 × 309mm | 0.203 / 0.790mm | 0.061 / 0.238mm |
| Cab-end lower | 422 × 351mm | 0.294 / 0.969mm | 0.089 / 0.292mm |
| Cab-end middle | 422 × 338mm | 0.274 / 0.912mm | 0.083 / 0.275mm |
| Cab-end upper | 422 × 309mm | 0.225 / 0.774mm | 0.068 / 0.232mm |

A one-way simply supported strip across the short clear dimension provides a conservative uniform-load bending
stress comparison: M = qb²/8 per unit width; σ = 6M/t². This gives 1.35–2.07MPa for 6mm and 0.61–0.93MPa for 9mm.
These are nominal demands, not stress concentrations or material capacity checks. Under the 3g case, multiply the
gravity stresses and immediate deflections by three. Doubling immediate sag is a separate illustrative creep allowance,
not a measured long-term prediction; changing the effective modulus from 3GPa to 1.5GPa also doubles sag.

## Rail bending and joints

Conservative local case: put an entire 12.5kg loaded shelf on one 447mm rear rail, with a 3g downward force of 368N.
The rail is simply supported, 60mm deep, with its force uniformly distributed. The glued pine ledge's additional
stiffness is ignored. I = t × 60³/12, deflection = 5FL³/(384EI), stress = 3FL/(4t × 60²).

| Rail thickness | Immediate deflection | Nominal bending stress |
|---|---:|---:|
| 12mm | 0.66mm | 2.85MPa |
| 9mm | 0.88mm | 3.81MPa |
| 6mm | 1.32mm | 5.71MPa |

For that deliberately concentrated load path, each rail end carries 184N. If two screws share an end load equally,
their demand is 92N each. On an 18 × 36mm block bond face, the average shear demand is 0.284MPa. Neither equal screw
sharing nor uniform glue stress is guaranteed. Eccentricity introduces peel and prying, and screw diameter, embedment,
edge distances and plywood face pull-through are unspecified. Glue and screw capacities must not simply be added.

The selected Aquadhere Exterior is a furniture PVA described by the manufacturer as non-structural. Its marketing
claim about wood failure does not supply an allowable joint stress or justify a numeric factor of safety.

## Longitudinal racking of the aisle frame

This is a conditional 2D Euler–Bernoulli frame calculation, not a whole-cabinet finite-element model.
It isolates the monolithic aisle frame and assigns all 80kg of longitudinal inertia to it, omitting assistance from
the rear rails and other panels. It assumes a restraint at every one of the three aisle-post ends at floor and ceiling.
Changing the number or location of attachments changes the result.

Post centrelines along the cabinet are 30, 564.5 and 970mm. Horizontal member centrelines are 30, 506, 760, 994.085
and 1228.17mm above the floor. Floor and ceiling restraint levels are 0 and 1258.17mm. All members have nominal
60mm width, with EA and EI from the stated modulus and thickness. Monolithic intersections have rigid joints.
Corner fillets, openings' local stress concentrations, shear deformation and joint/anchor slip are omitted.

Contents inertia is applied at the corresponding shelf-rail nodes: 12kg at the lower level, 24kg at the middle,
24kg at the upper. Empty-cabinet inertia is distributed equally across the five horizontal-member levels.

| Frame thickness | Maximum sway at 1g, pinned attachment rotations | Sway with fixed attachment rotations | Nominal peak stress |
|---|---:|---:|---:|
| 12mm | 1.48mm | 1.16mm | 3.85MPa |
| 9mm | 1.97mm | 1.55mm | 5.14MPa |
| 6mm | 2.95mm | 2.33mm | 7.70MPa |

Both attachment cases prevent translation at floor and ceiling. "Pinned" permits rotation; "fixed" prevents it.
These are two ideal attachment conditions, not bounds guaranteed to enclose the real cabinet response.
Modulus uncertainty scales deflection inversely; nominal linear-elastic stress demand is unchanged by a uniform E change.
No available plywood allowable stress establishes a pass/fail margin. Door gaps must be compared with actual relative
opening distortion, not just maximum frame displacement.

## Transverse partition response

An illustrative load path uses two intact 300mm-wide partitions spanning 1258mm between floor and ceiling restraints,
each sharing a 0.5g lateral load equally. Total force is 392N at 800mm height. Ends prevent lateral displacement but
permit rotation. Bending deflection at the load is Fa²(H − a)²/(3EI H), using the combined I of both panels.
Add the simple shear estimate Fa(H − a)/(HGA), G = E/[2(1 + ν)].

| Partition thickness | Deflection at load height | Nominal peak bending stress |
|---|---:|---:|
| 9mm | 0.133mm | 0.423MPa |
| 6mm | 0.200mm | 0.635MPa |

These figures assume intact constant-width panels and direct effective top/bottom restraint. The real wheel-arch
notches and indirect connections invalidate treating them as verified whole-partition results. They indicate low
nominal in-plane panel demand; they do not establish joint strength or notch strength.

## Buckling sensitivity

Euler Pcr = π²EI/L² illustrates weak-axis instability of an isolated 60mm-wide frame post, with pinned ends.
This intentionally omits restraint from the bonded shelves and partitions; it is not the cabinet's buckling capacity.

| Frame thickness | Pcr with 500mm unbraced length | Pcr with 750mm unbraced length |
|---|---:|---:|
| 12mm | 1023N | 455N |
| 9mm | 432N | 192N |
| 6mm | 128N | 57N |

For a 300mm-wide intact partition treated as an isolated pinned column with 730mm unbraced height, the corresponding
values are 1013N at 9mm and 300N at 6mm. Actual edge restraint, imperfections and wheel-arch notches change the mode.
Effective bracing length and compressive force sharing are required before a genuine buckling margin can be calculated.
Reducing thickness 9 → 6mm retains only 30% of this weak-axis stiffness, even where in-plane stresses look small.

## Floor and ceiling mounting demands and overturning

Use a separate transparent two-level restraint model: 80kg total mass, centre of gravity at an assumed 800mm height,
floor and ceiling lateral restraints 1258mm apart, no reliance on friction or base-width restoring moment.
F = ma; overturning moment M = Fh; ceiling reaction = M/H; floor reaction = F − M/H.
The centre of gravity is an assumed screening value, not a measured CAD mass centroid.

| Load case | Total force | Overturning moment | Ceiling reaction | Floor reaction |
|---|---:|---:|---:|---:|
| 1g forward | 785N | 628N·m | 499N | 286N |
| 0.5g sideways/rearward | 392N | 314N·m | 250N | 143N |
| Illustrative 20g forward | 15.70kN | 12.56kN·m | 9.98kN | 5.72kN |

The 3g downward support demand is 2.35kN if carried entirely by the floor. Vertical load sharing with the ceiling
depends on connection stiffness and cannot be inferred from "attached at both ends".

The more detailed aisle-frame idealization above produces about 570N total longitudinal ceiling reaction at 1g,
because distributed loads and vertical reaction couples alter the load split. Use the load-path-appropriate result;
the two models are not interchangeable. Per-fastener reactions, roof-rib bending, floor pull-through and anchor
tension require attachment coordinates, fastener details and the supporting vehicle-member geometry.

Ceiling restraint substantially reduces overturning demand on floor fixings, provided that the complete roof load
path can carry the ceiling reaction. No roof or floor capacity has been established here.

## Door retention and hinges

Conservatively assign one shelf's 12kg contents plus a 0.5kg door to outward loading: 61N at 0.5g or 123N at 1g.
For a resultant at half the hinge-to-catch distance, the catch carries half: approximately 31N or 61N.
If the load acts close to the catch, demand approaches the full 61N or 123N. These are static demands only.
The Taskmaster catch has no verified holding-force rating, so its margin cannot be calculated.

For a 230mm-high drop-down leaf, a 0.5kg door alone creates approximately 0.56N·m about its horizontal
hinge when open. Two symmetric chains would each require F = 0.56/(2r sin θ), where r is door attachment distance
from hinge and θ is the chain's angle to the leaf. Neither anchor position nor angle is specified. Leaning on the
open door, placing items on it, fastener pull-through and impact require separate cases.

## Clarification of plywood attachments and additional brackets

The cabinet is to be attached to the floor and ceiling wood, which is itself fixed. The load path is therefore
cabinet → cabinet-to-plywood joint → plywood → plywood-to-vehicle fixings → vehicle structure. Being fixed does
not quantify plywood bending, fastener slip or capacity. The previous rigid-restraint frame results remain useful
reference cases but cannot be assigned to this arrangement without those details.
The current project specifies 12mm floor plywood and 3mm ceiling plywood. The 3mm ceiling is treated as lining,
with no assigned structural restraint capacity until the connection to backing or vehicle members is defined.

For an illustrative direct bracket arrangement, place one bracket near floor level and one near ceiling level,
or two at each level for four brackets total. Use the same 1258mm vertical spacing, 80kg mass and 800mm centre
of gravity as the simple restraint calculation. Allocate all horizontal restraint to the direct brackets, taking
no capacity credit for the plywood route. The two supports must be capable of resisting the load direction in question.

| Direct brackets | 1g forward demand per upper bracket | Demand per lower bracket |
|---|---:|---:|
| Two: one upper, one lower | 499N | 286N |
| Four: two upper, two lower | 250N | 143N |

At 0.5g lateral acceleration, halve those forces. These are ideal equal-sharing force demands, before connection
eccentricity, prying, unequal stiffness or impact; they are not required product ratings or demonstrated capacities.
Mounting height and spacing along the cabinet matter as well as bracket count. Brackets clustered at the bottom
cannot use this table. Four spread along the cabinet and between upper/lower levels provide more attachment
locations, but their capacity is not established simply by having four.

Bracket suitability needs the bracket geometry and load direction, cabinet-side fastening and backing, vehicle-side
fastening, and the strength of the engaged vehicle member. Timber-connector load tables apply only to their specified
substrates and fixing arrangements and cannot be transferred directly to thin plywood and van sheet metal.

## Assessment and remaining inputs

The 6mm shelves remain a reasonable candidate under the stated pantry loads and continuous perimeter support.
Effective floor and ceiling restraint makes a 12 → 9mm frame comparison worth pursuing: about 1.06kg saved, with modelled
longitudinal sway increasing by roughly 0.4–0.5mm at 1g. This is a candidate, not approval to change it.
Doors offer a separate approximately 1.27kg saving at 9 → 6mm, conditional on hinge/catch fixings and satisfactory
flatness and handling stiffness. Reducing partitions saves approximately 1.32kg, but bracing and notch details
need resolving before using low nominal bending stress as justification.

No verified overall factor of safety can be reported. Every checked capacity needs a matching load case, material
design value and joint/anchor capacity. Required inputs are:

1. Plywood-to-vehicle and cabinet-to-plywood fixing locations/details, plus proposed direct bracket locations,
   bolts/screws/backing and vehicle members engaged.
2. Plywood lay-up/directional properties or acceptance of the stated comparison assumptions.
3. Screw types, embedment, spacing and joint arrangement; chain anchors and catch holding data.
4. Confirmation of 60kg total contents, any bottom-compartment load, and the desired collision-restraint case.

## Sources

- [NZTA truck-loading basic criteria](https://www.nzta.govt.nz/driving-skills/learn-to-drive/roadcode/heavy-vehicle-road-code/the-truck-loading-code/general-requirements/basic-criteria-and-precaution)
- [University of Auckland plate theory, including energy methods and buckling](https://pkel015.connect.amazon.auckland.ac.nz/SolidMechanicsBooks/Part_II/06_PlateTheory/06_PlateTheory_Complete.pdf)
- [Comparable poplar plywood properties, showing directional variation](https://www.iwoodenterprises.com/products/panels/poplar-plywood/)
- [Selleys Aquadhere Exterior limitations and application](https://www.selleys.co.nz/products/glues-adhesives/wood-glue/aquadhere-exterior/)
- [APA guidance on panel-edge fastening](https://help.apawood.org/portal/en/kb/articles/nailing-into-panel-edge)
- [American Wood Council creep guidance](https://awc.org/faq/what-is-creep-and-how-can-i-address-it/)
- [Simpson Strong-Tie angle connector capacity and specified timber/fixing assumptions](https://strongtie.co.nz/products/a34-a35-reinforced-angle-bracket)

## Approved construction change

Following this assessment, Gert approved 9mm aisle frame, rear upright and rails; 6mm doors; retained 9mm
partitions, 6mm shelves and 18 × 18mm pine supports. Frame parts and partitions share the 9mm Tigerply Okoume
product; doors and shelves share its 6mm product. The mass and force tables above retain the pre-change
assessment geometry and assumptions. Estimated additional wood saving is 2.33kg before dependent geometry changes.
