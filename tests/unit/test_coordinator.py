"""Controlled barriers prove coalescing, publication ordering and lifecycle ownership."""

import asyncio
from dataclasses import FrozenInstanceError

import pytest

from campervan.coordinator import Coordinator
from campervan.parameters import Parameters
from campervan.settings import Settings
from campervan.worker import GenerationError, PublicationError


class ControlledWorker:
    def __init__(self, parameters):
        self.parameters = parameters
        self.generated = asyncio.Event()
        self.publishing = asyncio.Event()
        self.finish = asyncio.Event()
        self.closed = asyncio.Event()
        self.closing = asyncio.Event()
        self.allow_close = asyncio.Event()
        self.allow_close.set()
        self.error = None
        self.publication_error = None

    async def wait_generated(self):
        await self.generated.wait()
        if self.error:
            raise self.error

    async def publish(self):
        self.publishing.set()
        await self.finish.wait()
        if self.publication_error:
            raise self.publication_error

    async def close(self):
        self.closing.set()
        await self.allow_close.wait()
        self.closed.set()


class Factory:
    def __init__(self):
        self.workers = asyncio.Queue()
        self.snapshots = []

    async def __call__(self, parameters, settings):
        worker = ControlledWorker(parameters)
        self.snapshots.append(parameters)
        await self.workers.put(worker)
        return worker

    async def next(self):
        return await asyncio.wait_for(self.workers.get(), 1)


async def completed(coordinator):
    # Queue a callback after the coordinator's current continuation, without a timing sleep.
    async with asyncio.timeout(5):
        while coordinator.status().state == "regenerating":
            barrier = asyncio.Event()
            asyncio.get_running_loop().call_soon(barrier.set)
            await barrier.wait()


def test_coalesces_and_never_authorizes_superseded_result():
    async def scenario():
        factory = Factory()
        coordinator = Coordinator(Settings(), factory)
        try:
            initial = coordinator.status()
            assert (initial.requested_revision, initial.published_revision, initial.state, initial.error) == (
                0,
                None,
                "idle",
                None,
            )
            with pytest.raises(FrozenInstanceError):
                initial.state = "ready"
            await coordinator.accept(Parameters(size_mm=101))
            first = await factory.next()
            await coordinator.accept(Parameters(size_mm=102))
            await coordinator.accept(Parameters(size_mm=103))
            first.generated.set()
            third = await factory.next()
            assert first.closed.is_set() and not first.publishing.is_set()
            assert [p.size_mm for p in factory.snapshots] == [101, 103]
            assert first.parameters.size_mm == 101
            third.generated.set()
            await asyncio.wait_for(third.publishing.wait(), 1)
            third.finish.set()
            await completed(coordinator)
            assert coordinator.status().published_revision == 3
            assert coordinator.status().state == "ready"
        finally:
            await coordinator.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("failure", [None, PublicationError("viewer timeout")])
def test_publication_holds_acceptance_gate_but_status_is_responsive(failure):
    async def scenario():
        factory = Factory()
        coordinator = Coordinator(Settings(), factory)
        try:
            await coordinator.accept()
            worker = await factory.next()
            worker.publication_error = failure
            worker.generated.set()
            await asyncio.wait_for(worker.publishing.wait(), 1)
            acceptance = asyncio.create_task(coordinator.accept(Parameters(size_mm=150)))
            barrier = asyncio.Event()
            asyncio.get_running_loop().call_soon(barrier.set)
            await barrier.wait()
            assert not acceptance.done()
            assert coordinator.status().requested_revision == 1
            assert coordinator.parameters.size_mm == 100
            worker.allow_close.clear()
            worker.finish.set()
            await asyncio.wait_for(worker.closing.wait(), 1)
            assert not acceptance.done()
            assert coordinator.status().requested_revision == 1
            worker.allow_close.set()
            assert await asyncio.wait_for(acceptance, 1) == 2
            assert coordinator.status().state == "regenerating"
            assert coordinator.status().error is None
            assert coordinator.status().published_revision == (1 if failure is None else None)
        finally:
            await coordinator.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("stage", ["generation", "publication"])
def test_failure_retains_published_revision_and_recovers(stage):
    async def scenario():
        factory = Factory()
        coordinator = Coordinator(Settings(), factory)
        try:
            await coordinator.accept()
            first = await factory.next()
            first.generated.set()
            first.finish.set()
            await completed(coordinator)
            await coordinator.accept()
            failed = await factory.next()
            if stage == "generation":
                failed.error = GenerationError("syntax error")
            else:
                failed.publication_error = PublicationError("timed out")
            failed.generated.set()
            failed.finish.set()
            await completed(coordinator)
            status = coordinator.status()
            assert status.state == "failed" and status.published_revision == 1
            assert status.error.stage == stage
            await coordinator.accept()
            recovered = await factory.next()
            recovered.generated.set()
            recovered.finish.set()
            await completed(coordinator)
            assert coordinator.status().published_revision == 3
            assert coordinator.status().error is None
        finally:
            await coordinator.close()

    asyncio.run(scenario())


def test_superseded_failure_does_not_replace_current_status_and_shutdown_closes_child():
    async def scenario():
        factory = Factory()
        coordinator = Coordinator(Settings(), factory)
        await coordinator.accept()
        first = await factory.next()
        await coordinator.accept(Parameters(size_mm=150))
        first.error = GenerationError("old failure")
        first.generated.set()
        current = await factory.next()
        assert coordinator.status().state == "regenerating"
        assert coordinator.status().error is None
        await coordinator.close()
        assert current.closed.is_set()
        with pytest.raises(RuntimeError):
            await coordinator.accept()

    asyncio.run(scenario())


def test_shutdown_retains_child_cleanup_through_repeated_cancellation():
    async def scenario():
        factory = Factory()
        coordinator = Coordinator(Settings(), factory)
        await coordinator.accept()
        worker = await factory.next()
        worker.allow_close.clear()
        close = asyncio.create_task(coordinator.close())
        try:
            await asyncio.wait_for(worker.closing.wait(), 1)
            for _ in range(3):
                close.cancel()
                barrier = asyncio.Event()
                asyncio.get_running_loop().call_soon(barrier.set)
                await barrier.wait()
                assert not close.done()
                assert not worker.closed.is_set()
            worker.allow_close.set()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(close, 1)
            assert worker.closed.is_set()
        finally:
            worker.allow_close.set()
            await asyncio.gather(close, return_exceptions=True)
            await coordinator.close()

    asyncio.run(scenario())


def test_worker_start_failure_is_generation_error_and_can_be_retried():
    async def scenario():
        factory = Factory()
        attempts = 0

        async def start(parameters, settings):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise OSError("spawn failed")
            return await factory(parameters, settings)

        coordinator = Coordinator(Settings(), start)
        try:
            await coordinator.accept()
            await completed(coordinator)
            assert coordinator.status().state == "failed"
            assert coordinator.status().error.stage == "generation"
            assert coordinator.status().error.message == "spawn failed"
            await coordinator.accept()
            worker = await factory.next()
            worker.generated.set()
            worker.finish.set()
            await completed(coordinator)
            assert coordinator.status().state == "ready"
        finally:
            await coordinator.close()

    asyncio.run(scenario())
