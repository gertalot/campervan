"""One fresh CAD child, with explicit parent authorization before publication."""

import asyncio
import multiprocessing
import traceback
from dataclasses import asdict
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Literal

from campervan.parameters import Parameters
from campervan.settings import Settings
from campervan.viewer import PublicationError

Stage = Literal["generation", "publication"]


class GenerationError(RuntimeError):
    """The child could not generate its requested model."""

    stage = "generation"


def worker_main(connection: Connection) -> None:
    """Hold geometry locally until authorized; EOF always abandons the result."""
    stage: Stage = "generation"
    try:
        request = connection.recv()
        if not isinstance(request, dict) or request.get("type") != "generate":
            raise GenerationError("Expected generate request")
        parameters = Parameters.model_validate(request["parameters"])
        settings = Settings(**request["settings"])
        # Keep imports in the guarded generation step so changed/broken CAD source
        # is loaded fresh and its import errors reach the parent's generation state.
        from campervan.cad.cube import make_cube

        cube = make_cube(parameters)
        connection.send({"type": "generated"})
        if connection.recv() != {"type": "publish"}:
            raise GenerationError("Expected publication authorization")
        stage = "publication"
        from campervan.viewer import publish_cube

        publish_cube(cube, settings)
        connection.send({"type": "published"})
    except (EOFError, BrokenPipeError):
        pass
    except Exception as error:
        traceback.print_exc()
        try:
            connection.send({"type": "error", "stage": stage, "message": str(error)})
        except (EOFError, OSError):
            pass
    finally:
        connection.close()


class Worker:
    """Own the child and pipe until they are closed and reaped."""

    def __init__(self, process: BaseProcess, connection: Connection, settings: Settings) -> None:
        self._process = process
        self._connection = connection
        self._settings = settings
        self._receives: list[asyncio.Task[object]] = []
        self._close_task: asyncio.Task[None] | None = None
        self._generated = False
        self._publication_started = False

    async def _receive(self, expected: str, stage: Stage) -> None:
        failure = GenerationError if stage == "generation" else PublicationError
        task = asyncio.create_task(asyncio.to_thread(self._connection.recv))
        self._receives.append(task)
        try:
            message = await asyncio.shield(task)
        except (EOFError, OSError) as error:
            raise failure(f"Child exited before {expected}") from error
        if isinstance(message, dict):
            if message == {"type": expected}:
                return
            if message.get("type") == "error" and message.get("stage") == stage:
                raise failure(str(message.get("message", "Child failed")))
        raise failure(f"Unexpected child message while waiting for {expected}")

    async def wait_generated(self) -> None:
        try:
            await self._receive("generated", "generation")
            self._generated = True
        except BaseException:
            await self.close()
            raise

    async def publish(self) -> None:
        if not self._generated or self._publication_started or self._close_task is not None:
            raise PublicationError("Worker is not awaiting publication authorization")
        self._publication_started = True
        try:
            self._connection.send({"type": "publish"})
            try:
                await asyncio.wait_for(
                    self._receive("published", "publication"), timeout=self._settings.publication_timeout_s
                )
            except TimeoutError as error:
                raise PublicationError("Viewer publication timed out") from error
            # Let a successful target exit normally before the final cleanup.
            await asyncio.to_thread(self._process.join, 2.0)
            if self._process.exitcode != 0:
                raise PublicationError("Child did not exit normally after publication")
        except (EOFError, OSError) as error:
            raise PublicationError("Child exited before publication completed") from error
        finally:
            await self.close()

    async def _close(self) -> None:
        try:
            if self._process.is_alive():
                self._process.terminate()
            await asyncio.to_thread(self._process.join, 2.0)
            if self._process.is_alive():
                self._process.kill()
                await asyncio.to_thread(self._process.join)
            # Reaping closes the last child endpoint and releases blocked recv.
            if self._receives:
                await asyncio.gather(*self._receives, return_exceptions=True)
        finally:
            self._connection.close()

    async def close(self) -> None:
        """Terminate/reap once and finish outstanding receives, including on cancellation."""
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._close())
        try:
            await asyncio.shield(self._close_task)
        except asyncio.CancelledError:
            await asyncio.shield(self._close_task)
            raise


async def start_worker(parameters: Parameters, settings: Settings) -> Worker:
    """Launch the fixed production target with JSON-like inputs and no CAD objects."""
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=True)
    process = context.Process(target=worker_main, args=(child,))
    try:
        process.start()
    except BaseException:
        parent.close()
        raise
    finally:
        child.close()
    worker = Worker(process, parent, settings)
    try:
        parent.send({"type": "generate", "parameters": parameters.model_dump(), "settings": asdict(settings)})
    except BaseException:
        await worker.close()
        raise
    return worker
