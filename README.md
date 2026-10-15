# Campervan CAD

Design a campervan interior with parametric Python models and inspect it in a local, interactive 3D viewer.
The application uses build123d for geometry and a browser interface for dimensions and configurations.

## Prerequisites

- Python 3.13.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Node.js 24 LTS and npm, for developing and building the web interface.
- `make`.

## Set up

From the project directory:

```sh
make setup
```

This installs the locked Python dependencies into `.venv` and the frontend dependencies into `frontend/node_modules`.
You do not need to activate the virtual environment. Run Python commands through `uv run --locked`.

## Develop with hot reload

Run each command in its own terminal, from the project directory:

```sh
# Terminal 1: 3D viewer
make viewer
```

```sh
# Terminal 2: backend and CAD source watcher
make dev-api
```

```sh
# Terminal 3: web interface
make dev-ui
```

```sh
# Terminal 4: Chrome DevTools
make chrome
```

Open **http://127.0.0.1:5173**.

Edit CAD models in `src/campervan/cad/` and the web interface in `frontend/src/`. Saving CAD changes rebuilds the model
and updates the viewer. Backend changes reload the API; frontend changes trigger Vite updates or a page reload.
Failed CAD builds display an error and leave the last successful model visible.

## Chrome and DevTools MCP

Launch a separate Chrome instance for this project:

```sh
make chrome
```

Chrome exposes remote debugging at `http://127.0.0.1:9223` and stores its profile in
`~/.config/chrome-devtools-campervan`. It can run alongside Qrtr's Chrome on port `9222` with its own profile.
The command runs in the foreground; open the application URL in this Chrome instance once your services are running.
If Chrome is installed in a nonstandard location, use `CHROME_BIN=/path/to/chrome make chrome`.

The project-local `.codex/config.toml` configures Chrome DevTools MCP to connect to port `9223`.
It uses `npx` to install and run `chrome-devtools-mcp@1.10.1` without a global npm installation.
Trust this project in Codex and restart the Codex session after adding the configuration so it loads the project override.
Start Chrome with `make chrome` before using the MCP's browser tools.

## Test

```sh
make check       # Formatting, lint and type checks
make test        # Python, geometry and API tests
make test-ui     # Frontend tests
```

These checks do not require running services. To run only the Python unit tests:

```sh
uv run --locked pytest tests/unit/
```

Apply Python formatting with `make format`.

## Build

```sh
make build
```

This builds the web interface and packages it with the Python application. The wheel and source distribution appear
in `dist/`. Building the application does not start services or generate the campervan geometry.

## Run in production mode

Build, check and install the application into a separate `.venv-prod` environment:

```sh
make install-prod
```

Then start the viewer and application in separate terminals:

```sh
# Terminal 1
.venv-prod/bin/python -m ocp_viewer --host 127.0.0.1 --port 3939
```

```sh
# Terminal 2
.venv-prod/bin/campervan serve --host 127.0.0.1 --port 8000 --data-dir ./var-production
```

Open **http://127.0.0.1:8000**.

Production mode serves the built web interface without development servers or source watchers. Parameter changes still
rebuild the model. To apply source changes, stop the services, rerun `make install-prod`, and start them again.
Your saved configurations and generated files live in `var-production/`, outside the installation.

Press Ctrl-C in each terminal to stop. Use the `.venv-prod/bin/` commands above for production; `uv run` uses the
development environment.

## Troubleshooting

- **Blank viewer:** check that the viewer terminal is running and open http://127.0.0.1:3939 directly.
- **Build failed:** read the error in the application and backend terminal, correct the model, then run `make model`.
- **Port already in use:** stop the previous instance you started before launching another.
- **Dependency or interpreter error:** check that Python 3.13 is available, then rerun `make setup`.

## Project documentation

- [Existing campervan design](docs/what-we-built-in-onshape.md)
- [Application architecture](docs/ARCHTECTURE.md)
- [Scaffolding proposal](docs/scaffolding-proposal.md)
- [Current FeatureScript](docs/fs/nv200-interior.fs)
