# Working on Campervan CAD

This is Gert's personal hobby project. Gert is its only user and developer. It runs locally and will never be
deployed. The software stakes are low; keep the code, tooling and development process simple.

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
- Use Python 3.13 through the project's uv environment (`uv run --locked ...`). Use the existing Make commands.
- Keep README instructions practical: how to set up, develop, check, build and run locally.
- Never start services yourself. Ask Gert to start them. Use only Chrome DevTools MCP for browser work.
- Do not access `.env`, `.env.test` or `.envrc`. Access `.beads` only through `bd`.
- Preserve unrelated edits, never expose credentials, and keep progress updates concise.
