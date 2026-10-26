"""Saved cutting settings and layouts for the local project."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Mode = Literal["straight", "nesting"]
Grain = Literal["length", "width", "free"]


class Stock(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    name: str = "Full sheet"
    length: float = Field(gt=0, le=10000)
    width: float = Field(gt=0, le=10000)
    copies: int = Field(default=0, ge=0, le=1000)  # Zero means buy as many as needed.
    offcut: bool = False


class CuttingSettings(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    algorithm: Mode = "straight"
    kerf: float = Field(default=3, ge=0, le=20)
    trim: float = Field(default=0, ge=0, le=100)
    grain: Grain = "length"


class StockOptions(BaseModel):
    confirmed: bool = False
    orientations: dict[str, Grain] = Field(default_factory=dict)
    stock: list[Stock] = Field(default_factory=list, max_length=30)


class CuttingOptions(StockOptions):
    """Effective solver input, assembled from global settings and material stock."""
    kerf: float
    trim: float
    grain: Grain


class CuttingState(BaseModel):
    settings: CuttingSettings = Field(default_factory=CuttingSettings)
    options: dict[str, StockOptions] = Field(default_factory=dict)
    results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def migrate_settings(cls, value: Any) -> Any:
        if isinstance(value, dict) and "settings" not in value:
            previous = value.get("options", {}).get(value.get("group"), {})
            value = value | {"settings": {"algorithm": value.get("mode", "straight"),
                                         **{key: previous[key] for key in ("kerf", "trim", "grain") if key in previous}}}
        return value


class LayoutRequest(BaseModel):
    group: str


class StockUpdate(BaseModel):
    group: str
    options: StockOptions
