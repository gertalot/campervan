# Simple cabinet frame implementation plan

Goal: replace disconnected rear members with connected, repeatable timber construction, preserving the rear chair
opening, two modules, current doors, five shelves, four visibility filters and side-only interface bolts.

Use the same sourced 40 × 18mm pine and existing skins. The lower back frame is vertical; the upper back frame is
one inclined plane. Fit these planes inside the restrictive rear-pillar envelope instead of profiling each timber
against the van. Use one upper rake angle, square joints within each back frame and repeated bevels at transverse
rail ends. Straight stiles replace segmented stiles. Back skins are two flat panels. No corner-return assembly.

1. Stage cabinet.py and cabinet_layout.py outside watched source. Determine lower depth and upper rake from the
   existing fitting volume; preserve at least 230mm rear chair clearance. Keep broad, usable timber sections.
2. Align rear cross-rails and wall post in one rear plane. Build straight posts and trim transverse rail ends against
   their mating posts. Rotate upper longitudinal back rails into the same plane as their stiles/back skin.
   Terminate middle bottom frames above the wheel arch rather than clipping disconnected feet around it.
3. Construct once using the saved project; inspect connections, clearances, timber shapes and native cut envelopes
   with direct build123d runtime geometry. Run scoped lint and type checks, no tests or browser interaction.
4. Update model/construction notes and publish source in one batch. Let the running app rebuild once and inspect
   its actual status/logs. No service starts, delegated reviews, commits or unrelated changes.
