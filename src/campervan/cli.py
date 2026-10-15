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
    serve = commands.add_parser("serve", help="Run one production API worker")
    serve.add_argument("--host")
    serve.add_argument("--port", type=_port)
    args = parser.parse_args()
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
