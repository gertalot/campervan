"""Open3D RGB-D fusion and portable colour texture baking, in metres."""

from pathlib import Path
from typing import Any

from campervan.scans import ScanSettings, read_json


def clean_manifold_vertices(mesh: Any) -> int:
    """Remove disconnected vertex fans which UVAtlas cannot parameterise."""
    before = len(mesh.triangles)
    mesh.remove_non_manifold_edges()
    bad = list(mesh.get_non_manifold_vertices())
    while bad:
        mesh.remove_vertices_by_index(bad)
        bad = list(mesh.get_non_manifold_vertices())
    mesh.remove_unreferenced_vertices()
    mesh.orient_triangles()
    return before - len(mesh.triangles)


def read_depth_frame(root: Path, frame: dict[str, Any], settings: ScanSettings,
                     exclusion_masks: list[str] | None = None) -> Any:
    """Read original depth pixels; exclusions are nonzero pixels in same-size single-channel masks."""
    import cv2
    import numpy as np

    depth = cv2.imread(str(root / frame["depth"]), cv2.IMREAD_UNCHANGED)
    if depth is None or depth.ndim != 2 or depth.dtype != np.uint16:
        raise ValueError(f"Invalid original depth image for node {frame['id']}")
    if frame.get("confidence") and settings.depth_confidence_min:
        confidence = cv2.imread(str(root / frame["confidence"]), cv2.IMREAD_UNCHANGED)
        if confidence is None or confidence.shape != depth.shape:
            raise ValueError(f"Invalid depth confidence image for node {frame['id']}")
        depth[confidence < settings.depth_confidence_min] = 0
    for asset in exclusion_masks or []:
        path = (root / asset).resolve()
        if Path(asset).is_absolute() or not path.is_relative_to(root.resolve()):
            raise ValueError("Cleanup mask must belong to the source result.")
        mask = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if mask is None or mask.shape != depth.shape:
            raise ValueError(f"Cleanup mask must use original depth pixels for node {frame['id']}")
        depth[mask != 0] = 0
    return depth


def reconstruct(frames_path: Path, poses_path: Path, output: Path, settings: ScanSettings,
                exclusion_masks: dict[str, list[str]] | None = None) -> dict[str, Any]:
    import cv2
    import numpy as np
    import open3d as o3d

    document = read_json(frames_path)
    masks = exclusion_masks if exclusion_masks is not None else document.get("exclusion_masks", {})
    unknown_frames = set(masks) - {str(frame["id"]) for frame in document["frames"]}
    if unknown_frames:
        raise ValueError(f"Cleanup masks reference unavailable frames: {sorted(unknown_frames)}")
    poses = read_json(poses_path)["poses"]
    depth_scale = float(document["depth_scale"])
    # Open3D 0.20's legacy ScalableTSDFVolume rescales metric depth twice (upstream #7592).
    # Use its supported tensor TSDF implementation, with explicit millimetre input units.
    volume = o3d.t.geometry.VoxelBlockGrid(
        attr_names=("tsdf", "weight", "color"),
        attr_dtypes=(o3d.core.float32, o3d.core.float32, o3d.core.float32),
        attr_channels=(o3d.core.SizeVector([1]), o3d.core.SizeVector([1]), o3d.core.SizeVector([3])),
        voxel_size=settings.voxel_mm / 1000,
        block_resolution=16,
        block_count=10000,
        device=o3d.core.Device("CPU:0"),
    )
    truncation = settings.sdf_trunc_mm / settings.voxel_mm
    confidence_frames = 0
    for index, frame in enumerate(document["frames"]):
        rgb = cv2.imread(str(output / frame["rgb"]))
        depth = read_depth_frame(output, frame, settings, masks.get(str(frame["id"])))
        if rgb is None:
            raise ValueError(f"Missing RGB/depth image for node {frame['id']}")
        if frame.get("confidence") and settings.depth_confidence_min:
            confidence_frames += 1
        if not np.any(depth):
            continue
        height, width = depth.shape
        # RTAB-Map exports registered RGB/depth in the same optical frame at different resolutions.
        # Preserve depth samples; resample colour and scale the per-frame intrinsic matrix.
        rgb = cv2.cvtColor(cv2.resize(rgb, (width, height), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        sx, sy = width / frame["width"], height / frame["height"]
        k = frame["intrinsics"]
        intrinsic = o3d.core.Tensor(
            np.array([[k[0] * sx, 0, k[2] * sx], [0, k[4] * sy, k[5] * sy], [0, 0, 1]]),
            dtype=o3d.core.float64,
            device=o3d.core.Device("CPU:0"),
        )
        extrinsic = o3d.core.Tensor(
            np.linalg.inv(np.asarray(poses[str(frame["id"])])), dtype=o3d.core.float64, device=o3d.core.Device("CPU:0")
        )
        depth_image = o3d.t.geometry.Image(o3d.core.Tensor(depth, o3d.core.uint16, o3d.core.Device("CPU:0")))
        colour_image = o3d.t.geometry.Image(o3d.core.Tensor(rgb, o3d.core.uint8, o3d.core.Device("CPU:0")))
        blocks = volume.compute_unique_block_coordinates(
            depth_image, intrinsic, extrinsic, depth_scale, settings.depth_max_m, truncation
        )
        volume.integrate(
            blocks,
            depth_image,
            colour_image,
            intrinsic,
            intrinsic,
            extrinsic,
            depth_scale,
            settings.depth_max_m,
            truncation,
        )
        if index % 50 == 0 or index + 1 == len(document["frames"]):
            print(f"Fused {index + 1}/{len(document['frames'])} frames", flush=True)
    cloud = volume.extract_point_cloud().to_legacy()
    mesh = volume.extract_triangle_mesh().to_legacy()
    if not len(mesh.triangles) or not len(cloud.points):
        raise ValueError("TSDF reconstruction produced empty geometry.")
    mesh.compute_vertex_normals()
    if not o3d.io.write_point_cloud(output / "cloud.ply", cloud):
        raise RuntimeError("Could not write fused cloud.")
    if not o3d.io.write_triangle_mesh(output / "working" / "full-mesh.ply", mesh):
        raise RuntimeError("Could not write full-resolution mesh.")
    before = len(mesh.triangles)
    mesh.remove_duplicated_vertices().remove_duplicated_triangles().remove_degenerate_triangles()
    if settings.min_component_triangles:
        clusters, counts, _ = mesh.cluster_connected_triangles()
        mesh.remove_triangles_by_mask(np.asarray(counts)[np.asarray(clusters)] < settings.min_component_triangles)
    mesh.remove_unreferenced_vertices()
    cleaned = len(mesh.triangles)
    if not cleaned:
        raise ValueError("Cleanup removed the entire mesh; reduce the component threshold.")
    if cleaned > settings.target_triangles:
        mesh = mesh.simplify_quadric_decimation(settings.target_triangles)
    mesh.remove_degenerate_triangles()
    manifold_removed = clean_manifold_vertices(mesh)
    mesh.compute_vertex_normals()
    if not o3d.io.write_triangle_mesh(output / "mesh.ply", mesh):
        raise RuntimeError("Could not write display mesh.")
    print(f"Mesh: {before:,} original → {cleaned:,} cleaned → {len(mesh.triangles):,} display triangles", flush=True)
    return {
        "open3d_version": o3d.__version__,
        "cloud_points": len(cloud.points),
        "full_triangles": before,
        "cleaned_triangles": cleaned,
        "triangles": len(mesh.triangles),
        "vertices": len(mesh.vertices),
        "confidence_filtered_frames": confidence_frames,
        "cleanup_masked_frames": len(masks),
        "cleanup_note": ("Reviewed original-depth-pixel exclusions applied before fusion." if masks else
                         "No reviewed cleanup masks supplied; cleanup context skipped."),
        "depth_resampling": "none",
        "backend": "VoxelBlockGrid CPU",
        "manifold_removed_triangles": manifold_removed,
    }


def bake_colour_texture(mesh_path: Path, output: Path, texture_size: int, uv_partitions: int = 4) -> list[Path]:
    import open3d as o3d

    mesh = o3d.io.read_triangle_mesh(mesh_path)
    if not mesh.is_vertex_manifold() or not mesh.is_edge_manifold():
        raise ValueError("Clean the mesh's non-manifold geometry before generating UVs.")
    if not mesh.has_vertex_colors() or not len(mesh.triangles):
        raise ValueError("A nonempty coloured mesh is required for texture baking.")
    print(f"UV mesh: {len(mesh.triangles):,} manifold triangles", flush=True)
    tensor_mesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    print("Generating UV atlas…", flush=True)
    tensor_mesh.compute_uvatlas(size=texture_size, parallel_partitions=uv_partitions, nthreads=uv_partitions)
    tensor_mesh.vertex["albedo"] = tensor_mesh.vertex.colors
    tensor_mesh.material.set_default_properties()
    print(f"Baking {texture_size}×{texture_size} colour texture…", flush=True)
    tensor_mesh.bake_vertex_attr_textures(texture_size, {"albedo"})
    # PNG stores integer samples; baking returns floating-point [0, 1] colours.
    tensor_mesh.material.texture_maps["albedo"] = tensor_mesh.material.texture_maps["albedo"].to(
        o3d.core.uint8, scale=255.0
    )
    output.mkdir()
    # The tensor writer retains the albedo material; the legacy OBJ writer reads a different texture list.
    if not o3d.t.io.write_triangle_mesh(output / "mesh.obj", tensor_mesh, write_triangle_uvs=True):
        raise RuntimeError("Could not export baked mesh.")
    assets = sorted(path for path in output.iterdir() if path.is_file())
    if not (output / "mesh.mtl").is_file() or not any(p.suffix == ".png" for p in assets):
        raise RuntimeError("Open3D did not export the texture/material sidecars.")
    return assets
