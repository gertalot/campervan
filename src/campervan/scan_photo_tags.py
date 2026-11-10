"""Locate printed tag corners in an undistorted photographic reconstruction."""

from itertools import combinations
from math import isfinite
from pathlib import Path
from typing import Any

from campervan.scans import write_json


def _triangulate_corner(
    observations: list[dict[str, Any]], corner: int, max_reprojection: float, min_angle_deg: float
) -> dict[str, Any]:
    import numpy as np
    import pycolmap

    active = []
    rejected = []
    result: dict[str, Any] = {"index": corner, "status": "unsupported", "support_image_ids": []}
    for observation in observations:
        pixel = observation["pixels"][corner]
        ray_xy = observation["camera"].cam_from_img(pixel)
        if ray_xy is None or not np.isfinite(ray_xy).all():
            rejected.append({"image_id": observation["image_id"], "reason": "Corner unprojection failed."})
            continue
        ray = np.append(ray_xy, 1.0)
        active.append({**observation, "pixel": pixel, "ray": ray / np.linalg.norm(ray)})

    # Filter observations in pixel space and retriangulate the remaining track.
    # No metre-valued monocular pose enters this arbitrary-scale reconstruction.
    while len(active) >= 2:
        try:
            point = pycolmap.triangulate_multi_view_point(
                [observation["camera_from_world"] for observation in active],
                np.asarray([observation["ray"] for observation in active]),
            )
        except (ValueError, RuntimeError) as error:
            result["reason"] = f"Corner triangulation failed: {error}"
            break
        if point is None or not np.isfinite(point).all():
            result["reason"] = "Corner triangulation failed or returned nonfinite coordinates."
            break
        point = np.asarray(point).reshape(3)
        result["point_arbitrary"] = point.tolist()
        retained = []
        residuals = []
        for observation in active:
            pose = observation["camera_from_world"]
            camera_point = pose[:, :3] @ point + pose[:, 3]
            rejection = None
            residual = None
            if not np.isfinite(camera_point).all() or camera_point[2] <= 0:
                rejection = "Triangulated corner is nonfinite or behind the camera."
            else:
                pixel = observation["camera"].img_from_cam(camera_point)
                if pixel is None or not np.isfinite(pixel).all():
                    rejection = "Corner reprojection failed."
                else:
                    residual = float(np.linalg.norm(pixel - observation["pixel"]))
                    if not isfinite(residual) or residual > max_reprojection:
                        rejection = "Corner reprojection exceeds the mapper threshold."
            if rejection:
                rejection_record: dict[str, Any] = {"image_id": observation["image_id"], "reason": rejection}
                if residual is not None and isfinite(residual):
                    rejection_record["reprojection_error_px"] = residual
                rejected.append(rejection_record)
            else:
                retained.append(observation)
                residuals.append({"image_id": observation["image_id"], "error_px": residual})
        if len(retained) != len(active):
            active = retained
            continue
        angle = max(
            float(np.degrees(pycolmap.calculate_triangulation_angle(a["centre"], b["centre"], point)))
            for a, b in combinations(active, 2)
        )
        result["max_triangulation_angle_deg"] = angle if isfinite(angle) else None
        result["reprojection_errors"] = residuals
        if not isfinite(angle) or angle < min_angle_deg:
            result["reason"] = "Corner track has insufficient triangulation angle."
            break
        result.update(
            status="supported",
            reason=None,
            support_image_ids=[observation["image_id"] for observation in active],
        )
        break
    else:
        result["reason"] = "Corner needs at least two geometrically supported registered views."
    result["rejected_observations"] = rejected
    return result


def _tag_pose(corners: Any) -> Any:
    import numpy as np

    # OpenCV / RTAB-Map: TL, TR, BR, BL have tag coordinates
    # (-x,+y), (+x,+y), (+x,-y), (-x,-y); +z points out of the print.
    x = corners[1] - corners[0] + corners[2] - corners[3]
    y = corners[0] - corners[3] + corners[1] - corners[2]
    x_length = float(np.linalg.norm(x))
    if not isfinite(x_length) or x_length <= 0:
        return None
    x /= x_length
    y -= x * float(x @ y)
    y_length = float(np.linalg.norm(y))
    if not isfinite(y_length) or y_length <= 0:
        return None
    y /= y_length
    pose = np.eye(4)
    pose[:3, :3] = np.column_stack((x, y, np.cross(x, y)))
    pose[:3, 3] = np.mean(corners, axis=0)
    return pose


def localise_photo_tags(
    model: Any, image_sources: dict[str, Any], tag_family: str, tag_size_mm: float, output: Path
) -> dict[str, Any]:
    """Return metric tag poses and scale without modifying the supplied COLMAP model.

    ``image_directory`` contains the exact undistorted images used by ``model``;
    ``images`` contains their COLMAP-relative ``name`` and original provenance.
    ``tag_size_mm`` is the configured black-square side, excluding white border.
    Support evidence remains in the original, arbitrary COLMAP coordinate frame.
    The caller applies ``scale.factor`` to the reconstruction once before MVS.
    """
    import cv2
    import numpy as np
    import pycolmap

    if tag_family != "36h11":
        raise ValueError(f"Unsupported photographic tag family: {tag_family}")
    if not isfinite(tag_size_mm) or tag_size_mm <= 0:
        raise ValueError("Printed tag black-square size must be positive and finite.")
    image_directory = Path(image_sources["image_directory"])
    sources = {source["name"]: source for source in image_sources["images"]}
    options = pycolmap.IncrementalMapperOptions()
    max_reprojection = float(options.filter_max_reproj_error)
    min_angle = float(options.filter_min_tri_angle)
    detector = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11))
    images = []
    detections: dict[int, list[dict[str, Any]]] = {}
    tracks: dict[int, list[dict[str, Any]]] = {}

    for image_id in sorted(model.reg_image_ids()):
        image = model.images[image_id]
        camera = model.cameras[image.camera_id]
        record: dict[str, Any] = {
            "image_id": image_id,
            "name": image.name,
            "source": sources.get(image.name),
            "detection_count": 0,
        }
        images.append(record)
        pixels = cv2.imread(str(image_directory / image.name), cv2.IMREAD_GRAYSCALE)
        if pixels is None:
            record["reason"] = "Cannot read registered undistorted image for tag detection."
            continue
        if pixels.shape != (camera.height, camera.width):
            record["reason"] = "Undistorted image dimensions disagree with its COLMAP camera."
            continue
        marker_corners, marker_ids, _ = detector.detectMarkers(pixels)
        if marker_ids is None:
            continue
        record["detection_count"] = len(marker_ids)
        ids = marker_ids.flatten().tolist()
        pose = np.asarray(image.cam_from_world().matrix())
        centre = np.asarray(image.projection_center()).reshape(3)
        for tag_id, corners in zip(ids, marker_corners, strict=True):
            corners = np.asarray(corners, dtype=float).reshape(4, 2)
            # COLMAP locates the top-left pixel centre at (0.5, 0.5).
            colmap_pixels = corners + 0.5
            detection: dict[str, Any] = {
                "image_id": image_id,
                "name": image.name,
                "corners_opencv": corners.tolist(),
                "corners_colmap": colmap_pixels.tolist(),
            }
            detections.setdefault(tag_id, []).append(detection)
            if ids.count(tag_id) > 1:
                detection["reason"] = "Repeated tag ID in one image makes corner correspondence ambiguous."
                continue
            tracks.setdefault(tag_id, []).append(
                {
                    "image_id": image_id,
                    "camera": camera,
                    "camera_from_world": pose,
                    "centre": centre,
                    "pixels": colmap_pixels,
                }
            )

    supported = []
    tag_records = []
    ratios = []
    size_m = tag_size_mm / 1000
    for tag_id, tag_detections in sorted(detections.items()):
        corners = [
            _triangulate_corner(tracks.get(tag_id, []), corner, max_reprojection, min_angle) for corner in range(4)
        ]
        tag_record: dict[str, Any] = {
            "id": tag_id,
            "status": "Detected but not located",
            "reason": "All four tag corners need supported triangulation.",
            "detections": tag_detections,
            "corners": corners,
        }
        tag_records.append(tag_record)
        if any(corner["status"] != "supported" for corner in corners):
            continue
        points = np.asarray([corner["point_arbitrary"] for corner in corners])
        sides = np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1)
        pose = _tag_pose(points)
        if pose is None or not np.isfinite(pose).all() or not np.isfinite(sides).all() or np.any(sides <= 0):
            tag_record["reason"] = "Triangulated tag corners do not define a finite nondegenerate tag pose."
            continue
        tag_ratios = size_m / sides
        if not np.isfinite(tag_ratios).all() or np.any(tag_ratios <= 0):
            tag_record["reason"] = "Triangulated tag sides do not define finite positive scale ratios."
            continue
        ratios.extend(tag_ratios.tolist())
        support_ids = sorted({image_id for corner in corners for image_id in corner["support_image_ids"]})
        tag_record.update(
            status="Located",
            reason=None,
            side_lengths_arbitrary=sides.tolist(),
            pose_arbitrary=pose.tolist(),
            support_image_ids=support_ids,
        )
        supported.append({"id": tag_id, "pose": pose.tolist(), "size_m": size_m, "observations": len(support_ids)})

    factor = float(np.median(ratios)) if ratios else None
    scale = {
        "status": "metric" if factor is not None else "unscaled",
        "factor": factor,
        "source": "printed_apriltag_size",
        "supporting_tag_ids": [tag["id"] for tag in supported],
        "reason": None if factor is not None else "No detected tag has four geometrically supported corners.",
    }
    tags = []
    if factor is not None:
        for tag in supported:
            pose = np.asarray(tag["pose"])
            pose[:3, 3] *= factor
            tags.append({**tag, "pose": pose.tolist()})
    support_asset = "tag-support.json"
    write_json(
        output / support_asset,
        {
            "coordinate_frame": "unscaled_colmap",
            "tag_family": tag_family,
            "black_square_size_m": size_m,
            "corner_order": ["top_left", "top_right", "bottom_right", "bottom_left"],
            "opencv_to_colmap_pixel_offset": [0.5, 0.5],
            "thresholds": {"filter_max_reproj_error": max_reprojection, "filter_min_tri_angle": min_angle},
            "scale": scale,
            "images": images,
            "tags": tag_records,
        },
    )
    return {"tags": tags, "scale": scale, "support_asset": support_asset}
