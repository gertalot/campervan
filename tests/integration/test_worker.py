"""Real spawn/IPC lifecycle tests. No target starts a service."""

import asyncio
import importlib

import pytest

from campervan.parameters import Parameters
from campervan.settings import Settings
from tests.fixtures import worker_targets


def modules():
    return importlib.import_module("campervan.worker")


async def start(monkeypatch, target, timeout=0.1):
    worker_module = modules()
    monkeypatch.setattr(worker_module, "worker_main", target)
    return await worker_module.start_worker(
        Parameters(size_mm=150), Settings(viewer_port=4567, publication_timeout_s=timeout)
    )


def assert_closed(worker):
    assert not worker._process.is_alive()
    assert worker._process.exitcode is not None
    assert worker._connection.closed
    assert all(task.done() for task in worker._receives)


def test_waits_for_authorization_and_reaps_after_publication(monkeypatch):
    async def run():
        worker = await start(monkeypatch, worker_targets.authorized)
        try:
            await worker.wait_generated()
            await asyncio.sleep(0.05)
            assert worker._process.is_alive()
            assert not worker._connection.poll()
            await worker.publish()
        finally:
            await worker.close()
        assert_closed(worker)
        assert worker._process.exitcode == 0

    asyncio.run(run())


@pytest.mark.parametrize(
    "target",
    [worker_targets.generation_error, worker_targets.eof, worker_targets.child_exit, worker_targets.unexpected],
)
def test_generation_errors_eof_exit_and_unexpected_messages_fail(monkeypatch, target):
    async def run():
        worker = await start(monkeypatch, target)
        with pytest.raises(modules().GenerationError) as error:
            await worker.wait_generated()
        assert error.value.stage == "generation"
        await worker.close()
        assert_closed(worker)

    asyncio.run(run())


def test_publication_error_is_not_success(monkeypatch):
    async def run():
        worker = await start(monkeypatch, worker_targets.publication_error)
        await worker.wait_generated()
        with pytest.raises(modules().PublicationError, match="viewer absent"):
            await worker.publish()
        await worker.close()
        assert_closed(worker)

    asyncio.run(run())


def test_publication_timeout_terminates_and_reaps_child(monkeypatch):
    async def run():
        worker = await start(monkeypatch, worker_targets.publication_hang)
        await worker.wait_generated()
        with pytest.raises(modules().PublicationError, match="timed out"):
            await worker.publish()
        assert_closed(worker)

    asyncio.run(run())


@pytest.mark.parametrize("stage", ["generation", "publication"])
def test_cancellation_finishes_receive_and_reaps_child(monkeypatch, stage):
    async def run():
        target = worker_targets.generation_hang if stage == "generation" else worker_targets.publication_hang
        worker = await start(monkeypatch, target, timeout=10)
        if stage == "publication":
            await worker.wait_generated()
            task = asyncio.create_task(worker.publish())
        else:
            task = asyncio.create_task(worker.wait_generated())
        await asyncio.sleep(0.1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert_closed(worker)

    asyncio.run(run())


def test_real_child_builds_cube_and_is_closed_without_publication():
    async def run():
        worker = await modules().start_worker(Parameters(size_mm=150), Settings())
        try:
            await asyncio.wait_for(worker.wait_generated(), timeout=30)
            assert worker._process.is_alive()
            assert not worker._connection.poll()
        finally:
            await worker.close()
        assert_closed(worker)

    asyncio.run(run())


@pytest.mark.parametrize("target", [worker_targets.publication_exit, worker_targets.published_then_crash])
def test_unexpected_exit_is_not_successful_publication(monkeypatch, target):
    async def run():
        worker = await start(monkeypatch, target)
        await worker.wait_generated()
        with pytest.raises(modules().PublicationError):
            await worker.publish()
        assert_closed(worker)

    asyncio.run(run())


def test_production_target_reports_cad_import_error_as_generation_failure(monkeypatch, capfd):
    async def run():
        worker = await start(monkeypatch, worker_targets.production_import_error)
        with pytest.raises(modules().GenerationError, match="controlled CAD import syntax failure"):
            await worker.wait_generated()
        assert_closed(worker)

    asyncio.run(run())
    assert "Traceback" in capfd.readouterr().err


def test_production_target_holds_shape_until_authorized(monkeypatch):
    async def run():
        worker = await start(monkeypatch, worker_targets.production_with_observed_publication)
        try:
            await worker.wait_generated()
            await asyncio.sleep(0.05)
            assert not worker._connection.poll()
            worker._connection.send({"type": "publish"})
            assert await asyncio.to_thread(worker._connection.recv) == {"type": "viewer-called"}
            assert await asyncio.to_thread(worker._connection.recv) == {"type": "published"}
        finally:
            await worker.close()
        assert_closed(worker)

    asyncio.run(run())


def test_parent_eof_abandons_held_shape_without_publication(monkeypatch):
    async def run():
        worker = await start(monkeypatch, worker_targets.production_with_observed_publication)
        await worker.wait_generated()
        worker._connection.close()
        await asyncio.to_thread(worker._process.join, 2)
        assert worker._process.exitcode == 0
        await worker.close()
        assert_closed(worker)

    asyncio.run(run())
