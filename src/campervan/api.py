"""Versioned parameter and model routes, with lifespan-owned regeneration."""

import asyncio
import math
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from campervan.coordinator import Coordinator, ModelStatus, WorkerFactory
from campervan.parameters import Parameters, parameter_schema
from campervan.settings import Settings, load_settings
from campervan.worker import start_worker


class ParameterResponse(BaseModel):
    session_id: str
    parameters: Parameters
    schema_: dict[str, object] = Field(serialization_alias="schema")
    viewer_url: str


class MutationResponse(BaseModel):
    session_id: str
    requested_revision: int


def _validation_json(value: object) -> object:
    """Normalize error inputs before applying FastAPI's standard JSON encoder."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: _validation_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_validation_json(item) for item in value]
    if isinstance(value, Exception):
        return str(value)
    return value


def build_app(settings: Settings, worker_factory: WorkerFactory = start_worker) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        coordinator = Coordinator(settings, worker_factory)
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

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": jsonable_encoder(_validation_json(error.errors()))})

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
