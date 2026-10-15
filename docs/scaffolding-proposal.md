# Campervan CAD scaffolding proposal

A local, parametric campervan CAD application built with Python and build123d, with an interactive OCP viewer.

**Status: scaffolding proposal.** This repository currently contains design documentation and the original
FeatureScript.
The Python package, frontend, Make targets, lockfiles and commands described below are proposed; they do not exist yet.
No dependencies or services were installed or started while preparing this proposal.

Read [the architecture](ARCHTECTURE.md) for application requirements and
[the existing model](what-we-built-in-onshape.md) for migration constraints. Keep the current FeatureScript in
`docs/fs/` and historical files in `docs/fs-archive/`.

## Recommended toolchain

| Responsibility | Choice | Reason |
|---|---|---|
| Python | Standard CPython 3.13 | Supported by the CAD dependencies; validate during setup |
| Environment and dependencies | uv, project-local `.venv`, committed `uv.lock` | One workflow for installation, locking and execution |
| Python packaging | `uv_build`, `src/` layout | Build a wheel containing Python code and web assets |
| CAD | build123d | Required by the architecture |
| Viewer | Standalone `ocp-viewer` | Maintainer-provided browser UI and Python publishing API |
| Backend, Phase B | FastAPI, Pydantic, Uvicorn | API, parameter validation and application serving |
| Frontend, Phase B | Vite, plain TypeScript and CSS | Development reload and production assets without a UI framework |
| Frontend tooling | Node.js 24 LTS, npm, committed `package-lock.json` | Standard tooling for one frontend package |
| Python checks | pytest, Ruff, mypy | Behaviour tests, formatting/linting and application type checks |
| Frontend checks, Phase B | TypeScript compiler, Vitest | Type checks and focused UI logic tests |
| Task shortcuts | Makefile | Short commands delegating to uv and npm |

Choose uv over Poetry here because there is no existing Poetry configuration to preserve and uv covers the environment,
lockfile, execution and packaging workflow. Plain `venv` plus pip would need additional conventions for locking and
upgrades. Use one Python dependency workflow throughout the project.

Vite adds Node during development and builds. That cost buys standard frontend reload and bundling instead of a custom
asset watcher. The installed production application needs Python and its dependencies; it serves already-built assets.
The standalone viewer already bundles its own frontend and does not require Node.

Node.js 24 is an LTS release; see the [official release table](https://nodejs.org/en/about/previous-releases).

Current dependency candidates are `build123d==0.13.0` and `ocp-viewer==1.2.0`. Their published metadata
supports this Python choice. Resolve and smoke-test them together before accepting the lockfile. Let build123d
select its compatible OpenCascade dependency rather than adding a separate kernel pin.
See [build123d metadata](https://pypi.org/project/build123d/),
[kernel wheels](https://pypi.org/project/cadquery-ocp-novtk/) and
[viewer installation](https://bernhard-42.github.io/ocp_viewer_docs/viewers/ocp_viewer/installation/).

Use `.python-version` containing `3.13` and `requires-python = ">=3.13,<3.14"` initially. Record the tested patch
version
when creating the scaffold. Configure uv to use the installed interpreter, with `python-preference = "only-system"`
and `python-downloads = "never"`. Setup should fail with a useful message if that interpreter is unavailable.
See [uv interpreter settings](https://docs.astral.sh/uv/reference/settings/#python-downloads).

Put Python tool configuration in `pyproject.toml`, including a 120-character Ruff line length. Pin the tested build
backend version in `[build-system]`; application dependency locking does not replace build-backend version control.
Use `uv_build` with `module-name = "campervan"` for the distribution named `campervan-cad`.
See [uv packaging](https://docs.astral.sh/uv/concepts/build-backend/).

## Implementation sequence

Start with **Phase A only**, as required by the architecture:

1. Add the Python package, uv configuration, lockfile, Makefile and focused checks.
2. Build a small named assembly with a dimensional parameter, separate parts and a moving component.
3. Publish it to a viewer started by the developer.
4. Change a dimension and rerun; verify the existing viewer updates and retains its camera.
5. Introduce a controlled build failure and verify the previous model remains visible.
6. Verify STEP output and installation of the wheel outside the source directory.

After that works, Phase B adds FastAPI, the execution coordinator, Vite and the parameter UI. The development and
production application commands below describe that target. Do not create empty modules for the full campervan,
manufacturing outputs or future API routes during Phase A.

## Proposed layout

```text
README.md
pyproject.toml
uv.lock
.python-version
.gitignore
Makefile
src/campervan/
    __init__.py
    cli.py                      # Explicit model commands; serving added in Phase B
    parameters.py
    components.py
    cad/
        assembly.py             # Initial test assembly, then incremental migration
    services/
        viewer.py               # Adapter using the supported OCP Python API
        exports.py
        model_runner.py         # Phase B: one build coordinator
    api/                        # Phase B
    app.py                      # Phase B
    web/                        # Phase B: generated assets included in the wheel
    defaults/                   # Packaged defaults/presets when introduced
frontend/                       # Phase B
    package.json
    package-lock.json
    vite.config.ts
    tsconfig.json
    index.html
    src/
tests/
    unit/
    geometry/
    integration/
docs/                           # Existing documentation and FeatureScript
```

Keep editable configuration, generated CAD files and runtime status outside the installed package. Use `./var/` as the
default local data directory, overridable by `--data-dir`; production examples use `./var-production/`. Ship immutable
default presets as package resources and copy them on first use without overwriting existing user configurations.

Ignore `.venv/`, `.venv-prod/`, `node_modules/`, generated `web/`, `dist/`, runtime directories and tool caches. Track
source,
defaults and both lockfiles. Use command options or ordinary environment variables for runtime settings.

## Set up development

These commands become available after the corresponding scaffold phase. Assume Python 3.13 is installed.
Install uv if needed; Node.js 24 and npm are needed only from Phase B onward.

```sh
# Phase A: create/synchronise .venv from the committed lockfile
uv sync --locked

# Phase B: install frontend dependencies from its committed lockfile
npm --prefix frontend ci
```

Use `uv run --locked ...` for project Python commands. Activating `.venv` is optional. The `--locked` flag reports a
stale
lockfile instead of changing it during routine development. See [uv locking](https://docs.astral.sh/uv/concepts/projects/sync/).

Proposed `make setup` wraps these commands for the implemented phase. Developers changing dependencies use `uv add`,
`uv add --dev`, or npm and review the resulting manifest and lockfile changes together.

## Run the Phase A prototype

Start the viewer in one terminal:

```sh
uv run --locked python -m ocp_viewer --host 127.0.0.1 --port 3939
```

In another terminal, use the proposed project command:

```sh
uv run --locked campervan model --publish
```

Open `http://127.0.0.1:3939`. The model command constructs and validates the entire assembly before publishing it.
Configure the Python client to use port 3939 explicitly. On subsequent updates use the documented `Camera.KEEP` option.
Camera retention across geometry updates still requires a local smoke test; it does not imply retention across a browser
or viewer restart. See [viewer camera behaviour](https://bernhard-42.github.io/ocp_viewer_docs/reset_camera/).

Proposed shortcuts are `make viewer` and `make model`. Running either command must not silently start another service.

## Develop with reload, Phase B

Use three terminals so each service has visible logs and an explicit lifecycle:

```sh
# Terminal 1: persistent OCP viewer
make viewer

# Terminal 2: FastAPI with API reload and CAD source watching
make dev-api

# Terminal 3: Vite development server
make dev-ui
```

| Service | Address | Behaviour |
|---|---|---|
| Application UI | `http://127.0.0.1:5173` | Vite reload; `/api` requests proxy to FastAPI |
| FastAPI | `http://127.0.0.1:8000` | API and schema edits restart the API process |
| OCP viewer | `http://127.0.0.1:3939` | Embedded iframe; receives successful geometry updates |

Bind all services to loopback and fail on an occupied port. Keep ports configurable but explicit. Test iframe embedding
and the viewer WebSocket during Phase B. The API returns parameter metadata so the UI does not duplicate defaults or
validation bounds.

The proposed `dev-api` command wraps `uv run --locked campervan serve --reload --watch-model`. Its implementation uses
Uvicorn reload for application code, excludes `cad/` from API restarts, and uses a debounced `watchfiles` watcher for
CAD
changes. Each build runs in a fresh subprocess using the environment's interpreter, avoiding stale Python imports.
An explicit `campervan rebuild` command sends a rebuild request to the running API and waits for the outcome.

Use one coordinator for UI edits, source watching and explicit rebuild requests. It permits one active CAD build and
coalesces pending requests to the latest revision. A superseded build cannot publish. Stage outputs before acceptance;
only an accepted successful result may replace the published model and its matching metadata/exports. On API shutdown,
stop and reap its build child so a prior API process cannot publish a late result.

The Phase A direct publisher remains a standalone diagnostic path; do not run it concurrently with the application's
coordinator against the same viewer. Headless geometry/export operations can run separately without publishing.

CAD edits update geometry without refreshing the browser. Vite provides CSS/module updates where supported and page
reloads for changes that require them; a page reload may reset viewer state. API errors should appear in the status
panel
while the last successful geometry remains visible. Viewer unavailability should produce a retryable publication error.
See [Uvicorn reload settings](https://uvicorn.dev/settings/) and [Vite](https://vite.dev/guide/).

Stop each terminal with Ctrl-C. The viewer remains running while restarting the API or UI.

## Test and check

Proposed commands:

```sh
make check       # Ruff check, Ruff format --check, mypy; Phase B also TypeScript checks
make test        # pytest unit, CAD geometry and in-process API/worker integration tests
make test-ui     # Phase B: Vitest tests for parameter controls and request handling
make format      # Apply Python formatting
```

`make test` must not require a running viewer or network services. Mock the viewer adapter, not the CAD kernel in
geometry
tests. Cover valid solids, dimensions, volumes, part identities, placement, invalid parameters, child-process failures,
superseded requests and preservation of the last successful outputs. Use explicit millimetre tolerances rather than
byte-for-byte CAD export comparisons.

In Phase B, test API routes in-process and test schema-driven form logic and debouncing in Vitest. Keep CAD-heavy tests
serial initially. Scope mypy to our code and confine third-party typing exceptions to the integration boundary.

Provide a separate, explicit viewer smoke-test procedure against a viewer the developer has already started. It must
cover initial publication, an update, camera retention, failure recovery and embedding. After packaging, verify
installed
resources and headless model execution from a temporary working directory, not only through the editable source tree.

## Build the application

Distinguish packaging from CAD generation:

```sh
make build       # Build the distributable Python application
make model       # Generate CAD geometry; Phase B delegates publication to the running API
```

In Phase A, `make build` runs `uv build`. In Phase B it first runs frontend type checks and `npm --prefix frontend run
build`,
writing assets into `src/campervan/web/`, then runs `uv build`. The wheel and source distribution go into `dist/`.
The build must include the generated assets and packaged defaults, and fail if expected frontend assets are missing.
Pin the build backend and frontend tooling; verify that a wheel rebuilt from the source distribution contains the
assets.

## Run in production mode, Phase B

Production here means a local application installed without editable source links or reload watchers. Use a separate
environment so installation does not disturb development. The proposed `make install-prod` performs:

1. `make check`, `make test`, `make test-ui` and `make build`.
2. Export locked runtime requirements, excluding the project itself and development dependencies.
3. Create `.venv-prod` using installed Python 3.13 and synchronise those locked requirements.
4. Install the specific wheel just built, with dependency resolution disabled.
5. Verify the installed package and its web assets outside the source directory.

Select the exact newly built wheel rather than a wildcard that could pick an old release. Record its filename and hash.
The Python wheel contains our application; the separately locked runtime dependencies include native CAD libraries.

Then start the services in separate terminals:

```sh
# Terminal 1
.venv-prod/bin/python -m ocp_viewer --host 127.0.0.1 --port 3939

# Terminal 2: proposed application entry point
.venv-prod/bin/campervan serve --host 127.0.0.1 --port 8000 --data-dir ./var-production
```

Open `http://127.0.0.1:8000`. FastAPI serves both `/api` and the packaged UI. The viewer remains on port 3939. Run one
API
worker because it owns the model coordinator. Parameter edits still regenerate models; source edits require a new build
and installation. Do not use `uv run` to launch production, as it may select or resynchronise the development
environment.

The developer starts and stops these services. Background launch-at-login management is outside the initial scaffold.

## Migration and unresolved checks

Preserve millimetres and the existing model axes initially: X across the van, Y rear-to-cab, Z upwards. The
architecture's
suggested X/Y convention differs; changing it requires an explicit transform. Use the documented current model values,
not the architecture's illustrative dimensions. Resolve the saved cabinet height before selecting the displayed
baseline.

Before treating this proposal as operational documentation, verify dependency resolution, native imports, packaged
assets, viewer publication, camera retention and iframe behaviour in the development environment. Metadata research supports the
toolchain choice, but does not substitute for those checks. Replace this proposal banner with the implemented phase and
tested commands as the scaffold lands.
