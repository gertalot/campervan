"""Placement advice with retained coverage and the same pair planner and effort budget."""

from pathlib import Path
from typing import Any

import numpy as np

from campervan.scan_measurements import MeasurementDocument
from campervan.scan_network import NETWORK_SETTINGS
from campervan.scan_suggestions import (
    PLANNER_SETTINGS, plan_measurements, planning_state, refresh_state, select_batch, source_associations, summary,
)
from campervan.scan_visibility import assess_segments
from campervan.scan_workflows import fingerprint
from campervan.scans import read_json, write_json

PLACEMENT_ALGORITHM_VERSION = "supported-placement-1"
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
                     network: dict[str, Any], planning: dict[str, Any], context: dict[str, Any] | None,
                     output: Path) -> dict[str, Any]:
    from campervan.scan_analysis import register_measured_shape

    print("[Review tag placement and retained coverage]", flush=True)
    cache: dict = {}
    plan = plan_measurements(run, manifest, measurements, network, planning, output, cache=cache)
    state = planning_state(network, measurements)
    ids, positions = state["ids"], state["positions"]
    captured = {tag["id"]: np.asarray(tag["pose"], dtype=float)[:3, 3] for tag in manifest.get("tags", [])}
    registration = register_measured_shape(network, captured)
    source_rotation = (registration["rotation"] if registration["status"] == "registered" else
                       np.asarray(network["solver"]["display_rotation"]))
    support = _observation_support(run, manifest)
    centred = positions - positions.mean(axis=0) if ids else positions
    _, singular, axes = np.linalg.svd(centred, full_matrices=True)
    extents = np.ptp(centred @ axes.T, axis=0).tolist() if ids else [0.0, 0.0, 0.0]
    proposed = {_pair_key(pair) for pair in plan["recommended_pairs"]}
    rows = []
    for i, tag in enumerate(ids):
        observed = support[tag]
        connections = [pair["tag_b"] if pair["tag_a"] == tag else pair["tag_a"] for pair in plan["rows"]
                       if tag in (pair["tag_a"], pair["tag_b"]) and
                       (pair["state"] != "proposed" or _pair_key(pair) in proposed)]
        single_view = observed["observation_count"] is not None and observed["observation_count"] < 2
        null_block = state["information"]["null_basis"][3*i:3*i+3]
        weak = []
        if null_block.size:
            vectors, energies, _ = np.linalg.svd(null_block, full_matrices=False)
            weak = [{"direction": (source_rotation @ vectors[:, j]).tolist(), "null_energy": float(value * value)}
                    for j, value in enumerate(energies) if value > NETWORK_SETTINGS["rank_rtol"]]
        rows.append({"tag_id": tag, "source_position_m": captured[tag].tolist(),
                     "recommendation": "consider_moving" if single_view else "keep",
                     "reason": "Only one captured view supports this tag. Check stable mounting and recapture from other directions before considering a move."
                     if single_view else "Retain this tag's spatial coverage and available range ties; proximity alone is not a reason to remove it.",
                     "useful_connections": connections, "observation_support": observed, "weak_modes": weak})
    # The common budget is the baseline planner's additional effort, including its best effort when target is impossible.
    budget = len(plan["recommended_pairs"])
    binding = context.get("binding") if context else None
    candidates = []
    for candidate in binding.get("placement_candidates", []) if binding else []:
        point, reason = _candidate_support(run, binding, candidate, ids)
        row = {"id": candidate["id"], "tag_id": candidate["tag_id"], "region_id": candidate["region_id"],
               "status": "unsupported" if reason else "assessed", "reason": reason,
               "source_position_m": point.tolist() if point is not None else None,
               "sigma_m": candidate["sigma_m"], "assumed_connections": sorted(set(candidate["connects_to"])),
               "common_budget": budget, "before_at_budget": plan["predicted"],
               "after_at_budget": None, "target_measurement_count_before":
                   plan["predicted"]["measurement_count"] if plan["predicted"]["target_met"] else None,
               "target_measurement_count_after": None, "selected_pairs": [], "target_pairs": [],
               "pairs": [], "coverage_preserved": True, "retained_tag_ids": ids,
               "assumptions": ["The reviewed patch position and candidate precision are assumptions, not achieved accuracy.",
                               "Compare only the identical retained tags after equal-weight rigid alignment."]}
        if point is not None:
            if registration["status"] == "registered":
                canonical = (point - registration["translation"]) @ registration["rotation"]
            else:
                anchor = network["solver"]["gauge_anchors"]
                origin = captured[anchor[0]] if anchor else np.zeros(3)
                canonical = (point - origin) @ np.asarray(network["solver"]["display_rotation"])
                row["assumptions"].append("The incomplete physical shape uses captured orientation for this patch estimate.")
            new_ids = sorted([*ids, candidate["tag_id"]])
            new_positions = np.asarray([canonical if tag == candidate["tag_id"] else positions[ids.index(tag)]
                                        for tag in new_ids])
            physical_rows = []
            for old in state["rows"]:
                padded = np.zeros((len(new_ids), 3))
                for i, tag in enumerate(ids):
                    padded[new_ids.index(tag)] = old[3*i:3*i+3]
                physical_rows.append(padded.reshape(-1))
            candidate_state = refresh_state(state | {"ids": new_ids, "positions": new_positions,
                                                "rows": physical_rows, "retained_ids": ids}, cache)
            extra_pairs = []
            for other in sorted(set(candidate["connects_to"])):
                a, b = sorted((candidate["tag_id"], other))
                length = float(np.linalg.norm(new_positions[new_ids.index(a)] - new_positions[new_ids.index(b)]))
                extra_pairs.append({"tag_a": a, "tag_b": b, "state": "proposed", "estimate_m": length,
                                    "sigma_m": candidate["sigma_m"], "manual_exclusion": None,
                                    "eligible": length >= NETWORK_SETTINGS["coincident_m"]})
            source_positions, moved = source_associations(registration, captured)
            source_positions = source_positions | {candidate["tag_id"]: point}
            moved[candidate["tag_id"]] = 0.0
            assess_segments(run, extra_pairs, source_positions, moved, manifest=manifest)
            for pair in extra_pairs:
                pair["eligible"] = pair["eligible"] and pair["clearance"] != "obstructed"
                pair["check_access"] = pair["clearance"] == "unknown"
            all_pairs = [*plan["rows"], *extra_pairs]
            selected, at_budget, _ = select_batch(candidate_state, all_pairs, planning["target_mm"],
                                                 planning["improvement_mm"], budget=budget,
                                                 reverse_delete=False, cache=cache)
            target_selected, target_state, target_stop = select_batch(candidate_state, all_pairs,
                                                                      planning["target_mm"],
                                                                      planning["improvement_mm"], cache=cache)
            target = summary(target_state, planning["target_mm"])
            row.update(after_at_budget=summary(at_budget, planning["target_mm"]),
                       target_measurement_count_after=target["measurement_count"] if target["target_met"] else None,
                       selected_pairs=[{"tag_a": p["tag_a"], "tag_b": p["tag_b"]} for p in selected],
                       target_pairs=[{"tag_a": p["tag_a"], "tag_b": p["tag_b"]} for p in target_selected],
                       pairs=extra_pairs, reason=target_stop)
        candidates.append(row)
    weak_regions = [{"tag_id": row["tag_id"], "source_position_m": row["source_position_m"],
                     "reason": "Seek a stable, accessible interior surface with depth separation from the current tags and tape connections across these weak modes.",
                     "directions": [mode["direction"] for mode in row["weak_modes"]]}
                    for row in rows if row["weak_modes"]]
    if not weak_regions and plan["predicted"]["local_worst_tag"]:
        worst = plan["predicted"]["local_worst_tag"]
        weak_regions.append({"tag_id": worst["tag_id"], "source_position_m": captured[worst["tag_id"]].tolist(),
                             "reason": "Review supported mounting surfaces and cross-network connections around the weakest retained tag.",
                             "directions": [(source_rotation @ np.asarray(worst["worst_direction"])).tolist()]})
    result = {"tag_ids": ids, "tags": rows, "extent_m": extents,
              "extent_directions": (source_rotation @ axes.T).tolist(), "direction_frame": "source",
              "geometry_singular_values_m": singular.tolist(), "weak_regions": weak_regions,
              "candidates": candidates, "baseline_plan": plan, "common_budget": budget,
              "retained_tag_ids": ids, "settings": PLACEMENT_SETTINGS,
              "notes": ["All active tags remain in the comparison; dropping a weak tag is not an accuracy gain.",
                        "Observation counts and camera spread describe support, not calibrated positional precision.",
                        "Keep coverage, loop ties and redundancy. Verify mounting reliability before moving or removing tags.",
                        "No automatic scene labels, new surface positions or physical observations were created."]}
    if not candidates or not any(candidate["status"] == "assessed" for candidate in candidates):
        result["notes"].append("No usable reviewed interior mounting/access patches are available; additions remain qualitative.")
    fingerprint(result)
    write_json(output / "placement.json", result)
    return result


def _pair_key(pair: dict[str, Any]) -> tuple[int, int]:
    return pair["tag_a"], pair["tag_b"]
