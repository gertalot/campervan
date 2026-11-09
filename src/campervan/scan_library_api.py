"""Local scan library API; discovery and asset addressing remain in their existing owner."""

from collections.abc import Callable
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from campervan.scan_groups import delete_group, move_item
from campervan.scan_library import ScanLibraryConflict, ScanLibraryDocument, ScanLibraryStore
from campervan.scan_processing import ScanProcessing
from campervan.scan_solutions import ScanSolutions
from campervan.scans import delete_scan_result


class DeleteScanResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    revision: int = Field(ge=0, strict=True)


class DeleteCaptureGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_id: str
    revision: int = Field(ge=0, strict=True)


class MoveScanItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["result", "capture"]
    key: str
    group_id: str | None
    revision: int = Field(ge=0, strict=True)


def register_scan_library(
    app: FastAPI, store: ScanLibraryStore, processing: ScanProcessing, history: ScanSolutions,
) -> Callable[[], ScanLibraryDocument]:

    def operation(action: Callable[[], ScanLibraryDocument]) -> ScanLibraryDocument:
        try:
            return action()
        except ScanLibraryConflict as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, f"Invalid scan library: {error}") from error
        except OSError as error:
            raise HTTPException(500, f"Scan library could not be read or saved: {error}") from error

    @app.get("/api/v1/scans/library")
    def get_library() -> ScanLibraryDocument:
        return operation(store.read)

    @app.put("/api/v1/scans/library")
    def put_library(candidate: ScanLibraryDocument) -> ScanLibraryDocument:
        return operation(lambda: store.save(candidate.revision, candidate))

    @app.delete("/api/v1/scans/library/result")
    def delete_result(edit: DeleteScanResult) -> ScanLibraryDocument:
        try:
            return operation(
                lambda: store.remove(edit.revision, edit.key, lambda: delete_scan_result(edit.key, store.path.parent))
            )
        except HTTPException as error:
            if error.status_code == 500:
                raise HTTPException(
                    500, f"Deletion did not finish; some files may already be removed. {error.detail}"
                ) from error
            raise

    @app.delete("/api/v1/scans/library/group")
    def remove_group(edit: DeleteCaptureGroup) -> ScanLibraryDocument:
        try:
            return operation(lambda: delete_group(processing, history, edit.revision, edit.group_id))
        except HTTPException as error:
            if error.status_code == 500:
                raise HTTPException(
                    500, f"Deletion did not finish; some files may already be removed. {error.detail}"
                ) from error
            raise

    @app.post("/api/v1/scans/library/move")
    def move(edit: MoveScanItem) -> ScanLibraryDocument:
        return operation(lambda: move_item(processing, edit.revision, edit.kind, edit.key, edit.group_id))

    return get_library
