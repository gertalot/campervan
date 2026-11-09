"""All useful candidate ranges, scored against the same correlated uncertainty baseline."""

from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

from campervan.scan_analysis import pair_jacobian
from campervan.scan_measurements import MeasurementDocument
from campervan.scan_visibility import assess_segments
from campervan.scans import read_json, write_json


def suggest(run: Path, analysis: Path, threshold_mm: float) -> dict[str, Any]:
    result = read_json(analysis / "result.json")
    document = MeasurementDocument.model_validate(read_json(analysis / "request.json")["measurements"])
    ids = result["tag_ids"]
    positions = np.asarray([np.asarray(tag["pose"])[:3, 3] for tag in sorted(result["tags"], key=lambda t: t["id"])])
    covariance = np.load(analysis / "covariance.npy", allow_pickle=False)
    pairs = list(combinations(range(len(ids)), 2))
    jacobians = np.asarray([pair_jacobian(positions, a, b) for a, b in pairs])
    variances = np.maximum(0, np.einsum("ij,jk,ik->i", jacobians, covariance, jacobians))
    baseline = 1.96 * np.sqrt(np.maximum(0, variances))
    measured = {(r.tag_a, r.tag_b) for r in document.distances}
    excluded = {(r.tag_a, r.tag_b): r.reason for r in document.excluded_pairs}
    sigma = document.default_sigma_m
    if sigma is None:
        raise ValueError("A measuring precision assumption is required.")
    suggestions = []
    profiles = []
    print("[Rank all candidate measurements]", flush=True)
    for i, (a, b) in enumerate(pairs):
        if (ids[a], ids[b]) in measured:
            continue
        projected = covariance @ jacobians[i]
        after = 1.96 * np.sqrt(np.maximum(0, variances - (jacobians @ projected) ** 2 / (sigma * sigma + variances[i])))
        gains = baseline - after
        target = int(np.argmax(gains))
        if gains[target] * 1000 < threshold_mm:
            continue
        ta, tb = pairs[target]
        row = {
            "tag_a": ids[a],
            "tag_b": ids[b],
            "predicted_distance_m": float(np.linalg.norm(positions[a] - positions[b])),
            "target_a": ids[ta],
            "target_b": ids[tb],
            "before_95_m": float(baseline[target]),
            "after_95_m": float(after[target]),
            "gain_m": float(gains[target]),
            "sigma_m": sigma,
        }
        suggestions.append(row)
        profiles.append(gains)
    assess_segments(
        run,
        suggestions,
        dict(zip(ids, positions, strict=True)),
        {m["id"]: m["distance_m"] for m in result["movements"]},
    )
    previous: list[tuple[dict[str, Any], Any]] = []
    for row, profile in sorted(zip(suggestions, profiles, strict=True), key=lambda item: -item[0]["gain_m"]):
        row["overlaps_with"] = []
        for earlier, other in previous:
            similarity = float(profile @ other) / (float(np.linalg.norm(profile) * np.linalg.norm(other)))
            if similarity >= 0.9:
                row["overlaps_with"].append([earlier["tag_a"], earlier["tag_b"]])
        if (row["tag_a"], row["tag_b"]) in excluded:
            row.update(clearance="obstructed", clearance_reason=excluded[(row["tag_a"], row["tag_b"])], manual=True)
        previous.append((row, profile))
    report = {
        "threshold_mm": threshold_mm,
        "sigma_m": sigma,
        "mesh_sha256": result["mesh_sha256"],
        "rows": sorted(suggestions, key=lambda r: -r["gain_m"]),
        "remeasure": [
            r
            for r in result["residuals"]
            if abs(r["standardised_residual"]) > 2 or r["sigma_m"] and r["sigma_m"] > sigma
        ],
        "note": "Gains share a baseline and overlap; do not add them. Unknown clearance does not mean a clear path.",
    }
    write_json(analysis / "suggestions.tmp", report)
    (analysis / "suggestions.tmp").replace(analysis / "suggestions.json")
    return report
