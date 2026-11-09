"""Imported captures and one local reconstruction subprocess, using the existing scan CLI."""

import asyncio
import os
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from campervan.scan_layouts import ScanLayouts
from campervan.scan_library import Name, ScanLibraryStore
from campervan.scans import SCAN_RUNS, ScanSettings, read_json, write_json


def identifier(value: str) -> str:
    if str(UUID(value)) != value:
        raise ValueError("Unknown capture or processing run.")
    return value


class ProcessCaptures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_id: str
    capture_ids: list[str] = Field(min_length=1)
    layout_id: str
    name: Name
    settings: ScanSettings = Field(default_factory=ScanSettings)


class ScanProcessing:
    def __init__(self, library: ScanLibraryStore, layouts: ScanLayouts):
        self.library = library
        self.layouts = layouts
        self.captures = library.path.parent / "scan-captures"
        self.jobs = SCAN_RUNS.parent / "scan-jobs"
        self.tasks: dict[str, asyncio.Task[None]] = {}

    def capture(self, value: str) -> dict[str, Any]:
        data: dict[str, Any] = read_json(self.captures / identifier(value) / "capture.json")
        if data["id"] != value:
            raise ValueError("Capture identity differs from its directory.")
        return data

    def list_captures(self) -> list[dict[str, Any]]:
        return [self.capture(path.parent.name) for path in sorted(self.captures.glob("*/capture.json"))]

    def job(self, value: str, include_log: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = read_json(self.jobs / f"{identifier(value)}.json")
        if data["state"] == "processing" and value not in self.tasks:
            data.update(
                state="interrupted", error="Processing was interrupted. The imported databases can be processed again."
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

    def start(self, request: ProcessCaptures) -> dict[str, Any]:
        if any(not task.done() for task in self.tasks.values()):
            raise ValueError("A capture reconstruction is already running. Wait for it to finish.")
        if request.group_id not in self.library.read().groups:
            raise ValueError("Unknown capture group.")
        if len(set(request.capture_ids)) != len(request.capture_ids):
            raise ValueError("Choose each database only once.")
        captures = [self.capture(value) for value in request.capture_ids]
        if any(capture["group_id"] != request.group_id for capture in captures):
            raise ValueError("Choose databases belonging to this capture group.")
        layout = self.layouts.layout(request.layout_id)
        if self.layouts.measurements(layout.id).read().tag_layout_id != layout.id:
            raise ValueError("Measurement document belongs to another tag layout.")
        for capture in captures:
            filename = capture["filename"]
            if Path(filename).name != filename or Path(filename).suffix.lower() != ".db":
                raise ValueError("Invalid stored capture filename.")
            path = self.captures / identifier(capture["id"]) / filename
            if path.is_symlink() or not path.is_file():
                raise ValueError("Imported capture file is missing or linked elsewhere.")
        settings = request.settings.model_copy(
            update={"tag_family": layout.tag_family, "tag_size_mm": layout.tag_size_mm}
        )
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
            "settings": settings.model_dump(),
            "state": "processing",
            "stage": "Starting reconstruction",
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.library.associate(request.group_id, layout.id)
        self._save(job)
        task = asyncio.create_task(self._run(job, captures))
        self.tasks[value] = task
        task.add_done_callback(lambda _: self.tasks.pop(value, None))
        return job

    def start_action(self, work_id: str, kind: str, command: list[str], metadata: dict[str, Any]) -> dict[str, Any]:
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
        task = asyncio.create_task(self._run(job, []))
        self.tasks[work_id] = task
        task.add_done_callback(lambda _: self.tasks.pop(work_id, None))
        return job

    def _save(self, job: dict[str, Any]) -> None:
        path = self.jobs / f"{job['id']}.json"
        temporary = path.with_suffix(".tmp")
        write_json(temporary, job)
        temporary.replace(path)

    async def _run(self, job: dict[str, Any], captures: list[dict[str, Any]]) -> None:
        value = job["id"]
        output = SCAN_RUNS / job["run_id"]
        measurements = self.layouts.directory / job["layout_id"] / "measurements.json"
        command = job.get("command")
        if command is None:
            command = [sys.executable, "-u", "-m", "campervan.cli", "scan", "process"]
            for capture in captures:
                command.append(str((self.captures / capture["id"] / capture["filename"]).resolve()))
            command += ["--output", str(output.resolve()), "--measurements", str(measurements.resolve())]
            for name, setting in job["settings"].items():
                if setting is not None:
                    command += [f"--{name.replace('_', '-')}", str(setting)]
        process = None
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
                    if text.startswith("[") and text.endswith("]"):
                        job["stage"] = text[1:-1]
                        self._save(job)
                code = await process.wait()
            if job.get("kind") != "analysis" and (output / "run.json").is_file():
                source = job.get("source_run_id")
                job["group_id"] = self.library.associate(
                    job["group_id"],
                    job["layout_id"],
                    (f"run:{job['run_id']}", job["name"]),
                    source_result=f"run:{source}" if source else None,
                )
                job["result_key"] = f"run:{job['run_id']}"
            if code:
                raise RuntimeError(f"Processing exited with code {code}. See the processing log below.")
            if "result_key" not in job and job.get("kind") != "analysis":
                raise RuntimeError("Processing finished without publishing a result. See the log below.")
            job.update(state="completed", stage="Ready to view")
        except asyncio.CancelledError:
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
