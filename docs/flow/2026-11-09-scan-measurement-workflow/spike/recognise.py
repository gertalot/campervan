"""Explicitly experimental image-to-observed-3D scene recognition; never edits source runs.

Run through the project's uv environment; see the sibling README. This is a bounded
feasibility spike, not the implementation of the guided scan workflow.
"""

from __future__ import annotations

import argparse
import gc
import importlib.metadata
import json
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import model_info
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor, Sam2Model, Sam2Processor

from rgbd_geometry import observed_points

LABELS: dict[str, list[int]] = {}
DETECTOR = "IDEA-Research/grounding-dino-tiny"
SEGMENTER = "facebook/sam2.1-hiera-tiny"


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except OSError:
        return ImageFont.load_default(size=size)


def synchronise(device: str) -> None:
    if device == "mps":
        torch.mps.synchronize()


def main() -> None:
    global LABELS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames", help="Comma-separated frame IDs; otherwise sample five across the capture.")
    parser.add_argument("--concepts", type=Path, default=Path(__file__).with_name("concepts.json"))
    parser.add_argument("--finish", action="store_true", help="Finish visualisation from saved inference outputs.")
    parser.add_argument("--device", choices=["cpu", "mps"], default="mps")
    parser.add_argument("--threshold", type=float, default=0.25)
    parser.add_argument("--detector-revision", default="main")
    parser.add_argument("--segmenter-revision", default="main")
    args = parser.parse_args()
    LABELS = json.loads(args.concepts.read_text())
    run = args.run.resolve()
    output = args.output.resolve()
    if output == run or run in output.parents:
        raise ValueError("Trial output must be separate from the source reconstruction.")
    if args.finish:
        finish(run, output, json.loads((output / "report.json").read_text()))
        return
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    frames_doc = json.loads((run / "frames.json").read_text())
    poses = json.loads((run / "poses.json").read_text())["poses"]
    frames = {frame["id"]: frame for frame in frames_doc["frames"]}
    if args.frames:
        selected = [frames[int(value)] for value in args.frames.split(",")]
    else:
        values = list(frames.values())
        selected = [values[int(i)] for i in np.linspace(0, len(values) - 1, min(5, len(values)))]
    device = args.device
    torch.set_num_threads(4)
    report = {
        "status": "running",
        "source_run": str(run),
        "device": device,
        "models": {"detector": DETECTOR, "segmenter": SEGMENTER},
        "packages": {name: importlib.metadata.version(name) for name in ["torch", "transformers", "numpy"]},
        "prompt": ". ".join(LABELS) + ".",
        "palette": LABELS,
        "threshold": args.threshold,
        "frames": [],
        "note": "Experimental predictions, not verified semantic truth. No source data modified.",
    }
    save_json(output / "report.json", report)
    detector_revision = model_info(DETECTOR, revision=args.detector_revision, token=False).sha
    segmenter_revision = model_info(SEGMENTER, revision=args.segmenter_revision, token=False).sha
    report["models"].update(detector_commit=detector_revision, segmenter_commit=segmenter_revision)
    print("[Load Grounding DINO tiny]", flush=True)
    processor = AutoProcessor.from_pretrained(DETECTOR, revision=detector_revision, token=False)
    detector = AutoModelForZeroShotObjectDetection.from_pretrained(
        DETECTOR, revision=detector_revision, token=False, disable_custom_kernels=True
    ).to(device).eval()
    print("[Load SAM 2.1 tiny]", flush=True)
    mask_processor = Sam2Processor.from_pretrained(SEGMENTER, revision=segmenter_revision, token=False)
    segmenter = Sam2Model.from_pretrained(SEGMENTER, revision=segmenter_revision, token=False).to(device).eval()
    label_names = list(LABELS)
    all_points, all_labels, all_scores, all_frames = [], [], [], []
    overlays = []
    for frame in selected:
        frame_start = time.monotonic()
        image = Image.open(run / frame["rgb"]).convert("RGB")
        print(f"[Recognise frame {frame['id']}]", flush=True)
        inputs = processor(images=image, text=report["prompt"], return_tensors="pt").to(device)
        with torch.inference_mode():
            detected = detector(**inputs)
        result = processor.post_process_grounded_object_detection(
            detected,
            inputs.input_ids,
            threshold=args.threshold,
            text_threshold=0.25,
            target_sizes=[(image.height, image.width)],
        )[0]
        boxes = result["boxes"].detach().cpu()
        scores = result["scores"].detach().cpu().numpy()
        texts = result["text_labels"] if "text_labels" in result else result["labels"]
        # The model returns phrases, not guaranteed members of the requested vocabulary.
        # Preserve the phrase and only map exact requested concepts or a contained concept.
        rows = []
        for index, (text, score) in enumerate(zip(texts, scores, strict=True)):
            normalised = str(text).strip().lower()
            matches = [name for name in label_names if name == normalised or name in normalised]
            if len(matches) == 1:
                rows.append({"index": index, "label": matches[0], "phrase": str(text), "score": float(score)})
            else:
                rows.append({"index": index, "label": None, "phrase": str(text), "score": float(score)})
        # Avoid duplicate overlapping boxes for the same phrase without hiding alternatives.
        from torchvision.ops import batched_nms

        if len(rows):
            category_ids = torch.tensor([label_names.index(r["label"]) if r["label"] else len(label_names) for r in rows])
            kept = batched_nms(boxes, torch.tensor(scores), category_ids, 0.6).tolist()[:12]
            active = [rows[i] for i in kept]
            selected_boxes = boxes[kept].tolist()
            mask_inputs = mask_processor(images=image, input_boxes=[selected_boxes], return_tensors="pt").to(device)
            print(f"[Segment {len(active)} regions in frame {frame['id']}]", flush=True)
            with torch.inference_mode():
                masks_output = segmenter(**mask_inputs, multimask_output=False)
            masks = mask_processor.post_process_masks(
                masks_output.pred_masks.cpu(), mask_inputs["original_sizes"].cpu()
            )[0].numpy()
            masks = masks.reshape(len(active), image.height, image.width).astype(bool)
            mask_quality = masks_output.iou_scores.detach().cpu().numpy().reshape(len(active), -1)[:, 0]
        else:
            active, masks, mask_quality = [], np.empty((0, image.height, image.width), bool), []
        rgb = np.asarray(image)
        blended = rgb.astype(float).copy()
        label_image = np.full((image.height, image.width), -1, dtype=np.int16)
        score_image = np.zeros((image.height, image.width), dtype=np.float32)
        for item, mask, quality in zip(active, masks, mask_quality, strict=True):
            item["box"] = boxes[item["index"]].tolist()
            item["mask_quality_score"] = float(quality)
            item["mask_pixels"] = int(mask.sum())
            colour = tuple(LABELS.get(item["label"], (210, 210, 210)))
            blended[mask] = 0.58 * blended[mask] + 0.42 * np.asarray(colour)
            if item["label"]:
                stronger = mask & (score_image < item["score"])
                label_image[stronger] = label_names.index(item["label"])
                score_image[stronger] = item["score"]
        overlay = Image.fromarray(np.uint8(np.clip(blended, 0, 255)))
        draw = ImageDraw.Draw(overlay)
        for item in active:
            box = item["box"]
            colour = tuple(LABELS.get(item["label"], (210, 210, 210)))
            draw.rectangle(box, outline=colour, width=3)
            caption = f"{item['phrase']} {item['score']:.2f}"
            caption_y = max(0, box[1] - 23)
            bounds = draw.textbbox((box[0], caption_y), caption, font=font(19))
            draw.rectangle(bounds, fill=(20, 24, 30))
            draw.text((box[0], caption_y), caption, fill=colour, font=font(19))
        overlay.save(output / f"frame-{frame['id']}-overlay.jpg", quality=92)
        image.save(output / f"frame-{frame['id']}-source.jpg", quality=92)
        overlays.append((frame["id"], overlay))
        np.savez_compressed(output / f"frame-{frame['id']}-masks.npz", masks=masks)
        pose = np.asarray(poses[str(frame["id"])])
        world, valid = observed_points(run, frame, pose, frames_doc["depth_scale"])
        h, w = valid.shape
        ids = cv2.resize(label_image, (w, h), interpolation=cv2.INTER_NEAREST)
        confidence = cv2.resize(score_image, (w, h), interpolation=cv2.INTER_NEAREST)
        valid &= ids >= 0
        # Window pixels often measure objects beyond the glass. Keep the 2D
        # recognition/mask, but do not call those depth returns a window surface.
        if "car window" in label_names:
            valid &= ids != label_names.index("car window")
        points = world[valid]
        all_points.append(points)
        all_labels.append(ids[valid])
        all_scores.append(confidence[valid])
        all_frames.append(np.full(len(points), frame["id"], dtype=np.int32))
        synchronise(device)
        row = {"id": frame["id"], "source_rgb": frame["rgb"], "detections": active,
               "all_detector_phrases": rows, "observed_labelled_points": len(points),
               "seconds": round(time.monotonic() - frame_start, 2)}
        report["frames"].append(row)
        save_json(output / "report.json", report)
        print(json.dumps({"frame": frame["id"], "detections": [(r["phrase"], round(r["score"], 2)) for r in active],
                          "points": len(points), "seconds": row["seconds"]}), flush=True)
    del detector, segmenter
    gc.collect()
    if device == "mps":
        torch.mps.empty_cache()
    points = np.concatenate(all_points)
    ids = np.concatenate(all_labels)
    scores = np.concatenate(all_scores)
    frame_ids = np.concatenate(all_frames)
    np.savez_compressed(output / "observed-labelled-points.npz", xyz=points, label=ids, score=scores, frame_id=frame_ids)
    report["load_and_inference_seconds"] = round(time.monotonic() - started, 2)
    save_json(output / "report.json", report)
    finish(run, output, report)


def finish(run: Path, output: Path, report: dict) -> None:
    global LABELS
    LABELS = report.get("palette", LABELS)
    started = time.monotonic()
    data = np.load(output / "observed-labelled-points.npz", allow_pickle=False)
    points, ids, scores, frame_ids = (data[key] for key in ["xyz", "label", "score", "frame_id"])
    label_names = list(LABELS)
    # Aggregate repeated depth observations by 20 mm voxel. This is a feasibility
    # visualisation, not a replacement reconstruction or a calibrated probability.
    cells: dict[tuple[int, int, int], dict] = {}
    for point, label, score, frame_id in zip(points, ids, scores, frame_ids, strict=True):
        key = tuple(np.floor(point / 0.02).astype(int).tolist())
        cell = cells.setdefault(key, {"sum": np.zeros(3), "n": 0, "votes": Counter(), "frames": set()})
        cell["sum"] += point
        cell["n"] += 1
        cell["votes"][int(label)] += float(score)
        cell["frames"].add(int(frame_id))
    xyz, classes, views = [], [], []
    for cell in cells.values():
        xyz.append(cell["sum"] / cell["n"])
        classes.append(cell["votes"].most_common(1)[0][0])
        views.append(len(cell["frames"]))
    xyz = np.asarray(xyz).reshape(-1, 3)
    classes = np.asarray(classes)
    palette = np.asarray(list(LABELS.values()))
    with (output / "semantic-points.ply").open("w") as stream:
        stream.write(f"ply\nformat ascii 1.0\nelement vertex {len(xyz)}\nproperty float x\nproperty float y\n"
                     "property float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\n"
                     "property int semantic_id\nproperty int supporting_views\nend_header\n")
        for point, label, count in zip(xyz, classes, views, strict=True):
            colour = palette[label]
            stream.write(" ".join(map(str, [*point, *colour, label, count])) + "\n")
    report["regions"] = []
    for label_id, name in enumerate(label_names):
        chosen = xyz[classes == label_id]
        if len(chosen):
            report["regions"].append({"label": name, "voxels": len(chosen), "bounds_min": chosen.min(0).tolist(),
                                       "bounds_max": chosen.max(0).tolist(), "colour": LABELS[name]})
    print("[Extract structural planes from original cloud]", flush=True)
    import open3d as o3d

    cloud = o3d.io.read_point_cloud(str(run / "cloud.ply")).voxel_down_sample(0.04)
    report["structural_planes"] = []
    o3d.utility.random.seed(0)
    for _ in range(6):
        if len(cloud.points) < 500:
            break
        coefficients, inliers = cloud.segment_plane(distance_threshold=0.025, ransac_n=3, num_iterations=500)
        if len(inliers) < 500:
            break
        plane_points = np.asarray(cloud.points)[inliers]
        coefficients = np.asarray(coefficients)
        coefficients /= np.linalg.norm(coefficients[:3])
        distances = np.abs(xyz @ coefficients[:3] + coefficients[3])
        nearby = classes[distances < 0.04]
        support = Counter(label_names[int(i)] for i in nearby)
        report["structural_planes"].append({"coefficients": coefficients.tolist(), "support_points": len(inliers),
            "centroid": plane_points.mean(0).tolist(), "semantic_voxel_support": dict(support),
            "note": "Geometric plane with nearby image-derived votes; not a verified semantic surface."})
        cloud = cloud.select_by_index(inliers, invert=True)
    print("[Render observed semantic points]", flush=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 8))
    axis = fig.add_subplot(projection="3d")
    for label_id, name in enumerate(label_names):
        chosen = xyz[classes == label_id]
        if len(chosen):
            chosen = chosen[::max(1, len(chosen) // 5000)]
            axis.scatter(*chosen.T, s=1, color=np.asarray(LABELS[name])/255, label=name, alpha=0.65)
    axis.set(xlabel="Captured X (m)", ylabel="Captured Y (m)", zlabel="Captured Z (m)",
             title="Predicted labels on observed depth points — five frames only")
    if len(xyz):
        axis.set_box_aspect(np.maximum(np.ptp(xyz, axis=0), 0.01))
    axis.legend(loc="upper left", markerscale=5)
    fig.tight_layout()
    fig.savefig(output / "semantic-points-preview.png", dpi=160)
    plt.close(fig)
    overlays = [(row["id"], Image.open(output / f"frame-{row['id']}-overlay.jpg").convert("RGB"))
                for row in report["frames"]]
    sheet = Image.new("RGB", (len(overlays) * 300, 470), "#20242b")
    draw = ImageDraw.Draw(sheet)
    for index, (frame_id, overlay) in enumerate(overlays):
        overlay.thumbnail((300, 400))
        sheet.paste(overlay, (index * 300, 30))
        draw.text((index * 300 + 8, 5), f"Frame {frame_id}", fill="white", font=font(16))
    draw.text((8, 440), "Experimental automatic detections — inspect masks; labels/scores are not verified truth.",
              fill="white", font=font(16))
    sheet.save(output / "recognition-contact-sheet.jpg", quality=94)
    report.update(status="complete", postprocess_seconds=round(time.monotonic() - started, 2),
                  inference_seconds=round(sum(row["seconds"] for row in report["frames"]), 2),
                  fused_voxels=len(xyz), palette=LABELS)
    save_json(output / "report.json", report)
    print(f"[Complete: {output}]", flush=True)


if __name__ == "__main__":
    main()
