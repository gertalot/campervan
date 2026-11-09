"""Conservative finite tape-segment obstruction and observed-free-space checks."""

from pathlib import Path
from typing import Any

import numpy as np

from campervan.scans import read_json


def assess_segments(run: Path, pairs: list[dict[str, Any]], positions: dict[int, Any], moved: dict[int, float]) -> None:
    import cv2
    import open3d as o3d

    manifest = read_json(run / "run.json")
    voxel = float(manifest["settings"]["voxel_mm"]) / 1000
    tolerance = 2 * voxel
    for pair in pairs:
        pair.update(clearance="unknown", clearance_reason="Insufficient surface/depth evidence.", tolerance_m=tolerance)
    if not (run / "mesh.ply").is_file() or not (run / "frames.json").is_file():
        return
    mesh = o3d.io.read_triangle_mesh(run / "mesh.ply")
    if not len(mesh.triangles):
        return
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(mesh))
    samples: list[Any] = []
    sample_count = 0
    spans = []
    eligible = []
    for pair in pairs:
        a, b = pair["tag_a"], pair["tag_b"]
        if max(moved.get(a, 0), moved.get(b, 0)) > tolerance:
            pair["clearance_reason"] = (
                "Proposed tags moved relative to the original surface. Apply/rebuild before checking clearance."
            )
            continue
        start, finish = positions[a], positions[b]
        delta = finish - start
        length = float(np.linalg.norm(delta))
        if length <= 4 * tolerance:
            pair["clearance_reason"] = "The endpoints are too close for this scan's surface tolerance."
            continue
        direction = delta / length
        u = np.cross(direction, np.eye(3)[int(np.argmin(abs(direction)))])
        u /= np.linalg.norm(u)
        v = np.cross(direction, u)
        start, finish = start + direction * tolerance, finish - direction * tolerance
        rays = np.array(
            [
                np.r_[start + offset, finish - start]
                for offset in [np.zeros(3), voxel * u, -voxel * u, voxel * v, -voxel * v]
            ],
            dtype=np.float32,
        )
        hits = scene.cast_rays(o3d.core.Tensor(rays, dtype=o3d.core.float32, device=o3d.core.Device("CPU:0")))[
            "t_hit"
        ].numpy()
        blocked = (hits > 0) & (hits < 1)
        if blocked.all():
            point = start + float(hits[0]) * (finish - start)
            pair.update(
                clearance="obstructed",
                clearance_reason="Reconstructed surface crosses the straight tape path.",
                hit=point.tolist(),
            )
            continue
        if blocked.any():
            pair["clearance_reason"] = "Nearby clearance rays disagree; the path is near a surface or mesh hole."
            continue
        points = np.linspace(start, finish, max(3, int(length / voxel)))
        lower = sample_count
        sample_count += len(points)
        samples.append(points)
        spans.append((lower, lower + len(points)))
        eligible.append(pair)
    if not samples:
        return
    world = np.concatenate(samples)
    covered = np.zeros(len(world), dtype=bool)
    frames = read_json(run / "frames.json")
    poses = read_json(run / "poses.json")["poses"]
    confidence_min = manifest["settings"]["depth_confidence_min"]
    print("[Check observed free space between tags]", flush=True)
    for frame in frames["frames"]:
        pending = np.flatnonzero(~covered)
        if not len(pending):
            break
        pose = np.asarray(poses[str(frame["id"])])
        camera = (world[pending] - pose[:3, 3]) @ pose[:3, :3]
        front = camera[:, 2] > 0
        if not front.any():
            continue
        depth = cv2.imread(str(run / frame["depth"]), cv2.IMREAD_UNCHANGED)
        if depth is None:
            continue
        h, w = depth.shape
        k = np.asarray(frame["intrinsics"]).reshape(3, 3).copy()
        k[0] *= w / frame["width"]
        k[1] *= h / frame["height"]
        projection = camera @ k.T
        pixels = np.zeros((len(camera), 2), dtype=int)
        pixels[front] = np.rint(projection[front, :2] / projection[front, 2:3]).astype(int)
        valid = front & (pixels[:, 0] >= 0) & (pixels[:, 0] < w) & (pixels[:, 1] >= 0) & (pixels[:, 1] < h)
        offsets = np.flatnonzero(valid)
        x, y = pixels[offsets].T
        measured = depth[y, x] / float(frames["depth_scale"])
        free = (measured > 0) & (camera[offsets, 2] < measured - tolerance)
        if frame.get("confidence"):
            confidence = cv2.imread(str(run / frame["confidence"]), cv2.IMREAD_UNCHANGED)
            if confidence is None:
                continue
            free &= confidence[y, x] >= confidence_min
        covered[pending[offsets[free]]] = True
    for pair, (lower, upper) in zip(eligible, spans, strict=True):
        pair["observed_fraction"] = float(covered[lower:upper].mean())
        if covered[lower:upper].all():
            pair.update(
                clearance="no_obstruction_detected",
                clearance_reason="No mesh hit; free space was observed along this segment. Check hand/tape access.",
            )
        else:
            pair["clearance_reason"] = "No mesh hit, but part of the segment lacks observed free-space coverage."
