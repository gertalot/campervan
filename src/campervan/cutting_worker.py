"""Stream improving layouts from a background solver process owned by the coordinator."""

import asyncio
import json
import os
import signal
import sys
import traceback
from collections.abc import AsyncIterator, Callable

from campervan.cutting_models import CuttingOptions

CPU_PERIOD = 0.2
CPU_RUN_FRACTION = 0.5
SEARCH_SECONDS = 20


class LayoutSearch:
    """Retain a native search between bounded, CPU-throttled runs."""

    def __init__(self, payload: dict, on_pause: Callable[[], None]) -> None:
        self._payload = payload
        self._on_pause = on_pause
        self._process: asyncio.subprocess.Process | None = None
        self._running = asyncio.Event()
        self._deadline = 0.0

    def resume(self) -> None:
        self._deadline = asyncio.get_running_loop().time() + SEARCH_SECONDS
        self._running.set()

    def pause(self) -> None:
        self._running.clear()
        if self._process is not None and self._process.returncode is None:
            try:
                self._process.send_signal(signal.SIGSTOP)
            except ProcessLookupError:
                pass
        self._on_pause()

    async def _share_cpu(self, process: asyncio.subprocess.Process) -> None:
        """Share the existing duty cycle, then suspend until explicitly resumed."""
        loop = asyncio.get_running_loop()
        while process.returncode is None:
            await self._running.wait()
            remaining = self._deadline - loop.time()
            if remaining <= 0:
                self.pause()
                continue
            # Align material searches so they leave the same half of each period free.
            phase = loop.time() % CPU_PERIOD
            running = phase < CPU_PERIOD * CPU_RUN_FRACTION
            try:
                process.send_signal(signal.SIGCONT if running else signal.SIGSTOP)
            except ProcessLookupError:
                return
            boundary = CPU_PERIOD * CPU_RUN_FRACTION if running else CPU_PERIOD
            await asyncio.sleep(min(boundary - phase, remaining))

    async def updates(self) -> AsyncIterator[dict]:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "campervan.cutting_worker",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            limit=1024 * 1024,
        )
        self._process = process
        try:
            # A stop request can arrive while the subprocess is being created.
            if not self._running.is_set():
                self.pause()
            async with asyncio.TaskGroup() as tasks:
                throttle = tasks.create_task(self._share_cpu(process))
                assert process.stdin is not None and process.stdout is not None
                process.stdin.write(json.dumps(self._payload).encode())
                await process.stdin.drain()
                process.stdin.close()
                async for line in process.stdout:
                    yield json.loads(line)
                await process.wait()
                throttle.cancel()
            if process.returncode:
                raise RuntimeError("The cutting solver stopped with an error. See the API log.")
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()
            self._process = None


if __name__ == "__main__":
    os.nice(10)
    from campervan.cutting import layout

    def publish(value: dict) -> None:
        print(json.dumps(value), flush=True)

    try:
        payload = json.load(sys.stdin)
        result = layout(payload["group"], CuttingOptions.model_validate(payload["options"]), payload["mode"],
                        lambda result: publish({"result": result, "running": True}))
        publish({"result": result, "running": False})
    except Exception as error:
        traceback.print_exc()
        publish({"error": str(error), "running": False})
