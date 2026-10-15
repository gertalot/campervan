"""Versioned parameter and model routes, with lifespan-owned regeneration."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from campervan.coordinator import Coordinator, ModelStatus, Regenerate
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


class BedPosition(BaseModel):
    bed_extension_percent: float = Field(ge=0, le=100, allow_inf_nan=False)


def build_app(settings: Settings, regenerator: Regenerate = regenerate_model) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        coordinator = Coordinator(settings, regenerator)
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

    def get_coordinator(request: Request) -> Coordinator:
        coordinator: Coordinator = request.app.state.coordinator
        return coordinator

    CurrentCoordinator = Annotated[Coordinator, Depends(get_coordinator)]

    @app.get("/api/v1/parameters", response_model=ParameterResponse)
    async def get_parameters(coordinator: CurrentCoordinator) -> ParameterResponse:
        return ParameterResponse(
            session_id=coordinator.session_id,
            parameters=coordinator.parameters,
            schema_=parameter_schema(),
            viewer_url=settings.viewer_url,
        )

    @app.put("/api/v1/parameters", status_code=202, response_model=MutationResponse)
    async def put_parameters(parameters: Parameters, coordinator: CurrentCoordinator) -> MutationResponse:
        revision = await coordinator.accept(parameters)
        return MutationResponse(session_id=coordinator.session_id, requested_revision=revision)

    @app.post("/api/v1/model/regenerate", status_code=202, response_model=MutationResponse)
    async def regenerate(coordinator: CurrentCoordinator) -> MutationResponse:
        revision = await coordinator.accept()
        return MutationResponse(session_id=coordinator.session_id, requested_revision=revision)

    @app.patch("/api/v1/model/position", response_model=BedPosition)
    async def set_position(position: BedPosition, coordinator: CurrentCoordinator) -> BedPosition:
        coordinator.set_bed_position(position.bed_extension_percent)
        return position

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
        app.mount("/", StaticFiles(directory=web, html=True), name="frontend")
    return app
