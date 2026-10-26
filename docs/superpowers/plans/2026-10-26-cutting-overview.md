# Whole-build cut-list overview

Approved by Gert: resume and implement the discussed overview, thickness focus and global settings.

- Default view draws all furniture cutting pieces and floor plywood, grouped by assembly, using CAD names.
- Repeated identical pieces may share a drawing with a visible quantity and their individual names in detail.
- Plywood-thickness filters lead to that material's parts and sheet layouts; timber remains identifiable.
- Algorithm, blade kerf and trimming are global. Stock sizes/offcuts and part direction remain material-specific.
- Remove search time. Publish improving layouts from a cancellable background solver worker with no time limit.
  Report the solver's optimality flag truthfully; display the best result while work continues.
- Each sheet names its material, thickness and physical size. Explain kerf and trim beside its drawing.
- Retain saved layouts and project backups. No tests, delegated reviews, extra services or browser interaction checks.

Use existing frontend SVG, FastAPI and project persistence. The solver worker follows the existing CAD subprocess
pattern. Inspect the existing application and logs; Gert provides visual acceptance.

Ruling: the coordinator owns background solver tasks, following its existing CAD worker ownership. The existing
model-status polling refreshes active cutting results. This keeps API requests short and lets shutdown cancel
unlimited searches. No new polling timer or long-lived HTTP stream is needed.

Ruling: add the previously excluded floor plywood to the cut data and a custom material role. Preserve its current
thickness and one-piece CAD shape; confirm stock before arranging custom material.

Research: OpenCutList cutting diagrams (material groups, labelled parts and allowances), NN/g recognition over recall
and progressive disclosure. These justify named visible parts and moving less-used settings out of the main view.
Sources: https://docs.opencutlist.org/features/parts/parts-list/cutting-diagrams
https://www.nngroup.com/articles/recognition-and-recall/
https://www.nngroup.com/articles/progressive-disclosure/

Started 2026-10-26 04:44 UTC. Estimate: 20–30 minutes including runtime inspection.

Implemented: all-pieces overview, thickness/material filters, CAD names, quantities with individual names in detail,
global settings, labelled sheet drawings and allowances, per-material stock, background optimisation and persistence.
The native nesting adapter's empty initial certificate needed handling; the running app exposed it and it was fixed.
Observed results after that fix: 18mm plywood (all eleven pieces) fits one sheet and 9mm doors fit one sheet;
PackingSolver reported optimal stock counts for both. The app reports 108 cutting pieces, including the floor.
Read-only browser inspection found no console warnings/errors. git diff --check passed. No tests or browser
interaction checks were run; visual acceptance remains with Gert.
