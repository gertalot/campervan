"""Printable 36h11 tags, sized including their one-cell white border."""

from io import BytesIO
from math import ceil, floor

import cv2
from pydantic import BaseModel, ConfigDict, Field, model_validator
from reportlab.lib.units import mm  # type: ignore[import-untyped]
from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]

LABEL_MM = 6
FOOTER_MM = 6


class AprilTagSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    size_mm: float = Field(default=100, ge=10, le=1000)
    count: int = Field(default=40, ge=1, le=587)
    start_id: int = Field(default=1, ge=0, le=586)
    paper_width_mm: float = Field(default=210, ge=50, le=1500)
    paper_height_mm: float = Field(default=297, ge=50, le=1500)
    margin_mm: float = Field(default=5, ge=1, le=100)
    gap_mm: float = Field(default=0, ge=0, le=100)
    cut_lines: bool = True
    crosshair: bool = True
    crosshair_diameter_mm: float = Field(default=10, gt=0, le=500)

    @model_validator(mode="after")
    def printable(self) -> "AprilTagSettings":
        if self.start_id + self.count > 587:
            raise ValueError("36h11 IDs run from 0 to 586. Reduce the quantity or starting ID.")
        if self.crosshair and self.crosshair_diameter_mm > self.size_mm * 0.6:
            raise ValueError("The centre mark must fit inside the tag's encoded area (60% of its printed width).")
        self.layout()
        return self

    def layout(self) -> dict[str, int | float]:
        columns = floor((self.paper_width_mm - 2 * self.margin_mm + self.gap_mm) / (self.size_mm + self.gap_mm))
        rows = floor(
            (self.paper_height_mm - 2 * self.margin_mm - FOOTER_MM + self.gap_mm)
            / (self.size_mm + LABEL_MM + self.gap_mm)
        )
        if columns < 1 or rows < 1:
            raise ValueError("No tag fits on this paper with the selected size, margins and ID label strip.")
        per_page = columns * rows
        return {
            "columns": columns,
            "rows": rows,
            "per_page": per_page,
            "pages": ceil(self.count / per_page),
            "marker_length_mm": self.size_mm * 0.8,
        }


def generate_pdf(settings: AprilTagSettings) -> bytes:
    """Use OpenCV's dictionary; draw each module as an exact vector rectangle."""
    layout = settings.layout()
    columns, rows = int(layout["columns"]), int(layout["rows"])
    per_page = columns * rows
    size, gap = settings.size_mm, settings.gap_mm
    tile_height = size + LABEL_MM
    left = (settings.paper_width_mm - columns * size - (columns - 1) * gap) / 2
    top = (
        settings.margin_mm
        + (settings.paper_height_mm - 2 * settings.margin_mm - FOOTER_MM - rows * tile_height - (rows - 1) * gap) / 2
    )
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    output = BytesIO()
    canvas = Canvas(output, pagesize=(settings.paper_width_mm * mm, settings.paper_height_mm * mm))
    canvas.setTitle(f"AprilTag 36h11 - IDs {settings.start_id}-{settings.start_id + settings.count - 1}")
    for page_start in range(0, settings.count, per_page):
        for index in range(page_start, min(page_start + per_page, settings.count)):
            slot = index - page_start
            x = left + (slot % columns) * (size + gap)
            y = settings.paper_height_mm - top - (slot // columns) * (tile_height + gap) - size
            tag_id = settings.start_id + index
            pattern = cv2.aruco.generateImageMarker(dictionary, tag_id, 8, borderBits=1)
            cell = size / 10
            canvas.setFillColorRGB(0, 0, 0)
            # The 8x8 black square sits inside the complete 10x10 tag.
            for row in range(8):
                for column in range(8):
                    if pattern[row, column] == 0:
                        canvas.rect(
                            (x + (column + 1) * cell) * mm,
                            (y + (8 - row) * cell) * mm,
                            cell * mm,
                            cell * mm,
                            stroke=0,
                            fill=1,
                        )
            if settings.crosshair:
                cx, cy, radius = (x + size / 2) * mm, (y + size / 2) * mm, settings.crosshair_diameter_mm / 2 * mm
                canvas.setStrokeColorRGB(0.6, 0.6, 0.6)
                canvas.setLineWidth(0.15 * mm)
                canvas.circle(cx, cy, radius, stroke=1, fill=0)
                canvas.line(cx - radius, cy, cx + radius, cy)
                canvas.line(cx, cy - radius, cx, cy + radius)
            canvas.setFillColorRGB(0.2, 0.2, 0.2)
            label = f"36h11 | ID {tag_id}"
            canvas.setFont("Helvetica", min(8, (size - 2) * mm / canvas.stringWidth(label, "Helvetica", 1)))
            canvas.drawCentredString((x + size / 2) * mm, (y - 4) * mm, label)
            if settings.cut_lines:
                canvas.setStrokeColorRGB(0.65, 0.65, 0.65)
                canvas.setLineWidth(0.1 * mm)
                canvas.rect(x * mm, (y - LABEL_MM) * mm, size * mm, tile_height * mm, stroke=1, fill=0)
        canvas.setFillColorRGB(0.3, 0.3, 0.3)
        footer = (
            f"Print at 100% / actual size | Tag {size:g} mm incl. white border | "
            f"RTAB-Map Marker/Length: {size * 0.0008:g} m | Page {page_start // per_page + 1}/{layout['pages']}"
        )
        canvas.setFont(
            "Helvetica",
            min(
                7,
                (settings.paper_width_mm - 2 * settings.margin_mm) * mm / canvas.stringWidth(footer, "Helvetica", 1),
            ),
        )
        canvas.drawCentredString(
            settings.paper_width_mm / 2 * mm,
            settings.margin_mm * mm,
            footer,
        )
        canvas.showPage()
    canvas.save()
    return output.getvalue()
