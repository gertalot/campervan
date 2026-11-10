# Voxel resolution comparison

Compare the existing 5 mm reconstruction with a separate 2.5 mm reconstruction. This changes only `voxel_mm` in the
fusion settings. It does not repeat database merging, tag detection or camera optimisation.

Source: `.local/scans/capture-fdfb86a1-db42-4087-8863-8f26568da3c5` (1,068 RGB-D frames).
Result: `.local/scans/voxel-detail-20261110-2p5mm`, labelled **Voxel experiment — 2.5 mm**, in the source capture group.

The local repeatable script reuses source frames, poses and available graph data through hard links, so no original
image or database bytes are duplicated. It calls the existing reconstruction function without changing its defaults.
Truncation remains 25 mm and the confidence threshold remains 50. The run initially retained the 500,000-triangle
display budget, but generating that simplified copy was stopped after several minutes. A process sample confirmed
Open3D was in `SimplifyQuadricDecimation`. The already completed full fusion mesh was published directly instead.
Textures are not regenerated: this comparison concerns the shaded geometry.

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 uv run --locked --no-sync python -u \
  .local/experiments/voxel-detail-20261110/run.py \
  .local/scans/capture-fdfb86a1-db42-4087-8863-8f26568da3c5 \
  .local/scans/voxel-detail-20261110-2p5mm --voxel-mm 2.5
```

Choose an unused output path when repeating. The execution log is
`.local/experiments/voxel-detail-20261110/processing.log`. If display decimation is stopped after the full mesh and
cloud have been written, `publish_full.py` in the same folder accepts the same arguments and publishes those completed
assets without repeating fusion. This was the publication route used here; no completed total runtime is recorded.

The published full mesh contains **13,155,834 triangles and 6,788,970 vertices**, approximately 493 MiB on disk.
The point cloud is approximately 331 MiB. These are new geometry assets; source images/databases remain hard-linked.
The full mesh is before cleanup, matching the baseline's full-resolution layer. There is no simplified layer for this
result. Open3D reported clamped colour values while saving PLY assets; the comparison uses neutral shaded geometry.

Refresh scans, select the original result, choose **Shaded surface — full resolution**, and frame the floor. Switch to
**Voxel experiment — 2.5 mm**, retaining the full-resolution layer and camera position. Assess whether the floor ridges
become more recognisable, rather than treating increased triangle count as increased accuracy.

The original full mesh has 2,699,007 triangles (2,614,806 after cleanup). Neither this baseline nor the new reconstruction
establishes the actual ridge depth without an independent physical measurement.
