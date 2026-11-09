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
processing stages and a processing log. **Show result in viewer** opens the finished reconstruction in its group.

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
Each compact row describes its reconstruction method and frame count. **Show in viewer** displays it;
**Inspect result** expands its processing details and management actions.
The **pencil** beside each result edits its display name. The **trash can** opens a confirmation naming the result
and its location. Confirming permanently deletes that generated result directory (or preview PLY) and removes its
library entry. Original capture databases and physical measurements are retained.

**Archive** hides a result from the selector without deleting any files. Use the manager's Archived filter to restore
it. If you archive the current result, the viewer selects an active fallback, or clears when none remains. New results
discovered outside the upload workflow start active in Ungrouped. Uploaded results are assigned to their capture group.
Library preferences live in `data/scan-library.json`, separately from assets and measurements.
The Interior trial group keeps three useful results active and archives earlier experiments. The 5 mm / 10 mm labels
describe fusion resolution, not an accuracy ranking.

### Measure between AprilTags

In **Scan**, click the tape-measure icon (**T**), then two tags. The bottom Distance field starts with the scan's
centre-to-centre distance or an existing measured value. Start typing to replace it; use units such as `841 mm`,
`12.4cm` or `1.2m`. **Enter** saves. **Esc** restores an edited value; a second Esc or an empty-space click cancels
the pair. Turning the tool off hides saved lines. The toolbar's **Manage measurements…** button reviews, edits and removes
saved pairs even when the tape tool is off. The status overlay offers **Restore**, **Cancel pair** or **Done** for
the current Escape action.

The status line overlays the viewer without resizing it. Escape at the first-tag prompt exits the tool.
The original trial uses `data/scan-measurements.json`; layouts created through import each have a separate
`data/scan-tag-layouts/<layout-id>/measurements.json`. No extra settings are needed. New documents start empty, and
the viewer selects the document associated with the displayed result. For manual CLI captures pass the intended
document with `--measurements FILE` to `scan process` (or `scan align` for an existing run). Reuse that file
while the physical tags stay fixed; use a new document/layout ID after moving them. No measurement is applied to
geometry automatically.

### Analyse measurements and improve the reconstruction

**Manage measurements…** uses the same side-panel component as **Manage scans…**, with an X close control and actions
above the list. The measurements panel leaves the viewer usable for orbit/pan inspection and does not resize it.

**Typical measuring precision (mm)** starts at an editable **3 mm** when no value is saved. Analyse and Suggest more
stay available while editing; clicking either validates and saves the chosen precision before continuing. Save precision
is also available separately. Missing/invalid values have a red field indicator and an adjacent explanation.
Precision is one standard deviation, not a guaranteed error bound; individual rows can override it (blank means use
the default). **Analyse uncertainty** fits the
original camera/tag observations together with the measured distances using GTSAM. It previews proposed tag movements,
original/fitted distances, residuals and approximate 95% uncertainty intervals. Inconsistent readings are downweighted
and marked Check. No entered distance is replaced with the fitted value.

**Apply** rebuilds a separate corrected result using fitted camera/tag poses; it keeps the source result and physical
measurements. The new result opens when ready unless that would interrupt measurement entry; **Show corrected result**
is also available. **Revert** discards an unapplied preview or returns to its source result after Apply. Failed builds
retain the solution and allow **Retry rebuild**. Accepted history survives reload in `data/scan-solutions.json`.

**Suggest more** lists every unmeasured pair predicted to reduce uncertainty by the selected threshold (initially
5 mm), ranked by expected benefit. The metric is reduction in the approximate 95% uncertainty half-width of at least
one tag-to-tag dimension. Gains share the same baseline and must not be added together. Expand a row to inspect the
affected dimension, clearance and overlapping benefits; **Measure pair** uses the normal tape-entry flow.

Clearance has three categories: No obstruction detected, Unknown, and Obstructed. The check uses the straight tape
segment, nearby mesh rays and observed depth coverage. Unknown is not a clear path; large proposed movements may need
Apply/rebuild before clearance can be assessed. **Show tape path** highlights the pair/obstruction, and **Not physically
measurable…** records a manual exclusion. Separate suggestions flag readings worth remeasuring.

Analysis requires a connected, observable graph. If uncertainty cannot be quantified, the panel shows diagnostics and
potential connections without invented millimetre benefits. Predictions depend on the stated noise assumptions; use
separate physical checks not included in fitting before relying on them for fabrication. No CAD dimensions change.
