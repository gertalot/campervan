# Timber cabinet model implementation

User authorizes replacement of the current cabinet and four local visibility filters. Implement inline; no tests,
services, browser interaction, delegated review or commits. Preserve unrelated edits. Stage source files outside the
watched source tree and publish one coherent batch.

1. Replace plywood carcass with sourced 40 × 18mm members, 3mm fixed skins, 6mm inset doors and shelves, and two
   modules. Keep chair loading, wall/roof fitting, side-only interface bolts and live door poses. Model hinge
   envelopes and their door-face attachment; both fixed and moving halves belong to Doors for visibility.
2. Keep each module's Frames, Skin, Shelves and Doors as stable hierarchy nodes. Update the existing visibility
   path rules and metadata eyes, retaining saved filters and parent/category interactions. Use native labelled
   checkboxes, following https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/.
3. Adapt cabinet material roles, saved selection migration, flat cuts/timber envelopes and dimensional limits.
   Keep only one timber responsibility for the new frame; remove superseded cabinet material roles.
4. Use the model's runtime construction plus scoped lint/type compilation. Do not create or run tests. Inspect
   relevant logs after the running app rebuilds; leave visual acceptance to Gert.
5. Update the cabinet modelling documentation and report actual completion and any visual verification limits.
