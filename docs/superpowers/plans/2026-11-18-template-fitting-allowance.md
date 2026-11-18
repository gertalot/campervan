# Template fitting allowance implementation plan

**Goal:** Reserve 50mm by default on explicitly identified vehicle-fitting edges without changing CAD furniture.

**Architecture:** Extend the existing cutting settings and per-part options. CAD profile extraction maps explicitly
identified fitting axes to drawing edges. One effective blank calculation supplies all solver and display consumers.
Fitted pieces reserve rectangular blanks in straight and nesting modes. Saved layouts remain visibly stale until replaced.

**Scope:** `materials.py`, `cad/bom.py`, `cad/cut_profiles.py`, `cutting_models.py`, `cutting.py`, their coordinator/API/
snapshot callers, and the existing frontend cutting files. Preserve unrelated work. No new library or service.

1. Add global 50mm default and per-part directional overrides. Mark cabinet supporting panels, shelves and roof infill
   by physical fitting axes, not by detecting arbitrary curved edges. Retain precise joining edges.
2. Compute enlarged blanks once; use them in packing, section candidates, orientation, areas and layout fingerprints.
   Translate nominal profiles inside their blanks; prevent nesting in reserved material or unfinished fitting notches.
3. Extend the piece details with labelled per-edge inputs. Show rough dimensions prominently, nominal references
   secondarily, and solid blanks/dashed reference profiles with fitting and datum explanations in drawings and exports.
4. Document operation. Use normal running-app CAD/cutting regeneration and existing logs; no tests, service starts,
   browser interaction checks or additional verification infrastructure, per project instructions.

UX evidence: W3C WAI [Labelling controls](https://www.w3.org/WAI/tutorials/forms/labels/) informs visible, associated
input labels. [OpenCutList](https://docs.opencutlist.org/features/parts/options#hide-rough-dimensions) establishes the
rough/model dimension distinction. These references do not establish universal accessibility compliance.
