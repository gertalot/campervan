"""Stream improving layouts from a background solver process owned by the coordinator."""

import asyncio
import json
import os
import signal
import sys
import traceback
from collections.abc import AsyncIterator

from campervan.cutting_models import CuttingOptions

CPU_PERIOD = 0.2
CPU_RUN_FRACTION = 0.5


async def _share_cpu(process: asyncio.subprocess.Process) -> None:
    """Pause all solver threads for half of each shared wall-clock period.

    Align material searches to the same clock so simultaneous searches still leave
    half the time free. A lower process priority alone would keep idle CPUs busy.
    """
    loop = asyncio.get_running_loop()
    while process.returncode is None:
        phase = loop.time() % CPU_PERIOD
        running = phase < CPU_PERIOD * CPU_RUN_FRACTION
        try:
            process.send_signal(signal.SIGCONT if running else signal.SIGSTOP)
        except ProcessLookupError:
            return
        boundary = CPU_PERIOD * CPU_RUN_FRACTION if running else CPU_PERIOD
        await asyncio.sleep(boundary - phase)


async def solve_layout(payload: dict) -> AsyncIterator[dict]:
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "campervan.cutting_worker",
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        limit=1024 * 1024,
    )
    try:
        async with asyncio.TaskGroup() as tasks:
            throttle = tasks.create_task(_share_cpu(process))
            assert process.stdin is not None and process.stdout is not None
            process.stdin.write(json.dumps(payload).encode())
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
