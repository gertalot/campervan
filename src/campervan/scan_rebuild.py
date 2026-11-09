"""Rebuild corrected camera/landmark solutions through the existing mesh/texture pipeline."""

import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from campervan.scan_alignment import TagAlignment, tag_alignment
from campervan.scan_graph import GraphDocument
from campervan.scans import ScanSettings, publish_reconstruction, read_json, write_json


def rebuild(source: Path, analysis: Path, output: Path) -> Path:
    original = read_json(source / "run.json")
    result = read_json(analysis / "result.json")
    solution = read_json(analysis / "solution.json")
    if result["run_id"] != source.name or original.get("tag_layout_id") != result["tag_layout_id"]:
        raise ValueError("Corrected poses do not belong to this source result/layout.")
    output.mkdir(parents=True, exist_ok=False)
    frames = read_json(source / "frames.json")
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
    graph = GraphDocument.model_validate_json((analysis / "graph.json").read_text())
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
        "analysis_id": analysis.name,
        "reference_run_id": original.get("reference_run_id", source.name),
        "measurement_revision": result["measurement_revision"],
        "tag_note": "GTSAM fitted landmarks; physical distance records are unchanged.",
    }
    for field in ["assets", "layers", "geometry", "photo_error", "alignment", "external_poses"]:
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
