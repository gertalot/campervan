# Where the current scan loses detail

Read-only investigation on 11 November 2026 of the whole-van capture, following reports of rounded geometry and
blurred colour. No application code, uploaded database, scan output or browser selection was changed. Diagnostic
images and arrays occupy approximately 8 MB under `.local/experiments/depth-cause-20261111/`.

## Result under inspection

Read the existing Chrome app tab's selected controls, without interaction:

- Result: `run:capture-629b87f2-3bf3-4caa-877f-2871adb54368`, displayed as `interior-v1 — preview`.
- Layer: `shaded-full`, 633,017 triangles.
- Saved settings: 10 mm voxels, 50 mm signed-distance truncation band, confidence threshold 50.
- 1,071 frames were integrated. Photographs are 720 × 960; depth images are 192 × 256.
- This is the depth-based preview, not the failed and subsequently deleted whole-van photographic reconstruction.

The truncation band is not a 50 mm Gaussian smoothing radius. It bounds the signed distances accumulated by TSDF.

## Direct preservation evidence

Opened all four uploaded databases with SQLite `mode=ro`. Matched their depth records to the preview's merged
database by the original node timestamp, then compared the stored depth blobs byte for byte:

| Uploaded database | Original depth records | Byte-identical in merged database |
|---|---:|---:|
| `261109-130018.db` | 278 | 278 |
| `261109-125517.db` | 271 | 271 |
| `261109-131101.db` | 302 | 302 |
| `261109-130540.db` | 293 | 293 |
| Total | 1,144 | 1,144 |

The original depth blobs are PNGs encoding four bytes of each floating-point depth sample as four image channels.
Decoded them directly, reinterpreted those bytes as float32, and compared all 1,071 exported depth images with
their corresponding database arrays. Export retains their dimensions; the maximum absolute difference was
0.999512 mm. That conversion quantizes metres to integer millimetres but does not spatially blur the image.

Evidence: `identity-summary.json`. Thus neither RTAB-Map merging nor our depth export introduces the broad rounding
seen in the current result. This comparison does not prove what happened before the original database was recorded.

## Geometry before and after our reconstruction

Made a contact sheet across the capture and selected eight views: frames 46, 181, 270, 554, 604, 653, 896 and 1094.
These cover door surrounds, upper pillars, seats, body panels, wheel-well surroundings and dashboard, rather than
only the floor. For each view:

1. Decode the floating-point depth directly from the database, bypassing export and reconstruction.
2. Unproject it with the frame's depth-scaled calibration.
3. Calculate local surface-normal shading from adjacent samples, without denoising or mesh simplification.
4. Repeat with only high-confidence samples (100).
5. Raycast the saved full mesh from the same camera, at the same depth-image resolution, using the same shading.

Rounded boundaries and missing photographic relief are present in the database depth itself. Masking to high
confidence removes samples but retains that rounded shape. The full fused mesh additionally suppresses detail
visible in those depth arrays. For close views 554, 604 and 896, median lateral sample spacing `z / fx` is approximately
2.30, 2.69 and 2.19 mm respectively; the preview's mesh grid is 10 mm. These are sampling distances, not accuracy
measurements, and do not imply that every depth pixel is an independent LiDAR return.

Evidence: `area-{id}.png`, `area-{id}.npz`, `area-summary.json`, `coverage-contact.jpg`.

## Isolating grid size from the input

Used only the saved images and poses for two small areas, with no full reconstruction rerun:

- Pillar: frame 604 alone, or five real frames 602–606.
- Body panel: frame 896 alone, or five real frames 894–898.
- Reconstructed each at 10 mm and 2.5 mm voxels with the existing Open3D integration calls, confidence threshold 50,
  and truncation multiplier 5.
- Single-view extraction uses weight threshold 0.5 to inspect one observation; five-view extraction uses the normal
  threshold 3. Compare voxel sizes within the same view count, not across different extraction thresholds.

The 10 mm versions lose contours retained by the 2.5 mm versions of exactly the same input. Fine versions also
retain more depth noise. The five-view results show additional changes and missing support near boundaries.
This demonstrates loss caused by our meshing settings; it does not establish that 2.5 mm is the best final setting
or measure physical accuracy. Both areas together took approximately 1.5 seconds to process.

Evidence: `grid-604.png`, `grid-896.png`, their JSON records and depth arrays. Reproduction script:
`grid-diagnostic.py` in the diagnostic directory. The comparison images use nearest-neighbour display of shaded
depth samples. Raycast misses are masked; numerical gradient warnings at missing/background values do not enter
the reported valid-depth differences.

## Separate, definite colour-detail loss in our code

`scan_reconstruction.py:85` resizes every photograph to the depth image dimensions with `INTER_AREA` before colour
fusion: 720 × 960 becomes 192 × 256. This keeps only 7.11% as many pixels. Colour is then fused into voxels and stored
at mesh vertices. The baked-colour layer bakes these already reduced vertex colours; a 4096 texture atlas does not
restore photographic detail.

This explains a substantial part of the coloured mesh's blur independently of geometric relief. Preserving the
original files on disk does not mean their resolution is preserved in the displayed colour.

## Rendering and capture boundaries

`frontend/src/scan.ts` creates shaded variants of the same PLY assets used by the coloured layers. The materials
change lighting and colour, not vertex positions. Full mesh is saved before simplification and component cleanup.
Consequently neither display simplification nor a shader geometry filter explains rounding in `shaded-full`.

The traced RTAB-Map 0.24.2 iOS code reads ARKit `sceneDepth`, clones the incoming floating-point depth, and rotates
it with the camera orientation. Its Smoothing control belongs to cloud/mesh generation. All four databases record
`Mem/ImagePreDecimation=1`, `Mem/ImagePostDecimation=1` and `Mem/SaveDepth16Format=false`.

Apple documents that `sceneDepth` is generated by machine-learning fusion of LiDAR readings and RGB imagery.
It is a processed depth product, not raw laser returns. The data demonstrates rounding already in the recorded
capture product. It cannot distinguish every contribution within Apple's closed depth estimator from the physical
sensor response, nor establish a universal 2 cm limit. The exact App Store build used for recording is not independently
identified by the database schema version.

The user subsequently confirmed using the most recent releases. The App Store listing currently identifies iOS app
0.22.1 (the listing says its functionality is the same as 0.22.0). Traced the 0.22.1 source as well: `RTABMap.swift`
lines 270–271 reads `sceneDepth`, and `RTABMapApp.cpp` line 4651 clones the incoming float depth. This agrees with
the newer source inspected earlier. Version information is not a prerequisite for the demonstrated downstream
losses, and no version-specific regression has been established.

- [App Store version history](https://apps.apple.com/us/app/rtab-map-3d-lidar-scanner/id1564774365).
- [0.22.1 ARKit input](https://github.com/introlab/rtabmap/blob/0.22.1/app/ios/RTABMapApp/RTABMap.swift#L270-L271).
- [0.22.1 native float-depth copy](https://github.com/introlab/rtabmap/blob/0.22.1/app/android/jni/RTABMapApp.cpp#L4651).

Primary references:

- [Apple: generation of ARKit scene depth](https://developer.apple.com/videos/play/wwdc2020/10611/).
- [RTAB-Map 0.24.2 iOS depth input](https://github.com/introlab/rtabmap/blob/0.24.2/app/ios/RTABMapApp/RTABMap.swift).
- [RTAB-Map capture bridge and cloud generation](https://github.com/introlab/rtabmap/blob/0.24.2/app/android/jni/RTABMapApp.cpp).
- [RTAB-Map float-depth PNG compression](https://github.com/introlab/rtabmap/blob/0.24.2/corelib/src/Compression.cpp).
- [Open3D integration API](https://www.open3d.org/docs/release/python_api/open3d.t.geometry.VoxelBlockGrid.html).
- [Apple: higher-resolution AVFoundation LiDAR depth and filtering control](https://developer.apple.com/videos/play/wwdc2022/110429/).

## Established causes and remaining boundary

The current displayed quality has multiple causes: the saved depth product already lacks photographic relief;
our 10 mm TSDF mesh loses additional supported detail; and our colour path deliberately downsamples photographs
before fusion. Merely changing shaded versus coloured display cannot recover either lost geometry or colour.

These findings locate losses in this data and application. They do not justify blaming all degradation on the
iPhone hardware or promising that a different capture app will resolve every feature. Distinguishing hardware
response from Apple's depth estimator would require a new acquisition with an independent depth path or physical
reference; the existing databases contain only the already processed depth.

## Quantitative follow-up: averaging matters more than grid size here

The first grid comparison above demonstrates a visible sampling effect, but must not be interpreted as showing
that the 10 mm grid is the principal source of the whole melted appearance. A numerical comparison changes that
emphasis. On the intersection of valid, confidence-50-or-better reference pixels shared by all variants:

| Reference view | 10 mm, one view | 2.5 mm, one view | 10 mm, five views | 2.5 mm, five views | Existing full 10 mm mesh |
|---|---:|---:|---:|---:|---:|
| Pillar 604 | 0.694 mm | 0.565 mm | 1.880 mm | 1.774 mm | 7.704 mm |
| Body panel 896 | 0.708 mm | 0.579 mm | 2.925 mm | 2.866 mm | 6.538 mm |

Values are mean absolute changes in camera-axis depth relative to the original floating-point depth, not errors
against physical ground truth. There are 30,760 common pixels for 604 and 37,573 for 896. The source-to-export
millimetre conversion contributes some of the single-view difference. Finer sampling retains more noise as well
as contours. The full result changes the source surfaces much more than changing grid size within one view does.
More views can improve true accuracy while changing an individual noisy observation; these numbers alone are
not a physical accuracy ranking. Evidence: `grid-distortion.json`.

### Cross-view disagreement is present within captures

Reprojected high-confidence points in small pillar/body-panel reference regions into the other saved cameras.
Used only target points marked high confidence, viewing-direction differences under 30 degrees, depth residuals
under 50 mm, at least 30 accepted points, and at least 80% acceptance of projected reference samples. This reduces
but does not eliminate occlusion effects. Residuals combine depth, calibration and pose errors.

The pillar region has a median per-view absolute disagreement of 4.27 mm within its own capture and 8.07 mm in
49 views from another capture. The body-panel region has a median per-view absolute disagreement of 6.49 mm
within its own capture; the 90th percentile of per-view signed medians is 17.53 mm. Thus the effect cannot be
attributed solely to merging separate databases. Evidence: `crossview-depth.json`.

### Independent photographic reference

Detected AprilTags in a bounded sample of 242 photographs. Accepted 142 observations with minimum detected side
35 pixels, best IPPE reprojection error at most one pixel, at least nine high-confidence depth samples near the
tag centre, and agreement of the two candidate plane-depth estimates within 2 mm. For more reliable photographic
comparisons, restricted to sides at least 60 pixels and best reprojection error under 0.5 pixels (43 observations).

The initial plane comparison uses the configured 80 mm tag size and is conditional on correct physical printing,
flatness and calibration. It is retained in `tag-depth-independent.json`, but not used as proof of absolute accuracy.

Then triangulated each repeated tag's centre from its photographic detections and saved cameras, using the
homography-projected centre rather than the arithmetic corner average. This second calculation uses neither
printed marker size nor measured depth. Optimized the common 3D point against photographic reprojection error.

- Tag 5: five views, camera baseline up to 0.661 m, 1.89-pixel RMS reprojection residual. Recorded depth is
  5.47–8.23 mm farther than the photo-triangulated centre.
- Tag 6: five views from one capture, baseline up to 0.313 m, 1.59-pixel RMS residual. Recorded depth is
  11.73–20.01 mm closer than the photo-triangulated centre.
- Other accepted repeated tags also show discrepancies. Some have larger reprojection residuals, so cannot be
  treated as independent precision references.

These comparisons establish inconsistency between recorded depth and photographic geometry under the saved
camera/calibration model. They do not establish that every millimetre is a pure sensor error: camera calibration,
pose error and tag motion remain possible contributions. Linearized one-pixel triangulation sensitivities are
stored for interpretation, not presented as ground-truth uncertainty bounds. Evidence: `tag-bearing-consistency.json`
and `photo-triangulated-depth.json`.

The stored `scan` fields also contain ARKit tracked visual 3D points. Decoded them using their stored scan format
and local transforms and compared with corresponding depth pixels. There are 102,138 high-confidence comparable
samples across 1,064 frames; only 60.2% agree within 20 mm. Visual tracking points are themselves estimates,
not a trustworthy ground-truth surface. This channel confirms differing geometry products are recorded, but cannot
independently assign which product is physically correct. Evidence: `visual-points-depth.json`.

### Capture mechanism and independent primary evidence

The dense 256 × 192 API array is not a grid of 49,152 independent laser measurements. Apple's documentation
explicitly describes forming it from sparse LiDAR measurements and RGB using machine learning. The iPhone 13 Pro
characterization below describes 576 underlying range points and documents edge distortion in its measured dense
depth. The exact physical spot pattern of this user's iPhone 14 Pro Max was not measured in this investigation;
do not turn the older-device measurement into an unqualified specification for every iPhone.

Apple's ARKitScenes dataset supplies a separate example of native ARKit depth losing local structure compared
with FARO scanner ground truth: Figure 5, columns b and c, shows drawer seams and raised structure absent from
the native low-resolution depth. This is evidence of per-frame fidelity loss in the depth product across other
scenes, not a numerical bound for the van or proof of a universal minimum feature size.

- [Characterization of iPhone LiDAR sensing, section 2 and section 3.2](https://www.mdpi.com/1424-8220/23/18/7832).
- [ARKitScenes paper, Figure 5, page 9](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/66f041e16a60928b05a7e228a89c3799-Paper-round1.pdf#page=9).
- [Apple ARKitScenes depth documentation](https://github.com/apple-aiml-research/ARKitScenes/blob/main/depth_upsampling/README.md).
- [OpenCV planar pose estimation](https://docs.opencv.org/4.13.0/d5/d1f/calib3d_solvePnP.html).

### Final diagnosis of this pipeline

The relevant mechanisms are the use of a processed low-spatial-detail ARKit depth product instead of dense
photographic geometry, inconsistent observations being accumulated into an averaged TSDF surface, additional
sampling loss at 10 mm, and colour downsampling before fusion. RTAB-Map's database merging does not blur the
depth arrays, and no separate application mesh-smoothing filter causes the effect. The strongest measured
post-capture change in the inspected regions comes from multi-view integration, not voxel size alone.

This diagnoses why this capture-to-preview pipeline fails to preserve the photographed detail. It is not a
claim that the iPhone hardware cannot obtain better detail through another acquisition/processing path, nor
an identification of a particular undisclosed neural-network operation inside Apple's depth estimator.
