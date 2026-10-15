"""Serialize acceptance and publication while coalescing pending CAD requests."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from typing import Literal, Protocol
from uuid import uuid4

from campervan.parameters import Parameters, default_parameters
from campervan.settings import Settings
from campervan.viewer import PublicationError
from campervan.worker import start_worker

logger = logging.getLogger(__name__)


class ModelWorker(Protocol):
    async def wait_generated(self) -> None: ...
    async def publish(self) -> None: ...
    async def close(self) -> None: ...


WorkerFactory = Callable[[Parameters, Settings], Awaitable[ModelWorker]]


@dataclass(frozen=True)
class ModelError:
    stage: Literal["generation", "publication"]
    message: str


@dataclass(frozen=True)
class ModelStatus:
    session_id: str
    requested_revision: int = 0
    published_revision: int | None = None
    state: Literal["idle", "regenerating", "ready", "failed"] = "idle"
    error: ModelError | None = None


class Coordinator:
    def __init__(self, settings: Settings, worker_factory: WorkerFactory = start_worker) -> None:
        self.session_id = str(uuid4())
        self._parameters = default_parameters()
        self._status = ModelStatus(session_id=self.session_id)
        self._settings = settings
        self._worker_factory = worker_factory
        self._gate = asyncio.Lock()
        self._pending: tuple[int, Parameters] | None = None
        self._task: asyncio.Task[None] | None = None
        self._closed = False
        self._close_task: asyncio.Task[None] | None = None

    @property
    def parameters(self) -> Parameters:
        return self._parameters

    async def accept(self, parameters: Parameters | None = None) -> int:
        async with self._gate:
            if self._closed:
                raise RuntimeError("Coordinator is closed")
            if parameters is not None:
                self._parameters = parameters
            revision = self._status.requested_revision + 1
            self._pending = (revision, self._parameters)
            self._status = replace(self._status, requested_revision=revision, state="regenerating", error=None)
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._run())
            return revision

    def status(self) -> ModelStatus:
        return self._status

    async def _run(self) -> None:
        while self._pending is not None and not self._closed:
            revision, parameters = self._pending
            self._pending = None
            worker = None
            stage: Literal["generation", "publication"] = "generation"
            try:
                worker = await self._worker_factory(parameters, self._settings)
                await worker.wait_generated()
                async with self._gate:
                    if revision != self._status.requested_revision or self._closed:
                        continue
                    stage = "publication"
                    try:
                        await worker.publish()
                    finally:
                        # Publication and reaping belong to the same acceptance transaction.
                        await worker.close()
                    self._status = replace(self._status, published_revision=revision, state="ready", error=None)
            except Exception as error:
                logger.exception("Model %s failed for revision %s", stage, revision)
                async with self._gate:
                    if revision == self._status.requested_revision and not self._closed:
                        self._status = replace(
                            self._status,
                            state="failed",
                            error=ModelError(
                                stage="publication" if isinstance(error, PublicationError) else stage,
                                message=str(error),
                            ),
                        )
            finally:
                if worker is not None:
                    await worker.close()

    async def _close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def close(self) -> None:
        self._closed = True
        self._pending = None
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._close())
        cancellation = None
        while not self._close_task.done():
            try:
                await asyncio.shield(self._close_task)
            except asyncio.CancelledError as error:
                cancellation = error
        self._close_task.result()
        if cancellation is not None:
            raise cancellation
