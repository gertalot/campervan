# Saved CAD model reuse

Goal: refresh or restart the application without rebuilding unchanged geometry.

Approved design: retain the last successful viewer payload, exact measurement geometry, motion tracks and cut list.
Reuse the existing OCP transport. Invalidate by resolved geometry dimensions, model/publishing source and dependency
versions. Live pose controls stay independent. Explicit Regenerate forces construction. Preserve a previous successful
model after a failed build and identify it as previous output.

Implementation follows the writing-plans and executing-plans skills in the current workspace. Repository instructions
supersede test, worktree, commit and delegated-review workflows: no tests or extra verification processes, no service
starts, no delegated review, preserve unrelated changes. Use read-only runtime evidence and Gert's visual inspection.

- [x] Capture an OCP bundle through its Comms interface; persist it atomically beside the local project.
  Files: src/campervan/model_cache.py, viewer.py, worker.py.
- [x] Restore bundle and cuts in Coordinator. Add a load/replay operation, reuse unchanged Apply, keep forced regeneration.
  Publish completed current revisions; retain prior bundle on failure. Files: coordinator.py, api.py, dev.py if needed.
- [x] Load/replay on frontend startup; display actual server state after mutations. Files: frontend/src/api.ts,
  controller.ts, main.ts, materials.ts as needed for previous-model feedback.
- [x] Update practical README and CAD workflow docs. Inspect the scoped diff, run git diff --check and inspect existing
  service logs/API without starting services or creating/running tests. Browser inspection uses the existing app tab
  through Chrome DevTools MCP only. State any unverified behavior.

Review focus: refreshed page while a build is running; changed dimensions versus a saved bundle; stale build completion;
viewer restart with exact measurement data; corrupted/incompatible cache; unchanged Apply; live pose replay.

Evidence: the existing development app constructed and saved an 11.4 MB bundle with display, measurement and motion
messages plus 118 cut parts. Its status reached Ready and the existing app tab contained the viewer canvas without
console errors. Read-only logs, API state and source review were used; git diff --check passed. No tests, builds or
browser interaction checks were run. Refresh/restart behavior, live poses and measurements remain for visual inspection.
