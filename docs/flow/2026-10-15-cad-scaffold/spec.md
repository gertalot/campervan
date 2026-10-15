# CAD application scaffold

Flow folder: [2026-10-15-cad-scaffold](./). Branch: `develop`.

## Outcome and authority

Install the build and development dependencies and provide a working FastAPI/Vite application displaying a build123d
cube through an embedded standalone OCP viewer. A size control must demonstrate the complete frontend-to-CAD update path.

This specification records the design approved in conversation. The user explicitly included the FastAPI/Vite servers,
the API/frontend integration, development and production tooling, and a correct `.gitignore`. The user approved the
parameter-update flow after asking how the web viewer loads geometry and communicates with the backend.

The [architecture](../../ARCHTECTURE.md) supplies the application boundaries; the approved scope includes its API and
frontend shell alongside the cube prototype. Its instruction to defer the application shell does not apply to this
user-approved scaffold. The [scaffolding proposal](../../scaffolding-proposal.md) is background, not additional scope.

Requirements below trace to these approved outcomes:

- **U1:** Build and development tools installed and usable.
- **U2:** A cube visible in the CAD viewer within our application frontend.
- **U3:** A frontend size control updates the model through FastAPI and Python.
- **U4:** Hot-reload development, production build/run, tests and a user-facing README.
- **U5:** Project-appropriate `.gitignore`.

## Scope

Implement one application package, one frontend, and one named cube. Include environment setup, dependency locks,
packaging, commands, focused tests, build status, validation/error display, and viewer integration needed for U1–U5.

Do not migrate the campervan, add presets, persist model parameters, implement moving assemblies, exports/BOM/cut lists,
introduce authentication or remote deployment, or replace the OCP renderer. Do not build generic job infrastructure.
The cube's dimensions are demonstration inputs, not campervan design decisions.

Keep all project choices independent of operating system and processor architecture. Verify on the available environment;
do not claim an unexecuted platform test matrix. No platform-specific installation paths belong in application code.

## Existing repository and reuse

Inspection at `99fd7ea` found documentation, FeatureScript references and historical JavaScript evaluator generators.
There is no application source, Python manifest, lockfile, frontend package, Makefile, test suite, CI or `.gitignore`.
There is no existing runtime mechanism to extend. The FeatureScript evaluators target Onshape and cannot provide the
local application/viewer transport. Preserve those references unchanged.

The installed tooling reports Python 3.13.5, uv 0.9.11, Node 22.23.3, npm 10.9.9 and GNU Make 3.81. The implementation must
use the installed Python. Node 22 meets Vite's documented 22.12+ requirement; avoid an unrelated global Node upgrade.
Update README prerequisites accordingly instead of requiring Node 24 solely because the earlier proposal named it.

## Toolchain and dependency ownership [U1, U4]

- Use CPython 3.13, `.python-version` containing `3.13`, and `requires-python = ">=3.13,<3.14"`.
- Use uv with `python-downloads = "never"` and `python-preference = "only-system"`. Create project-local `.venv`.
- Declare Python dependencies and tool settings in `pyproject.toml`; commit `uv.lock`. Routine commands use `--locked`.
- Use a tested, exactly pinned `uv_build` backend, distribution `campervan-cad`, module `campervan`, and `src/` layout.
- Runtime dependencies: build123d, ocp-viewer, FastAPI, Pydantic, Uvicorn. Declare direct dependencies used by our code.
- Development dependencies: pytest, HTTPX for in-process API tests, Ruff, mypy and watchfiles for reload/watching.
- Use Vite with plain TypeScript/CSS. Use npm and commit `frontend/package-lock.json`; install with `npm ci`.
- Use TypeScript checks and Vitest for frontend logic. Do not introduce a UI framework for the cube form.
- Resolve compatible released packages, then lock their exact versions. Initial CAD candidates are build123d 0.13.0 and
  ocp-viewer 1.2.0. Respect build123d's kernel dependency rather than adding an independent OpenCascade version pin.
- Configure Ruff for 120-character lines; type-check our Python application with mypy and our frontend with TypeScript.
  Constrain unavoidable third-party typing exceptions to the integration boundary.
- Install missing project dependencies during implementation. Do not upgrade global tools that satisfy the requirements.

The dependency-resolution and native-import checks are implementation evidence, not results established by this spec.

## Application boundary and runtime [U2, U3, U4]

Three user-started services participate in development:

| Service | Default address | Responsibility |
|---|---|---|
| Vite | `http://127.0.0.1:5173` | Our frontend; proxy `/api` to FastAPI |
| FastAPI | `http://127.0.0.1:8000` | Parameters, build coordination/status; production static assets |
| OCP Viewer | `http://127.0.0.1:3939` | Viewer page, state and supported geometry transport |

Use these same loopback defaults in development and production, except production does not run Vite. Ports and the viewer
URL must be explicit settings, passed through a single backend settings boundary. Expose the viewer URL to our frontend
through an API response so the browser does not independently hardcode it. Occupied ports fail visibly instead of causing
an automatic switch. No command other than the corresponding service command starts that service implicitly.

Our page contains a large iframe for the standalone viewer, a labelled cube-size input in millimetres, an Apply button,
a Rebuild button and a readable status/error area. Use the OCP-provided object tree and navigation controls.

The iframe loads the OCP server's viewer page. The Python OCP API tessellates build123d geometry and sends it through the
OCP server's WebSocket transport to the embedded three-cad-viewer renderer. Our frontend sends parameter JSON to FastAPI;
it does not implement the viewer protocol or manipulate the iframe DOM.

Verify iframe embedding and updates with the selected release. If embedding cannot work using documented configuration,
report the concrete blocker; do not substitute a custom renderer or undocumented transport as an implementation shortcut.

## Cube and API contract [U2, U3]

Generate one valid solid cube named `Cube`, centred at the origin, with equal side lengths in millimetres. Its initial
size is 100 mm. Keep the geometry-building function independent of FastAPI and viewer publication.

The parameter contract is a JSON object with one field, `size_mm`. Accept finite JSON numbers greater than zero and at
most 1000. Reject booleans, numeric strings, missing fields and unknown fields. The 1000 mm limit bounds this demo input.
Publish its default, bounds, unit and label through the backend's schema/metadata response; do not duplicate them in UI
source. UI validation improves feedback; the backend remains authoritative.

| Endpoint | Contract |
|---|---|
| `GET /api/parameters` | Current accepted `parameters`, field `schema`, and configured `viewer_url` |
| `PUT /api/parameters` | Complete `{"size_mm": 150}`; validate, accept a snapshot and request a build |
| `POST /api/model/rebuild` | Request a fresh build using current accepted parameters |
| `GET /api/model/status` | Latest requested revision, last published revision, state and error |

Successful mutation requests return HTTP 202 with their requested revision. Validation errors return HTTP 422 with
field-level details and do not change parameters, request a build, or disturb the displayed geometry. Unknown endpoints
under `/api` remain API errors; the static frontend handler must not conceal them.

Include an opaque API `session_id` in parameter, mutation and status responses; change it on every API process start.
Use monotonically increasing integer revisions within that session. Status states are `idle`, `building`,
`ready` and `failed`; `published_revision` is null before the first successful publication. An error identifies validation,
generation or viewer publication as applicable. Keep full Python diagnostics in the backend terminal.

Parameters and revision state are in memory. Restarting the API resets them to the default and a new revision sequence.
The frontend reloads current parameter/schema data when it observes a changed session and does not compare revisions
across sessions. The cube scaffold does not promise parameter persistence across restarts.

On page load, fetch parameters and initialize the iframe, then request a build so the page does not depend on the viewer
replaying an earlier scene. Handle initial viewer connection readiness with a bounded wait using supported viewer APIs;
report a publication error and allow Rebuild if the viewer is absent or fails to become ready.

Apply submits a valid edit; editing a field alone does not start builds. While work is outstanding, poll status every
500 ms. Continue a slower two-second status poll while idle so source-watcher builds and API restarts are observable.
Handle API unavailability without discarding the viewer; retry at the idle interval and refresh parameters/status when
the API returns. Rebuild uses the same coordinator as Apply.

## Build execution and failure handling [U2, U3, U4]

The API owns one coordinator and allows at most one active geometry build. Keep only the most recent pending request.
Take immutable parameter snapshots. Run CAD generation in a fresh subprocess using the project's interpreter, ensuring
source changes take effect without Python module-reload tricks. Do not perform heavy CAD work on the API event loop.

Do not publish partial results. After successful generation, the coordinator must check whether the revision is still
eligible before allowing publication through the supported OCP API. Serialize publication authorization with acceptance
of newer revisions: an already superseded result cannot replace a newer requested model. Once publication begins, treat
that publish as a serialized operation and process subsequently accepted work afterward.

Use a bounded publication timeout and capture failures. Mark `ready` only after generation and publication have succeeded;
this denotes completion of the publisher operation, not independently verified browser rendering. Verify visible rendering
in the integration acceptance procedure. Build/render telemetry beyond these states is outside scope.

Generation failure leaves the prior scene untouched. Preserve camera state on subsequent publications using documented
`Camera.KEEP` behaviour, and fit the initial cube. Publication failure reports an error without clearing the scene; a
connection failure cannot guarantee what the browser received, so allow explicit retry and do not claim a successful
revision. A failed attempt does not advance `published_revision`.

On application shutdown/reload, stop and reap its child before abandoning ownership. A child from an old API process must
not publish after its coordinator exits. No distributed queue, database, generic worker framework or second publishing
CLI is required. The CLI rebuild command routes through the running API.

## Development and production commands [U1, U4]

Use a Makefile compatible with the installed Make version, with thin recipes delegating to uv, npm and project entrypoints.
Keep lifecycle/state logic in Python rather than shell process-management scripts.

| Command | Behaviour |
|---|---|
| `make setup` | Install locked Python and frontend dependencies; create `.venv`; start no services |
| `make viewer` | Run the standalone viewer in the foreground using `.venv` |
| `make dev-api` | Run FastAPI with API reload and a CAD source watcher |
| `make dev-ui` | Run Vite with frontend hot reload and the API proxy |
| `make model` | Request a rebuild through FastAPI, wait for its outcome, exit nonzero on failure |
| `make check` | Ruff lint/format checks, mypy and TypeScript checks |
| `make test` | Python unit, real cube geometry and in-process API/worker integration tests |
| `make test-ui` | Frontend form/status/request tests with Vitest |
| `make format` | Apply Python formatting |
| `make build` | Build frontend assets, then wheel and source distribution in `dist/`; start no services |
| `make install-prod` | Check/test/build, install locked runtime dependencies and the exact built wheel into `.venv-prod` |

The development API uses Uvicorn reload for API/schema code. Exclude `cad/` from API restart triggers; a watchfiles watcher
debounces CAD edits and submits work to the same coordinator. The page-load request owns the initial build; the watcher
reacts to subsequent edits and recovers from syntax/build errors after the next valid edit. Avoid duplicate builds from
overlapping watchers. Frontend CSS/module edits
use Vite updates where supported; full-page reloads may recreate the iframe and camera.

Use `src/campervan/` for the package, with API, CAD and viewer-integration responsibilities separated. Use `frontend/` for
the TypeScript application, and package its generated output under `src/campervan/web/`. Introduce only modules that this
cube path needs; no empty campervan component modules or generic parameter/configuration framework.

The Python wheel must contain the compiled UI. Build the frontend before packaging and fail on missing assets. A source
distribution must retain the assets needed to rebuild an equivalent wheel without requiring a frontend rebuild. Do not
include development environments or frontend dependency directories. Serve package resources independently of the
working directory.

Production uses `.venv-prod` and a non-editable installation of the specific newly built wheel, plus runtime dependencies
exported from the lockfile without development dependencies or the project itself. Install the wheel without re-resolving
dependencies. Do not select old wheels with an ambiguous wildcard. Keep `.venv` intact.

Production startup uses `.venv-prod/bin/python -m ocp_viewer` and `.venv-prod/bin/campervan serve` on POSIX shells, with
equivalent environment executable paths documented for other shells when needed. Run one API worker. FastAPI serves the
compiled frontend and `/api` from port 8000. No Vite, reload or source watcher runs in production. Changing parameters still
rebuilds the cube. Source changes require rebuilding/installing and restarting. Node is a build-time dependency.

## Git and documentation [U4, U5]

Create `.gitignore` covering project Python environments, Python bytecode, tool/test/coverage caches, packaging metadata,
`dist/`, generated frontend assets, `node_modules/`, frontend build/test outputs and local log files. Include patterns for
local environment/credential configuration without reading, creating or modifying those protected files. Use scoped
patterns so source, tests, lockfiles, default configuration and existing documentation stay trackable. Do not untrack or
remove existing committed files as part of ignore setup.

Update README to document the implemented setup, development, tests, package build and production commands, service URLs,
shutdown and common failure recovery. It is for a first-time project user. Do not include roadmap stages, temporal status
banners, agent instructions or platform-specific project requirements. Remove commands and behaviour that this scaffold
does not provide, including presets, persistent data directories and campervan exports.

Keep the architecture and proposal as background documents. This spec owns the scaffold's concrete scope; no broad
documentation rewrite or historical transcript edit is needed.

## Verification and acceptance

The implementation is complete only when the following evidence exists. The user must start services: the working
agreement prohibits the agent from starting them. Ask for those launches after preparing the runnable commands and all
non-service checks. Use Chrome DevTools MCP for browser verification. Do not substitute a claimed pass if service/browser
access is unavailable; report the unverified acceptance item.

| ID | Acceptance evidence | Trace |
|---|---|---|
| A1 | `make setup` succeeds with installed Python and lockfiles unchanged; required CLI tools/imports work in `.venv` | U1 |
| A2 | `make check`, `make test`, `make test-ui` pass without running services | U1, U4 |
| A3 | User starts the three dev services; the application page displays one named cube with interactive rotation/zoom | U2 |
| A4 | Set size to 150 mm and Apply; backend builds/publishes it and the iframe updates without manual refresh | U3 |
| A5 | Invalid size input produces a useful error and preserves the last successful cube | U3 |
| A6 | A controlled CAD failure reports failure; restoring valid source updates the viewer through the dev watcher | U4 |
| A7 | Rapid accepted edits cannot publish a superseded build; generation does not block API status responses | U3, U4 |
| A8 | Backend and frontend edits trigger their documented reload behaviour; viewer update preserves camera where specified | U4 |
| A9 | Build/install production; verify packaged assets and cube builder from outside the checkout | U1, U4 |
| A10 | User starts production services; port 8000 serves the UI and parameter-to-viewer update works without Vite/watchers | U2–U4 |
| A11 | `git check-ignore` covers representative generated files while source, tests and both locks remain trackable | U5 |
| A12 | README commands match verified commands and retain no roadmap/status banners or platform prerequisites | U4 |

Test real cube geometry for validity, dimensions and volume with explicit tolerances. Test API schema validation,
revision/coalescing behaviour, child failure/shutdown and publication authorization using controlled workers and a mocked
viewer adapter. Test frontend metadata-driven input, Apply/rebuild requests, errors and status recovery using Vitest.
Verify packaging by installing the built wheel and checking static resources outside the editable source tree. Do not
require binary-identical CAD data, a full campervan model or cross-platform CI for this scaffold.

## Evidence and tool evaluation

Repository search, README, `docs/ARCHTECTURE.md`, `docs/scaffolding-proposal.md`, and the initial commit establish the
absence of reusable application code and the documented build123d/OCP/FastAPI boundaries. Installed tool versions above
were read with version commands; no project code, dependency installation or services ran during planning.

Official sources checked for integration:

- [OCP architecture](https://bernhard-42.github.io/ocp_viewer_docs/concepts/architecture/): renderer, tessellation and transport ownership.
- [Standalone transport](https://bernhard-42.github.io/ocp_viewer_docs/viewers/ocp_viewer/concepts/): Python → viewer server → browser.
- [OCP show API](https://bernhard-42.github.io/ocp_viewer_docs/show/): names, port selection and camera settings.
- [Standalone installation](https://bernhard-42.github.io/ocp_viewer_docs/viewers/ocp_viewer/installation/): released assets and server startup.
- [build123d metadata](https://pypi.org/project/build123d/): Python version requirements and released package.
- [uv projects](https://docs.astral.sh/uv/guides/projects/): project environment and lockfile workflow.
- [uv build backend](https://docs.astral.sh/uv/concepts/build-backend/): package layout and resource inclusion.
- [uv locking](https://docs.astral.sh/uv/concepts/projects/sync/): locked installs and development groups.
- [Vite guide](https://vite.dev/guide/): TypeScript template, development/build commands and Node requirement.
- [Uvicorn settings](https://uvicorn.dev/settings/): reload directories and process configuration.

### Candidate decisions

These comparisons concern tools introduced by this scaffold. They are not instructions to upgrade installed globals or
add alternatives to the dependency graph. All selected tools run locally without a required paid service.

| Responsibility | Selected approach and fit | Alternatives evaluated |
|---|---|---|
| Python workflow | uv owns environment, resolution, locking and execution; uv_build packages our Python code and assets | Poetry also locks/packages but supplies no repository-specific advantage; pip/venv requires additional lock/build conventions |
| API/schema | FastAPI, Pydantic and Uvicorn provide the approved ASGI API, validation/JSON Schema and serving/reload | Flask is viable but would need separate schema/validation integration; raw ASGI would duplicate routing and errors |
| Frontend | Vite with vanilla TypeScript supplies development serving and production bundling with a small UI | Plain JS is adequate for the form but requires extra reload/build conventions; a React/Vue UI framework adds no needed cube-shell capability |
| Python checks | pytest for behavioural fixtures/tests, Ruff for lint/format, mypy for application types | unittest can test the code but pytest's fixture ecosystem fits worker/API cases; Black plus separate linters adds tools; Pyright is viable but mypy keeps Python checking in the Python dependency group |
| Frontend checks | TypeScript compiler plus Vitest reuse the frontend language and Vite configuration | Node's test runner is viable but would need separate TypeScript setup; a browser automation framework is unnecessary for focused logic tests and the mandated Chrome DevTools verification |
| Source events | watchfiles supplies notifications, polling fallback, debounce and async interfaces; our coordinator owns rebuild decisions | A custom polling watcher duplicates an established library; watchdog is viable but watchfiles also integrates with Uvicorn's reload filters |
| CAD/display | build123d and standalone OCP Viewer follow the approved architecture and supplied Python publication API | Raw OpenCascade bindings increase modelling work; direct three-cad-viewer integration moves transport/render integration into our application and is outside this approved scaffold |

Our wheel contains Python and generated web assets; native dependencies do not require a native build backend for our
own package. Keep the publication adapter small and use the upstream API. The coordinator's revision and child-lifecycle
rules are application policy, not a replacement filesystem watcher or distributed task system.

### Maintenance, licensing and security evidence

Official release metadata checked on 15 October 2026 shows ongoing release activity: uv/uv_build, FastAPI, Pydantic,
Ruff, mypy, Vite and Vitest have October releases; Uvicorn, watchfiles and build123d have September releases; pytest has a
June release. The standalone ocp-viewer release is recent, and shares core/viewer functionality with the maintainer's
other integrations. That split supports code reuse but makes exact-version integration testing particularly important.
Recency and established integrations are maintenance/ecosystem evidence, not guarantees of compatibility.

The selected top-level licenses are permissive: uv/uv_build MIT OR Apache-2.0; build123d/ocp-viewer and TypeScript
Apache-2.0; Uvicorn BSD-3-Clause; FastAPI, Pydantic, pytest, Ruff, mypy, watchfiles, Vite and Vitest MIT; npm Artistic-2.0.
This is not a transitive-license audit or vulnerability certification. Locks and local binding reduce operational
variability/exposure but do not prove dependencies safe. Do not disable Vite hostname/CORS restrictions to make the
integration work. Use explicit API proxying and the selected viewer's supported configuration.

Supporting primary sources for these decisions:

- [Poetry workflow](https://python-poetry.org/docs/) and [pip installation controls](https://pip.pypa.io/en/stable/topics/secure-installs/).
- [FastAPI features](https://fastapi.tiangolo.com/features/) and [Flask documentation](https://flask.palletsprojects.com/en/stable/).
- [npm ci](https://docs.npmjs.com/cli/v10/commands/npm-ci/) and [Vitest configuration](https://vitest.dev/guide/#configuring-vitest).
- [watchfiles](https://watchfiles.helpmanual.io/) and [Uvicorn watcher integration](https://uvicorn.dev/settings/#reloading-with-watchfiles).
- [pytest](https://github.com/pytest-dev/pytest), [Ruff](https://github.com/astral-sh/ruff), [mypy](https://github.com/python/mypy).
- [Python package metadata](https://pypi.org/): each named project's release and license metadata; [uv metadata](https://pypi.org/pypi/uv/json), [viewer metadata](https://pypi.org/pypi/ocp-viewer/json).
- [Vite release metadata](https://registry.npmjs.org/vite), [Vitest](https://registry.npmjs.org/vitest), [TypeScript](https://registry.npmjs.org/typescript), [npm](https://registry.npmjs.org/npm).
- [uv index policy](https://docs.astral.sh/uv/concepts/indexes/#searching-across-multiple-indexes), [FastAPI security policy](https://github.com/fastapi/fastapi/security/policy), [Vite server controls](https://vite.dev/config/server-options.html).

The dependency resolver, imports, iframe, publication and packaging still require execution evidence during implementation.
