"""Photographic camera reconstruction and native OpenMVS geometry, independent of LiDAR fusion."""

import re
import shutil
import time
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from campervan.scans import native_command, read_json, write_json


class PhotographicSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    num_threads: int = Field(default=4, ge=1, le=4)
    target_triangles: int = Field(default=500000, gt=0)
    texture_size: int = Field(default=4096, ge=256, le=16384)


def _stage(name: str, action: Any, *, log: Path, timings: dict[str, float]) -> Any:
    print(f"[{name}]", flush=True)
    started = time.monotonic()
    try:
        return action()
    except Exception as error:
        # Native diagnostics stay in the log and the concrete last lines reach the shared error UI.
        detail = ""
        if isinstance(error, RuntimeError) and log.is_file():
            lines = log.read_text(errors="replace").splitlines()
            detail = " · " + " | ".join(lines[-5:]) if lines else ""
        raise RuntimeError(f"{name}: {error}{detail}") from error
    finally:
        timings[name] = round(time.monotonic() - started, 3)


def process_photos(request: dict[str, Any], output: Path) -> Path:
    import numpy as np
    import pycolmap

    from campervan.scan_photo_tags import localise_photo_tags
    from campervan.scan_photos import prepare_photo_inputs
    from campervan.scan_texturing import _tool

    settings = PhotographicSettings.model_validate(request["settings"])
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    working = output / "working"
    working.mkdir()
    write_json(output / "request.json", request)
    log = output / "processing.log"
    timings: dict[str, float] = {}

    stage = partial(_stage, log=log, timings=timings)

    prepared = stage("Prepare photographic inputs", lambda: prepare_photo_inputs(request["inputs"], output, log))
    image_dir = Path(prepared["image_directory"])
    images = prepared["images"]
    if len(images) < 2:
        raise ValueError("Camera reconstruction needs overlapping photographs from at least two viewpoints.")
    database = working / "features.db"
    extraction = pycolmap.FeatureExtractionOptions(num_threads=settings.num_threads)
    groups: dict[str, list[dict]] = {}
    for image in images:
        groups.setdefault(str(Path(image["name"]).parent), []).append(image)

    def extract() -> None:
        for index, (_, group) in enumerate(sorted(groups.items()), 1):
            print(f"[Extract features: camera group {index}/{len(groups)}]", flush=True)
            reader = pycolmap.ImageReaderOptions()
            calibration = group[0].get("calibration")
            if calibration:
                k = calibration.get("intrinsics")
                if k:
                    # Exported RTAB RGB uses OpenCV pixel centres; COLMAP uses +0.5 centres.
                    reader.camera_model = "OPENCV"
                    reader.camera_params = ",".join(map(str, [k[0], k[4], k[2] + .5, k[5] + .5, 0, 0, 0, 0]))
            pycolmap.extract_features(database, image_dir, image_names=[image["name"] for image in group],
                                      camera_mode=pycolmap.CameraMode.PER_FOLDER, reader_options=reader,
                                      extraction_options=extraction, device=pycolmap.Device.cpu)

    stage("Extract photographic features", extract)
    stage("Match photographs and verify geometry", lambda: pycolmap.match_exhaustive(
        database, matching_options=pycolmap.FeatureMatchingOptions(num_threads=settings.num_threads),
        device=pycolmap.Device.cpu))
    sparse_dir = working / "sparse"
    sparse_dir.mkdir()
    mapper = pycolmap.IncrementalPipelineOptions(num_threads=settings.num_threads)
    mapper.mapper.num_threads = settings.num_threads
    models = stage("Reconstruct cameras and bundle adjust", lambda: pycolmap.incremental_mapping(
        database, image_dir, sparse_dir, options=mapper,
        next_image_callback=lambda: print("[Camera registered; refining photographic reconstruction]", flush=True)))
    if not models:
        raise RuntimeError("Camera reconstruction found no connected component. Inspect overlap and image sharpness.")
    component_id, model = min(models.items(), key=lambda item: (
        -item[1].num_reg_images(), -item[1].num_points3D(), item[0]))
    components = [{"id": key, "registered_images": value.num_reg_images(), "sparse_points": value.num_points3D()}
                  for key, value in sorted(models.items())]
    selected_dir = working / "selected-model"
    selected_dir.mkdir()
    model.write(selected_dir)
    dense_dir = working / "colmap-dense"
    stage("Undistort registered photographs", lambda: pycolmap.undistort_images(
        dense_dir, selected_dir, image_dir, output_type="COLMAP", num_threads=settings.num_threads))
    undistorted = pycolmap.Reconstruction(dense_dir / "sparse")
    support = stage("Locate photographic tags and establish scale", lambda: localise_photo_tags(
        undistorted, {**prepared, "image_directory": str(dense_dir / "images")},
        request["tag_family"], request["tag_size_mm"], output))
    scale = support["scale"]
    if scale["status"] == "metric":
        similarity = pycolmap.Sim3d(scale["factor"], pycolmap.Rotation3d(), np.zeros(3))
        undistorted.transform(similarity)
        model.transform(similarity)
        undistorted.write(dense_dir / "sparse")
        model.write(selected_dir)
    registered = {image.name for image in undistorted.images.values() if image.has_pose}
    poses = {}
    frame_records = []
    by_name = {image["name"]: image for image in images}
    for image in undistorted.images.values():
        if not image.has_pose:
            continue
        world_camera = np.eye(4)
        world_camera[:3, :] = image.cam_from_world().matrix()
        poses[str(image.image_id)] = np.linalg.inv(world_camera).tolist()
        camera = undistorted.cameras[image.camera_id]
        frame_records.append({**by_name[image.name], "id": image.image_id,
                              "rgb": str((dense_dir / "images" / image.name).relative_to(output)),
                              "width": camera.width, "height": camera.height,
                              "intrinsics": camera.calibration_matrix().ravel().tolist(), "depth_source": "photographic"})
    write_json(output / "poses.json", {"convention": "camera_to_world", "units": "m" if scale["status"] == "metric"
                                     else "arbitrary", "poses": poses})
    write_json(output / "frames.json", {"frames": frame_records, "depth_source": "photographic",
                                       "note": "Native image-derived depth maps retained in working/; no original LiDAR."})

    scene = working / "scene.mvs"
    threads = ["--max-threads", str(settings.num_threads)]

    def native(tool: str, arguments: list[str]) -> None:
        native_command([_tool(tool), *arguments, *threads, "--archive-type", "2"], log, cwd=working)

    stage("Import photographic model", lambda: native("InterfaceCOLMAP", [
        "-i", str(dense_dir), "-o", str(scene), "--image-folder", str(dense_dir / "images")]))
    largest = max(max(frame["width"], frame["height"]) for frame in frame_records)
    dense = working / "dense.mvs"
    stage("Dense photographic reconstruction", lambda: native("DensifyPointCloud", [
        "-i", str(scene), "-o", str(dense), "--resolution-level", "0", "--max-resolution", str(largest)]))
    mesh_scene = working / "surface.mvs"
    stage("Mesh photographic depth", lambda: native("ReconstructMesh", [
        "-i", str(dense), "-o", str(mesh_scene), "--decimate", "1", "--close-holes", "0"]))
    refined_scene = working / "refined.mvs"
    stage("Refine photographic surface", lambda: native("RefineMesh", [
        "-i", str(mesh_scene), "-o", str(refined_scene), "--resolution-level", "0", "--decimate", "1",
        "--close-holes", "0", "--ensure-edge-size", "0"]))
    return publish_photos(request, output, support, components, component_id, timings)


def publish_photos(request: dict[str, Any], output: Path, support: dict[str, Any], components: list[dict],
                   component_id: int, timings: dict[str, float]) -> Path:
    """Publish the completed photographic surface through the existing result manifest contract."""
    import open3d as o3d
    import pycolmap
    from campervan.scan_texturing import texture_scene

    settings = PhotographicSettings.model_validate(request["settings"])
    working = output / "working"
    log = output / "processing.log"
    stage = partial(_stage, log=log, timings=timings)
    prepared = read_json(output / "image_sources.json")
    images = prepared["images"]
    frame_records = read_json(output / "frames.json")["frames"]
    registered = {frame["name"] for frame in frame_records}
    largest = max(max(frame["width"], frame["height"]) for frame in frame_records)
    scale = support["scale"]
    refined_scene = working / "refined.mvs"
    dense = working / "dense.mvs"
    full = working / "full-mesh.ply"
    shutil.copyfile(refined_scene.with_suffix(".ply"), full)
    shutil.copyfile(dense.with_suffix(".ply"), output / "cloud.ply")
    mesh = o3d.io.read_triangle_mesh(str(full))
    if not len(mesh.triangles):
        raise RuntimeError("Photographic meshing produced no triangles.")
    full_count = len(mesh.triangles)
    # A display copy is the only simplified asset; the retained master and texture source stay intact.
    if full_count > settings.target_triangles:
        mesh = stage("Create simplified viewing copy", lambda: mesh.simplify_quadric_decimation(settings.target_triangles))
    mesh.compute_vertex_normals()
    if not o3d.io.write_triangle_mesh(str(output / "mesh.ply"), mesh):
        raise RuntimeError("Could not save the photographic viewing mesh.")
    manifest = {
        "schema_version": 1, "created_at": datetime.now(UTC).isoformat(), "name": request["name"],
        "purpose": "photographic", "units": "m" if scale["status"] == "metric" else "arbitrary", "scale": scale,
        "settings": settings.model_dump(), "tag_layout_id": request["tag_layout_id"], "measured": False,
        "inputs": request["inputs"], "tags": support["tags"],
        "tag_note": "Photographically triangulated tags; unsupported detections remain in tag support details.",
        "pose_source": "photographic_bundle_adjustment", "stages_seconds": timings,
        "frames": {"included_frames": len(frame_records)},
        "geometry": {"full_triangles": full_count, "triangles": len(mesh.triangles), "vertices": len(mesh.vertices),
                     "backend": "COLMAP/OpenMVS photographic stereo"},
        "layers": [{"id": "cloud", "label": "Photographic cloud", "asset": "cloud.ply", "kind": "cloud"},
                   {"id": "mesh", "label": "Photographic mesh", "asset": "mesh.ply", "kind": "mesh"}],
        "assets": ["cloud.ply", "mesh.ply", "image_sources.json", str(full.relative_to(output)), support["support_asset"]],
        "photo_reconstruction": {"selected_image_count": len(images), "registered_image_count": len(registered),
            "unregistered_image_ids": [image["name"] for image in images if image["name"] not in registered],
            "component_summaries": components, "selected_component_id": component_id,
            "settings": {**settings.model_dump(), "matching": "exhaustive", "resolution_level": 0,
                         "max_resolution": largest, "bundle_adjustment": "standard local/global"},
            "versions": {"pycolmap": pycolmap.__version__, "openmvs": next(iter(
                re.findall(r"OpenMVS[^\n]*v[\d.]+", log.read_text(errors="replace"))), "See processing.log")},
            "tag_support_asset": support["support_asset"],
            "image_sources": images},
    }
    definition = request.get("alignment_definition")
    if definition and scale["status"] == "metric":
        from campervan.scan_alignment import TagAlignment, tag_alignment
        try:
            manifest["alignment"] = tag_alignment(support["tags"], TagAlignment.model_validate(definition))
        except ValueError as error:
            manifest["alignment"] = {"status": "unaligned", "definition": definition, "reason": str(error)}
    else:
        manifest["alignment"] = {"status": "unaligned", "reason": "No supported metric axis definition applied."}

    def save() -> None:
        manifest["elapsed_seconds"] = round(time.time() - (output / "request.json").stat().st_mtime, 3)
        write_json(output / "run.json", manifest)

    try:
        photo_assets = stage("Texture photographic surface", lambda: texture_scene(
            refined_scene, full, output / "photo", settings.texture_size, log, settings.num_threads))
    except (RuntimeError, ValueError, OSError) as error:
        manifest["photo_error"] = str(error)
        save()
        raise
    manifest["assets"] += [str(path.relative_to(output)) for path in photo_assets]
    manifest["layers"].append({"id": "photo", "label": "Photo texture", "asset": "photo/mesh.obj", "kind": "obj"})
    save()
    print(f"[Saved photographic reconstruction: {len(registered)}/{len(images)} photographs]", flush=True)
    return output / "run.json"
