"""Run CAD in a fresh Python process so source edits take effect."""

import asyncio
import json
import sys
from dataclasses import asdict

from campervan.parameters import Parameters
from campervan.settings import Settings


async def regenerate_model(parameters: Parameters, settings: Settings) -> None:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "campervan.worker",
        parameters.model_dump_json(),
        json.dumps(asdict(settings)),
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await process.communicate()
        if stderr:
            print(stderr.decode(errors="replace"), file=sys.stderr, end="")
        if process.returncode:
            message = stderr.decode(errors="replace").strip()
            raise RuntimeError(message.splitlines()[-1] if message else "CAD process failed")
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


if __name__ == "__main__":
    from campervan.cad.model import build_campervan
    from campervan.viewer import publish_model

    parameters = Parameters.model_validate_json(sys.argv[1])
    settings = Settings(**json.loads(sys.argv[2]))
    publish_model(build_campervan(parameters), settings)
