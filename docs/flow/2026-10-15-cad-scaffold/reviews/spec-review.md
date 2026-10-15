# Scaffold spec review

Spec: [spec.md](../spec.md). Initial reviewed commit: `0a1d6bb`.

Six read-only reviews ran once, as required by `flow:plan`:

| Review | Result |
|---|---|
| Gap analysis | CLI supersession and API-restart scene recovery findings |
| Ambiguity | CLI supersession finding |
| Scope coherence | No findings |
| Design integrity | CLI supersession finding |
| Reuse and tool evaluation | No findings |
| Refactor-style | CLI supersession and API-restart scene recovery findings |

After deduplication: two findings, zero mechanical fixes, zero discarded out-of-scope findings. The user resolved both
through ordinary-chat discussion. The spec changes were applied together after the decisions were complete.

## Decision 1: explicit regeneration

The original `make model` contract could wait indefinitely when its revision was superseded or the API restarted. The
user removed the need for that CLI contract: no `make model` or model-regeneration CLI. Keep automatic regeneration and
an explicit UI button backed by a versioned API endpoint.

The user selected **Regenerate** as the term for executing CAD code and updating the viewer. Use
`POST /api/v1/model/regenerate` and version the other application API routes under `/api/v1`. Keep **build** for application
packaging. The Regenerate button provides retry/refresh; it does not become a prerequisite for normal interaction.

## Decision 2: automatic restart recovery

The original restart contract refreshed parameters but could retain a scene from the old API session indefinitely.
The user chose automatic regeneration after API process reload, preserving the previous scene until successful
publication. The frontend reuses initialization to refresh parameters/schema and request one regeneration for the new
session, or follow one already outstanding. OCP's existing WebSocket transport delivers the updated geometry.

The user clarified two normal triggers: accepted parameter/configuration changes through the API, and developer edits to
model source. For this cube, accepted size changes automatically schedule regeneration. CAD source changes load through
a fresh subprocess and retain the API's accepted parameters. Restarting the API process for API-code changes is a separate
recovery case. This clarification does not add campervan configuration/visibility controls to the cube scope.

## Viewer connection clarification

After discussing a same-origin OCP reverse proxy, the user chose simplicity for a localhost development setup. Keep
direct iframe and WebSocket connections to OCP Viewer; Vite proxies only the application API. No viewer proxy is needed.

## Verification limits

Reviewers inspected the spec, relevant repository documentation and tool evidence. The review established no dependency
installation, runtime, browser, geometry or production-package test result. Those checks remain implementation acceptance
work. The final written spec requires the user's review before the Flow implementation-plan handoff.
