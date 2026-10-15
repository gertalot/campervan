"""Run CAD in a fresh Python process so source edits take effect."""

import asyncio
import json
import sys
from contextlib import redirect_stdout
from dataclasses import asdict

from campervan.parameters import Parameters
from campervan.settings import Settings


async def regenerate_model(parameters: Parameters, settings: Settings) -> list[str]:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "campervan.worker",
        parameters.model_dump_json(),
        json.dumps(asdict(settings)),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await process.communicate()
        if stderr:
            print(stderr.decode(errors="replace"), file=sys.stderr, end="")
        if process.returncode:
            message = stderr.decode(errors="replace").strip()
            raise RuntimeError(message.splitlines()[-1] if message else "CAD process failed")
        return list(json.loads(stdout))
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


if __name__ == "__main__":
    # Keep library diagnostics in the server log; stdout carries the published paths.
    with redirect_stdout(sys.stderr):
        from campervan.cad.model import build_campervan
        from campervan.viewer import publish_model

        parameters = Parameters.model_validate_json(sys.argv[1])
        settings = Settings(**json.loads(sys.argv[2]))
        paths = publish_model(build_campervan(parameters), settings, parameters)
    print(json.dumps(paths))
