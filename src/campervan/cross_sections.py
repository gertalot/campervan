"""Hand-authored cross-section outlines and explicit recording, separate from scan geometry."""

from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal, Self

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

Point = Annotated[tuple[float, float], Field(strict=False)]


class SectionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)


class OutlineSegment(SectionRecord):
    """Coordinates are horizontal position and CAD Z in the section's plane, in millimetres."""

    kind: Literal["line", "cubic"]
    end: Point
    control1: Point | None = None
    control2: Point | None = None

    @model_validator(mode="after")
    def controls_match_kind(self) -> Self:
        if self.kind == "cubic" and (self.control1 is None or self.control2 is None):
            raise ValueError("A cubic segment needs both control points.")
        if self.kind == "line" and (self.control1 is not None or self.control2 is not None):
            raise ValueError("A straight segment must not have curve control points.")
        return self


class CrossSection(SectionRecord):
    id: str = Field(min_length=1, max_length=128)
    label: str = Field(default="", max_length=240)
    plane: Literal["XZ", "YZ"] = "XZ"
    y_mm: float | None = None
    x_mm: float | None = None
    scan_key: str = Field(min_length=1, max_length=240)
    centre_x_mm: float = 750.0
    start: Point | None = None
    floor_z_mm: float | None = None
    ceiling_z_mm: float | None = None
    segments: list[OutlineSegment] = Field(min_length=1)
    mirror_x: bool = True
    opposite_start: Point | None = None
    opposite_segments: list[OutlineSegment] | None = Field(default=None, min_length=1)
    state: Literal["draft", "recorded"] = "draft"
    notes: str = ""

    @model_validator(mode="after")
    def plane_and_outline(self) -> Self:
        if self.opposite_segments is not None and not self.notes.strip():
            raise ValueError("Explain the authored side-to-side exception in the section notes.")
        if self.plane == "YZ":
            if self.x_mm is None or self.start is None or self.y_mm is not None:
                raise ValueError("A YZ section needs x_mm and a [Y, Z] start, without y_mm.")
            if self.opposite_start is not None and self.opposite_segments is None:
                raise ValueError("An opposite start needs an authored opposite outline.")
            if self.opposite_segments is not None and not self.mirror_x:
                raise ValueError("An opposite YZ outline requires mirror_x so both side positions are displayed.")
            return self

        if self.y_mm is None or self.x_mm is not None or self.start is not None:
            raise ValueError("An XZ section needs y_mm, without x_mm or an explicit start.")
        if not self.mirror_x:
            raise ValueError("mirror_x applies to YZ sections; XZ sections use both half-outlines.")
        if self.opposite_start is not None:
            raise ValueError("XZ outlines start at the floor centreline and must not define opposite_start.")
        floor, ceiling = self.floor_z_mm, self.ceiling_z_mm
        if floor is None or ceiling is None:
            raise ValueError("An XZ section needs floor_z_mm and ceiling_z_mm.")
        if ceiling <= floor:
            raise ValueError("The ceiling must be above the floor.")
        self._validate_half(self.segments, floor, ceiling)
        if self.opposite_segments is not None:
            self._validate_half(self.opposite_segments, floor, ceiling)
        return self

    @staticmethod
    def _validate_half(segments: list[OutlineSegment], floor: float, ceiling: float) -> None:
        if len(segments) < 3:
            raise ValueError("An XZ half-outline needs at least three segments.")
        for segment in segments:
            for point in (segment.end, segment.control1, segment.control2):
                if point is not None and point[0] < 0:
                    raise ValueError("XZ coordinates must be nonnegative distances from the centreline.")
        first, last = segments[0], segments[-1]
        if first.kind != "line" or first.end[0] <= 0 or abs(first.end[1] - floor) > 1e-6:
            raise ValueError("The outline must start with a horizontal floor from the centreline.")
        if (
            last.kind != "line"
            or abs(last.end[0]) > 1e-6
            or abs(last.end[1] - ceiling) > 1e-6
            or segments[-2].end[0] <= 0
            or abs(segments[-2].end[1] - ceiling) > 1e-6
        ):
            raise ValueError("The outline must finish with a horizontal ceiling back to the centreline.")


class CrossSectionDocument(SectionRecord):
    version: Literal[1] = 1
    revision: int = Field(default=0, ge=0)
    sections: list[CrossSection] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_ids(self) -> Self:
        ids = [section.id for section in self.sections]
        if len(ids) != len(set(ids)):
            raise ValueError("The cross-section document contains duplicate section IDs.")
        return self


class EditSection(SectionRecord):
    revision: int = Field(ge=0)
    section: CrossSection


class RecordSection(SectionRecord):
    revision: int = Field(ge=0)


class SectionConflict(ValueError):
    pass


class UnknownSection(ValueError):
    pass


class CrossSectionStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()

    def read(self) -> CrossSectionDocument:
        if not self.path.exists():
            return CrossSectionDocument()
        return CrossSectionDocument.model_validate_json(self.path.read_text(encoding="utf-8"))

    def _current(self, revision: int) -> CrossSectionDocument:
        document = self.read()
        if document.revision != revision:
            raise SectionConflict("Cross sections changed. Refresh the sections before saving again.")
        return document

    def _save(self, document: CrossSectionDocument) -> CrossSectionDocument:
        document.revision += 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(document.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
        return document

    def upsert(self, revision: int, section: CrossSection) -> CrossSectionDocument:
        with self.lock:
            document = self._current(revision)
            previous = next((item for item in document.sections if item.id == section.id), None)
            if previous is not None and previous.state == "recorded":
                raise SectionConflict("Recorded sections are kept unchanged. Create a new draft with a new ID.")
            if section.state != "draft":
                raise ValueError("Save an authored outline as a draft, then use Record section explicitly.")
            document.sections = [item for item in document.sections if item.id != section.id] + [section]
            return self._save(document)

    def record(self, revision: int, section_id: str) -> CrossSectionDocument:
        with self.lock:
            document = self._current(revision)
            section = next((item for item in document.sections if item.id == section_id), None)
            if section is None:
                raise UnknownSection("Unknown cross section.")
            if section.state == "recorded":
                raise SectionConflict("This section is already recorded and has been kept unchanged.")
            section.state = "recorded"
            return self._save(document)


def register_cross_sections(app: FastAPI, project_path: Path) -> None:
    store = CrossSectionStore(project_path.with_name("cross-sections.json"))

    def operation(action: Callable[[], CrossSectionDocument]) -> CrossSectionDocument:
        try:
            return action()
        except UnknownSection as error:
            raise HTTPException(404, str(error)) from error
        except SectionConflict as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, f"Invalid cross-section data: {error}") from error
        except OSError as error:
            raise HTTPException(500, f"Cross sections could not be read or saved: {error}") from error

    @app.get("/api/v1/cross-sections")
    def get_sections() -> CrossSectionDocument:
        return operation(store.read)

    @app.put("/api/v1/cross-sections/{section_id}")
    def put_section(section_id: str, edit: EditSection) -> CrossSectionDocument:
        if edit.section.id != section_id:
            raise HTTPException(422, "The section ID must match the URL.")
        return operation(lambda: store.upsert(edit.revision, edit.section))

    @app.post("/api/v1/cross-sections/{section_id}/record")
    def record_section(section_id: str, edit: RecordSection) -> CrossSectionDocument:
        return operation(lambda: store.record(edit.revision, section_id))
