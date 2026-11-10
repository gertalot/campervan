"""Physical Point3 range network and orthogonally aligned free-network information.

Captured positions choose an initial configuration and display handedness only. This
module owns the common range derivative and information convention used by planning.
"""

import random
import signal
from functools import cache
from importlib.metadata import version
from itertools import combinations
from pathlib import Path
from time import perf_counter
from typing import Any

from campervan.scan_measurements import MeasurementDocument
from campervan.scan_workflows import fingerprint
from campervan.scans import write_json

ALGORITHM_VERSION = "physical-ranges-4"
NETWORK_SETTINGS = {
    "huber_k": 1.345,
    "rank_rtol": 1e-9,
    "poor_condition_ratio": 1e-8,
    "coincident_m": 1e-6,
    "linear_solver": "MULTIFRONTAL_QR",
    "rigidity_algorithm": "randomized",
    "rigidity_probability": 1e-4,
    "rigidity_budget_s": 5.0,
    "covariance_convention": "equal-weight-orthogonal-free-network",
    "relative_groups": "local-distance-closure-observable-projection-1",
    "coverage_geometry_penalty": 2.0,
}


def pair_jacobian(positions: Any, a: int, b: int) -> Any:
    import numpy as np

    delta = positions[a] - positions[b]
    length = np.linalg.norm(delta)
    if length < NETWORK_SETTINGS["coincident_m"]:
        raise ValueError("Coincident tag centres cannot constrain a distance.")
    row = np.zeros(positions.size)
    row[3 * a:3 * a + 3], row[3 * b:3 * b + 3] = delta / length, -delta / length
    return row


def rigid_complement(positions: Any, *, rtol: float = 1e-9) -> Any:
    """Orthogonal complement of the actual rigid-motion span, reusable at fixed positions."""
    import numpy as np

    motions = np.zeros((positions.size, 6))
    if len(positions):
        centred = positions - positions.mean(axis=0)
        for i, (x, y, z) in enumerate(centred):
            motions[3 * i:3 * i + 3, :3] = np.eye(3)
            motions[3 * i:3 * i + 3, 3:] = [[0, z, -y], [-z, 0, x], [y, -x, 0]]
    lengths = np.linalg.norm(motions, axis=0)
    motions[:, lengths > 0] /= lengths[lengths > 0]
    u, singular, _ = np.linalg.svd(motions, full_matrices=True)
    rank = int(np.count_nonzero(singular > (singular[0] * rtol if singular.size else 0)))
    return u[:, rank:]


def free_network_information(positions: Any, rows: Any, *, rtol: float = 1e-9, q: Any = None) -> dict[str, Any]:
    """Return array-valued Q/covariance/null basis from *whitened* range rows.

    Rows and positions use the same sorted tag order. Q removes only the actual
    global rigid-motion span. A rank-deficient shape has covariance=None; its
    retained null basis is in full 3N coordinates, including truncated modes.
    """
    import numpy as np

    size = positions.size
    q = rigid_complement(positions, rtol=rtol) if q is None else q
    a = np.asarray(rows, dtype=float).reshape((-1, size)) @ q if size else np.zeros((0, 0))
    _, singular, vt = np.linalg.svd(a, full_matrices=a.shape[0] < q.shape[1])
    cutoff = float(singular[0] * rtol) if singular.size else 0.0
    rank = int(np.count_nonzero(singular > cutoff))
    shape_dimension = q.shape[1]
    null_basis = q @ vt[rank:].T
    covariance = None
    observable_root = q @ vt[:rank].T / singular[:rank] if rank else np.zeros((size, 0))
    if rank == shape_dimension and size:
        scaled = q @ vt.T / singular if shape_dimension else np.zeros((size, 0))
        covariance = scaled @ scaled.T
    # Include nonzero truncated modes in conditioning diagnostics; do not hide them.
    positive = singular[singular > 0]
    ratio = float(positive[-1] / positive[0]) if positive.size else None
    return {
        "Q": q, "covariance": covariance, "null_basis": null_basis, "observable_root": observable_root,
        "rigid_motion_rank": size - q.shape[1], "shape_dimension": shape_dimension,
        "rank": rank, "nullity": shape_dimension - rank, "singular_values": singular,
        "rank_cutoff": cutoff, "nonzero_singular_ratio": ratio,
        "condition_number": float(1 / ratio) if rank == shape_dimension and ratio and np.isfinite(1 / ratio) else None,
        "poorly_conditioned": ratio is not None and ratio < NETWORK_SETTINGS["poor_condition_ratio"],
    }


@cache
def uncertainty_conversion() -> float:
    from scipy.stats import chi2

    return float(chi2.ppf(.95, 3))


def position_ellipsoids(ids: list[int], covariance: Any) -> list[dict[str, Any]]:
    import numpy as np

    conversion = uncertainty_conversion()
    result = []
    for i, tag in enumerate(ids):
        values, directions = np.linalg.eigh(covariance[3*i:3*i+3, 3*i:3*i+3])
        axes = np.sqrt(conversion * np.maximum(values, 0))
        result.append({"tag_id": tag, "semi_axes_95_m": axes.tolist(), "directions": directions.tolist(),
                       "longest_semi_axis_95_m": float(axes[-1]), "worst_direction": directions[:, -1].tolist()})
    return result


def coverage_diagnostic(tag: int, rows: Any, neighbours: list[int], *, precision_available: bool = True,
                        include_ellipsoid: bool = True) -> dict[str, Any]:
    """Conditional measurement coverage: neighbouring positions are held fixed for this diagnostic only.

    This is the tag's own weighted Jacobian block, not a prior, full-network covariance or proof of uniqueness.
    QR retains a small reusable factor; SVD avoids squaring the rank tolerance in an information matrix.
    """
    import numpy as np

    block = np.asarray(rows, dtype=float).reshape((-1, 3))
    block = block[np.linalg.norm(block, axis=1) > 0]
    factor = np.linalg.qr(block, mode="r")
    _, singular, vt = np.linalg.svd(factor, full_matrices=True)
    cutoff = singular[0] * NETWORK_SETTINGS["rank_rtol"] if singular.size else 0.0
    rank = int(np.count_nonzero(singular > cutoff))
    ellipsoid = None
    penalty = None
    radius = None
    if rank == 3 and precision_available:
        radius = float(np.sqrt(uncertainty_conversion()) / singular[-1])
        ideal = float(np.sqrt(uncertainty_conversion() * 3 / np.sum(singular ** 2)))
        penalty = radius / ideal
        if include_ellipsoid:
            root = vt.T / singular
            ellipsoid = position_ellipsoids([tag], root @ root.T)[0]
    missing = vt[rank:].tolist()
    return {"tag_id": tag, "neighbour_ids": sorted(set(neighbours)), "rank": rank,
            "missing_directions": 3 - rank, "missing_direction_vectors": missing,
            "weakest_direction": vt[-1].tolist(), "ellipsoid": ellipsoid,
            "conditional_radius_95_m": radius,
            "geometry_penalty": penalty,
            "poorly_spread": rank < 3 or penalty is not None and penalty > NETWORK_SETTINGS["coverage_geometry_penalty"],
            "precision_available": precision_available, "factor": factor.tolist(),
            "assumption": "Neighbouring tag positions held fixed; optimistic local diagnostic only."}


def measurement_coverage(ids: list[int], rows: Any, edges: list[tuple[int, int]],
                         unknown_precision: list[tuple[int, int]]) -> list[dict[str, Any]]:
    import numpy as np

    matrix = np.asarray(rows, dtype=float).reshape((-1, 3 * len(ids))) if ids else np.zeros((0, 0))
    return [coverage_diagnostic(tag, matrix[:, 3*i:3*i+3],
                                [b if a == tag else a for a, b in edges if tag in (a, b)],
                                precision_available=not any(tag in pair for pair in unknown_precision))
            for i, tag in enumerate(ids)]


def relative_groups(ids: list[int], positions: Any, information: dict[str, Any],
                    edges: list[tuple[int, int]]) -> list[dict[str, Any]]:
    """Local rigid groups and uncertainty of their internal shape, never their placement in the whole.

    A group must annihilate every remaining free mode after its own rigid motion is removed.
    Only that observable projection uses the positive singular modes. The full network covariance
    remains unavailable when its shape has free modes; no anchor or scan prior is added.
    """
    import networkx as nx
    import numpy as np

    tolerance = NETWORK_SETTINGS["rank_rtol"]
    free = information["null_basis"]
    closure = nx.Graph()
    closure.add_nodes_from(ids)
    for i, j in combinations(range(len(ids)), 2):
        try:
            h = pair_jacobian(positions, i, j)
        except ValueError:
            continue
        if np.linalg.norm(h @ free) <= tolerance * np.linalg.norm(h):
            closure.add_edge(ids[i], ids[j])
    measured = {tuple(sorted(edge)) for edge in edges}
    result = []
    # Maximal cliques of the observable-distance closure, not cliques of raw measured edges:
    # indirect constraints can hold a group together, while overlapping groups can hinge.
    candidates = {tuple(sorted(group)) for group in nx.find_cliques(closure) if len(group) >= 3}
    # A flat exceptional larger clique may fail the full shape-projection check while containing
    # valid triangles. Preserve those smaller structures rather than dropping their information.
    candidates.update(triangle for triangle in combinations(ids, 3)
                      if all(closure.has_edge(a, b) for a, b in combinations(triangle, 2)))
    for members in sorted(candidates, key=lambda group: (-len(group), group)):
        if any(set(members).issubset(group["tag_ids"]) for group in result):
            continue
        members = list(members)
        indices = [ids.index(tag) for tag in members]
        sub = positions[indices]
        singular = np.linalg.svd(sub - sub.mean(axis=0), compute_uv=False)
        geometry_rank = int(np.count_nonzero(singular > singular[0] * tolerance)) if singular.size else 0
        if geometry_rank < 2:
            continue
        q = rigid_complement(sub, rtol=tolerance)
        projection = q @ q.T
        coordinates = [axis for i in indices for axis in range(3*i, 3*i+3)]
        if np.linalg.norm(projection @ free[coordinates]) > tolerance:
            # Pairwise first-order invariance alone is insufficient at exceptional/flat geometry.
            continue
        root = projection @ information["observable_root"][coordinates]
        covariance = root @ root.T
        unresolved = [tag for tag in ids if tag not in members and
                      any(not closure.has_edge(tag, member) for member in members)]
        result.append({"id": ":".join(map(str, members)), "tag_ids": members,
                       "geometry_rank": geometry_rank, "ellipsoids": position_ellipsoids(members, covariance),
                       "shape_unique": all(tuple(pair) in measured for pair in combinations(members, 2)),
                       "unresolved_with_tag_ids": unresolved,
                       "convention": "within-group-orthogonal-free-network",
                       "qualification": "Local internal shape only, after removing this group's translation and rotation. "
                                        "This does not bound its position/orientation relative to other groups or "
                                        "exclude nonlinear alternatives unless shape uniqueness is established."})
    return result


def topology_deficits(ids: list[int], edges: list[tuple[int, int]]) -> tuple[int, dict[int, int]]:
    """Necessary generic 3D conditions only; satisfying them is not a certificate."""
    neighbours = {tag: set() for tag in ids}
    for a, b in set(tuple(sorted(edge)) for edge in edges):
        neighbours[a].add(b)
        neighbours[b].add(a)
    n = len(ids)
    required = 3 * n - 5 if n > 4 else n * (n - 1) // 2
    minimum_degree = 4 if n > 4 else max(0, n - 1)
    return max(0, required - sum(map(len, neighbours.values())) // 2), {
        tag: max(0, minimum_degree - len(adjacent)) for tag, adjacent in neighbours.items()}


def topology_certificate(ids: list[int], edges: list[tuple[int, int]],
                         cache: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """PyRigi generic 3D certificate, with a reproducible worker-local random seed."""
    vertices, pairs = sorted(ids), sorted(set(tuple(sorted(edge)) for edge in edges))
    key = fingerprint({"vertices": vertices, "edges": pairs, "settings": NETWORK_SETTINGS})
    if cache is not None and key in cache:
        return cache[key]
    # A 52-bit seed also survives the browser's JSON number representation exactly.
    seed = int(key[:13], 16)
    result = {"status": "unknown", "vertices": vertices, "edges": pairs, "seed": seed,
              "package": "pyrigi", "version": None, "dimension": 3,
              "algorithm": NETWORK_SETTINGS["rigidity_algorithm"],
              "probability": NETWORK_SETTINGS["rigidity_probability"],
              "qualification": "Generic topology only; randomized false-negative probability at most 1e-4 "
                               "under PyRigi's assumptions. Exceptional geometry is assessed separately.",
              "error": None, "reason": None, "budget_s": NETWORK_SETTINGS["rigidity_budget_s"]}
    started = perf_counter()
    edge_deficit, degrees = topology_deficits(vertices, pairs)
    if edge_deficit or any(degrees.values()) or len(vertices) <= 4:
        result.update(status="not_certified" if edge_deficit or any(degrees.values()) else "rigid",
                      reason="Necessary edge/degree conditions are not met." if edge_deficit or any(degrees.values())
                      else "Complete graph on at most four vertices.", elapsed_s=perf_counter() - started)
        if cache is not None:
            cache[key] = result
        return result
    state = random.getstate()
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def expired(_signal, _frame):
        raise TimeoutError("Global-rigidity computation exceeded its time budget.")

    try:
        signal.signal(signal.SIGALRM, expired)
        signal.setitimer(signal.ITIMER_REAL, NETWORK_SETTINGS["rigidity_budget_s"])
        from pyrigi import Graph

        result["version"] = version("pyrigi")
        random.seed(seed)
        rigid = Graph.from_vertices_and_edges(vertices, pairs).is_globally_rigid(
            dim=3, algorithm="randomized", prob=1e-4,
        )
        result["status"] = "rigid" if rigid else "not_certified"
    except TimeoutError:
        result["reason"] = "time_budget_exceeded"
    except (ImportError, RuntimeError, ValueError) as error:
        result["error"] = str(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0]:
            signal.setitimer(signal.ITIMER_REAL, max(1e-6, previous_timer[0] - (perf_counter() - started)),
                             previous_timer[1])
        random.setstate(state)
    result["elapsed_s"] = perf_counter() - started
    if cache is not None:
        cache[key] = result
    return result


def _canonical_positions(positions: Any, ids: list[int]) -> tuple[Any, list[int], Any]:
    import numpy as np

    if not len(ids):
        return positions.copy(), [], np.eye(3)
    # Farthest pair, then largest altitude: deterministic, separated gauge anchors.
    a, b = max(((i, j) for i in range(len(ids)) for j in range(i + 1, len(ids))),
               key=lambda pair: np.linalg.norm(positions[pair[1]] - positions[pair[0]]), default=(0, 0))
    shifted = positions - positions[a]
    anchors = [a]
    length = np.linalg.norm(shifted[b])
    if length < NETWORK_SETTINGS["coincident_m"]:
        return shifted, anchors, np.eye(3)
    x = shifted[b] / length
    anchors.append(b)
    transverse = shifted - np.outer(shifted @ x, x)
    c = int(np.argmax(np.linalg.norm(transverse, axis=1)))
    altitude = np.linalg.norm(transverse[c])
    if altitude >= NETWORK_SETTINGS["coincident_m"]:
        y = transverse[c] / altitude
        anchors.append(c)
    else:
        axis = np.eye(3)[int(np.argmin(np.abs(x)))]
        y = axis - x * (axis @ x)
        y /= np.linalg.norm(y)
    rotation = np.column_stack((x, y, np.cross(x, y)))
    return shifted @ rotation, anchors, rotation


def _fit(positions: Any, ids: list[int], records: list[Any], sigmas: list[float],
         anchors: list[int]) -> tuple[Any, dict[str, Any]]:
    import gtsam
    import numpy as np

    graph, initial = gtsam.NonlinearFactorGraph(), gtsam.Values()
    involved = {tag for record in records for tag in (record.tag_a, record.tag_b)}
    involved.update(ids[i] for i in anchors)
    for i, tag in enumerate(ids):
        if tag in involved:
            initial.insert(tag, gtsam.Point3(*positions[i]))
    for record, sigma in zip(records, sigmas):
        noise = gtsam.noiseModel.Robust.Create(
            gtsam.noiseModel.mEstimator.Huber.Create(NETWORK_SETTINGS["huber_k"]),
            gtsam.noiseModel.Isotropic.Sigma(1, sigma),
        )
        graph.add(gtsam.RangeFactor3(record.tag_a, record.tag_b, record.distance_m, noise))
    if anchors:
        graph.add(gtsam.PriorFactorPoint3(ids[anchors[0]], gtsam.Point3(0, 0, 0),
                                         gtsam.noiseModel.Constrained.All(3)))

    def coordinate_factor(index: int, coordinates: list[int]) -> None:
        key, selector = ids[index], np.eye(3)[coordinates]

        def error(_: Any, values: Any, jacobians: Any) -> Any:
            if jacobians is not None:
                jacobians[0] = selector
            return selector @ values.atPoint3(key)

        graph.add(gtsam.CustomFactor(gtsam.noiseModel.Constrained.All(len(coordinates)), [key], error))

    if len(anchors) > 1:
        coordinate_factor(anchors[1], [1, 2])
    if len(anchors) > 2:
        coordinate_factor(anchors[2], [2])
    parameters = gtsam.LevenbergMarquardtParams()
    # QR preserves the hard partial-coordinate gauge factors without normal equations.
    parameters.setLinearSolverType(NETWORK_SETTINGS["linear_solver"])
    optimizer = gtsam.LevenbergMarquardtOptimizer(graph, initial, parameters)
    values = optimizer.optimize()
    fitted = positions.copy()
    for i, tag in enumerate(ids):
        if tag in involved:
            fitted[i] = values.atPoint3(tag)
    if not np.isfinite(fitted).all():
        raise ValueError("The range solver returned nonfinite positions.")
    return fitted, {"status": "fitted", "iterations": optimizer.iterations(),
                    "initial_objective": float(graph.error(initial)), "final_objective": float(graph.error(values))}


def analyse_network(run: dict[str, Any], measurements: MeasurementDocument,
                    settings: dict[str, Any], output: Path, *, certify: bool = True) -> dict[str, Any]:
    """Analyse an immutable manifest/measurement snapshot; never write source data."""
    started = perf_counter()
    imports_started = perf_counter()
    import gtsam
    import numpy as np

    del gtsam
    dependencies = {name: version(name) for name in ("gtsam", "numpy", "scipy")}
    import_elapsed = perf_counter() - imports_started
    if settings != NETWORK_SETTINGS:
        raise ValueError("Unsupported physical-network algorithm settings.")
    if run.get("tag_layout_id") != measurements.tag_layout_id:
        raise ValueError("Source capture and physical measurements belong to different layouts.")
    tags = sorted(run.get("tags", []), key=lambda tag: tag["id"])
    ids = [tag["id"] for tag in tags]
    if any(type(tag) is not int or tag <= 0 for tag in ids) or len(set(ids)) != len(ids):
        raise ValueError("Detected tag IDs must be unique positive integers.")
    captured = np.asarray([np.asarray(tag["pose"], dtype=float)[:3, 3] for tag in tags]).reshape((-1, 3))
    if not np.isfinite(captured).all():
        raise ValueError("Captured tag positions must be finite.")
    positions, anchors, rotation = _canonical_positions(captured, ids)
    index = {tag: i for i, tag in enumerate(ids)}
    records = sorted((record for record in measurements.distances
                      if record.tag_a in index and record.tag_b in index), key=lambda r: (r.tag_a, r.tag_b))
    inactive = [{**record.model_dump(), "reason": "One or both tags are absent from this source capture."}
                for record in measurements.distances if record.tag_a not in index or record.tag_b not in index]
    sigmas = [r.sigma_m or measurements.default_sigma_m for r in records]
    missing_sigma = any(sigma is None for sigma in sigmas)
    warnings = []
    solver: dict[str, Any] = {"status": "not_needed", "iterations": 0,
                              "initial_objective": None, "final_objective": None}
    coincident = [(r.tag_a, r.tag_b) for r in records
                  if np.linalg.norm(positions[index[r.tag_a]] - positions[index[r.tag_b]]) < settings["coincident_m"]]
    fit_started = perf_counter()
    if missing_sigma:
        solver["status"] = "unavailable"
        warnings.append("Set typical measuring precision or an override for every active measured pair.")
    elif coincident:
        solver["status"] = "unavailable"
        warnings.append("Coincident initial tag centres prevent a range derivative; no metric perturbation was added.")
    elif records:
        print("[Fit physical tag ranges]", flush=True)
        try:
            positions, solver = _fit(positions, ids, records, sigmas, anchors)
        except RuntimeError as error:
            solver["status"] = "unavailable"
            warnings.append(f"Physical range solver unavailable: {error}")
    fit_elapsed = perf_counter() - fit_started
    residuals, rows, unweighted_rows = [], [], []
    for record, sigma in zip(records, sigmas):
        a, b = index[record.tag_a], index[record.tag_b]
        fitted = float(np.linalg.norm(positions[a] - positions[b]))
        residual = fitted - record.distance_m
        z = residual / sigma if sigma else None
        weight = min(1.0, settings["huber_k"] / abs(z)) if z else 1.0
        residuals.append({"tag_a": record.tag_a, "tag_b": record.tag_b, "entered_m": record.distance_m,
                          "fitted_m": fitted if solver["status"] != "unavailable" else None,
                          "residual_m": residual if solver["status"] != "unavailable" else None,
                          "sigma_m": sigma, "standardised_residual": z if solver["status"] != "unavailable" else None,
                          "weight": weight if solver["status"] != "unavailable" else None})
        try:
            row = pair_jacobian(positions, a, b)
        except ValueError:
            warnings.append(f"Tag centres {record.tag_a}–{record.tag_b} coincide; their derivative is unavailable.")
            continue
        if sigma:
            rows.append(row * np.sqrt(weight) / sigma)
            unweighted_rows.append(row / sigma)
    information = free_network_information(positions, rows, rtol=settings["rank_rtol"])
    original_information = free_network_information(positions, unweighted_rows, rtol=settings["rank_rtol"])
    geometry_s = np.linalg.svd(positions - positions.mean(axis=0), compute_uv=False) if ids else np.asarray([])
    geometry_rank = int(np.count_nonzero(geometry_s > (geometry_s[0] * settings["rank_rtol"] if geometry_s.size else 0)))
    adequate_geometry = len(ids) >= 4 and geometry_rank == 3
    if not adequate_geometry:
        warnings.append("Inadequate 3D geometry: observe at least four spatially independent tag centres.")
    if information["poorly_conditioned"]:
        warnings.append("The physical shape is poorly conditioned; small range errors can cause large positional changes.")
    print("[Assess physical-network rigidity]" if certify else "[Assess local physical-network rank]", flush=True)
    edges = [(record.tag_a, record.tag_b) for record in records]
    topology = topology_certificate(ids, edges, {}) if certify else {
        "status": "unknown", "reason": "Not checked for this planning baseline.", "version": None, "elapsed_s": 0.0}
    neighbours = {tag: set() for tag in ids}
    for a, b in edges:
        neighbours[a].add(b)
        neighbours[b].add(a)
    remaining, components = set(ids), []
    while remaining:
        pending, component = [min(remaining)], set()
        while pending:
            tag = pending.pop()
            if tag not in component:
                component.add(tag)
                pending.extend(neighbours[tag] - component)
        components.append(sorted(component))
        remaining -= component
    redundancy = len(rows) - information["rank"]
    if redundancy <= 0:
        warnings.append("Redundancy is insufficient to check measurement errors reliably; "
                        "a small residual is not proof of accuracy.")
    ambiguous = topology["status"] != "rigid" or not adequate_geometry
    if ambiguous:
        warnings.append("Nonlinear uniqueness is not established; a local covariance cannot exclude alternative shapes.")
    covariance = information["covariance"]
    local_status = ("unknown" if solver["status"] == "unavailable" or not information["shape_dimension"]
                    else "unbounded" if information["nullity"] else "finite")
    status = "unknown" if local_status == "finite" and ambiguous else local_status
    if local_status != "finite":
        covariance = None
    ellipsoids = position_ellipsoids(ids, covariance) if covariance is not None else []
    worst = max(ellipsoids, key=lambda row: row["longest_semi_axis_95_m"], default=None)
    groups = relative_groups(ids, positions, information, edges) if solver["status"] != "unavailable" else []
    coverage = measurement_coverage(ids, rows, edges, [(r.tag_a, r.tag_b) for r, sigma in zip(records, sigmas) if sigma is None])
    diagnostics = {key: value.tolist() if isinstance(value, np.ndarray) else value
                   for key, value in information.items() if key not in ("Q", "covariance", "null_basis", "observable_root")}
    complete = not ambiguous and status == "finite" and not information["poorly_conditioned"]
    result = {
        "tag_ids": ids, "positions_m": positions.tolist(), "Q": information["Q"].tolist(),
        "covariance_m2": covariance.tolist() if covariance is not None else None,
        "null_basis": information["null_basis"].tolist(), "information": diagnostics,
        "completeness": {"status": "complete" if complete else "incomplete",
                         "active_tag_count": len(ids), "active_measurement_count": len(records),
                         "inactive_measurement_count": len(inactive), "inactive_measurements": inactive,
                         "unmeasured_tags": [tag for tag in ids if not neighbours[tag]], "components": components,
                         "remaining_motions": information["nullity"], "generic_rigidity": topology,
                         "actual_geometry_rank": geometry_rank, "actual_geometry_singular_values_m": geometry_s.tolist(),
                         "adequate_3d_geometry": adequate_geometry, "nonlinear_ambiguity": ambiguous,
                         "coincident_initial_pairs": coincident},
        "consistency": {"status": "unknown" if solver["status"] == "unavailable" else "assessed",
                        "residual_sign": "fitted-entered", "residuals": residuals, "redundancy": redundancy,
                        "can_check_errors": redundancy > 0 and solver["status"] != "unavailable",
                        "downweighted_pairs": sum(1 for r in residuals if r["weight"] is not None and r["weight"] < 1),
                        "rank_before_robust_weights": original_information["rank"],
                        "rank_after_robust_weights": information["rank"]},
        "measurement_coverage": coverage,
        "uncertainty": {"status": status, "local_status": local_status, "ellipsoids": ellipsoids, "relative_groups": groups,
                        "worst_tag": worst if status == "finite" else None, "local_worst_tag": worst,
                        "confidence": .95, "conversion": "sqrt(chi2.ppf(0.95,3)*eigenvalues)",
                        "convention": settings["covariance_convention"], "nonlinear_ambiguity": ambiguous,
                        "qualification": "Local and model-dependent; excludes tape bias, incorrect tag centres "
                                         "and scan systematic errors."},
        "solver": {**solver, "method": "GTSAM Point3 RangeFactor3 LevenbergMarquardt",
                   "linear_solver": settings["linear_solver"],
                   "loss": "Huber", "huber_k": settings["huber_k"], "sigma_rule": "pair_sigma_m or document.default_sigma_m",
                   "gauge_anchors": [ids[i] for i in anchors], "gauge_coordinates": ["A.xyz", "B.yz", "C.z"][:len(anchors)],
                   "display_rotation": rotation.tolist(), "scan_information": False, "damping_information": False},
        "settings": settings, "warnings": warnings,
        "runtime": {"dependencies": dependencies | {"pyrigi": topology["version"]},
                    "dependency_import_s": import_elapsed, "fit_s": fit_elapsed,
                    "rigidity_s": topology["elapsed_s"], "total_s": perf_counter() - started},
    }
    # Enforce finite JSON at the numerical boundary, including nested array values.
    fingerprint(result)
    write_json(output / "network.json", result)
    return result
