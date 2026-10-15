# Campervan CAD

Design a campervan interior with parametric Python models and inspect it in a local, interactive 3D viewer.
The application uses build123d for geometry and a browser interface for dimensions and configurations.
This is a personal, local-only hobby project.

## Prerequisites

- Python 3.13.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Node.js 22.12+ and npm, for developing and building the web interface.
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

The page automatically regenerates the model on opening. Change **Cube size** and click **Apply** to regenerate it.
Use **Regenerate** to retry after an error.
Regeneration refits the model with space around it.

Edit CAD models in `src/campervan/cad/` and the web interface in `frontend/src/`. Saving CAD changes regenerates the
model with the selected parameters. Backend changes reload the API, reset parameters to defaults and automatically
regenerate. Frontend changes trigger Vite updates or a page reload. Parameters are kept in memory only.
Failed regeneration displays an error and leaves the last successful model visible.

Press Ctrl-C in each terminal to stop.

Server output also goes to `logs/api.log`, `logs/ui.log` and `logs/viewer.log`. Each launch replaces its log.
For example, inspect backend errors with `tail -n 80 logs/api.log`.

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

## Check and test

```sh
make check       # Formatting, lint and type checks
make test        # Minimal Python and frontend smoke tests
```

These commands do not require running services. Apply Python formatting with `make format`.
The main validation is inspecting the model in the viewer and trying the changes you're working on.
Automated tests provide a small sanity check of the plumbing and cube geometry.

## Build and run without hot reload

```sh
make build
```

This compiles the web interface and packages the Python application into `dist/`. It does not generate CAD geometry.
To run the built interface locally, start these commands in separate terminals:

```sh
make viewer
```

```sh
make serve
```

Open **http://127.0.0.1:8000**. Vite is not needed in this mode. Parameter changes still regenerate the model.
After changing source code, stop the application, run `make build` again and restart it with `make serve`.

## Troubleshooting

- **Blank viewer:** check that the viewer terminal is running and open http://127.0.0.1:3939/viewer directly.
- **Regeneration failed:** read the error in the application and backend terminal, correct the model, then click **Regenerate**.
- **Port already in use:** stop the previous instance you started before launching another.
- **Dependency or interpreter error:** check that Python 3.13 is available, then rerun `make setup`.

## Project documentation

- [Existing campervan design](docs/what-we-built-in-onshape.md)
- [Application architecture](docs/ARCHTECTURE.md)
- [Scaffolding proposal](docs/scaffolding-proposal.md)
- [Current FeatureScript](docs/fs/nv200-interior.fs)
