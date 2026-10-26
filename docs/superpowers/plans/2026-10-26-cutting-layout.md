# Cut list and selectable layout modes

Approved scope: add a Cut list tab with straight-cut guillotine layouts and actual-shape nesting, selectable in the app.
Reuse model cuts, selected stock and local project persistence. Show kerf, trim, orientation, top views, part labels,
material use and unplaced parts. Keep generated layouts until replaced and identify stale results.

Implementation uses the writing-plans and executing-plans skills. Project instructions override tests, delegated
reviews, worktrees and service starts: do none of those. Inspect existing runtime output and the scoped diff.

- [x] Extend CAD cutting output with flat outlines and through holes; preserve developed blanks for curved sheet.
- [x] Add local PackingSolver integration for guillotine and irregular modes, saved settings/results and API routes.
- [x] Add the Cut list tab, accessible controls, SVG layouts, linked parts and print/export. Show only the selected mode.
- [x] Update practical documentation; inspect existing service logs and git diff --check. Leave visual acceptance to Gert.

Use a 0.1mm profile sampling tolerance with an explicit spacing allowance for polygon approximation. Preserve stock
dimensions separately from part contours. Use the native cutting tree for straight-cut instructions; nesting has
profile cuts and inner holes, with no promise of a through-cut sequence or a mathematical minimum.
