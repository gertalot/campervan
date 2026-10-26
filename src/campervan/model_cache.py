"""One saved CAD result: display messages, exact measurement geometry and cuts."""

import hashlib
import json
import logging
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from campervan.materials import CutPart
from campervan.parameters import Parameters

logger = logging.getLogger(__name__)


class ModelBundle(BaseModel):
    version: Literal[1] = 1
    fingerprint: str
    libraries: dict[str, str]
    frames: list[tuple[Literal["B", "D", "S"], str]]
    cuts: list[CutPart]


def library_versions() -> dict[str, str]:
    return {
        name: version(name)
        for name in (
            "build123d",
            "cadquery-ocp-novtk",
            "cadquery-ocp-proxy",
            "ocp-tessellate",
            "ocp-viewer",
            "ocp-viewer-core",
        )
    }


def model_fingerprint(parameters: Parameters) -> str:
    """Live poses are replayed relative to the bundle's recorded construction pose."""
    dimensions = {
        name: value
        for name, value in parameters.model_dump().items()
        if not isinstance(extra := Parameters.model_fields[name].json_schema_extra, dict)
        or extra.get("control") != "position"
    }
    digest = hashlib.sha256(json.dumps(dimensions, sort_keys=True).encode())
    package = Path(__file__).resolve().parent
    sources = sorted((package / "cad").glob("*.py"))
    sources += [package / name for name in ("parameters.py", "materials.py", "viewer.py", "worker.py", "model_cache.py")]
    for path in sources:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    # Include installed versions as well as source: this also works from a built wheel.
    digest.update(json.dumps(library_versions(), sort_keys=True).encode())
    return digest.hexdigest()


def read_bundle(path: Path) -> ModelBundle | None:
    if not path.exists():
        return None
    try:
        bundle = ModelBundle.model_validate_json(path.read_bytes())
        if bundle.libraries != library_versions():
            raise ValueError("Saved model uses different CAD/viewer library versions")
        if not any(kind == "B" for kind, _ in bundle.frames) or not any(kind == "D" for kind, _ in bundle.frames):
            raise ValueError("Model bundle is missing geometry or measurement data")
        for _, payload in bundle.frames:
            json.loads(payload)
        return bundle
    except (OSError, ValueError) as error:
        logger.warning("Saved CAD model could not be loaded; it will be rebuilt: %s", error)
        return None


def save_bundle(path: Path, bundle: ModelBundle) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(bundle.model_dump_json())
    temporary.replace(path)
