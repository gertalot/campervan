# Cut list and layout research

Research date: 2026-10-26. The user approved both methods, selectable in the app.

## Implementation

The Cut list tab uses PackingSolver 0.1.1229 for straight-cut blanks and actual-shape nesting. Its default overview
draws all cutting pieces under their CAD assembly names, including the floor plywood. Thickness filters lead to
the relevant pieces, named sheet drawings and detailed cut list. Equal timber cuts share a drawing and quantity;
their individual CAD names remain available in the piece detail dialog. A global settings disclosure holds algorithm,
kerf, edge trim and default grain. Stock sizes and per-part direction stay material-specific. Only one algorithm's
results appear at a time. Settings and results persist with the project and JSON backups.

Flat CAD sections provide outlines and through-holes; the union of sections near both faces and mid-thickness
keeps blind pockets out of the nesting holes. Curves use a 0.1mm chord tolerance and nesting reserves another
0.2mm between profiles. The curved backing remains a developed blank and requires a wheel-arch template.
The saw adapter retains the native three-stage cutting tree and uses integer hundredths of a millimetre.
Timber uses the same guillotine engine as fixed-width lengths, with end trims and crosscut kerf.

Straight-cut sheets with one stock size use PackingSolver's `bin-packing-with-leftovers` objective, which searches
for fewer sheets and a larger rectangular remainder. The coordinator ranks published candidates by stock use,
then the best rectangular remnant's area/perimeter ratio, then the number of blank-separating saw cuts. Only
separated rectangular remnants count; material inside profile openings is not included. A higher area/perimeter
ratio favours larger, less slender rectangles. The drawing marks the best rectangle and gives its dimensions.

This is candidate ranking, not an exact solver for all three priorities: the native search objective does not
directly optimise area/perimeter or cut count, and its callback only publishes improvements to its own objective.
It can miss a candidate with a better ratio or fewer cuts. Its leftovers objective also does not report a complete
optimality proof. Sheet count is marked proven when it matches the greater of the blank-area lower bound and the
solver's bin-packing bound. That claim does not extend to offcut quality or cut count. Staggered blanks can still
have a valid guillotine sequence; curved profiles, notches and internal openings are cut after separating blanks.
Aligning equal-sized parts may simplify the sequence, but it is not a feasibility requirement.

Nesting and timber with one stock size retain the bin-packing objective. Multiple stock entries minimise full stock
pieces, treating owned offcuts as low-cost stock; these do not use the native leftovers objective. Each worker runs
for at most 20 seconds of wall-clock time per start/resume, including the CPU-sharing intervals. The parent suspends
the process with SIGSTOP at the deadline, retaining the native search state. Arrange sheets resumes the same process
for another 20 seconds; Stop optimisation pauses it early. Native solver timers remain unlimited because they count
time spent suspended too. The coordinator owns/cancels the tasks, saves improving candidates and keeps better saved
candidates when a new search starts. Paused searches consume no CPU, but retain process memory until invalidated or
the backend shuts down. Only the best layout survives a backend restart, not the native search state.
The existing model-status poll also refreshes active cutting results. API requests return immediately; leaving the
tab does not end the current 20-second run. Returning to the tab does not automatically resume a paused search.
Global setting changes, stock edits, changed CAD dimensions and application shutdown discard affected workers.

Objective references: [PackingSolver guillotine documentation](https://fontanf.github.io/packingsolver/rectangleguillotine.html)
and the [native solution comparator](https://github.com/fontanf/packingsolver/blob/master/src/rectangleguillotine/solution.cpp).

Observed on the current 9mm parts with 3mm kerf, no trim and free rotation: the previous one-sheet layout's best
rectangular remnant was 1260 × 737.92mm. The leftovers search found a one-sheet layout with a 1281 × 1200mm remnant,
placing all ten pieces. The current 12mm candidate still places all 23 pieces on two sheets and aligns both
376 × 290mm drawer end panels in one row. These are observed candidates, not proofs of best offcuts or fewest cuts.

CPU use: solver processes use Unix niceness +10 and a shared 200ms cycle: 100ms runnable, 100ms suspended with
SIGSTOP/SIGCONT. Suspending the process covers native solver threads too. Wall-clock alignment keeps simultaneous
material searches in the same runnable window, targeting 50% of unrestricted sustained CPU use across searches.
This is a duty cycle, not a thread-count or single-core percentage limit; short CPU spikes remain possible.
The search state survives suspension, and cancellation kills the worker even while suspended. The coordinator
owns the throttle task alongside stdout streaming so a throttle failure ends and cleans up that search.
Priority alone would still allow continuous CPU saturation when other applications are idle. The installed binding
does not expose a thread-count control. No additional process-management dependency or user setting is needed.

Observed UX problems in the first implementation: a material selector hid most pieces; generated IDs did not identify
parts; configuration and statistics occupied the initial viewport; sheet headings omitted material/thickness; an
unexplained 5mm trim inset the pieces. The revised overview uses CAD names and visible thickness filters. Global
settings use progressive disclosure. New settings default to zero trim, and diagrams label and hatch nonzero trim.

The UI decisions follow [recognition over recall](https://www.nngroup.com/articles/recognition-and-recall/) and
[progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/), with OpenCutList's material,
part-identification and allowance conventions. These sources inform the design; Gert's visual use provides acceptance.

The 20-second pause/resume change follows [W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html):
the existing layout status identifies a paused search without taking focus, with a polite status role. A visible note
explains the 20-second limit and the existing Arrange sheets action's continuation behaviour; no search-time setting
or extra action is added. This guidance informs the change; screen-reader behaviour has not been verified.

## Plywood purchase and design audit, 26 October 2026

**Implemented drawer revision:** 1200mm sides, with two 12mm full-width end caps, give an overall length of 1224mm.
Both end caps are 376 × 290mm; the bottom is 1200 × 352mm. Internal length decreases from 1226 to 1200mm. The selected
1200mm locking drawer sliders align with the sides at Y=12–1212; their levers project rearward. The bench frames,
tie strip, guide ledges, rear cross-beam and slats retain their positions and dimensions. The checked capped-drawer
layout accounts for all 23 pieces on two 2400 × 1200mm sheets with 3mm kerf and rotation allowed. It supersedes the
earlier 1200mm-overall-body alternative in this historical audit.
After regeneration, the running app's native straight-cut and shape-nesting solvers both returned two sheets,
zero unplaced pieces and `is_proven_optimal() = true` for the current 12mm geometry. Both searches completed.

**Subsequent implemented decision:** remove the long-bench cab-end skin and use 9mm plywood for the cross-bench
rear skin, sharing its sheet with the cabinet doors. The 4mm skin purchase is eliminated. Keep all slat positions
and the long-bench frames/guide ledges unchanged; shorten the cross-bench support frames from 576 to 571mm behind
the thicker rear skin. The audit drawings below record the earlier snapshot and alternative layouts; their two-skin
consolidation illustration is superseded by this one-skin decision.

Gert requires locking drawer runners, the existing slat dimensions and positions, and **no special-order purchases**.
Exclude special-order products from viable purchasing options. Ordinary listings still need local stock confirmation.
Rotation through 90 degrees
on the stock sheet is allowed. A 1200mm part can use the sheet's full 1200mm width; subtracting kerf from that
dimension is unnecessary when both stock edges form the finished ends. Kerf remains necessary between parts.

The audit used the running app's current `/api/v1/cutting` and `/api/v1/materials` responses. The published CAD
dimensions were current. The global cutting settings were 3mm kerf, zero edge trim and free orientation. No CAD,
material selection, saved layout or background search was changed during the audit.

### Concrete layouts

[Open all layout drawings](plywood-layout-audit/index.html). Each drawing includes names, dimensions and placement
coordinates. [Placement data and source profiles](plywood-layout-audit/placements.json) retain the inspected snapshot.
The drawings show complete rectangular blanks around the current CAD profiles. They do not depend on salvaging
material from frame openings. Proposed shorter drawer sides appear as rectangular blanks; their finished profiles
have not been regenerated.

| Alternative | 18mm stock | 12mm furniture stock | Drawer/body changes | Status |
| --- | --- | --- | --- | --- |
| Existing dimensions, rectangular cutting | 1 × 2400 × 1200 | 3 × 2400 × 1200 | None | One 18mm sheet demonstrated; two 12mm sheets impossible for unchanged rectangular blanks |
| 1200mm drawer body, existing bench | 1 × 2400 × 1200 | 2 × 2400 × 1200 | Drawer sides 1250 → 1200; bottom 1226 → 1176 | Complete placement for all 11 bench and 23 cabinet/drawer blanks |
| Existing drawer, mixed sheet sizes | 1 × 2400 × 1200 | 1 × 2700 × 1200 + 1 × 2400 × 1200 | None | Rejected: the researched 2700mm product is special order |
| Shorter 1100mm locking runners | 1 × 2400 × 1200 | 2 × 2400 × 1200 | Further drawer depth/travel reduction | Does not remove another sheet; hardware cost comparison below |

**The bench can stay unchanged.** The 18mm drawing accommodates the existing wall frame (1160 × 372), fixed aisle
frame (1280 × 372), internal support (1258 × 372), moving frame (1280 × 372), cab-end frame (432 × 372), both
cross-bench frames (576 × 372), header, tie strip and both guide ledges. Rip six strips of widths 372, 1280, 576,
40, 60 and 42mm. Five 3mm kerfs give a total of 2385mm. Crosscut the pieces inside their strips. The two 560mm guide
ledges share the 42mm strip, with one 3mm kerf between them. This is a straight-cut arrangement and also accommodates
5mm perimeter trim if the entire placement shifts 5mm inward: its maximum X becomes 2390 and maximum Y becomes 1165.

The old saved straight-cut result used fixed lengthwise grain and 5mm edge trim. It is stale relative to the current
free-rotation settings. Its two-sheet count should not have been used as evidence that shortening the frames was
necessary. The current saved nesting result already uses one 18mm sheet.

**Unchanged 12mm rectangular blanks need at least three selected-size sheets.** The cabinet aisle-frame blank is
1284.39 × 1000. It cannot share a 2400 × 1200 sheet with any of the five long blanks (drawer bottom, both drawer sides,
middle partition, cab-end partition): each is longer than 1200mm, each is at least 290mm wide, each combined length
with the frame exceeds 2400mm, and each combined width exceeds 1200mm. Neither can rotate its long dimension across
the sheet. Therefore all five would have to occupy the second sheet. Every horizontal blank longer than 1200mm
crosses that sheet's X=1200 line, but their widths total 352 + 290 + 290 + 363 + 363 = 1658mm, exceeding the available
1200mm even before kerf. This rules out two sheets of complete rectangular blanks at their existing sizes. It does
not rule out a two-sheet actual-shape nest.

For the 1200mm drawer option, sheet 1 carries the aisle frame, rear upright, both rotated drawer sides, rear upper
panel and both drawer ends. Sheet 2 carries both tall partitions, the shorter drawer bottom, all five shelves and
all eight wall rails. The 23 blanks occupy 4.863m², so one sheet is impossible and the two-sheet rectangular layout
reaches the minimum count for these dimensions. The full-width drawer sides require an actual usable sheet width
of 1200mm and zero trim at those ends.

The mixed-stock drawings record a rejected purchasing option: the researched larger sheet is special order.
They retain all 23 current 12mm pieces. The larger sheet takes the aisle frame and rear upright
on the left, with both 1250mm drawer sides and the 1226mm drawer bottom on the right. The 2400mm sheet takes the
remaining 18 pieces. No furniture joints or dimensions change for this stock option.

### Connections and moving clearances

The earlier centred shorter-frame proposal is withdrawn. Keeping the existing 18mm pieces preserves these
relationships rather than introducing joints or reduced end bearings:

| Relationship | Current construction retained |
| --- | --- |
| Rearmost fixed slat and rear cross-beam | Existing rear posts and header stay at Y=0; the internal post retains its full height |
| Frontmost fixed slat and cab-end bracing | Cab-end frame/skin and ends of the fixed supports stay in their current positions |
| Bed guide ledges | Rear ledge stays at Y=120–138; cab-end ledge stays at Y=1240–1258 |
| Tie strip and extension stop | Existing Y=122–1256 span and lateral travel remain unchanged |
| Moving slats, moving frame and angle brackets | Same seven slats, frame, three bracket positions and fixed-frame reliefs throughout conversion |
| Wheel arch and rounded rear corner | Wall frame and internal support keep their current outlines and transverse positions |
| Cross-bench slats and cushions | Bench length datum remains 1280mm; the cross bench still starts there |
| Drawer runner side clearances | Current 376mm tray width and two 19mm mounting gaps stay unchanged |
| Runner height | Rail envelope remains Z=22–75, inside both lower mounting bands |
| Drawer top and rear header | Drawer top stays Z=300; header underside stays Z=312, leaving 12mm |
| Closed drawer and cab-end frame | A 1200mm body leaves 58mm to the current frame's inner face at Y=1258 |

The model currently adds a 50mm runner setback to the tray length and represents the runner bodies at Y=50–1250.
That rule should not determine the plywood length. For a proposed 1200mm tray, place the 1200mm rail bodies at
Y=0–1200 and reserve the lever's free operating space toward negative Y. The fixed mounting bands already cover
that full body length. Model the lever separately and preserve the rear cross-beam above it.

Instant Panel specifies a 45mm locking lever and 50mm operating clearance. With the bench 100mm forward of the rear
opening datum, the proposed clearance envelope would extend back to vehicle Y=50; the lever tip would reach Y=55.
That leaves nominal room relative to the rear-opening datum. Actual hatch trim/handle protrusions, lever sweep
and finger access are not dimensioned in the model or supplier guide. Those remain manufacturing measurements;
the datum gap does not establish their exact clearances against the closed hatch. The body and lever lengths also
need confirming on the selected hardware drawing or delivered pair.

The locking runner product must replace the current non-locking catalogue selection before manufacture. No
non-locking hardware meets Gert's requirement. The audit does not silently change the saved product selection.

### Other ways to reduce purchases

| Family investigated | Finding |
| --- | --- |
| Rotate existing bench pieces | Demonstrated one-sheet rectangular layout; no structural redesign needed |
| Shorten/centre bench frames | No additional 18mm sheet can be removed once the count is one; introduces guide/header/joint problems |
| Separate posts, rails or splice long panels | Can reduce individual blank dimensions, but adds connections without improving the demonstrated one-sheet bench count |
| Harvest frame openings | Current nesting already does this in principle; optional for the displayed rectangular layouts, which keep openings as spare stock |
| Shorten drawer body by removing the plywood allowance | Demonstrated two-sheet 12mm furniture layout while retaining 1200mm runner bodies and bench structure |
| Use 1100mm locking runners | Saves $15 against 1200mm locking runners; no further sheet-count benefit in the demonstrated layout |
| Use larger stock | Rejected for the researched 2700mm product: special order |
| Join cabinet partitions at shelf heights / assemble aisle frame from rails and posts | Could make shorter blanks while preserving the cabinet envelope, but adds joints and door/hinge/ledge attachment details. The mixed-stock layout provides a no-joint two-sheet alternative |
| Consolidate 4mm skins into the 9mm door sheet | All nine doors and both skin blanks fit on one sheet; replaces the currently selected special-order 4mm product. Requires thicker-skin joint changes and local stock confirmation for the 9mm product |
| Consolidate 9mm doors into the 12mm sheets | With the 1200mm drawer, the rectangular blank area totals 5.811m², exceeding two sheets' 5.760m². Would require shape reuse or more changes; door thickness also affects hinges, latches and swings |
| Change 18mm structural frames to thinner ply | Would change strength and attachments. The existing 18mm parts already fit one sheet; no thickness reduction is needed for that result |
| Use purchased offcuts/smaller panels | The two 4mm skins fit inside a 1155 × 372mm rectangle, including their separating kerf. A usable offcut of that size avoids buying the full 4mm sheet; local price/stock not established |
| Reuse the existing floor | Avoids a floor purchase if retained. The saved floor has no selected product or ownership decision, so furniture savings must not silently include it |

The floor cut in CAD is a single 1900 × 1500mm contour. It cannot be cut intact from the selected stock sizes.
If replaced, it needs a panel division and support/fastening detail. Treat it as the existing floor reference until
that decision is made; the furniture layouts do not include its area. Ceiling lining is 3mm in the CAD parameters
but is not part of the furniture cutting list, so the counts here also exclude a new ceiling purchase.

The current catalogue explicitly marks the selected 4mm Tigerply skin product as special order at Lyall Bay, so it
also needs replacing. Do not treat it as an acceptable purchase. The 9mm product has no Special Order label in the
catalogue, but local availability remains unconfirmed. A stocked 4mm offcut is another possible replacement.

The optional 9mm skin layout includes the existing 432 × 372 and 720 × 372 outlines. Increasing them from 4 to 9mm
requires 5mm of additional space. To retain the current outer planes, the long-bench cab-end frame would move 5mm
rearward, its internal support would shorten by 5mm at the cab end, and the adjacent guide attachment would need
adjustment. Cross-bench frames would start 5mm farther forward behind its thicker rear skin. Keep the existing
slat and wall-frame datums independent of these end-skin thicknesses: globally changing `wall_thickness_mm` would
also alter the reused slat lengths. The drawing proves stock fit only; these joint changes have not been modelled.

### Costs, including GST

| Item | Price | Source |
| --- | --- | --- |
| Current 2400 × 1200 × 18mm Tigerply | $89.90 | Project catalogue / [Bunnings](https://www.bunnings.co.nz/tigerply-2400-x-1200-x-18mm-non-structural-untreated-plywood-18mm_p0170556) |
| Current 2400 × 1200 × 12mm Tigerply | $57.50 | Project catalogue / [Bunnings](https://www.bunnings.co.nz/tigerply-2400-x-1200-x-12mm-non-structural-untreated-plywood-12mm_p0170555) |
| Rejected: 2700 × 1200 × 12mm Okoume | $110.00, special order | [Bunnings](https://www.bunnings.co.nz/tigerply-2700-x-1200-x-12mm-okoume-plywood_p0345107) |
| 1200mm locking runner pair | $194.99 | [Instant Panel, SKU 10632](https://instantpanel.co.nz/product/drawer-slides-1200mm-x-53mm-with-lock-heavy-duty-runners.html) |
| 1100mm locking runner pair | $179.99 | [Instant Panel, SKU 108205](https://instantpanel.co.nz/product/drawer-slides-1100mm-x-53mm-with-lock-heavy-duty-runners.html) |
| Rejected current selection: 2400 × 1200 × 4mm skin plywood | $47.57, special order | Project catalogue; replacement needed |

With the 1200mm drawer, two selected 12mm sheets cost $115 instead of $172.50 for three: a $57.50 saving. One
2700mm and one 2400mm sheet cost $167.50, saving $5 while preserving the current drawer dimensions. Compare freight
and collection separately. Switching from the incorrectly selected $179.99 non-locking pair to the required
$194.99 locking pair adds $15. Accordingly, the 1200mm-drawer option saves $42.50 against the current saved
three-sheet/non-locking furniture selection. If locking runners form the baseline, its saving is $57.50.

The one-sheet bench layout saves $89.90 against the stale two-sheet straight-cut result. It adds no further saving
against the current one-sheet nesting result. If the thicker-skin alternative is later completed, removing the
separate 4mm sheet saves another $47.57 before additional fixing/finishing costs. These are distinct comparisons.

### Evidence and limits

The audit accounts for every current cutting-list furniture plywood piece: 11 at 18mm, 23 at 12mm, nine doors at
9mm and two skins at 4mm. The flute-board lining and reused timber slats remain separate materials. Each displayed
alternative has an explicit inventory and coordinates. Direct calculations checked that each full blank stays
inside its sheet, no blank overlaps another and at least 3mm separates every pair. The two 12mm alternatives each
contain all 23 distinct paths exactly once. The main three sheet drawings were rasterised and visually inspected.
No software tests or CAD regeneration were run.

A focused, CPU-throttled PackingSolver search attempted to put the five unchanged long 12mm pieces together on
one sheet. It produced no feasible candidate within the 90-second investigation allocation. This does not prove
that a two-sheet actual-shape arrangement is impossible. The rectangular lower bound above is independent of that
search. Further actual-shape nesting and all possible construction redesigns have not been exhaustively enumerated.

Primary hardware sources: [1200mm locking runner specification](https://instantpanel.co.nz/product/drawer-slides-1200mm-x-53mm-with-lock-heavy-duty-runners.html)
and [manufacturer installation guide](https://instantpanel.co.nz/productfiles/drawer_slides/Drawer_slides_2053_Installation_Precautions_and_Instructions.pdf).
Repository sources: `cad/bench.py`, `cad/sliding_bed.py`, `cad/drawer.py`, `cad/cross_bench.py`, `cad/cabinet.py`,
`cad/body.py`, `cad/bom.py`, `materials.py`, `materials.json`, `parameters.py`, original drawer constraints in
`docs/fs/nv200-interior.fs`, and construction history in `docs/what-we-built-in-onshape.md`.

The remaining sections record the original research and proposal, before the overview and global-settings revision.

## Recommendation

For sheets cut with a circular saw, track saw or panel saw, use guillotine cutting-stock optimisation. Each cut
crosses the current sheet or offcut. Keep the cutting tree so the app can show an executable sequence.
Use the existing Python backend and a flat SVG drawing in a new **Cut list** tab.

PackingSolver's `rectangleguillotine` module is the strongest candidate found. Its documented inputs include blade
kerf, edge trims, different sheet sizes, stock quantities and per-part rotation restrictions. Its output includes
the cutting tree. Its `BinPackingWithLeftovers` objective combines sheet count with a useful remaining offcut.
This recommendation assumes hand cutting; CNC work would make shape nesting a relevant alternative.

The current PyPI release provides macOS ARM64 and Intel wheels with the CPython 3.12 stable ABI and declares
Python >=3.12. That covers the project's Python 3.13 version at the package-metadata level. The ARM64 wheel is
about 4.4 MB. Version 0.1.1229 was installed through uv in the project's Python 3.13 environment.

## Alternatives considered

| Approach | Fit for this project |
| --- | --- |
| Guillotine cutting stock | Produces rectangular blanks and a sequence of through cuts suitable for saw work. Recommended for hand cutting. |
| MaxRects / free rectangle packing | Useful when unrestricted rectangle placement matters. A resulting arrangement needs a separate check for a feasible through-cut sequence. |
| Irregular shape nesting | Uses actual profiles and can exploit gaps between curved pieces. Relevant to CNC, laser or a deliberately planned profile-cutting workflow. |

The small TypeScript package `guillotine-packer` handles kerf and compares sorting/splitting strategies. Its documented
API exposes placements, one standard bin size and a global rotation option. Per-part grain constraints and an exposed
cut sequence would need further investigation. It is a possible browser-only alternative if the requirements shrink.

Python `rectpack` offers Guillotine, MaxRects and Skyline heuristics, but its documented API does not supply native
saw kerf or a cutting tree. PackingSolver covers more of the required woodworking inputs without an app-specific
solver. No engine can be called best on this particular part list until it has been run against that list.

## Existing application

- `cad/bom.py` already extracts cutting envelopes from local assembly leaves, independently of live poses.
- `materials.CutPart` currently stores a path, material role, length, width and thickness. It has no outline or grain axis.
- The extractor sorts bounding-box dimensions. Preserve explicit stock-plane axes before adding grain rules or outlines.
- The cabinet back lining already uses developed centre-curve length rather than its curved bounding-box depth.
- `GET /api/v1/materials` supplies cuts, selected products, stock sizes and model revisions.
- The BOM's `stockGroups` groups compatible uses by selected product; custom stock remains separate by role.
- The tab controller currently supports CAD, BOM and Plan. Extend it while retaining the mounted CAD viewer.

These sources establish the current mechanism. Repository documentation says kerf, grain, waste and purchase sheet
counts still need a layout. No existing layout optimiser or recorded algorithm choice was found.

## Proposed behaviour

1. Load part dimensions and material selections from the model. Group compatible material and thickness together.
2. Read full-sheet sizes from the selected products. Allow owned rectangular offcuts with their dimensions and quantity.
3. Show kerf, edge trim and grain/rotation settings beside the layout. Keep kerf separate from fitting/finishing allowance.
4. Pack rectangular blanks for the curved partitions, frames and doors. Overlay actual flat profiles and internal
   cutouts when the CAD output supplies them. Identify curves, pockets, rebates and edge finishing as later operations.
5. Use the solver's cut thickness at each split. A shared cut loses one kerf; a finished part keeps its requested size.
   Exact sheet-edge fits must remain possible. Reserve edge trim independently.
6. Preserve each part's grain axis, face orientation and permitted rotation. Grain may matter for appearance or strength.
   Do not infer grain from whichever bounding-box dimension happens to be longest.
7. For one stock size, minimise the number of sheets, then prefer useful offcuts. For different purchasable sizes,
   compare purchase cost. Show cut count and the cutting sequence so the user can judge handling effort.
8. Plan ready-made timber lengths separately with 1D cutting-stock logic, including kerf and end trims. Exclude
   purchased hardware from sheet layouts. Keep reused slats identifiable as owned stock.
9. Save cutting settings with the project. Keep an accepted layout stable until the user requests a replacement;
   mark it out of date when its model revision, material selection or cutting settings change.

Use integer dimensions at a documented precision, such as hundredths of a millimetre, to avoid floating-point fits.
Round required blanks upward and available stock downward at that precision. Display millimetres throughout.
List oversize parts and insufficient stock explicitly. Call a result the best layout found unless the solver proves
optimality. Internal cutout reuse needs its own cutting-order treatment; rectangular blank packing does not establish it.

## Proposed tab

- A visible **Cut list** entry beside the existing project views.
- A material/stock selector and compact inputs for sheet size, kerf, trim, grain and available offcuts.
- One clear **Generate layout** action, plus print/export actions beside the result.
- Top views of the sheets with millimetre dimensions, labelled parts, grain arrows, kerf bands and numbered cuts.
- A neighbouring cut-list table: part, quantity, blank dimensions, material and finishing operations.
- Selecting a part highlights its placement; selecting a placement highlights its table row. Keep IDs visible in both.
- Show sheet requirements, used offcuts, usable remnants and any unplaced parts. Distinguish blank utilisation from
  the final material area of frames with large cutouts.
- Include parts and settings in printable output, with legible labels and a useful scale. Export SVG and CSV.

Follow WAI guidance for tab keyboard operation and selected-panel semantics when extending the project navigation.
Use labels and line styles as well as colour. Keep the table available as a textual representation of the diagram.
Primary settings and actions should remain visible rather than requiring a context menu.

## Sources

- [PackingSolver guillotine documentation](https://fontanf.github.io/packingsolver/rectangleguillotine.html):
  supported constraints, cutting-tree output, objectives and rotation restrictions.
- [PackingSolver repository](https://github.com/fontanf/packingsolver): local Python interface and other problem types.
- [PackingSolver on PyPI](https://pypi.org/project/packingsolver/): package metadata and wheel availability.
- [OpenCutList cutting diagrams](https://docs.opencutlist.org/features/parts/parts-list/cutting-diagrams):
  workshop-oriented modes, kerf/spacing, trims, offcuts, grain, dimensions and diagram presentation.
- [rectpack](https://github.com/secnot/rectpack): available heuristics, rotation controls and decimal precision guidance.
- [guillotine-packer](https://github.com/tyschroed/guillotine-packer): small TypeScript alternative and its documented API.
- [Jylänki's rectangle-packing survey](https://raw.githubusercontent.com/rougier/freetype-gl/master/doc/RectangleBinPack.pdf):
  the Guillotine, MaxRects and Skyline algorithm families and empirical comparisons.
- [WAI tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/): keyboard and selection semantics.
- [WCAG use of colour](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html): additional labels or visual cues.

Research used repository reads and primary documentation. Implementation used the existing running application and
read-only browser inspection. No tests, application services or browser interaction checks were started.
