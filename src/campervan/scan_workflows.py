"""Revisioned workflow persistence and canonical artifact fingerprints."""

import hashlib
import json
from pathlib import Path
from threading import Lock
from typing import Any, Callable

from campervan.scan_workflow_models import ArtifactEnvelope, ArtifactStatus, WorkflowDocument


class WorkflowConflict(ValueError):
    pass


class ScanWorkflowStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()

    def read(self) -> WorkflowDocument:
        try:
            return WorkflowDocument.model_validate_json(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return WorkflowDocument()

    def edit(self, revision: int, change: Callable[[WorkflowDocument], None]) -> WorkflowDocument:
        with self.lock:
            document = self.read()
            if document.revision != revision:
                raise WorkflowConflict("Workflow data changed. Refresh and retry.")
            change(document)
            document.revision += 1
            document = WorkflowDocument.model_validate(document.model_dump())
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(document.model_dump_json(indent=2) + "\n", encoding="utf-8")
            temporary.replace(self.path)
            return document


def fingerprint(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def artifact_status(artifact: ArtifactEnvelope, current: dict[str, str] | None) -> ArtifactStatus:
    if current is None:
        return ArtifactStatus(status="unavailable", reasons=["Source or required inputs are unavailable."])
    changed = sorted(key for key in artifact.fingerprints.keys() | current.keys()
                     if current.get(key) != artifact.fingerprints.get(key))
    if changed:
        return ArtifactStatus(status="stale", reasons=[f"Changed input: {key}" for key in changed])
    return ArtifactStatus(status="current")


def fingerprint_inputs(kind: str, algorithm_version: str, *, physical: Any, source: Any,
                       context: Any, planning: Any, settings: Any = None) -> dict[str, str]:
    """Canonical dependency keys shared by artifact writers and readers."""
    inputs: dict[str, Any] = {"algorithm": algorithm_version}
    if kind != "context_review":
        inputs["physical"] = physical
    if kind != "measurement_network":
        inputs["source"] = source
        inputs["context"] = context
    if kind in ("measurement_plan", "placement_review"):
        inputs["planning"] = planning
    if settings is not None:
        inputs["settings"] = settings
    return {key: fingerprint(value) for key, value in inputs.items()}


def capture_inputs(item: Any, document: WorkflowDocument, layouts: Any, kind: str,
                   algorithm_version: str, *, settings: Any = None, context_used: bool = True) -> dict[str, Any]:
    """Read acknowledged inputs once for a worker request and its later freshness comparison."""
    from campervan.scans import SCAN_RUNS, file_hash, scan_manifest

    run = scan_manifest(item.source_run_id)
    measurements = layouts.measurements(item.layout_id).read()
    tags = sorted(tag["id"] for tag in run.get("tags", []))
    physical = {
        "tags": tags,
        "layout_id": item.layout_id,
        "distances": sorted((r.tag_a, r.tag_b, r.distance_m, r.sigma_m or measurements.default_sigma_m or .003)
                            for r in measurements.distances if r.tag_a in tags and r.tag_b in tags),
    }
    source = None
    context = None
    if kind != "measurement_network":
        root = (SCAN_RUNS / item.source_run_id).resolve()
        assets = {}
        for name in sorted(run.get("assets", [])):
            path = (root / name).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError(f"Source asset unavailable: {name}")
            assets[name] = file_hash(path)
        source = {"manifest": run, "assets": assets}
        if context_used:
            profile = (document.profiles[item.profile_ref.profile_id][item.profile_ref.revision - 1].model_dump()
                       if item.profile_ref else None)
            context = {"profile": profile, "binding": item.source_binding.model_dump() if item.source_binding else None}
    planning = None
    if kind in ("measurement_plan", "placement_review"):
        planning = {"exclusions": sorted((p.tag_a, p.tag_b, p.reason) for p in measurements.excluded_pairs),
                    "candidate_sigmas": item.candidate_sigmas, "target_mm": item.target_mm,
                    "improvement_mm": item.improvement_mm}
    inputs = {"physical": physical, "source": source, "context": context, "planning": planning, "settings": settings}
    return {"measurement_revision": measurements.revision, "measurements": measurements.model_dump(),
            "inputs": inputs, "fingerprints": fingerprint_inputs(kind, algorithm_version, **inputs)}
