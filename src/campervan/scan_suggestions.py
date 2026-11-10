"""One correlated, free-network range planner for checklists and placement comparisons."""

from itertools import combinations
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from campervan.scan_measurements import MeasurementDocument
from campervan.scan_network import (
    NETWORK_SETTINGS, coverage_diagnostic, free_network_information, measurement_coverage,
    pair_jacobian, position_ellipsoids, relative_groups,
    topology_certificate, topology_deficits,
    uncertainty_conversion as _confidence_conversion,
)
from campervan.scan_visibility import assess_segments
from campervan.scan_workflows import fingerprint
from campervan.scans import write_json

PLANNER_ALGORITHM_VERSION = "physical-pair-planner-4"
PLANNER_SETTINGS = {
    "network": NETWORK_SETTINGS, "selection": "connectivity-rank-rigidity-worst-ellipsoid",
    "reverse_delete": "proposed-only", "overlap_cosine": .9, "confidence": .95,
    "visibility": "finite-segment-observed-depth-4", "registration": "registered-shape-or-captured-estimate",
    "certification": "final-graph-only", "prediction": "fixed-geometry-correlated-update",
}


def _pair(row: dict[str, Any]) -> tuple[int, int]:
    return row["tag_a"], row["tag_b"]


def _pair_wire(row: dict[str, Any]) -> dict[str, int]:
    return {"tag_a": row["tag_a"], "tag_b": row["tag_b"]}


def source_associations(registration: dict[str, Any], captured: dict[int, Any]) -> tuple[dict[int, Any], dict[int, float]]:
    """Use registered endpoints or the captured geometry itself, never an unregistered fitted deformation."""
    if registration["status"] != "registered":
        return captured, {tag: 0.0 for tag in captured}
    positions = registration["positions"]
    moved = {tag: float(np.linalg.norm(point - captured[tag])) for tag, point in positions.items()}
    return positions, moved


def _components(ids: list[int], edges: list[tuple[int, int]]) -> list[list[int]]:
    neighbours = {tag: set() for tag in ids}
    for a, b in edges:
        neighbours[a].add(b)
        neighbours[b].add(a)
    remaining, result = set(ids), []
    while remaining:
        pending, component = [min(remaining)], set()
        while pending:
            tag = pending.pop()
            if tag not in component:
                component.add(tag)
                pending.extend(neighbours[tag] - component)
        result.append(sorted(component))
        remaining -= component
    return result


def planning_state(network: dict[str, Any] | None, measurements: MeasurementDocument, *,
                   positions: Any = None, ids: list[int] | None = None,
                   basis: str = "registered_measured_shape") -> dict[str, Any]:
    """Linearize actual ranges at explicit planning coordinates; capture supplies no information rows."""
    ids = network["tag_ids"] if network else ids
    if ids is None or positions is None and network is None:
        raise ValueError("Planning requires explicit tag IDs and positions.")
    positions = np.asarray(network["positions_m"] if positions is None else positions, dtype=float).reshape((-1, 3))
    index = {tag: i for i, tag in enumerate(ids)}
    residuals = {_pair(row): row for row in network["consistency"]["residuals"]} if network else {}
    rows, edges, unknown_precision = [], [], []
    for record in measurements.distances:
        if record.tag_a not in index or record.tag_b not in index:
            continue
        edge = (record.tag_a, record.tag_b)
        edges.append(edge)
        sigma = record.sigma_m or measurements.default_sigma_m
        if sigma is None:
            unknown_precision.append(edge)
            continue
        try:
            h = pair_jacobian(positions, index[edge[0]], index[edge[1]])
        except ValueError:
            continue
        weight = residuals.get(edge, {}).get("weight")
        rows.append(h * np.sqrt(weight if weight is not None else 1.0) / sigma)
    state = {"ids": ids, "positions": positions, "rows": rows, "edges": edges,
             "unknown_precision": unknown_precision, "retained_ids": ids,
             "scan_dependent": basis == "captured_estimate", "planning_basis": basis,
             "fit_available": True, "pair_rows": {}}
    return refresh_state(state, {}, certificate=network["completeness"]["generic_rigidity"] if network else None)


def refresh_state(state: dict[str, Any], cache: dict, *, certificate: dict | None = None) -> dict[str, Any]:
    q = state.get("information", {}).get("Q")
    if q is not None and q.shape[0] != state["positions"].size:
        q = None
    info = free_network_information(state["positions"], state["rows"], rtol=NETWORK_SETTINGS["rank_rtol"], q=q)
    state = state | {"information": info, "components": _components(state["ids"], state["edges"])}
    singular = np.linalg.svd(state["positions"] - state["positions"].mean(axis=0), compute_uv=False) if state["ids"] else []
    rank = int(np.count_nonzero(singular > singular[0] * NETWORK_SETTINGS["rank_rtol"])) if len(singular) else 0
    state["adequate_3d_geometry"] = len(state["ids"]) >= 4 and rank == 3
    pairs = sorted(set(tuple(sorted(edge)) for edge in state["edges"]))
    state["topology"] = (certificate if certificate is not None and certificate.get("vertices") == state["ids"]
                         and sorted(tuple(edge) for edge in certificate.get("edges", [])) == pairs else None)
    state["ellipsoids"] = _ellipsoids(state, info["covariance"])
    state["coverage"] = measurement_coverage(state["ids"], state["rows"], state["edges"], state["unknown_precision"])
    return state


def _ellipsoids(state: dict[str, Any], covariance: Any) -> list[dict[str, Any]]:
    if covariance is None or state["unknown_precision"] or not state["fit_available"]:
        return []
    ids, retained = state["ids"], state["retained_ids"]
    indices = [i for tag in retained for i in range(3 * ids.index(tag), 3 * ids.index(tag) + 3)]
    matrix = covariance[np.ix_(indices, indices)]
    if retained != ids:
        # Compare identical retained coverage in its own equal-weight rigid alignment.
        positions = state["positions"][[ids.index(tag) for tag in retained]]
        projection = state.get("retained_projection")
        if projection is None:
            q = free_network_information(positions, [])["Q"]
            projection = state["retained_projection"] = q @ q.T
        matrix = projection @ matrix @ projection
    return position_ellipsoids(retained, matrix)


def summary(state: dict[str, Any], target_mm: float, *, include_groups: bool = False) -> dict[str, Any]:
    info = state["information"]
    ellipsoids = state["ellipsoids"]
    worst = max(ellipsoids, key=lambda value: value["longest_semi_axis_95_m"], default=None)
    rigid = state["topology"] is not None and state["topology"]["status"] == "rigid"
    bounded = bool(worst) and rigid and state["adequate_3d_geometry"]
    status = "finite" if bounded else "unbounded" if info["nullity"] else "unknown"
    local_target = bool(worst and state["adequate_3d_geometry"] and not info["poorly_conditioned"] and
                        worst["longest_semi_axis_95_m"] * 1000 <= target_mm)
    edge_deficit, degree_deficits = topology_deficits(state["ids"], state["edges"])
    return {"status": status, "components": state["components"], "rank": info["rank"],
            "shape_dimension": info["shape_dimension"], "remaining_motions": info["nullity"],
            "generic_rigidity": state["topology"], "adequate_3d_geometry": state["adequate_3d_geometry"],
            "poorly_conditioned": info["poorly_conditioned"], "condition_number": info["condition_number"],
            "ellipsoids": ellipsoids, "local_worst_tag": worst, "worst_tag": worst if bounded else None,
            "target_met": bool(bounded and local_target), "local_target_met": local_target,
            "necessary_topology_met": not edge_deficit and not any(degree_deficits.values()),
            "planning_basis": state["planning_basis"],
            "unbounded_tag_ids": [tag for i, tag in enumerate(state["ids"])
                                  if np.linalg.norm(info["null_basis"][3*i:3*i+3]) > NETWORK_SETTINGS["rank_rtol"]],
            "relative_groups": relative_groups(state["ids"], state["positions"], info, state["edges"])
            if include_groups and not state["unknown_precision"] else [],
            "measurement_coverage": state["coverage"],
            "measurement_count": len(state["edges"]), "retained_tag_ids": state["retained_ids"],
            "unknown_precision_pairs": [{"tag_a": a, "tag_b": b} for a, b in state["unknown_precision"]]}


def enumerate_pairs(state: dict[str, Any], measurements: MeasurementDocument,
                    candidate_sigmas: dict[str, float], network: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    ids, positions = state["ids"], state["positions"]
    measured = {(row.tag_a, row.tag_b): row for row in measurements.distances}
    excluded = {(row.tag_a, row.tag_b): row.reason for row in measurements.excluded_pairs}
    residuals = {_pair(row): row for row in network["consistency"]["residuals"]} if network else {}
    result = []
    for i, j in combinations(range(len(ids)), 2):
        a, b = ids[i], ids[j]
        record = measured.get((a, b))
        sigma = (record.sigma_m or measurements.default_sigma_m) if record else candidate_sigmas.get(
            f"{a}:{b}", measurements.default_sigma_m)
        residual = residuals.get((a, b), {})
        suspect = record and (abs(residual.get("standardised_residual") or 0) > 2 or
                              sigma is not None and measurements.default_sigma_m is not None and
                              sigma > measurements.default_sigma_m)
        result.append({"tag_a": a, "tag_b": b, "state": "recheck" if suspect else "measured" if record else "proposed",
                       "estimate_m": float(np.linalg.norm(positions[i] - positions[j])), "sigma_m": sigma,
                       "manual_exclusion": excluded.get((a, b)), "clearance": "unknown",
                       "clearance_reason": "Source evidence has not been assessed.", "hit": None,
                       "observed_fraction": None, "tolerance_m": None, "check_access": True,
                       "eligible": False, "useful": False, "recommended_order": None,
                       "baseline_gain": None, "marginal_gain": None, "overlaps_with": [], "reason": ""})
    return result


def score_addition(state: dict[str, Any], pair: dict[str, Any]) -> dict[str, Any]:
    """Full correlated update in the fixed free-network complement; no symbolic graph call per pair."""
    ids, info = state["ids"], state["information"]
    a, b = _pair(pair)
    h = _row(state, pair)
    sigma = pair["sigma_m"]
    if sigma is None:
        raise ValueError("Candidate measuring precision is unknown.")
    projected = h @ info["null_basis"] / sigma
    energy = float(projected @ projected)
    scale = max(float(np.linalg.norm(h / sigma)),
                float(info["singular_values"][0]) if len(info["singular_values"]) else 0)
    rank_reduction = int(energy ** .5 > scale * NETWORK_SETTINGS["rank_rtol"])
    edge_deficit, degrees = topology_deficits(ids, state["edges"])
    component = {tag: i for i, tags in enumerate(state["components"]) for tag in tags}
    gain = {"rank_reduction": rank_reduction, "connectivity_reduction": int(component[a] != component[b]),
            "structural_gain": int(degrees[a] > 0) + int(degrees[b] > 0) + int(edge_deficit > 0),
            "null_mode_energy": energy, "information_gain": None, "max_tag_reduction_mm": None,
            "global_worst_reduction_mm": None, "most_improved_tag_id": None, "tag_reductions_mm": {},
            "coverage_rank_reduction": 0, "coverage_gain_mm": None, "coverage_tag_gains": {}}
    for tag in (a, b):
        index = ids.index(tag)
        before = state["coverage"][index]
        after = coverage_diagnostic(tag, [*before["factor"], (h[3*index:3*index+3] / sigma).tolist()],
                                    before["neighbour_ids"], precision_available=before["precision_available"],
                                    include_ellipsoid=False)
        rank_gain = max(0, after["rank"] - before["rank"])
        reduction = None
        if before["conditional_radius_95_m"] is not None and after["conditional_radius_95_m"] is not None:
            reduction = max(0.0, (before["conditional_radius_95_m"] - after["conditional_radius_95_m"]) * 1000)
        gain["coverage_rank_reduction"] += rank_gain
        gain["coverage_tag_gains"][str(tag)] = {"rank_reduction": rank_gain, "reduction_mm": reduction}
        if reduction is not None:
            gain["coverage_gain_mm"] = max(gain["coverage_gain_mm"] or 0.0, reduction)
    covariance = info["covariance"]
    if covariance is not None:
        ch = covariance @ h
        variance = max(0.0, float(h @ ch))
        denominator = sigma * sigma + variance
        gain["information_gain"] = float(np.log1p(variance / (sigma * sigma)))
        before_tags = state["ellipsoids"]
        # Normal plans need only the updated 3x3 tag blocks. Retained-coverage comparisons also project
        # away the retained subset's rigid motion, so use the same full correlated convention there.
        if state["retained_ids"] != ids:
            after_tags = _ellipsoids(state, covariance - np.outer(ch, ch) / denominator)
            after_lengths = [tag["longest_semi_axis_95_m"] for tag in after_tags]
        else:
            blocks = np.asarray([covariance[3*i:3*i+3, 3*i:3*i+3] -
                                 np.outer(ch[3*i:3*i+3], ch[3*i:3*i+3]) / denominator for i in range(len(ids))])
            after_lengths = np.sqrt(_confidence_conversion() * np.maximum(np.linalg.eigvalsh(blocks)[:, -1], 0)).tolist()
        if before_tags:
            reductions = [(before["longest_semi_axis_95_m"] - later) * 1000
                          for before, later in zip(before_tags, after_lengths, strict=True)]
            best = int(np.argmax(reductions))
            gain.update(max_tag_reduction_mm=max(0.0, float(reductions[best])),
                        most_improved_tag_id=before_tags[best]["tag_id"],
                        global_worst_reduction_mm=max(0.0, (max(t["longest_semi_axis_95_m"] for t in before_tags) -
                                                          max(after_lengths)) * 1000),
                        tag_reductions_mm={str(t["tag_id"]): max(0.0, float(v))
                                           for t, v in zip(before_tags, reductions, strict=True)})
            if (state["topology"] is None or state["topology"]["status"] != "rigid" or
                    not state["adequate_3d_geometry"]):
                gain["global_worst_reduction_mm"] = None
    return gain


def _row(state: dict[str, Any], pair: dict[str, Any]) -> Any:
    key = _pair(pair)
    if key not in state["pair_rows"]:
        state["pair_rows"][key] = pair_jacobian(state["positions"], state["ids"].index(key[0]),
                                               state["ids"].index(key[1]))
    return state["pair_rows"][key]


def _add(state: dict[str, Any], pair: dict[str, Any], cache: dict) -> dict[str, Any]:
    a, b = _pair(pair)
    row = _row(state, pair) / pair["sigma_m"]
    return refresh_state(state | {"rows": [*state["rows"], row], "edges": [*state["edges"], (a, b)]}, cache)


def _useful(gain: dict[str, Any], state: dict[str, Any], improvement_mm: float) -> bool:
    return bool(gain["connectivity_reduction"] or gain["rank_reduction"] or gain["coverage_rank_reduction"] or gain["structural_gain"] or
                gain["coverage_gain_mm"] is not None and gain["coverage_gain_mm"] >= improvement_mm or
                gain["max_tag_reduction_mm"] is not None and gain["max_tag_reduction_mm"] >= improvement_mm)


def select_batch(state: dict[str, Any], pairs: list[dict[str, Any]], target_mm: float, improvement_mm: float,
                 *, mode: str = "initial", budget: int | None = None, reverse_delete: bool = True,
                 cache: dict | None = None) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    """Recompute each marginal benefit. Reverse deletion never touches entered distances."""
    cache = {} if cache is None else cache
    original, selected = state, []
    available = [pair for pair in pairs if pair["state"] == "proposed" and pair["eligible"]]
    stop = "No feasible unmeasured candidates remain. Review placement, access or measuring precision."
    while available:
        current = summary(state, target_mm)
        if budget is not None and len(selected) >= budget:
            stop = "Common measurement budget reached."
            break
        if budget is None and mode == "initial" and current["local_target_met"] and current["necessary_topology_met"]:
            stop = "Local precision target and necessary topology conditions reached; uniqueness checked separately."
            break
        scored = [(pair, score_addition(state, pair)) for pair in available]
        if current["remaining_motions"] and not any(gain["rank_reduction"] or gain["connectivity_reduction"]
                                                   for _, gain in scored):
            stop = "No available single pair restores a remaining shape mode at the current numerical tolerance. Review placement or precision."
            break
        if mode == "additional":
            scored = [(pair, gain) for pair, gain in scored if _useful(gain, state, improvement_mm)]
        if not scored:
            stop = "No remaining pair meets the marginal improvement threshold or restores a missing constraint."
            break
        def priority(item):
            pair, gain = item
            geometric = gain["null_mode_energy"] if current["remaining_motions"] else (
                gain["information_gain"] or 0) if not current["necessary_topology_met"] else (
                gain["global_worst_reduction_mm"] if gain["global_worst_reduction_mm"] is not None else
                gain["max_tag_reduction_mm"] or 0)
            return (-gain["connectivity_reduction"], -gain["rank_reduction"], -gain["coverage_rank_reduction"],
                    -gain["structural_gain"], -geometric,
                    -(gain["max_tag_reduction_mm"] or 0), pair["clearance"] != "no_obstruction_detected",
                    pair["estimate_m"], pair["tag_a"], pair["tag_b"])

        pair, gain = min(scored, key=priority)
        selected.append(pair | {"marginal_gain": gain})
        state = _add(state, pair, cache)
        available = [value for value in available if _pair(value) != _pair(pair)]
        print(f"[Selected {len(selected)} additional pairs; {state['information']['nullity']} shape motions remain]", flush=True)
    achieved = summary(state, target_mm)
    if achieved["local_target_met"] and achieved["necessary_topology_met"] and mode == "initial" and budget is None:
        stop = "Local precision target and necessary topology conditions reached; uniqueness checked separately."
    if achieved["local_target_met"] and achieved["necessary_topology_met"] and reverse_delete and mode == "initial" and budget is None:
        print("[Prune unnecessary proposed measurements]", flush=True)
        for candidate in list(reversed(selected)):
            remaining = [value for value in selected if _pair(value) != _pair(candidate)]
            trial = original
            # Only certify the complete trial topology; intermediate exact checks add no evidence here.
            trial_rows, trial_edges = list(original["rows"]), list(original["edges"])
            for pair in remaining:
                a, b = _pair(pair)
                trial_rows.append(pair_jacobian(trial["positions"], trial["ids"].index(a),
                                               trial["ids"].index(b)) / pair["sigma_m"])
                trial_edges.append((a, b))
            trial = refresh_state(trial | {"rows": trial_rows, "edges": trial_edges}, cache)
            trial_summary = summary(trial, target_mm)
            if trial_summary["local_target_met"] and trial_summary["necessary_topology_met"]:
                selected, state = remaining, trial
        # Report marginal effects in the retained order, not the superseded greedy prefix.
        state = original
        for pair in selected:
            pair["marginal_gain"] = score_addition(state, pair)
            state = _add(state, pair, cache)
        stop = "Local target reached; unnecessary proposed pairs removed. Global uniqueness is checked separately."
    return selected, state, stop


def score_pairs(state: dict[str, Any], pairs: list[dict[str, Any]], planning: dict[str, Any]) -> None:
    """One baseline scoring policy for placement repairs and both checklist modes."""
    for pair in pairs:
        pair["check_access"] = pair["clearance"] == "unknown"
        pair["eligible"] = (pair["state"] == "proposed" and pair["manual_exclusion"] is None and
                            pair["clearance"] != "obstructed" and pair["sigma_m"] is not None and
                            pair["estimate_m"] >= NETWORK_SETTINGS["coincident_m"])
        if pair["state"] != "proposed":
            pair["reason"] = ("Recheck by editing this observation; it is not an independent new range."
                              if pair["state"] == "recheck" else "Entered physical observation is preserved.")
        elif pair["sigma_m"] is None:
            pair["reason"] = "Set measuring precision to predict this pair's contribution."
        elif pair["estimate_m"] < NETWORK_SETTINGS["coincident_m"]:
            pair["reason"] = "Coincident planning centres have no usable range derivative."
        else:
            gain = score_addition(state, pair)
            pair["baseline_gain"] = gain
            pair["useful"] = pair["eligible"] and _useful(gain, state, planning["improvement_mm"])
            pair["reason"] = ("Restores a missing connection or shape mode." if gain["rank_reduction"] or
                              gain["connectivity_reduction"] else "Reinforces the network against ambiguity." if
                              gain["structural_gain"] else
                              "Reduces an individual tag's longest positional ellipsoid axis." if pair["useful"] else
                              "Below the individual-tag meaningful improvement threshold.")
        if pair["manual_exclusion"] is not None:
            pair["reason"] = "Manually excluded: " + pair["manual_exclusion"]
        elif pair["clearance"] == "obstructed":
            pair["reason"] = pair["clearance_reason"]


def repair_pairs(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """All individually useful alternatives; gains share a baseline and cannot be added."""
    return sorted((pair for pair in pairs if pair["eligible"] and pair["useful"]), key=lambda pair: (
        -pair["baseline_gain"]["rank_reduction"], -pair["baseline_gain"]["coverage_rank_reduction"],
        -(pair["baseline_gain"]["coverage_gain_mm"] or 0),
        -(pair["baseline_gain"]["max_tag_reduction_mm"] or 0),
        pair["clearance"] != "no_obstruction_detected", pair["estimate_m"], pair["tag_a"], pair["tag_b"]))


def plan_measurements(run: Path, manifest: dict[str, Any], measurements: MeasurementDocument,
                      network: dict[str, Any], planning: dict[str, Any], output: Path,
                      *, mode: str = "initial", cache: dict | None = None) -> dict[str, Any]:
    from campervan.scan_analysis import register_measured_shape

    started = perf_counter()
    print("[Assess tape paths at planning coordinates]", flush=True)
    captured = {tag["id"]: np.asarray(tag["pose"], dtype=float)[:3, 3] for tag in manifest.get("tags", [])}
    registration = register_measured_shape(network, captured)
    positions, moved = source_associations(registration, captured)
    state = planning_state(network, measurements, positions=[positions[tag] for tag in network["tag_ids"]],
                           basis="registered_measured_shape" if registration["status"] == "registered" else
                           "captured_estimate")
    pairs = enumerate_pairs(state, measurements, planning["candidate_sigmas"], network)
    assess_segments(run, pairs, positions, moved, manifest=manifest)
    visibility_elapsed = perf_counter() - started
    score_pairs(state, pairs, planning)
    print("[Select informative measurements]", flush=True)
    selection_started = perf_counter()
    selected, predicted, stop = select_batch(state, pairs, planning["target_mm"], planning["improvement_mm"],
                                            mode=mode, cache=cache)
    selection_elapsed = perf_counter() - selection_started
    print("[Check final measurement plan for global ambiguity]", flush=True)
    certificate = topology_certificate(predicted["ids"], predicted["edges"], cache)
    predicted = predicted | {"topology": certificate}
    if certificate["status"] != "rigid":
        stop += " This is a provisional checklist: global uniqueness has not been established."
    selected_map = {_pair(pair): (i + 1, pair["marginal_gain"]) for i, pair in enumerate(selected)}
    useful = [pair for pair in pairs if pair["state"] == "proposed" and pair["useful"]]
    useful.sort(key=lambda pair: (-pair["baseline_gain"]["connectivity_reduction"],
                                 -pair["baseline_gain"]["rank_reduction"],
                                 -(pair["baseline_gain"]["global_worst_reduction_mm"] or 0),
                                 -(pair["baseline_gain"]["max_tag_reduction_mm"] or 0),
                                 -pair["baseline_gain"]["null_mode_energy"],
                                 pair["clearance"] != "no_obstruction_detected", pair["estimate_m"],
                                 pair["tag_a"], pair["tag_b"]))
    for pair in useful:
        profile = np.array(list(pair["baseline_gain"]["tag_reductions_mm"].values()))
        if profile.size and np.linalg.norm(profile):
            for other in useful:
                if other is pair:
                    continue
                comparison = np.array(list(other["baseline_gain"]["tag_reductions_mm"].values()))
                norm = np.linalg.norm(profile) * np.linalg.norm(comparison)
                if norm and profile @ comparison / norm >= PLANNER_SETTINGS["overlap_cosine"]:
                    pair["overlaps_with"].append(_pair_wire(other))
    for pair in pairs:
        if _pair(pair) in selected_map:
            pair["recommended_order"], pair["marginal_gain"] = selected_map[_pair(pair)]
    result = {"mode": mode, "tag_ids": state["ids"], "target_mm": planning["target_mm"],
              "improvement_mm": planning["improvement_mm"], "default_sigma_m": measurements.default_sigma_m,
              "rows": pairs, "recommended_pairs": [_pair_wire(pair) for pair in selected],
              "alternatives": [_pair_wire(pair) for pair in useful if _pair(pair) not in selected_map],
              "rechecks": [_pair_wire(pair) for pair in pairs if pair["state"] == "recheck"],
              "baseline": summary(state, planning["target_mm"], include_groups=True),
              "predicted": summary(predicted, planning["target_mm"], include_groups=True),
              "stop_reason": stop, "settings": PLANNER_SETTINGS,
              "runtime": {"visibility_s": visibility_elapsed, "selection_s": selection_elapsed,
                          "rigidity_s": certificate["elapsed_s"], "total_s": perf_counter() - started,
                          "candidate_count": len(pairs), "selected_count": len(selected)},
              "registration": {key: value for key, value in registration.items()
                               if key in ("status", "reasons", "scan_dependent_tag_ids")},
              "notes": ["Planning coordinates and prospective ranges are estimates, never entered physical distances.",
                        "All individual gains share one baseline and overlap; do not add them. The batch uses sequential marginal gains.",
                        "Predictions are local and model-dependent, not achieved accuracy or a globally minimal checklist.",
                        "Unknown clearance requires checking access; a mesh miss alone is not a free-space observation.",
                        "Partial best-effort correction remains available even when this target is unattainable."]}
    if state["scan_dependent"]:
        result["notes"].append("Incomplete physical constraints leave planning geometry scan-dependent.")
    if not state["adequate_3d_geometry"]:
        result["notes"].append("At least four spatially independent tag centres are needed; coplanar or collinear positions cannot establish adequate 3D geometry.")
    if state["unknown_precision"]:
        result["notes"].append("Some entered ranges have no measuring precision. Set their precision before finite prediction is possible.")
    if not state["fit_available"]:
        result["notes"].append("The physical fit is unavailable; finite precision gains are not reported.")
    fingerprint(result)
    write_json(output / "plan.json", result)
    return result


def suggest_more(run: Path, manifest: dict[str, Any], measurements: MeasurementDocument,
                 network: dict[str, Any], planning: dict[str, Any], output: Path) -> dict[str, Any]:
    return plan_measurements(run, manifest, measurements, network, planning, output, mode="additional")
