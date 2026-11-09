"""Shared observed-depth projection for scene-recognition experiments."""

from pathlib import Path

import cv2
import numpy as np


def observed_points(run: Path, frame: dict, pose: np.ndarray, depth_scale: float,
                    confidence_min: int = 50, depth_max: float = 4) -> tuple[np.ndarray, np.ndarray]:
    depth = cv2.imread(str(run / frame["depth"]), cv2.IMREAD_UNCHANGED)
    if depth is None:
        raise ValueError(f"Missing depth for frame {frame['id']}")
    h, w = depth.shape
    z = depth.astype(float) / depth_scale
    valid = (z > 0) & (z < depth_max)
    if frame.get("confidence"):
        confidence = cv2.imread(str(run / frame["confidence"]), cv2.IMREAD_UNCHANGED)
        if confidence is None:
            raise ValueError(f"Missing depth confidence for frame {frame['id']}")
        valid &= confidence >= confidence_min
    k = np.asarray(frame["intrinsics"]).reshape(3, 3).copy()
    k[0] *= w / frame["width"]
    k[1] *= h / frame["height"]
    y, x = np.indices((h, w))
    camera = np.stack([(x-k[0, 2])*z/k[0, 0], (y-k[1, 2])*z/k[1, 1], z], axis=-1)
    return camera @ pose[:3, :3].T + pose[:3, 3], valid


def sample_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    return cv2.resize(mask.astype(np.uint8), (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)


def visible_box(points: np.ndarray, frame: dict, pose: np.ndarray, world: np.ndarray,
                valid: np.ndarray, tolerance: float) -> tuple[list[float], int] | None:
    """Project only points supported by this frame's measured depth, not through occluders."""
    camera = (points - pose[:3, 3]) @ pose[:3, :3]
    h, w = valid.shape
    k = np.asarray(frame["intrinsics"]).reshape(3, 3).copy()
    k[0] *= w / frame["width"]
    k[1] *= h / frame["height"]
    front = camera[:, 2] > 0
    indices = np.flatnonzero(front)
    if not len(indices):
        return None
    projected = camera[indices] @ k.T
    pixels = np.rint(projected[:, :2] / projected[:, 2:]).astype(int)
    inside = (pixels[:, 0] >= 0) & (pixels[:, 0] < w) & (pixels[:, 1] >= 0) & (pixels[:, 1] < h)
    indices, pixels = indices[inside], pixels[inside]
    if not len(indices):
        return None
    x, y = pixels.T
    keep = valid[y, x] & (np.linalg.norm(points[indices] - world[y, x], axis=1) <= tolerance)
    pixels = pixels[keep]
    if len(pixels) < 20:
        return None
    lo, hi = pixels.min(0), pixels.max(0) + 1
    scale = np.array([frame["width"]/w, frame["height"]/h])
    return [*(lo*scale).tolist(), *(hi*scale).tolist()], len(pixels)
