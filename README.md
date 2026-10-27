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
