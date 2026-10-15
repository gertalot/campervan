"""Validated, immutable inputs and metadata for the demonstration cube."""

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_SIZE_MM = 100.0


class Parameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    size_mm: float = Field(
        strict=True,
        allow_inf_nan=False,
        gt=0,
        le=1000,
        title="Cube size",
        json_schema_extra={"default": DEFAULT_SIZE_MM, "unit": "mm"},
    )


def default_parameters() -> Parameters:
    return Parameters(size_mm=DEFAULT_SIZE_MM)


def parameter_schema() -> dict[str, object]:
    return Parameters.model_json_schema()
