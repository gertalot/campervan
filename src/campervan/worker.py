"""Run CAD in a fresh Python process so source edits take effect."""

import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from campervan.materials import CutPart
from campervan.parameters import Parameters
from campervan.settings import Settings


async def regenerate_model(parameters: Parameters, settings: Settings) -> list[CutPart]:
    with TemporaryDirectory(prefix="campervan-bom-") as directory:
        return await _regenerate(parameters, settings, Path(directory) / "bom.json")


async def _regenerate(parameters: Parameters, settings: Settings, output: Path) -> list[CutPart]:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "campervan.worker",
        parameters.model_dump_json(),
        json.dumps(asdict(settings)),
        str(output),
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await process.communicate()
        if stderr:
            print(stderr.decode(errors="replace"), file=sys.stderr, end="")
        if process.returncode:
            message = stderr.decode(errors="replace").strip()
            raise RuntimeError(message.splitlines()[-1] if message else "CAD process failed")
        return [CutPart.model_validate(item) for item in json.loads(output.read_text())]
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


if __name__ == "__main__":
    from campervan.cad.bom import cut_list
    from campervan.cad.model import build_campervan
    from campervan.viewer import publish_model

    parameters = Parameters.model_validate_json(sys.argv[1])
    settings = Settings(**json.loads(sys.argv[2]))
    model = build_campervan(parameters)
    cuts = cut_list(model, parameters)
    publish_model(model, settings, parameters)
    Path(sys.argv[3]).write_text(json.dumps([cut.model_dump() for cut in cuts]))
