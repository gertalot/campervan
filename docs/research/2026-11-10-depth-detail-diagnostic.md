# Where surface detail is lost

Read-only diagnostic of `.local/scans/capture-fdfb86a1-db42-4087-8863-8f26568da3c5`, prompted by rounded floor and
sliding-door features in both 5 mm and 2.5 mm full-resolution meshes. No reconstruction or capture data was modified.

## Direct observations

Inspected saved RGB, original exported depth and confidence for frames 916, 922, 385 and 501 near tag 18. Unprojected
depth using each frame's calibration and computed surface-normal shading directly from adjacent depth samples, without
fusion, denoising or mesh simplification. Compared against the original 5 mm full mesh raycast from the same cameras,
at the same depth-image dimensions and with the same normal-shading calculation.

- Floor stampings visible in the photographs are already poorly represented in the individual saved depth surfaces.
  Rounded floor/sill transitions are present before our fusion, not introduced solely by a later mesh operation.
- Applying the confidence threshold removes samples but does not account for the widespread rounded appearance.
  Frame 916 retains 46,206 of 49,152 samples; frame 922 retains 42,431. Rejected pixels appear blank in the figures.
- Fusion changes boundaries and surface noise further; it does not restore the missing photographic floor relief.
- Current reconstruction code applies no separate geometric smoothing filter. Full meshes are saved before cleanup
  and quadric simplification. TSDF integration itself averages signed-distance observations.

Figures and numerical arrays are retained in `.local/experiments/depth-diagnostic-20261110/`:
`frame-916.png`, `frame-922.png`, `frame-385.png`, `frame-501.png`, matching NPZ arrays, `summary.json`, and
`inspect_depth.py`. Surface-normal brightness shows orientation, not measured height; these figures are not physical
ridge-depth measurements. Invalid raycast/background pixels produce gradient warnings and are excluded from statistics.

## Independent cross-view agreement diagnostic

Detected AprilTag 18 directly in photographs 173, 795, 916, 922 and 976 using OpenCV's AprilTag 36h11 dictionary.
Compared detected corner-average image centres with projections of the run's saved tag position. Residuals range from
3.9 to 15.4 pixels at 720 × 960 image resolution. Sampled original depth at the corresponding detected centres and
transformed these estimates through each saved camera pose. Maximum pairwise separation is **19.7 mm**.

This combines depth uncertainty, pixel sampling, detection and calibration/pose disagreement. It does not isolate
camera error or independently establish true metric accuracy. Corner-average centres approximate projected tag
centres, especially under perspective. The result demonstrates centimetre-scale cross-view disagreement at this
reference; it is not a universal bound for the entire scan.

The blurred frame 501 has a particularly large depth-versus-fused-view discrepancy, but no detected tag in that
image was available to corroborate its cause. Do not label that discrepancy as a proven pose error.

Tag observations and annotated images are in `tag-projections.json` and `tag-projection-*.jpg` in the same directory.

## Source verification and limits

Current upstream RTAB-Map iOS reads `sceneDepth`, clones incoming floating-point depth, scales confidence 0/1/2 to
0/50/100 and rotates arrays for orientation. The traced ingress does not spatially smooth depth. The optional
Smoothing setting is used in cloud/mesh-generation paths, not this ingress. This does not establish every downstream
database conversion, the exact installed iOS version, or Apple's internal depth estimation processing.

- [RTAB-Map ARKit input](https://github.com/introlab/rtabmap/blob/master/app/ios/RTABMapApp/RTABMap.swift#L263)
- [iOS native bridge](https://github.com/introlab/rtabmap/blob/master/app/ios/RTABMapApp/NativeWrapper.cpp#L288)
- [Shared mobile application](https://github.com/introlab/rtabmap/blob/master/app/android/jni/RTABMapApp.cpp)
- [Mobile camera data handling](https://github.com/introlab/rtabmap/blob/master/app/android/jni/CameraMobile.cpp)
- [Open3D TSDF integration](https://www.open3d.org/docs/release/tutorial/t_reconstruction_system/integration.html)

Conclusion: much of the observed detail loss is already present in the saved depth; fusion additionally combines
observations with measurable disagreement. There is no demonstrated single post-mesh smoothing switch to disable.
Reducing output voxel size cannot recover the absent source relief. This investigation does not establish an iPhone
hardware limit or the best detail obtainable from other capture settings or photographic reconstruction.
