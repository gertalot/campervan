"""Cross-bed slats, sliding frame and hinged storage lid, following the Onshape geometry."""

from dataclasses import dataclass
from math import ceil

from build123d import Align, Color, Compound, Cylinder, Location

from campervan.cad.bed_motion import bed_offset
from campervan.cad.cross_stops import build_cross_stops, cross_stop_layout, cut_stop_pocket
from campervan.cad.panels import panel
from campervan.cad.sliding_bed import angle_bracket, long_bed_layout
from campervan.parameters import Parameters


@dataclass(frozen=True)
class CrossBedLayout:
    width: float
    travel: float
    moving_start: float
    slats: tuple[tuple[float, float], ...]
    slat_gap: float
    leg_x: float
    fixed_end: float
    deck_start: float
    lid_end: float


def cross_bed_layout(p: Parameters) -> CrossBedLayout:
    width = (p.bed_width_mm + p.long_bench_width_mm) / 2
    closed_width = width + p.frame_thickness_mm
    travel = p.bed_width_mm - closed_width
    overlap = p.long_bench_width_mm + p.frame_thickness_mm - p.wall_thickness_mm - long_bed_layout(p).travel
    moving_start = closed_width - travel - overlap
    length = p.cargo_length_mm - p.seat_length_mm
    # Reused stock keeps its width. Fit an odd count with a positive, evenly distributed gap.
    count = ceil(length / p.slat_width_mm) - 1
    if count % 2 == 0:
        count -= 1
    if count < 7 or count > 101 or travel <= 0 or moving_start < p.wall_thickness_mm:
        raise ValueError("Cross bed needs room for seven or more slats and positive extension with retained overlap.")
    slat_gap = (length - count * p.slat_width_mm) / (count - 1)
    slats = tuple((p.seat_length_mm + i * (p.slat_width_mm + slat_gap), p.slat_width_mm) for i in range(count))
    leg_x = closed_width - p.member_width_mm
    fixed_end = leg_x - p.cross_leg_clearance_mm
    storage_face = width - 2 * p.frame_thickness_mm - p.wall_thickness_mm - p.cross_toilet_bay_depth_mm
    seam = storage_face + p.frame_thickness_mm / 2
    gap = p.cross_storage_lid_gap_mm
    if seam + gap / 2 > moving_start or seam - gap / 2 <= p.wall_thickness_mm:
        raise ValueError("Storage lid must fit beside the closed moving slats.")
    leg_height = p.platform_height_mm - p.slat_thickness_mm - p.cross_bearer_height_mm
    if fixed_end <= seam + gap / 2 or leg_height <= p.bracket_arm_mm:
        raise ValueError("Cross-bed supports need space beside the divider and below the bearer for the leg brackets.")
    if p.bracket_width_mm > p.member_width_mm or p.frame_thickness_mm + p.bracket_arm_mm > p.slat_width_mm:
        raise ValueError("Cross-bed brackets must fit the leg faces and stay beneath the outer moving slats.")
    return CrossBedLayout(
        width, travel, moving_start, slats, slat_gap, leg_x, fixed_end, seam + gap / 2, seam - gap / 2
    )


def build_cross_slats(p: Parameters, layout: CrossBedLayout, *, moving: bool) -> Compound:
    slats = []
    stop = cross_stop_layout(p, layout)
    start = layout.moving_start if moving else layout.deck_start
    for i in range(0 if moving else 1, len(layout.slats), 2):
        y, width = layout.slats[i]
        slat = panel(layout.width + p.frame_thickness_mm - start, width, p.slat_thickness_mm)
        slat.location = Location((start, y, p.platform_height_mm - p.slat_thickness_mm))
        slat = cut_stop_pocket(slat, p, layout, stop, i, moving=moving)
        slat.label = f"{'Moving' if moving else 'Fixed'} slat {i + 1:02}"
        slat.color = Color(0.87, 0.70, 0.43) if moving else Color(0.72, 0.52, 0.32)
        slats.append(slat)
    return Compound(label="Moving slats" if moving else "Fixed slats", children=slats)


def build_cross_sliding_assembly(p: Parameters, layout: CrossBedLayout) -> Compound:
    length = p.cargo_length_mm - p.seat_length_mm
    height = p.platform_height_mm - p.slat_thickness_mm
    member, thickness = p.member_width_mm, p.frame_thickness_mm
    leg_height = height - p.cross_bearer_height_mm
    bearer = panel(member, length, p.cross_bearer_height_mm)
    bearer.location = Location((layout.leg_x, p.seat_length_mm, leg_height))
    bearer.label, bearer.color = "Bearer", Color(0.88, 0.61, 0.25)
    legs = []
    for name, y in (("Rear leg", p.seat_length_mm), ("Cab-end leg", p.cargo_length_mm - thickness)):
        leg = panel(member, thickness, leg_height)
        leg.location = Location((layout.leg_x, y, 0))
        leg.label, leg.color = name, Color(0.88, 0.61, 0.25)
        legs.append(leg)
    brackets = []
    bracket_x = layout.leg_x + (member - p.bracket_width_mm) / 2
    # Face the two brackets inward along the van, beneath the bearer and against each leg.
    for name, x, y, rotation in (
        ("Rear angle bracket", bracket_x, p.seat_length_mm + thickness, -90),
        ("Cab-end angle bracket", bracket_x + p.bracket_width_mm, p.cargo_length_mm - thickness, 90),
    ):
        bracket = angle_bracket(p)
        bracket.location = Location((x, y, leg_height), (0, 0, rotation))
        bracket.label, bracket.color = name, Color(0.62, 0.66, 0.70)
        brackets.append(bracket)
    assembly = Compound(
        label="Sliding assembly",
        children=[
            build_cross_slats(p, layout, moving=True),
            bearer,
            Compound(label="Legs", children=legs),
            Compound(label="Angle brackets", children=brackets),
            build_cross_stops(p, layout),
        ],
    )
    assembly.location = Location((bed_offset(layout.travel, p.bed_extension_percent), 0, 0))
    return assembly


def build_storage_lid(p: Parameters, layout: CrossBedLayout) -> Compound:
    gap = p.cross_storage_lid_gap_mm
    rear, front = p.seat_length_mm + gap, p.cargo_length_mm - gap
    height = p.platform_height_mm - p.slat_thickness_mm
    deck = panel(layout.lid_end - gap, front - rear, p.cross_deck_thickness_mm)
    deck.location = Location((gap, rear, height - p.cross_deck_thickness_mm))
    storage_face = layout.deck_start - gap / 2 - p.frame_thickness_mm / 2
    finger_x = (p.wall_thickness_mm + p.frame_thickness_mm + storage_face) / 2
    lid_gaps = layout.slats[::2]
    y, width = lid_gaps[(len(lid_gaps) - 1) // 2]
    diameter = p.cross_lid_finger_diameter_mm
    if diameter + 2 * gap >= min(p.slat_width_mm, storage_face - p.wall_thickness_mm - p.frame_thickness_mm):
        raise ValueError("Storage lid finger hole must fit within the lid and between its attached slats.")
    deck -= Cylinder(diameter / 2, p.cross_deck_thickness_mm + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((finger_x, y + width / 2, height - p.cross_deck_thickness_mm - 1))
    )
    deck.label, deck.color = "Plywood lid", Color(0.78, 0.70, 0.53)
    pieces = [deck]
    # Continue the fixed toilet-side rows across the lid seam, using the same stock width.
    for i in range(1, len(layout.slats), 2):
        y, width = layout.slats[i]
        start_x = max(p.wall_thickness_mm, gap)
        slat = panel(layout.lid_end - start_x, width, p.slat_thickness_mm)
        slat.location = Location((start_x, y, height))
        slat.label, slat.color = f"Lid slat {i + 1:02}", Color(0.72, 0.52, 0.32)
        pieces.append(slat)
    # Put the group origin on the cab-side hinge so CAD and viewer rotate the same assembly.
    for piece in pieces:
        piece.move(Location((0, -front, -p.platform_height_mm)))
    lid = Compound(label="Storage lid", children=pieces)
    lid.location = Location((0, front, p.platform_height_mm), (-70 * p.cross_lid_open_percent / 100, 0, 0))
    return lid
