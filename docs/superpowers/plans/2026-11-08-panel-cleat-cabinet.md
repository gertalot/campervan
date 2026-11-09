# Panel-and-cleat cabinet implementation plan

Replace the timber skeleton with supporting 9mm Tigerply Okoume end panels and a centre divider, using the
existing Bunnings product. Keep five 6mm shelves, nine existing doors, front hardware support, side-only module
bolts, 20mm alignment guides, the rear chair opening and the full scribed van contour.

1. Stage geometry and stock bindings outside watched source. Reuse the existing constant-thickness scribing,
   door construction, module fasteners, material roles and four visibility groups.
2. Retain the 40 × 18mm front frame. Replace transverse/rear ladders with full-profile plywood panels and
   face-mounted 40 × 18mm shelf ledgers. Panels butt behind the front frame; no thin plywood edge fixings.
3. Retain the 90 × 18mm arch bridge with end-panel bearing blocks and divider bearing blocks. Give all five
   shelves face-mounted side supports. Preserve 230 × 730mm rear chair access without a lower sill.
4. Use straight side joining rails in both modules, bearing timber-to-timber at the existing joint. Scribe the
   lower guide extensions and upper panel seam without letting a front/rear joining rail obstruct access.
5. Migrate only the previous 3mm skin stock to the existing 9mm product; update stock notes, cutting attribution
   and construction notes. Preserve unrelated edits and custom material selections.
6. Build the cabinet using saved inputs and inspect physical overlaps, panel thickness, shelf support, joint
   bearing and cut-list attribution with direct CAD operations. Use existing runtime constraints and scoped
   lint/types. No tests, service starts, browser interaction suites, review delegation or commits.
7. Publish one source batch. Build and save a complete bundle outside the reloadable API, then load it through
   the existing saved-model endpoint. Report publication separately from Gert's visual acceptance.
