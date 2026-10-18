"""Versioned parameter and model routes, with lifespan-owned regeneration."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.util import find_spec
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from campervan.coordinator import Coordinator, ModelStatus, Regenerate
from campervan.materials import PROJECT_PATH, ROLES, MaterialUpdate, catalogue
from campervan.parameters import Parameters, parameter_schema
from campervan.settings import Settings, load_settings
from campervan.worker import regenerate_model


class ParameterResponse(BaseModel):
    session_id: str
    parameters: Parameters
    schema_: dict[str, object] = Field(serialization_alias="schema")
    viewer_url: str


class MutationResponse(BaseModel):
    session_id: str
    requested_revision: int


class Positions(BaseModel):
    """Live pose controls, updated without regenerating geometry."""

    bed_extension_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    drawer_extension_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    cross_lid_open_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    doors_close_percent: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)


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
    package = find_spec("ocp_viewer")
    assert package is not None and package.origin is not None
    assets = Path(package.origin).parent / "server" / "static"
    app.mount("/viewer-assets", StaticFiles(directory=assets), name="viewer-assets")

    def get_coordinator(request: Request) -> Coordinator:
        coordinator: Coordinator = request.app.state.coordinator
        return coordinator

    CurrentCoordinator = Annotated[Coordinator, Depends(get_coordinator)]

    @app.exception_handler(ValueError)
    async def value_error(request: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.get("/api/v1/parameters", response_model=ParameterResponse)
    async def get_parameters(coordinator: CurrentCoordinator) -> ParameterResponse:
        schema = cast(dict[str, Any], parameter_schema())
        for role in ROLES:
            for parameter in role.fields.values():
                schema["properties"][parameter]["material"] = role.id
        return ParameterResponse(
            session_id=coordinator.session_id,
            parameters=coordinator.parameters,
            schema_=schema,
            viewer_url=settings.viewer_url,
        )

    @app.put("/api/v1/parameters", status_code=202, response_model=MutationResponse)
    async def put_parameters(parameters: Parameters, coordinator: CurrentCoordinator) -> MutationResponse:
        revision = await coordinator.accept(parameters)
        return MutationResponse(session_id=coordinator.session_id, requested_revision=revision)

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

    @app.put("/api/v1/materials", status_code=202, response_model=MutationResponse)
    async def put_materials(update: MaterialUpdate, coordinator: CurrentCoordinator) -> MutationResponse:
        role = next((role for role in ROLES if role.id == update.role), None)
        if role is None:
            raise HTTPException(422, "Unknown material role")
        if set(update.custom) - role.fields.keys() or (update.custom and update.selection.product_id):
            raise HTTPException(422, "Custom dimensions require custom stock and must match this material role")
        values = coordinator.parameters.model_dump()
        values.update({role.fields[key]: value for key, value in update.custom.items()})
        parameters = Parameters.model_validate(values)
        revision = await coordinator.accept(parameters, coordinator.materials | {role.id: update.selection})
        return MutationResponse(session_id=coordinator.session_id, requested_revision=revision)

    @app.post("/api/v1/model/regenerate", status_code=202, response_model=MutationResponse)
    async def regenerate(coordinator: CurrentCoordinator) -> MutationResponse:
        revision = await coordinator.accept()
        return MutationResponse(session_id=coordinator.session_id, requested_revision=revision)

    @app.patch("/api/v1/model/position", response_model=Positions)
    async def set_position(position: Positions, coordinator: CurrentCoordinator) -> Positions:
        coordinator.set_positions(position.model_dump(exclude_unset=True))
        return Positions(
            bed_extension_percent=coordinator.parameters.bed_extension_percent,
            drawer_extension_percent=coordinator.parameters.drawer_extension_percent,
            cross_lid_open_percent=coordinator.parameters.cross_lid_open_percent,
            doors_close_percent=coordinator.parameters.doors_close_percent,
        )

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
        @app.get("/bom", include_in_schema=False)
        @app.get("/bom/{material}", include_in_schema=False)
        async def frontend_view() -> FileResponse:
            return FileResponse(web / "index.html")

        app.mount("/", StaticFiles(directory=web, html=True), name="frontend")
    return app
