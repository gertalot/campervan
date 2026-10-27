"""Versioned parameter and model routes, with lifespan-owned regeneration."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.util import find_spec
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from campervan.coordinator import Coordinator, ModelStatus, Regenerate
from campervan.cutting import effective_options, source_key, stock_groups
from campervan.cutting_models import CuttingSettings, LayoutRequest, StockUpdate
from campervan.materials import PROJECT_PATH, ROLES, MaterialUpdate, catalogue, resolve
from campervan.parameter_fit import FitError, fit_parameters, parameter_constraints
from campervan.parameters import Parameters, parameter_schema
from campervan.planning_api import register_planning
from campervan.settings import Settings, load_settings
from campervan.worker import regenerate_model


class ParameterResponse(BaseModel):
    session_id: str
    parameters: Parameters
    schema_: dict[str, object] = Field(serialization_alias="schema")
    viewer_url: str
    errors: dict[str, str] = Field(default_factory=dict)
    adjustments: dict[str, str] = Field(default_factory=dict)


class Positions(BaseModel):
    """Live pose controls, updated without regenerating geometry."""

    table_mount: float = Field(default=0, ge=0, le=2, multiple_of=2, allow_inf_nan=False)
    table_height_mm: float = Field(default=700, ge=620, le=780, allow_inf_nan=False)
    table_arm_swivel_deg: float = Field(default=180, ge=0, le=360, allow_inf_nan=False)
    table_top_rotation_deg: float = Field(default=0, ge=0, le=360, allow_inf_nan=False)
    table_top_offset_percent: float = Field(default=0, ge=-100, le=100, allow_inf_nan=False)
    table_fold_open_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    table_stowed_x_mm: float = Field(default=800, ge=-1000, le=2500, allow_inf_nan=False)
    table_stowed_y_mm: float = Field(default=450, ge=-1000, le=2500, allow_inf_nan=False)
    table_stowed_z_mm: float = Field(default=0, ge=0, le=1500, allow_inf_nan=False)
    table_stowed_yaw_deg: float = Field(default=0, ge=0, le=360, allow_inf_nan=False)

    bed_extension_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    drawer_extension_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    doors_close_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    cabinet_upper_doors_open_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    cabinet_lower_doors_open_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    cabinet_storage_doors_open_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    cabinet_front_upper_door_open_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    cabinet_storage_upper_doors_open_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    solar_bag_x_mm: float = 750
    solar_bag_y_mm: float = 45
    solar_bag_z_mm: float = 0
    solar_bag_yaw_deg: float = 0
    chair_1_x_mm: float = 520
    chair_1_y_mm: float = 600
    chair_1_z_mm: float = 0
    chair_1_yaw_deg: float = 90
    chair_2_x_mm: float = 640
    chair_2_y_mm: float = 600
    chair_2_z_mm: float = 0
    chair_2_yaw_deg: float = 90
    chilly_bin_x_mm: float = 750
    chilly_bin_y_mm: float = 1050
    chilly_bin_z_mm: float = 0
    chilly_bin_yaw_deg: float = 90
    chilly_bin_handle_angle_deg: float = 0


def build_app(
    settings: Settings, regenerator: Regenerate = regenerate_model, project_path: Path = PROJECT_PATH
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        coordinator = Coordinator(settings, regenerator, project_path)
        app.state.coordinator = coordinator
        stop = asyncio.Event()
        watcher = None
        if settings.development:
            from campervan.dev import watch_cad

            watcher = asyncio.create_task(watch_cad(Path(__file__).resolve().parent / "cad", coordinator, stop))
        try:
            yield
        finally:
            try:
                if watcher is not None:
                    stop.set()
                    watcher.cancel()
                    try:
                        await watcher
                    except asyncio.CancelledError:
                        pass
            finally:
                await coordinator.close()

    app = FastAPI(lifespan=lifespan)
    register_planning(app, project_path)
    package = find_spec("ocp_viewer")
    assert package is not None and package.origin is not None
    assets = Path(package.origin).parent / "server" / "static"

    @app.get("/viewer-assets/js/shared-renderer.js", include_in_schema=False)
    async def shared_renderer() -> Response:
        # The pinned OCP bundle includes the complete THREE namespace. Expose it
        # from this same module so app meshes and GLTFLoader share its constructors.
        source = (assets / "js" / "three-cad-viewer.esm.js").read_text()
        return Response(source + "\nexport { THREE as sharedThree };\n", media_type="text/javascript")

    app.mount("/viewer-assets", StaticFiles(directory=assets), name="viewer-assets")

    def get_coordinator(request: Request) -> Coordinator:
        coordinator: Coordinator = request.app.state.coordinator
        return coordinator

    CurrentCoordinator = Annotated[Coordinator, Depends(get_coordinator)]

    @app.exception_handler(ValueError)
    async def value_error(request: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    def parameter_response(coordinator: Coordinator, parameters: Parameters) -> ParameterResponse:
        schema = cast(dict[str, Any], parameter_schema())
        for name, constraint in parameter_constraints(parameters).items():
            field = schema["properties"][name]
            field.update(constraint)
            field.pop("exclusiveMinimum", None)
            field.pop("exclusiveMaximum", None)
        for role in ROLES:
            for parameter in role.fields.values():
                schema["properties"][parameter]["material"] = role.id
        return ParameterResponse(
            session_id=coordinator.session_id,
            parameters=parameters,
            schema_=schema,
            viewer_url=settings.viewer_url,
        )

    @app.get("/api/v1/parameters", response_model=ParameterResponse)
    async def get_parameters(coordinator: CurrentCoordinator) -> ParameterResponse:
        return parameter_response(coordinator, coordinator.parameters)

    @app.post("/api/v1/parameters/preview", response_model=ParameterResponse)
    async def preview_parameters(parameters: Parameters, coordinator: CurrentCoordinator) -> ParameterResponse:
        parameters = resolve(parameters, coordinator.materials)
        adjustments: dict[str, str] = {}
        errors: dict[str, str] = {}
        try:
            parameters, adjustments = fit_parameters(parameters)
        except FitError as error:
            errors[error.field] = str(error)
        return parameter_response(coordinator, parameters).model_copy(
            update={"errors": errors, "adjustments": adjustments}
        )

    @app.put("/api/v1/parameters", status_code=202, response_model=ModelStatus)
    async def put_parameters(parameters: Parameters, coordinator: CurrentCoordinator) -> ModelStatus:
        await coordinator.accept(parameters)
        return coordinator.status()

    @app.get("/api/v1/materials")
    async def get_materials(coordinator: CurrentCoordinator) -> dict[str, object]:
        status = coordinator.status()
        return {
            "roles": [role.model_dump() for role in ROLES],
            "products": [product.model_dump() for product in catalogue()],
            "selections": {name: selection.model_dump() for name, selection in coordinator.materials.items()},
            "parameters": coordinator.parameters.model_dump(),
            "cuts": [cut.model_dump() for cut in coordinator.cuts],
            "cuts_revision": coordinator.cuts_revision,
            "requested_revision": status.requested_revision,
        }

    def cutting_data(coordinator: Coordinator) -> dict:
        groups = stock_groups(coordinator.cuts, coordinator.materials)
        sources = {}
        for group in groups:
            options = effective_options(group, coordinator.cutting.settings, coordinator.cutting.options.get(group["key"]))
            sources[group["key"]] = source_key(group, options)
        return {"groups": groups, "sources": sources, "state": coordinator.cutting.model_dump(),
                "jobs": coordinator.cutting_jobs,
                "current": coordinator.cuts_revision == coordinator.status().requested_revision}

    @app.get("/api/v1/cutting")
    async def get_cutting(coordinator: CurrentCoordinator) -> dict:
        return cutting_data(coordinator)

    def cutting_group(key: str, coordinator: Coordinator) -> dict:
        group = next((g for g in stock_groups(coordinator.cuts, coordinator.materials)
                      if g["key"] == key), None)
        if group is None:
            raise HTTPException(422, "This material is no longer in the cut list.")
        return group

    @app.put("/api/v1/cutting/settings")
    async def put_cutting_settings(settings: CuttingSettings, coordinator: CurrentCoordinator) -> dict:
        await coordinator.stop_cutting()
        coordinator.cutting.settings = settings
        coordinator.save_cutting()
        return cutting_data(coordinator)

    @app.put("/api/v1/cutting/options")
    async def put_cutting_options(update: StockUpdate, coordinator: CurrentCoordinator) -> dict:
        cutting_group(update.group, coordinator)
        await coordinator.stop_cutting(update.group)
        coordinator.cutting.options[update.group] = update.options
        coordinator.save_cutting()
        return cutting_data(coordinator)

    @app.post("/api/v1/cutting/layout", status_code=202)
    async def generate_cutting_layout(update: LayoutRequest, coordinator: CurrentCoordinator) -> dict:
        if coordinator.cuts_revision != coordinator.status().requested_revision:
            raise HTTPException(409, "The cut list is waiting for the current CAD model. Generate after it finishes.")
        group = cutting_group(update.group, coordinator)
        await coordinator.start_cutting(group)
        return cutting_data(coordinator)

    @app.post("/api/v1/cutting/stop")
    async def stop_cutting_layout(update: LayoutRequest, coordinator: CurrentCoordinator) -> dict:
        await coordinator.stop_cutting(update.group)
        return cutting_data(coordinator)

    @app.put("/api/v1/materials", status_code=202, response_model=ModelStatus)
    async def put_materials(update: MaterialUpdate, coordinator: CurrentCoordinator) -> ModelStatus:
        role = next((role for role in ROLES if role.id == update.role), None)
        if role is None:
            raise HTTPException(422, "Unknown material role")
        if set(update.custom) - role.fields.keys() or (update.custom and update.selection.product_id):
            raise HTTPException(422, "Custom dimensions require custom stock and must match this material role")
        values = coordinator.parameters.model_dump()
        values.update({role.fields[key]: value for key, value in update.custom.items()})
        parameters = Parameters.model_validate(values)
        await coordinator.accept(parameters, coordinator.materials | {role.id: update.selection})
        return coordinator.status()

    @app.post("/api/v1/model/load", response_model=ModelStatus)
    async def load_model(coordinator: CurrentCoordinator) -> ModelStatus:
        return await coordinator.load()

    @app.post("/api/v1/model/regenerate", status_code=202, response_model=ModelStatus)
    async def regenerate(coordinator: CurrentCoordinator) -> ModelStatus:
        await coordinator.accept(force=True)
        return coordinator.status()

    @app.patch("/api/v1/model/position", response_model=Positions)
    async def set_position(position: Positions, coordinator: CurrentCoordinator) -> Positions:
        coordinator.set_positions(position.model_dump(exclude_unset=True))
        return Positions.model_validate(coordinator.parameters.model_dump())

    @app.get("/api/v1/model/status", response_model=ModelStatus)
    async def model_status(coordinator: CurrentCoordinator) -> ModelStatus:
        return coordinator.status()

    return app


def create_app() -> FastAPI:
    settings = load_settings()
    app = build_app(settings)
    if not settings.development:
        web = Path(__file__).resolve().parent / "web"
        if not (web / "index.html").is_file():
            raise RuntimeError("Built frontend missing. Run make build first, or use make dev-api for development.")

        @app.get("/cad", include_in_schema=False)
        @app.get("/plan", include_in_schema=False)
        @app.get("/cuts", include_in_schema=False)
        @app.get("/bom", include_in_schema=False)
        @app.get("/bom/{material}", include_in_schema=False)
        async def frontend_view() -> FileResponse:
            return FileResponse(web / "index.html")

        app.mount("/", StaticFiles(directory=web, html=True), name="frontend")
    return app
