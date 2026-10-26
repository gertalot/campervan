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

One stock size uses bin packing to minimise stock count. Multiple stock entries minimise full stock pieces,
treating owned offcuts as low-cost stock. The page labels proof of minimum count only when PackingSolver's
`is_proven_optimal()` reports it. Native solver workers have no time limit. The coordinator owns/cancels their tasks,
saves improving candidates and keeps better saved candidates when a new search starts. The existing model-status
poll also refreshes active cutting results. API requests return immediately; leaving the tab does not end the search.
Global setting changes, stock edits, changed CAD dimensions and application shutdown stop affected workers.

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
