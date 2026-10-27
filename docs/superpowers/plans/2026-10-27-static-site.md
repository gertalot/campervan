# Static snapshot export

Approved scope: `make site` exports the model, cutting layouts, BOM and purchases for static hosting.
The Plan page and its document remain available in the local app and are excluded from static exports.
The export keeps camera, visibility, mannequin controls, joint motion and CAD/cut-list links. Dimensions, project
editing, regeneration, layout optimisation and exact backend measurements are unavailable. No publication is requested.

Implementation uses the existing viewer messages and page components. A static data source loads frozen read responses;
project mutation controls are hidden or read-only. Relative asset URLs and hash navigation support GitHub Pages project
subdirectories. The live local application keeps its existing URLs and backend behaviour.

Saved project inputs now live in `data/project.json` and `data/planning.json`, ready to be committed alongside the source.
The local application and exporter share these files. The generated model cache and plan recovery files stay in
gitignored `.local/`. Existing saved inputs were relocated without changing their contents.

- [x] Export consistent project data and model display/motion frames, sharing response builders with the local API.
- [x] Add `campervan site` and `make site`, producing `site/` with the frontend and installed viewer assets.
- [x] Load the snapshot directly, without WebSocket, polling or project writes. Keep poses in browser storage.
- [x] Make purchases read-only, retaining links, filters and totals; exclude the Plan page and document.
- [x] Show saved cutting layouts without optimisation or editable stock settings.
- [x] Document the command, output, refresh workflow and manual inspection limits.

Follow AGENTS.md: no tests, services, browser interaction checks or delegated review. Inspect the changes and use
`git diff --check`; Gert performs visual acceptance. Do not run an export/build just as an extra verification process.

References consulted for the interaction and hosting choices:

- https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/disabled — use native read-only/disabled
  controls for unavailable edits; preserve ordinary viewing and navigation.
- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages — static HTML/CSS/JavaScript
  hosting; project sites normally live beneath the repository name.
- https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/ — read-only plan items retain disclosure buttons, `aria-expanded`
  and native keyboard activation.
- https://www.w3.org/WAI/ARIA/apg/patterns/tabs/ — the static tab list contains only CAD, BOM and Cut list; its existing
  arrow/Home/End navigation operates over those three available tabs. Old `#/plan` links resolve to CAD.

Export performed with `make site`: Vite build succeeded and produced the snapshot, model messages, viewer assets and
mannequin GLB. Six current cutting layouts were included; floor plywood and existing bed slats had no current saved
layout. A Vite chunk-size advisory remains. No tests or services were run; the exported site's visual behaviour still
needs manual inspection in a browser served over HTTP(S).
