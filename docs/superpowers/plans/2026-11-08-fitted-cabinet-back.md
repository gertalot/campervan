# Recover fitted cabinet depth

Goal: recover the wall-side depth, restricting the setback to the roughly 100mm rear-pillar region. Preserve
rear loading, two modules, side-only bolts, doors/hinges, shelf functions and the four visibility filters.

Use separate rear-corner and main back planes, each with a vertical lower frame and one straight upper rake.
The rear end frame remains at its existing plane. At the pillar's forward edge, one shaped 140 × 18mm upright
per module connects short rear back rails to full-depth main back rails with square end joints. Both uprights
bear through the module interface to the floor. A narrow plywood return closes the step. All remaining frame
stock stays 40 × 18mm and the bridge 90 × 18mm. Bunnings NZ 140 × 18 × 1800mm item 0132635 is listed at $27.43;
local stock unconfirmed. The board requires a guided straight/tapered inner-edge cut, not a custom timber size.

1. Stage affected CAD/material/parameter files outside watched source. Solve main planes against the wall beyond
   the pillar, rear planes only against the rear face. Clip cabinet depth by station, not globally.
2. Add shaped return uprights and local back rails/skins, extend shelves to the main back. Preserve actual
   connections and native cutting envelopes. Account for 140mm purchased stock in the existing BOM mechanism.
3. Construct once from saved parameters and measure wall gap, shelf depths, rear opening, joint contact and
   return-stock envelopes. Run scoped lint/types; no tests, browser interactions or delegated reviews.
4. Update documentation and publish a single source batch. Use existing regeneration and inspect status/logs.
   No service starts, commits, unrelated changes or further whole-cabinet profile shifts.
