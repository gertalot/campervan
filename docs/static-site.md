# Static export and GitHub Pages

Run from the project directory after setup:

```sh
make site
```

The export goes into `site/` and includes the model, motion data, saved cutting layouts, bill of materials and plan.
Both the local application and exporter read `data/project.json` and `data/planning.json`. Commit these files with the
source so GitHub Actions receives the saved design and plan.

The exporter reuses a matching model cache or builds the geometry offline. It starts no services.

## Included controls

Visitors can move the camera, toggle visibility, adjust mannequins and operate sliders or drag moving parts.
Links between CAD pieces and cutting drawings work. The plan and purchases support reading, search and filters.
Visitors can download cutting drawings and CSV lists.

Dimensions, materials, the plan and purchase records are read-only. Regeneration, cutting optimisation and exact CAD
measurements require the local application.

Calculate missing cutting layouts in the local app before exporting. `make site` includes current saved layouts and
reports any missing or outdated ones; it includes the corresponding pieces and dimensions without a layout.
It does not run the cutting optimiser.

## Hosting

Upload the contents of `site/` to an HTTP(S) static host. Opening `index.html` through `file:///` is unsupported.
Relative asset paths and hash URLs such as `#/cuts` allow hosting beneath a repository path without server rewrites.
The exporter includes `.nojekyll`. Generated `site/` is gitignored.

Run `make site` again to update an export. The header shows its export date. Browser preferences stay in that browser;
they do not change the project files. The site includes the complete saved plan, purchases and supplier details.

## GitHub Pages

In the repository's **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions**.
The workflow in [site.yml](../.github/workflows/site.yml) runs on pushes to `main`, or manually on `main` from Actions.
Other branches skip the build and deployment.

The workflow checks that both saved data files are tracked, runs `make setup` and `make site`, and uploads `site/` for
publication. It runs no tests or local services. The deployment provides the site's URL.

Reference: [GitHub's Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
