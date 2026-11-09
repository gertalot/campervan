# Cabinet modules implementation plan

**Goal:** Build two separable cabinet modules joined at the middle shelves, using 40 × 18mm upper timber,
18 × 18mm lower supports, sliding 20mm guide lips and eight M5 through-bolts.

**Architecture:** Retain the existing cabinet geometry builder and partition its components into Lower module
and Upper module. A cabinet-specific join helper constructs the mating ring, guide relief and bolt holes.
Update direct consumers of assembly paths and materials; preserve saved visibility preferences.

**Spec:** `docs/research/cabinet-modules.md` and Gert's approved offset-guide sketch and 40 × 18mm stock choice.

**Constraints:** No tests, no browser checks, no service starts, no commits. Preserve unrelated working changes.
Use the existing running app for regeneration and inspect its resulting CAD cuts/status, plus focused lint/build checks.

1. Add stock-driven upper-ring parameters and material roles, with the verified Bunnings 40 × 18 × 1800mm product.
2. Split the cabinet at the middle shelf top; raise transverse-panel seams by 9mm, leaving the aisle entry open.
   Give mating faces 0.5mm clearance. Replace shared-level rear joint blocks with the upper ring where they overlap.
3. Add eight vertical bolt holes through upper timber, shelves and lower timber; model eight M5 × 75mm fixing sets.
   Hardware sets remain explicitly unpriced until a matching bolt/washer/nut purchase is sourced.
4. Update timber and developed backing cut extraction, door motion paths and visibility preference migration.
5. Save the new timber selection, document assembly and joint machining, and inspect the app's regenerated output.

**Review focus:** Every manufactured part belongs to exactly one module; no member bridges the removable seam;
entry guides do not require lifting above ceiling; bolt bores align with real supported stock; door motion and
visibility survive path changes; the curved lining has separate developed cut lengths.
