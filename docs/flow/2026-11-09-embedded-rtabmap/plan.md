# Installed RTAB-Map binary integration plan

**Status:** revised on 9 November 2026 after installation of the official app. Planning only.
**Goal:** use installed RTAB-Map CLI binaries for capture processing without native compilation, defaulting to
`/Applications/RTABMap.app` on this Mac and allowing another installation directory to be configured.
**Architecture:** call the app's existing exporter/reprocessor executables from the current processing worker.
Supply library search paths only to those subprocesses, using the app's bundled Frameworks directory. Preserve the
installed app, its signatures, current logging/cancellation and scan interchange.
**Flow folder:** [this folder](./). **Previous spec:** [spec.md](spec.md).
**Preserved interchange:** [shared C1/C5 contracts](../2026-11-09-scan-measurement-workflow/shared-contracts.md).

## Decisions replacing the previous plans

Gert's latest direction supersedes the source-build/in-process-extension choices and the subsequent private-copy
installation plan. The previous spec's minimal-build, Python-binding and GUI-exclusion prescriptions are historical
design choices, not instructions to reintroduce that implementation. Preserve N1–N4: Homebrew independence, native
processing semantics, downstream compatibility and factual provenance/footprint. This changes the implementation
plan, not the historical approval record.

- Use the official app already installed in `/Applications`; do not download/install another copy under `.local`.
- Keep its supplied libraries and GUI components. Do not trim, patch, relocate, re-sign or rebuild the app.
- No installer script, setup Make target, Python extension, CMake, scikit-build-core or dependency-environment changes.
- Preserve existing Python OpenCV/Open3D/GTSAM dependencies and OpenMVS integration.
- Configure an optional `CAMPERVAN_RTABMAP_BIN_DIR` through the existing `Settings`/`load_settings` boundary. It names
  the directory containing both CLI binaries, not a particular platform or installation format. No value is required
  for the standard macOS installation. An explicit directory is authoritative: missing tools fail without fallback.
- No global PATH/DYLD/shell-profile changes, Homebrew fallback, new service, scheduler or package-management framework.
- No tests, service launches, browser automation, app-code changes or capture processing during planning.
- If the scoped subprocess environment cannot run the supplied binaries, report the actual failure. It does not
  authorize compilation, binary modification, security-setting changes or another packaging project.

## Established facts and remaining uncertainty

The official `RTABMap-0.24.2-Darwin-Tahoe-Apple-Silicon-cv4.dmg` was downloaded, publisher checksum verified, and its
intact `RTABMap.app` copied into `/Applications`. The installer was unmounted and deleted. No app was launched during
installation and no security settings changed.

| Item | Observed value |
| --- | --- |
| DMG SHA-256 | `e1ada2b05fb274287b6a3d8f3785224afc9ba13422b948500afad2d7e7d11872` |
| Download size | 211,784,074 bytes (about 202 MiB) |
| Bundle size | `du -sh` reported 677 MiB during inspection |
| Exporter | `/Applications/RTABMap.app/Contents/bin/rtabmap-export` |
| Reprocessor | `/Applications/RTABMap.app/Contents/bin/rtabmap-reprocess` |
| Libraries | `/Applications/RTABMap.app/Contents/Frameworks` |
| CLI linkage | Absolute Homebrew dependency names and `@rpath` RTAB-Map references remain in the supplied tools |
| Replacement files | All directly referenced Homebrew dylib basenames and Qt framework binaries were found in the app |
| Exporter signature | Ad hoc/linker-signed, flags `0x20002`; no hardened-runtime flag shown by `codesign -dv` |

Apple's installed `dyld(1)` manual documents `DYLD_LIBRARY_PATH` leaf-name lookup and `DYLD_FRAMEWORK_PATH` framework
lookup before the encoded install paths, with restrictions for protected executables. This supports trying a
process-local environment before modifying any binary. Successful loading and Homebrew independence are not yet
established: the earlier unconfigured `--version` attempt was interrupted without usable output.

The upstream distribution is versioned, checksum-published, Apple Silicon-native and includes both required tools
and their libraries. It is the selected candidate. No subscription, new package manager or source build is required
by this plan. Retain upstream notices; official distribution is not itself a security audit or compatibility proof.

## Scope traceability

| Outcome | Owner and evidence |
| --- | --- |
| N1: no Homebrew requirement | Task 1: actual CLI output and loaded-library paths; Task 2: real import |
| N2: settings/tags/sessions/sources | Task 2: unchanged arguments, representative multi-capture run and input hashes |
| N3: downstream compatibility | Task 2: existing validators, published assets and Gert's visual inspection |
| N4: provenance/footprint/notices | Task 1: version, executable hashes and bundle details; Task 2: setup docs |

## Task 1: Establish that the installed CLI tools run with bundled libraries

**Spec coverage:** N1, N4 under the superseding decisions above.
**Changes:** evidence in this Flow folder only. No installation or binary modifications.

- [ ] Run the two absolute tool paths with `--version`, supplying `DYLD_LIBRARY_PATH` and `DYLD_FRAMEWORK_PATH` equal
  to `/Applications/RTABMap.app/Contents/Frameworks` only in each child process's environment. Do not export variables
  globally, launch the GUI or change Gatekeeper/quarantine. Confirm actual version and g2o support; report any macOS
  approval requirement plainly. If an invocation stalls, stop it and inspect the actual cause rather than retrying.
- [ ] For these same invocations, add `DYLD_PRINT_LIBRARIES=1` to the child environment and retain dyld diagnostics.
  Inspect actual resolved library paths; non-system libraries must resolve inside the app, with none loaded from
  Homebrew or `/usr/local`. Read `otool -L`/run paths only as needed to explain a named loader failure. Do not assume
  the existence of bundled files proves their runtime use. Remove diagnostic printing for normal processing.
- [ ] Record actual output/status, app version, two executable SHA-256 values, release URL/checksum, installed bundle
  size and notices location. If unsuccessful, stop dependent implementation with the precise failure. No automatic
  alternative build, relocation or security bypass.

## Task 2: Use the verified executables in the existing scan pipeline

**Spec coverage:** N1–N4, shared C1/C5.
**Files:** `src/campervan/scans.py`, `src/campervan/settings.py`, `README.md`, `docs/photogrammetry.md`; evidence in this
Flow folder. The settings addition is the existing configuration boundary's direct contract, not a new config system.

- [x] Add optional `rtabmap_bin_dir: str | None = None` to the existing `Settings`, loaded from
  `CAMPERVAN_RTABMAP_BIN_DIR`. Keep configuration optional and load it through the same boundary in the processing
  worker. Existing inherited subprocess environments carry the setting; do not duplicate it in capture/geometry data.
- [x] Add a small resolver in `scans.py` for only `rtabmap-export` and `rtabmap-reprocess`. If the directory is
  configured, expand/resolve it and require the requested executable there. Otherwise on macOS use
  `/Applications/RTABMap.app/Contents/bin`; on Linux use normal PATH discovery. Return absolute executable paths before
  any subprocess changes directory. Missing-tool messages identify the selected location and optional setting. No
  fallback from a configured directory, no implicit Homebrew lookup on macOS, and no CAD startup-time dependency check.
- [x] Add one helper returning the child environment. Only on macOS, when the selected tools are in an app bundle's
  `Contents/bin` and its sibling `Contents/Frameworks` exists, set both DYLD search paths to that Frameworks directory.
  Derive the directory from the resolved tools, allowing the app to move. On Linux or for a non-bundle installation,
  use the normal inherited environment without injecting macOS library settings. Use the helper for RTAB-Map version
  queries, export and reprocessing only. Do not mutate `os.environ` or affect OpenMVS/Python reconstruction.
- [x] Extend `native_command(command, log, cwd=None, *, env: dict[str, str] | None = None)` to forward the optional
  environment to its existing `subprocess.Popen`. Existing callers keep inherited environments by default. Replace
  only the RTAB-Map executable heads/PATH checks and supply the verified environment to the three RTAB-Map call sites.
  Keep logs, errors, cancellation, worker ownership and stage names intact.
- [x] Preserve all arguments and algorithms: `-abort_disconnected_sessions --Optimizer/Strategy 1`, marker dictionary
  20, tag-size conversion from mm to metres, export pose format 11 and existing `pose_source` values. Preserve the
  string `manifest["versions"]`; add native provenance with installed app version, explicit tool paths and executable
  hashes. Keep original DBs/copies, graph information, frames, confidence, calibration, optical poses and publication.
- [ ] Run one representative real multi-database operation using the existing CLI, a fresh output and the three
  original `data/261107-*-van-int.db` files, with `--voxel-mm 10 --sdf-trunc-mm 50 --tag-family 36h11 --tag-size-mm 80`.
  Record source hashes before/after, actual session/tag outcomes, loaded-library evidence and processing/publication
  logs. Reuse this run; do not repeat it for another reviewer or add a second reconstruction simply for coverage.
- [ ] Use existing runtime validators and Gert's visual inspection of the mesh/tags in the existing Scan tab. No test
  suite, broad build/verification campaign, browser automation or service launch. State any unexercised disconnected
  input and photo-texturing limitations. An observed failure does not authorize compiling or changing algorithms.
- [x] Document the ordinary installation: download the pinned official DMG, verify checksum and drag `RTABMap.app`
  into `/Applications`; the existing `uv sync --locked --extra scan` installs only Python scan dependencies. Explain
  that the app supplies the native libraries, CAD-only use needs no RTAB-Map, and the child environment is automatic.
  Record installed size and actual compatibility evidence. No native installer framework, purge commands or rebuilds.
  Document the optional `CAMPERVAN_RTABMAP_BIN_DIR=/path/to/bin` override using the existing settings convention. It
  requires no environment-file edits. Record resolved executable paths in provenance, so another machine's directory
  is visible without being embedded into reusable capture data. Linux runtime compatibility is not claimed until
  exercised on Linux; this change makes tool discovery configurable rather than adding a Linux packaging project.

## Self-review and phase boundary

The installation is already complete. Two bounded tasks remain: establish the installed CLI launch environment,
then make the small pipeline change and process representative captures. This plan preserves the existing data,
logging and job owners and does not change the installed bundle. Only this plan was edited; implementation has not
started. The key unproven point is actual runtime loading under the process-local environment.

Sources: [official release](https://github.com/introlab/rtabmap/releases/tag/0.24.2),
[release assets/checksums](https://github.com/introlab/rtabmap/releases/expanded_assets/0.24.2), direct bundle inspection,
the installed Apple `dyld(1)` manual, and [Apple dynamic-library guidance](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/DynamicLibraryUsageGuidelines.html).
