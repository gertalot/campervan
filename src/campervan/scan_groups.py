"""Capture-group deletion and moves over the existing library and imported files."""

import shutil
from typing import Literal

from campervan.scan_library import ScanEntryPreferences, ScanLibraryDocument
from campervan.scan_processing import ScanProcessing, identifier
from campervan.scans import completed_scans, delete_scan_result, read_json, write_json


def result_family(key: str) -> set[str]:
    parents = {
        f"run:{run['id']}": f"run:{run['source_run_id']}"
        for run in completed_scans() if run.get("source_run_id")
    }
    family = {key}
    while True:
        expanded = family | {parent for child, parent in parents.items() if child in family}
        expanded |= {child for child, parent in parents.items() if parent in expanded}
        if expanded == family:
            return family
        family = expanded


def move_item(
    processing: ScanProcessing,
    revision: int,
    kind: Literal["result", "capture"],
    key: str,
    group_id: str | None,
) -> ScanLibraryDocument:
    def change(document: ScanLibraryDocument) -> None:
        if group_id is not None and group_id not in document.groups:
            raise ValueError("Unknown destination capture group.")
        if kind == "capture":
            if group_id is None:
                raise ValueError("Choose a capture group for an imported database.")
            if any(not task.done() for task in list(processing.tasks.values())):
                raise ValueError("Wait for scan processing to finish before moving an imported database.")
            directory = processing.captures / identifier(key)
            if directory.is_symlink() or directory.resolve().parent != processing.captures.resolve():
                raise ValueError("Invalid imported capture directory.")
            capture = processing.capture(key)
            capture["group_id"] = group_id
            path = processing.captures / identifier(key) / "capture.json"
            temporary = path.with_suffix(".tmp")
            write_json(temporary, capture)
            temporary.replace(path)
        else:
            available = {f"run:{run['id']}" for run in completed_scans()}
            if key not in document.entries and key not in available:
                raise ValueError("Unknown scan result.")
            for member in result_family(key):
                document.entries.setdefault(member, ScanEntryPreferences()).group_id = group_id
    return processing.library.edit(revision, change)


def delete_group(
    processing: ScanProcessing, revision: int, group_id: str,
) -> ScanLibraryDocument:
    def change(document: ScanLibraryDocument) -> None:
        if group_id not in document.groups:
            raise ValueError("Unknown capture group.")
        if any(not task.done() for task in list(processing.tasks.values())):
            raise ValueError("Wait for scan processing to finish before deleting a capture group.")
        keys = {key for key, entry in document.entries.items() if entry.group_id == group_id}
        for key in list(keys):
            keys.update(result_family(key))
        captures = [capture for capture in processing.list_captures() if capture["group_id"] == group_id]
        # Validate imported directories before deleting any files; never follow a stored directory link.
        directories = [processing.captures / identifier(capture["id"]) for capture in captures]
        for directory in directories:
            if directory.is_symlink() or directory.resolve().parent != processing.captures.resolve():
                raise ValueError("Invalid imported capture directory.")
        for key in keys:
            delete_scan_result(key, processing.library.path.parent)
        for directory in directories:
            shutil.rmtree(directory)
        # Physical measurements and workflow evidence remain independent of capture-library deletion.
        run_ids = {key.removeprefix("run:") for key in keys if key.startswith("run:")}
        for job_path in processing.jobs.glob("*.json"):
            job = read_json(job_path)
            if (
                job.get("group_id") == group_id
                or job.get("run_id") in run_ids
                or job.get("source_run_id") in run_ids
            ):
                job_path.unlink()
                job_path.with_suffix(".log").unlink(missing_ok=True)
        for key in keys:
            document.entries.pop(key, None)
        if document.default_key in keys:
            document.default_key = None
        document.group_layouts.pop(group_id, None)
        del document.groups[group_id]
    return processing.library.edit(revision, change)
