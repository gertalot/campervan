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
