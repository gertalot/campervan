"""Export the saved project as a portable, read-only static site."""

import json
import shutil
import subprocess
from datetime import UTC, datetime
from importlib.metadata import distribution
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from campervan.materials import load_project
from campervan.model_cache import model_fingerprint, read_bundle
from campervan.paths import MODEL_CACHE_PATH, PROJECT_PATH
from campervan.planning import parse_document
from campervan.purchases import purchase_view
from campervan.snapshot import cutting_data, material_data, parameter_response
from campervan.worker import regenerate_model


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def _copy_viewer_assets(output: Path) -> None:
    package = find_spec("ocp_viewer")
    if package is None or package.origin is None:
        raise ValueError("The OCP viewer is not installed. Run make setup first.")
    assets = Path(package.origin).parent / "server" / "static"
    target = output / "viewer-assets"
    shutil.copytree(assets, target)
    source = (assets / "js" / "three-cad-viewer.esm.js").read_text(encoding="utf-8")
    (target / "js" / "shared-renderer.js").write_text(
        source + "\nexport { THREE as sharedThree };\n", encoding="utf-8",
    )
    # Keep the redistributed viewer packages' licence text with their assets.
    for name in ("ocp-viewer", "ocp-viewer-core"):
        installed = distribution(name)
        for file in installed.files or ():
            if "/licenses/" in str(file):
                destination = target / "licenses" / name / Path(file).name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(installed.locate_file(file), destination)


async def export_site() -> None:
    """Build entirely offline; never connect to or start the local application."""
    root = Path.cwd()
    frontend = root / "frontend"
    if not (frontend / "node_modules" / ".bin" / "vite").is_file():
        raise ValueError("Run make site from the project directory after make setup.")
    project_path = root / PROJECT_PATH
    project = load_project(project_path)
    fingerprint = model_fingerprint(project.parameters)
    bundle = read_bundle(root / MODEL_CACHE_PATH)
    if bundle is None or bundle.fingerprint != fingerprint:
        print("Building the current CAD model for the static site…", flush=True)
        bundle = await regenerate_model(project.parameters)
        if bundle.fingerprint != fingerprint or model_fingerprint(project.parameters) != fingerprint:
            raise ValueError("CAD sources changed during export. Run make site again after saving your changes.")
    else:
        print("Using the saved CAD model.", flush=True)

    planning_path = project_path.with_name("planning.json")
    if planning_path.exists():
        planning = parse_document(json.loads(planning_path.read_text(encoding="utf-8")))
    else:
        from campervan.planning_migration import seed_v1

        planning = parse_document(seed_v1().model_dump())

    cutting = cutting_data(bundle.cuts, project.materials, project.cutting, {}, True)
    results = cutting["state"]["results"]
    for key, result in list(results.items()):
        group, _, mode = key.rpartition(":")
        if mode not in {"straight", "nesting"} or result.get("source") != cutting["sources"].get(group):
            del results[key]
            print(f"Warning: omitted an outdated cutting layout ({key}).", flush=True)
    for group in cutting["groups"]:
        key = f"{group['key']}:{project.cutting.settings.algorithm}"
        if key not in results:
            print(f"Warning: no current saved cutting layout for {group['name']}; its cut list is included.", flush=True)

    purchases = purchase_view(planning, project.materials, bundle.cuts)
    snapshot = {
        "exported_at": datetime.now(UTC).isoformat(),
        "parameters": parameter_response(f"static-{fingerprint[:16]}", project.parameters, "").model_dump(
            mode="json", by_alias=True,
        ),
        "materials": material_data(project.parameters, project.materials, bundle.cuts, 0, 0),
        "cutting": cutting,
        "planning": planning.model_dump(mode="json"),
        "purchases": purchases | {"filtered_totals": purchases["totals"]},
    }
    frames = [json.loads(payload) for kind, payload in bundle.frames if kind != "B"]
    # Finish in a temporary directory so a failed build leaves the previous export intact.
    with TemporaryDirectory(prefix=".campervan-site-", dir=root) as temporary:
        output = Path(temporary) / "site"
        subprocess.run(
            [str(frontend / "node_modules" / ".bin" / "vite"), "build", "--mode", "static",
             "--base", "./", "--outDir", str(output)],
            cwd=frontend, check=True,
        )
        _write_json(output / "snapshot.json", snapshot)
        _write_json(output / "viewer-frames.json", frames)
        _copy_viewer_assets(output)
        (output / ".nojekyll").touch()
        destination = root / "site"
        if destination.exists():
            shutil.rmtree(destination)
        output.replace(destination)
    print("Static site exported to site/. Upload that directory to your static host.")
