"""Acceptance history, separate from physical measurements and immutable scan runs."""

from pathlib import Path
from threading import Lock
from typing import Any

from campervan.scan_measurements import MeasurementConflict
from campervan.scans import read_json, write_json


class ScanSolutions:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "revision": 0, "entries": {}}
        document: dict[str, Any] = read_json(self.path)
        if document.get("version") != 1 or not isinstance(document.get("entries"), dict):
            raise ValueError("Invalid scan solution history; it has not been reset.")
        return document

    def update(self, expected: int, analysis_id: str, record: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            document = self.read()
            if document["revision"] != expected:
                raise MeasurementConflict("Accepted solutions changed. Refresh before applying/reverting.")
            previous = document["entries"].get(analysis_id)
            document["entries"][analysis_id] = {**record, "previous": previous}
            document["revision"] += 1
            temporary = self.path.with_suffix(".tmp")
            write_json(temporary, document)
            temporary.replace(self.path)
            return document
