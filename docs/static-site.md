# Static export and GitHub Pages

Run from the project directory after setup:

```sh
make site
```

The export goes into `site/` and includes the model, motion data, saved cutting layouts, bill of materials and purchases.
Commit `data/project.json` with the source so GitHub Actions receives the saved design, materials and cutting layouts.
Keep `data/planning.json` local and ignored. Local exports read it when present to include purchase records; GitHub
Actions uses the exporter's existing default planning data when that file is absent. The static site excludes the
Plan page and its document.

The versioned `data/scan-reference/mesh.ply` is the selected coloured van-interior reference. Its minimal
`reference.json` records the scan alignment and CAD registration. The exporter copies that mesh and includes its
descriptor in the snapshot; the published CAD viewer uses the same loading, placement and opacity controls as the
local viewer. Raw captures, processing runs and scan-editing/cross-section tools remain local. To publish a different
reference, replace both the mesh and its registration together.

The exporter reuses a matching model cache or builds the geometry offline. It starts no services.
The saved project includes all three mannequin poses, their individual visibility and the group's visibility.
An export starts with that configuration. Visitor changes stay in browser storage and do not update the project.

## Included controls

Visitors can move the camera, toggle visibility, adjust mannequins and operate sliders or drag moving parts.
Links between CAD pieces and cutting drawings work. Purchases support reading, search and filters.
Visitors can download cutting drawings and CSV lists.

Dimensions, materials and purchase records are read-only. Regeneration, cutting optimisation and exact CAD
measurements require the local application.

Calculate missing cutting layouts in the local app before exporting. `make site` includes current saved layouts and
reports any missing or outdated ones; it includes the corresponding pieces and dimensions without a layout.
It does not run the cutting optimiser.

## Hosting

Upload the contents of `site/` to an HTTP(S) static host. Opening `index.html` through `file:///` is unsupported.
Relative asset paths and hash URLs such as `#/cuts` allow hosting beneath a repository path without server rewrites.
The exporter includes `.nojekyll`. Generated `site/` is gitignored.

Run `make site` again to update an export. The header shows its export date. Browser preferences stay in that browser;
they do not change the project files. The site includes purchases and supplier details, and excludes the plan document.

## GitHub Pages

In the repository's **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions**.
The workflow in [site.yml](../.github/workflows/site.yml) runs on pushes to `main`, or manually on `main` from Actions.
Other branches skip the build and deployment.

The workflow checks that the saved project and scan-reference files are tracked, runs `make setup` and `make site`, and uploads `site/` for
publication. It runs no tests or local services. The deployment provides the site's URL.

Reference: [GitHub's Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
