# Recognition trial results — 9 November 2026

Status: requested feasibility spike completed; no production scene-understanding integration or backend selection.

## Execution

- Apple M1, 16 GB; PyTorch 2.15.0, Transformers 5.22.2, MPS device.
- Grounding DINO tiny revision `a2bb814dd30d776dcf7e30523b00659f4f141c71`.
- SAM 2.1 tiny revision `de431c4043854a71d8101e17995dfe596bf101a5`.
- Source: existing `capture-00fe810c-6bba-4c5f-9f5a-da0d63c5a64f`, frames 76, 415, 470, 770 and 1020.
- Five-frame detection/segmentation/projection elapsed 22.06 seconds, excluding model loading/downloads and final
  aggregation/visualisation. Initial warm-up is included in the first frame's 10.44 seconds.
- Follow-up on frames 76/415 with wheel-arch/insulation/door-panel concepts: 6.46 seconds for those frame operations.
- Original depth/confidence/optical poses projected accepted masks into observed 3D geometry; source data unchanged.
- Extracted six large planes from the original cloud as separate geometric evidence. Nearby semantic votes are
  recorded, not interpreted as proven surface classifications.

## What visual inspection supports

- SAM2 often follows visible boundaries closely: plywood roof, glass apertures, front seat and foil-covered wheel
  well have recognisable masks in the saved images.
- Initial DINO labels plausibly identify the roof/windows/front seat in representative images.
- Initial DINO incorrectly calls the foil-covered wheel well a car seat and rear-door trim a dashboard.
- Adding "wheel arch", "insulation" and "door panel" produces a plausible wheel-arch detection in frame 76, but
  introduces or retains substantial errors elsewhere. Frame 415 loses the floor label and calls floor geometry
  door panels/windows. Prompt wording materially changes the result.
- Object identity and material are not mutually exclusive: insulation covers a wheel arch. Taking the largest raw
  score as the sole point label is a crude trial visualisation, not a suitable final semantic fusion model.

This is manual inspection of seven inference frames across five unique views, not a labelled benchmark, accuracy
measurement or evidence of reliable whole-van recognition. Raw labels are not ready to drive automatic deletion or
structural constraints. The result establishes local runtime feasibility and useful boundary proposals only.

## Artifacts

- Five-frame outputs: `.local/scene-understanding-trial/second-pass/`.
- Vocabulary follow-up: `.local/scene-understanding-trial/wheel-arch-followup-complete/`.
- Each contains full-resolution overlays/source images, masks, per-frame detections/scores, report/provenance,
  observed labelled point arrays, semantic PLY, static point-cloud preview and a recognition contact sheet.
- The five-frame sample yields 9,014 labelled 20 mm voxels; this is sparse trial coverage, not a semantic mesh of the
  entire van. Glass masks are retained in 2D but not projected as glass surfaces because depth may see through glass.

See [repeatable invocation](README.md). Use another source run/frame list and separate concept data for future trials.
Temporary uv-run dependencies and public model downloads were used; project dependency files were not edited.
No application services/browser were started, no app interaction automation or tests were created/run, and no capture,
physical measurement, mesh, pose or existing viewer state was changed.

## Trial failures corrected

An initial attempt stopped because newer Transformers configuration objects no longer expose the private commit-hash
attribute; the script now resolves public model revision metadata. Rendering the completed first inference pass then
needed matplotlib; visualisation was resumed from saved inference arrays without repeating model inference. Moving
colours into JSON exposed a Pillow list-versus-tuple drawing error; that was corrected before the completed follow-up.
The abandoned output folders retain partial diagnostics and are not completed results.

## Consequence for the design

Keep semantic recognition a required capability, but do not claim this tiny-model combination achieves it reliably.
Reject Grounding DINO tiny as the proposed primary semantic recogniser for this workflow. Next work must establish
context-aware vision-language identification of the actual van features before adding more fusion/constraint work.
Segmentation remains useful for boundaries, while original depth/poses supply measured geometry. Symmetry and
multi-view consistency support interpretation; they must not be used to conceal an inadequate recognition component.
A suitable vision-language backend remains an open choice. The current trial is not OpenMask3D, full cross-view semantic
validation, corrected mesh generation or an implementation of the four-stage UX.
