"""Stream local database imports and expose reconstruction progress without a separate service."""

import asyncio
import hashlib
import shutil
import sqlite3
from collections.abc import Callable
from typing import Any, TypeVar
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from campervan.scan_layouts import NewTagLayout, ScanLayouts, TagLayout
from campervan.scan_processing import ProcessCaptures, ScanProcessing
from campervan.scans import database_info, write_json

T = TypeVar("T")


def register_scan_processing(app: FastAPI, processing: ScanProcessing, layouts: ScanLayouts) -> None:
    def operation(action: Callable[[], T]) -> T:
        try:
            return action()
        except (ValueError, KeyError, sqlite3.DatabaseError) as error:
            raise HTTPException(422, str(error)) from error
        except OSError as error:
            raise HTTPException(500, str(error)) from error

    @app.get("/api/v1/scans/imports")
    def imports() -> dict[str, Any]:
        return operation(
            lambda: {"captures": processing.list_captures(), "jobs": processing.list_jobs(), "layouts": layouts.list()}
        )

    @app.post("/api/v1/scans/layouts", status_code=201)
    def create_layout(definition: NewTagLayout) -> TagLayout:
        return operation(lambda: layouts.create(definition))

    @app.post("/api/v1/scans/captures", status_code=201)
    async def upload(request: Request, group_id: str, filename: str) -> dict[str, Any]:
        if group_id not in operation(processing.library.read).groups:
            raise HTTPException(422, "Unknown capture group.")
        if not filename.lower().endswith(".db") or len(filename) > 200 or any(c in filename for c in "/\\;\x00"):
            raise HTTPException(422, "Select an RTAB-Map .db file with a plain filename.")
        value = str(uuid4())
        directory = processing.captures / value
        directory.mkdir(parents=True)
        temporary = directory / "upload.part"
        try:
            digest = hashlib.sha256()
            with temporary.open("wb") as stream:
                async for chunk in request.stream():
                    stream.write(chunk)
                    digest.update(chunk)
            info = await asyncio.to_thread(database_info, temporary)
            if not info["node_ids"]:
                raise ValueError("This database contains no capture frames.")
            fingerprint = digest.hexdigest()
            for previous in processing.list_captures():
                if previous["group_id"] == group_id and previous.get("sha256") == fingerprint:
                    shutil.rmtree(directory)
                    return previous
            with processing.library.lock:
                if group_id not in processing.library.read().groups:
                    raise ValueError("The capture group was deleted during upload.")
                temporary.rename(directory / filename)
                capture = {
                    "id": value,
                    "group_id": group_id,
                    "filename": filename,
                    "bytes": (directory / filename).stat().st_size,
                    "frames": len(info["node_ids"]),
                    "database_version": info["version"],
                    "sha256": fingerprint,
                }
                write_json(directory / "capture.json", capture)
            return capture
        except BaseException as error:
            shutil.rmtree(directory)
            if isinstance(error, (ValueError, sqlite3.DatabaseError)):
                raise HTTPException(422, f"Cannot import {filename}: {error}") from error
            raise

    @app.post("/api/v1/scans/process", status_code=202)
    async def process(request: ProcessCaptures) -> dict[str, Any]:
        return operation(lambda: processing.start(request))

    @app.get("/api/v1/scans/process/{job_id}")
    def progress(job_id: str) -> dict[str, Any]:
        return operation(lambda: processing.job(job_id))

    @app.post("/api/v1/scans/process/{job_id}/cancel")
    async def cancel(job_id: str) -> dict[str, Any]:
        operation(lambda: processing.job(job_id))
        return await processing.cancel(job_id)
