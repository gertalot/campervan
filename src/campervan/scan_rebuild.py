"""Rebuild corrected camera/landmark solutions through the existing mesh/texture pipeline."""

import os
import shutil
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from campervan.scan_alignment import TagAlignment, tag_alignment
from campervan.scan_graph import GraphDocument
from campervan.scan_workflow_models import ArtifactEnvelope, CleanupMask, SourceBinding
from campervan.scans import ScanSettings, file_hash, publish_reconstruction, read_json, write_json


def rebuild(source: Path, correction: Path, output: Path, *, fingerprints: dict[str, str],
            cleanup_masks: list[CleanupMask] | None = None) -> Path:
    original = read_json(source / "run.json")
    artifact = ArtifactEnvelope.model_validate(read_json(correction / "artifact.json"))
    if artifact.kind != "scan_correction" or artifact.fingerprints != fingerprints:
        raise ValueError("Update mesh requires a current scan-correction artifact with matching full fingerprints.")
    if artifact.id != correction.name or artifact.source_run_id != source.name or original.get("tag_layout_id") != artifact.layout_id:
        raise ValueError("Corrected poses do not belong to this source result/layout.")
    if (file_hash(correction / "solution.json") != artifact.payload["solution_sha256"] or
        file_hash(correction / "graph.json") != artifact.payload["graph_sha256"]):
        raise ValueError("The saved corrected camera/tag solution differs from its preview artifact.")
    solution = read_json(correction / "solution.json")
    binding_data = artifact.assumptions.get("source_binding")
    binding = SourceBinding.model_validate(binding_data) if binding_data else None
    if binding and (binding.source_run_id != source.name or binding.profile_ref != artifact.profile_ref):
        raise ValueError("Reviewed cleanup context does not belong to this correction source/profile.")
    reviewed_masks = binding.masks if binding else []
    if cleanup_masks is not None and cleanup_masks != reviewed_masks:
        raise ValueError("Cleanup masks differ from the reviewed correction preview.")
    cleanup_masks = reviewed_masks
    output.mkdir(parents=True, exist_ok=False)
    frames = read_json(source / "frames.json")
    frame_ids = {str(frame["id"]) for frame in frames["frames"]}
    mask_provenance = []
    exclusions: dict[str, list[str]] = {}
    for index, mask in enumerate(cleanup_masks or []):
        asset = (source / mask.asset).resolve()
        if Path(mask.asset).is_absolute() or not asset.is_relative_to(source.resolve()) or not asset.is_file():
            raise ValueError("Cleanup mask must be an existing asset of the original source result.")
        if mask.frame_id not in frame_ids:
            raise ValueError(f"Cleanup mask refers to unavailable source frame {mask.frame_id}.")
        destination = output / "working" / "cleanup-masks" / f"{index}{asset.suffix}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(asset, destination)
        relative = str(destination.relative_to(output))
        exclusions.setdefault(mask.frame_id, []).append(relative)
        mask_provenance.append({**mask.model_dump(), "preserved_asset": relative, "sha256": file_hash(destination)})
    frames["exclusion_masks"] = exclusions
    frames["database"] = str((source / frames["database"]).resolve())
    frames["poses_corrected"] = True
    for frame in frames["frames"]:
        for field, folder, suffix in [
            ("rgb", "capture_rgb", "jpg"),
            ("depth", "capture_depth", "png"),
            ("confidence", "capture_confidence", "png"),
        ]:
            if frame.get(field):
                destination = output / "working" / "extracted" / folder / f"{frame['id']}.{suffix}"
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.link((source / frame[field]).resolve(), destination)
                frame[field] = str(destination.relative_to(output))
    write_json(output / "frames.json", frames)
    write_json(
        output / "poses.json", {"convention": "camera_to_world", "units": "m", "poses": solution["camera_poses"]}
    )
    graph = GraphDocument.model_validate_json((correction / "graph.json").read_text())
    graph.poses = solution["graph_poses"]
    write_json(output / "graph.json", graph.model_dump())
    manifest = {
        **original,
        "created_at": datetime.now(UTC).isoformat(),
        "name": output.name,
        "pose_source": "gtsam_measured_distances",
        "tags": solution["tags"],
        "stages_seconds": {},
        "source_run_id": source.name,
        "correction_artifact_id": artifact.id,
        "workflow_id": artifact.workflow_id,
        "reference_run_id": original.get("reference_run_id", source.name),
        "measurement_revision": artifact.measurement_revision,
        "tag_note": "GTSAM fitted landmarks; physical distance records are unchanged.",
        "cleanup": {
            "source_run_id": source.name,
            "pre_cleanup_run_id": source.name,
            "masks": mask_provenance,
            "pixel_coordinates": "original depth; nonzero pixels excluded before fusion",
            "note": ("Reviewed pixel masks applied to original RGB-D." if cleanup_masks else
                     "No reviewed cleanup masks supplied; cleanup context skipped."),
        },
        "correction": {
            "label": "Corrected reconstruction",
            "original_run_id": source.name,
            "artifact_id": artifact.id,
            "fingerprints": artifact.fingerprints,
            "solution_sha256": artifact.payload["solution_sha256"],
            "context": artifact.payload["context"],
            "registration": artifact.payload["registration"],
        },
    }
    for field in ["assets", "layers", "geometry", "photo_error", "alignment", "external_poses", "analysis_id"]:
        manifest.pop(field, None)
    if (original.get("alignment") or {}).get("definition"):
        manifest["alignment"] = tag_alignment(
            solution["tags"], TagAlignment.model_validate(original["alignment"]["definition"])
        )
    settings = ScanSettings.model_validate(original["settings"])

    def stage(name: str, action: Callable[[], Any]) -> Any:
        print(f"[{name}]", flush=True)
        started = time.monotonic()
        value = action()
        manifest["stages_seconds"][name] = round(time.monotonic() - started, 3)
        return value

    return publish_reconstruction(output, manifest, settings, stage)
