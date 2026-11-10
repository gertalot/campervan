"""Publish CAD geometry before extracting cuts from the same model in a fresh process."""

import asyncio
import json
import sys
from collections.abc import AsyncGenerator
from contextlib import aclosing
from pathlib import Path
from tempfile import TemporaryDirectory

from campervan.model_cache import ModelBundle
from campervan.parameters import Parameters


async def model_updates(parameters: Parameters) -> AsyncGenerator[ModelBundle]:
    with TemporaryDirectory(prefix="campervan-model-") as directory:
        output = Path(directory)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "campervan.worker",
            parameters.model_dump_json(),
            str(output),
            stdout=asyncio.subprocess.PIPE,
        )
        try:
            assert process.stdout is not None
            bundle = None
            async for line in process.stdout:
                event = json.loads(line)
                if error := event.get("error"):
                    raise RuntimeError(error)
                if event["stage"] == "model":
                    bundle = ModelBundle.model_validate_json((output / "model.json").read_bytes())
                else:
                    if bundle is None:
                        raise RuntimeError("CAD worker returned cuts before geometry")
                    bundle = ModelBundle.model_validate(
                        bundle.model_dump()
                        | {
                            "cuts": json.loads((output / "cuts.json").read_bytes()),
                        }
                    )
                yield bundle
            await process.wait()
            if process.returncode:
                raise RuntimeError("CAD process failed. See the API log.")
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()


async def regenerate_model(parameters: Parameters) -> ModelBundle:
    """Offline exports require both geometry and cutting outlines."""
    async with aclosing(model_updates(parameters)) as updates:
        async for bundle in updates:
            if bundle.cuts is not None:
                return bundle
    raise RuntimeError("CAD process did not return a complete model")


if __name__ == "__main__":
    import os
    import traceback
    from contextlib import redirect_stdout

    def publish(event: dict[str, str]) -> None:
        print(json.dumps(event), flush=True)

    try:
        # Keep stdout exclusively for completion events; CAD progress belongs in the API log.
        with redirect_stdout(sys.stderr):
            from campervan.model_cache import library_versions, model_fingerprint
            from campervan.viewer import build_viewer_frames

            parameters = Parameters.model_validate_json(sys.argv[1])
            output = Path(sys.argv[2])
            fingerprint = model_fingerprint(parameters)
            from campervan.cad.bom import cut_list
            from campervan.cad.model import build_campervan

            model = build_campervan(parameters)
            bundle = ModelBundle(
                fingerprint=fingerprint,
                libraries=library_versions(),
                frames=build_viewer_frames(model, parameters),
            )
            (output / "model.json").write_text(bundle.model_dump_json())
        publish({"stage": "model"})
        # The viewer can now publish independently while this process extracts manufacturing data.
        os.nice(10)
        with redirect_stdout(sys.stderr):
            cuts = cut_list(model, parameters)
            (output / "cuts.json").write_text(json.dumps([cut.model_dump() for cut in cuts]))
        publish({"stage": "cuts"})
    except Exception as error:
        traceback.print_exc()
        publish({"error": str(error)})
        sys.exit(1)
