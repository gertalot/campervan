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
            return self._save(document)

    def publish(self, artifact: ArtifactEnvelope,
                freshness: Callable[[WorkflowDocument], ArtifactStatus]) -> ArtifactStatus:
        """The API job owner merges a successful immutable result into current edits."""
        with self.lock:
            document = self.read()
            item = document.workflows[artifact.workflow_id]
            if item.source_run_id != artifact.source_run_id or item.layout_id != artifact.layout_id:
                raise ValueError("Artifact no longer belongs to this workflow source/layout.")
            status = freshness(document)
            item.artifact_refs[artifact.kind] = artifact.id
            self._save(document)
            return status

    def _save(self, document: WorkflowDocument) -> WorkflowDocument:
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
    from campervan.scans import SCAN_RUNS, file_hash, read_json, scan_manifest

    run = scan_manifest(item.source_run_id)
    measurements = layouts.measurements(item.layout_id).read()
    tags = sorted({tag["id"] for tag in run.get("tags", [])})
    physical = {
        "tags": tags,
        "layout_id": item.layout_id,
        "distances": sorted((r.tag_a, r.tag_b, r.distance_m, r.sigma_m or measurements.default_sigma_m)
                            for r in measurements.distances if r.tag_a in tags and r.tag_b in tags),
    }
    source = None
    context = None
    if kind != "measurement_network":
        root = (SCAN_RUNS / item.source_run_id).resolve()

        def evidence(name: str, *, required: bool = False) -> str | None:
            path = (root / name).resolve()
            if Path(name).is_absolute() or not path.is_relative_to(root):
                raise ValueError("Source evidence must be relative to its run.")
            if not path.is_file():
                if required:
                    raise ValueError(f"Required source evidence unavailable: {name}")
                return None
            return file_hash(path)

        files = {name: evidence(name, required=(name == "graph.json" and kind == "scan_correction"))
                 for name in ("graph.json", "frames.json", "poses.json", "mesh.ply")}
        frame_assets: dict[str, str | None] = {}
        if files["frames.json"] is not None:
            frames = read_json(root / "frames.json")
            fields = ("rgb", "depth", "confidence") if kind in ("context_review", "scan_correction") else (
                "depth", "confidence"
            )
            for frame in frames["frames"]:
                for field in fields:
                    name = frame.get(field)
                    if name:
                        frame_assets[name] = evidence(name)
        if context_used and item.source_binding:
            for mask in item.source_binding.masks:
                frame_assets[mask.asset] = evidence(mask.asset)
            for region in item.source_binding.regions:
                for support in region.support:
                    frame_assets[support.asset] = evidence(support.asset)
        source = {"manifest": run, "files": files, "frame_assets": dict(sorted(frame_assets.items()))}
        if context_used:
            profile = (document.profiles[item.profile_ref.profile_id][item.profile_ref.revision - 1].model_dump()
                       if item.profile_ref else None)
            context = {"profile": profile, "binding": item.source_binding.model_dump() if item.source_binding else None}
    planning = None
    if kind in ("measurement_plan", "placement_review"):
        planning = {"exclusions": sorted((p.tag_a, p.tag_b, p.reason) for p in measurements.excluded_pairs),
                    "default_sigma_m": measurements.default_sigma_m,
                    "candidate_sigmas": item.candidate_sigmas, "target_mm": item.target_mm,
                    "improvement_mm": item.improvement_mm}
    inputs = {"physical": physical, "source": source, "context": context, "planning": planning, "settings": settings}
    return {"run": run, "measurement_revision": measurements.revision, "measurements": measurements.model_dump(),
            "inputs": inputs, "fingerprints": fingerprint_inputs(kind, algorithm_version, **inputs)}
