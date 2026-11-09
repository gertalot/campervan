"""Automatic unlabelled region proposals for the scene-recognition feasibility trial."""

from __future__ import annotations

import argparse
import html
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from rgbd_geometry import observed_points, sample_mask, visible_box

SEGMENTER = "facebook/sam2.1-hiera-tiny"
REVISION = "de431c4043854a71d8101e17995dfe596bf101a5"


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def masks(args: argparse.Namespace) -> None:
    import torch
    from transformers import Sam2Model, Sam2Processor, pipeline

    run, output = args.run.resolve(), args.output.resolve()
    if output == run or run in output.parents:
        raise ValueError("Proposal output must be separate from the source reconstruction.")
    output.mkdir(parents=True, exist_ok=False)
    (output / "masks").mkdir()
    frames = json.loads((run / "frames.json").read_text())["frames"]
    if args.frames:
        lookup = {f["id"]: f for f in frames}
        selected = [lookup[int(v)] for v in args.frames.split(",")]
    else:
        selected = [frames[int(i)] for i in np.linspace(0, len(frames)-1, min(5, len(frames)))]
    settings = {"source_run": str(run), "frame_ids": [f["id"] for f in selected],
                "model": SEGMENTER, "revision": REVISION, "points_per_crop": args.grid,
                "points_per_batch": 16, "pred_iou_thresh": 0.88, "stability_score_thresh": 0.95,
                "min_area_fraction": args.min_area, "max_area_fraction": 0.85,
                "packages": {n: importlib.metadata.version(n) for n in ["torch", "transformers"]},
                "frames": []}
    save(output / "mask-settings.json", settings)
    torch.set_num_threads(4)
    processor = Sam2Processor.from_pretrained(SEGMENTER, revision=REVISION, token=False)
    model = Sam2Model.from_pretrained(SEGMENTER, revision=REVISION, token=False).to("mps").eval()
    generator = pipeline("mask-generation", model=model, image_processor=processor.image_processor, device="mps")
    for frame in selected:
        print(f"[Generate unlabelled masks: frame {frame['id']}]", flush=True)
        started = time.monotonic()
        image = Image.open(run / frame["rgb"]).convert("RGB")
        result = generator(image, points_per_crop=args.grid, points_per_batch=16,
                           pred_iou_thresh=0.88, stability_score_thresh=0.95)
        all_masks = np.asarray(result["masks"], dtype=bool)
        scores = result["scores"]
        scores = scores.detach().cpu().numpy() if hasattr(scores, "detach") else np.asarray(scores)
        rows, kept = [], []
        for index, (mask, score) in enumerate(zip(all_masks, scores, strict=True)):
            area = float(mask.mean())
            if not args.min_area <= area <= 0.85:
                continue
            y, x = np.nonzero(mask)
            rows.append({"index": len(kept), "raw_index": index, "score": float(score), "area_fraction": area,
                         "box": [int(x.min()), int(y.min()), int(x.max()+1), int(y.max()+1)]})
            kept.append(mask)
        stack = np.asarray(kept, dtype=bool).reshape(-1, image.height, image.width)
        np.savez_compressed(output / "masks" / f"{frame['id']}.npz", masks=stack)
        save(output / "masks" / f"{frame['id']}.json", rows)
        row = {"id": frame["id"], "raw_count": len(all_masks), "retained_count": len(kept),
               "seconds": round(time.monotonic()-started, 2)}
        settings["frames"].append(row)
        save(output / "mask-settings.json", settings)
        print(json.dumps(row), flush=True)
    print(f"[Automatic masks saved: {output}]", flush=True)


def assemble(args: argparse.Namespace) -> None:
    import open3d as o3d

    output = args.output.resolve()
    settings = json.loads((output / "mask-settings.json").read_text())
    run = Path(settings["source_run"])
    if run != args.run.resolve():
        raise ValueError("Mask proposals and source reconstruction differ.")
    frames_doc = json.loads((run / "frames.json").read_text())
    frames = {f["id"]: f for f in frames_doc["frames"]}
    poses = {int(k): np.asarray(v) for k, v in json.loads((run / "poses.json").read_text())["poses"].items()}
    selected = [frames[i] for i in settings["frame_ids"]]
    worlds = {f["id"]: observed_points(run, f, poses[f["id"]], frames_doc["depth_scale"]) for f in selected}
    registry: dict[tuple[int, int, int], int] = {}
    centers = []

    def voxels(points: np.ndarray) -> set[int]:
        keys = np.unique(np.floor(points / args.voxel_m).astype(np.int64), axis=0)
        result = set()
        for key in keys:
            cell = tuple(key.tolist())
            if cell not in registry:
                registry[cell] = len(centers)
                centers.append((key + 0.5) * args.voxel_m)
            result.add(registry[cell])
        return result

    candidates = []
    print("[Associate automatic masks with observed 3D points]", flush=True)
    for frame in selected:
        stack = np.load(output / "masks" / f"{frame['id']}.npz", allow_pickle=False)["masks"]
        rows = json.loads((output / "masks" / f"{frame['id']}.json").read_text())
        world, valid = worlds[frame["id"]]
        for row, mask in zip(rows, stack, strict=True):
            points = world[valid & sample_mask(mask, valid.shape)]
            footprint = voxels(points)
            candidates.append({"kind": "image_mask", "voxels": footprint,
                "image_frames": {frame["id"]}, "quality": row["score"],
                "views": [{"frame_id": frame["id"], "box": row["box"], "score": row["score"],
                           "pixels": int(mask.sum()), "mask_index": row["index"], "kind": "image_mask"}],
                "mask_source": {"frame_id": frame["id"], "index": row["index"]}})
    print("[Generate unlabelled geometric patches from original cloud]", flush=True)
    cloud = o3d.io.read_point_cloud(str(run / "cloud.ply")).voxel_down_sample(0.04)
    o3d.utility.random.seed(0)
    for plane_number in range(6):
        if len(cloud.points) < 300:
            break
        coefficients, inliers = cloud.segment_plane(distance_threshold=0.025, ransac_n=3, num_iterations=500)
        if len(inliers) < 300:
            break
        patch = cloud.select_by_index(inliers)
        labels = np.asarray(patch.cluster_dbscan(eps=0.12, min_points=8))
        xyz = np.asarray(patch.points)
        for component in sorted(set(labels) - {-1}):
            points = xyz[labels == component]
            if len(points) < 80:
                continue
            views = []
            for frame in selected:
                world, valid = worlds[frame["id"]]
                visible = visible_box(points, frame, poses[frame["id"]], world, valid, tolerance=0.06)
                if visible:
                    box, count = visible
                    views.append({"frame_id": frame["id"], "box": box, "score": 1.0,
                                  "pixels": count, "kind": "geometric_patch"})
            if views:
                candidates.append({"kind": "geometric_patch", "voxels": voxels(points), "quality": 1.0,
                    "image_frames": set(), "views": views, "plane": coefficients, "plane_index": plane_number})
        cloud = cloud.select_by_index(inliers, invert=True)
    print(f"[Conservatively associate {len(candidates)} candidate regions]", flush=True)
    parents = list(range(len(candidates)))
    group_frames = [set(c["image_frames"]) for c in candidates]

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    edges = []
    for i, first in enumerate(candidates):
        a = first["voxels"]
        if len(a) < 20:
            continue
        for j in range(i):
            second = candidates[j]
            b = second["voxels"]
            if len(b) < 20:
                continue
            intersection = len(a & b)
            iou = intersection / len(a | b)
            smaller_overlap = intersection / min(len(a), len(b))
            ratio = min(len(a), len(b)) / max(len(a), len(b))
            same_image = bool(first["image_frames"] & second["image_frames"])
            eligible = (iou >= 0.8 if same_image else iou >= 0.2 and smaller_overlap >= 0.6 and ratio >= 0.35)
            if eligible:
                edges.append((iou, i, j))
    associations = []
    for score, i, j in sorted(edges, reverse=True):
        a, b = root(i), root(j)
        if a == b:
            continue
        # Preserve competing nested hypotheses from the same image unless almost identical.
        if group_frames[a] & group_frames[b] and score < 0.8:
            continue
        parents[b] = a
        group_frames[a] |= group_frames[b]
        associations.append({"a": i, "b": j, "voxel_iou": score})
    groups = {}
    for index in range(len(candidates)):
        groups.setdefault(root(index), []).append(index)
    regions = []
    voxel_arrays = {}
    center_array = np.asarray(centers)
    for number, members in enumerate(groups.values(), 1):
        identifier = f"region-{number:04d}"
        footprint = set().union(*(candidates[i]["voxels"] for i in members))
        views = {}
        for i in members:
            for view in candidates[i]["views"]:
                key = view["frame_id"]
                if key not in views or view["pixels"] * view["score"] > views[key]["pixels"] * views[key]["score"]:
                    views[key] = view
        ordered = sorted(views.values(), key=lambda v: v["pixels"] * v["score"], reverse=True)
        voxel_arrays[identifier] = center_array[sorted(footprint)].reshape(-1, 3)
        regions.append({"id": identifier, "members": members, "kinds": sorted({candidates[i]["kind"] for i in members}),
                        "views": ordered, "voxel_count": len(footprint), "footprint": footprint,
                        "quality": max(candidates[i]["quality"] for i in members), "selected": False})
    np.savez_compressed(output / "region-points.npz", **voxel_arrays)
    remaining = list(regions)
    covered = set()
    chosen = []
    while remaining and (not args.max_regions or len(chosen) < args.max_regions):
        def score(region: dict) -> float:
            footprint = region["footprint"]
            if footprint:
                novelty = len(footprint - covered) / len(footprint)
                return (len(footprint) ** 0.5) * (0.25 + novelty) * (1 + 0.15*np.log1p(len(region["views"])))
            # Retain appearance-only proposals where depth is absent, including possible glass.
            return (max(v["pixels"] for v in region["views"]) / 100) ** 0.5
        region = max(remaining, key=score)
        region["selection_score"] = float(score(region))
        region["selected"] = True
        chosen.append(region)
        covered |= region["footprint"]
        remaining.remove(region)
    prompt_file = Path(__file__).with_name("region-prompt.json").resolve()
    cases = []
    for region in chosen:
        views = region["views"][:2]
        cases.append({"name": region["id"], "frame_ids": [v["frame_id"] for v in views],
                      "regions": [v["box"] for v in views]})
    save(output / "automatic-cases.json", {"prompt_file": str(prompt_file), "cases": cases})
    serialised = [{k: v for k, v in r.items() if k != "footprint"} for r in regions]
    catalog = {"source_run": str(run), "frame_ids": settings["frame_ids"], "voxel_m": args.voxel_m,
               "raw_candidate_count": len(candidates), "region_count": len(regions), "selected_count": len(chosen),
               "selection": "Greedy 3D coverage with a size/shape-hypothesis diversity term; no category labels.",
               "max_regions": args.max_regions, "associations": associations, "regions": serialised,
               "note": "Tentative depth associations, not verified objects. Glass may measure surfaces beyond it. "
                       "Conservative voxel overlap is not the full MaskClustering view-consensus algorithm."}
    save(output / "proposals.json", catalog)
    (output / "previews").mkdir(exist_ok=True)
    columns, cell_w, cell_h = 6, 210, 300
    sheet = Image.new("RGB", (columns*cell_w, max(1, (len(regions)+columns-1)//columns)*cell_h), "#20242b")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=15)
    parts = ["<!doctype html><html lang='en'><meta charset='utf-8'><title>Automatic region proposals</title>",
             "<style>body{background:#20242b;color:#eee;font:16px system-ui;margin:2rem}"
             ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem}"
             "img{max-width:100%}article{border:1px solid #666;padding:.5rem}</style>",
             f"<h1>Automatic region proposals</h1><p>{len(candidates)} raw proposals; {len(regions)} tentative regions; "
             f"{len(chosen)} selected for the bounded recognition batch. All proposals retained below.</p><div class='grid'>"]
    for index, region in enumerate(regions):
        view = region["views"][0]
        image = Image.open(run / frames[view["frame_id"]]["rgb"]).convert("RGB")
        ImageDraw.Draw(image).rectangle(view["box"], outline=(255, 30, 30), width=5)
        image.thumbnail((200, 250))
        image.save(output / "previews" / f"{region['id']}.jpg", quality=90)
        x, y = (index % columns)*cell_w, (index//columns)*cell_h
        sheet.paste(image, (x+5, y+25))
        title = region["id"] + (" · selected" if region["selected"] else "")
        draw.text((x+5, y+5), title, font=font, fill="#96d7ff" if region["selected"] else "white")
        draw.text((x+5, y+275), f"{len(region['views'])} views · {region['voxel_count']} voxels", font=font, fill="white")
        parts.append(f"<article><strong>{html.escape(title)}</strong><img src='previews/{region['id']}.jpg' "
                     f"alt='Unlabelled automatic region'><p>{html.escape(', '.join(region['kinds']))}; "
                     f"{len(region['views'])} source views</p></article>")
    sheet.save(output / "automatic-proposals.jpg", quality=92)
    parts.append("</div><p>Red boxes are generated automatically. No target labels or manual coordinates were used.</p></html>")
    (output / "proposals.html").write_text("\n".join(parts))
    print(json.dumps({"raw_candidates": len(candidates), "regions": len(regions), "selected": len(chosen)}), flush=True)


def highlight(args: argparse.Namespace) -> None:
    """Replace box-only geometric cues with source-supported projected surface masks."""
    from scipy.spatial import cKDTree

    output = args.output.resolve()
    catalog = json.loads((output / "proposals.json").read_text())
    run = Path(catalog["source_run"])
    if run != args.run.resolve():
        raise ValueError("Proposal source differs from the requested reconstruction.")
    document = json.loads((run / "frames.json").read_text())
    frames = {f["id"]: f for f in document["frames"]}
    poses = json.loads((run / "poses.json").read_text())["poses"]
    worlds = {i: observed_points(run, frames[i], np.asarray(poses[str(i)]), document["depth_scale"])
              for i in catalog["frame_ids"]}
    point_sets = np.load(output / "region-points.npz", allow_pickle=False)
    directory = output / "surface-masks"
    directory.mkdir(exist_ok=True)
    cases = []
    for region in catalog["regions"]:
        if not region["selected"] or "geometric_patch" not in region["kinds"]:
            continue
        tree = cKDTree(point_sets[region["id"]])
        views = []
        for view in region["views"]:
            frame = frames[view["frame_id"]]
            world, valid = worlds[frame["id"]]
            distances, _ = tree.query(world[valid], distance_upper_bound=0.06)
            mask = np.zeros(valid.shape, dtype=np.uint8)
            mask[valid] = np.isfinite(distances).astype(np.uint8)*255
            mask_image = Image.fromarray(mask).resize((frame["width"], frame["height"]), Image.Resampling.NEAREST)
            mask = np.asarray(mask_image)
            y, x = np.nonzero(mask)
            if len(x) < 100:
                continue
            path = directory / f"{region['id']}-{frame['id']}.png"
            mask_image.save(path)
            views.append({"frame": frame["id"], "mask": str(path), "pixels": len(x),
                          "box": [int(x.min()), int(y.min()), int(x.max()+1), int(y.max()+1)]})
        views.sort(key=lambda v: v["pixels"], reverse=True)
        views = views[:2]
        if views:
            cases.append({"name": region["id"], "frame_ids": [v["frame"] for v in views],
                          "regions": [v["box"] for v in views], "region_masks": [v["mask"] for v in views]})
    prompt = json.loads(Path(__file__).with_name("region-prompt.json").read_text())
    prompt["context"] += (" The red-tinted pixels and their detailed outline identify the projected surface. "
                          "The surrounding bounding rectangle is only a locator: objects inside the rectangle but "
                          "outside the highlighted surface are not the target. A proposed surface can span parts "
                          "of several objects; report that ambiguity instead of forcing one identity.")
    prompt["question"] = prompt["question"].replace("highlighted by the red rectangle", "marked by the red-tinted surface pixels")
    save(output / "surface-cases.json", {**prompt, "cases": cases})
    print(json.dumps({"surface_mask_cases": len(cases)}), flush=True)


def symmetry(args: argparse.Namespace) -> None:
    """Estimate a body reflection plane and propose counterpart queries without category answers."""
    import open3d as o3d
    from scipy.spatial import cKDTree

    output = args.output.resolve()
    catalog = json.loads((output / "proposals.json").read_text())
    recognition = json.loads(args.recognition.read_text())
    arrays = np.load(output / "region-points.npz", allow_pickle=False)
    regions = {r["id"]: r for r in catalog["regions"] if r["selected"]}
    floors = [c["name"] for c in recognition["cases"] if c.get("parsed") and
              "floor" in c["parsed"].get("object_identity", "").lower() and c["name"] in regions]
    if not floors:
        raise ValueError("No recognised floor candidate supports estimating body symmetry.")
    floor_id = max(floors, key=lambda name: len(arrays[name]))
    floor = arrays[floor_id]
    centre = floor.mean(0)
    _, _, basis = np.linalg.svd(floor-centre, full_matrices=False)
    normal = basis[2]
    run = Path(catalog["source_run"])
    poses = json.loads((run / "poses.json").read_text())["poses"]
    cameras = np.asarray([np.asarray(v)[:3, 3] for v in poses.values()])
    if (cameras.mean(0)-centre) @ normal < 0:
        normal = -normal
    along, across = basis[0], basis[1]
    cloud = o3d.io.read_point_cloud(str(run / "cloud.ply")).voxel_down_sample(0.06)
    xyz = np.asarray(cloud.points)
    floor_xy = np.stack([(floor-centre) @ along, (floor-centre) @ across], axis=1)
    spans = np.ptp(floor_xy, axis=0)
    coords = np.stack([(xyz-centre) @ along, (xyz-centre) @ across], axis=1)
    low, high = np.percentile(floor_xy, [2, 98], axis=0)
    inside = ((coords > low-0.15*spans) & (coords < high+0.15*spans)).all(axis=1)
    body = xyz[inside & ((xyz-centre) @ normal > 0.08)]
    if len(body) < 200:
        raise ValueError("Insufficient body geometry for a symmetry hypothesis.")
    tree = cKDTree(body)
    best = None
    for angle in np.linspace(-np.pi/12, np.pi/12, 25):
        direction = np.cos(angle)*across + np.sin(angle)*along
        for shift in np.linspace(-0.15*spans[1], 0.15*spans[1], 25):
            origin = centre + shift*direction
            reflected = body - 2*((body-origin) @ direction)[:, None]*direction
            distances, _ = tree.query(reflected)
            cost = float(np.mean(np.minimum(distances, 0.12)**2))
            if best is None or cost < best[0]:
                best = (cost, direction, origin)
    cost, direction, origin = best
    names = list(regions)
    centres = {name: arrays[name].mean(0) for name in names if len(arrays[name]) >= 30}
    sides = {name: float((p-origin) @ direction) for name, p in centres.items()}
    edges = []
    for i, a in enumerate(centres):
        for b in list(centres)[:i]:
            if sides[a]*sides[b] >= 0 or min(abs(sides[a]), abs(sides[b])) < 0.15*spans[1]:
                continue
            pa, pb = arrays[a], arrays[b]
            if min(len(pa), len(pb))/max(len(pa), len(pb)) < 0.45:
                continue
            reflected = pa - 2*((pa-origin) @ direction)[:, None]*direction
            distance = float(np.linalg.norm(reflected.mean(0)-pb.mean(0)))
            if distance > 0.35:
                continue
            forward = cKDTree(pb).query(reflected)[0]
            backward = cKDTree(reflected).query(pb)[0]
            residual = float((np.median(forward)+np.median(backward))/2)
            if residual <= 0.16:
                edges.append({"a": a, "b": b, "centroid_distance_m": distance,
                              "surface_residual_m": residual, "score": residual+0.2*distance})
    matches = {}
    for edge in sorted(edges, key=lambda e: e["score"]):
        matches.setdefault(edge["a"], edge["b"])
        matches.setdefault(edge["b"], edge["a"])
    pairs = [e for e in sorted(edges, key=lambda e: e["score"])
             if matches.get(e["a"]) == e["b"] and matches.get(e["b"]) == e["a"]]
    prompt = json.loads(Path(__file__).with_name("region-prompt.json").read_text())
    prompt["context"] += (" These are distinct candidate regions on opposite sides of an automatically estimated "
                          "longitudinal reflection plane. Geometric matching suggests they may be corresponding "
                          "body features. That hypothesis can be wrong: use the images to assess it, and report "
                          "disagreement if the regions represent different things.")
    prompt["question"] = prompt["question"].replace("What physical object or structural feature is highlighted",
        "What physical objects or structural features are highlighted")
    cases = []
    for edge in pairs:
        views = [regions[edge[name]]["views"][0] for name in ["a", "b"]]
        cases.append({"name": edge["a"]+"-and-"+edge["b"],
                      "frame_ids": [v["frame_id"] for v in views], "regions": [v["box"] for v in views]})
    save(output / "symmetry.json", {"floor_region": floor_id, "plane_normal": direction.tolist(),
         "plane_origin": origin.tolist(), "floor_normal": normal.tolist(), "clipped_rms_m": float(np.sqrt(cost)),
         "candidate_pairs": edges, "mutual_best_pairs": pairs,
         "note": "Approximate geometric hypothesis, not surveyed alignment or verified semantic symmetry."})
    save(output / "symmetry-cases.json", {**prompt, "cases": cases})
    print(json.dumps({"symmetry_pairs": pairs}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["masks", "assemble", "highlight", "symmetry"], required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames")
    parser.add_argument("--grid", type=int, default=32)
    parser.add_argument("--min-area", type=float, default=0.005)
    parser.add_argument("--voxel-m", type=float, default=0.03)
    parser.add_argument("--max-regions", type=int, default=24)
    parser.add_argument("--recognition", type=Path)
    args = parser.parse_args()
    if args.stage == "masks":
        masks(args)
    elif args.stage == "assemble":
        assemble(args)
    elif args.stage == "highlight":
        highlight(args)
    else:
        symmetry(args)


if __name__ == "__main__":
    main()
