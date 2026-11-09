"""Physical distances for a supplied tag layout, independent of reconstructed geometry."""

from pathlib import Path
from threading import Lock
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DistanceMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    tag_a: int = Field(gt=0, strict=True)
    tag_b: int = Field(gt=0, strict=True)
    distance_m: float = Field(gt=0)
    entered_text: str = Field(min_length=1, max_length=128)
    source_run_id: str = Field(min_length=1)
    sigma_m: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def canonical_pair(self) -> "DistanceMeasurement":
        if self.tag_a == self.tag_b:
            raise ValueError("Choose two different tags.")
        self.tag_a, self.tag_b = sorted((self.tag_a, self.tag_b))
        return self


class ExcludedPair(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tag_a: int = Field(gt=0, strict=True)
    tag_b: int = Field(gt=0, strict=True)
    reason: str = Field(min_length=1, max_length=240)

    @model_validator(mode="after")
    def pair(self) -> "ExcludedPair":
        if self.tag_a == self.tag_b:
            raise ValueError("Choose two different tags.")
        self.tag_a, self.tag_b = sorted((self.tag_a, self.tag_b))
        return self


class MeasurementDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    tag_layout_id: str = Field(min_length=1)
    revision: int = Field(ge=0, strict=True)
    distances: list[DistanceMeasurement]
    default_sigma_m: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    excluded_pairs: list[ExcludedPair] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_pairs(self) -> "MeasurementDocument":
        pairs = [(record.tag_a, record.tag_b) for record in self.distances]
        if len(set(pairs)) != len(pairs):
            raise ValueError("The measurement document contains duplicate tag pairs.")
        exclusions = [(record.tag_a, record.tag_b) for record in self.excluded_pairs]
        if len(set(exclusions)) != len(exclusions):
            raise ValueError("The measurement document contains duplicate excluded pairs.")
        return self


class MeasurementConflict(ValueError):
    pass


def read_measurements(path: Path) -> MeasurementDocument:
    return MeasurementDocument.model_validate_json(path.read_text(encoding="utf-8"))


class MeasurementStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()

    def read(self) -> MeasurementDocument:
        return read_measurements(self.path)

    def _current(self, revision: int, layout: str) -> MeasurementDocument:
        document = self.read()
        if document.tag_layout_id != layout:
            raise MeasurementConflict("The selected capture belongs to a different tag layout.")
        if document.revision != revision:
            raise MeasurementConflict("Measurements changed. Review the refreshed values and press Enter again.")
        return document

    def _save(self, document: MeasurementDocument) -> MeasurementDocument:
        document.revision += 1
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(document.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
        return document

    def upsert(self, expected_revision: int, tag_layout_id: str, record: DistanceMeasurement) -> MeasurementDocument:
        with self.lock:
            document = self._current(expected_revision, tag_layout_id)
            pair = (record.tag_a, record.tag_b)
            previous = next((r for r in document.distances if (r.tag_a, r.tag_b) == pair), None)
            record = record.model_copy(update={"sigma_m": previous.sigma_m if previous else None})
            document.distances = [r for r in document.distances if (r.tag_a, r.tag_b) != pair] + [record]
            document.distances.sort(key=lambda r: (r.tag_a, r.tag_b))
            return self._save(document)

    def remove(self, expected_revision: int, tag_layout_id: str, tag_a: int, tag_b: int) -> MeasurementDocument:
        with self.lock:
            document = self._current(expected_revision, tag_layout_id)
            pair = tuple(sorted((tag_a, tag_b)))
            document.distances = [r for r in document.distances if (r.tag_a, r.tag_b) != pair]
            return self._save(document)

    def configure(
        self,
        expected_revision: int,
        tag_layout_id: str,
        default_sigma_m: float | None,
        pair_sigmas: dict[str, float | None],
        excluded_pairs: list[ExcludedPair],
    ) -> MeasurementDocument:
        with self.lock:
            document = self._current(expected_revision, tag_layout_id)
            document.default_sigma_m = default_sigma_m
            document.excluded_pairs = excluded_pairs
            known = {f"{r.tag_a}:{r.tag_b}" for r in document.distances}
            if set(pair_sigmas) - known:
                raise ValueError("Unknown measured pair for precision override.")
            for record in document.distances:
                key = f"{record.tag_a}:{record.tag_b}"
                if key in pair_sigmas:
                    record.sigma_m = pair_sigmas[key]
            document = MeasurementDocument.model_validate(document.model_dump())
            return self._save(document)
