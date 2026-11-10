"""Imported captures and one local reconstruction subprocess, using the existing scan CLI."""

import asyncio
import os
import re
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Callable, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from campervan.scan_alignment import TagAlignment
from campervan.scan_layouts import ScanLayouts
from campervan.scan_library import Name, ScanLibraryStore
from campervan.scan_photogrammetry import PhotographicSettings
from campervan.scans import SCAN_RUNS, ScanSettings, read_json, write_json


def identifier(value: str) -> str:
    if str(UUID(value)) != value:
        raise ValueError("Unknown capture or processing run.")
    return value


class CaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_id: str
    capture_ids: list[str] = Field(min_length=1)
    layout_id: str
    name: Name
    alignment_definition: TagAlignment | None = None


class PreviewCaptures(CaptureRequest):
    purpose: Literal["preview"]
    settings: ScanSettings = Field(default_factory=ScanSettings)


class ReconstructPhotos(CaptureRequest):
    purpose: Literal["photographic"]
    settings: PhotographicSettings = Field(default_factory=PhotographicSettings)


ProcessCaptures = Annotated[PreviewCaptures | ReconstructPhotos, Field(discriminator="purpose")]


class ScanProcessing:
    def __init__(self, library: ScanLibraryStore, layouts: ScanLayouts):
        self.library = library
        self.layouts = layouts
        self.captures = library.path.parent / "scan-captures"
        self.jobs = SCAN_RUNS.parent / "scan-jobs"
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.cancel_requests: set[str] = set()

    def capture(self, value: str) -> dict[str, Any]:
        data: dict[str, Any] = read_json(self.captures / identifier(value) / "capture.json")
        if data["id"] != value:
            raise ValueError("Capture identity differs from its directory.")
        data["kind"] = "database" if Path(data["filename"]).suffix.lower() == ".db" else "photo"
        return data

    def list_captures(self) -> list[dict[str, Any]]:
        return [self.capture(path.parent.name) for path in sorted(self.captures.glob("*/capture.json"))]

    def job(self, value: str, include_log: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = read_json(self.jobs / f"{identifier(value)}.json")
        if data["state"] == "processing" and value not in self.tasks:
            data.update(
                state="interrupted", error="Processing was interrupted. The imported captures can be processed again."
            )
        if data.get("source_run_id"):
            source = self.library.read().entries.get(f"run:{data['source_run_id']}")
            data["group_id"] = source.group_id if source else None
        elif data.get("result_key"):
            result = self.library.read().entries.get(data["result_key"])
            if result is not None:
                data["group_id"] = result.group_id
        if data.get("result_key") and not (SCAN_RUNS / data["run_id"] / "run.json").is_file():
            data.pop("result_key")
        log = self.jobs / f"{value}.log"
        if include_log and log.is_file():
            with log.open("rb") as stream:
                stream.seek(max(0, log.stat().st_size - 12000))
                data["log_tail"] = stream.read().decode(errors="replace")
        return data

    def list_jobs(self) -> list[dict[str, Any]]:
        return sorted(
            [
                job
                for path in self.jobs.glob("*.json")
                if (job := self.job(path.stem, include_log=False)).get("kind") != "analysis"
            ],
            key=lambda job: job["created_at"],
            reverse=True,
        )

    async def cancel(self, value: str) -> dict[str, Any]:
        job = self.job(identifier(value), include_log=False)
        task = self.tasks.get(value)
        if job["state"] != "processing" or task is None or task.done():
            return self.job(value)
        if value not in self.cancel_requests:
            self.cancel_requests.add(value)
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        # A task cancelled before its coroutine starts never enters _run's finally block.
        saved = read_json(self.jobs / f"{value}.json")
        if saved["state"] == "processing":
            saved.update(state="cancelled", stage="Cancelled", error=None, finished_at=datetime.now(UTC).isoformat())
            self._save(saved)
        self.cancel_requests.discard(value)
        return self.job(value)

    def start(self, request: ProcessCaptures) -> dict[str, Any]:
        if any(not task.done() for task in self.tasks.values()):
            raise ValueError("A capture reconstruction is already running. Wait for it to finish.")
        if request.group_id not in self.library.read().groups:
            raise ValueError("Unknown capture group.")
        if len(set(request.capture_ids)) != len(request.capture_ids):
            raise ValueError("Choose each capture only once.")
        captures = [self.capture(value) for value in request.capture_ids]
        if any(capture["group_id"] != request.group_id for capture in captures):
            raise ValueError("Choose captures belonging to this capture group.")
        if request.purpose == "preview" and any(capture["kind"] != "database" for capture in captures):
            raise ValueError("Quick previews use database depth. Deselect the still photos, or choose detailed reconstruction.")
        layout = self.layouts.layout(request.layout_id)
        if self.layouts.measurements(layout.id).read().tag_layout_id != layout.id:
            raise ValueError("Measurement document belongs to another tag layout.")
        for capture in captures:
            filename = capture["filename"]
            if Path(filename).name != filename or Path(filename).suffix.lower() not in {
                ".db", ".jpg", ".jpeg", ".png", ".heic"
            }:
                raise ValueError("Invalid stored capture filename.")
            path = self.captures / identifier(capture["id"]) / filename
            if path.is_symlink() or not path.is_file():
                raise ValueError("Imported capture file is missing or linked elsewhere.")
        settings = request.settings
        if request.purpose == "preview":
            settings = settings.model_copy(update={"tag_family": layout.tag_family, "tag_size_mm": layout.tag_size_mm,
                                                   "texture_mode": "baked"})
        value = str(uuid4())
        run_id = f"capture-{value}"
        self.jobs.mkdir(parents=True, exist_ok=True)
        job = {
            "id": value,
            "run_id": run_id,
            "group_id": request.group_id,
            "name": request.name,
            "layout_id": layout.id,
            "capture_ids": request.capture_ids,
            "purpose": request.purpose,
            "settings": settings.model_dump(),
            "state": "processing",
            "stage": "Starting reconstruction",
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
        }
        job["request"] = {
            "purpose": request.purpose, "name": request.name, "group_id": request.group_id,
            "tag_layout_id": layout.id, "tag_family": layout.tag_family, "tag_size_mm": layout.tag_size_mm,
            "settings": settings.model_dump(),
            "alignment_definition": request.alignment_definition.model_dump() if request.alignment_definition else None,
            "inputs": [{**capture, "capture_id": capture["id"],
                        "path": str((self.captures / capture["id"] / capture["filename"]).resolve())}
                       for capture in captures],
        }
        self.library.associate(request.group_id, layout.id)
        self._save(job)
        task = asyncio.create_task(self._run(job, captures))
        self.tasks[value] = task
        task.add_done_callback(lambda _: self.tasks.pop(value, None))
        return job

    def start_action(self, work_id: str, kind: str, command: list[str], metadata: dict[str, Any],
                     publish: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
        if any(not task.done() for task in self.tasks.values()):
            raise ValueError("Another scan task is running. Wait for it to finish.")
        self.jobs.mkdir(parents=True, exist_ok=True)
        job = {
            **metadata,
            "id": identifier(work_id),
            "kind": kind,
            "command": command,
            "state": "processing",
            "stage": "Starting",
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._save(job)
        task = asyncio.create_task(self._run(job, [], publish))
        self.tasks[work_id] = task
        task.add_done_callback(lambda _: self.tasks.pop(work_id, None))
        return job

    def _save(self, job: dict[str, Any]) -> None:
        path = self.jobs / f"{job['id']}.json"
        temporary = path.with_suffix(".tmp")
        write_json(temporary, job)
        temporary.replace(path)

    async def _run(self, job: dict[str, Any], captures: list[dict[str, Any]],
                   publish: Callable[[dict[str, Any]], None] | None = None) -> None:
        value = job["id"]
        output = SCAN_RUNS / job["run_id"]
        measurements = self.layouts.directory / job["layout_id"] / "measurements.json"
        command = job.get("command")
        if command is None:
            if job.get("purpose") == "photographic":
                command = [sys.executable, "-u", "-m", "campervan.cli", "scan", "reconstruct", "--request",
                           str((self.jobs / f"{value}.json").resolve()), "--output", str(output.resolve())]
            else:
                command = [sys.executable, "-u", "-m", "campervan.cli", "scan", "process"]
                for capture in captures:
                    command.append(str((self.captures / capture["id"] / capture["filename"]).resolve()))
                command += ["--output", str(output.resolve()), "--measurements", str(measurements.resolve())]
                for name, setting in job["settings"].items():
                    if setting is not None:
                        command += [f"--{name.replace('_', '-')}", str(setting)]
        process = None
        failure_detail = None
        try:
            with (self.jobs / f"{value}.log").open("wb") as log:
                process = await asyncio.create_subprocess_exec(
                    *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, start_new_session=True
                )
                assert process.stdout is not None
                while line := await process.stdout.readline():
                    log.write(line)
                    log.flush()
                    text = line.decode(errors="replace").strip()
                    if text.startswith("Scan processing failed:"):
                        failure_detail = text.removeprefix("Scan processing failed:").strip()
                    if text.startswith("[") and text.endswith("]"):
                        job["stage"] = text[1:-1]
                        job.pop("progress_percent", None)
                        self._save(job)
                    elif text.startswith(("Estimated depth-maps", "Optimized depth-maps", "Fused depth-maps",
                                          "Filtered depth-maps", "Dense fused depth-maps",
                                          "Geometric-consistent estimated depth-maps", "Processed iterations")):
                        job["stage"] = text
                        percentage = re.search(r"\(([\d.]+)%", text)
                        if percentage:
                            job["progress_percent"] = float(percentage[1])
                        self._save(job)
                code = await process.wait()
            if job.get("kind") != "analysis" and (output / "run.json").is_file():
                if job.get("purpose") == "preview":
                    manifest = read_json(output / "run.json")
                    manifest.update(purpose="preview", units="m", inputs=job["request"]["inputs"])
                    if definition := job["request"].get("alignment_definition"):
                        from campervan.scan_alignment import tag_alignment
                        try:
                            manifest["alignment"] = tag_alignment(manifest["tags"], TagAlignment.model_validate(definition))
                        except ValueError as error:
                            manifest["alignment"] = {"status": "unaligned", "definition": definition, "reason": str(error)}
                    write_json(output / "run.json", manifest)
                source = job.get("source_run_id")
                job["group_id"] = self.library.associate(
                    job["group_id"],
                    job["layout_id"],
                    (f"run:{job['run_id']}", job["name"]),
                    source_result=f"run:{source}" if source else None,
                )
                job["result_key"] = f"run:{job['run_id']}"
            if code:
                raise RuntimeError(failure_detail or f"Processing exited with code {code}. See the processing log below.")
            if "result_key" not in job and job.get("kind") != "analysis":
                raise RuntimeError("Processing finished without publishing a result. See the log below.")
            if publish is not None:
                publish(job)
            job.update(state="completed", stage="Ready to view")
        except asyncio.CancelledError:
            if value in self.cancel_requests:
                job.update(state="cancelled", stage="Cancelled", error=None)
            else:
                job.update(state="interrupted", error="API stopped during processing. Imported databases are retained.")
            raise
        except Exception as error:
            job.update(state="failed", error=str(error))
        finally:
            if process is not None and process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                await process.wait()
            job["finished_at"] = datetime.now(UTC).isoformat()
            self._save(job)

    async def close(self) -> None:
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
