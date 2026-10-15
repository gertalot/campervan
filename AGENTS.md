# Working on Campervan CAD

This is Gert's personal hobby project. Gert is its only user and developer. It runs locally and will never be
deployed. The software stakes are low; keep the code, tooling and development process simple.

## What we're building

- [Project architecture](docs/ARCHTECTURE.md): the local Python CAD system and intended workflow.
- [Existing campervan design](docs/what-we-built-in-onshape.md): the NV200 interior, geometry, parameters and design intent
  to carry over from Onshape. The current FeatureScript sources are in `docs/fs/`.
- [README](README.md): setup and the commands to develop, build and run the application.
- Follow Gert's latest decisions and this file when older design or Flow documents prescribe heavier machinery.

## Validation

- The main test is Gert visually inspecting the model and reporting what looks wrong.
- Keep only a minimum of fast smoke tests for scaffolding and plumbing. Do not grow exhaustive API contracts,
  subprocess fault injection, race-condition matrices, browser automation suites, coverage targets or release gates.
- Later, as the actual model develops, add small, direct geometry checks where useful: unintended intersections,
  clearance and whether a moving object hits an obstacle. Do not build a collision-testing framework in advance.
- Prefer a few obvious assertions using build123d geometry operations. Keep checks easy to read, run and change.
- Run the checks relevant to a change once. Broaden them only when an observed failure warrants it. Report what was
  checked and what still needs visual inspection; do not claim that automated checks prove the design is correct.

## Development

- Implement the smallest coherent solution. Avoid production infrastructure, deployment workflows and speculative
  abstractions. Existing Flow documents are background; these instructions supersede their heavier test requirements.
- Use library defaults and direct calls. Do not add custom readiness gates, retries, timeouts or defensive lifecycle
  protocols without a demonstrated need. Gert can see whether the viewer is working; display real errors plainly.
- Use Python 3.13 through the project's uv environment (`uv run --locked ...`). Use the existing Make commands.
- Keep README instructions practical: how to set up, develop, check, build and run locally.
- Never start services yourself. Ask Gert to start them. Use only Chrome DevTools MCP for browser work.
- Do not access `.env`, `.env.test` or `.envrc`. Access `.beads` only through `bd`.
- Preserve unrelated edits, never expose credentials, and keep progress updates concise.

## Server logs

- `make dev-api` (or `make serve`), `make dev-ui` and `make viewer` print to the terminal and save combined stdout/stderr
  in `logs/api.log`, `logs/ui.log` and `logs/viewer.log`. Each launch replaces that process's log; logs are gitignored.
- Inspect the relevant logs when diagnosing a failure: `tail -n 80 logs/api.log` and
  `rg -n 'ERROR|Error|Traceback|failed|Warning' logs/*.log`. Check viewer logs for rendering/transport problems and UI
  logs for Vite/build errors. Browser console errors are separate from these server logs.
- Read the actual exception and its context before changing code. Do not infer success from an HTTP 200 alone.
- A process started before log capture was added still writes only to its terminal. Ask Gert for that terminal output
  or to restart the relevant Make command; never restart a service yourself or pretend missing logs were examined.

## Inspecting the running app

- Use Chrome DevTools MCP only. Start by listing pages and select the Campervan app by its URL
  (`http://127.0.0.1:5173` for development, `http://127.0.0.1:8000` for the built app). Leave unrelated tabs alone.
- If needed, open the running app in a new tab in the connected Chrome. Never start its servers to enable inspection.
  `make chrome` launches the project's debugging browser on port 9223; ask Gert to run it if browser access is missing.
- Use a DOM snapshot to locate controls, a screenshot to inspect layout/model framing, and the console/network tools
  to inspect actual failures. The OCP viewer is the iframe at `http://127.0.0.1:3939/viewer`; inspect that frame too.
- Try the relevant control and inspect the visible result. API publication status alone does not prove the model rendered.
  Use small manual checks, not a browser test suite. Gert's visual feedback remains the main acceptance check.
