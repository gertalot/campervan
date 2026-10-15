"""Editable, provisional vehicle dimensions in millimetres."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Parameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, allow_inf_nan=False)

    cargo_width_mm: float = Field(
        default=1500.0, gt=0, title="Cargo width", json_schema_extra={"unit": "mm", "group": "Vehicle"}
    )
    cargo_length_mm: float = Field(
        default=1860.0, gt=0, title="Cargo length", json_schema_extra={"unit": "mm", "group": "Vehicle"}
    )
    arch_rear_offset_mm: float = Field(
        default=216.0,
        ge=0,
        title="Rear offset",
        description="Distance from the rear floor edge to the wheel arches.",
        json_schema_extra={"unit": "mm", "group": "Wheel arches"},
    )
    arch_length_mm: float = Field(
        default=750.0, gt=0, title="Length", json_schema_extra={"unit": "mm", "group": "Wheel arches"}
    )
    arch_height_mm: float = Field(
        default=280.0, gt=0, title="Height", json_schema_extra={"unit": "mm", "group": "Wheel arches"}
    )
    arch_radius_mm: float = Field(
        default=200.0, gt=0, title="Top radius", json_schema_extra={"unit": "mm", "group": "Wheel arches"}
    )
    arch_gap_mm: float = Field(
        default=1220.0,
        gt=0,
        title="Clear gap",
        description="Clear width between the arches; intrusion is derived from cargo width.",
        json_schema_extra={"unit": "mm", "group": "Wheel arches"},
    )
    rear_corner_radius_mm: float = Field(
        default=100.0, gt=0, title="Radius", json_schema_extra={"unit": "mm", "group": "Rear corners"}
    )
    rear_corner_height_mm: float = Field(
        default=1228.0,
        gt=0,
        title="Height",
        description="Reference surface height: the original rear door opening height plus its zero sill.",
        json_schema_extra={"unit": "mm", "group": "Rear corners"},
    )

    @model_validator(mode="after")
    def check_geometry(self) -> Self:
        if self.arch_gap_mm >= self.cargo_width_mm:
            raise ValueError("Arch clear gap must be smaller than cargo width.")
        if self.arch_rear_offset_mm + self.arch_length_mm > self.cargo_length_mm:
            raise ValueError("Wheel arches must fit within the cargo length.")
        if self.arch_radius_mm >= self.arch_height_mm or 2 * self.arch_radius_mm >= self.arch_length_mm:
            raise ValueError("Arch top radius must be below its height and half its length.")
        if 2 * self.rear_corner_radius_mm >= self.cargo_width_mm or self.rear_corner_radius_mm >= self.cargo_length_mm:
            raise ValueError("Rear corner radius must fit within the cargo outline.")
        return self


def default_parameters() -> Parameters:
    return Parameters()


def parameter_schema() -> dict[str, object]:
    return Parameters.model_json_schema()
