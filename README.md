# Campervan CAD

A local CAD and build-planning app for a Nissan NV200 campervan conversion. Use it to design the furniture,
check the available space, plan the build and track materials and purchases.

The design includes a sliding slat bed, cross bench, storage cabinet, locking rear drawer and folding laptop table.
The model uses parametric Python geometry built with [build123d](https://github.com/gumyr/build123d).

## The application

| View | What you can do |
| --- | --- |
| CAD | Change dimensions, move the furniture, and check space using mannequins and stored gear. |
| Bill of materials | Track materials, suppliers, costs and purchases, with categories, filters and totals. |
| Plan | Break the conversion into nested tasks, with notes, tables and linked purchases. |
| Cut list | See individual pieces and sheet layouts, allowing for kerf, grain direction and available stock. |
| AprilTags | Generate a PDF of unique 36h11 tags, automatically fitted to the selected paper and print dimensions. |

Double-click a wooden piece to find it in the other view: CAD to cut list, or cut list to CAD.

## Run locally

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node.js 22.12+ and `make`.

```sh
make setup
```

Start these in separate terminals:

```sh
make viewer     # 3D viewer service
make dev-api    # Python API and CAD source watcher
make dev-ui     # Web interface
```

Open **http://127.0.0.1:5173**. Keep one application tab open: the viewer service sends geometry to one active connection.

Edit the model in `src/campervan/cad/` or change dimensions in the app. Dimension changes rebuild geometry; sliders
and dragging move the existing model in the browser. The development services reload source changes.

## Saved project

- `data/project.json`: dimensions, material selections, cutting layouts and mannequin configurations.
- `data/planning.json`: the conversion plan and purchase records.

Commit these files with the source. Generated caches and recovery files stay in the ignored `.local/` directory.
Camera, category visibility and moving-part pose preferences stay in browser storage.

## Guides

- [Using the application](docs/using-the-app.md)
- [CAD model and construction details](docs/cad-model.md)
- [Conversion planner and purchases](docs/planner.md)
- [Cushion-making guide](docs/squabs-guide.md)
- [Development and troubleshooting](docs/development.md)

## Share the design

`make site` exports an interactive snapshot to `site/`, including the model, saved cutting layouts, BOM and purchases.
The Plan page and its document are excluded from the static site.
Visitors can explore the design; editing requires the local app.
See [static export and GitHub Pages](docs/static-site.md) for publishing instructions.

## Process an interior scan

The **Scan** tab displays exported point clouds and completed reconstruction runs using the same navigation as CAD.
Processing runs offline, without starting the application or viewer services:

For scan processing on macOS, download the [official RTAB-Map 0.24.2 release](https://github.com/introlab/rtabmap/releases/tag/0.24.2),
verify the DMG checksum against the release assets, and drag `RTABMap.app` to `/Applications`. The app supplies its
native libraries; the processor configures its child processes automatically. CAD-only use does not need RTAB-Map.
Set `CAMPERVAN_RTABMAP_BIN_DIR=/path/to/bin` to select another installation; both required tools must be there.
On Linux, the default discovery uses PATH, but runtime compatibility has not yet been verified.

```sh
uv sync --locked --extra scan
uv run --locked --extra scan campervan scan process data/van-interior-merged-tags.db \
  --output .local/scans/van-next-5mm --voxel-mm 5
```

Use a new output directory for each run. In the app, select **Scan → Refresh scans**, choose the run and switch between
Cloud, Coloured mesh and Baked colour. Original database files remain unchanged. Generated assets and native
processing diagnostics live in the run directory; retain a separate backup of irreplaceable databases.

For original, separate scans, supply their paths together; RTAB-Map merges their sessions before reconstruction:

```sh
uv run --locked --extra scan campervan scan process \
  data/261107-170546-van-int.db data/261107-171946-van-int.db data/261107-172733-van-int.db \
  --output .local/scans/van-new-run --voxel-mm 10 --sdf-trunc-mm 50 \
  --tag-family 36h11 --tag-size-mm 80
```

`--texture-mode photo` additionally uses OpenMVS to texture the same Open3D mesh from the saved photographs.
Pass `--alignment data/scan-alignment.json` to use this van's saved tag-to-axis definition. The pipeline has no implicit
alignment configuration; another scene can supply its own definition. New captures solve a new transform using the
same tag roles. To align existing results without rebuilding:

```sh
uv run --locked --extra scan campervan scan align .local/scans/van-5mm \
  --alignment data/scan-alignment.json
```

See [scan processing and native-tool setup](docs/photogrammetry.md) for installation, settings and limitations.

### Organise scan results

To process new captures, open **Scan → Manage scans…** and click **Add capture databases…** beside the capture group
(for example `interior-v1`), or drop `.db` files onto that group. Review the selected databases, choose **Create new
tag layout…** for newly placed tags, and enter the layout name and actual printed tag size. Choose a result name,
surface detail and optional photographic texture, then click **Process captures**. The dialog shows upload progress,
processing stages and a processing log. **Review capture** opens the finished reconstruction and its measurement
workflow; **Show result in viewer** remains available.

Previously imported databases remain selectable for another run without uploading again. Processing continues when
the dialog closes; use **Show processing progress…** in the group to return. One reconstruction runs at a time.
Stopping/reloading the API interrupts processing; imported databases remain available to process again.

Imports are kept under `data/scan-captures/`; new tag layouts and separate measurement documents live under
`data/scan-tag-layouts/`. Generated results remain in `.local/scans/`. A new layout never inherits the old tag roles,
measurements or axis alignment. After opening a result, the tape tool uses that result's measurement document.

The **Result** selector shows active results. **Manage scans…** opens a panel for searching, viewing processing
details, renaming results, organising capture groups and choosing the startup default. Renames are display labels;
original filenames and run IDs stay unchanged. Reloading this tab preserves its selected result and layer. The startup
default applies to a fresh tab, or when the remembered result is unavailable or archived.
Scan changes, layer changes and page reloads preserve the camera position, pan, zoom and projection, including for
unaligned scans. Use the viewer's **Fit** control when you want to frame a different result automatically.
Each compact row describes its reconstruction method and frame count. **Show in viewer** displays it;
**Inspect result** expands its processing details and management actions.
The **pencil** beside each result edits its display name. The **trash can** opens a confirmation naming the result
and its location. Confirming permanently deletes that generated result directory (or preview PLY) and removes its
library entry. Original capture databases and physical measurements are retained.

Capture groups use larger section headings above their databases and results. The group's **trash can** confirms
deletion of the group, its imported database copies, generated results, linked corrections and processing history.
Reusable tag layouts/physical measurements and source files outside the app's capture storage are retained.
Expand **Imported databases** to see the raw captures. Drag a database or result onto another group. For keyboard
use, focus a database row and press **Enter** to choose a group; results retain **Change capture group…** in their
details. Moving a result moves its source/corrected-result family together;
correction jobs use the source's current group when publishing their result.

Group and result deletion reuse one named confirmation dialog, focus **Cancel** initially and restore focus on
close, following the relevant [WAI modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).
The keyboard actions provide an alternative to dragging; this is not a claim of a complete accessibility audit.

**Archive** hides a result from the selector without deleting any files. Use the manager's Archived filter to restore
it. If you archive the current result, the viewer selects an active fallback, or clears when none remains. New results
discovered outside the upload workflow start active in Ungrouped. Uploaded results are assigned to their capture group.
Library preferences live in `data/scan-library.json`, separately from assets and measurements.
The Interior trial group keeps three useful results active and archives earlier experiments. The 5 mm / 10 mm labels
describe fusion resolution, not an accuracy ranking.

### Review and improve a scan

Open **Review and improve scan…** for a result with a tag layout. The four stages share the same saved physical
measurements as the tape tool. Stage status is advice; incomplete measurements can still support a clearly labelled
best-effort correction when the required source inputs exist.

| Stage | Action |
| --- | --- |
| Review capture | Inspect the scan and tags; use **Review placement** for coverage and geometry advice. |
| Measure | Set precision, **Generate checklist**, and enter physical centre-to-centre distances. |
| Check accuracy | **Check measurements** assesses physical ranges; **Suggest more** offers pairs and rechecks. |
| Update reconstruction | Inspect **Preview corrections**, then explicitly **Update mesh** for a new result. |

The editable defaults have different meanings: **3 mm** measuring precision is one standard deviation of a range;
**5 mm** positional target is the longest semi-axis of a tag's approximate 95% uncertainty ellipsoid; the separate
**5 mm** meaningful-improvement threshold controls additional suggestions. These are assumptions and goals, not a
woodworking accuracy guarantee. Scan coordinates initialise/orient the physical assessment; they do not constrain its
fit or supply its information. The correction preview is a separate, scan-assisted calculation.

The checklist and tape accept `mm`, `cm`, `m`, `in` and `ft`; bare values mean millimetres. **Enter** saves a row and
advances after acknowledgement; leaving an edited nonempty row also saves. **Escape** restores its saved value. Save
errors retain the draft for correction or retry. The scan estimate is labelled separately and is never saved merely
by selecting a pair. Precision fields use millimetres; individual pairs can override the default.

The planner considers all useful pairs, rather than a fixed shortlist. Inspect overlapping benefits and access
reasons: **Unknown** clearance is not evidence of a clear path. Record **Cannot measure this pair…** when needed.
Suggestions and physical checks never rebuild geometry. Changed inputs mark affected reports as needing an update;
review current reports before rebuilding. Originals and entered distances remain intact. A completed rebuild never
switches the displayed result automatically. Use **Show original** or **Show corrected result** to compare results in
their capture group without resetting the camera.

Reuse a saved tag layout across captures only while the physical tags remain fixed. If tags move, use **Revise tag
layout…** and identify unchanged, moved, removed and added tags: only pairs whose two endpoints are confirmed unchanged
are carried forward. Existing captures keep their layout; select the revised layout for replacement captures.
A fresh layout starts with separate empty measurements and no inherited vehicle-axis roles.
See [the scan workflow guide](docs/photogrammetry.md#workflow) for assumptions and revision details.

For a quick pair, enable the tape icon (**T**) and select two tags. Type the physical distance in the bottom field and
press **Enter**. **Escape** restores an edit, then cancels the pair; at the first-tag prompt it exits the tool. Turning
the tool off hides saved lines. The workflow panel remains usable without tape mode and leaves orbit/pan available.

Workflow state is stored beside the project in `data/scan-workflows.json`; managed layouts and physical measurements
live in `data/scan-tag-layouts/`. The original trial uses `data/scan-measurements.json`. Manual CLI captures select the
intended document with `--measurements FILE` on `scan process` or `scan align`. Existing capture and measurement files
are retained; obsolete analysis/history files are not read or automatically migrated by the replacement workflow.
The four-stage workflow still needs Gert's visual and physical acceptance in the running app.
