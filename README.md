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

The page automatically regenerates the model on opening. Edit dimensions in the sidebar and click **Apply**.
Sidebar groups follow the model's assembly hierarchy. Click a heading to collapse it; the browser remembers that choice.
Click a group's eye icon to show or hide its geometry without regeneration. Visibility is saved across reloads;
the eye icons and category checkboxes reflect partial visibility when only some children are shown.
Drag the sidebar's right edge to resize it; the browser remembers its width too.
Use **Regenerate** to retry after an error.
The browser remembers your camera view, slider positions and visibility choices across regeneration and page reloads.
Use the viewer toolbar to reset or refit the camera when needed.

The viewer has a minimal display/measurement toolbar, a ViewCube at the top right and an XYZ indicator.
Click a cube face, edge or corner to select a view; its four top corners give the four upright isometric views.
Clicks rotate at 360°/s; drag the cube to orbit directly. View changes preserve zoom and viewing centre.
Dragging in the main viewer also keeps Z upright, so the vehicle does not roll onto its side.
Dragging, zooming or another click interrupts the rotation. There is no splash model or Tools/Info panel.
Vehicle references include rounded wheel arches, tapered walls, sliding-door openings, a crowned roof, a separate
finished-ceiling reference and the rear hatch opening. Use the group eyes to hide the walls or roof while working inside.
Body length is independent of furniture layout length. Width is shared. Profile controls and door positions are editable
under **Vehicle references**; their tooltips identify estimates. See the [NV200 research](docs/research/nv200/README.md)
for sources and the measurements needed to check the fit against the van.
The long bench contains separate fixed plywood frames, a cab-end skin and a rear header. Its dimensions and construction
thicknesses are editable in the sidebar. Platform height includes the allowance for slats above the frame.
Live controls sit at the top of the sidebar, outside the collapsible dimension groups.
The **Vehicle**, **Slats**, **Cushions** and **Cabinet** checkboxes show or hide those categories without regeneration.
Slats includes both beds' fixed and moving slats, the cross-bench plywood deck, hinged storage lid and plate stops.
Visibility preferences are saved in the browser and reapplied after regeneration.
Drag **Bed conversion (%)** through three stages: 0–40 extends both bed frames, 40–80 repositions the cushions,
and 80–100 lowers the backrests into place. Dragging backward reverses that sequence.
**Drawer extension (%)** moves the rear drawer independently from retracted to fully extended.
**Storage lid opening (%)** opens the lid up to 70 degrees.
No Apply or regeneration is needed. Slider positions are saved in browser storage and sent to the API;
dimension changes, source edits and page reloads retain the selected positions.
The bed slider also previews the six cushions moving from seats and upright backrests to a flat bed. This represents
repositioning them by hand. Use each bench's **Cushions** eye to hide its foam, or the top checkbox to hide all six.
Shared foam thickness is under **Long bench → Cushions**; cab-facing backrest length is under **Cross bench → Cushions**.
Hide cushions when inspecting the storage lid; they do not lift with it.
The rear drawer has five 12mm plywood panels and simplified three-stage rails on each side. Its dimensions are under
**Long bench → Rear drawer**. Rails and bed brackets are provisional hardware envelopes.
The cross bench behind the cab contains its fixed frame, toilet-storage divider, deck, sliding slats and hinged storage
lid. Adjust the toilet bay depth and deck dimensions under **Cross bench → Fixed frame**, and the lid gap and finger
hole under **Cross bench → Storage lid**. Its width follows the bed and long-bench widths; its depth fills the space
between the long bench and the cab.
The two recessed cross-bed stops move with the slats. Their dimensions are under
**Cross bench → Sliding assembly → Extension stops**.
Both cross-bench end slats move, keeping a regular support gap at the long-bench junction. Slats retain their stock
width; the cross bench distributes the remaining space evenly between them.
The right-side **Cabinet** has an aisle frame and stepped end frames with the same rounded openings as the benches.
Each end frame is one piece, narrowing above the upper shelf rail. All shelf rails align across the aisle and end
frames: a bottom rail, a lower shelf rail matching the bed support, and an upper shelf rail. Only the 7mm skins follow
the wall and ceiling curves. Adjust **Upper shelf rail height**, length and **Ceiling gap** under **Cabinet**.
The ceiling gap defaults to 3mm, and zero brings the skins to the ceiling. Top, shelves, doors and bottom are not included.
Under **Vehicle references → Roof**, adjust the estimated **Roof bows** and the **Finished ceiling** plywood thickness.
The 3mm plywood follows the bows' shallow underside curve. Cabinet height and skin contours follow its underside.

Edit CAD models in `src/campervan/cad/` and the web interface in `frontend/src/`. Saving CAD changes regenerates the
model with the selected parameters. Backend changes reload the API, reset dimensions to defaults and automatically
regenerate with your saved slider positions. Frontend changes trigger Vite updates or a page reload.
Dimensions are kept in API memory; camera, slider and visibility preferences are kept in browser storage.
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
Automated tests provide a small sanity check of the plumbing and reference geometry.

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

- **OCP logo instead of the model:** keep only one app/viewer tab open. OCP sends updates to one active browser connection.
  Close duplicate viewer tabs, reload your app page, then click **Regenerate** if needed. DevTools should inspect that
  same tab, not open another viewer.
- **Blank viewer:** inspect the viewer terminal or `logs/viewer.log`, then reload the app page.
- **Regeneration failed:** read the error in the application and backend terminal, correct the model, then click **Regenerate**.
- **Port already in use:** stop the previous instance you started before launching another.
- **Dependency or interpreter error:** check that Python 3.13 is available, then rerun `make setup`.

## Project documentation

- [Existing campervan design](docs/what-we-built-in-onshape.md)
- [Application architecture](docs/ARCHTECTURE.md)
- [CAD model conventions](docs/cad-model.md)
- [Current FeatureScript](docs/fs/nv200-interior.fs)
