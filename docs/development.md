# Development and troubleshooting

See the [README](../README.md#run-locally) for dependencies and local startup commands.

## Source and saved data

- `src/campervan/cad/`: Python geometry and assembly definitions.
- `src/campervan/parameters.py`: dimensions and live-control metadata.
- `frontend/src/`: TypeScript web interface.
- `src/campervan/materials.json`: product catalogue and supplier details.
- `data/`: saved project inputs, versioned with the source.
- `.local/`: generated model cache and plan recovery files, ignored by Git.

Use Python through `uv run --locked`. `make setup` installs the locked dependencies without activating the virtual
environment. The local API restores saved project data after a reload; the frontend reloads through Vite.

The model cache contains viewer geometry, measurement shapes, motion tracks and cut parts. Its fingerprint includes
dimensions, CAD/publishing source and installed CAD/viewer versions. Live pose changes reuse the existing geometry.
Failed construction retains the previous complete model and reports the error in the app.

## Checks and formatting

```sh
make check      # Python formatting, lint and type checks; frontend type checks
make format     # Apply Python formatting
```

The project uses manual visual inspection for model and interaction changes. It has no maintained test suite.

## Build without hot reload

```sh
make build
```

This compiles the web interface and packages the Python application into `dist/`. It does not generate CAD geometry.
Start `make viewer` and `make serve` in separate terminals, then open **http://127.0.0.1:8000**.
After source changes, stop the application, build again and restart it.

## Chrome and DevTools MCP

`make chrome` starts a separate debugging browser for this project. Open the app in that browser once the services
are running. Use one application tab; a second viewer connection can take over geometry delivery.

Chrome exposes remote debugging at `http://127.0.0.1:9223` and keeps its profile in
`~/.config/chrome-devtools-campervan`. Set `CHROME_BIN` if Chrome has a nonstandard location.
The project-local `.codex/config.toml` connects Chrome DevTools MCP to that port.

## Logs and troubleshooting

The services print terminal output and save it to `logs/api.log`, `logs/ui.log` and `logs/viewer.log`. Each launch replaces
its log. Read the exception in the relevant terminal or log when something fails.

| Symptom | Where to look |
| --- | --- |
| OCP logo instead of the model | Keep one app/viewer tab open, reload it, then regenerate if needed. |
| Blank viewer | Viewer terminal, `logs/viewer.log` and the browser console. |
| Regeneration failed | Error in the application and backend terminal or `logs/api.log`. |
| Frontend build error | UI terminal or `logs/ui.log`. |
| Port already in use | Stop the previous process using that port before restarting. |
| Dependency or interpreter error | Check Python 3.13 is available, then rerun `make setup`. |
