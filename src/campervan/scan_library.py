"""Project-owned presentation preferences, separate from scan assets and measurements."""

from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class ScanEntryPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: Name | None = None
    group_id: str | None = None
    archived: bool = Field(default=False, strict=True)


class ScanLibraryDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    revision: int = Field(default=0, ge=0, strict=True)
    default_key: str | None = None
    groups: dict[str, Name] = Field(default_factory=dict)
    group_layouts: dict[str, str] = Field(default_factory=dict)
    entries: dict[str, ScanEntryPreferences] = Field(default_factory=dict)

    @model_validator(mode="after")
    def references(self) -> "ScanLibraryDocument":
        if any(not key.strip() for key in self.groups):
            raise ValueError("Capture group IDs cannot be blank.")
        if any(key not in self.groups for key in self.group_layouts):
            raise ValueError("Unknown capture group for tag layout.")
        for key, entry in self.entries.items():
            if not key.startswith(("run:", "preview:")) or not key.partition(":")[2]:
                raise ValueError("Result keys must start with run: or preview: and include an identifier.")
            if entry.group_id is not None and entry.group_id not in self.groups:
                raise ValueError("Unknown capture group.")
        if self.default_key is not None:
            if self.default_key not in self.entries or self.entries[self.default_key].archived:
                raise ValueError("The default must be an active library entry.")
        return self


class ScanLibraryConflict(ValueError):
    pass


class ScanLibraryStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()

    def read(self) -> ScanLibraryDocument:
        try:
            source = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ScanLibraryDocument()
        return ScanLibraryDocument.model_validate_json(source)

    def save(self, expected_revision: int, candidate: ScanLibraryDocument) -> ScanLibraryDocument:
        with self.lock:
            if self.read().revision != expected_revision:
                raise ScanLibraryConflict("Scan library changed. Review the refreshed library and retry your edit.")
            document = ScanLibraryDocument.model_validate(candidate.model_dump())
            return self._write(document, expected_revision + 1)

    def remove(self, expected_revision: int, key: str, delete_files: Callable[[], None]) -> ScanLibraryDocument:
        with self.lock:
            document = self.read()
            if document.revision != expected_revision:
                raise ScanLibraryConflict("Scan library changed. Review the refreshed library before deleting.")
            delete_files()
            document.entries.pop(key, None)
            if document.default_key == key:
                document.default_key = None
            return self._write(document, expected_revision + 1)

    def _write(self, document: ScanLibraryDocument, revision: int) -> ScanLibraryDocument:
        document.revision = revision
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(document.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
        return document

    def edit(self, expected_revision: int, change: Callable[[ScanLibraryDocument], None]) -> ScanLibraryDocument:
        with self.lock:
            document = self.read()
            if document.revision != expected_revision:
                raise ScanLibraryConflict("Scan library changed. Review the refreshed library before continuing.")
            change(document)
            document = ScanLibraryDocument.model_validate(document.model_dump())
            return self._write(document, expected_revision + 1)

    def associate(
        self,
        group_id: str | None,
        layout_id: str,
        result: tuple[str, str] | None = None,
        *, source_result: str | None = None,
    ) -> str | None:
        """Merge a processing update with current preferences, preserving intervening user edits."""
        with self.lock:
            document = self.read()
            if source_result is not None:
                source = document.entries.get(source_result)
                group_id = source.group_id if source else None
            if group_id is not None and group_id not in document.groups:
                raise ValueError("Unknown capture group.")
            if group_id is not None and source_result is None:
                document.group_layouts[group_id] = layout_id
            if result:
                key, name = result
                document.entries[key] = ScanEntryPreferences(display_name=name, group_id=group_id)
            self._write(document, document.revision + 1)
            return group_id

    def restore_result(self, key: str) -> None:
        with self.lock:
            document = self.read()
            entry = document.entries.get(key)
            if entry is not None and entry.archived:
                entry.archived = False
                self._write(document, document.revision + 1)


def decorate_scans(discovered: list[dict[str, Any]], document: ScanLibraryDocument) -> list[dict[str, Any]]:
    results = []
    for scan in discovered:
        key = f"run:{scan['id']}" if scan.get("id") else f"preview:{scan['name']}"
        entry = document.entries.get(key, ScanEntryPreferences())
        results.append(
            {
                **scan,
                "key": key,
                "display_name": entry.display_name or scan["name"],
                "group_id": entry.group_id,
                "group_name": document.groups.get(entry.group_id) if entry.group_id is not None else None,
                "archived": entry.archived,
                "is_default": document.default_key == key,
            }
        )
    return results
