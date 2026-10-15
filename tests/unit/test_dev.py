"""Inject filesystem events without running an operating-system watcher."""

import asyncio
from pathlib import Path

from campervan.coordinator import Coordinator
from campervan.dev import watch_cad
from campervan.parameters import Parameters
from campervan.settings import Settings
from campervan.worker import GenerationError
from tests.unit.test_coordinator import Factory, completed


def test_cad_watch_filters_batches_and_recovers_without_resetting_parameters(monkeypatch, tmp_path):
    async def scenario():
        import watchfiles

        changes = asyncio.Queue()
        observed = {}

        async def events(directory, **kwargs):
            observed.update(directory=directory, **kwargs)
            while not kwargs["stop_event"].is_set():
                yield await changes.get()

        monkeypatch.setattr(watchfiles, "awatch", events)
        factory = Factory()
        coordinator = Coordinator(Settings(), factory)
        stop = asyncio.Event()
        task = asyncio.create_task(watch_cad(tmp_path, coordinator, stop))
        try:
            session = coordinator.session_id
            await coordinator.accept(Parameters(size_mm=150))
            first = await factory.next()
            first.generated.set()
            first.finish.set()
            await completed(coordinator)
            assert coordinator.status().requested_revision == 1  # watcher has no initial request
            await changes.put({(2, str(tmp_path / "notes.txt")), (2, str(tmp_path.parent / "api.py"))})
            await changes.put({(2, str(tmp_path / "cube.py")), (1, str(tmp_path / "other.py"))})
            broken = await factory.next()
            broken.error = GenerationError("invalid syntax")
            broken.generated.set()
            await completed(coordinator)
            assert coordinator.status().state == "failed"
            await changes.put({(2, str(tmp_path / "cube.py"))})
            fixed = await factory.next()
            fixed.generated.set()
            fixed.finish.set()
            await completed(coordinator)
            assert coordinator.status().requested_revision == 3
            assert coordinator.status().state == "ready"
            assert coordinator.parameters.size_mm == 150
            assert coordinator.session_id == session
            assert observed["debounce"] == 250
            assert Path(observed["directory"]) == tmp_path
        finally:
            stop.set()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            await coordinator.close()

    asyncio.run(scenario())


def test_app_stops_watcher_before_coordinator(monkeypatch):
    async def scenario():
        import campervan.dev
        from campervan.api import build_app

        started = asyncio.Event()
        stopped = asyncio.Event()

        async def watcher(directory, coordinator, stop):
            started.set()
            try:
                await stop.wait()
            finally:
                assert not coordinator._closed
                stopped.set()

        monkeypatch.setattr(campervan.dev, "watch_cad", watcher)
        app = build_app(Settings(development=True), Factory())
        async with app.router.lifespan_context(app):
            await asyncio.wait_for(started.wait(), 1)
        assert stopped.is_set()
        assert app.state.coordinator._closed

    asyncio.run(scenario())
