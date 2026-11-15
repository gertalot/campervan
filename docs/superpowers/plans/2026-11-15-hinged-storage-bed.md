# Hinged storage bed implementation plan

## Current agreed structure

One bottomless plywood box stands on the van floor, with a transverse centre divider creating two equal bays.
Its wall-side outer face starts flush with the slat ends, then the accepted 24mm shared bed offset moves
both benches and their components towards the aisle for the middle pillar. All five panels rise to support the fixed and moving slats
directly. Both fixed horizontal supports and the moving rear rail are removed. The moving front support remains
flat, made from slat stock and supported by provisional metal legs. Couch width and 1070mm sleeping width remain.

The current full-length lid-opening preview and provisional hinges remain pending redesign; removing the rear
fixed support removes its previous hinge/slat connection. Vehicle-wall clearance, actual bed length, pivot setback,
slat retention, alignment, stops and hardware strength remain to refine. Keep the existing cushion conversion.

## Work

1. Replace old frame/drawer/bracket geometry with bottomless box, centre divider, directly supported slats, moving front rail and provisional hardware.
2. Update live lid/extension motion, visibility, controls and the existing table mounting backing.
3. Retire superseded parameters and purchasing roles while preserving existing purchase records.
4. Update CAD and usage documentation; inspect the existing app regeneration and generated cutting data.

No tests, new services, browser automation, commits or independent review passes.

## Interaction guidance

Reuse the existing labelled native position slider and numeric input for lid opening (0–100%, 0–75 degrees).
Preserve keyboard/focus behavior rather than adding a custom control. W3C APG slider guidance, consulted
15 November 2026: https://www.w3.org/WAI/ARIA/apg/patterns/slider/ . This does not establish full accessibility compliance.

## Accepted middle-pillar placement

The accepted 24mm offset now belongs to the complete bed through `bed_inward_offset_mm`, applied at the long- and
cross-bench assembly roots. The former box-only parameter migrates without losing its value. Slats, moving front
support, legs, hinge preview and cushions follow the box. The mounted table and fixed bracket follow the same datum;
its independent stowed pose stays put. Retain all dimensions and the 1070mm sleeping width, including 452mm slide travel.
This restores the 5mm box/rail running gap. The cabinet front subsequently follows the bed offset: Gert approved a 24mm depth reduction to restore the former nominal gap. Wheel-arch fitting remains separate.
