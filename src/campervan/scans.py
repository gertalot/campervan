"""Offline, repeatable RTAB-Map capture processing; no CAD or service dependency."""

import hashlib
import json
import re
import shutil
import sqlite3
import struct
import subprocess
import time
import zlib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCAN_RUNS = Path(".local/scans")


class ScanSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_default=True)
    voxel_mm: float = Field(default=5, gt=0)
    sdf_trunc_mm: float = Field(default=25, gt=0)
    depth_max_m: float = Field(default=4, gt=0)
    depth_confidence_min: int = Field(default=50, ge=0, le=100)
    min_component_triangles: int = Field(default=200, ge=0)
    target_triangles: int = Field(default=500000, gt=0)
    texture_size: int = Field(default=4096, ge=256, le=16384)
    uv_partitions: int = Field(default=4, ge=1, le=16)
    tag_family: Literal["36h11"] | None = None
    tag_size_mm: float | None = Field(default=None, gt=0)
    texture_mode: Literal["baked", "photo"] = "baked"

    @model_validator(mode="after")
    def check_settings(self) -> "ScanSettings":
        if self.sdf_trunc_mm <= self.voxel_mm:
            raise ValueError("SDF truncation must be larger than the voxel size.")
        if (self.tag_family is None) != (self.tag_size_mm is None):
            raise ValueError("Provide both tag family and tag size, or neither.")
        return self


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def native_command(command: list[str], log: Path, cwd: Path | None = None) -> None:
    """Keep the real diagnostics visible and retain them with this run."""
    with log.open("a", encoding="utf-8") as stream:
        stream.write(f"\nDirectory: {cwd or Path.cwd()}\nCommand: {json.dumps(command)}\n")
        stream.flush()
        with subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
            assert process.stdout is not None
            try:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    stream.write(line)
                result = process.wait()
            except BaseException:
                process.terminate()
                process.wait()
                raise
        if result:
            raise RuntimeError(f"{Path(command[0]).name} exited {result}; see {log}")


def database_info(path: Path) -> dict[str, Any]:
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        version = db.execute("SELECT version FROM Admin").fetchone()[0]
        if not str(version).startswith("0.24."):
            raise ValueError(f"Unsupported RTAB-Map database version {version}: {path}")
        saved = db.execute("SELECT length(opt_poses), length(opt_ids) FROM Admin").fetchone()
        return {
            "version": version,
            "node_ids": [row[0] for row in db.execute("SELECT id FROM Node ORDER BY id")],
            "saved_poses": bool(saved and saved[0] and saved[1]),
            "sessions": [row[0] for row in db.execute("SELECT DISTINCT map_id FROM Node ORDER BY map_id")],
        }


def _calibration(path: Path) -> dict[str, Any]:
    import cv2

    storage = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    if not storage.isOpened():
        raise ValueError(f"Cannot read calibration: {path}")
    try:
        data = storage.getNode("camera_matrix").getNode("data")
        matrix = [data.at(index).real() for index in range(data.size())]
        if len(matrix) != 9 or matrix[0] <= 0 or matrix[4] <= 0:
            raise ValueError(f"Invalid pinhole calibration: {path}")
        distortion = storage.getNode("distortion_coefficients").getNode("data")
        if any(abs(distortion.at(i).real()) > 1e-9 for i in range(distortion.size())):
            raise ValueError(f"Non-rectified calibration is not yet supported: {path}")
        return {
            "width": int(storage.getNode("image_width").real()),
            "height": int(storage.getNode("image_height").real()),
            "intrinsics": matrix,
        }
    finally:
        storage.release()


def saved_tags(database: Path) -> list[dict[str, Any]]:
    """Read RTAB-Map 0.24 saved landmark poses in the same world frame as the mesh."""
    database_info(database)  # Enforce the supported database version.

    def unpack(blob: bytes, kind: int, code: str) -> tuple[int, tuple[Any, ...]]:
        # Compression.cpp: zlib payload followed by rows, columns and OpenCV type.
        rows, columns, mat_type = struct.unpack("<3i", blob[-12:])
        payload = zlib.decompress(blob[:-12])
        if rows != 1 or mat_type != kind or len(payload) != columns * 4:
            raise ValueError("Unsupported RTAB-Map saved landmark matrix.")
        return columns, struct.unpack(f"<{columns}{code}", payload)

    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        ids_blob, poses_blob = db.execute("SELECT opt_ids, opt_poses FROM Admin").fetchone()
        if not ids_blob or not poses_blob:
            return []
        count, ids = unpack(ids_blob, 4, "i")
        pose_count, poses = unpack(poses_blob, 5, "f")
        if pose_count != count * 12:
            raise ValueError("Saved landmark IDs and poses have different lengths.")
        observations: dict[int, set[int]] = {}
        sizes = {}
        for camera, landmark, size_blob in db.execute("SELECT from_id,to_id,user_data FROM Link WHERE type=8"):
            observations.setdefault(landmark, set()).add(camera)
            if size_blob:
                length, values = unpack(size_blob, 5, "f")
                if length == 1 and values[0] > 0:
                    sizes[landmark] = values[0]
        tags = []
        for index, landmark in enumerate(ids):
            if landmark >= 0 or landmark not in observations:
                continue
            values = poses[index * 12 : (index + 1) * 12]
            tags.append(
                {
                    "id": -landmark,
                    "pose": [list(values[i : i + 4]) for i in (0, 4, 8)] + [[0, 0, 0, 1]],
                    "size_m": sizes.get(landmark),
                    "observations": len(observations[landmark]),
                }
            )
        return sorted(tags, key=lambda tag: tag["id"])


def _camera_poses(path: Path) -> dict[str, list[list[float]]]:
    import numpy as np
    from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

    poses = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        values = line.split()
        if len(values) != 9:
            raise ValueError(f"Unexpected native camera-pose format: {path}")
        matrix = np.eye(4)
        matrix[:3, :3] = Rotation.from_quat([float(v) for v in values[4:8]]).as_matrix()
        matrix[:3, 3] = [float(v) for v in values[1:4]]
        poses[values[8]] = matrix.tolist()
    return poses


def extract_frames(database: Path, output: Path, log: Path, poses: Path | None = None) -> dict[str, Any]:
    import cv2
    import numpy as np

    info = database_info(database)
    if not info["saved_poses"]:
        raise ValueError("This database has no saved optimised poses. Merge/reprocess it explicitly first.")
    directory = output / "working" / "extracted"
    directory.mkdir()
    native_command(
        [
            "rtabmap-export",
            "--images_id",
            "--poses_camera",
            "--poses_format",
            "11",
            "--opt",
            "2",
            "--output",
            "capture",
            "--output_dir",
            str(directory),
            str(database),
        ],
        log,
    )
    pose_files = sorted(directory.glob("capture_camera_poses*.txt"))
    if len(pose_files) != 1:
        raise ValueError("Exactly one RGB-D optical camera is supported per frame.")
    camera_poses = _camera_poses(pose_files[0])
    if poses:
        document = read_json(poses)
        if document.get("convention") != "camera_to_world" or document.get("units") != "m":
            raise ValueError("External poses require convention=camera_to_world and units=m.")
        external = document["poses"]
        if set(external) != set(camera_poses):
            raise ValueError("External poses must match the exported camera node IDs exactly.")
        camera_poses = external
    frames, omitted = [], []
    for node_id in info["node_ids"]:
        key = str(node_id)
        rgb = directory / "capture_rgb" / f"{key}.jpg"
        depth = directory / "capture_depth" / f"{key}.png"
        calib = directory / "capture_calib" / f"{key}.yaml"
        confidence = directory / "capture_confidence" / f"{key}.png"
        if key not in camera_poses or not all(p.is_file() for p in [rgb, depth, calib]):
            omitted.append({"id": node_id, "reason": "No exported saved camera pose, RGB, depth or calibration"})
            continue
        transform = np.asarray(camera_poses[key], dtype=float)
        if (
            transform.shape != (4, 4)
            or not np.isfinite(transform).all()
            or not np.allclose(transform[3], [0, 0, 0, 1])
            or not np.allclose(transform[:3, :3].T @ transform[:3, :3], np.eye(3), atol=1e-4)
            or not np.isclose(np.linalg.det(transform[:3, :3]), 1, atol=1e-4)
        ):
            raise ValueError(f"Invalid rigid camera pose for node {key}")
        calibration = _calibration(calib)
        d = cv2.imread(str(depth), cv2.IMREAD_UNCHANGED)
        colour = cv2.imread(str(rgb))
        if d is None or d.dtype != np.uint16 or d.ndim != 2 or colour is None:
            raise ValueError(f"Expected RGB and millimetre uint16 depth for node {key}")
        if colour.shape[:2] != (calibration["height"], calibration["width"]):
            raise ValueError(f"RGB dimensions differ from calibration for node {key}")
        if not np.isclose(d.shape[1] / colour.shape[1], d.shape[0] / colour.shape[0]):
            raise ValueError(f"RGB/depth aspect ratios differ for node {key}; registration required.")
        frames.append(
            {
                "id": node_id,
                "rgb": str(rgb.relative_to(output)),
                "depth": str(depth.relative_to(output)),
                "confidence": str(confidence.relative_to(output)) if confidence.is_file() else None,
                "depth_width": d.shape[1],
                "depth_height": d.shape[0],
                **calibration,
            }
        )
    if not frames:
        raise ValueError("No complete RGB-D frames with saved camera poses were exported.")
    write_json(
        output / "frames.json",
        {
            "database": str(database.relative_to(output)),
            "depth_scale": 1000,
            "registered_depth": True,
            "frames": frames,
            "omitted": omitted,
        },
    )
    write_json(
        output / "poses.json",
        {
            "convention": "camera_to_world",
            "units": "m",
            "poses": {str(f["id"]): camera_poses[str(f["id"])] for f in frames},
        },
    )
    return {
        "included_frames": len(frames),
        "omitted": omitted,
        "confidence_frames": sum(bool(f["confidence"]) for f in frames),
    }


def process_scan(
    inputs: list[Path],
    output: Path,
    settings: ScanSettings,
    poses: Path | None = None,
    alignment: Path | None = None,
    measurements: Path | None = None,
) -> Path:
    """Process captures offline; reusable by a future API subprocess entry point."""
    output = output.resolve()
    if not inputs or any(not p.is_file() or p.suffix.lower() != ".db" for p in inputs):
        raise ValueError("Supply one or more existing RTAB-Map .db files.")
    if len({path.resolve() for path in inputs}) != len(inputs):
        raise ValueError("The same input database was supplied more than once.")
    if any(p.resolve().is_relative_to(output) for p in inputs):
        raise ValueError("Input databases must be outside the output directory.")
    if poses and (not poses.is_file() or poses.resolve().is_relative_to(output)):
        raise ValueError("External poses must be an existing file outside the output directory.")
    infos = [database_info(path) for path in inputs]
    for tool in ["rtabmap-export"] + (["rtabmap-reprocess"] if len(inputs) > 1 or settings.tag_family else []):
        if not shutil.which(tool):
            raise ValueError(f"{tool} is not installed or is not on PATH.")
    output.mkdir(parents=True, exist_ok=False)
    working = output / "working"
    working.mkdir()
    log = output / "processing.log"
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "name": output.name,
        "units": "m",
        "frame": "scan",
        "measured": False,
        "settings": settings.model_dump(),
        "inputs": [],
        "stages_seconds": {},
    }

    def stage(name: str, action: Callable[[], Any]) -> Any:
        print(f"[{name}]", flush=True)
        stage_start = time.monotonic()
        with log.open("a") as stream:
            stream.write(f"\n[{name}]\n")
        try:
            result = action()
        except Exception as error:
            with log.open("a") as stream:
                stream.write(f"FAILED {name}: {error}\n")
            raise RuntimeError(f"{name} failed: {error}. Run retained at {output}") from error
        manifest["stages_seconds"][name] = round(time.monotonic() - stage_start, 3)
        return result

    copies = []
    if measurements is not None:
        from campervan.scan_measurements import read_measurements

        manifest["tag_layout_id"] = read_measurements(measurements).tag_layout_id
    for index, (source, info) in enumerate(zip(inputs, infos, strict=True)):
        manifest["inputs"].append(
            {
                "path": str(source.resolve()),
                "sha256": file_hash(source),
                "version": info["version"],
                "sessions": info["sessions"],
            }
        )
        destination = working / f"input-{index}.db"
        shutil.copy2(source, destination)
        copies.append(destination)
    write_json(working / "request.json", manifest)
    manifest["versions"] = stage(
        "Native versions",
        lambda: subprocess.check_output(["rtabmap-export", "--version"], text=True, stderr=subprocess.STDOUT),
    )
    if len(copies) > 1 or settings.tag_family:
        if not re.search(r"With g2o:\s+true", manifest["versions"]):
            raise RuntimeError("Multi-session processing requires an RTAB-Map build with g2o enabled.")
        database = working / "merged.db"
        command = ["rtabmap-reprocess", "-abort_disconnected_sessions", "--Optimizer/Strategy", "1"]
        if settings.tag_family:
            assert settings.tag_size_mm is not None  # Validated as a pair by ScanSettings.
            command += [
                "--RGBD/MarkerDetection",
                "true",
                "--Marker/Dictionary",
                "20",
                "--Marker/Length",
                str(settings.tag_size_mm / 1000),
            ]
        command += [";".join(str(p) for p in copies), str(database)]
        stage("Merge sessions / detect tags (g2o)", lambda: native_command(command, log))
        manifest["pose_source"] = "rtabmap_merge_g2o" if len(copies) > 1 else "rtabmap_reprocess_g2o"
    else:
        database = copies[0]
        manifest["pose_source"] = "saved_camera_poses"
    if poses:
        manifest["pose_source"] = "external_camera_poses"
        manifest["external_poses"] = {"path": str(poses.resolve()), "sha256": file_hash(poses)}
    manifest["frames"] = stage("Extract RGB-D and cameras", lambda: extract_frames(database, output, log, poses))
    # Saved landmarks cannot be reused with independently corrected external camera poses.
    manifest["tags"] = [] if poses else stage("Read saved tag poses", lambda: saved_tags(database))
    manifest["tag_note"] = (
        "Saved tags omitted: external camera poses require correspondingly corrected tag poses."
        if poses
        else "Saved tag estimates in the scan frame; not surveyed reference positions."
    )
    if poses is None:
        from campervan.scan_graph import ensure_graph

        stage("Export original graph observations", lambda: ensure_graph(output))
    if alignment is not None:
        from campervan.scan_alignment import TagAlignment, tag_alignment

        definition = TagAlignment.model_validate(read_json(alignment))
        manifest["alignment"] = stage(
            "Align reference axes from tags", lambda: tag_alignment(manifest["tags"], definition)
        )
        write_json(output / "alignment.json", manifest["alignment"])
        if manifest["alignment"]["status"] != "aligned":
            print(f"Reference axes unavailable: {manifest['alignment']['reason']}", flush=True)
    publish_reconstruction(output, manifest, settings, stage)
    print(
        f"Completed {output}: {manifest['frames']['included_frames']} frames, {manifest['elapsed_seconds']:.1f}s",
        flush=True,
    )
    return output / "run.json"


def publish_reconstruction(
    output: Path,
    manifest: dict[str, Any],
    settings: ScanSettings,
    stage: Callable[[str, Callable[[], Any]], Any],
) -> Path:
    """Publish the shared Open3D/texture stages for original and corrected reconstructions."""
    from campervan.scan_reconstruction import bake_colour_texture, reconstruct

    log = output / "processing.log"
    manifest["geometry"] = stage(
        "Open3D fusion and cleanup",
        lambda: reconstruct(output / "frames.json", output / "poses.json", output, settings),
    )
    colour_assets = stage(
        "Bake colour texture",
        lambda: bake_colour_texture(
            output / "mesh.ply", output / "colour", settings.texture_size, settings.uv_partitions
        ),
    )
    manifest["layers"] = [
        {"id": "cloud", "label": "Cloud", "asset": "cloud.ply", "kind": "cloud"},
        {"id": "mesh", "label": "Coloured mesh", "asset": "mesh.ply", "kind": "mesh"},
        {"id": "colour", "label": "Baked colour", "asset": "colour/mesh.obj", "kind": "obj"},
    ]
    assets = [output / "cloud.ply", output / "mesh.ply", *colour_assets]
    if settings.texture_mode == "photo":
        from campervan.scan_texturing import texture_photos

        try:
            photo_assets = stage("Photo texture", lambda: texture_photos(output, settings, log))
        except RuntimeError as error:
            # A completed Open3D result remains inspectable when the optional texturer fails.
            manifest["photo_error"] = str(error)
            manifest["assets"] = [str(path.relative_to(output)) for path in assets]
            manifest["elapsed_seconds"] = round(sum(manifest["stages_seconds"].values()), 3)
            write_json(output / "run.json", manifest)
            raise
        assets += photo_assets
        manifest["layers"].append({"id": "photo", "label": "Photo texture", "asset": "photo/mesh.obj", "kind": "obj"})
        manifest["photo_tool_version"] = next(
            (line.strip() for line in log.read_text().splitlines() if "OpenMVS" in line and "v2." in line),
            "See processing.log",
        )
    manifest["assets"] = [str(path.relative_to(output)) for path in assets]
    manifest["elapsed_seconds"] = round(sum(manifest["stages_seconds"].values()), 3)
    write_json(output / "run.json", manifest)
    return output / "run.json"


def completed_scans(directory: Path = SCAN_RUNS) -> list[dict[str, Any]]:
    """Only published manifests and their public assets are discoverable."""
    runs = []
    for path in sorted(directory.glob("*/run.json")):
        if path.parent.resolve().parent != directory.resolve():
            continue
        try:
            data = read_json(path)
            if data["schema_version"] != 1:
                continue
            runs.append(
                {
                    "id": path.parent.name,
                    "name": data["name"],
                    "bytes": 0,
                    "geometry": data["geometry"],
                    "layers": data["layers"],
                    "measured": data["measured"],
                    "tags": data.get("tags", []),
                    "tag_note": data.get("tag_note", "This run has no exported tag poses."),
                    "alignment": data.get("alignment"),
                    "tag_layout_id": data.get("tag_layout_id"),
                    "created_at": data.get("created_at"),
                    "input_filenames": [Path(item["path"]).name for item in data.get("inputs", [])],
                    "pose_source": data.get("pose_source"),
                    "settings": data.get("settings", {}),
                    "frame_count": data.get("frames", {}).get("included_frames"),
                    "analysis_id": data.get("analysis_id"),
                    "source_run_id": data.get("source_run_id"),
                    "reference_run_id": data.get("reference_run_id"),
                }
            )
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return runs


def scan_manifest(run_id: str, directory: Path = SCAN_RUNS) -> dict[str, Any]:
    run = (directory / run_id).resolve()
    if run.parent != directory.resolve():
        raise ValueError("Unknown scan run.")
    manifest: dict[str, Any] = read_json(run / "run.json")
    return manifest


def scan_asset(run_id: str, asset: str, directory: Path = SCAN_RUNS) -> Path:
    manifest = scan_manifest(run_id, directory)
    run = (directory / run_id).resolve()
    path = (run / asset).resolve()
    if asset not in manifest["assets"] or not path.is_relative_to(run) or not path.is_file():
        raise ValueError("Unknown scan asset.")
    return path


def delete_scan_result(key: str, previews: Path, directory: Path = SCAN_RUNS) -> None:
    """Delete one published result, never follow a result link or delete source databases."""
    kind, _, identifier = key.partition(":")
    if not identifier or identifier in {".", ".."} or Path(identifier).name != identifier:
        raise ValueError("Invalid scan result identifier.")
    base = (directory if kind == "run" else previews).resolve()
    path = base / identifier
    if kind not in {"run", "preview"} or path.is_symlink() or path.resolve().parent != base:
        raise ValueError("Invalid scan result path.")
    if not path.exists():
        return  # An unavailable result can still have its library preferences removed.
    if kind == "preview":
        if path.suffix != ".ply" or not path.is_file():
            raise ValueError("Only a preview PLY can be deleted here.")
        path.unlink()
    else:
        if scan_manifest(identifier, directory).get("schema_version") != 1:
            raise ValueError("Only a published scan result can be deleted here.")
        shutil.rmtree(path)
