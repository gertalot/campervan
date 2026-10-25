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
Bed-height limits update while editing and explain which part prevents a lower or higher platform. Drawer and support
heights reduce automatically if needed; the sidebar shows those adjustments. Invalid drafts cannot be applied and are
not saved or sent to CAD. Stock sizes and measured vehicle dimensions remain unchanged.
Sidebar groups follow the model's assembly hierarchy. Click a heading to collapse it; the browser remembers that choice.
Click a group's eye icon to show or hide its geometry without regeneration. Visibility is saved across reloads;
the eye icons and category checkboxes reflect partial visibility when only some children are shown.
The floor reference rectangle and rear-door opening wire are hidden by default.
Drag the sidebar's right edge to resize it; the browser remembers its width too.
Use **Regenerate** to retry after an error.
The browser remembers your camera view, slider positions and visibility choices across regeneration and page reloads.
Use the viewer toolbar to reset or refit the camera when needed.

The viewer has a minimal display/measurement toolbar, a ViewCube at the top right and an XYZ indicator.
Click a cube face, edge or corner to select a view; its four top corners give the four upright isometric views.
Clicks rotate at 360°/s; drag the cube to orbit directly. View changes preserve zoom and viewing centre.
Dragging in the main viewer also keeps Z upright, so the vehicle does not roll onto its side.
Dragging, zooming or another click interrupts the rotation. There is no splash model or Tools/Info panel.
Vehicle references use the measured door openings, rear pillars, fitted floor and ceiling, plus approximate wheel
arches and cab geometry. Open sliding-door envelopes and a closed hatch inner surface show storage clearances. Use the group eyes to hide the walls or roof while working inside.
Body length is independent of furniture layout length. Width is shared. Profile controls and door positions are editable
under **Vehicle references**; their tooltips identify estimates. See the [NV200 research](docs/research/nv200/README.md)
for sources and the measurements needed to check the fit against the van.
The long bench contains separate fixed plywood frames, a cab-end skin and a rear header. Its dimensions and construction
thicknesses are editable in the sidebar. Platform height includes the allowance for slats above the frame.
Live controls sit at the top of the sidebar, outside the collapsible dimension groups.
The **Vehicle**, **Slats**, **Cushions**, **Cabinet**, **Long bench** and **Cross bench** checkboxes show or hide those
categories without regeneration. Assembly switches and content filters work together: showing a bench keeps disabled
slats/cushions hidden, and enabling slats/cushions never reveals a hidden bench. Checkboxes retain their own settings.
Slats includes the long bench's fixed/moving slats and the fixed cross-bench slats.
Visibility preferences are saved in the browser and reapplied after regeneration.
**Doors closed (%)** slides both doors forward, then pulls them inward over the final 15%.
Zero is fully open; 100 is closed. The control animates instantly and retains its position.
**Long bench conversion (%)** runs through three stages: 0–40 extends its frame, 40–80 repositions its seat and
backrests, and 80–100 lowers them into place. The green backrest is split into 580mm along the cross bench’s right side and 700mm along its front.
Both pieces fill the outer long-bed strip when extended. The cross bench has one full-width fixed cushion
and no conversion slider. Dragging backward reverses the long-bench sequence.
**Drawer extension (%)** moves the rear drawer independently from retracted to fully extended.
No Apply or regeneration is needed. Slider positions are saved in browser storage and sent to the API;
dimension changes, source edits and page reloads retain the selected positions.
The sliders preview the cushions being repositioned. This represents
repositioning them by hand. Use each bench's **Cushions** eye to hide its foam, or the top checkbox to hide all cushions and pillows.
Shared foam thickness is under **Long bench → Cushions**.

Expand **Mannequin** for a poseable human sized to 178cm with an 80cm inseam, 40cm thighs and 50cm floor-to-knee height.
**Seated mannequin** fits the initial seated pose. X/Y/Z, facing, hip/knee bend, back recline, back curvature, head tilt and
arm angles have live sliders. Position is measured at the hip joint. Ankles compensate to keep the feet flat;
changing leg angles adjusts hip height to retain floor contact. Changing hip height solves the leg angles instead.
The seat cushion dents under the person; **Foam compression** is an estimate, adjustable in millimetres.
**Visibility → Mannequin** toggles all three mannequins. Each nested control group saves its posture independently.
The lying controls adjust position offsets, rotation, back, head, hip/knee bend and hand position live.
**Lying mannequin** and **Second lying mannequin** show two same-size people on their respective pillows automatically when the bed is fully extended, with the head on the front pillow, ankles lightly
crossed and hands over the belly. **Pillow compression** adjusts head support directly in the browser.
The seated preview is hidden while extending the bed. Other body proportions and foam deformation are estimates;
the mannequin is a visual fit reference and is not part of CAD exports.

The rear drawer has five 12mm plywood panels and simplified three-stage rails on each side. Its dimensions are under
**Long bench → Rear drawer**. Rails and bed brackets are provisional hardware envelopes.
The fixed cross bench behind the cab is two open-legged plywood support frames, with slats screwed directly
across their top rails. The existing aft skin spans between the rear legs of the two frames. There is no slide-out,
divider, deck, hinged lid, stop hardware or cab-end skin. Its footprint remains the fully extended bed width by the
remaining cargo length. **Cross bench → Fixed frame → Aisle slat overhang / foot recess** defaults to 200mm
at the aisle end. The wall-side support follows the internal drawer support, giving 150mm overhang at defaults.
The two support frames run fore/aft. Four long slats run across the van, with the first and last
at the bench edges, matching the previous extended cross bench. At defaults, 80mm slats have 86⅔mm clear gaps
within the 580mm depth; the junction to the extended long bench retains its 90mm gap. Toilet/tray hardware and
fixing details remain unmodelled.
The left-side **Cabinet** uses 12mm plywood for its solid centre/cab-end partitions, aisle frame, seven separate
rear rails and narrow transverse rear upright, independently of the bed's 18mm frames. The rails and upright
are under **Cabinet → Wall supports**. There are no cabinet skins, broad wall-side frames or bottom panel.
The rear bay has two shelves above a 650mm-deep, 730mm-high chair compartment with a clear rear entrance.
Above that entrance, a 12mm **Rear upper panel** closes the two shelf compartments at the cabinet's rear edge.
Its bottom follows **Rear storage clear height**, its top follows the ceiling, and its outer edge is scribed to the body.
The forward bay has three shelves and 326mm clear length at defaults. The van floor serves as the bottom.
The rear upright stands ahead of the rear pillar; its narrow plywood profile and the partitions will need
physical templates from the real van. Straight rear rails sit progressively inward at higher levels and join
the cabinet's partitions/upright. They are not fastened to the vehicle wall. The solid centre partition has a
wheel-arch notch and reaches the floor inside the arch. Shelves are notched around the rear upright.
All five shelves are intended to be glued to their pine ledges, with ledges bonded to the supporting panels/rails.
Fourteen vertical pine blocks reinforce both ends of every rear rail, under **Cabinet → Rail joint blocks**.
They are 18 × 18 × 60mm at defaults, with two adjacent faces glued to the rail and its upright/partition.
Shelf corners are notched and adjoining ledges shortened around them. Two aisle corner cleats remain in the forward bay.
Ledges, joint blocks, cleats and latch blocks use ready-made
18 × 18mm untreated clear pine, sourced from Bunnings in 2.4m lengths; only square crosscuts are needed.
The BoM includes one initial 250ml bottle of exterior PVA; clamp close-fitting bare-wood joints while curing.
Glue layers, assembly screws and vehicle restraints are not modelled. Restraint must use existing mounting
points only. The flute board is non-structural; the approximate CAD wall is not a final fabrication template.
Ledge bottoms align with the rail bottoms, leaving a 30mm retaining lip at the default material sizes.
Both bays share their middle shelf and beam heights, set by **Rear storage clear height**. Adjust **Upper shelf reference
height**, length and **Ceiling gap** under **Cabinet**, and material sizes under **Shelves** and **Shelf ledges**.
The ceiling gap defaults to 3mm; zero brings the solid cab-end panel to the ceiling. There is no cabinet top panel.
The aisle frame above the doors always extends to the plywood ceiling, with its top scribed to the ceiling profile.
The lower front shelf top follows the slat-top height plus uncompressed mattress thickness plus **Lower shelf above
mattress** (10mm). The matching aisle beam and door overlap follow this height. With the saved 390mm platform and
100mm mattress, the shelf top is 500mm, beam 470–530mm and upper door bottoms 515mm. Numeric bed/mattress bounds
keep the raised divider below the next shelf opening; they update when these dimensions change.
The cabinet has ten 9mm overlay doors with 15mm overlap, 12mm corner radii and 2mm edge roundovers.
The rear storage doors are split into lower and above-bed pairs, each opening outward on opposite hinges.
An aisle-only crossbeam joins their horizontal split; there is no shelf behind it and rear loading stays clear.
Its aisle skin is removed while rear loading stays open. All nine doors use Vanlifer NZ Point push latches;
their 50mm depth is measured from the door front, so 41mm sits inside the cupboard. Latch and striker envelopes
are shown; four pine blocks support the topmost and lower-storage strikers. Striker dimensions and fixing details still need
checking against the actual hardware.
Each of the four upper shelf openings has its own bottom-hinged flap, restrained horizontally by two short chains.
The bottom storage pair and bottom forward door remain side-hinged. The merged storage above-bed door and its
forward neighbour are bottom-hinged flaps, each with two chain restraints.
The **Cabinet upper doors** slider operates the four drop-down flaps. **Cabinet front bottom door**,
**Cabinet front above-bed door**, **Storage bottom doors** and **Storage above-bed flap** independently open
the corresponding doors to 90 degrees without regenerating.
The carcass moves toward the wall to reserve the door thickness and closing gap, retaining the 1070mm bed envelope.
Door plywood, small face-mounted hinges and two 3m packs of restraint chain have Bunnings NZ links and prices;
the nine positive push latches are sourced from Vanlifer NZ. Hardware and fasteners are sourcing candidates;
confirm leaf thickness, fixing holes, through-fixings and chain attachment/closing clearance before drilling 9mm doors.
Under **Vehicle references → Roof**, adjust the estimated **Roof bows** and the **Finished ceiling** plywood thickness, rear position and length.
The 3mm plywood follows the bows' shallow underside curve. Cabinet height and the cab-end panel contour follow its underside.

**Vehicle references → Cab** contains an estimated cab floor, driver/passenger seats and headliner. Adjust the floor
length/width, shared seat sizes, individual seat positions/reclines and headliner profile in those groups. Cab and
cargo floors are one level. The driver
is on the right. Each group can be hidden independently. Cab dimensions are provisional; see the
[cab research and measurement notes](docs/research/nv200/cab.md).

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
- [Conversion planner and purchases](docs/planner.md)
- [Current FeatureScript](docs/fs/nv200-interior.fs)

Use **Plan** as a continuous rich-text document with nested tasks, multiline text, tables and linked purchases.
Use the compact toolbar or slash commands. Enter continues text within a task; Cmd/Ctrl+Shift+Enter adds another task.
Use **Bill of materials** to edit categories/tags, quantities, purchases and costs, with filters and totals.
Its **CAD stock and cutting details** section retains supplier links, pack sizes, availability and component uses. Bunnings availability is for Lyall Bay, Wellington;
listed prices exclude freight. Each supplier product appears once, combining requirements across components.
Material dimensions in the CAD sidebar open that product and highlight the relevant component use.

Expand a product using its arrow to see **Used by** and the **Combined cut list**. Identical cut sizes are grouped
across components; expand a size to see its part locations. Sheet and timber purchase counts need a
cutting layout that allows for kerf, grain and waste. Hardware pack counts come from the model; the three stages
of each drawer slide count as one purchased slide. Shelves and drawer share the same 12mm plywood product.

Tell Codex when you want a product sourced or changed. Selected stock dimensions drive the model automatically:
shelf ledges use the sourced 18 × 18mm pine, for example. Measured overrides account for the actual material you buy.
Sheet sizes and timber lengths define stock to cut; they do not change the furniture layout. Product details live in
`src/campervan/materials.json`; default selections and parameter bindings live in `materials.py`. Selections and
measured overrides persist with parameters in `.local/project.json` and can be updated through the materials API.
Camera and visibility stay intact when switching tabs.
The URL records the tab and highlighted material (`/cad`, `/bom`, `/bom/skins`, `/plan`), so reloads, bookmarks and
browser Back/Forward restore that view.

Two dark-grey 600 × 400 × 200mm pillows share the long-bench conversion control. In day mode they are propped at 45°:
the rear pillow sits diagonally in the rear-door/backrest corner and the front pillow sits toward the right sliding door; in bed mode they lie side by side at the cab end, each remaining 600mm wide across the bed.
