"""Local vision-language recognition spike; inputs/results remain separate from captures."""

from __future__ import annotations

import argparse
import html
import importlib.metadata
import json
import textwrap
import time
from pathlib import Path

import mlx.core as mx
from huggingface_hub import model_info, snapshot_download
from mlx_vlm import generate, load
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def annotate_detections(output: Path, case: dict, paths: list[str], parsed: object,
                        categories: list[str]) -> tuple[list[str], list[dict], list[dict]]:
    """Render target-only model proposals; invalid outputs remain recorded, never become regions."""
    accepted, rejected = [], []
    detections = parsed.get("detections") if isinstance(parsed, dict) else None
    if not isinstance(detections, list) or len(paths) != 1:
        return paths, accepted, [{"reason": "Expected one source image and a detections array"}]
    marked = Image.open(paths[0]).convert("RGB")
    draw = ImageDraw.Draw(marked)
    font = ImageFont.load_default(size=20)
    for detection in detections:
        box = detection.get("bbox") if isinstance(detection, dict) else None
        category = detection.get("category") if isinstance(detection, dict) else None
        valid_box = (isinstance(box, list) and len(box) == 4
                     and all(type(v) in (int, float) and 0 <= v <= 1000 for v in box))
        if category not in categories or not valid_box or not (box[0] < box[2] and box[1] < box[3]):
            rejected.append({"detection": detection, "reason": "Unrequested category or invalid normalized box"})
            continue
        pixels = [round(box[0]*marked.width/1000), round(box[1]*marked.height/1000),
                  round(box[2]*marked.width/1000), round(box[3]*marked.height/1000)]
        accepted.append({**detection, "bbox_pixels": pixels, "frame_id": case["frame_ids"][0]})
        draw.rectangle(pixels, outline=(255, 110, 30), width=4)
        draw.text((pixels[0]+4, pixels[1]+4), category, font=font,
                  fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    path = output / f"{case['name']}-detections.jpg"
    marked.save(path, quality=95)
    return [str(path)], accepted, rejected


def render_report(output: Path, report: dict) -> None:
    heading = ImageFont.load_default(size=22)
    body = ImageFont.load_default(size=18)
    columns = max(1, min(4, len(report["cases"])))
    rows = max(1, (len(report["cases"])+columns-1)//columns)
    sheet = Image.new("RGB", (columns*360, rows*760+40), "#20242b")
    draw = ImageDraw.Draw(sheet)
    parts = ["<!doctype html><html lang='en'><meta charset='utf-8'><title>Van recognition trial</title>",
             "<style>body{font:16px system-ui;background:#20242b;color:#eee;max-width:1100px;margin:2rem auto;"
             "padding:1rem}img{max-width:100%}section{border-top:1px solid #666;margin-top:2rem}"
             "pre{white-space:pre-wrap}h2{color:#96d7ff}</style>",
             "<h1>Context-aware scene recognition trial</h1>",
             f"<p>{html.escape(report['model'])}. Responses are provisional; no source geometry changed.</p>"]
    for index, case in enumerate(report["cases"]):
        parsed = case["parsed"] or {}
        identity = parsed.get("object_identity", case["name"])
        shown = case.get("display_image_paths", case["image_paths"])
        chosen = shown[1] if len(shown) > 1 else shown[0]
        image = Image.open(chosen).convert("RGB")
        image.thumbnail((350, 470))
        offset, top = (index % columns)*360, (index//columns)*760
        sheet.paste(image, (offset + 5, top + 45))
        draw.text((offset + 8, top + 10), case["name"], font=heading, fill="white")
        y = top + 530
        for line in textwrap.wrap(identity, 30):
            draw.text((offset + 8, y), line, font=heading, fill="#96d7ff")
            y += 27
        y += 10
        for line in textwrap.wrap("Material: " + parsed.get("surface_material", "see full response"), 34):
            draw.text((offset + 8, y), line, font=body, fill="white")
            y += 23
        draw.text((offset + 8, top + 720), f"{case['seconds']:.1f}s · local MLX", font=body, fill="#c0c5cc")
        parts.extend([f"<section><h2>{html.escape(identity)}</h2>",
                      f"<img src='{html.escape(case['name'], quote=True)}-sources.jpg' alt='Source views'>",
                      "<pre>" + html.escape(case["response"]) + "</pre>",
                      f"<p>{case['seconds']:.2f} seconds; peak MLX allocation {case['peak_memory_gb']:.2f} GB.</p></section>"])
    caption = ("Provisional target-feature detections; boxes are model predictions."
               if report.get("task") == "detect_features" else
               "Provisional recognition. Region boxes, where present, are supplied proposals.")
    draw.text((10, rows*760+6), caption, font=body, fill="white")
    sheet.save(output / "vlm-recognition-summary.jpg", quality=94)
    parts.append("<p>This is recognition feasibility, not automatic complete-scene detection or mesh correction.</p></html>")
    (output / "report.html").write_text("\n".join(parts))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("vlm-cases.json"))
    parser.add_argument("--model", default="mlx-community/Qwen3.5-4B-MLX-4bit")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--max-tokens", type=int, default=1000)
    args = parser.parse_args()
    run, output = args.run.resolve(), args.output.resolve()
    if run == output or run in output.parents:
        raise ValueError("Trial outputs must be separate from the source reconstruction.")
    output.mkdir(parents=True, exist_ok=False)
    frames = {f["id"]: f for f in json.loads((run / "frames.json").read_text())["frames"]}
    cases = json.loads(args.cases.read_text())
    if cases.get("prompt_file"):
        prompt_file = Path(cases["prompt_file"])
        if not prompt_file.is_absolute():
            prompt_file = args.cases.parent / prompt_file
        cases = {**json.loads(prompt_file.read_text()), **cases}
    revision = model_info(args.model, revision=args.revision, token=False).sha
    report = {"status": "downloading", "model": args.model, "revision": revision,
              "task": cases.get("task", "identify_regions"), "categories": cases.get("categories", []),
              "packages": {n: importlib.metadata.version(n) for n in ["mlx-vlm", "mlx", "transformers"]},
              "source_run": str(run), "context": cases["context"], "question": cases["question"],
              "temperature": 0, "enable_thinking": False, "max_tokens": args.max_tokens, "cases": []}
    save(output / "report.json", report)
    print(f"[Download/load {args.model} at {revision}]", flush=True)
    snapshot = snapshot_download(args.model, revision=revision, token=False,
                                 allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.jinja", "*.tiktoken"])
    model, processor = load(snapshot, trust_remote_code=False)
    config = load_config(snapshot)
    report["status"] = "recognising"
    save(output / "report.json", report)
    for case in cases["cases"]:
        print(f"[Interpret {case['name']}: frames {case['frame_ids']}]", flush=True)
        paths = [str(run / frames[i]["rgb"]) for i in case["frame_ids"]]
        if case.get("regions"):
            marked_paths = []
            for index, (path, box) in enumerate(zip(paths, case["regions"], strict=True)):
                marked = Image.open(path).convert("RGB")
                if case.get("region_masks"):
                    mask = Image.open(case["region_masks"][index]).convert("L")
                    tint = Image.new("RGB", marked.size, (255, 50, 50))
                    marked = Image.composite(Image.blend(marked, tint, 0.14), marked, mask)
                    expanded = mask.filter(ImageFilter.MaxFilter(3))
                    contracted = mask.filter(ImageFilter.MinFilter(3))
                    import PIL.ImageChops
                    edge = PIL.ImageChops.subtract(expanded, contracted)
                    marked.paste((255, 30, 30), mask=edge)
                ImageDraw.Draw(marked).rectangle(box, outline=(255, 30, 30), width=5)
                marked_path = output / f"{case['name']}-image-{index + 1}.jpg"
                marked.save(marked_path, quality=95)
                marked_paths.append(str(marked_path))
            paths = marked_paths
        prompt = cases["context"] + "\n\n" + cases["question"]
        formatted = apply_chat_template(processor, config, prompt, num_images=len(paths), enable_thinking=False)
        started = time.monotonic()
        result = generate(model, processor, formatted, image=paths, max_tokens=args.max_tokens,
                          temperature=0, verbose=False)
        text = result.text
        (output / f"{case['name']}.txt").write_text(text + "\n")
        try:
            parsed = json.loads(text.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError:
            parsed = None
        row = {"name": case["name"], "frame_ids": case["frame_ids"], "image_paths": paths,
               "input_regions": case.get("regions"),
               "input_region_masks": case.get("region_masks"),
               "response": text, "parsed": parsed, "seconds": round(time.monotonic() - started, 2),
               "prompt_tokens": result.prompt_tokens, "generation_tokens": result.generation_tokens,
               "generation_tps": result.generation_tps, "peak_memory_gb": result.peak_memory,
               "finish_reason": result.finish_reason, "response_complete": result.finish_reason != "length",
               "structured_response_valid": parsed is not None}
        if report["task"] == "detect_features":
            shown, detections, rejected = annotate_detections(output, case, paths, parsed, report["categories"])
            row.update(display_image_paths=shown, detections=detections, rejected_detections=rejected,
                       structured_response_valid=parsed is not None and not rejected)
        else:
            shown = paths
        report["cases"].append(row)
        save(output / "report.json", report)
        # Source paths remain recorded; the sheet shows input regions or predicted target detections.
        sheet = Image.new("RGB", (len(paths) * 360, 500), "#20242b")
        draw = ImageDraw.Draw(sheet)
        for index, (path, frame_id) in enumerate(zip(shown, case["frame_ids"], strict=True)):
            image = Image.open(path).convert("RGB")
            image.thumbnail((360, 460))
            sheet.paste(image, (index * 360, 30))
            draw.text((index * 360 + 5, 6), f"Image {index + 1}: frame {frame_id}", fill="white")
        sheet.save(output / f"{case['name']}-sources.jpg", quality=94)
        print(json.dumps({k: row[k] for k in ["name", "seconds", "generation_tokens", "generation_tps",
                                              "peak_memory_gb", "finish_reason"]}), flush=True)
        mx.clear_cache()
    report["status"] = ("complete" if all(c["response_complete"] and c["structured_response_valid"]
                                          for c in report["cases"]) else "complete_with_warnings")
    save(output / "report.json", report)
    render_report(output, report)
    print(f"[Complete: {output}]", flush=True)


if __name__ == "__main__":
    main()
