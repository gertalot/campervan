"""Saved finishes for paintable CAD parts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


class PaintSwatch(BaseModel):
    colour: Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$", to_lower=True)]
    opacity: float = Field(ge=0, le=1, allow_inf_nan=False)
    texture: str = Field(min_length=1)


class PaintFinishes(BaseModel):
    assignments: dict[str, PaintSwatch] = Field(default_factory=dict)
    favourites: list[PaintSwatch] = Field(default_factory=list)


class PaintView(PaintFinishes):
    can_undo: bool
    can_redo: bool


class PaintChange(BaseModel):
    target: str = Field(min_length=1)
    swatch: PaintSwatch | None

    def apply_to(self, current: dict[str, PaintSwatch]) -> dict[str, PaintSwatch]:
        assignments = current.copy()
        if self.swatch is None:
            assignments.pop(self.target, None)
        else:
            assignments[self.target] = self.swatch
        return assignments


class PaintState(PaintFinishes):
    undo: list[PaintChange] = Field(default_factory=list)
    redo: list[PaintChange] = Field(default_factory=list)

    def view(self) -> PaintView:
        return PaintView(
            assignments=self.assignments, favourites=self.favourites, can_undo=bool(self.undo), can_redo=bool(self.redo)
        )

    def assign(self, change: PaintChange) -> PaintState:
        previous = self.assignments.get(change.target)
        if previous == change.swatch:
            return self
        return self.model_copy(
            update={
                "assignments": change.apply_to(self.assignments),
                "undo": [*self.undo, PaintChange(target=change.target, swatch=previous)],
                "redo": [],
            }
        )

    def step(self, direction: Literal["undo", "redo"]) -> PaintState:
        source, destination = (self.undo, self.redo) if direction == "undo" else (self.redo, self.undo)
        if not source:
            return self
        change = source[-1]
        inverse = PaintChange(target=change.target, swatch=self.assignments.get(change.target))
        opposite = "redo" if direction == "undo" else "undo"
        return self.model_copy(
            update={
                "assignments": change.apply_to(self.assignments),
                direction: source[:-1],
                opposite: [*destination, inverse],
            }
        )
