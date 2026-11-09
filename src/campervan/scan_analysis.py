"""Registered measured proposals and joint original-observation correction, separate from physical assessment."""

from pathlib import Path
from typing import Any

import numpy as np

from campervan.scan_graph import GraphDocument, ensure_graph
from campervan.scan_measurements import MeasurementDocument
from campervan.scan_network import ALGORITHM_VERSION as NETWORK_ALGORITHM_VERSION, NETWORK_SETTINGS, analyse_network
from campervan.scan_workflow_models import SourceBinding
from campervan.scans import file_hash, read_json, write_json


class UnobservableGraph(ValueError):
    pass


CORRECTION_ALGORITHM_VERSION = "scan-correction-1"
CORRECTION_SETTINGS = {"registration": "weighted-proper-rigid-no-scale", "huber_k": 1.345,
                       "context": "source-depth-refit-soft-relations-1", "linear_solver": "MULTIFRONTAL_QR",
                       "physical_initializer": {"algorithm": NETWORK_ALGORITHM_VERSION, "settings": NETWORK_SETTINGS}}


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
        raise UnobservableGraph("Original scan graph is disconnected; the joint correction needs connected observations.")
    if not any(link.kind == 7 for link in document.links):
        _gauge(graph, initial, root, document.gravity_sigma_rad > 0 and any(link.kind == 9 for link in document.links))
    return graph, initial


def register_measured_shape(network: dict[str, Any], captured_positions: dict[int, Any]) -> dict[str, Any]:
    """Orient an identifiable range fit for the source; incomplete modes keep labelled captured support."""
    ids = network["tag_ids"]
    captured = np.asarray([captured_positions[tag] for tag in ids], dtype=float).reshape((-1, 3))
    fitted = np.asarray(network["positions_m"], dtype=float).reshape((-1, 3))
    if fitted.shape != captured.shape or not np.isfinite(fitted).all() or not np.isfinite(captured).all():
        raise ValueError("Physical and captured tag positions must be finite and have identical IDs.")
    reasons = []
    if network["solver"]["status"] != "fitted":
        reasons.append("The independent range fit is unavailable or has no active measurements.")
    if network["information"]["nullity"] or network["completeness"]["nonlinear_ambiguity"]:
        reasons.append("The measured shape has unresolved modes or nonlinear ambiguity.")
    if len(ids) < 3 or np.linalg.matrix_rank(fitted - fitted.mean(axis=0)) < 2:
        reasons.append("The measured shape cannot identify a full rigid registration.")
    weights = np.ones(len(ids))
    covariance = network.get("covariance_m2")
    if covariance is not None:
        matrix = np.asarray(covariance)
        if matrix.shape != (3 * len(ids), 3 * len(ids)) or not np.isfinite(matrix).all():
            raise ValueError("Physical covariance does not match the fitted tag positions.")
        variances = np.array([np.trace(matrix[3*i:3*i+3, 3*i:3*i+3]) for i in range(len(ids))])
        if np.any(variances <= 0):
            raise ValueError("Physical registration weights require positive positional covariance.")
        weights = 1 / variances
    weights = weights / weights.sum() if len(weights) else weights
    if reasons:
        return {"positions": dict(zip(ids, captured, strict=True)), "rotation": np.eye(3),
                "translation": np.zeros(3), "weights": weights.tolist(), "status": "scan_dependent",
                "reasons": reasons, "scan_dependent_tag_ids": ids,
                "unresolved_mode_count": network["information"]["nullity"]}
    source_centre = np.sum(fitted * weights[:, None], axis=0)
    target_centre = np.sum(captured * weights[:, None], axis=0)
    u, _, vt = np.linalg.svd(((fitted - source_centre) * weights[:, None]).T @ (captured - target_centre))
    correction = np.diag([1.0, 1.0, 1.0 if np.linalg.det(vt.T @ u.T) >= 0 else -1.0])
    rotation = vt.T @ correction @ u.T
    translation = target_centre - rotation @ source_centre
    registered = fitted @ rotation.T + translation
    return {"positions": dict(zip(ids, registered, strict=True)), "rotation": rotation, "translation": translation,
            "weights": weights.tolist(), "status": "registered", "reasons": [], "scan_dependent_tag_ids": [],
            "unresolved_mode_count": 0}


def _initialise_proposal(initial: Any, document: GraphDocument, proposed: dict[int, Any]) -> None:
    """Move tag translations and their directly observing camera starts together; preserve native rotations/gauge."""
    import gtsam

    shifts = {tag: np.asarray(point) - initial.atPose3(_key(-tag)).translation() for tag, point in proposed.items()}
    camera_shifts: dict[int, list[tuple[Any, float]]] = {}
    for link in document.links:
        a, b = link.from_id, link.to_id
        if a > 0 > b and -b in shifts:
            camera, tag = a, -b
        elif b > 0 > a and -a in shifts:
            camera, tag = b, -a
        else:
            continue
        weight = float(np.trace(np.asarray(link.information)[:3, :3]))
        camera_shifts.setdefault(camera, []).append((shifts[tag], weight))
    translations = {-tag: shift for tag, shift in shifts.items()}
    translations.update({camera: np.average([shift for shift, _ in supports], axis=0,
                                            weights=[weight for _, weight in supports])
                         for camera, supports in camera_shifts.items()})
    root = min(int(node) for node in document.poses if int(node) > 0)
    # _build fixes the original root gauge; keep the initializer on that same equality manifold.
    offset = translations.get(root, np.zeros(3)) if not any(link.kind == 7 for link in document.links) else np.zeros(3)
    for node in document.poses:
        pose = initial.atPose3(_key(int(node)))
        initial.update(_key(int(node)), gtsam.Pose3(pose.rotation(),
                       pose.translation() + translations.get(int(node), np.zeros(3)) - offset))


def preview_correction(run: Path, measurements: MeasurementDocument, output: Path, *,
                       network: dict[str, Any] | None = None, binding: SourceBinding | None = None) -> dict[str, Any]:
    """Fit original graph factors and each active original range once; publish no measurement-only uncertainty."""
    import gtsam
    from campervan.scan_context_factors import add_context_factors

    manifest = read_json(run / "run.json")
    if manifest.get("tag_layout_id") != measurements.tag_layout_id:
        raise ValueError("Selected source and physical measurements belong to different tag layouts.")
    document = ensure_graph(run)
    ids = sorted(tag["id"] for tag in manifest.get("tags", []))
    if len(ids) != len(set(ids)) or any(str(-tag) not in document.poses for tag in ids):
        raise ValueError("Captured tag IDs do not match the original graph landmarks.")
    active = [record for record in measurements.distances if record.tag_a in ids and record.tag_b in ids]
    inactive = [{**record.model_dump(), "reason": "One or both tags are absent from this source capture."}
                for record in measurements.distances if record not in active]
    if any((record.sigma_m or measurements.default_sigma_m) is None for record in active):
        raise ValueError("Set measuring precision for each active physical range before correction.")
    if network is None:
        network = analyse_network(manifest, measurements, NETWORK_SETTINGS, output)
    if network["tag_ids"] != ids:
        raise ValueError("Measured proposal belongs to different captured tags.")
    before = {tag["id"]: np.asarray(tag["pose"])[:3, 3] for tag in manifest.get("tags", [])}
    registration = register_measured_shape(network, before)
    graph, initial = _build(document)
    _initialise_proposal(initial, document, registration["positions"])
    original_factors = graph.size()
    for record in active:
        sigma = record.sigma_m or measurements.default_sigma_m
        noise = gtsam.noiseModel.Robust.Create(
            gtsam.noiseModel.mEstimator.Huber.Create(CORRECTION_SETTINGS["huber_k"]),
            gtsam.noiseModel.Isotropic.Sigma(1, sigma),
        )
        graph.add(gtsam.RangeFactorPose3(_key(-record.tag_a), _key(-record.tag_b), record.distance_m, noise))
    context = add_context_factors(graph, initial, document, run, binding, _key)
    parameters = gtsam.LevenbergMarquardtParams()
    parameters.setLinearSolverType(CORRECTION_SETTINGS["linear_solver"])
    print("[Fit original graph and physical ranges]", flush=True)
    optimizer = gtsam.LevenbergMarquardtOptimizer(graph, initial, parameters)
    fitted = optimizer.optimize()
    graph_poses = {node: fitted.atPose3(_key(int(node))).matrix().tolist() for node in document.poses}
    if not all(np.isfinite(matrix).all() for matrix in map(np.asarray, graph_poses.values())):
        raise ValueError("Joint correction returned nonfinite camera or landmark poses.")
    camera_poses = {node: (np.asarray(graph_poses[node]) @ np.asarray(offset)).tolist()
                    for node, offset in document.optical_transforms.items()}
    tags = [{**tag, "pose": graph_poses[str(-tag["id"])], "scan_dependent": tag["id"] in
             registration["scan_dependent_tag_ids"]} for tag in manifest.get("tags", [])]
    after = {tag: np.asarray(graph_poses[str(-tag)])[:3, 3] for tag in ids}
    residuals = []
    for record in active:
        distance = float(np.linalg.norm(after[record.tag_a] - after[record.tag_b]))
        sigma = record.sigma_m or measurements.default_sigma_m
        z = (distance - record.distance_m) / sigma
        residuals.append({**record.model_dump(), "effective_sigma_m": sigma, "fitted_m": distance,
                          "residual_m": distance - record.distance_m, "standardised_residual": z,
                          "weight": min(1.0, CORRECTION_SETTINGS["huber_k"] / abs(z)) if z else 1.0})
    result = {
        "tag_ids": ids, "tags": tags,
        "movements": [{"id": tag, "before": before[tag].tolist(), "after": after[tag].tolist(),
                       "registered_proposal": registration["positions"][tag].tolist(),
                       "distance_m": float(np.linalg.norm(after[tag] - before[tag])),
                       "scan_dependent": tag in registration["scan_dependent_tag_ids"]} for tag in ids],
        "residuals": residuals, "inactive_measurements": inactive, "inactive_measurement_count": len(inactive),
        "registration": {key: value.tolist() if isinstance(value, np.ndarray) else value
                         for key, value in registration.items() if key != "positions"},
        "context": context,
        "cleanup": {"mask_count": len(binding.masks) if binding else 0,
                    "note": "Reviewed masks will be applied before fusion." if binding and binding.masks else
                            "No reviewed cleanup masks supplied; cleanup context skipped."},
        "diagnostics": {"nodes": len(document.poses), "original_factors": original_factors,
                        "physical_range_factors": len(active), "context_factors": sum(item["active"] for item in context),
                        "iterations": optimizer.iterations(), "initial_error": float(graph.error(initial)),
                        "final_error": float(graph.error(fitted)),
                        "note": "Joint scan-assisted correction; movements and residuals are not physical-network accuracy."},
    }
    write_json(output / "graph.json", document.model_dump())
    write_json(output / "solution.json", {"graph_poses": graph_poses, "camera_poses": camera_poses, "tags": tags})
    result["solution_sha256"] = file_hash(output / "solution.json")
    result["graph_sha256"] = file_hash(output / "graph.json")
    return result


