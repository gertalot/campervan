"""Independent physical tag layouts and their measurement documents."""

from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from campervan.scan_library import Name
from campervan.scan_measurements import MeasurementDocument, MeasurementStore


class NewTagLayout(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    name: Name
    tag_family: Literal["36h11"] = "36h11"
    tag_size_mm: float = Field(gt=0)


class TagLayout(NewTagLayout):
    id: str


class ScanLayouts:
    def __init__(self, legacy_path: Path):
        self.legacy = MeasurementStore(legacy_path)
        self.directory = legacy_path.parent / "scan-tag-layouts"
        self.stores: dict[str, MeasurementStore] = {}
        self.lock = Lock()

    def layout(self, identifier: str) -> TagLayout:
        if str(UUID(identifier)) != identifier:
            raise ValueError("Unknown tag layout.")
        layout = TagLayout.model_validate_json((self.directory / identifier / "layout.json").read_text())
        if layout.id != identifier:
            raise ValueError("Tag layout identity differs from its directory.")
        return layout

    def list(self) -> list[TagLayout]:
        return [self.layout(path.parent.name) for path in sorted(self.directory.glob("*/layout.json"))]

    def create(self, definition: NewTagLayout) -> TagLayout:
        layout = TagLayout(id=str(uuid4()), **definition.model_dump())
        directory = self.directory / layout.id
        directory.mkdir(parents=True)
        (directory / "measurements.json").write_text(
            MeasurementDocument(tag_layout_id=layout.id, revision=0, distances=[]).model_dump_json(indent=2) + "\n"
        )
        (directory / "layout.json").write_text(layout.model_dump_json(indent=2) + "\n")
        return layout

    def measurements(self, identifier: str | None = None) -> MeasurementStore:
        if identifier is None:
            return self.legacy
        try:
            managed = str(UUID(identifier)) == identifier
        except ValueError:
            managed = False
        if managed and (self.directory / identifier / "layout.json").is_file():
            self.layout(identifier)
        elif self.legacy.path.is_file() and self.legacy.read().tag_layout_id == identifier:
            return self.legacy
        else:
            raise ValueError("Unknown tag layout.")
        with self.lock:
            if identifier not in self.stores:
                self.stores[identifier] = MeasurementStore(self.directory / identifier / "measurements.json")
            return self.stores[identifier]
