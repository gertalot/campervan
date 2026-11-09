# Embedded RTAB-Map import and reprocessing

**Status:** approved requirements reorganised into a split draft; boundary review pending.
**Flow folder:** [embedded-rtabmap](./).
**Programme:** [scope index](../2026-11-09-scan-measurement-workflow/README.md).
**Binding shared contracts:** [shared ownership and interchange](../2026-11-09-scan-measurement-workflow/shared-contracts.md).
**Approved baseline:** [combined spec](../2026-11-09-scan-measurement-workflow/approved-combined-spec.md) §1, §3, §13.1 and AC13.
**Research/tool evaluation:** [native integration investigation](../2026-11-09-scan-measurement-workflow/rtabmap-integration-research.md).

## 1. Outcome and closed boundary

Process the phone's databases through app-managed RTAB-Map libraries so Homebrew RTAB-Map and otherwise-unused
Homebrew dependencies can be uninstalled. Preserve RTAB-Map's database decoding, marker detection and multi-session
registration; do not replace its processing with new SLAM algorithms. This is one native importer replacement.

Use the existing scan settings, processing worker, progress/log owner and reconstruction/publication contracts.
Changes are confined to the native package/build integration, scans.py's native adapter calls, required dependency
configuration and setup documentation. No measurement algorithms, semantic recognition, stage-panel redesign,
region editor, new services or app-wide package system belong here. Original databases remain unchanged.

## 2. Required native integration

Use a version-pinned minimal native build, initially targeting the existing macOS/Apple Silicon and Python 3.13
environment. Expose only the import/reprocessing operations the scan pipeline needs through a Python extension,
running inside the existing processing worker rather than adding a service or invoking the Homebrew tools.
Preserve original inputs, frame IDs, depth/confidence, calibration, optical transforms, graph constraints and saved
pose semantics. Reuse upstream processing orchestration where needed; a binding must not silently change session
joining, landmark handling or disconnected-session behavior. Keep the current g2o reprocessing strategy initially;
switching to GTSAM here is a separate algorithmic decision, not required to remove Homebrew.

Exclude the desktop GUI, visualization and unused capture SDKs/integrations. PCL and OpenCV remain required native
dependencies; their own builds must also exclude unnecessary integrations. Linking the existing Homebrew core or
copying a library that still resolves dependencies through `/opt/homebrew` does not meet this requirement. Package
required non-system libraries with relocatable loader paths and record versions, build options and license notices.
Retain the separate Python OpenCV/GTSAM/Open3D packages where used; do not assume their wheels expose a compatible
C++ SDK or can be linked as replacements for native build dependencies.

Establish the installed runtime footprint and temporary build/download space before large builds. Do not promise
a size saving before measuring the packaged dependency closure. Before removing Homebrew packages, demonstrate
real database import, tag detection and multi-session processing with dependency resolution confined to the package
and macOS system libraries. No automated test suite is introduced. Uninstalling Homebrew software is a separate
explicit cleanup action; preserve dependencies required by other installed software.

See [native integration investigation](../2026-11-09-scan-measurement-workflow/rtabmap-integration-research.md). No native build/binding has yet been made.

## 3. Existing mechanisms and preserved consumer contract

- `scans.py:process_scan` remains the processing entry point, operating on copies and preserving lineage/settings.
- Replace its exporter/reprocessor executable dependency through one narrow native adapter. Preserve the tag-family
  and size handling, current g2o strategy and disconnected-session behavior; avoid a permanent second importer path.
- Preserve `extract_frames`'s frame IDs, RGB/depth/confidence assets, intrinsics, image dimensions, depth units and
  camera-to-world optical poses in metres. Preserve original native graph/link information and landmark observations.
- `scan_graph.py`, `scan_rebuild.py` and `publish_reconstruction` keep their consumer roles. Existing limited
  version-aware graph reading need not be rewritten simply because the native call boundary changes.
- Use the existing `ScanProcessing` worker ownership and current frontend job presentation; do not create the shared
  staged UI here. Later workflow changes must consume the same outputs from this importer.

The research document records the accepted minimal core/binding direction and rejected Homebrew-linked wrapper,
wholesale closure copy and custom-registration replacement. Exact build recipe/binding signatures belong in this
scope's implementation plan; they cannot change the approved native algorithms, output semantics or runtime isolation.

## 4. Acceptance and independent verification

| ID | Required result |
| --- | --- |
| N1 | Real supported databases import/reprocess via app-managed RTAB-Map without either Homebrew executable or runtime libraries resolved from Homebrew. |
| N2 | Tag detection and multi-session joining preserve the existing settings, graph/frame conventions and disconnected-session behavior; sources are unchanged. |
| N3 | Existing downstream fusion, texture publication, saved tags and graph/correction consumers work through the preserved importer contract. |
| N4 | Installed runtime and temporary build/download footprint, selected dependency versions/features and license notices are recorded; no unmeasured saving is promised. |

N1 is the owner of original AC13. N2–N4 specify the already-approved §13.1 contract, not additional product scope.
Verify with the current importer/UI and bounded representative real captures; the other scopes are not prerequisites.
No test suites, service launches or automated browser interactions. Do not uninstall Homebrew software as part of
verification; any eventual removal is a separately authorised cleanup preserving other software's dependencies.

README/setup and docs/photogrammetry.md changes describe the app-managed import requirement and repeatable build/use.
This scope has its own implementation plan and completion evidence; it does not wait for scene or measurement UX.
