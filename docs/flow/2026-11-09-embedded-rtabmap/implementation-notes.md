# RTAB-Map implementation evidence

## Task 1 — installed CLI launch, 2026-11-09

On macOS 26.6.2 (25G83), arm64, both commands below completed with exit status 0 from
`/Users/gert/Code/campervan`. Each received the variables only in its child environment. Full combined stdout/stderr,
including dyld diagnostics and the version feature list, is retained in the adjacent files.

```sh
env DYLD_LIBRARY_PATH=/Applications/RTABMap.app/Contents/Frameworks DYLD_FRAMEWORK_PATH=/Applications/RTABMap.app/Contents/Frameworks DYLD_PRINT_LIBRARIES=1 /Applications/RTABMap.app/Contents/bin/rtabmap-export --version > /tmp/campervan-rtabmap-export-version.log 2>&1
env DYLD_LIBRARY_PATH=/Applications/RTABMap.app/Contents/Frameworks DYLD_FRAMEWORK_PATH=/Applications/RTABMap.app/Contents/Frameworks DYLD_PRINT_LIBRARIES=1 /Applications/RTABMap.app/Contents/bin/rtabmap-reprocess --version > /tmp/campervan-rtabmap-reprocess-version.log 2>&1
```

Both report `RTAB-Map: 0.24.2` and `With g2o: true`. Export also printed a deprecation warning that launching without
required options adds `--cloud` for compatibility. No macOS approval prompt or error was observed for these invocations;
this does not establish behavior on a different installation or machine. Version output does not prove capture processing.

The diagnostics contain 431 app path entries and 630 system path entries per process, including the executable itself.
All path-bearing dyld entries are under `/Applications/RTABMap.app/`, `/System/Library/`, or `/usr/lib/`; none is under
Homebrew or `/usr/local`. For example, both load `Contents/Frameworks/librtabmap_core.0.24.2.dylib` and
`Contents/Frameworks/libg2o_core.0.2.0.dylib` within the app. Dyld also prints non-path `move loaded to delayed` notices.
Normal processing should omit `DYLD_PRINT_LIBRARIES`.

| Evidence | Value |
| --- | --- |
| App version | 0.24.2 reported by both tools; `CFBundleShortVersionString` and `CFBundleVersion` in Info.plist are empty |
| Export binary SHA-256 | `e29253b1a7e8d2cee9358c598d4977ef26d8b7e73023a388ee98dd718d18b075` |
| Reprocess binary SHA-256 | `9485a758c8c20e16cc06a6cb0df56146aacbd7afe04fe6aba8c7359aa63a1c1e` |
| Installed app size | `du -sh /Applications/RTABMap.app`: `677M` |
| Release | https://github.com/introlab/rtabmap/releases/tag/0.24.2 |
| DMG | `RTABMap-0.24.2-Darwin-Tahoe-Apple-Silicon-cv4.dmg`, SHA-256 `e1ada2b05fb274287b6a3d8f3785224afc9ba13422b948500afad2d7e7d11872` (prior verification recorded in plan; DMG removed) |
| Notices | No filenames matching `*licen*`, `*notice*`, or `*copying*` found under the installed app's Contents; upstream source license is https://github.com/introlab/rtabmap/blob/0.24.2/LICENSE. Do not infer that this covers third-party notices. |
| Export diagnostic SHA-256 | `e6b3ae3b7cc5b6714159966902270a1b9339ea7b6a642b8db80ef0a60a9a130e` |
| Reprocess diagnostic SHA-256 | `2db19ac736e8c5b385febe3c448519997c366da0e2b491be85e299ddf0d45b7d` |

Diagnostics: [export](rtabmap-export-version-dyld.txt), [reprocess](rtabmap-reprocess-version-dyld.txt).
The executable hashes identify the files used; the previously recorded DMG checksum is provenance, not a fresh check
of the deleted installer. No GUI, service, tests, or processing were run.

## Task 2 — installed tools in the scan pipeline, 2026-11-09

The single representative run used the installed app, with no configured binary directory, on macOS 26.6.2 arm64:

```sh
DYLD_PRINT_LIBRARIES=1 uv run --locked --no-sync --extra scan campervan scan process \
  data/261107-170546-van-int.db data/261107-171946-van-int.db data/261107-172733-van-int.db \
  --output .local/scans/embedded-rtabmap-20261109 --voxel-mm 10 --sdf-trunc-mm 50 \
  --tag-family 36h11 --tag-size-mm 80
```

The command exited 0, published `run.json` in 177.972 seconds, and reported 5/5 sessions linked to the last pose.
It retained 851 frames with confidence, omitted 39 lacking an exported pose, RGB, depth or calibration, and saved
17 tags (IDs 1–17). It exported `graph.json`, `frames.json`, `poses.json`, cloud, mesh and baked colour assets.
The log reports 609,163 original, 601,049 cleaned and 499,893 display triangles. Open3D warned about clamping PLY
colour values. The manifest records `rtabmap_merge_g2o`, version 0.24.2, both resolved tool paths and hashes.
The native log remains at `.local/scans/embedded-rtabmap-20261109/processing.log`; the full console, including
publication, is retained as [task-2-console.log](task-2-console.log). Working copies and merged DB remain in the run.

| Source database | SHA-256 before and after |
| --- | --- |
| `261107-170546-van-int.db` | `075749decf878628f7d22a2a26885742e9a2de5368b36623accc66690766b5aa` |
| `261107-171946-van-int.db` | `f7eba3e34e15557a4d2d33cdd64621d35fa3babaaf975ee9fd904dce96da9d2c` |
| `261107-172733-van-int.db` | `497ab331e415f7b8ad8ecba767fef8ea9800dfc2610d92f7cc6c8bdaf3f3700d` |

`shasum -a 256` also confirmed after the run that both executable hashes match Task 1 and the manifest. The scoped
library paths are the same as Task 1's successful version invocations. Although the command prefixed
`DYLD_PRINT_LIBRARIES=1`, no dyld diagnostics appeared in either processing log; the cause was not established.
Thus Task 1 documents startup library resolution for those binaries, but libraries dynamically loaded during actual
capture processing were not audited. No repeat processing run was made. Disconnected input, photo texturing, Linux
and the optional override were not exercised. Gert's visual inspection of the mesh and tags in the Scan tab remains
outstanding; publication does not establish visual correctness. No tests, builds, services or browsers were run.
