"""Joint camera/landmark fitting and model-based uncertainty, without changing observations."""

from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

from campervan.scan_graph import GraphDocument, ensure_graph
from campervan.scan_measurements import MeasurementDocument
from campervan.scan_network import pair_jacobian
from campervan.scans import file_hash, read_json, write_json


class UnobservableGraph(ValueError):
    pass


def _key(node: int) -> int:
    import gtsam

    return int(gtsam.symbol("x" if node > 0 else "l", abs(node)))


def _gauge(graph: Any, initial: Any, root: int, gravity: bool) -> None:
    import gtsam

    key = _key(root)
    pose = initial.atPose3(key)
    if not gravity:
        graph.add(gtsam.NonlinearEqualityPose3(key, pose))
        return
    # Gravity observes roll/pitch. Fix only the remaining global translation/yaw gauge.
    origin = pose.translation()
    rotation = pose.rotation().matrix()
    axis = int(np.argmax(np.sum(rotation[:2] ** 2, axis=0)))
    yaw = np.arctan2(rotation[1, axis], rotation[0, axis])

    def error(_: Any, values: Any, jacobians: Any) -> Any:
        current = values.atPose3(key)
        r = current.rotation().matrix()
        direction = r[:, axis]
        angle = np.arctan2(direction[1], direction[0]) - yaw
        angle = np.arctan2(np.sin(angle), np.cos(angle))
        if jacobians is not None:
            gradient = np.array([-direction[1], direction[0], 0]) / (direction[0] ** 2 + direction[1] ** 2)
            basis = np.eye(3)[:, axis]
            skew = np.array([[0, -basis[2], basis[1]], [basis[2], 0, -basis[0]], [-basis[1], basis[0], 0]])
            h = np.zeros((4, 6))
            h[:3, 3:] = r
            h[3, :3] = gradient @ (-r @ skew)
            jacobians[0] = h
        return np.r_[current.translation() - origin, angle]

    graph.add(gtsam.CustomFactor(gtsam.noiseModel.Constrained.All(4), [key], error))


def _build(document: GraphDocument) -> tuple[Any, Any]:
    import gtsam

    graph = gtsam.NonlinearFactorGraph()
    initial = gtsam.Values()
    for key, matrix in document.poses.items():
        initial.insert(_key(int(key)), gtsam.Pose3(np.asarray(matrix)))
    connected: dict[int, set[int]] = {int(key): set() for key in document.poses}
    order = [3, 4, 5, 0, 1, 2]
    for link in document.links:
        a, b = link.from_id, link.to_id
        pose = gtsam.Pose3(np.asarray(link.transform))
        information = np.asarray(link.information)[np.ix_(order, order)]
        model = gtsam.noiseModel.Gaussian.Information(information)
        if link.kind == 7:
            if a != b:
                raise ValueError("Pose prior must be a self link.")
            graph.add(gtsam.PriorFactorPose3(_key(a), pose, model))
        elif link.kind == 9:
            if document.gravity_sigma_rad > 0:
                measured = np.asarray(link.transform)[:3, :3].T @ np.array([0.0, 0.0, 1.0])
                graph.add(
                    gtsam.AttitudeFactorPose3(
                        _key(a),
                        gtsam.Unit3(0, 0, 1),
                        gtsam.noiseModel.Isotropic.Sigma(2, document.gravity_sigma_rad),
                        gtsam.Unit3(measured),
                    )
                )
        else:
            if a == b:
                raise ValueError("Relative graph observation cannot be a self link.")
            graph.add(gtsam.BetweenFactorPose3(_key(a), _key(b), pose, model))
            connected[a].add(b)
            connected[b].add(a)
    root = min(key for key in connected if key > 0)
    reached: set[int] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node not in reached:
            reached.add(node)
            stack.extend(connected[node] - reached)
    if reached != set(connected):
        raise UnobservableGraph("Original scan graph is disconnected; no finite joint uncertainty can be reported.")
    if not any(link.kind == 7 for link in document.links):
        _gauge(graph, initial, root, document.gravity_sigma_rad > 0 and any(link.kind == 9 for link in document.links))
    return graph, initial


def _positions(values: Any, ids: list[int]) -> Any:
    return np.asarray([values.atPose3(_key(-tag)).translation() for tag in ids])


def _covariance(graph: Any, values: Any, ids: list[int]) -> Any:
    import gtsam

    try:
        marginals = gtsam.Marginals(graph, values)
        joint = marginals.jointMarginalCovariance([_key(-tag) for tag in ids]).fullMatrix()
    except RuntimeError as error:
        raise UnobservableGraph(f"Graph uncertainty is unobservable or ill-conditioned: {error}") from error
    jacobian = np.zeros((3 * len(ids), 6 * len(ids)))
    for i, tag in enumerate(ids):
        jacobian[3 * i : 3 * i + 3, 6 * i + 3 : 6 * i + 6] = values.atPose3(_key(-tag)).rotation().matrix()
    result = jacobian @ joint @ jacobian.T
    if not np.isfinite(result).all() or np.min(np.linalg.eigvalsh(result)) < -1e-8:
        raise UnobservableGraph("Joint covariance is invalid; uncertainty cannot be quantified.")
    return result


def _analyse(run: Path, measurements: MeasurementDocument, output: Path) -> dict[str, Any]:
    import gtsam

    manifest = read_json(run / "run.json")
    if manifest.get("tag_layout_id") != measurements.tag_layout_id:
        raise ValueError("Selected run and measurements belong to different tag layouts.")
    if measurements.default_sigma_m is None:
        raise ValueError("Set the typical measuring precision before analysing uncertainty.")
    document = ensure_graph(run)
    write_json(output / "graph.json", document.model_dump())
    ids = sorted(tag["id"] for tag in manifest["tags"])
    if len(ids) < 2:
        raise ValueError("At least two observed tag centres are required.")
    graph, initial = _build(document)
    parameters = gtsam.LevenbergMarquardtParams()
    print("[Fit original scan observations]", flush=True)
    baseline = gtsam.LevenbergMarquardtOptimizer(graph, initial, parameters).optimize()
    baseline_cov = _covariance(graph, baseline, ids)
    for record in measurements.distances:
        if record.tag_a not in ids or record.tag_b not in ids:
            raise ValueError(f"Measured pair {record.tag_a}–{record.tag_b} is missing from this run.")
        sigma = record.sigma_m or measurements.default_sigma_m
        noise = gtsam.noiseModel.Robust.Create(
            gtsam.noiseModel.mEstimator.Huber.Create(1.345), gtsam.noiseModel.Isotropic.Sigma(1, sigma)
        )
        graph.add(gtsam.RangeFactorPose3(_key(-record.tag_a), _key(-record.tag_b), record.distance_m, noise))
    print("[Fit measured tag distances]", flush=True)
    fitted = gtsam.LevenbergMarquardtOptimizer(graph, baseline, parameters).optimize()
    covariance = _covariance(graph, fitted, ids)
    positions = _positions(fitted, ids)
    before = np.asarray([np.asarray(tag["pose"])[:3, 3] for tag in sorted(manifest["tags"], key=lambda t: t["id"])])
    residuals = []
    for record in measurements.distances:
        a, b = ids.index(record.tag_a), ids.index(record.tag_b)
        distance = float(np.linalg.norm(positions[a] - positions[b]))
        z = (distance - record.distance_m) / (record.sigma_m or measurements.default_sigma_m)
        residuals.append(
            {
                **record.model_dump(),
                "scan_m": float(np.linalg.norm(before[a] - before[b])),
                "fitted_m": distance,
                "residual_m": distance - record.distance_m,
                "standardised_residual": z,
                "weight": min(1.0, 1.345 / abs(z)) if z else 1.0,
            }
        )
    dimensions = []
    for a, b in combinations(range(len(ids)), 2):
        h = pair_jacobian(positions, a, b)
        h0 = pair_jacobian(_positions(baseline, ids), a, b)
        dimensions.append(
            {
                "tag_a": ids[a],
                "tag_b": ids[b],
                "before_95_m": float(1.96 * np.sqrt(max(0.0, h0 @ baseline_cov @ h0))),
                "after_95_m": float(1.96 * np.sqrt(max(0.0, h @ covariance @ h))),
            }
        )
    graph_poses = {key: fitted.atPose3(_key(int(key))).matrix().tolist() for key in document.poses}
    camera_poses = {
        key: (np.asarray(graph_poses[key]) @ np.asarray(offset)).tolist()
        for key, offset in document.optical_transforms.items()
    }
    tags = [{**tag, "pose": graph_poses[str(-tag["id"])]} for tag in manifest["tags"]]
    mesh = run / "mesh.ply"
    result = {
        "version": 1,
        "run_id": run.name,
        "tag_layout_id": measurements.tag_layout_id,
        "measurement_revision": measurements.revision,
        "default_sigma_m": measurements.default_sigma_m,
        "graph_sha256": file_hash(run / "graph.json"),
        "mesh_sha256": file_hash(mesh) if mesh.is_file() else None,
        "manifest_sha256": file_hash(run / "run.json"),
        "tag_ids": ids,
        "tags": tags,
        "movements": [
            {
                "id": tag,
                "before": before[i].tolist(),
                "after": positions[i].tolist(),
                "distance_m": float(np.linalg.norm(positions[i] - before[i])),
            }
            for i, tag in enumerate(ids)
        ],
        "residuals": residuals,
        "dimensions": dimensions,
        "diagnostics": {
            "nodes": len(document.poses),
            "original_factors": len(document.links),
            "excluded_nonlocalised_links": document.excluded_links,
            "gravity_sigma_rad": document.gravity_sigma_rad,
            "note": "Approximate 95% half-widths under the stated noise model; not calibrated physical accuracy.",
        },
    }
    write_json(output / "solution.json", {"graph_poses": graph_poses, "camera_poses": camera_poses, "tags": tags})
    np.save(output / "covariance.npy", covariance)
    write_json(output / "result.tmp", result)
    (output / "result.tmp").replace(output / "result.json")
    return result


def analyse(run: Path, measurements: MeasurementDocument, output: Path) -> dict[str, Any]:
    try:
        return _analyse(run, measurements, output)
    except UnobservableGraph as error:
        document = ensure_graph(run)
        neighbours: dict[int, set[int]] = {int(key): set() for key in document.poses}
        for link in document.links:
            if link.from_id != link.to_id:
                neighbours[link.from_id].add(link.to_id)
                neighbours[link.to_id].add(link.from_id)
        components: dict[int, int] = {}
        for key in neighbours:
            if key in components:
                continue
            component = len(components)
            stack = [key]
            while stack:
                item = stack.pop()
                if item not in components:
                    components[item] = component
                    stack.extend(neighbours[item] - components.keys())
        ids = sorted(tag["id"] for tag in read_json(run / "run.json")["tags"])
        measured = {(r.tag_a, r.tag_b) for r in measurements.distances}
        blocked = {(r.tag_a, r.tag_b) for r in measurements.excluded_pairs}
        disconnected = len(set(components.values())) > 1
        pairs = [
            {"tag_a": a, "tag_b": b}
            for a, b in combinations(ids, 2)
            if (a, b) not in measured
            and (a, b) not in blocked
            and (not disconnected or components[-a] != components[-b])
        ]
        write_json(
            output / "diagnostic.tmp",
            {
                "message": str(error),
                "pairs": pairs,
                "note": "Potential connections only: improvement cannot yet be quantified. Physical access is unknown.",
            },
        )
        (output / "diagnostic.tmp").replace(output / "diagnostic.json")
        raise
