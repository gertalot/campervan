"""Foreground service entrypoints with settings resolved in Python."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from campervan.settings import load_settings


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer from 1 to 65535") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be an integer from 1 to 65535")
    return port


def _foreground(command: list[str], env: dict[str, str] | None = None) -> None:
    try:
        result = subprocess.run(command, env=env, check=False)
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    raise SystemExit(result.returncode if result.returncode >= 0 else 128 - result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(prog="campervan")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("viewer", help="Run the standalone OCP viewer")
    commands.add_parser("dev-api", help="Run the development API and CAD watcher")
    commands.add_parser("dev-ui", help="Run the Vite development UI")
    commands.add_parser("site", help="Export the saved project to site/ for static hosting")
    scan = commands.add_parser("scan", help="Process RTAB-Map captures offline")
    scan_commands = scan.add_subparsers(dest="scan_command", required=True)
    process = scan_commands.add_parser("process", help="Fuse RGB-D captures into a mesh and textures")
    process.add_argument("inputs", nargs="+", type=Path)
    process.add_argument("--output", required=True, type=Path)
    process.add_argument("--poses", type=Path, help="External camera-to-world poses.json, in metres")
    process.add_argument(
        "--measurements", type=Path, help="Associate the capture with this physical tag-layout document"
    )
    process.add_argument(
        "--alignment", type=Path, help="Explicit tag-to-axis definition; omitted leaves scan coordinates"
    )
    process.add_argument("--voxel-mm", type=float, default=5)
    process.add_argument("--sdf-trunc-mm", type=float, default=25)
    process.add_argument("--depth-max-m", type=float, default=4)
    process.add_argument("--depth-confidence-min", type=int, default=50)
    process.add_argument("--min-component-triangles", type=int, default=200)
    process.add_argument("--target-triangles", type=int, default=500000)
    process.add_argument("--texture-size", type=int, default=4096)
    process.add_argument("--uv-partitions", type=int, default=4)
    process.add_argument("--tag-family", choices=["36h11"])
    process.add_argument("--tag-size-mm", type=float)
    process.add_argument("--texture-mode", choices=["baked", "photo"], default="baked")
    photographic = scan_commands.add_parser("reconstruct", help="Reconstruct photographic cameras, dense geometry and texture")
    photographic.add_argument("--request", required=True, type=Path, help="JSON containing an immutable photographic request")
    photographic.add_argument("--output", required=True, type=Path)
    align = scan_commands.add_parser("align", help="Set vehicle axes on completed runs without rebuilding geometry")
    align.add_argument("runs", nargs="+", type=Path)
    align.add_argument("--alignment", type=Path, required=True)
    align.add_argument("--measurements", type=Path, help="Associate the capture with this physical tag-layout document")
    serve = commands.add_parser("serve", help="Run the built local application without hot reload")
    serve.add_argument("--host")
    serve.add_argument("--port", type=_port)
    args = parser.parse_args()
    if args.command == "scan":
        from campervan.scans import ScanSettings, process_scan

        try:
            if args.scan_command == "reconstruct":
                from campervan.scan_photogrammetry import process_photos
                from campervan.scans import read_json
                process_photos(read_json(args.request)["request"], args.output)
                return
            if args.scan_command == "align":
                from campervan.scan_alignment import align_run

                for run in args.runs:
                    result = align_run(run, args.alignment, args.measurements)
                    print(f"{run}: {result['status']}")
                    if result["status"] != "aligned":
                        raise ValueError(result["reason"])
                return
            scan_settings = ScanSettings(**{name: getattr(args, name) for name in ScanSettings.model_fields})
            process_scan(args.inputs, args.output, scan_settings, args.poses, args.alignment, args.measurements)
        except (OSError, ValueError, RuntimeError, ImportError, subprocess.CalledProcessError) as error:
            parser.exit(1, f"Scan processing failed: {error}\n")
        return
    if args.command == "site":
        import asyncio

        from campervan.site import export_site

        try:
            asyncio.run(export_site())
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
            parser.exit(1, f"Site export failed: {error}\n")
        return
    if args.command in {"dev-api", "serve"}:
        os.environ["CAMPERVAN_DEV"] = "1" if args.command == "dev-api" else "0"
    settings = load_settings()
    if args.command == "viewer":
        _foreground(
            [sys.executable, "-m", "ocp_viewer", "--host", settings.viewer_host, "--port", str(settings.viewer_port)]
        )
    elif args.command == "dev-ui":
        environment = dict(os.environ)
        environment.update(
            CAMPERVAN_API_TARGET=f"http://{settings.api_host}:{settings.api_port}",
            CAMPERVAN_UI_HOST=settings.ui_host,
            CAMPERVAN_UI_PORT=str(settings.ui_port),
        )
        _foreground(["npm", "--prefix", "frontend", "run", "dev"], environment)
    else:
        import uvicorn

        if args.command == "dev-api":
            package = Path(__file__).resolve().parent
            uvicorn.run(
                "campervan.api:create_app",
                factory=True,
                host=settings.api_host,
                port=settings.api_port,
                reload=True,
                reload_dirs=[str(package)],
                reload_excludes=[str(package / "cad")],
            )
        else:
            uvicorn.run(
                "campervan.api:create_app",
                factory=True,
                host=args.host or settings.api_host,
                port=args.port or settings.api_port,
                workers=1,
                reload=False,
            )


if __name__ == "__main__":
    main()
