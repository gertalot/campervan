# Embedded RTAB-Map Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: use the execution sub-skill selected by `flow:implement` only after Gert
> invokes that phase. Flow's execution policy and repository instructions override generic testing, worktree, review
> and automatic-handoff defaults. Do not start implementation from this planning invocation.

**Goal:** replace the Homebrew RTAB-Map executable dependency with a local Python extension that preserves native
import/reprocessing and bundles its required numerical/vision code.

**Architecture:** a scan-only local Python package builds pinned native sources in a private prefix and exposes the
existing upstream Export/Reprocess operations through a narrow CPython extension. `scans.py` calls a typed adapter
inside its existing processing worker; its frame/graph/publication contracts and optional OpenMVS subprocesses stay
intact. Prefer static native libraries in the extension so Homebrew's shared-library closure is not shipped or loaded.

**Tech stack:** CPython 3.13 C API, C++17, scikit-build-core/CMake, upstream RTAB-Map 0.24.2, g2o/CXSparse, PCL,
OpenCV; existing uv, GTSAM/Open3D reconstruction and Make commands.

**Flow folder:** [embedded-rtabmap](./). **Spec:** [spec.md](spec.md).
**Shared contracts:** [C1–C5](../2026-11-09-scan-measurement-workflow/shared-contracts.md).
**Research and accepted alternatives:** [native investigation](../2026-11-09-scan-measurement-workflow/rtabmap-integration-research.md).

## Global Constraints

- Binding source: approved spec §§1–4, especially “This is one native importer replacement” and “Keep the current
  g2o reprocessing strategy initially”. Preserve all N1–N4 criteria and shared C1/C5 constraints.
- Runtime target is this macOS/Apple Silicon machine and standard CPython 3.13. Set native deployment target 14.0,
  architecture arm64, C++17 and Release consistently across the native build. This is not a cross-platform release.
- “Linking the existing Homebrew core or copying a library that still resolves dependencies through `/opt/homebrew`
  does not meet this requirement.” No Homebrew RTAB-Map/PCL/OpenCV/g2o headers, archives or shared libraries are build
  inputs. Only the selected project Python headers and Apple SDK/toolchain may sit outside the private source/prefix.
- Preserve original input databases, settings, native session joining, marker dictionary/size, optical poses,
  confidence and native graph information. The supported current database format remains 0.24.x; no schema migration.
- Python OpenCV/GTSAM/Open3D wheels remain separate consumers. Do not treat them as native SDKs or upgrade them here.
- No services, model runs/downloads, recognition changes, measurement algorithms, frontend redesign, package-manager
  replacement or Homebrew uninstall. Native source downloads/builds belong to later implementation, not this phase.
- **Never create or run tests**, including upstream test targets, pytest, CTest or frontend tests. Use compiler
  diagnostics, the existing runtime validators, required static checks and Gert's manual inspection. No test fixtures,
  test scripts or replacement verification framework. Do not access protected env files or `.beads` directly.
- Stay in the current directory/branch. Baseline is `1ece9b4` plus the working scan implementation: `scans.py`,
  `scan_graph.py`, `scan_processing.py`, `scan_rebuild.py` and `scan_texturing.py` are existing untracked working files;
  pyproject/lock/README/photogrammetry already have scan changes. Use those working versions, not an empty HEAD checkout.
  Before editing, record their identities and preserve unrelated CAD/project/frontend changes. Do not commit unrelated work.
- Task implementers own focused evidence below. Task 3's implementer owns final integration once on the resulting
  state: `make check`, package audit, the real multi-database import and manual viewer evidence. Reuse prior focused
  evidence only for unchanged inputs; no repeated import solely because another phase/reviewer starts.
- Record command, cwd, input hashes, package/build ID, result/exit status and limitations in
  `docs/flow/2026-11-09-embedded-rtabmap/implementation-notes.md` during implementation. This is an evidence record,
  not a new task tracker. No checks or builds have been executed by this plan-writing phase.
- Carry this context into the applicable [Flow execution policy](/Users/gert/.codex/plugins/cache/flow-private/flow/1.1.0/skills/implement/references/execution-policy.md)
  briefs/evidence records. The implementing phase owns its execution ledger; do not create a parallel tracker here.

## Scope Traceability

| Criterion | Implementation owner | Final verification owner and focused command |
| --- | --- | --- |
| N1 Homebrew-independent processing | Tasks 1–2 | Task 3: `uv run --locked --extra scan python -m campervan_rtabmap --audit`, plus the real multi-import below |
| N2 Tags/sessions/settings/source preservation | Tasks 1–2 | Task 3: existing `campervan scan process` on the three original DBs with `--tag-family 36h11 --tag-size-mm 80`; source hashes before/after |
| N3 Existing downstream consumers | Task 2 | Task 3: retained Task 2 single-import evidence, multi-import runtime graph/fusion publication and Gert's existing viewer inspection |
| N4 Footprint/build features/provenance/notices | Task 1 | Task 3: package `--audit` report plus `du` of the native build/package paths and factual setup documentation |

Every task includes its own spec coverage. The final multi-import is one operation covering N1–N3; do not separately
rerun it for each criterion. No criterion requires the scene-review or measurement-workflow deliverables.

## File and contract map

| Path | Responsibility |
| --- | --- |
| `native/rtabmap/pyproject.toml` | Scan-only `campervan-rtabmap` package; leave the root uv_build backend unchanged |
| `native/rtabmap/CMakeLists.txt` | Small upstream-dependency superbuild, then extension build/staging |
| `native/rtabmap/cmake/dependencies.cmake` | Pinned private native prefix and explicit feature flags |
| `native/rtabmap/sources.lock.json` | Fixed source versions/commits/URLs and recorded archive hashes |
| `native/rtabmap/patches/` | Only fixed upstream embedding/build-compatibility patches described in Task 1 |
| `native/rtabmap/src/CMakeLists.txt`, `module.cpp`, `embedded_tools.hpp` | CPython module and the two embedded upstream entry points |
| `native/rtabmap/python/campervan_rtabmap/` | Typed module facade, `__main__.py` info/audit entry point, build metadata and notices |
| `src/campervan/scan_native.py` | Lazy native import, fixed argument construction, typed build info and native log capture |
| `src/campervan/scans.py` | Replace the two RTAB-Map subprocess call sites and version/PATH checks only |
| `pyproject.toml`, `uv.lock`, `Makefile` | Optional local package source, locked dependencies and one native build target |
| `README.md`, `docs/photogrammetry.md` | App-managed native setup, exact retained inputs and measured footprint/limits |

No edits to graph math, TSDF/texturing, job ownership, API/frontend interactions or source data are planned. Inspect
their direct contracts to establish compatibility; inspection alone does not authorise changes.

## Review Focus

1. A packaged extension must not quietly use Homebrew transitive libraries or runtime plugin discovery. Task 1's
   feature flags and Task 3's recursive Mach-O audit own this risk.
2. Embedding console sources must not terminate Python on usage errors, collide on helper symbols, retain stale
   per-run globals or leave native signal handlers installed. Task 1's checked patches/bridge own this risk.
3. Confidence, depth units and optical transforms must not change while replacing the call boundary. Task 2 keeps
   the current parsers/validators; Task 3 inspects the resulting frame/graph metadata and published view.
4. Default g2o solver support and disconnected-session checks must survive the minimal build. Keep CXSparse and the
   upstream abort path; Task 3 records the actual joined-session outcome and any unexercised failure branch.
5. Optional native loading and C-level stdout/stderr capture must not break ordinary CAD imports, OpenMVS commands or
   worker error/progress logs. Task 2 owns this seam; the final static/runtime evidence covers its direct consumers.

## Task 1: Build the isolated native processing package

**Spec coverage:** N1, N2, N4; spec §2 and C1/C5.

**Files:** create `native/rtabmap/` files in the map above; add only the `scan-native` target to `Makefile`.

**Interfaces produced:**

```python
# campervan_rtabmap facade and matching _native.pyi; ordinary non-free-threaded CPython 3.13.
class NativeBuildInfo(TypedDict):
    rtabmap_version: str
    opencv_version: str
    pcl_version: str
    g2o_available: bool
    csparse_available: bool
    build_id: str
    version_text: str

def build_info() -> NativeBuildInfo: ...
def _run_export(argv: list[str]) -> int: ...
def _run_reprocess(argv: list[str]) -> int: ...
```

The private argument arrays include argv[0]. Calls execute native code in the existing worker, not an executable.
Only Task 2 constructs the supported operations. The package facade is typed (`py.typed` and `_native.pyi`).

- [ ] **Record the disk/build baseline before large downloads.** Record `df -h .`, sizes of this task's native
  caches (when present), expected compressed/expanded source sizes and a conservative object/build working-space
  estimate. Separate estimates from measured bytes; do not claim a final size or start a build that cannot fit.
  Keep all sources/build/prefix/wheel artifacts under `.local/native-rtabmap/`, never the Homebrew Cellar. Do not
  delete existing captures, model caches or unrelated files to make space.
- [ ] **Create the local PEP 517 package.** Name/version `campervan-rtabmap==0.1.0`, `requires-python >=3.13,<3.14`;
  use build-only `scikit-build-core==0.11.6`, `cmake==3.31.6`, `ninja==1.11.1.1`. Build the extension with the standard
  CPython C API, not a new full RTAB-Map binding library. The root build backend stays `uv_build==0.9.11`.
  Set a persistent scikit-build `build-dir` beneath `../../.local/native-rtabmap/build/{wheel_tag}` relative to this
  native project. Stage only the extension/facade/metadata/notices into the wheel, not headers, static archives,
  tools or source/build trees. This local wheel has no publishing/deployment step.
- [ ] **Pin and assemble the native dependency recipe.** Use the source inventory below. Store source archive hashes
  when fetching the pinned commits, before compiling; subsequent builds use the recorded hashes, never mutable
  branch heads. The Boost archive has the publisher's expected SHA-256 below. The one-purpose CMake superbuild uses
  `ExternalProject` dependency ordering, a private install prefix and a final inner extension project after its
  dependencies are installed. It is not a general package manager.

| Component | Pin | Required build content |
| --- | --- | --- |
| RTAB-Map | 0.24.2, `8cd2f81a735722402d1e220147c4e83a1a746eaf` | core/utilite and resource generation; no installed applications/tools |
| OpenCV | 4.12.0, `49486f61fb25722cbcf586b7f4320921d46fb38e` | core/imgproc/imgcodecs/features2d/flann/calib3d/photo/stitching/video/videoio/highgui/objdetect, with required transitive modules; objdetect supplies ArUco/AprilTag |
| PCL | 1.15.1, `3346843ea6b97697a1577293aa9cdf236b5c7ffb` | common/io/octree/kdtree/search/surface/filters/registration/sample_consensus/segmentation and their declared features/ml/geometry dependencies |
| g2o | 20241228_git, `eec325a1da1273e87bc97887d49e70570f28570c` | core/stuff, standard 2D/3D/SBA/ICP/Sim3 types and Eigen/PCG/CSparse solvers; no apps/viewers |
| SuiteSparse | v7.8.3, `d3c4926d2c47fd6ae558e898bfc072ade210a2a1` | only `suitesparse_config;cxsparse`; not the whole SuiteSparse library collection |
| Eigen | 3.4.0, `3147391d946bb4b6c68edd901f2add6ac1f31f8c` | headers/config only |
| FLANN | 1.9.2, `c50f296b0b27e14667d272b37acc63f949b305c4` | static C++ library; no Python/Matlab/C bindings, examples or docs |
| LZ4 | v1.10.0, `ebb370ca83af193212df4dcbadcc5d87bc0de2f0` | static library only |
| Qhull | 2020.2, `613debeaea72ee66626dace9ba1a2eff11b5d37d` | static reentrant/C++ libraries used by PCL surface code |
| Boost | official 1.86.0 `boost_1_86_0.tar.gz` | headers and static iostreams; disable optional compression-library discovery except SDK zlib |

Boost SHA-256: `2575e74ffc3ef1cd0babac2c1ee8bdb5782a0ee672b1912da40e5b4b591ca01f` from the publisher's archive metadata.
Use official project source hosts referenced below. OpenCV supplies its vendored JPEG/PNG dependencies; SDK zlib,
SQLite and system frameworks can remain system dependencies. Retain PCL's vendored cJSON notices where used.

- [ ] **Make the minimal/static configuration explicit.** Common: static libraries, PIC, consistent arm64/SDK/standard,
  hidden symbols, no fast-math change. Disable every upstream test/example/benchmark target (RTAB-Map
  `BUILD_TESTING=OFF`, `BUILD_PERF_TESTS=OFF`; FLANN `BUILD_TESTS=OFF`; g2o `BUILD_UNITTESTS=OFF`; PCL global tests OFF).
  OpenCV: disable GUI backends, video backends/plugins, OpenCL/CUDA/IPP, GStreamer/FFmpeg, GAPI/DNN and unwanted image
  codecs; keep highgui/videoio API modules without backend integrations because RTAB-Map expects their headers/APIs.
  PCL: `PCL_SHARED_LIBS=OFF`, `WITH_VTK=OFF`, `WITH_QT=NO`, CUDA/OpenGL/GLEW/libusb/PCAP/OpenNI/OpenNI2/OpenMP OFF;
  set `WITH_PNG=OFF` (image export uses OpenCV), `WITH_SYSTEM_CJSON=OFF`; retain Qhull, SDK zlib and required numeric
  components, and turn off unrelated apps/tools/visualization/recognition/
  people/tracking/outofcore/simulation/stereo/GPU components. Keep normal point-type support, not an unproven reduced set.
  g2o: CSparse ON, CHOLMOD/OpenGL/logging/OpenMP/apps/examples/benchmarks OFF. SuiteSparse: only the two listed projects,
  shared libs and OpenMP OFF. RTAB-Map: `WITH_QT=OFF`, `WITH_G2O=ON`, unrelated optimisers/mappers/capture SDKs,
  Python/Torch/PDAL/Open3D/OctoMap integrations OFF, `BUILD_APP/TOOLS/EXAMPLES=OFF`; marker detection uses OpenCV.
  Retain the existing g2o strategy and default CSparse solver; do not override them to avoid compiling a dependency.
- [ ] **Confine dependency discovery.** Pass only private prefix package configs/libraries, disable CMake package
  registries, ignore `/opt/homebrew`, `/usr/local` and `/opt/local` native prefixes, and prevent optional plugin/backend
  autoload. Explicitly bind source dependency paths; a missing private library fails configuration instead of falling
  back to a system package. For FLANN's old pkg-config-only LZ4 lookup, use one checked source patch replacing it with
  private-prefix `find_path(LZ4_INCLUDE_DIRS lz4.h)`/`find_library(LZ4_LIBRARIES lz4)`; no Homebrew pkg-config prerequisite.
  Any required compile compatibility patch stays local, pinned and algorithm-neutral; never patch numerical behavior.
- [ ] **Embed the two upstream tool entry points.** Compile the pinned `tools/Export/main.cpp` and
  `tools/Reprocess/main.cpp` as extension implementation sources, preserving their applicable processing flow.
  Per-source compiler definitions rename `main` to `campervan_export_main` / `campervan_reprocess_main` and
  `showUsage` to unique names to avoid their global-symbol collision. Do not ship either executable or expose their
  unrelated cloud/mesh operations as new product features. One checked patch per source replaces its usage-helper
  `exit(1)` with a C++ exception; validate the expected single site. Catch native exceptions at the C boundary after
  restoring the GIL. No `setjmp`, command shell or process exit for ordinary errors.
  Reset Reprocess's per-run counters/containers/`g_loopForever`/`exportPoses` at entry and restore prior signal handlers
  on return/exception; this preserves repeated in-process invocation without changing session algorithms. Use the
  pinned source's closed global inventory (from `g_loopForever` through `sessionCount`), not a generic state framework.
  Keep argument storage mutable/stable with a trailing null pointer. Release the GIL only around native execution;
  perform Python argument conversion and result/error creation while holding it. Flush native stdio before/after calls.
- [ ] **Implement metadata and package audit.** `build_info()` reports compiled RTAB/OpenCV/PCL versions, g2o/CSparse
  availability, a source/options/patch build ID and version text. Ship `build-info.json` with pins/hashes/options and
  selected license notices. `python -m campervan_rtabmap --info` prints those facts; `--audit` additionally locates the
  installed extension, recursively resolves `otool -L`/`LC_RPATH` and reports package bytes and any external edge.
  The expected static result depends only on Apple system libraries/frameworks. Reject unresolved or non-system/
  non-package edges, including Homebrew paths; do not silently bundle whatever the developer machine provides.
  Use normal macOS extension linking (`Python::Module`, no explicit libpython linkage); hide native symbols except
  the CPython module initializer to avoid interposition with the separately installed Python OpenCV/GTSAM wheels.
- [ ] **Build once and inspect.** Add `make scan-native` executing
  `CMAKE_BUILD_PARALLEL_LEVEL=2 uv build native/rtabmap --wheel --out-dir .local/native-rtabmap/wheels`.
  Run it only in implementation after the space record. Inspect the resulting local cp313/arm64 wheel with the package
  audit (install into the project's optional scan environment in Task 2; until then use `uv run --locked --with WHEEL
  python -m campervan_rtabmap --audit`, where WHEEL is the exact produced file). Record actual archive/source/build/
  installed sizes and compiler result. No capture processing yet; this task proves build/package isolation, not N2/N3.
- [ ] **Checkpoint this component** with only its new native files and Make target. No root build-backend migration.

## Task 2: Replace the RTAB-Map calls without changing scan data contracts

**Spec coverage:** N1, N2, N3; spec §3 and shared C1/C5.

**Files:** create `src/campervan/scan_native.py`; modify `scans.py`, optional dependency/source configuration in
`pyproject.toml` and `uv.lock`. Read existing graph/rebuild/texturing/worker callers; change none unless a concrete
direct-contract incompatibility is demonstrated and recorded.

**Interfaces consumed:** Task 1's typed package functions. **Interfaces produced:**

```python
def native_build_info() -> NativeBuildInfo: ...
def export_capture(database: Path, output: Path, log: Path) -> None: ...
def reprocess_captures(
    databases: list[Path], output: Path, log: Path, *,
    tag_family: Literal["36h11"] | None, tag_size_mm: float | None,
) -> None: ...
```

- [ ] **Register the optional local package.** Add `campervan-rtabmap==0.1.0` to the existing scan extra and its local
  source under `[tool.uv.sources]`, path `native/rtabmap`. Regenerate the lock with `uv lock`; install through
  `uv sync --locked --extra scan`. Ordinary CAD setup must not build/import the native package. Use lazy loading
  in `scan_native.py` with the typed interface; unavailable native support raises a clear scan-setup error only when
  processing is requested. No required runtime path/env variable or automatic Homebrew fallback.
- [ ] **Construct only the existing fixed operations.** `export_capture` calls the embedded Export entry with
  `--images_id --poses_camera --poses_format 11 --opt 2 --output capture --output_dir OUTPUT DATABASE`.
  `reprocess_captures` supplies `-abort_disconnected_sessions --Optimizer/Strategy 1`, conditionally the existing
  `--RGBD/MarkerDetection true --Marker/Dictionary 20 --Marker/Length SIZE_M`, then the upstream ordered database list
  and output DB. Family/size remain validated as a pair; millimetres convert to metres exactly once. No shell,
  executable lookup, new registration algorithm or changed solver setting. Preserve native unsupported-input errors.
- [ ] **Preserve live native diagnostics.** Within the existing single worker, use a narrowly scoped FD-level tee:
  save stdout/stderr descriptors, redirect them to a pipe during the GIL-released native call, and have one reader
  thread forward bytes to the saved stdout and append `processing.log`. Flush C/Python streams before redirection
  and before restoring; restore descriptors and finish/drain the reader in `finally`, including native errors.
  Python `redirect_stdout` alone does not capture C++ `printf`. This serves the existing log contract, not a new job
  scheduler/readiness protocol. The reader preserves raw bytes; if writing a destination fails, keep draining the
  pipe and report the saved I/O failure after restoring descriptors, rather than blocking native execution on a full
  pipe. Nonzero native status raises an operation/status error referencing the retained log.
- [ ] **Change the exact existing call sites.** In `scans.py:process_scan`, remove the RTAB-only `shutil.which`
  checks and `rtabmap-export --version` subprocess; inspect `native_build_info` before creating outputs. Keep the
  “Native versions” stage and string `manifest["versions"]`; add structured `manifest["native_runtime"]` metadata.
  Check typed g2o/CSparse capabilities instead of regex-parsing a command's stdout. Keep “Merge sessions / detect tags
  (g2o)” and “Extract RGB-D and cameras” stages, pose_source values, copy behavior, saved tags and original graph flow.
  Replace only the corresponding native calls in `process_scan` and `extract_frames`. `extract_frames` still creates
  `working/extracted`, invokes export into it, reads the same pose/YAML/image names and runs its existing rigid-pose,
  RGB/depth/aspect/calibration validation. Do not alter external-pose matching or saved-tag suppression with those poses.
- [ ] **Keep direct consumers unchanged.** Preserve `frames.json` (`depth_scale=1000`, registered depth, IDs, relative
  asset paths and omissions), `poses.json` (`camera_to_world`, metres), source DB references, `graph.json` link ordering/
  information and saved-landmark interpretation. Keep `native_command` itself: `scan_texturing.py` still uses it for
  OpenMVS. Do not remove `subprocess` if remaining texturing/generic helper code needs it. No job/UI changes are needed.
- [ ] **Run focused static checks once:** `uv run --locked ruff check src/campervan/scans.py src/campervan/scan_native.py`
  and `uv run --locked ruff format --check src/campervan/scans.py src/campervan/scan_native.py`.
  Then perform the existing single prepared-DB operation once:

```sh
uv run --locked --extra scan campervan scan process data/van-interior-merged-tags.db \
  --output .local/scans/native-saved-poses --voxel-mm 10 --sdf-trunc-mm 50
```

Use a fresh output; if that path already exists, choose another and record it, without deletion/overwrite. Expected:
the saved-pose branch skips reprocessing, existing validators accept frames/calibration/optical poses, original graph
is retained and normal Open3D publication completes. Inspect actual `processing.log` errors and manifest/asset paths;
a “completed” message alone is not proof of correct rendering. Retain this run for final inspection, not another rerun.
Record source hashes before/after as read-only evidence, and explain any omitted frames using existing output reasons.
- [ ] **Checkpoint the adapter and only its required configuration/call-site changes.** Preserve all unrelated dirty files.

## Task 3: Establish the integrated native replacement and practical setup documentation

**Spec coverage:** N1–N4; owns final acceptance evidence for all criteria.

**Files:** update `README.md` (“Process an interior scan”) and `docs/photogrammetry.md` (native setup/import/CLI
sections); record evidence in this Flow folder. Task 1–2's closed file inventory remains available for fixes caused
by this implementation or blocking its native contracts. No unrelated production/documentation edits are admitted.

- [ ] **Inspect the installed package, not the build prefix.** Run
  `uv run --locked --extra scan python -m campervan_rtabmap --audit`. Record the resolved native closure, source/build
  ID and actual installed bytes; no `PATH` filtering is accepted as proof of library isolation. Check the wheel does
  not ship GUI/tools/source trees and compile configuration excludes native plugin backends. Retain the package in
  the managed project environment; no temporary references back to source-build libraries may remain.
- [ ] **Run the real multi-session/tag pipeline once**, through the current CLI and worker contracts:

```sh
uv run --locked --extra scan campervan scan process \
  data/261107-170546-van-int.db data/261107-171946-van-int.db data/261107-172733-van-int.db \
  --output .local/scans/native-multi-tags --voxel-mm 10 --sdf-trunc-mm 50 \
  --tag-family 36h11 --tag-size-mm 80
```

Record original source hashes before/after, selected build ID, merged-session/tag results, actual logs and publication
outcome. `pose_source` remains `rtabmap_merge_g2o`; tag detection must produce actual retained observations, not merely
a true build flag. Inspect the original graph and optical-transform metadata through current readers. Preserve
upstream disconnected-session rejection; if no real disconnected capture is exercised, state that limit and cite
the retained abort path rather than manufacture a test fixture or claim that failure branch ran. No requirement
for bitwise-identical meshes/optimised floats across different native builds is invented.
- [ ] **Establish final integration static evidence once with `make check`.** It contains Ruff, formatting, mypy
  and frontend type checking, not tests. Record every required check's actual result. Reproduce/classify failures;
  fix those caused by this work or within the native import's direct contracts. Report unrelated CAD/frontend issues
  without expanding the task. Do not run a test suite or repeat completed imports to satisfy another reviewer.
- [ ] **Have Gert inspect the saved and multi-session results in the existing Scan tab**, including tags, mesh and
  existing layer controls. Do not start services or a browser; ask Gert to start the normal Make command if needed.
  Do not automate UI interactions. Optional photo texturing remains the existing OpenMVS path; verify its unchanged
  call sites and do not rerun a nine-minute texturing job without an observed integration issue. Report that limit.
- [ ] **Update practical documentation.** Describe `uv sync --locked --extra scan`, first-build source/toolchain
  requirements, private build location, local wheel rebuild via `make scan-native`, initial source-build cost and
  measured installed/temporary footprint. Replace Homebrew RTAB-Map as a setup requirement; retain upstream tools
  only as optional historical/reference examples. Explain that existing saved runs and raw DBs remain usable, native
  processing still uses RTAB-Map/g2o, Python packages remain separate, and Homebrew cleanup is not performed here.
  Do not rewrite recognition, measurement UX or other scopes' descriptions. Record selected dependency notices
  (including CXSparse and any vendored codecs/cJSON) rather than asserting one license covers the entire package.
- [ ] **Record final dispositions and checkpoint this bounded delivery.** Keep source failures, unavailable manual
  inspection or isolation failures visible; an incomplete required criterion prevents claiming completion. The plan
  authorises no purge command. A later user request can remove Homebrew RTAB-Map/dependencies after this evidence exists.

## Sources and planning evidence

Read-only planning inspected the current working `scans.py`, graph/rebuild/texturing/worker callers, Makefile, root
packaging and scan documentation. Approved reuse/tooling evidence is in the linked spec/research. Existing Homebrew
headers/version listings were reference evidence only; no native build, install, scan, model run or test occurred.

- [RTAB-Map pinned source/API and tool entry points](https://github.com/introlab/rtabmap/tree/8cd2f81a735722402d1e220147c4e83a1a746eaf)
- [PCL 1.15.1 options](https://github.com/PointCloudLibrary/pcl/blob/pcl-1.15.1/cmake/pcl_options.cmake)
  and [Boost requirements](https://github.com/PointCloudLibrary/pcl/blob/pcl-1.15.1/cmake/pcl_find_boost.cmake)
- [g2o build/solver options](https://github.com/RainerKuemmerle/g2o/blob/20241228_git/CMakeLists.txt),
  [SuiteSparse component selection](https://github.com/DrTimothyAldenDavis/SuiteSparse/blob/v7.8.3/CMakeLists.txt)
- [CPython extension interface](https://docs.python.org/3.13/extending/extending.html),
  [scikit-build-core 0.11.6 metadata](https://pypi.org/project/scikit-build-core/0.11.6/),
  [CMake ExternalProject](https://cmake.org/cmake/help/v3.31/module/ExternalProject.html)
- [Boost source hash](https://archives.boost.io/release/1.86.0/source/boost_1_86_0.tar.gz.json)

CPython's existing C API is sufficient for argument arrays/status/metadata; no broad binding generator or handwritten
SLAM is needed. Scikit-build-core/CMake are build-only packaging glue for the approved native package, not a root
backend migration, new runtime framework or another package manager. Static source libraries preserve a clear
runtime-isolation target. These implementation choices do not claim a successful minimal build before compilation.

## Self-review and phase boundary

One author self-review completed: N1–N4 each has a final verification owner; the package/adapter signatures agree;
the recipe retains the default CSparse backend; the generic texturing helper is retained; optional native import,
native logging and static-check ownership are explicit. Tightened PCL's optional dependency flags and Task 3's fix
inventory during that review. No production code or checks were executed.

Final acceptance remains contingent on later evidence: especially static-link compatibility/footprint, tag/session
outcomes and Gert's model inspection. No plan-review subagents or extra verification processes are requested.
Stop after this plan; do not invoke implementation.
