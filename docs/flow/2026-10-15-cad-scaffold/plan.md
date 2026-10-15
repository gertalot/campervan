# CAD Application Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or
> superpowers:executing-plans to implement this plan task-by-task, subject to Flow's execution policy.
> Steps use checkbox (`- [ ]`) syntax for tracking. Flow owns execution selection and the final review handoff.

**Goal:** Install the project toolchain and display an automatically regenerated build123d cube in the local web app.

**Architecture:** Vite serves a TypeScript form and an iframe pointing directly to OCP Viewer. FastAPI owns parameters
and a single regeneration coordinator; each regeneration runs in a fresh Python child process. OCP supplies rendering
and geometry transport. The packaged application serves the compiled frontend through FastAPI.

**Tech Stack:** Python 3.13, uv/uv_build, build123d, ocp-viewer, FastAPI/Pydantic/Uvicorn, watchfiles,
Vite/TypeScript, pytest/HTTPX, Ruff/mypy, Vitest, npm and Make.

**Spec:** [spec.md](./spec.md). **Flow folder:** [2026-10-15-cad-scaffold](./).

## User scope correction — 2026-10-15

The user also explicitly removed defensive runtime machinery after the viewer readiness gate blocked a working viewer.
Regeneration now runs CAD and OCP `show()` directly in a fresh Python subprocess. Runs are serial; edits during a run
replace the parameters for the next run. There is no readiness polling, publication authorization handshake, custom
publication timeout, cancellation framework or frontend session-history protocol. FastAPI handles validation errors.
These decisions supersede the older runtime implementation details in Tasks 2–4 and the original spec.

This is a low-stakes, single-user, local hobby project that will never be deployed. Root `AGENTS.md` and the user's
latest instructions supersede the original test matrices and production acceptance requirements below.

- Keep minimal scaffold/plumbing smoke tests. Remove fault-injection fixtures, subprocess lifecycle test machinery,
  exhaustive contracts and duplicate coverage. Visual inspection by Gert is the main validation.
- Later model checks should be direct, simple geometry assertions for unintended intersections and obstructed motion.
  No collision framework or speculative model checks belong in this scaffold.
- Tasks 1–4 below record the original implementation work; their extensive test lists are historical, not requirements
  to preserve or restore. Keep the implemented runtime behavior.
- Replace Tasks 5–6 with the small local build/documentation and visual check described below. No `.venv-prod`,
  install orchestrator, production acceptance matrix or repeated full-suite gates.

## Global Constraints

- Read the approved spec and [review decisions](./reviews/spec-review.md) before executing. This plan implements U1–U5
  and A1–A12; the architecture/proposal are background, not additional requirements.
- Starting revision: `8759225ae40bd1c602c483fe000796511493152b`, branch `develop`, current checkout. No worktree.
  Recheck HEAD and ownership of changes at implementation entry. The existing README edit belongs to the user: it
  removes the manual `make model` paragraph. Preserve it and adapt the remaining README as authorized by Task 5.
- Scope ID is `docs/flow/2026-10-15-cad-scaffold/plan.md`. Follow the
  [Flow execution policy](/Users/gert/.codex/plugins/cache/codex-local/flow/1.0.0+codex.20260928233502/skills/implement/references/execution-policy.md).
  Worker briefs include the spec, assigned task, direct contracts, allowed files, exclusions and applicable evidence.
- Use installed CPython 3.13, `requires-python = ">=3.13,<3.14"`, `.python-version` = `3.13`, uv settings
  `python-downloads = "never"` and `python-preference = "only-system"`. Project Python runs through `.venv` via uv;
  no project Python before declaring that environment.
- Keep the installed compatible global tools. Node 22.23.3 satisfies Vite's 22.12+ requirement. Commit both lockfiles;
  routine sync/run/export commands use `--locked`. Initial lock creation is the deliberate exception.
- Distribution `campervan-cad`, import package `campervan`, `src/` layout; plain TypeScript/CSS, no UI framework.
  Use `uv_build==0.9.11`, matching the installed uv version, and verify it with Task 5's packaging checks.
- Preserve the spec's library choices and candidate evaluation. Start with build123d 0.13.0 and ocp-viewer 1.2.0;
  resolve released compatible dependencies and commit exact lock results. Declare direct imports as direct dependencies.
- All services bind loopback by default: Vite 5173, API 8000, OCP 3939. Vite proxies only `/api`. The iframe and its
  WebSocket connect directly to OCP. No viewer reverse proxy or implicit service startup.
- **Never start services as the agent.** Task 6 gives the user the prepared commands and waits for their launches.
  Browser work uses only Chrome DevTools MCP. Missing browser access leaves acceptance pending, not passed.
- Do not access `.env`, `.env.test` or `.envrc`. Settings use process environment/CLI values, with no dotenv loader.
  Do not access `.beads` directly. Do not expose credentials in output or evidence.
- No campervan migration, presets, persistence, moving assemblies, exports/BOM, authentication, deployment service,
  custom renderer, generic job framework or regeneration CLI. No `make model`. **Regenerate** runs CAD Python;
  **build** packages the application. Existing FeatureScript and historical documents remain untouched.
- CAD edits regenerate with current parameters without restarting the API. API-code reload creates a new session;
  the frontend refreshes parameters and automatically regenerates. Display-only controls are outside this scaffold.
- Use 120-character Python formatting. Keep unavoidable third-party typing exceptions at the viewer/CAD boundary.
- Run `make check`, the minimal `make test` suite and `make build` once after relevant changes. Reuse valid evidence.
- Record command, cwd, tested file identities, tool/environment versions, exit status, result and acceptance coverage
  in Flow's existing task reports/ledger and final review evidence. Do not create another tracking mechanism.

## Verification under the revised scope

Keep one API smoke test, one cube geometry check and three frontend checks. Run lint/type checks and a local build.
Gert's visual inspection of the cube and size changes supplies the main application feedback. Source reload and error
recovery can be checked while developing if needed; no scripted failure matrix or production environment is required.
The original A9/A10 isolated production acceptance requirements are retired.

## File and Task Boundaries

All application paths below are new. README is the only existing non-Flow file to modify. Add `__init__.py` files for
Python package directories that contain modules; do not create empty future component packages.

| Location | Owner and responsibility |
|---|---|
| `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, `Makefile` | Task 1 establishes toolchain; later tasks add their commands |
| `src/campervan/parameters.py`, `settings.py`, `cad/cube.py` | Task 1: strict parameter contract, runtime settings, pure geometry |
| `src/campervan/viewer.py`, `worker.py` | Task 2: supported OCP adapter and one-child generation/publication handshake |
| `src/campervan/coordinator.py`, `api.py`, `dev.py`, `cli.py` | Task 3: lifecycle, HTTP API, source watching, service commands |
| `frontend/package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, `src/` | Task 1 setup; Task 4 UI, API proxy, frontend tests |
| `src/campervan/web/` | Task 5: generated frontend assets, built through Make |
| `tests/integration/`, `tests/geometry/` | Minimal API and cube smoke tests |
| `README.md` | Task 5: setup, develop, test, build, run and recovery instructions |

## Task 1: Install the Toolchain and Establish the Cube Contract

**Spec coverage:** U1–U5; A1, A2, A5, A11. Depends on no implementation task.

**Files:** Create root manifests/locks/Makefile/ignore file; `src/campervan/__init__.py`, `parameters.py`, `settings.py`,
`cad/__init__.py`, `cad/cube.py`; frontend package/lock/tsconfig; `tests/unit/test_parameters.py`,
`tests/unit/test_settings.py`, `tests/geometry/test_cube.py`.

**Interfaces:**

```python
DEFAULT_SIZE_MM = 100.0
class Parameters(BaseModel):  # frozen=True, extra="forbid"
    size_mm: float  # required, strict, finite, 0 < size_mm <= 1000

def default_parameters() -> Parameters: ...
def parameter_schema() -> dict[str, object]: ...
def make_cube(parameters: Parameters) -> Part: ...

@dataclass(frozen=True)
class Settings:
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    viewer_host: str = "127.0.0.1"
    viewer_port: int = 3939
    ui_host: str = "127.0.0.1"
    ui_port: int = 5173
    development: bool = False
    publication_timeout_s: float = 30.0
    @property
    def viewer_url(self) -> str: ...  # http://<viewer_host>:<viewer_port>/viewer

def load_settings(environ: Mapping[str, str] | None = None) -> Settings: ...
```

- [x] Establish the environment before executing project code. Add Python metadata, `uv_build` settings with
  `module-name = "campervan"`, uv policy, Ruff/mypy/pytest configuration, and declared runtime/dev dependencies from
  the spec. Set version `0.1.0`. Put watchfiles in dev dependencies and import it only in development paths.
  Create the package initializer so editable installation succeeds without built frontend assets.
- [x] Add npm scripts `dev`, `build` (`tsc --noEmit && vite build`), `check` (`tsc --noEmit`), `test` (`vitest run`),
  and dev dependencies Vite, TypeScript and Vitest. Vitest uses the Node environment and pure controller tests;
  no DOM test framework is required. Create initial locks with `uv lock` and
  `npm --prefix frontend install --package-lock-only`, then use `uv sync --locked` and
  `npm --prefix frontend ci`. Do not install global tools or start anything.
- [x] Add `make setup` with those two install commands; `check`, `test`, `test-ui`, and `format` delegate to the
  declared tools. `make check` runs Ruff check/format-check, mypy and TypeScript; `make test` runs pytest.
  Frontend checks become executable when Task 4 supplies its sources; do not disguise missing tests as a pass.
- [x] Write parameter/geometry/settings tests before their implementations. Accept integer and float JSON numbers;
  reject `0`, `-1`, `1001`, non-finite numbers, `true`, `"150"`, missing `size_mm` and unknown fields. Assert default
  100, metadata label `Cube size`, unit `mm`, exclusive minimum 0 and maximum 1000.
  For sizes 100 and 150, assert one valid solid, bounds `[-size/2, size/2]` on all axes and volume `size**3`
  with `pytest.approx(rel=1e-9, abs=1e-6)`.
- [x] Run the focused tests and observe the missing implementation failure. Implement Pydantic strict finite bounds
  on a required field; put the schema's default/unit in field metadata rather than making missing input valid.
  Derive metadata with `model_json_schema()`. Build `Box(size, size, size)` centred on all axes and label it `Cube`.
- [x] Implement the single settings boundary using `CAMPERVAN_API_HOST`, `CAMPERVAN_API_PORT`,
  `CAMPERVAN_VIEWER_HOST`, `CAMPERVAN_VIEWER_PORT`, `CAMPERVAN_UI_HOST`, `CAMPERVAN_UI_PORT`, and `CAMPERVAN_DEV`.
  Default dev flag is false; validate configured ports as 1–65535. CLI overrides are applied through this boundary.
  Settings tests cover defaults, valid overrides, invalid ports and the derived viewer URL. No file-based secrets loader.
- [x] Add scoped ignore patterns for `.venv/`, `.venv-prod/`, Python caches/bytecode, Ruff/mypy/pytest/coverage outputs,
  egg metadata, `dist/`, `src/campervan/web/`, `frontend/node_modules/`, frontend build/coverage and local logs.
  Include environment/credential filename patterns without accessing those files. Do not ignore all JSON/TOML or docs.
- [x] Verify with `uv run --locked pytest tests/unit/test_parameters.py tests/unit/test_settings.py tests/geometry/`.
  Run `make setup` and confirm SHA-256 hashes of `uv.lock` and `frontend/package-lock.json` are unchanged.
  Check `uv run --locked python -c 'import build123d, ocp_viewer, fastapi, pydantic, uvicorn'`, Ruff/mypy/pytest versions,
  and `npm --prefix frontend exec -- vite --version`. These imports/version commands start no services.
- [x] Feed the ignore command representative paths `.venv/example`, `.venv-prod/example`, `dist/example.whl`,
  `src/campervan/web/index.html`, `frontend/node_modules/example`, `.pytest_cache/example` and `__pycache__/example.pyc`;
  assert all are ignored. In a separate invocation, assert `src/campervan/parameters.py`, `tests/unit/test_parameters.py`,
  `uv.lock`, `frontend/package-lock.json`, `pyproject.toml` and `docs/ARCHTECTURE.md` are not ignored.
  Use path strings only, without creating generated or protected files for this check.
- [x] Commit only Task 1 files: `feat(scaffold): install toolchain and define cube parameters`.

## Task 2: Generate in a Child and Publish through OCP

**Spec coverage:** U2–U4; A3, A5–A8. Depends on Task 1.

**Files:** Create `src/campervan/viewer.py`, `worker.py`, `tests/unit/test_viewer.py`,
`tests/integration/test_worker.py`, and `tests/fixtures/worker_targets.py`.

**Interfaces:**

```python
def publish_cube(cube: Part, settings: Settings) -> None: ...  # raises PublicationError

def worker_main(connection: Connection) -> None: ...
async def start_worker(parameters: Parameters, settings: Settings) -> Worker: ...
class Worker:
    async def wait_generated(self) -> None: ...
    async def publish(self) -> None: ...
    async def close(self) -> None: ...  # terminate if needed, join, close IPC
```

- [x] Write tests for delayed authorization, generation error, EOF, child exit and publication timeout. Use controlled
  worker targets in tests; the production target is fixed, not selected by HTTP input. A child must hold its generated
  shape without publishing until authorized. One real-child test creates the actual cube and stops before publication.
  Viewer tests mock the public OCP calls and assert explicit host/port, name `Cube`, `Camera.KEEP`, readiness timeout,
  transport warning conversion and propagated errors. Run tests to establish failures before implementation.
- [x] Use `multiprocessing.get_context("spawn")` to create one fresh child with a duplex `Pipe`. No CAD shape crosses
  IPC. Import `cad.cube` inside the child's guarded generation step so syntax/import errors become generation failures.
  The parent closes its copy of the child connection immediately after launch. Run blocking receive/join operations
  off the event loop with `asyncio.to_thread`; closing kills/reaps as necessary and finishes outstanding receive work.
  On close, terminate an active child, wait up to two seconds, then kill and join if necessary. Always close the pipe.
- [x] Use this small internal message contract; do not expose it as a public regeneration CLI:

  | Direction | Message |
  |---|---|
  | Parent → child | `{"type":"generate","parameters":{"size_mm":150},"settings":{...}}` |
  | Child → parent | `{"type":"generated"}` |
  | Parent → child | `{"type":"publish"}` |
  | Child → parent | `{"type":"published"}` |
  | Child → parent | `{"type":"error","stage":"generation" or "publication","message":"..."}` |

  Log full tracebacks to stderr. EOF or parent-directed termination exits without publication. The child exits after
  publication or error. Treat unexpected messages/exit as failure, never as a successful publication.
- [x] Implement the adapter with public `ocp_viewer.set_port(port, host)`, `status()` and
  `show(cube, names=["Cube"], reset_camera=Camera.KEEP)`. OCP handles initial splash-camera fitting; verify that
  behaviour in Task 6. Do not call clear/reset before replacement. Wait up to 10 seconds, polling at 100 ms, for
  nonempty browser-reported status; the parent's 30-second publication deadline bounds all adapter work.
  Convert connection warnings to publication failures within a scoped warning filter. A missing/empty status times out.
- [x] Preserve the upstream limit: `show()` returns no delivery acknowledgement, and status can be stale after a
  browser disconnect. `published` means the adapter completed without a detected failure, not proof of rendering.
  Do not implement a private OCP protocol, monkeypatch transport, or claim guaranteed browser delivery. Test the
  supported readiness/warning behaviour of the selected lock; if it cannot meet the spec, report the concrete blocker.
- [x] Verify `uv run --locked pytest tests/unit/test_viewer.py tests/integration/test_worker.py` without services.
  Assert child reaping on normal completion, timeout and cancellation. Record mocked transport evidence separately
  from the real CAD child result. Commit Task 2 files: `feat(cad): isolate generation and gate viewer publication`.

## Task 3: Add the API, Coordinator and Development Reloads

**Spec coverage:** U2–U4; A4–A8. Depends on Tasks 1–2.

**Files:** Create `src/campervan/coordinator.py`, `api.py`, `dev.py`, `cli.py`,
`tests/unit/test_coordinator.py`, `test_dev.py`, `test_cli.py`, `tests/integration/test_api.py`.
Modify `pyproject.toml` for `campervan = "campervan.cli:main"`, and `Makefile` for service commands.

**Interfaces:**

```python
class Coordinator:
    def __init__(self, settings: Settings, worker_factory=start_worker) -> None: ...
    session_id: str
    parameters: Parameters  # immutable accepted snapshot; replaced only by accept()
    async def accept(self, parameters: Parameters | None = None) -> int: ...
    def status(self) -> ModelStatus: ...
    async def close(self) -> None: ...

def create_app() -> FastAPI: ...  # production/development settings from load_settings()
def build_app(settings: Settings, worker_factory=start_worker) -> FastAPI: ...  # in-process tests
async def watch_cad(directory: Path, coordinator: Coordinator, stop_event: asyncio.Event) -> None: ...
def main() -> None: ...  # argparse: viewer, dev-api, dev-ui, serve
```

- [x] Define `ModelStatus` and its optional error value as frozen dataclasses in `coordinator.py`; use their fields
  below for HTTP serialization. Define parameter/mutation response models in `api.py`. The API imports coordinator
  types; the coordinator must not import the API. Use consistent field names in Task 4:

  | Response | Exact fields |
  |---|---|
  | Parameters | `session_id`, `parameters`, `schema` (parameter JSON Schema), `viewer_url` |
  | Mutation | `session_id`, `requested_revision` |
  | Status | `session_id`, `requested_revision`, `published_revision`, `state`, `error` |
  | Error value | null or `{"stage":"generation" or "publication","message":"..."}` |

  Initial status: requested revision 0, published null, state `idle`, error null. Use a UUID session ID per application
  lifespan. Create the coordinator inside lifespan; its loop starts on first acceptance. Pydantic 422 responses own
  validation errors and do not alter coordinator status.
- [x] Write controlled-worker tests: revision 1 starts; accept 2 then 3; finishing 1 cannot authorize it; only 3 runs
  next and publishes. Use events/barriers, not timing sleeps. A publication in progress holds the acceptance gate;
  a later mutation is accepted only after it completes/fails. Concurrent status reads remain responsive.
  Cover generation error, publication error/timeout, recovery, immutable snapshots and shutdown with an active child.
- [x] Implement one async coordinator task, one active child and one replaceable pending request. `accept` acquires
  the publication gate, atomically stores parameters and increments revision, replaces pending work and clears the
  latest error. Keep state `regenerating` while a current request is outstanding. After generation, take the same gate
  and check that the active revision still equals requested revision before publishing. Hold it through the bounded
  publish and cleanup. Superseded success/failure must not overwrite the current request's status.
  On eligible success update published revision/state; on eligible failure retain published revision and set `failed`.
  Status reads copy a consistent snapshot without waiting for the publication gate. Shutdown stops the watcher first,
  blocks new acceptance, cancels the coordinator and reaps its child before lifespan exits.
- [x] Write in-process FastAPI tests and then implement the four spec routes under `/api/v1`: GET/PUT parameters,
  POST model/regenerate, GET model/status. Mutations return 202. PUT schedules once; POST uses existing parameters.
  Invalid/missing/unknown input returns 422 without mutation or worker launch. Unknown `/api` paths return 404.
  Use HTTPX/TestClient and controlled workers; lifespan is explicitly entered. No network service is started.
- [x] Implement `watch_cad` with watchfiles `awatch`, filtering `.py` changes under the package's `cad/` directory,
  debounce 250 ms, and calls to `accept()` using current parameters. No watcher-triggered initial regeneration.
  Import watchfiles only on this dev path. Test change batches with an injected event source, including syntax-error
  failure followed by a valid edit; preserve the API session and accepted size.
- [x] Implement CLI service commands. `dev-api` enables `CAMPERVAN_DEV=1` and invokes Uvicorn with the import-string
  factory, reload on the package directory, and the absolute CAD directory excluded. `serve` disables dev mode,
  uses one worker, no reload/watcher, and supports `--host`/`--port` overrides. Test generated Uvicorn arguments and
  watcher lifecycle without invoking Uvicorn. No CAD import is needed in the API process.
- [x] `viewer` runs the project's interpreter with `-m ocp_viewer --host <viewer_host> --port <viewer_port>`.
  `dev-ui` invokes npm's dev script, passing resolved API target and UI host/port as process environment values
  `CAMPERVAN_API_TARGET`, `CAMPERVAN_UI_HOST`, `CAMPERVAN_UI_PORT`. This keeps settings resolution in Python.
  Commands stay foreground, propagate child exit status and handle Ctrl-C. Add thin Make recipes delegating to
  `uv run --locked campervan viewer`, `dev-api`, `dev-ui`. No other Make recipe starts these services.
- [x] Run `uv run --locked pytest tests/unit/test_coordinator.py tests/unit/test_dev.py tests/unit/test_cli.py
  tests/integration/test_api.py` as one shell command (join the wrapped line). Assert the CAD directory is excluded
  from the actual Uvicorn reload filter using the selected Uvicorn version. Commit Task 3 files:
  `feat(api): regenerate automatically through one coordinator`.

## Task 4: Display the Viewer and Drive Regeneration from the UI

**Spec coverage:** U2–U4; A3–A5, A8. Depends on Tasks 1 and 3.

**Files:** Create `frontend/index.html`, `vite.config.ts`, `src/main.ts`, `src/style.css`, `src/api.ts`,
`src/controller.ts`, `src/controller.test.ts`. Complete frontend package configuration from Task 1.

**Interfaces:** `api.ts` mirrors Task 3's four response shapes and exports `getParameters`, `getStatus`,
`putParameters({size_mm})`, `regenerate`, all returning typed promises. `controller.ts` exports
`createController(api, view, clock): { start(): Promise<void>; apply(raw: string): Promise<void>;
regenerate(): Promise<void>; stop(): void }`. The view provides `setMetadata`, `setParameters`, `setViewerUrl`,
`setStatus`, `setError`; clock provides timer scheduling/cancellation. Tests inject these small dependencies.

- [x] Write controller tests with deferred promises and fake timers. Cover metadata-derived bounds/unit/default,
  Apply sends one PUT with a number and no POST, explicit Regenerate sends POST, invalid/empty input sends nothing,
  422 field errors, publication errors, active 500 ms/idle 2000 ms polling, API unavailability/recovery, and session change.
  Reject a late response from an obsolete initialization/poll after session recovery; never compare revisions between
  sessions. Test that repeated polls for the same new session cause at most one automatic regeneration.
- [x] Implement sequential polling (schedule the next poll after completion) and an initialization generation token
  to discard obsolete responses. Initial load fetches metadata, sets the iframe URL, checks status and requests one
  regeneration unless it is already outstanding. API recovery refreshes parameters/status. A changed session uses the
  same initialization path once; a same-session reconnection follows existing status without an automatic extra request.
  Ignore a response whose session is obsolete; refresh before acting on a response from a new session.
- [x] Preserve the iframe element and its URL across normal renders, errors and API restarts. Do not inspect its DOM
  or carry geometry through the application API. Iframe loading can begin before regeneration; Task 2 bounds readiness.
  A failed initialization request is shown as an error with Regenerate available, not retried by every idle poll.
- [x] Wire `main.ts` to a labelled numeric size field, Apply, Regenerate, a readable live status/error region and the
  large iframe. Validate from the returned JSON Schema, including exclusive minimum. Do not hardcode 100/1000 in TS.
  A field edit alone does not submit. Preserve dirty input during ordinary polls; a new session refreshes accepted
  parameters as specified. Show accepted request status and keep controls usable for newer edits while regenerating.
- [x] Configure Vite from the process values supplied by Task 3: loopback host, fixed port, `strictPort: true`, and
  `/api` proxy only. Keep normal Vite host/CORS protections. Output to `../src/campervan/web` with that directory as
  the sole build-clean target; generated assets live under `/assets`. Use Vitest's Node environment for controller tests.
- [x] Run `npm --prefix frontend test` and `npm --prefix frontend run check`. Neither launches a service.
  Commit Task 4 files: `feat(ui): embed the viewer and synchronize regeneration state`.

## Task 5: Finish the Local Build and Usage Guide

- [x] Add a thin `make build`: compile the frontend and run `uv build`. No custom orchestration script.
- [x] Serve the built frontend with the existing local `campervan serve` command, without reload.
- [x] Update README to the actual setup, development, minimal tests, build and local run commands.
  Preserve the user's Chrome instructions. No deployment workflow, saved-configuration claims or `make model`.
- [x] Run lint/type checks, the retained smoke tests and one build. No packaging compatibility matrix or release gate.

## Task 6: Inspect the Cube

- [ ] Ask Gert to start the viewer, API and UI if they are not running. Never start services as the agent.
- [ ] Inspect the cube and change its size. Use Chrome DevTools MCP if available, or Gert's visual feedback.
  Visual inspection is the main test; no automated browser acceptance suite is needed.
- [ ] Report actual results and any remaining visual verification. Do not claim browser results from headless checks.

## Planning Evidence and Self-Review

The approved spec records repository reuse, candidate selection and tooling evaluation. Repository inspection for this
plan confirms no application implementation or CI to reuse. README has the known user deletion described above. The
scaffold is one integrated deliverable: tooling, API, viewer, frontend and packaging all serve the cube acceptance path.

Primary implementation references checked:

- [OCP 1.2.0 public exports](https://github.com/bernhard-42/ocp_viewer/blob/v1.2.0/ocp_viewer/__init__.py),
  [show binding](https://github.com/bernhard-42/ocp_viewer/blob/v1.2.0/ocp_viewer/show.py),
  [status API](https://github.com/bernhard-42/ocp_viewer/blob/v1.2.0/ocp_viewer/config.py).
- [OCP core transport](https://github.com/bernhard-42/ocp-viewer-core/blob/v1.1.2-1.1.0/ocp_viewer_core/websocket.py)
  and [viewer state](https://github.com/bernhard-42/ocp_viewer/blob/v1.2.0/ocp_viewer/server/viewer.py): warning and
  acknowledgement limits. These sources justify adapter isolation; they do not authorize replacing the transport.
- [uv_build resource inclusion](https://docs.astral.sh/uv/concepts/build-backend/) and
  [Uvicorn reload controls](https://uvicorn.dev/settings/). Installed `uv build --help` and `uv export --help` were
  checked for executable command syntax. `uv_build` 0.9.11 release metadata exists; its package checks remain Task 5 work.

Implementation verification after the scope correction: two Python tests passed in 4.20 seconds, three frontend
tests passed in 164 ms, `make check` and `make build` passed. A one-off in-process smoke check confirmed built HTML,
assets and API routes, and the wheel contains the frontend. No services were started. Visual inspection is pending.
A brief final code review found no blocking issues. The broad test machinery was removed, leaving 134 test lines.
