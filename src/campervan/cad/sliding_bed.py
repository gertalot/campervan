"""Slotted plywood storage lid, lifted by a photo-derived four-bar pair."""

from dataclasses import dataclass
from math import floor

from build123d import Align, Color, Compound, Cylinder, Face, Location, Part, Solid, Wire

from campervan.cad.bed_motion import bed_offset
from campervan.cad.bed_lift import lid_location
from campervan.cad.panels import panel
from campervan.parameters import Parameters

WOOD = Color(0.87, 0.70, 0.43)
FIXED_WOOD = Color(0.72, 0.52, 0.32)
METAL = Color(0.62, 0.66, 0.70)
HINGE_SLAT_TRIM = 5.0
COMB_TOOTH_OVERHANG = 20.0
BOX_RAIL_RESERVE = 20.0


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
    lid_rear: float
    box_top: float


def long_bed_layout(p: Parameters) -> BedLayout:
    gap = p.slat_side_gap_mm
    rear = p.long_bench_inset_mm + p.frame_thickness_mm
    front = p.long_bench_width_mm + p.frame_thickness_mm
    moving_front = front - p.frame_thickness_mm
    # Back the extended slat bearing, reserving the outer 20mm for a future rail.
    box_front = front - BOX_RAIL_RESERVE
    travel = p.bed_width_mm - front
    count = floor((p.seat_length_mm + gap) / (p.slat_width_mm + gap))
    if count % 2 == 0:
        count -= 1
    if count < 3 or travel <= 0:
        raise ValueError("The slat lid needs at least three interleaving slats and positive extension travel.")
    slat_bottom = p.platform_height_mm - p.slat_thickness_mm
    box_top = slat_bottom - p.frame_thickness_mm
    rail_bottom = box_top - p.bed_moving_rail_height_mm
    lid_rear = rear
    if rail_bottom <= 0 or slat_bottom <= p.frame_thickness_mm or box_front <= rear + 2 * p.frame_thickness_mm:
        raise ValueError("The storage box needs positive internal height and width below its lid supports.")
    if p.frame_thickness_mm >= BOX_RAIL_RESERVE:
        raise ValueError("The moving plywood rail must fit within the reserved 20mm beside the box wall.")
    if front - lid_rear - p.bed_slat_rear_setback_mm - HINGE_SLAT_TRIM <= travel:
        raise ValueError("Shortened sliding slats must retain positive overlap at full bed extension.")
    if 2 * p.bed_lid_strip_width_mm >= p.long_bench_width_mm:
        raise ValueError("The two solid lid bands must leave positive ventilation slot length.")
    if gap >= COMB_TOOTH_OVERHANG or p.slat_width_mm <= 2 * COMB_TOOTH_OVERHANG:
        raise ValueError("Comb ledges need bearing under moving slats and clearance beside their rail spacers.")
    margin = (p.seat_length_mm - count * p.slat_width_mm - (count - 1) * gap) / 2
    ys = tuple(margin + i * (p.slat_width_mm + gap) for i in range(count))
    return BedLayout(ys, travel, rear, front, box_front, moving_front, slat_bottom, rail_bottom,
                     lid_rear, box_top)


def build_bed_slats(p: Parameters, layout: BedLayout, *, moving: bool) -> Compound:
    name = "Moving" if moving else "Fixed"
    # Retain the existing hidden slat blanks until their separate redesign.
    slat_length = layout.front - layout.lid_rear - p.bed_slat_rear_setback_mm - HINGE_SLAT_TRIM
    x = p.bed_slat_rear_setback_mm + HINGE_SLAT_TRIM
    slats = []
    for i in range(1 if moving else 0, len(layout.slat_ys), 2):
        if moving:
            slat = panel(slat_length, p.slat_width_mm, p.slat_thickness_mm)
        else:
            # Keep the existing bevel until the deferred slat redesign.
            thickness = p.slat_thickness_mm
            section = Face(Wire.make_polygon([
                (0, 0, 0), (slat_length, 0, 0), (slat_length, 0, thickness), (thickness, 0, thickness),
            ]))
            slat = Part([Solid.extrude(section, (0, p.slat_width_mm, 0))])
        slat.location = Location((x, layout.slat_ys[i], layout.slat_bottom - layout.box_top))
        slat.label, slat.color = f"{name} slat {i + 1:02}", WOOD if moving else FIXED_WOOD
        slats.append(slat)
    return Compound(label=f"{name} slats", children=slats)


def slat_support(p: Parameters, layout: BedLayout, name: str, x: float) -> Part:
    """Vertical plywood rail beneath the spacer blocks, spanning every moving row."""
    rail = panel(p.frame_thickness_mm, p.seat_length_mm, p.bed_moving_rail_height_mm)
    rail.label, rail.color = name, Color(0.88, 0.61, 0.25)
    rail.location = Location((x - layout.lid_rear, 0, layout.rail_bottom - layout.box_top))
    return rail


def build_sliding_bed(p: Parameters, layout: BedLayout) -> Compound:
    spacers = []
    for index, y in enumerate(layout.slat_ys[1::2], start=1):
        # Fit between the comb teeth, retaining the slat gap on each side while sliding.
        spacer = panel(p.frame_thickness_mm, p.slat_width_mm - 2 * COMB_TOOTH_OVERHANG, p.frame_thickness_mm)
        spacer.label, spacer.color = f"Rail spacer block {index:02}", Color(0.88, 0.61, 0.25)
        spacer.location = Location((layout.moving_front - layout.lid_rear, y + COMB_TOOTH_OVERHANG,
                                    0))
        spacers.append(spacer)
    legs = []
    # Unsourced removable table-leg envelopes; not a selected product or load rating.
    for index, y in enumerate((p.seat_length_mm * 0.15, p.seat_length_mm * 0.85), start=1):
        tube = Cylinder(p.bed_leg_diameter_mm / 2, layout.rail_bottom, align=(Align.CENTER, Align.CENTER, Align.MIN))
        tube -= Cylinder(
            max(0.1, p.bed_leg_diameter_mm / 2 - 1.5), layout.rail_bottom, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        tube.label, tube.color = f"Provisional metal leg {index}", METAL
        tube.location = Location((layout.moving_front - layout.lid_rear + p.frame_thickness_mm / 2,
                                  y, -layout.box_top))
        legs.append(tube)
    assembly = Compound(
        label="Sliding assembly",
        children=[
            build_bed_slats(p, layout, moving=True),
            Compound(label="Moving front slat support", children=[
                slat_support(p, layout, "Moving front slat rail", layout.moving_front), *spacers,
            ]),
            Compound(label="Provisional metal legs", children=legs),
        ],
    )
    assembly.location = Location((bed_offset(layout.travel, p.bed_extension_percent), 0, 0))
    return Compound(label="Sliding bed", children=[assembly])


def build_lid(p: Parameters, layout: BedLayout) -> Compound:
    strip = panel(p.long_bench_width_mm, p.seat_length_mm, p.frame_thickness_mm)
    band = p.bed_lid_strip_width_mm
    slot_length = p.long_bench_width_mm - 2 * band
    slot_width = p.slat_width_mm + 2 * p.slat_side_gap_mm - 2 * COMB_TOOTH_OVERHANG
    for y in layout.slat_ys[1::2]:
        slot = panel(slot_length, slot_width, p.frame_thickness_mm + 2)
        strip -= slot.moved(Location((band, y + COMB_TOOTH_OVERHANG - p.slat_side_gap_mm, -1)))
    strip.label, strip.color = "Slotted plywood lid", Color(0.88, 0.61, 0.25)
    lid = Compound(
        label="Hinged lid",
        children=[
            strip,
            build_bed_slats(p, layout, moving=False),
            build_sliding_bed(p, layout),
        ],
    )
    lid.location = lid_location(layout.lid_rear, layout.box_top, p.bed_lid_open_percent)
    return lid
