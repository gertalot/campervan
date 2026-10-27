"""Keep the last complete CAD bundle and construct only changed geometry."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from campervan.materials import CutPart, Project, Selection, load_project, resolve, save_project
from campervan.model_cache import ModelBundle, model_fingerprint, read_bundle, save_bundle
from campervan.parameter_fit import fit_parameters
from campervan.parameters import Parameters
from campervan.paths import MODEL_CACHE_PATH, PROJECT_PATH
from campervan.settings import Settings
from campervan.viewer import replay_model
from campervan.worker import regenerate_model
from campervan.cutting import effective_options, layout_score, source_key
from campervan.cutting_worker import solve_layout

Regenerate = Callable[[Parameters], Awaitable[ModelBundle]]
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
        self._cache_path = MODEL_CACHE_PATH
        project = load_project(project_path)
        self.parameters = project.parameters
        self.materials = project.materials
        self.cutting = project.cutting
        self.cutting_jobs: dict[str, dict[str, Any]] = {}
        self._cutting_tasks: dict[str, asyncio.Task[None]] = {}
        self._bundle = read_bundle(self._cache_path)
        self.cuts: list[CutPart] = self._bundle.cuts if self._bundle else []
        self.cuts_revision: int | None = 0 if self._bundle else None
        matches = self._bundle is not None and self._bundle.fingerprint == model_fingerprint(self.parameters)
        self._status = ModelStatus(
            session_id=self.session_id,
            requested_revision=1 if self._bundle and not matches else 0,
            published_revision=0 if self._bundle else None,
            state="ready" if matches else "idle",
        )
        self._settings = settings
        self._regenerate = regenerate
        self._task: asyncio.Task[None] | None = None
        self._publication = asyncio.Lock()

    def save_cutting(self) -> None:
        save_project(Project(parameters=self.parameters, materials=self.materials, cutting=self.cutting),
                     self._project_path)

    async def start_cutting(self, group: dict) -> None:
        mode = self.cutting.settings.algorithm
        key = f"{group['key']}:{mode}"
        options = effective_options(group, self.cutting.settings, self.cutting.options.get(group["key"]))
        if not group["stock_sourced"] and not options.confirmed:
            raise ValueError("Set the available stock dimensions before arranging these pieces.")
        source = source_key(group, options)
        if self.cutting_jobs.get(key, {}).get("state") == "running":
            return
        self.cutting_jobs[key] = {"state": "running", "source": source, "error": None}
        self._cutting_tasks[key] = asyncio.create_task(
            self._run_cutting(key, {"group": group, "mode": mode, "options": options.model_dump()})
        )

    async def _run_cutting(self, key: str, payload: dict) -> None:
        try:
            async for event in solve_layout(payload):
                if error := event.get("error"):
                    raise ValueError(error)
                if result := event.get("result"):
                    previous = self.cutting.results.get(key)
                    if previous and previous["source"] == result["source"]:
                        if layout_score(result) > layout_score(previous):
                            continue
                    self.cutting.results[key] = result
                    self.save_cutting()
            self.cutting_jobs[key]["state"] = "complete"
        except asyncio.CancelledError:
            self.cutting_jobs[key]["state"] = "stopped"
            raise
        except Exception as error:
            logger.exception("Cutting layout failed")
            self.cutting_jobs[key].update(state="failed", error=str(error))

    async def stop_cutting(self, group: str | None = None) -> None:
        tasks = [task for key, task in self._cutting_tasks.items() if group is None or key.startswith(group + ":")]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def accept(
        self, parameters: Parameters | None = None, materials: dict[str, Selection] | None = None, *, force: bool = False
    ) -> int:
        selected = self.materials if materials is None else materials
        resolved = resolve(parameters or self.parameters, selected)
        resolved, _ = fit_parameters(resolved)
        previous_key = model_fingerprint(self.parameters)
        key = model_fingerprint(resolved)
        if key != previous_key:
            await self.stop_cutting()
        save_project(Project(parameters=resolved, materials=selected, cutting=self.cutting), self._project_path)
        self.parameters, self.materials = resolved, selected
        if not force and key == previous_key and self._status.state == "regenerating":
            return self._status.requested_revision
        if not force and self._bundle is not None and key == self._bundle.fingerprint:
            # A return to cached dimensions also supersedes an in-flight build for different dimensions.
            replay = key != previous_key or self._status.state != "ready"
            revision = self._status.requested_revision + int(replay)
            self.cuts = self._bundle.cuts
            self.cuts_revision = revision
            self._status = replace(self._status, requested_revision=revision, error=None)
            if replay:
                try:
                    async with self._publication:
                        await asyncio.to_thread(replay_model, self._bundle, self._settings)
                except Exception as failure:
                    logger.exception("Saved model delivery failed")
                    if revision == self._status.requested_revision:
                        self._status = replace(self._status, state="failed", error=ModelError(message=str(failure)))
                    return revision
            if revision == self._status.requested_revision:
                self._status = replace(self._status, published_revision=revision, state="ready", error=None)
            return revision
        revision = self._status.requested_revision + 1
        self._status = replace(self._status, requested_revision=revision, state="regenerating", error=None)
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())
        return revision

    async def load(self) -> ModelStatus:
        """Replay a saved model after the browser connects, or start its first build."""
        revision = self._status.requested_revision
        try:
            async with self._publication:
                if self._bundle is not None:
                    await asyncio.to_thread(replay_model, self._bundle, self._settings)
        except Exception as failure:
            logger.exception("Saved model delivery failed")
            if revision == self._status.requested_revision:
                self._status = replace(
                    self._status, state="failed", error=ModelError(message=f"Saved model delivery failed: {failure}")
                )
            return self._status
        if self._status.state != "regenerating":
            if self._bundle is not None and self._bundle.fingerprint == model_fingerprint(self.parameters):
                revision = self._status.requested_revision
                self.cuts_revision = revision
                self._status = replace(self._status, published_revision=revision, state="ready", error=None)
            else:
                await self.accept()
        return self._status

    def status(self) -> ModelStatus:
        return self._status

    def set_positions(self, positions: dict[str, float]) -> None:
        """Retain the displayed pose for subsequent builds without regenerating geometry."""
        self.parameters = Parameters.model_validate(self.parameters.model_dump() | positions)

    async def _run(self) -> None:
        while True:
            # An Apply returning to the cached model may have fulfilled the latest revision while we were building.
            if self._status.state == "ready":
                return
            revision = self._status.requested_revision
            try:
                bundle = await self._regenerate(self.parameters)
                if revision != self._status.requested_revision:
                    continue
                if bundle.fingerprint != model_fingerprint(self.parameters):
                    # Source changed during construction: do not label old geometry with the new source fingerprint.
                    continue
                async with self._publication:
                    if revision != self._status.requested_revision:
                        continue
                    save_bundle(self._cache_path, bundle)
                    self._bundle = bundle
                    self.cuts = bundle.cuts
                    self.cuts_revision = revision
                    await asyncio.to_thread(replay_model, bundle, self._settings)
                    if revision == self._status.requested_revision:
                        self._status = replace(self._status, published_revision=revision, state="ready", error=None)
                        return
            except Exception as failure:
                logger.exception("CAD build or viewer delivery failed")
                if revision == self._status.requested_revision:
                    self._status = replace(self._status, state="failed", error=ModelError(message=str(failure)))
                    return

    async def close(self) -> None:
        await self.stop_cutting()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
