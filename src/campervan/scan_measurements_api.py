"""Small local API for the explicitly configured physical measurement document."""

from collections.abc import Callable

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from campervan.scan_layouts import ScanLayouts
from campervan.scan_measurements import (
    DistanceMeasurement,
    ExcludedPair,
    MeasurementConflict,
    MeasurementDocument,
)
from campervan.scans import scan_manifest


class EditDistance(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    revision: int = Field(ge=0, strict=True)
    tag_layout_id: str = Field(min_length=1)
    distance_m: float = Field(gt=0)
    entered_text: str = Field(min_length=1, max_length=128)
    source_run_id: str = Field(min_length=1)
    sigma_m: float | None = Field(default=None, gt=0)


class RemoveDistance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0, strict=True)
    tag_layout_id: str = Field(min_length=1)


class ConfigureMeasurements(RemoveDistance):
    default_sigma_m: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    pair_sigmas: dict[str, float | None] = Field(default_factory=dict)
    excluded_pairs: list[ExcludedPair] = Field(default_factory=list)


def register_scan_measurements(app: FastAPI, layouts: ScanLayouts) -> None:

    def operation(action: Callable[[], MeasurementDocument]) -> MeasurementDocument:
        try:
            return action()
        except MeasurementConflict as error:
            raise HTTPException(409, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, f"Invalid measurement data: {error}") from error
        except OSError as error:
            raise HTTPException(500, f"Measurements were not saved: {error}") from error

    @app.get("/api/v1/scans/measurements")
    def get_measurements(tag_layout_id: str | None = None) -> dict[str, bool | str | MeasurementDocument | None]:
        document = operation(lambda: layouts.measurements(tag_layout_id).read())
        name = document.tag_layout_id
        if document.tag_layout_id in layouts.stores:
            name = layouts.layout(document.tag_layout_id).name
        return {"configured": True, "document": document, "layout_name": name}

    @app.put("/api/v1/scans/measurements/settings")
    def configure(edit: ConfigureMeasurements) -> MeasurementDocument:
        return operation(
            lambda: layouts.measurements(edit.tag_layout_id).configure(
                edit.revision, edit.tag_layout_id, edit.default_sigma_m, edit.pair_sigmas, edit.excluded_pairs
            )
        )

    @app.put("/api/v1/scans/measurements/{tag_a}/{tag_b}")
    def put_measurement(tag_a: int, tag_b: int, edit: EditDistance) -> MeasurementDocument:
        try:
            run = scan_manifest(edit.source_run_id)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise HTTPException(422, "Unknown source scan.") from error
        if run.get("tag_layout_id") != edit.tag_layout_id:
            raise HTTPException(409, "This capture is not associated with the configured tag layout.")
        ids = {tag["id"] for tag in run.get("tags", [])}
        if tag_a not in ids or tag_b not in ids:
            raise HTTPException(422, "Both tags must be detected in the selected capture.")
        return operation(
            lambda: layouts.measurements(edit.tag_layout_id).upsert(
                edit.revision,
                edit.tag_layout_id,
                DistanceMeasurement(
                    tag_a=tag_a, tag_b=tag_b,
                    **edit.model_dump(exclude={"revision", "tag_layout_id"}, exclude_unset=True),
                ),
            )
        )

    @app.delete("/api/v1/scans/measurements/{tag_a}/{tag_b}")
    def delete_measurement(tag_a: int, tag_b: int, edit: RemoveDistance) -> MeasurementDocument:
        if tag_a <= 0 or tag_b <= 0 or tag_a == tag_b:
            raise HTTPException(422, "Choose two different positive tag IDs.")
        return operation(
            lambda: layouts.measurements(edit.tag_layout_id).remove(edit.revision, edit.tag_layout_id, tag_a, tag_b)
        )
