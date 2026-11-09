"""Revision-bound analysis previews, explicit acceptance, and non-destructive result history."""

import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from campervan.scan_layouts import ScanLayouts
from campervan.scan_measurements import MeasurementConflict
from campervan.scan_processing import ScanProcessing, identifier
from campervan.scan_solutions import ScanSolutions
from campervan.scans import SCAN_RUNS, file_hash, read_json, scan_manifest, write_json

ANALYSES = Path(".local/scan-analyses")


class AnalyseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    tag_layout_id: str
    revision: int = Field(ge=0, strict=True)


class AcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    solution_revision: int = Field(ge=0, strict=True)


class SuggestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    threshold_mm: float = Field(default=5, gt=0, allow_inf_nan=False)


def register_scan_analysis(
    app: FastAPI, processing: ScanProcessing, layouts: ScanLayouts, history: ScanSolutions
) -> None:
    def location(value: str) -> Path:
        return ANALYSES / identifier(value)

    def context(value: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
        directory = location(value)
        request = read_json(directory / "request.json")
        return directory, request, read_json(directory / "result.json")

    def current(request: dict[str, Any], result: dict[str, Any]) -> bool:
        run = SCAN_RUNS / request["run_id"]
        document = layouts.measurements(request["tag_layout_id"]).read()
        return bool(
            document.revision == request["measurement_revision"]
            and file_hash(run / "run.json") == result["manifest_sha256"]
            and file_hash(run / "graph.json") == result["graph_sha256"]
            and (file_hash(run / "mesh.ply") if (run / "mesh.ply").is_file() else None) == result["mesh_sha256"]
        )

    def worker(kind: str, directory: Path, *arguments: str) -> list[str]:
        return [
            sys.executable,
            "-u",
            "-m",
            "campervan.scan_analysis_worker",
            kind,
            str(directory.resolve()),
            *arguments,
        ]

    def available() -> None:
        if any(not task.done() for task in processing.tasks.values()):
            raise HTTPException(409, "Another scan task is running. Wait for it to finish.")

    @app.post("/api/v1/scans/analyses", status_code=202)
    async def create(request: AnalyseRequest) -> dict[str, Any]:
        available()
        try:
            run = scan_manifest(request.run_id)
            document = layouts.measurements(request.tag_layout_id).read()
            if run.get("tag_layout_id") != request.tag_layout_id or document.revision != request.revision:
                raise MeasurementConflict("The selected run/layout or measurements changed. Refresh before analysis.")
            if document.default_sigma_m is None:
                raise ValueError("Set typical measuring precision before analysis.")
            preference = processing.library.read().entries.get(f"run:{request.run_id}")
            value = str(uuid4())
            directory = location(value)
            directory.mkdir(parents=True)
            write_json(
                directory / "request.json",
                {
                    "run_id": request.run_id,
                    "tag_layout_id": request.tag_layout_id,
                    "measurement_revision": request.revision,
                    "measurements": document.model_dump(),
                    "job_id": value,
                },
            )
            processing.start_action(
                value,
                "analysis",
                worker("analyse", directory),
                {
                    "run_id": request.run_id,
                    "source_run_id": request.run_id,
                    "layout_id": request.tag_layout_id,
                    "name": "Analyse uncertainty",
                    "group_id": preference.group_id if preference else None,
                },
            )
            return {"id": value}
        except MeasurementConflict as error:
            raise HTTPException(409, str(error)) from error
        except (ValueError, KeyError) as error:
            raise HTTPException(422, str(error)) from error
        except OSError as error:
            raise HTTPException(500, str(error)) from error

    @app.get("/api/v1/scans/analyses/{analysis_id}")
    def status(analysis_id: str) -> dict[str, Any]:
        try:
            directory = location(analysis_id)
            request = read_json(directory / "request.json")
            result = read_json(directory / "result.json") if (directory / "result.json").is_file() else None
            diagnostic = read_json(directory / "diagnostic.json") if (directory / "diagnostic.json").is_file() else None
            solutions = history.read()
            acceptance = solutions["entries"].get(analysis_id)
            accepted_job = processing.job(acceptance["job_id"]) if acceptance else None
            suggestion_request = directory / "suggestion-job.json"
            suggestions_job = (
                processing.job(read_json(suggestion_request)["id"]) if suggestion_request.is_file() else None
            )
            suggestions = (
                read_json(directory / "suggestions.json") if (directory / "suggestions.json").is_file() else None
            )
            stale = layouts.measurements(request["tag_layout_id"]).read().revision != request["measurement_revision"]
            stale = stale or result is not None and not current(request, result)
            return {
                "id": analysis_id,
                "job": processing.job(request["job_id"]),
                "result": result,
                "diagnostic": diagnostic,
                "stale": stale,
                "acceptance": acceptance,
                "accepted_job": accepted_job,
                "solution_revision": solutions["revision"],
                "suggestions_job": suggestions_job,
                "suggestions": suggestions,
            }
        except (ValueError, KeyError, OSError) as error:
            raise HTTPException(422, f"Analysis unavailable: {error}") from error

    @app.post("/api/v1/scans/analyses/{analysis_id}/apply", status_code=202)
    async def apply(analysis_id: str, edit: AcceptRequest) -> dict[str, Any]:
        available()
        try:
            directory, request, result = context(analysis_id)
            if not current(request, result):
                raise MeasurementConflict("Analysis is stale. Analyse the current measurements before applying.")
            preference = processing.library.read().entries.get(f"run:{request['run_id']}")
            source_name = preference.display_name if preference and preference.display_name else request["run_id"]
            suffix = " — corrected"
            corrected_name = source_name[: 120 - len(suffix)] + suffix
            job_id = str(uuid4())
            run_id = f"corrected-{job_id}"
            history.update(
                edit.solution_revision,
                analysis_id,
                {
                    "source_run_id": request["run_id"],
                    "tag_layout_id": request["tag_layout_id"],
                    "result_run_id": run_id,
                    "job_id": job_id,
                    "active": True,
                },
            )
            return processing.start_action(
                job_id,
                "rebuild",
                worker("rebuild", directory, run_id),
                {
                    "run_id": run_id,
                    "source_run_id": request["run_id"],
                    "layout_id": request["tag_layout_id"],
                    "group_id": preference.group_id if preference else None,
                    "name": corrected_name,
                },
            )
        except MeasurementConflict as error:
            raise HTTPException(409, str(error)) from error
        except (ValueError, KeyError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/v1/scans/analyses/{analysis_id}/revert")
    def revert(analysis_id: str, edit: AcceptRequest) -> dict[str, str]:
        try:
            _, request, _ = context(analysis_id)
            record = history.read()["entries"].get(analysis_id)
            if record:
                scan_manifest(record["source_run_id"])
                history.update(edit.solution_revision, analysis_id, {**record, "active": False})
                processing.library.restore_result(f"run:{record['source_run_id']}")
            return {"result_key": f"run:{request['run_id']}"}
        except MeasurementConflict as error:
            raise HTTPException(409, str(error)) from error
        except (ValueError, KeyError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @app.post("/api/v1/scans/analyses/{analysis_id}/suggestions", status_code=202)
    async def suggestions(analysis_id: str, edit: SuggestRequest) -> dict[str, str]:
        available()
        try:
            directory, request, result = context(analysis_id)
            if not current(request, result):
                raise MeasurementConflict("Analysis is stale. Analyse again before requesting suggestions.")
            preference = processing.library.read().entries.get(f"run:{request['run_id']}")
            value = str(uuid4())
            processing.start_action(
                value,
                "analysis",
                worker("suggest", directory, str(edit.threshold_mm)),
                {
                    "run_id": request["run_id"],
                    "source_run_id": request["run_id"],
                    "layout_id": request["tag_layout_id"],
                    "name": "Suggest more measurements",
                    "group_id": preference.group_id if preference else None,
                },
            )
            write_json(directory / "suggestion-job.json", {"id": value})
            return {"id": value}
        except MeasurementConflict as error:
            raise HTTPException(409, str(error)) from error
        except (ValueError, KeyError, OSError) as error:
            raise HTTPException(422, str(error)) from error
