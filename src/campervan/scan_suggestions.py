"""One correlated, free-network range planner for checklists and placement comparisons."""

from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

from campervan.scan_measurements import MeasurementDocument
from campervan.scan_network import NETWORK_SETTINGS, free_network_information, pair_jacobian, topology_certificate
from campervan.scan_visibility import assess_segments
from campervan.scan_workflows import fingerprint
from campervan.scans import write_json

PLANNER_ALGORITHM_VERSION = "physical-pair-planner-1"
PLANNER_SETTINGS = {
    "network": NETWORK_SETTINGS, "selection": "connectivity-rank-rigidity-worst-ellipsoid",
    "reverse_delete": "proposed-only", "overlap_cosine": .9, "confidence": .95,
    "visibility": "finite-segment-observed-depth-2", "registration": "weighted-proper-rigid-no-scale",
}


def _pair(row: dict[str, Any]) -> tuple[int, int]:
    return row["tag_a"], row["tag_b"]


def _pair_wire(row: dict[str, Any]) -> dict[str, int]:
    return {"tag_a": row["tag_a"], "tag_b": row["tag_b"]}


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


def planning_state(network: dict[str, Any], measurements: MeasurementDocument) -> dict[str, Any]:
    """Keep the fitted coordinates and robust physical rows; capture is never an information prior."""
    ids = network["tag_ids"]
    positions = np.asarray(network["positions_m"], dtype=float).reshape((-1, 3))
    index = {tag: i for i, tag in enumerate(ids)}
    residuals = {_pair(row): row for row in network["consistency"]["residuals"]}
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
        weight = residuals[edge].get("weight")
        rows.append(h * np.sqrt(weight if weight is not None else 1.0) / sigma)
    state = {"ids": ids, "positions": positions, "rows": rows, "edges": edges,
             "unknown_precision": unknown_precision, "retained_ids": ids,
             "scan_dependent": network["completeness"]["status"] != "complete",
             "fit_available": network["solver"]["status"] != "unavailable"}
    return refresh_state(state, {}, certificate=network["completeness"]["generic_rigidity"])


def refresh_state(state: dict[str, Any], cache: dict, *, certificate: dict | None = None) -> dict[str, Any]:
    info = free_network_information(state["positions"], state["rows"], rtol=NETWORK_SETTINGS["rank_rtol"])
    state = state | {"information": info, "components": _components(state["ids"], state["edges"])}
    singular = np.linalg.svd(state["positions"] - state["positions"].mean(axis=0), compute_uv=False) if state["ids"] else []
    rank = int(np.count_nonzero(singular > singular[0] * NETWORK_SETTINGS["rank_rtol"])) if len(singular) else 0
    state["adequate_3d_geometry"] = len(state["ids"]) >= 4 and rank == 3
    if certificate is None and info["nullity"] == 0 and state["adequate_3d_geometry"]:
        certificate = topology_certificate(state["ids"], state["edges"], cache)
    state["topology"] = certificate
    return state


def _ellipsoids(state: dict[str, Any], covariance: Any) -> list[dict[str, Any]]:
    from scipy.stats import chi2

    if covariance is None or state["unknown_precision"] or not state["fit_available"]:
        return []
    ids, retained = state["ids"], state["retained_ids"]
    indices = [i for tag in retained for i in range(3 * ids.index(tag), 3 * ids.index(tag) + 3)]
    matrix = covariance[np.ix_(indices, indices)]
    if retained != ids:
        # Compare identical retained coverage in its own equal-weight rigid alignment.
        positions = state["positions"][[ids.index(tag) for tag in retained]]
        q = free_network_information(positions, [])["Q"]
        projection = q @ q.T
        matrix = projection @ matrix @ projection
    result = []
    conversion = chi2.ppf(.95, 3)
    for i, tag in enumerate(retained):
        values, directions = np.linalg.eigh(matrix[3*i:3*i+3, 3*i:3*i+3])
        axes = np.sqrt(conversion * np.maximum(values, 0))
        result.append({"tag_id": tag, "semi_axes_95_m": axes.tolist(), "directions": directions.tolist(),
                       "longest_semi_axis_95_m": float(axes[-1]), "worst_direction": directions[:, -1].tolist()})
    return result


def summary(state: dict[str, Any], target_mm: float) -> dict[str, Any]:
    info = state["information"]
    ellipsoids = _ellipsoids(state, info["covariance"])
    worst = max(ellipsoids, key=lambda value: value["longest_semi_axis_95_m"], default=None)
    rigid = state["topology"] is not None and state["topology"]["status"] == "rigid"
    bounded = bool(worst) and rigid and state["adequate_3d_geometry"]
    status = "finite" if bounded else "unbounded" if info["nullity"] else "unknown"
    return {"status": status, "components": state["components"], "rank": info["rank"],
            "shape_dimension": info["shape_dimension"], "remaining_motions": info["nullity"],
            "generic_rigidity": state["topology"], "adequate_3d_geometry": state["adequate_3d_geometry"],
            "poorly_conditioned": info["poorly_conditioned"], "condition_number": info["condition_number"],
            "ellipsoids": ellipsoids, "local_worst_tag": worst, "worst_tag": worst if bounded else None,
            "target_met": bool(bounded and not info["poorly_conditioned"] and
                               worst["longest_semi_axis_95_m"] * 1000 <= target_mm),
            "measurement_count": len(state["edges"]), "retained_tag_ids": state["retained_ids"],
            "unknown_precision_pairs": [{"tag_a": a, "tag_b": b} for a, b in state["unknown_precision"]]}


def enumerate_pairs(network: dict[str, Any], measurements: MeasurementDocument,
                    candidate_sigmas: dict[str, float]) -> list[dict[str, Any]]:
    ids = network["tag_ids"]
    positions = np.asarray(network["positions_m"], dtype=float).reshape((-1, 3))
    measured = {(row.tag_a, row.tag_b): row for row in measurements.distances}
    excluded = {(row.tag_a, row.tag_b): row.reason for row in measurements.excluded_pairs}
    residuals = {_pair(row): row for row in network["consistency"]["residuals"]}
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
    h = pair_jacobian(state["positions"], ids.index(a), ids.index(b))
    sigma = pair["sigma_m"]
    if sigma is None:
        raise ValueError("Candidate measuring precision is unknown.")
    projected = h @ info["null_basis"] / sigma
    energy = float(projected @ projected)
    scale = max(float(np.linalg.norm(h / sigma)),
                float(info["singular_values"][0]) if len(info["singular_values"]) else 0)
    rank_reduction = int(energy ** .5 > scale * NETWORK_SETTINGS["rank_rtol"])
    if info["nullity"] and rank_reduction:
        # A new precise row can also raise the relative cutoff; confirm the actual shape-rank gain.
        after_information = free_network_information(state["positions"], [*state["rows"], h / sigma],
                                                     rtol=NETWORK_SETTINGS["rank_rtol"])
        rank_reduction = max(0, after_information["rank"] - info["rank"])
    component = {tag: i for i, tags in enumerate(state["components"]) for tag in tags}
    gain = {"rank_reduction": rank_reduction, "connectivity_reduction": int(component[a] != component[b]),
            "null_mode_energy": energy, "information_gain": None, "max_tag_reduction_mm": None,
            "global_worst_reduction_mm": None, "most_improved_tag_id": None, "tag_reductions_mm": {}}
    covariance = info["covariance"]
    if covariance is not None:
        ch = covariance @ h
        variance = max(0.0, float(h @ ch))
        after = covariance - np.outer(ch, ch) / (sigma * sigma + variance)
        gain["information_gain"] = float(np.log1p(variance / (sigma * sigma)))
        before_tags, after_tags = _ellipsoids(state, covariance), _ellipsoids(state, after)
        if before_tags:
            reductions = [(before["longest_semi_axis_95_m"] - later["longest_semi_axis_95_m"]) * 1000
                          for before, later in zip(before_tags, after_tags, strict=True)]
            best = int(np.argmax(reductions))
            gain.update(max_tag_reduction_mm=max(0.0, float(reductions[best])),
                        most_improved_tag_id=before_tags[best]["tag_id"],
                        global_worst_reduction_mm=max(0.0, (max(t["longest_semi_axis_95_m"] for t in before_tags) -
                                                          max(t["longest_semi_axis_95_m"] for t in after_tags)) * 1000),
                        tag_reductions_mm={str(t["tag_id"]): max(0.0, float(v))
                                           for t, v in zip(before_tags, reductions, strict=True)})
            if (state["topology"] is None or state["topology"]["status"] != "rigid" or
                    not state["adequate_3d_geometry"]):
                gain["global_worst_reduction_mm"] = None
    return gain


def _add(state: dict[str, Any], pair: dict[str, Any], cache: dict) -> dict[str, Any]:
    a, b = _pair(pair)
    row = pair_jacobian(state["positions"], state["ids"].index(a), state["ids"].index(b)) / pair["sigma_m"]
    return refresh_state(state | {"rows": [*state["rows"], row], "edges": [*state["edges"], (a, b)]}, cache)


def _useful(gain: dict[str, Any], state: dict[str, Any], improvement_mm: float) -> bool:
    # Uncertified full-rank topologies still need extra physical ties; do not invent a finite global gain.
    topology_needed = (state["information"]["nullity"] == 0 and state["adequate_3d_geometry"] and
                       (state["topology"] is None or state["topology"]["status"] != "rigid"))
    return bool(gain["connectivity_reduction"] or gain["rank_reduction"] or topology_needed or
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
        if budget is None and mode == "initial" and current["target_met"]:
            stop = "Predicted target and generic rigidity reached."
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
        topology_needed = not current["generic_rigidity"] or current["generic_rigidity"]["status"] != "rigid"

        def priority(item):
            pair, gain = item
            geometric = gain["null_mode_energy"] if current["remaining_motions"] else (
                gain["information_gain"] or 0) if topology_needed else (gain["global_worst_reduction_mm"] or 0)
            return (-gain["connectivity_reduction"], -gain["rank_reduction"], -geometric,
                    -(gain["max_tag_reduction_mm"] or 0), pair["clearance"] != "no_obstruction_detected",
                    pair["estimate_m"], pair["tag_a"], pair["tag_b"])

        pair, gain = min(scored, key=priority)
        selected.append(pair | {"marginal_gain": gain})
        state = _add(state, pair, cache)
        available = [value for value in available if _pair(value) != _pair(pair)]
    if summary(state, target_mm)["target_met"] and mode == "initial" and budget is None:
        stop = "Predicted target and generic rigidity reached."
    if summary(state, target_mm)["target_met"] and reverse_delete and mode == "initial" and budget is None:
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
            if summary(trial, target_mm)["target_met"]:
                selected, state = remaining, trial
        # Report marginal effects in the retained order, not the superseded greedy prefix.
        state = original
        for pair in selected:
            pair["marginal_gain"] = score_addition(state, pair)
            state = _add(state, pair, cache)
        stop = "Predicted target and generic rigidity reached; redundant proposed pairs were reverse-deleted."
    return selected, state, stop


def plan_measurements(run: Path, manifest: dict[str, Any], measurements: MeasurementDocument,
                      network: dict[str, Any], planning: dict[str, Any], output: Path,
                      *, mode: str = "initial", cache: dict | None = None) -> dict[str, Any]:
    from campervan.scan_analysis import register_measured_shape

    print("[Plan physical tape measurements]", flush=True)
    state = planning_state(network, measurements)
    pairs = enumerate_pairs(network, measurements, planning["candidate_sigmas"])
    captured = {tag["id"]: np.asarray(tag["pose"], dtype=float)[:3, 3] for tag in manifest.get("tags", [])}
    registration = register_measured_shape(network, captured)
    positions = registration["positions"]
    moved = {tag: float(np.linalg.norm(point - captured[tag])) for tag, point in positions.items()}
    assess_segments(run, pairs, positions, moved, manifest=manifest)
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
            pair["useful"] = _useful(gain, state, planning["improvement_mm"])
            pair["reason"] = ("Restores a missing connection or shape mode." if gain["rank_reduction"] or
                              gain["connectivity_reduction"] else "Reinforces the network against ambiguity." if
                              state["topology"]["status"] != "rigid" else
                              "Reduces an individual tag's longest positional ellipsoid axis." if pair["useful"] else
                              "Below the individual-tag meaningful improvement threshold.")
        if pair["manual_exclusion"] is not None:
            pair["reason"] = "Manually excluded: " + pair["manual_exclusion"]
        elif pair["clearance"] == "obstructed":
            pair["reason"] = pair["clearance_reason"]
    selected, predicted, stop = select_batch(state, pairs, planning["target_mm"], planning["improvement_mm"],
                                            mode=mode, cache=cache)
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
              "baseline": summary(state, planning["target_mm"]), "predicted": summary(predicted, planning["target_mm"]),
              "stop_reason": stop, "settings": PLANNER_SETTINGS,
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
