"""Placement advice with retained coverage and the same pair planner and effort budget."""

from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from campervan.scan_measurements import MeasurementDocument
from campervan.scan_network import NETWORK_SETTINGS, pair_jacobian
from campervan.scan_suggestions import (
    PLANNER_SETTINGS, enumerate_pairs, planning_state, refresh_state, repair_pairs, score_pairs, select_batch, summary,
)
from campervan.scan_visibility import assess_segments
from campervan.scan_workflows import fingerprint
from campervan.scans import read_json, write_json

PLACEMENT_ALGORITHM_VERSION = "captured-placement-4"
PLACEMENT_SETTINGS = {"planner": PLANNER_SETTINGS, "comparison": "same-retained-tags-same-added-range-budget",
                      "candidate_source": "reviewed-interior-mounting-access-support"}


def _observation_support(run: Path, manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Original camera links describe available views; counts are not precision estimates."""
    result = {tag["id"]: {"observation_count": tag.get("observations"), "viewpoint_count": None,
                          "maximum_view_angle_deg": None,
                          "consistency": "Not calibrated by this report.", "missing": []}
              for tag in manifest.get("tags", [])}
    if not (run / "graph.json").is_file():
        for item in result.values():
            item["missing"].append("Original camera/tag observations are unavailable.")
        return result
    graph = read_json(run / "graph.json")
    poses = graph["poses"]
    cameras = {tag: set() for tag in result}
    for link in graph["links"]:
        if link["kind"] != 8:
            continue
        a, b = link["from_id"], link["to_id"]
        if a > 0 > b and -b in cameras:
            cameras[-b].add(a)
        elif b > 0 > a and -a in cameras:
            cameras[-a].add(b)
    centres = {tag["id"]: np.asarray(tag["pose"])[:3, 3] for tag in manifest.get("tags", [])}
    for tag, observers in cameras.items():
        directions = []
        for camera in sorted(observers):
            if str(camera) not in poses:
                continue
            direction = np.asarray(poses[str(camera)])[:3, 3] - centres[tag]
            norm = np.linalg.norm(direction)
            if norm > 0:
                directions.append(direction / norm)
        result[tag]["viewpoint_count"] = len(directions)
        if len(directions) > 1:
            result[tag]["maximum_view_angle_deg"] = float(np.degrees(np.arccos(np.clip(
                np.min(np.asarray(directions) @ np.asarray(directions).T), -1, 1))))
        else:
            result[tag]["missing"].append("At least two source camera viewpoints are needed to describe angular spread.")
        result[tag]["missing"].append("Image-space detection consistency and mounting stability are not established.")
    return result


def _candidate_support(run: Path, binding: dict[str, Any] | None, candidate: dict[str, Any],
                       active_ids: list[int]) -> tuple[Any, str | None]:
    if candidate["tag_id"] in active_ids:
        return None, "This candidate reuses an active ID; a moved tag needs an explicitly revised layout."
    if not all(candidate[key] for key in ("mounting_confirmed", "access_confirmed", "interior_confirmed")):
        return None, "Interior surface, mounting stability and physical access must all be explicitly reviewed."
    regions = {region["id"]: region for region in binding["regions"]}
    region = regions.get(candidate["region_id"])
    if region is None or candidate["support_index"] >= len(region["support"]):
        return None, "The candidate has no matching reviewed source surface support."
    support = region["support"][candidate["support_index"]]
    root = run.resolve()
    asset = (root / support["asset"]).resolve()
    if Path(support["asset"]).is_absolute() or not asset.is_relative_to(root) or not asset.is_file():
        return None, "The reviewed surface support asset is unavailable for this source."
    if support.get("observed_xyz") is None:
        return None, "The reviewed patch has no observed source position; only qualitative advice is possible."
    if not (run / "frames.json").is_file():
        return None, "The candidate's original source frame association is unavailable."
    frame_ids = {str(frame["id"]) for frame in read_json(run / "frames.json")["frames"]}
    if support["frame_id"] not in frame_ids:
        return None, "The reviewed support refers to an absent source frame."
    if not candidate["connects_to"] or any(tag not in active_ids for tag in candidate["connects_to"]):
        return None, "Candidate connections must name retained active tags."
    return np.asarray(support["observed_xyz"], dtype=float), None


def review_placement(run: Path, manifest: dict[str, Any], measurements: MeasurementDocument,
                     planning: dict[str, Any], context: dict[str, Any] | None,
                     output: Path) -> dict[str, Any]:
    started = perf_counter()
    print("[Review captured tag coverage]", flush=True)
    captured = {tag["id"]: np.asarray(tag["pose"], dtype=float)[:3, 3] for tag in manifest.get("tags", [])}
    ids = sorted(captured)
    positions = np.asarray([captured[tag] for tag in ids]).reshape((-1, 3))
    if not np.isfinite(positions).all():
        raise ValueError("Captured tag centres must be finite.")
    state = planning_state(None, measurements, ids=ids, positions=positions, basis="captured_estimate")
    support = _observation_support(run, manifest)
    centred = positions - positions.mean(axis=0) if ids else positions
    _, singular, axes = np.linalg.svd(centred, full_matrices=True)
    extents = np.ptp(centred @ axes.T, axis=0).tolist() if ids else [0.0, 0.0, 0.0]
    pairs = enumerate_pairs(state, measurements, planning["candidate_sigmas"])
    print("[Check likely tape connections in captured mesh]", flush=True)
    scene = assess_segments(run, pairs, captured, dict.fromkeys(ids, 0.0), manifest=manifest, mesh_only=True)
    score_pairs(state, pairs, planning)
    visibility_elapsed = perf_counter() - started
    # An optimistic geometric bound, not a checklist: add all potentially accessible connections at once.
    possible = [pair for pair in pairs if pair["eligible"]]
    all_rows = [*state["rows"], *[pair_jacobian(positions, ids.index(pair["tag_a"]), ids.index(pair["tag_b"])) /
                                 pair["sigma_m"] for pair in possible]]
    all_edges = [*state["edges"], *[(pair["tag_a"], pair["tag_b"]) for pair in possible]]
    attainable = refresh_state(state | {"rows": all_rows, "edges": all_edges}, {})
    optimistic = summary(attainable, planning["target_mm"], include_groups=True)
    measured_network = summary(state, planning["target_mm"], include_groups=True)
    ellipsoids = {row["tag_id"]: row for row in optimistic["ellipsoids"]}
    rows, weak_regions = [], []
    for i, tag in enumerate(ids):
        observed = support[tag]
        measured = [b if a == tag else a for a, b in state["edges"] if tag in (a, b)]
        connections = [pair["tag_b"] if pair["tag_a"] == tag else pair["tag_a"] for pair in possible
                       if tag in (pair["tag_a"], pair["tag_b"])]
        weak = []
        null_block = attainable["information"]["null_basis"][3*i:3*i+3]
        if null_block.size:
            vectors, energies, _ = np.linalg.svd(null_block, full_matrices=False)
            weak = [{"direction": vectors[:, j].tolist(), "null_energy": float(value * value)}
                    for j, value in enumerate(energies) if value > NETWORK_SETTINGS["rank_rtol"]]
        local = ellipsoids.get(tag)
        if not weak and local and local["longest_semi_axis_95_m"] * 1000 > planning["target_mm"]:
            weak = [{"direction": local["worst_direction"], "null_energy": 0.0}]
        single_view = observed["viewpoint_count"] == 1 or observed["observation_count"] == 1
        reason = ("Only one captured viewpoint supports this tag. Check mounting and capture it from more directions."
                  if single_view else "Keep this tag's captured coverage; nearby tags can still provide useful redundancy.")
        if weak:
            reason += " Even the optimistic available connections leave a weak direction here."
            weak_regions.append({"tag_id": tag, "source_position_m": captured[tag].tolist(),
                                 "reason": "Seek a stable interior mounting region with depth separation and tape paths across the highlighted weak directions.",
                                 "directions": [mode["direction"] for mode in weak]})
        rows.append({"tag_id": tag, "source_position_m": captured[tag].tolist(), "recommendation": "keep",
                     "reason": reason, "useful_connections": sorted(set(connections)),
                     "measured_connections": sorted(set(measured)), "observation_support": observed, "weak_modes": weak})
    print("[Summarise placement findings]", flush=True)
    cache, candidates = {}, []
    binding = context.get("binding") if context else None
    baseline_selected, baseline_summary = None, None
    for candidate in binding.get("placement_candidates", []) if binding else []:
        point, reason = _candidate_support(run, binding, candidate, ids)
        # Only supplied supported alternatives need a numerical effort comparison. The ordinary report
        # never builds a complete checklist or performs a symbolic certificate.
        if point is not None and baseline_selected is None:
            baseline_selected, baseline_state, _ = select_batch(state, pairs, planning["target_mm"],
                                                               planning["improvement_mm"], cache=cache)
            baseline_summary = summary(baseline_state, planning["target_mm"])
        budget = len(baseline_selected) if baseline_selected is not None else 0
        row = {"id": candidate["id"], "tag_id": candidate["tag_id"], "region_id": candidate["region_id"],
               "status": "unsupported" if reason else "assessed", "reason": reason,
               "source_position_m": point.tolist() if point is not None else None,
               "sigma_m": candidate["sigma_m"], "assumed_connections": sorted(set(candidate["connects_to"])),
               "common_budget": budget, "before_at_budget": baseline_summary, "after_at_budget": None,
               "target_measurement_count_before": baseline_summary["measurement_count"]
                   if baseline_summary and baseline_summary["local_target_met"] else None,
               "target_measurement_count_after": None, "selected_pairs": [], "target_pairs": [], "pairs": [],
               "coverage_preserved": True, "retained_tag_ids": ids,
               "assumptions": ["Captured geometry, candidate connections and precision are planning assumptions.",
                               "Equal retained coverage is compared; global uniqueness is not certified."]}
        if point is not None:
            new_ids = sorted([*ids, candidate["tag_id"]])
            new_positions = np.asarray([point if tag == candidate["tag_id"] else captured[tag] for tag in new_ids])
            candidate_state = planning_state(None, measurements, ids=new_ids, positions=new_positions,
                                              basis="captured_estimate")
            candidate_state["retained_ids"] = ids
            candidate_state = refresh_state(candidate_state, cache)
            extra_pairs = []
            for other in sorted(set(candidate["connects_to"])):
                a, b = sorted((candidate["tag_id"], other))
                length = float(np.linalg.norm(new_positions[new_ids.index(a)] - new_positions[new_ids.index(b)]))
                extra_pairs.append({"tag_a": a, "tag_b": b, "state": "proposed", "estimate_m": length,
                                    "sigma_m": candidate["sigma_m"], "manual_exclusion": None,
                                    "eligible": length >= NETWORK_SETTINGS["coincident_m"]})
            scene = assess_segments(run, extra_pairs, captured | {candidate["tag_id"]: point},
                                    dict.fromkeys(new_ids, 0.0), manifest=manifest, mesh_only=True, scene=scene)
            for pair in extra_pairs:
                pair["eligible"] &= pair["clearance"] != "obstructed"
                pair["check_access"] = pair["clearance"] == "unknown"
            selected, at_budget, _ = select_batch(candidate_state, [*pairs, *extra_pairs], planning["target_mm"],
                                                 planning["improvement_mm"], budget=budget, reverse_delete=False,
                                                 cache=cache)
            target_selected, target_state, target_stop = select_batch(candidate_state, [*pairs, *extra_pairs],
                                                                      planning["target_mm"], planning["improvement_mm"],
                                                                      cache=cache)
            target = summary(target_state, planning["target_mm"])
            row.update(after_at_budget=summary(at_budget, planning["target_mm"]),
                       target_measurement_count_after=target["measurement_count"] if target["local_target_met"] else None,
                       selected_pairs=[{"tag_a": p["tag_a"], "tag_b": p["tag_b"]} for p in selected],
                       target_pairs=[{"tag_a": p["tag_a"], "tag_b": p["tag_b"]} for p in target_selected],
                       pairs=extra_pairs, reason=target_stop)
        candidates.append(row)
    result = {"tag_ids": ids, "tags": rows, "extent_m": extents, "extent_directions": axes.T.tolist(),
              "direction_frame": "source", "geometry_singular_values_m": singular.tolist(),
              "weak_regions": weak_regions, "candidates": candidates, "retained_tag_ids": ids,
              "common_budget": len(baseline_selected) if baseline_selected is not None else None,
              "measured_network": measured_network, "optimistic_connections": optimistic,
              "paths": pairs, "repair_pairs": repair_pairs(pairs), "settings": PLACEMENT_SETTINGS,
              "runtime": {"coverage_and_paths_s": visibility_elapsed, "total_s": perf_counter() - started},
              "notes": ["Captured positions predict placement quality; no physical fit or measurement checklist was required.",
                        "The all-available-connections result is an optimistic local bound, not measured accuracy or a uniqueness certificate.",
                        "Unknown tape access is conditional. A mesh miss does not establish free space.",
                        "Extents use principal directions of the tags, not recognised van axes or surfaces.",
                        "Observation counts and camera spread are not calibrated positional precision.",
                        "No tag is removed merely for proximity. All retained tags remain in comparisons."]}
    if not any(candidate["status"] == "assessed" for candidate in candidates):
        result["notes"].append("No supported reviewed mounting alternatives are available; additions remain qualitative.")
    fingerprint(result)
    write_json(output / "placement.json", result)
    return result
