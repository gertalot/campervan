"""Regenerate serially, using the latest parameters when edits arrive during a run."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal
from uuid import uuid4

from campervan.materials import PROJECT_PATH, CutPart, Project, Selection, load_project, resolve, save_project
from campervan.parameters import Parameters
from campervan.settings import Settings
from campervan.worker import regenerate_model

Regenerate = Callable[[Parameters, Settings], Awaitable[list[CutPart] | None]]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelError:
    message: str


@dataclass(frozen=True)
class ModelStatus:
    session_id: str
    requested_revision: int = 0
    published_revision: int | None = None
    state: Literal["idle", "regenerating", "ready", "failed"] = "idle"
    error: ModelError | None = None


class Coordinator:
    def __init__(
        self, settings: Settings, regenerate: Regenerate = regenerate_model, project_path: Path = PROJECT_PATH
    ) -> None:
        self.session_id = str(uuid4())
        self._project_path = project_path
        project = load_project(project_path)
        self.parameters = project.parameters
        self.materials = project.materials
        self.cuts: list[CutPart] = []
        self.cuts_revision: int | None = None
        self._status = ModelStatus(session_id=self.session_id)
        self._settings = settings
        self._regenerate = regenerate
        self._task: asyncio.Task[None] | None = None

    async def accept(self, parameters: Parameters | None = None, materials: dict[str, Selection] | None = None) -> int:
        selected = self.materials if materials is None else materials
        resolved = resolve(parameters or self.parameters, selected)
        save_project(Project(parameters=resolved, materials=selected), self._project_path)
        self.parameters, self.materials = resolved, selected
        revision = self._status.requested_revision + 1
        self._status = replace(self._status, requested_revision=revision, state="regenerating", error=None)
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())
        return revision

    def status(self) -> ModelStatus:
        return self._status

    def set_positions(self, positions: dict[str, float]) -> None:
        """Retain the displayed pose for subsequent builds without regenerating geometry."""
        self.parameters = self.parameters.model_copy(update=positions)

    async def _run(self) -> None:
        while True:
            revision = self._status.requested_revision
            error = None
            try:
                cuts = await self._regenerate(self.parameters, self._settings)
                if revision == self._status.requested_revision:
                    self.cuts = cuts or []
                    self.cuts_revision = revision
                self._status = replace(self._status, published_revision=revision)
            except Exception as failure:
                logger.error("Regeneration failed: %s", failure)
                error = ModelError(message=str(failure))
            if revision == self._status.requested_revision:
                self._status = replace(self._status, state="failed" if error else "ready", error=error)
                return

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
