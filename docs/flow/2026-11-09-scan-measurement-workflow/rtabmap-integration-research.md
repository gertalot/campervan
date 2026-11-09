# App-managed RTAB-Map investigation — 9 November 2026

Status: source/dependency investigation; no native package built and no Homebrew software removed.

## Agreed outcome

The scan app should work after uninstalling Homebrew RTAB-Map and its otherwise-unused dependencies. Retain
RTAB-Map's existing processing algorithms in a minimal app-managed native package, exposed through a narrow Python
binding. Do not replace its registration/mapping implementation with application-specific SLAM code.

Embedding alone does not reduce disk use. Savings depend on excluding unnecessary libraries/features and packaging
only the required runtime artifacts. Actual package size is not established by this investigation.

## Current integration

`src/campervan/scans.py:extract_frames` calls `rtabmap-export` to obtain RGB, depth, confidence, camera calibration and
saved optical camera poses. `process_scan` calls `rtabmap-reprocess` for multiple databases or marker detection,
selecting g2o (`Optimizer/Strategy=1`), AprilTag dictionary 20 and the supplied physical tag size. It rejects
disconnected sessions and operates on copies, preserving original databases.

`scan_graph.py` already decodes original saved poses and links using a limited version-aware SQLite reader.
Python GTSAM handles subsequent measured-distance correction, while Python Open3D handles fusion/meshing. Native
RTAB-Map reprocessing and Python GTSAM correction are separate stages; this packaging change need not switch solvers.

## Upstream integration points

- The public [DBDriver API](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/include/rtabmap/core/DBDriver.h)
  exposes sensor data, calibration, node metadata, links and landmark observations. Native decoding can remain
  upstream-owned rather than duplicating compressed image/calibration formats in Python.
- [Reprocess](https://github.com/introlab/rtabmap/blob/0.24.2/tools/Reprocess/main.cpp) uses `DBReader`, `Rtabmap::init`,
  `Rtabmap::process`, session handling and final graph checks. Preserve the applicable orchestration, not just a
  nominal one-line call to `process`. Calling core classes without matching this behavior is not proven equivalent.
- The existing [exporter](https://github.com/introlab/rtabmap/blob/0.24.2/tools/Export/main.cpp) is the reference for
  optical poses, sensor-to-node transforms, confidence and exported frame conventions.
- The [maintainer's Python-wrapper answer](https://github.com/introlab/rtabmap/discussions/1310) reports no Python
  wrapper in July 2024. Current source exposes C++ APIs. Its `WITH_PYTHON` feature embeds Python-backed detectors and
  matchers; it is not the required Python-to-RTAB-Map interface. A scan-specific extension is still needed.

## Minimal-build findings

The pinned [0.24.2 build configuration](https://github.com/introlab/rtabmap/blob/0.24.2/CMakeLists.txt) permits a
headless core with `WITH_QT=OFF`, omitting PCL's visualization component. OpenCV and nonvisual PCL components remain
required. Desktop applications, examples, optional capture SDKs and PDAL/OctoMap integrations need not be shipped for
our offline RGB-D processing. Keep the currently used g2o and OpenCV marker capabilities initially.

This needs compatible minimal dependency builds too. Disabling RTAB-Map's GUI while linking broad Homebrew PCL or
OpenCV builds can retain unwanted transitive dependencies. Python OpenCV/Open3D/GTSAM wheels are not assumed to be
compatible development SDKs for this native package.

PCL's [I/O build](https://github.com/PointCloudLibrary/pcl/blob/pcl-1.15.1/io/CMakeLists.txt) lists VTK and sensor
integrations as optional dependencies, supporting investigation of a nonvisual build rather than assuming PCL
necessarily requires Qt/VTK. RTAB-Map also requests OpenCV highgui/video modules; a headless OpenCV build must retain
the expected APIs without bringing back desktop/video-backend dependencies unnecessarily. Exact feature choices
remain build work, not confirmed working configuration flags in this document.

The [Homebrew formula](https://github.com/Homebrew/homebrew-core/blob/master/Formula/r/rtabmap.rb) installs a much
broader collection, including Qt, VTK, PDAL and capture SDKs. The currently installed core's recursive `otool -L`
inspection reaches visualization, GIS, video/ML and sensor libraries even before loading the standalone GUI.
Machine-local dependency edges and size data are recorded at `.local/rtabmap-homebrew-linkage.json`. Unresolved
loader paths are recorded explicitly; this diagnostic is not a packaged-size estimate or proof of isolation.

Observed baseline: 361 unique resolved library/framework files, 623,463,184 bytes (about 595 MiB), and zero unresolved
edges after resolving each binary's `LC_RPATH`/`@loader_path`. The largest linked family is VTK (about 151 MiB).
These file sizes exclude headers, tools, plugin discovery, resources, caches and build artifacts, and are not the
amount reclaimable by uninstalling Homebrew packages. The diagnostic inspects linkage; it does not run scan processing.

## Bounded implementation direction

1. Build a pinned headless native dependency set and RTAB-Map core for this Mac/Python environment. Keep intermediate
   build/download space separate from measured installed runtime size; avoid concurrent large builds during inference.
2. Expose scan-specific extraction and reprocessing operations through one extension/adapter. Use existing scan
   settings, progress/log owner and worker process. Do not expose the entire C++ API or add another service.
3. Supply required non-system libraries beside the extension, with package-relative loader paths and recorded build
   options, dependency versions and license notices. Avoid dependency discovery from `/opt/homebrew` at runtime.
4. Replace `scans.py`'s native executable calls while retaining the downstream frames/graph/publication contracts.
   Preserve confidence, source node/session identity, original constraints and camera frame conventions.
5. Inspect actual loader resolution and run a bounded representative import/reprocessing operation on copies of real
   databases before claiming the package can replace Homebrew. No test suite or service launch is part of this work.
6. Only after the replacement works, separately remove Homebrew RTAB-Map and dependencies unused by other software.

The binding technology/build packaging, exact dependency feature set, installed size and time/space needed to build
are not yet established. No claim of a ready-to-install Python package or a tiny dependency-free binding is made.

## Choices assessed

| Choice | Decision and consequence |
| --- | --- |
| Minimal RTAB-Map core plus narrow binding | Agreed direction. Reuses established processing and database compatibility; requires maintaining a native build/package. BSD-3-Clause core; selected dependencies/features need their own notices/license review. No service, subscription or credentials required. |
| Bind the existing Homebrew core | Useful only as a temporary development reference. Fails the requested outcome if installed code still links to Homebrew libraries. |
| Copy the existing dependency closure wholesale | Could remove the package-manager requirement after relocation, but retains unnecessary features/space. Not the proposed minimal package. |
| Replace RTAB-Map with custom Python registration | Rejected for this change. Existing math/vision libraries do not automatically reproduce RTAB-Map's registration and graph construction; unnecessary algorithmic replacement. |

The baseline remains RTAB-Map 0.24.2, matching the installed tool and supported database schema. Upstream has public
source, API documentation and active changes; no independent security audit or future compatibility guarantee is
claimed. Pinning and a bounded adapter limit integration churn. A build recipe must be repeatable without making
Gert install the full desktop application again.
