"""Reproduce manual pixel measurements, CSV and figure; not a vehicle geometry generator.

Run from the repository: uv run --locked python docs/research/nv200/analysis/aperture_pixels.py
Image coordinates are original-source pixels, origin at top left. See ../curvature.md for interpretation.
"""

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SOURCES = HERE.parent / "sources"
# y, left x, right x: manually selected clear-opening edges, not outer vehicle silhouette.
JAPAN = [(110, 75, 203), (80, 75, 203), (70, 76, 202), (50, 79, 198.5), (40, 82, 195.5)]
COMBI = [
    (330, 51, 270),
    (300, 51, 270),
    (250, 52, 270),
    (200, 56, 267),
    (170, 60, 264),
    (150, 64, 260),
    (140, 71, 253),
    (133, 84, 242),
]


def dimensions(points, width_pixels, top, bottom):
    # Independent axis scales: source illustrations do not support a single isotropic scale.
    return [(1230 * (bottom - y) / (bottom - top), 1255 * (right - left) / width_pixels) for y, left, right in points]


japan = dimensions(JAPAN, 128, 37, 152)
combi = dimensions(COMBI, 219, 128, 346)
with (HERE / "aperture-pixels.csv").open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["source", "y_px", "left_px", "right_px", "height_above_sill_mm", "width_mm"])
    for name, points, values in [("Japanese diagram", JAPAN, japan), ("Combi photo", COMBI, combi)]:
        for point, (height, width) in zip(points, values, strict=True):
            writer.writerow([name, *point, round(height, 1), round(width, 1)])

canvas = Image.new("RGB", (1600, 920), "#f6f7f8")
draw = ImageDraw.Draw(canvas)


def font(size):
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def text(x, y, message, size=22, color="#202b33"):
    draw.text((x, y), message, font=font(size), fill=color)


text(35, 25, "NV200 rear opening: pixel evidence", 34)
text(35, 75, "Two independent sources, normalised to Japanese opening dimensions: 1255 wide x 1230 high", 23)
text(35, 130, "Nissan Japan diagram", 25)
text(545, 130, "Nissan Combi photograph", 25)
text(1050, 130, "Opening width vs height", 25)


def annotated_image(filename, crop, at, scale, points, color):
    source = Image.open(SOURCES / filename).convert("RGB").crop(crop)
    source = source.resize((round(source.width * scale), round(source.height * scale)))
    canvas.paste(source, at)
    for y, left, right in points:
        x1 = at[0] + (left - crop[0]) * scale
        x2 = at[0] + (right - crop[0]) * scale
        yp = at[1] + (y - crop[1]) * scale
        draw.line((x1, yp, x2, yp), fill=color, width=3)
        for xp in (x1, x2):
            draw.ellipse((xp - 4, yp - 4, xp + 4, yp + 4), fill=color)


annotated_image("nissan-japan-apertures.jpg", (55, 20, 220, 165), (35, 200), 2.9, JAPAN, "#007b9b")
annotated_image("nissan-combi-rear.png", (35, 105, 285, 365), (545, 180), 1.8, COMBI, "#ae4b09")

x0, y0, w, h = 1100, 210, 440, 440


def plot_point(height, width):
    return x0 + (width - 800) / 500 * w, y0 + h - height / 1250 * h


for width in (800, 1000, 1200, 1300):
    xp, _ = plot_point(0, width)
    draw.line((xp, y0, xp, y0 + h), fill="#d0d6dc")
    text(xp - 24, y0 + h + 10, str(width), 18)
for height in (0, 400, 800, 1200):
    _, yp = plot_point(height, 800)
    draw.line((x0, yp, x0 + w, yp), fill="#d0d6dc")
    text(x0 - 50, yp - 12, str(height), 17)
for values, color in [(japan, "#007b9b"), (combi, "#ae4b09")]:
    pixels = [plot_point(height, width) for height, width in values]
    draw.line(pixels, fill=color, width=4)
    for x, y in pixels:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
text(1100, 180, "Height above sill (mm)", 18)
text(1210, 690, "Width (mm)", 18)
text(35, 700, "Blue: Japanese schematic", 23, "#007b9b")
text(545, 700, "Orange: short-body Combi photo", 23, "#ae4b09")
text(35, 755, "Both support inward taper above the lower upright sides. Upper-corner shape differs markedly.", 24)
text(
    35, 800, "Illustration-derived estimates only; allow roughly 50-100 mm and greater uncertainty near the header.", 22
)
text(
    35,
    840,
    "This is the door opening, not the wider cargo section or ceiling. Sources and pixel coordinates: curvature.md",
    22,
)
canvas.save(HERE / "aperture-comparison.png")
print("Wrote aperture-pixels.csv and aperture-comparison.png")
