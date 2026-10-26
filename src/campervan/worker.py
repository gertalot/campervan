"""Construct a complete model bundle in a fresh process so CAD source edits take effect."""

import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from campervan.model_cache import ModelBundle
from campervan.parameters import Parameters


async def regenerate_model(parameters: Parameters) -> ModelBundle:
    with TemporaryDirectory(prefix="campervan-model-") as directory:
        return await _regenerate(parameters, Path(directory) / "model.json")


async def _regenerate(parameters: Parameters, output: Path) -> ModelBundle:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "campervan.worker",
        parameters.model_dump_json(),
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
        return ModelBundle.model_validate_json(output.read_bytes())
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


if __name__ == "__main__":
    from campervan.model_cache import library_versions, model_fingerprint
    from campervan.viewer import build_viewer_frames

    parameters = Parameters.model_validate_json(sys.argv[1])
    # Hash before construction: an edit during the build must not give old geometry a new fingerprint.
    fingerprint = model_fingerprint(parameters)
    from campervan.cad.bom import cut_list
    from campervan.cad.model import build_campervan

    model = build_campervan(parameters)
    bundle = ModelBundle(
        fingerprint=fingerprint,
        libraries=library_versions(),
        frames=build_viewer_frames(model, parameters),
        cuts=cut_list(model, parameters),
    )
    Path(sys.argv[2]).write_text(bundle.model_dump_json())
