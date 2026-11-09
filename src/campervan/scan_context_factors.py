"""Optional reviewed geometry relationships, evaluated from original RGB-D under current camera poses.

Region support assets are single-channel masks in original depth pixel coordinates (nonzero means support).
They supply associations, not independent point observations. No fitted XYZ is used as a pose prior.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from campervan.scan_graph import GraphDocument
from campervan.scan_reconstruction import read_depth_frame
from campervan.scan_workflow_models import BoundRelationship, SourceBinding, SourcePixel
from campervan.scans import ScanSettings, read_json


@dataclass
class Samples:
    frame_id: str
    key: int
    optical: Any
    pixels: Any
    camera_points: Any

    def world(self, poses: dict[int, Any]) -> Any:
        transform = poses[self.key].matrix() @ self.optical
        return self.camera_points @ transform[:3, :3].T + transform[:3, 3]

    def point_world(self, poses: dict[int, Any], index: int) -> Any:
        transform = poses[self.key].matrix() @ self.optical
        return transform[:3, :3] @ self.camera_points[index] + transform[:3, 3]


def source_support_asset(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("Region support must belong to the original source result.")
    if not path.is_file():
        raise ValueError(f"Region support asset is unavailable: {name}")
    return path


def _plane(points: Any) -> tuple[Any, Any]:
    centre = points.mean(axis=0)
    _, singular, vectors = np.linalg.svd(points - centre, full_matrices=False)
    if len(singular) < 3 or singular[1] <= max(1e-9, singular[0] * 1e-6):
        raise ValueError("Region support cannot define a plane.")
    return centre, vectors[-1] / np.linalg.norm(vectors[-1])


def _samples(source: Path, region: Any, document: dict[str, Any], graph: GraphDocument,
             settings: ScanSettings, key: Callable[[int], int], masks: dict[str, list[str]]) -> list[Samples]:
    import cv2

    frames = {str(frame["id"]): frame for frame in document["frames"]}
    samples = []
    # Union masks within each frame so overlapping support is never counted twice.
    supports: dict[str, list[str]] = {}
    for support in region.support:
        supports.setdefault(support.frame_id, []).append(support.asset)
    for frame_id, assets in supports.items():
        if frame_id not in frames or frame_id not in graph.optical_transforms:
            raise ValueError(f"Region frame {frame_id} lacks original depth or optical calibration.")
        frame = frames[frame_id]
        depth = read_depth_frame(source, frame, settings, masks.get(frame_id))
        selected = np.zeros(depth.shape, dtype=bool)
        for asset in assets:
            support = cv2.imread(str(source_support_asset(source, asset)), cv2.IMREAD_UNCHANGED)
            if support is None or support.shape != depth.shape:
                raise ValueError("Region masks must use original depth pixels without resampling.")
            selected |= support != 0
        z = depth.astype(float) / float(document["depth_scale"])
        selected &= (z > 0) & (z <= settings.depth_max_m) & np.isfinite(z)
        v, u = np.nonzero(selected)
        if not len(u):
            continue
        height, width = depth.shape
        k = frame["intrinsics"]
        sx, sy = width / frame["width"], height / frame["height"]
        fx, fy, cx, cy = k[0] * sx, k[4] * sy, k[2] * sx, k[5] * sy
        if fx <= 0 or fy <= 0:
            raise ValueError("Region frame has invalid original camera intrinsics.")
        points = np.column_stack(((u - cx) * z[v, u] / fx, (v - cy) * z[v, u] / fy, z[v, u]))
        samples.append(Samples(frame_id, key(int(frame_id)), np.asarray(graph.optical_transforms[frame_id]),
                               np.column_stack((u, v)), points))
    if sum(len(sample.camera_points) for sample in samples) < 3:
        raise ValueError("Region has fewer than three valid observed depth samples.")
    return samples


def _matched_point(pixel: SourcePixel, samples: dict[str, list[Samples]]) -> tuple[Samples, int]:
    for sample in samples.get(pixel.region_id, []):
        if sample.frame_id == pixel.frame_id:
            indices = np.flatnonzero(np.all(sample.pixels == pixel.pixel, axis=1))
            if len(indices) == 1:
                return sample, int(indices[0])
    raise ValueError("Matched body pixel is outside the reviewed region's valid original depth support.")


def _residual(relation: BoundRelationship, regions: dict[str, Any], samples: dict[str, list[Samples]],
              initial: dict[int, Any]) -> tuple[Callable[[dict[int, Any]], Any], float]:
    if relation.sigma is None:
        raise ValueError("No explicit relationship tolerance supplied.")
    if len(relation.region_ids) != 2 or len(set(relation.region_ids)) != 2:
        raise ValueError("Relationship needs two distinct reviewed regions.")
    first, second = relation.region_ids
    if not relation.support:
        raise ValueError("No reviewed supporting association references supplied.")

    def points(region_id: str, poses: dict[int, Any]) -> Any:
        return np.concatenate([sample.world(poses) for sample in samples[region_id]])

    if relation.kind in {"parallel", "orthogonal"}:
        if relation.units not in {"rad", "deg"}:
            raise ValueError("Angular relationship tolerance needs rad or deg units.")
        references = [_plane(points(region, initial))[1] for region in (first, second)]

        def angular(poses: dict[int, Any]) -> Any:
            normals = [_plane(points(region, poses))[1] for region in (first, second)]
            normals = [normal if normal @ reference >= 0 else -normal
                       for normal, reference in zip(normals, references, strict=True)]
            return (np.cross(*normals) if relation.kind == "parallel" else
                    np.array([float(normals[0] @ normals[1])]))

        return angular, float(np.deg2rad(relation.sigma) if relation.units == "deg" else relation.sigma)
    if relation.units != "m":
        raise ValueError("Linear relationship tolerance needs metre units.")
    if relation.kind == "above":
        if relation.up_direction is None or np.linalg.norm(relation.up_direction) <= 1e-12:
            raise ValueError("Above requires a reviewed up direction in the original source frame.")
        up = np.asarray(relation.up_direction) / np.linalg.norm(relation.up_direction)

        def above(poses: dict[int, Any]) -> Any:
            upper, _ = _plane(points(first, poses))
            lower, _ = _plane(points(second, poses))
            separation = float((upper - lower) @ up)
            return np.array([max(0.0, relation.minimum_separation_m - separation)])

        return above, relation.sigma
    if relation.kind == "symmetry":
        if any(regions[region].symmetry_scope != "body" or
               any(excluded in regions[region].label.lower() for excluded in ("seat", "window", "opening", "front"))
               for region in (first, second)):
            raise ValueError("Symmetry is restricted to reviewed body support; seats/openings/front are excluded.")
        if len(relation.matched_support) < 3:
            raise ValueError("Symmetry needs at least three explicit matched original body-pixel pairs.")
        pairs = []
        seen: set[tuple[str, str, tuple[int, int]]] = set()
        for match in relation.matched_support:
            if (match.first.region_id, match.second.region_id) != (first, second):
                raise ValueError("Symmetry matches must follow the relationship's two body regions.")
            for pixel in (match.first, match.second):
                identity = (pixel.region_id, pixel.frame_id, pixel.pixel)
                if identity in seen:
                    raise ValueError("Symmetry support pixels must not be counted twice.")
                seen.add(identity)
            pairs.append((_matched_point(match.first, samples), _matched_point(match.second, samples)))

        def symmetry(poses: dict[int, Any]) -> Any:
            left = np.array([sample.point_world(poses, index) for (sample, index), _ in pairs])
            right = np.array([sample.point_world(poses, index) for _, (sample, index) in pairs])
            middle = (left + right) / 2
            # Refit one reflection plane from the explicit pairs, without a fixed world-plane prior.
            centre = middle.mean(axis=0)
            difference = left - right
            if np.linalg.norm(difference) <= 1e-9:
                raise ValueError("Matched body support does not identify a reflection direction.")
            # Minimise reflection error: midpoint projection error minus matched separation alignment.
            spread = middle - centre
            eigenvalues, vectors = np.linalg.eigh(4 * spread.T @ spread - difference.T @ difference)
            if eigenvalues[1] - eigenvalues[0] <= 1e-12:
                raise ValueError("Matched body support does not identify one reflection plane.")
            normal = vectors[:, 0]
            reflected = left - 2 * ((left - centre) @ normal)[:, None] * normal
            # A relation's sigma describes RMS support error; more pixels do not invent more observations.
            return ((reflected - right) / np.sqrt(len(pairs))).ravel()

        return symmetry, relation.sigma
    raise ValueError(f"Unsupported reviewed relationship kind: {relation.kind}")


def add_context_factors(graph: Any, initial: Any, document: GraphDocument, source: Path,
                        binding: SourceBinding | None, key: Callable[[int], int]) -> list[dict[str, Any]]:
    """Add soft camera factors only; return explicit active/inactive provenance for every supplied relation."""
    import gtsam
    from gtsam.utils.numerical_derivative import numericalDerivative11

    if binding is None:
        return [{"active": False, "reason": "No reviewed source-bound geometry context supplied."}]
    if binding.source_run_id != source.name:
        raise ValueError("Reviewed context belongs to another original source result.")
    frames = read_json(source / "frames.json")
    settings = ScanSettings.model_validate(read_json(source / "run.json")["settings"])
    regions = {region.id: region for region in binding.regions}
    if len(regions) != len(binding.regions):
        raise ValueError("Reviewed region IDs must be unique within the source binding.")
    masks: dict[str, list[str]] = {}
    for mask in binding.masks:
        masks.setdefault(mask.frame_id, []).append(mask.asset)
    reports = []
    for index, relation in enumerate(binding.relationships):
        report: dict[str, Any] = {"index": index, "kind": relation.kind, "active": False,
                                  "region_ids": relation.region_ids, "sigma": relation.sigma, "units": relation.units}
        try:
            if not relation.enabled:
                raise ValueError("Relationship is disabled by review.")
            if relation.sigma is None:
                raise ValueError("No explicit relationship tolerance supplied.")
            if any(region not in regions for region in relation.region_ids):
                raise ValueError("Relationship refers to an unavailable reviewed region.")
            samples = {region: _samples(source, regions[region], frames, document, settings, key, masks)
                       for region in relation.region_ids}
            keys = sorted({sample.key for values in samples.values() for sample in values})
            poses = {pose_key: initial.atPose3(pose_key) for pose_key in keys}
            residual, sigma = _residual(relation, regions, samples, poses)
            dimension = len(residual(poses))

            def error(_: Any, values: Any, jacobians: Any, *, keys=keys, residual=residual) -> Any:
                current = {pose_key: values.atPose3(pose_key) for pose_key in keys}
                if jacobians is not None:
                    for i, pose_key in enumerate(keys):
                        jacobians[i] = numericalDerivative11(
                            lambda pose: residual({**current, pose_key: pose}), current[pose_key]
                        )
                return residual(current)

            graph.add(gtsam.CustomFactor(gtsam.noiseModel.Isotropic.Sigma(dimension, sigma), keys, error))
            report.update(active=True, contributing_frames=sorted({sample.frame_id for values in samples.values()
                                                                   for sample in values}),
                          support_samples=sum(len(sample.camera_points) for values in samples.values()
                                              for sample in values))
        except (ValueError, OSError) as error:
            report["reason"] = str(error)
        reports.append(report)
    return reports or [{"active": False, "reason": "No reviewed relationships supplied; geometry context skipped."}]
