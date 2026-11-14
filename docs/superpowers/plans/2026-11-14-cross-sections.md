# Cross sections implementation plan

## Agreed behaviour

Move an exact transverse scan section along CAD Y with a slider. Draw it green, preserving fragments and gaps.
Give raw and authored section lines separate opacity sliders. Use labelled native controls with millimetre and
percentage readouts; retain normal keyboard operation and the viewer camera.

Blue sections are authored through conversation, using the scan, recorded measurements, vehicle construction and
Gert's estimates. There is no point averaging, automatic contour cleaning, global spline fit or automatic blue draft.
An authored half-outline contains individually chosen lines and cubic curve segments. Mirror it about its stated
centreline. Explicit horizontal floor and ceiling segments keep those surfaces parallel. Preserve sharp junctions,
small formed-metal blends, beam shoulders, panel returns and flat glazing as appropriate to the chosen station.

Gert chooses station spacing and explicitly records an approved draft. Keep all records in data/cross-sections.json.
Moving the green section never edits a blue record. Display the active blue section prominently and the other records
faintly. A saved-section selector returns to any authored station. Do not alter vehicle geometry during this work.

## Implementation

1. Add a pure TypeScript triangle-plane intersection index with 50mm Y buckets. Load the existing full-resolution
   registered mesh when available, using the same CAD transform as the scan reference. Do not infer missing surfaces.
2. Add a small cross-section document/API with finite piecewise geometry, draft/recorded states, immutable recorded
   outlines, atomic persistence and the repository's revision conflict convention.
3. Add section controls beside Scan comparison: Y slider and numeric input, green/blue opacity, saved-section selector,
   explicit Record action and status. Persist inspection settings in localStorage. Read authored changes periodically
   so a draft created through conversation appears without reloading the viewer.
4. Add independently managed viewer overlays that survive CAD regeneration. Use the installed Three.js wide-line
   addon for green 1.5px and active blue 3px lines. Keep saved inactive outlines faint and non-pickable.
5. Update the user/model documentation. Use the existing running app for inspection and the relevant frontend type
   check once, plus focused lint for the new API/storage. Do not create or run tests, start services,
   or delegate review passes.

## Focused failure cases

- Open scan sections remain open; no bridging or fabricated green contours.
- No blue draft exists until explicitly authored; empty state explains the next conversational step.
- Slider movement preserves all recorded geometry; conflicting writes report a conflict instead of overwriting it.
- Scan opacity and visibility do not hide the independently controlled cross-section lines.
- Reference translations, scan replacement and CAD regeneration retain correct section coordinates and camera.
- Recorded outlines are independent of mesh disposal and cannot be silently overwritten by a new draft.

## Sources and decisions

- Native range controls and visible units follow https://www.w3.org/WAI/ARIA/apg/patterns/slider/ .
- Wide lines use https://threejs.org/docs/pages/LineMaterial.html and
  https://threejs.org/docs/pages/LineSegments2.html .
- Existing scan loading/registration: frontend/src/cad-scan-reference.ts and frontend/src/scan-assets.ts.
- Existing viewer lifecycle: frontend/src/viewer.ts. Existing persistence conventions: scan_measurements_api.py.
- No general accessibility-compliance claim is made from these references.

## Approved longitudinal extension

Add an independent YZ raw section moving along X, using the same exact intersection engine with its indexed axis
selected explicitly. Both families share the registered scan buffers and retain separate position and opacity choices.
Keep existing XZ settings and negative rear-door stations through loading/reloads.

Extend authored records with a plane and plane-specific position. XZ remains the legacy default. YZ uses explicit
signed Y/Z points and a start, with no front/back mirroring or forced closure. An authored YZ baseline normally
appears at matching opposite X stations; only the inspected station is prominent. Explicit opposite-side geometry
and notes capture real trim differences. XZ can likewise carry an authored right-side half instead of an exact mirror.
All records remain hand-authored and explicitly recorded; there is no point averaging, automatic blue generation,
or vehicle/CAD change as part of this extension.
