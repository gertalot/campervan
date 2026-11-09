"""Workflow persistence and eligibility routes for the scan workspace."""

import sys
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import Field

from campervan.scan_layouts import ReviseTagLayout, ScanLayouts
from campervan.scan_library import ScanLibraryStore
from campervan.scan_network import ALGORITHM_VERSION, NETWORK_SETTINGS
from campervan.scan_processing import ScanProcessing, identifier
from campervan.scan_workflow_models import (
    ArtifactEnvelope, ArtifactStatus, ChecklistBatch, Model, ProfileRef, ProfileRevision, SourceBinding, Stage, Workflow,
)
from campervan.scan_workflows import ScanWorkflowStore, WorkflowConflict, artifact_status, capture_inputs
from campervan.scans import scan_asset, scan_manifest, write_json


class CreateWorkflow(Model):
    source_run_id: str
    layout_id: str


class EditWorkflow(Model):
    revision: int = Field(ge=0, strict=True)
    stage: Stage | None = None
    target_mm: float | None = Field(default=None, gt=0)
    improvement_mm: float | None = Field(default=None, gt=0)
    candidate_sigmas: dict[str, float] | None = None
    checklist_batches: list[ChecklistBatch] | None = None
    review_decisions: dict[str, Any] | None = None
    profile: ProfileRevision | None = None
    profile_ref: ProfileRef | None = None
    source_binding: SourceBinding | None = None


class ActionRequest(Model):
    revision: int = Field(ge=0, strict=True)
    measurement_revision: int = Field(ge=0, strict=True)


Action = Literal["review-placement", "plan-measurements", "check-measurements", "suggest-more",
                 "preview-correction", "update-mesh"]


def register_scan_workflows(app: FastAPI, store: ScanWorkflowStore, layouts: ScanLayouts,
                            library: ScanLibraryStore, processing: ScanProcessing) -> None:
    artifact_directory = store.path.parent / "scan-workflow-artifacts"

    def workflow(document, value: str) -> Workflow:
        identifier(value)
        if value not in document.workflows:
            raise HTTPException(404, "Workflow not found.")
        return document.workflows[value]

    def read_artifact(item: Workflow, document, artifact_id: str):
        identifier(artifact_id)
        try:
            artifact = ArtifactEnvelope.model_validate_json((artifact_directory / artifact_id / "artifact.json").read_text())
        except FileNotFoundError as error:
            raise HTTPException(404, "Artifact not found.") from error
        if artifact.id != artifact_id or artifact.workflow_id != item.id or artifact.source_run_id != item.source_run_id or artifact.layout_id != item.layout_id:
            raise HTTPException(404, "Artifact not found for this workflow.")
        try:
            # Compare against the current producer, never replay a saved version/settings as current policy.
            algorithm = ALGORITHM_VERSION if artifact.kind == "measurement_network" else artifact.algorithm_version
            settings = NETWORK_SETTINGS if artifact.kind == "measurement_network" else artifact.assumptions.get("settings")
            current = capture_inputs(item, document, layouts, artifact.kind, algorithm,
                                     settings=settings,
                                     context_used=artifact.assumptions.get("context_used", True))["fingerprints"]
        except (ValueError, OSError, KeyError) as error:
            return artifact, ArtifactStatus(status="unavailable", reasons=[f"Source evidence unavailable: {error}"])
        return artifact, artifact_status(artifact, current)

    def actions(source_available: bool) -> dict[str, Any]:
        result = {name: {"available": False, "reasons": ["Producer unavailable."]}
                  for name in ("review-placement", "plan-measurements", "check-measurements", "suggest-more",
                               "preview-correction", "update-mesh")}
        reasons = ([] if source_available else ["Source capture is unavailable."])
        if any(not task.done() for task in processing.tasks.values()):
            reasons.append("Another scan task is running. Wait for it to finish.")
        result["check-measurements"] = {"available": not reasons, "reasons": reasons}
        return result

    def view(document, item: Workflow) -> dict[str, Any]:
        preference = library.read().entries.get(f"run:{item.source_run_id}")
        displayed = item.model_copy(update={"group_id": preference.group_id if preference else None})
        measurement = layouts.measurements(item.layout_id).read()
        try:
            scan_manifest(item.source_run_id)
            available = True
        except (ValueError, OSError, KeyError):
            available = False
        artifacts = {}
        for kind, value in item.artifact_refs.items():
            try:
                _, status = read_artifact(item, document, value)
            except (HTTPException, ValueError, OSError):
                status = ArtifactStatus(status="unavailable", reasons=["Artifact is missing or invalid."])
            artifacts[kind] = status
        jobs = [job for path in processing.jobs.glob("*.json")
                if (job := processing.job(path.stem, include_log=False)).get("workflow_id") == item.id]
        stage_kinds = {"review_capture": "placement_review", "measure": "measurement_plan",
                       "check_accuracy": "measurement_network", "update_reconstruction": "scan_correction"}
        stages = {}
        for stage, kind in stage_kinds.items():
            status = artifacts.get(kind)
            stages[stage] = ("In progress" if any(j.get("artifact_kind") == kind and j["state"] == "processing" for j in jobs)
                             else "Not started" if status is None else "Complete" if status.status == "current"
                             else "Needs updating")
        return {"revision": document.revision, "workflow": displayed, "measurement": measurement,
                "source_available": available, "profile": (document.profiles[item.profile_ref.profile_id][item.profile_ref.revision - 1] if item.profile_ref else None),
                "artifacts": artifacts, "stages": stages, "jobs": jobs,
                "actions": actions(available)}

    @app.post("/api/v1/scans/workflows")
    def create(request: CreateWorkflow):
        try:
            run = scan_manifest(request.source_run_id)
            source_id = run.get("reference_run_id") or request.source_run_id
            run = scan_manifest(source_id)
            if run.get("tag_layout_id") != request.layout_id:
                raise ValueError("Source capture belongs to another layout.")
            layouts.measurements(request.layout_id).read()
            document = store.read()
            existing = next((w for w in document.workflows.values() if w.source_run_id == source_id and w.layout_id == request.layout_id), None)
            if existing:
                return view(document, existing)
            item = Workflow(id=str(uuid4()), source_run_id=source_id, layout_id=request.layout_id)
            document = store.edit(document.revision, lambda d: d.workflows.update({item.id: item}))
            return view(document, document.workflows[item.id])
        except WorkflowConflict as error:
            raise HTTPException(409, str(error)) from error
        except (ValueError, OSError, KeyError) as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/v1/scans/workflows/{workflow_id}")
    def get(workflow_id: str):
        document = store.read()
        return view(document, workflow(document, workflow_id))

    @app.patch("/api/v1/scans/workflows/{workflow_id}")
    def edit(workflow_id: str, request: EditWorkflow):
        def change(document):
            item = workflow(document, workflow_id)
            updates = request.model_dump(exclude_unset=True, exclude={"revision", "profile", "source_binding"})
            if request.profile and "profile_ref" in request.model_fields_set:
                raise ValueError("Choose a profile revision or create one, not both.")
            if "profile_ref" in request.model_fields_set:
                updates["source_binding"] = None
            if request.profile:
                profile = request.profile
                versions = document.profiles.setdefault(profile.profile_id, [])
                if (profile.layout_id != item.layout_id or profile.revision != len(versions) + 1
                    or any(previous.layout_id != profile.layout_id for previous in versions)):
                    raise ValueError("Profile must be the next revision for this layout.")
                versions.append(profile)
                updates["profile_ref"] = {"profile_id": profile.profile_id, "revision": profile.revision}
                updates["source_binding"] = None
            if request.source_binding:
                for mask in request.source_binding.masks:
                    scan_asset(item.source_run_id, mask.asset)
                for region in request.source_binding.regions:
                    for support in region.support:
                        scan_asset(item.source_run_id, support.asset)
                updates["source_binding"] = request.source_binding.model_dump()
            document.workflows[item.id] = Workflow.model_validate(item.model_dump() | updates)
        try:
            document = store.edit(request.revision, change)
            return view(document, workflow(document, workflow_id))
        except WorkflowConflict as error:
            raise HTTPException(409, str(error)) from error
        except (ValueError, OSError, KeyError) as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/v1/scans/workflows/{workflow_id}/actions/{action}", status_code=202)
    async def action(workflow_id: str, action: Action, request: ActionRequest):
        document = store.read()
        item = workflow(document, workflow_id)
        if document.revision != request.revision:
            raise HTTPException(409, "Workflow data changed. Refresh and retry.")
        try:
            scan_manifest(item.source_run_id)
            eligibility = actions(True)[action]
            if not eligibility["available"]:
                raise HTTPException(409 if action == "check-measurements" else 503, " ".join(eligibility["reasons"]))
            snapshot = capture_inputs(item, document, layouts, "measurement_network", ALGORITHM_VERSION,
                                      settings=NETWORK_SETTINGS, context_used=False)
            if snapshot["measurement_revision"] != request.measurement_revision:
                raise HTTPException(409, "Measurements changed. Refresh and retry.")
            value = str(uuid4())
            directory = artifact_directory / value
            directory.mkdir(parents=True)
            envelope = ArtifactEnvelope(
                id=value, kind="measurement_network", algorithm_version=ALGORITHM_VERSION,
                workflow_id=item.id, source_run_id=item.source_run_id, layout_id=item.layout_id,
                measurement_revision=snapshot["measurement_revision"], profile_ref=None,
                fingerprints=snapshot["fingerprints"], job_id=value, payload={},
                assumptions={"settings": NETWORK_SETTINGS, "context_used": False,
                             "physical_inputs": snapshot["inputs"]["physical"],
                             "capture_role": "Initial coordinates and display mirror convention only."},
            )
            write_json(directory / "request.json", {
                "run_id": item.source_run_id, "run": snapshot["run"],
                "measurements": snapshot["measurements"], "settings": NETWORK_SETTINGS,
                "artifact": envelope.model_dump(),
            })

            def publish(job):
                artifact, _ = read_artifact(item, store.read(), value)

                def freshness(current_document):
                    _, status = read_artifact(current_document.workflows[item.id], current_document, value)
                    return status

                job["artifact_status"] = store.publish(artifact, freshness).model_dump()
                job["artifact_id"] = artifact.id

            preference = library.read().entries.get(f"run:{item.source_run_id}")
            processing.start_action(
                value, "analysis",
                [sys.executable, "-u", "-m", "campervan.scan_analysis_worker", "check-measurements",
                 str(directory.resolve())],
                {"run_id": item.source_run_id, "source_run_id": item.source_run_id,
                 "workflow_id": item.id, "layout_id": item.layout_id, "artifact_kind": "measurement_network",
                 "group_id": preference.group_id if preference else None, "name": "Check measurements"},
                publish=publish,
            )
            return {"id": value, "artifact_id": value}
        except (OSError, ValueError) as error:
            raise HTTPException(422, f"Source or measurements unavailable: {error}") from error

    @app.get("/api/v1/scans/workflows/{workflow_id}/artifacts/{artifact_id}")
    def artifact(workflow_id: str, artifact_id: str):
        document = store.read()
        envelope, status = read_artifact(workflow(document, workflow_id), document, artifact_id)
        return {"artifact": envelope, "status": status}

    @app.post("/api/v1/scans/layouts/{layout_id}/revise", status_code=201)
    def revise(layout_id: str, request: ReviseTagLayout):
        try:
            document = store.read()
            references = [ref for versions in document.profiles.values() for profile in versions
                          if profile.layout_id == layout_id for ref in profile.tag_references]
            known = {value for ref in references for key, value in ref.items()
                     if key == "tag_id" and isinstance(value, int) and not isinstance(value, bool)}
            known.update(value for ref in references for value in ref.get("tag_ids", [])
                         if isinstance(value, int) and not isinstance(value, bool))
            return layouts.revise(layout_id, request, known)
        except (OSError, ValueError) as error:
            raise HTTPException(422, str(error)) from error
