"""Reusable physical tag roles, with a separately solved rigid transform for each capture."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from campervan.scans import read_json, write_json


class TagDirection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_tag: int = Field(gt=0)
    to_tag: int = Field(gt=0)

    @model_validator(mode="after")
    def check_endpoints(self) -> "TagDirection":
        if self.from_tag == self.to_tag:
            raise ValueError("Direction endpoints must be different tags.")
        return self


class TagAlignment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    target_frame: str = Field(min_length=1)
    description: str = ""
    origin_tag: int = Field(gt=0)
    up_normal_tags: list[int] = Field(min_length=1)
    x_direction: TagDirection
    y_direction: TagDirection

    @model_validator(mode="after")
    def check_ids(self) -> "TagAlignment":
        if any(i <= 0 for i in self.up_normal_tags) or len(set(self.up_normal_tags)) != len(self.up_normal_tags):
            raise ValueError("Up-normal tags must be distinct positive IDs.")
        return self


def tag_alignment(tags: list[dict[str, Any]], definition: TagAlignment) -> dict[str, Any]:
    """Solve supplied geometric references; no project paths, tag assignments or vehicle conventions."""
    import numpy as np
    from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

    poses = {tag["id"]: np.asarray(tag["pose"], dtype=float) for tag in tags}
    required = {definition.origin_tag}
    for direction in (definition.x_direction, definition.y_direction):
        required.update((direction.from_tag, direction.to_tag))
    required.update(definition.up_normal_tags)
    result: dict[str, Any] = {"definition": definition.model_dump(), "units": "m", "source_frame": "scan"}
    if missing := sorted(required - poses.keys()):
        return {**result, "status": "unaligned", "reason": f"Missing alignment tags: {missing}"}
    for tag_id in required:
        pose = poses[tag_id]
        if (
            pose.shape != (4, 4)
            or not np.isfinite(pose).all()
            or not np.allclose(pose[3], [0, 0, 0, 1])
            or not np.allclose(pose[:3, :3].T @ pose[:3, :3], np.eye(3), atol=1e-4)
            or not np.isclose(np.linalg.det(pose[:3, :3]), 1, atol=1e-4)
        ):
            raise ValueError(f"Invalid alignment pose for tag {tag_id}.")

    def unit(vector: Any) -> Any:
        length = float(np.linalg.norm(vector))
        if length < 1e-6:
            raise ValueError("Tag alignment references do not define independent directions.")
        return vector / length

    origin = poses[definition.origin_tag][:3, 3]
    across = unit(poses[definition.x_direction.to_tag][:3, 3] - poses[definition.x_direction.from_tag][:3, 3])
    forward = unit(poses[definition.y_direction.to_tag][:3, 3] - poses[definition.y_direction.from_tag][:3, 3])
    up_hint = unit(np.cross(across, forward))
    normals = [poses[tag][:3, 2] for tag in definition.up_normal_tags]
    normals = [normal if normal @ up_hint >= 0 else -normal for normal in normals]
    up = unit(np.sum(normals, axis=0))
    across = unit(across - up * (across @ up))
    forward = unit(forward - up * (forward @ up))
    if np.cross(across, forward) @ up <= 0:
        raise ValueError("Tag directions disagree with a right-handed reference frame.")
    # Align-constrain: fix the floor normal, then least-squares fit the two horizontal directions.
    rotation, _ = Rotation.align_vectors(
        [[0, 0, 1], [1, 0, 0], [0, 1, 0]], [up, across, forward], weights=[float("inf"), 1, 1]
    )
    transform = np.eye(4)
    transform[:3, :3] = rotation.as_matrix()
    transform[:3, 3] = -rotation.apply(origin)
    return {
        **result,
        "status": "aligned",
        "target_frame": definition.target_frame,
        "convention": "scan_to_reference",
        "matrix": transform.tolist(),
        "diagnostics": {
            "horizontal_reference_angle_deg": float(np.degrees(np.arccos(np.clip(across @ forward, -1, 1)))),
            "floor_normal_residual_deg": [
                float(np.degrees(np.arccos(np.clip(normal @ up, -1, 1)))) for normal in normals
            ],
            "reference_positions_m": {
                str(tag): rotation.apply(poses[tag][:3, 3] - origin).tolist() for tag in sorted(required)
            },
        },
    }


def align_run(output: Path, profile: Path, measurements: Path | None = None) -> dict[str, Any]:
    """Update alignment metadata only; preserve all original scan-frame assets and poses."""
    manifest = read_json(output / "run.json")
    if measurements is not None:
        from campervan.scan_measurements import read_measurements

        manifest["tag_layout_id"] = read_measurements(measurements).tag_layout_id
    definition = TagAlignment.model_validate(read_json(profile))
    alignment = tag_alignment(manifest.get("tags", []), definition)
    write_json(output / "alignment.json", alignment)
    manifest["alignment"] = alignment
    write_json(output / "run.json", manifest)
    return alignment
