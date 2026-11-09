# Context-aware recognition trial — 9 November 2026

Status: useful local recognition result; no automatic complete-scene or 3D semantic integration claimed.

## Method and provenance

- Candidate: `mlx-community/Qwen3.5-4B-MLX-4bit`, revision
  `32f3e8ecf65426fc3306969496342d504bfa13f3`, an Apache-2.0 vision-language model conversion.
- MLX-VLM 0.7.12, MLX 0.32.4; Apple M1/16 GB. Native MLX inference, no model service.
- Public safetensors downloaded locally. Photos remained local. No project dependency files were changed.
- Same source capture and representative rear/front frames as the earlier detector trial.
- Prompts, frame IDs and optional region coordinates are data files, separate from the runner.
- No expected object names or old detector labels were supplied to the VLM. Context stated that the photos show a
  cargo van and that the body is approximately symmetric. That symmetry was prompt context, not a geometric solver.

## First pass: open-ended scene interpretation

Input pairs: rear frames 76/415 and front frames 770/1020. Outputs are preserved at
`.local/scene-understanding-trial/vlm-qwen35-4b/`.

The front response recognises dashboard, centre console/shifter, front seat, side-door region, wooden ceiling panel
and windshield. However, it guesses the vehicle make/model incorrectly and asserts details that were not established.
The rear response identifies the ribbed metal floor and doors, but separates out coverings as features and misses
the wheel-well identity. Its verbose output reaches the 1,000-token limit and is incomplete JSON. This pass is not
evidence of reliable automatic full-scene interpretation.

Observed elapsed times: rear 65.31 seconds (truncated), front 50.95 seconds. Peak reported MLX allocation approximately
4.44 GB. This is not total system/process RAM or a calibrated accuracy benchmark.

## Second pass: region identity with full-image context

Use the established context-aware region-query mechanism: original full photos carry an unlabelled red box around
a proposed region. Three regions come from saved detector/SAM proposals selected for this diagnostic; a fourth is
the visible roof patch. The region names passed through the runner are generic IDs, not category answers.

This isolates interpretation given a region, not automatic proposal discovery or selection. Recognition is assessed
by manual comparison with the source photographs, not tests or an automated scoring suite.

| Region | VLM identity | Observed assessment | Elapsed |
| --- | --- | --- | --- |
| Foil-covered protrusion, frames 76/415 | Rear wheel well liner or fender flare | Broad wheel-well identity is appropriate; exact subtype/function wording remains speculative | 20.15 s |
| Dark rear-door insert, frame 76 | Rear cargo door panel | Appropriate broad identity; material guess is unverified | 12.98 s |
| Front seat back/headrest, frame 1020 | Seat | Appropriate broad identity | 11.08 s |
| Plywood roof patch, frame 76 | Ceiling panel, plywood | Appropriate broad identity/material from visible grain and location | 10.77 s |

All four region responses completed and parsed as JSON. Peak reported MLX allocation: 4.447 GB. The wheel-well query
used two views; the other three used one full photo each. There was no expected wheel-well, seat or door-panel answer
in the model questions. No further label-specific prompt tuning was performed.

Results, exact prompts/responses and source images:
`.local/scene-understanding-trial/vlm-qwen35-regions/` (`report.html`, `report.json`,
`vlm-recognition-summary.jpg`, individual region text and images).

## Conclusion and remaining work

Context-aware region identification is materially more useful than the failed tiny keyword detector for these
selected examples. It runs locally on this machine, so this recognition component does not presently require a
bigger machine. That does not establish that a whole-capture pipeline or a larger model will have the same footprint.

The model still makes unsupported specifics and material guesses. Preserve uncertainty and source evidence. Do not
treat every sentence as measured fact or allow it to generate metric geometry.

The next coherent pipeline is automatic class-agnostic geometric/mask proposals, contextual identification of those
regions using useful source views, multi-view 3D association, then structural/symmetry consistency. The region-cued
trial supports the identification component; automatic coverage, boundary accuracy, full 3D association, geometric
symmetry inference and their combined recognition quality remain unimplemented/unverified.

The general-caption pass is retained as a failure/limit, not hidden or counted as a success. No captures,
measurements, existing poses, meshes or viewer state were modified. No tests, browser interactions or services were
created/run. See [repeatable runner instructions](README.md).
