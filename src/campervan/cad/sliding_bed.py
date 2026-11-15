"""Interleaved slats resting on the box, with one moving front rail and metal legs."""

from dataclasses import dataclass
from math import floor

from build123d import Align, Color, Compound, Cylinder, Location, Part

from campervan.cad.bed_motion import bed_offset
from campervan.cad.panels import panel
from campervan.parameters import Parameters

WOOD = Color(0.87, 0.70, 0.43)
FIXED_WOOD = Color(0.72, 0.52, 0.32)
METAL = Color(0.62, 0.66, 0.70)
LID_OPEN_ANGLE = 75.0


@dataclass(frozen=True)
class BedLayout:
    slat_ys: tuple[float, ...]
    travel: float
    rear: float
    front: float
    box_front: float
    moving_front: float
    slat_bottom: float
    rail_bottom: float


def long_bed_layout(p: Parameters) -> BedLayout:
    rail, gap = p.slat_width_mm, p.slat_side_gap_mm
    rear = p.long_bench_inset_mm + p.frame_thickness_mm
    front = p.long_bench_width_mm + p.frame_thickness_mm
    moving_front = front - rail
    box_front = moving_front - gap
    travel = p.bed_width_mm - front
    count = floor((p.seat_length_mm + gap) / (p.slat_width_mm + gap))
    if count % 2 == 0:
        count -= 1
    if count < 3 or travel <= 0:
        raise ValueError("The slat lid needs at least three interleaving slats and positive extension travel.")
    slat_bottom = p.platform_height_mm - p.slat_thickness_mm
    rail_bottom = slat_bottom - p.slat_thickness_mm
    if rail_bottom <= 0 or box_front <= rear + 2 * p.frame_thickness_mm:
        raise ValueError("The storage box needs positive internal height and width below its lid supports.")
    margin = (p.seat_length_mm - count * p.slat_width_mm - (count - 1) * gap) / 2
    ys = tuple(margin + i * (p.slat_width_mm + gap) for i in range(count))
    return BedLayout(ys, travel, rear, front, box_front, moving_front, slat_bottom, rail_bottom)


def build_bed_slats(p: Parameters, layout: BedLayout, *, moving: bool) -> Compound:
    name = "Moving" if moving else "Fixed"
    slats = []
    for i in range(1 if moving else 0, len(layout.slat_ys), 2):
        slat = panel(layout.front - layout.rear, p.slat_width_mm, p.slat_thickness_mm)
        slat.location = Location((0, layout.slat_ys[i], 0))
        slat.label, slat.color = f"{name} slat {i + 1:02}", WOOD if moving else FIXED_WOOD
        slats.append(slat)
    return Compound(label=f"{name} slats", children=slats)


def slat_support(p: Parameters, layout: BedLayout, name: str, x: float) -> Part:
    """Same stock as the slats, lying flat and spanning every row."""
    rail = panel(p.slat_width_mm, p.seat_length_mm, p.slat_thickness_mm)
    rail.label, rail.color = name, WOOD
    rail.location = Location((x - layout.rear, 0, -p.slat_thickness_mm))
    return rail


def build_sliding_bed(p: Parameters, layout: BedLayout) -> Compound:
    legs = []
    # Unsourced removable table-leg envelopes; not a selected product or load rating.
    for index, y in enumerate((p.seat_length_mm * 0.15, p.seat_length_mm * 0.85), start=1):
        tube = Cylinder(p.bed_leg_diameter_mm / 2, layout.rail_bottom, align=(Align.CENTER, Align.CENTER, Align.MIN))
        tube -= Cylinder(
            max(0.1, p.bed_leg_diameter_mm / 2 - 1.5), layout.rail_bottom, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        tube.label, tube.color = f"Provisional metal leg {index}", METAL
        tube.location = Location((layout.moving_front - layout.rear + p.slat_width_mm / 2, y, -layout.slat_bottom))
        legs.append(tube)
    assembly = Compound(
        label="Sliding assembly",
        children=[
            build_bed_slats(p, layout, moving=True),
            slat_support(p, layout, "Moving front slat support", layout.moving_front),
            Compound(label="Provisional metal legs", children=legs),
        ],
    )
    assembly.location = Location((bed_offset(layout.travel, p.bed_extension_percent), 0, 0))
    return Compound(label="Sliding bed", children=[assembly])


def build_lid(p: Parameters, layout: BedLayout) -> Compound:
    lid = Compound(
        label="Hinged lid",
        children=[
            build_bed_slats(p, layout, moving=False),
            build_sliding_bed(p, layout),
        ],
    )
    lid.location = Location(
        (layout.rear, 0, layout.slat_bottom), (0, -LID_OPEN_ANGLE * p.bed_lid_open_percent / 100, 0)
    )
    return lid
