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

    def revise(self, identifier: str, definition: "ReviseTagLayout", known_tags: set[int] | None = None) -> TagLayout:
        source = self.measurements(identifier)
        with source.lock:
            document = source.read()
            if document.revision != definition.revision:
                raise ValueError("Measurements changed. Refresh before revising the layout.")
            sets = [definition.unchanged, definition.moved, definition.removed, definition.added]
            if any(tag <= 0 for group in sets for tag in group):
                raise ValueError("Tag IDs must be positive.")
            if sum(map(len, sets)) != len(set().union(*sets)):
                raise ValueError("Tag change sets must be disjoint.")
            from campervan.scans import SCAN_RUNS, scan_manifest
            known = {tag["id"] for path in SCAN_RUNS.glob("*/run.json")
                     for run in [scan_manifest(path.parent.name)] if run.get("tag_layout_id") == identifier
                     for tag in run.get("tags", [])}
            known |= known_tags or set()
            known |= {tag for pair in [*document.distances, *document.excluded_pairs]
                     for tag in (pair.tag_a, pair.tag_b)}
            if definition.added & known:
                raise ValueError("Added tags must not already belong to the old layout.")
            if not known <= definition.unchanged | definition.moved | definition.removed:
                raise ValueError("Classify every tag referenced by saved observations or exclusions.")
            layout = TagLayout(id=str(uuid4()), name=definition.name, tag_family=definition.tag_family,
                               tag_size_mm=definition.tag_size_mm)
            copied = MeasurementDocument(
                tag_layout_id=layout.id, revision=0,
                distances=[r for r in document.distances
                           if r.tag_a in definition.unchanged and r.tag_b in definition.unchanged],
                default_sigma_m=document.default_sigma_m,
                excluded_pairs=[r for r in document.excluded_pairs
                                if r.tag_a in definition.unchanged and r.tag_b in definition.unchanged],
            )
            directory = self.directory / layout.id
            directory.mkdir(parents=True)
            (directory / "measurements.json").write_text(
                copied.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
            (directory / "layout.json").write_text(layout.model_dump_json(indent=2) + "\n", encoding="utf-8")
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


class ReviseTagLayout(NewTagLayout):
    revision: int = Field(ge=0, strict=True)
    unchanged: set[int] = Field(default_factory=set)
    moved: set[int] = Field(default_factory=set)
    removed: set[int] = Field(default_factory=set)
    added: set[int] = Field(default_factory=set)
