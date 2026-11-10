"""Full-resolution photographic inputs, calibration groups and immutable source provenance."""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from campervan.scans import (
    _calibration,
    database_info,
    export_images,
    rtabmap_environment,
    rtabmap_tool,
    write_json,
)
from campervan.settings import load_settings


def _open_photo(path: Path) -> Any:
    from PIL import Image
    from pillow_heif import register_heif_opener

    register_heif_opener()
    image = Image.open(path)
    if image.format not in {"JPEG", "PNG", "HEIF"}:
        image.close()
        raise ValueError(f"Unsupported photograph format: {path.name}")
    return image


def _photo_metadata(image: Any) -> dict[str, Any]:
    from PIL import ExifTags

    image.load()  # Decode the primary, full-size image, including HEIC container transforms.
    exif = image.getexif()
    detail = exif.get_ifd(ExifTags.IFD.Exif)
    orientation = int(exif.get(ExifTags.Base.Orientation, 1))
    width, height = image.size
    metadata: dict[str, Any] = {
        "format": image.format,
        "original_width": width,
        "original_height": height,
        "orientation": image.info.get("original_orientation") or orientation,
        "decoded_orientation": orientation,
        "width": height if orientation in {5, 6, 7, 8} else width,
        "height": width if orientation in {5, 6, 7, 8} else height,
        "primary_image_index": image.tell(),
        # For HEIC, libheif has already applied container orientation before Pillow exposes pixels.
        "source_coordinates": "decoder_pixels_before_exif_transpose",
    }
    for name, tag in {
        "camera_make": ExifTags.Base.Make,
        "camera_model": ExifTags.Base.Model,
        "lens_make": ExifTags.Base.LensMake,
        "lens_model": ExifTags.Base.LensModel,
        "datetime_original": ExifTags.Base.DateTimeOriginal,
    }.items():
        value = detail.get(tag, exif.get(tag))
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        if value is not None and str(value).strip("\x00 "):
            metadata[name] = str(value).strip("\x00 ")
    for name, tag in {
        "focal_length_mm": ExifTags.Base.FocalLength,
        "focal_length_35mm": ExifTags.Base.FocalLengthIn35mmFilm,
    }.items():
        value = detail.get(tag, exif.get(tag))
        if value is not None:
            try:
                number = float(value)
            except (TypeError, ValueError, ZeroDivisionError):
                continue
            if math.isfinite(number) and number > 0:
                metadata[name] = number
    return metadata


def photo_info(path: Path) -> dict[str, Any]:
    """Validate a primary JPEG/PNG/HEIC image without modifying its original bytes."""
    with _open_photo(path) as image:
        return _photo_metadata(image)


def _identifier(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", value)
    if safe != value or not safe:
        safe += "-" + hashlib.sha256(value.encode()).hexdigest()[:12]
    return safe


def _camera_group(metadata: dict[str, Any], identity: str) -> str:
    fields = ("camera_make", "camera_model", "lens_model", "focal_length_mm", "width", "height")
    if all(metadata.get(key) is not None for key in fields):
        key = [metadata[field] for field in fields]
        prefix = "lens"
    else:
        # Missing lens/focal metadata cannot establish that two images share calibration.
        key, prefix = [identity], "image"
    digest = hashlib.sha256(json.dumps(key, ensure_ascii=True).encode()).hexdigest()[:20]
    return f"{prefix}-{digest}"


def prepare_photo_inputs(inputs: list[dict], output: Path, log: Path) -> dict:
    """Prepare exactly the selected sources; depth and saved poses do not provide photo geometry."""
    from PIL import ExifTags, ImageOps

    if not inputs:
        raise ValueError("Select at least one photographic input.")
    output = output.resolve()
    directory = output / "working" / "images"
    directory.mkdir(parents=True)
    images: list[dict[str, Any]] = []
    names: set[str] = set()

    def prepare(capture: dict, source: Path, node_id: str | None = None, calibration: Path | None = None) -> None:
        capture_id = str(capture["capture_id"])
        filename = Path(capture.get("filename", source.name)).stem
        source_name = str(node_id if node_id is not None else capture.get("source_node_id", filename))
        identity = f"{capture_id}-{source_name}"
        with _open_photo(source) as image:
            metadata = _photo_metadata(image)
            group = _camera_group(metadata, identity)
            name = f"{group}/{_identifier(capture_id)}-{_identifier(source_name)}.png"
            if name in names:
                raise ValueError(f"Duplicate photographic input identity: {identity}")
            names.add(name)
            destination = directory / name
            destination.parent.mkdir(exist_ok=True)
            with ImageOps.exif_transpose(image) as oriented:
                exif = oriented.getexif()
                exif[ExifTags.Base.Orientation] = 1
                if ExifTags.Base.ImageWidth in exif:
                    exif[ExifTags.Base.ImageWidth] = oriented.width
                if ExifTags.Base.ImageLength in exif:
                    exif[ExifTags.Base.ImageLength] = oriented.height
                detail = exif.get_ifd(ExifTags.IFD.Exif)
                for tag, value in (
                    (ExifTags.Base.ExifImageWidth, oriented.width),
                    (ExifTags.Base.ExifImageHeight, oriented.height),
                ):
                    if tag in detail:
                        detail[tag] = value
                # PNG retains focal metadata for COLMAP's EXIF-based initialisation without JPEG recompression.
                save_metadata = {"exif": exif.tobytes()}
                if image.info.get("icc_profile"):
                    save_metadata["icc_profile"] = image.info["icc_profile"]
                if oriented.mode in {"RGB", "RGBA", "L", "LA", "I;16", "I"}:
                    oriented.save(destination, **save_metadata)
                else:
                    with oriented.convert("RGB") as rgb:
                        rgb.save(destination, **save_metadata)
        record = {
            **{key: value for key, value in capture.items() if key != "path"},
            **metadata,
            "name": name,
            "capture_id": capture_id,
            "source_path": str(Path(capture["path"]).resolve()),
            "source_image_path": str(source.resolve()),
            "camera_group": group,
        }
        if node_id is not None:
            record["source_node_id"] = int(node_id) if node_id.isdecimal() else node_id
        if calibration is not None and calibration.is_file():
            record["calibration_path"] = str(calibration.relative_to(output))
            try:
                record["calibration"] = _calibration(calibration)
            except ValueError as error:
                record["calibration_error"] = str(error)
        images.append(record)
        print(f"[Prepared {len(images)} images; {capture_id}/{source_name}]", flush=True)

    print(f"[Preparing {len(inputs)} selected captures]", flush=True)
    for capture in inputs:
        source = Path(capture["path"]).resolve()
        if capture["kind"] == "photo":
            prepare(capture, source)
        elif capture["kind"] == "database":
            database_info(source)  # Version validation only; no saved-pose requirement.
            tool = rtabmap_tool("rtabmap-export", load_settings().rtabmap_bin_dir)
            extracted = output / "working" / "extracted" / _identifier(str(capture["capture_id"]))
            print(f"[Exporting database photographs from {capture['capture_id']}]", flush=True)
            export_images(source, extracted, log, tool, rtabmap_environment(tool))
            rgb = sorted(
                path
                for path in (extracted / "capture_rgb").glob("*")
                if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
            )
            if not rgb:
                raise ValueError(f"No RGB photographs exported from {source.name}.")
            print(f"[Exported {len(rgb)} database photographs]", flush=True)
            for path in rgb:
                prepare(capture, path, path.stem, extracted / "capture_calib" / f"{path.stem}.yaml")
        else:
            raise ValueError(f"Unsupported capture kind: {capture['kind']}")
    result = {"images": images, "image_directory": str(directory)}
    write_json(output / "image_sources.json", result)
    groups = len({image["camera_group"] for image in images})
    print(f"[Prepared {len(images)} full-resolution photographs in {groups} camera groups]", flush=True)
    return result
