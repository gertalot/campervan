"""Slotted plywood storage lid, lifted by a photo-derived four-bar pair."""

from dataclasses import dataclass
from math import floor

from build123d import Align, Axis, Color, Compound, Cylinder, Face, Location, Part, Solid, Wire, fillet

from campervan.cad.bed_motion import bed_offset
from campervan.cad.bed_lift import RAIL_WIDTH, lid_location
from campervan.cad.cross_bench_layout import LAGUN_BRACKET_WIDTH
from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters

WOOD = Color(0.87, 0.70, 0.43)
FIXED_WOOD = Color(0.72, 0.52, 0.32)
HINGE_SLAT_TRIM = 5.0
COMB_TOOTH_OVERHANG = 20.0
BOX_RAIL_RESERVE = 20.0
MOVING_FRAME_UPSTAND = 50.0
SIDE_RAIL_END_RADIUS = 10.0
FIXED_SLAT_END_TRIM = 10.0
FIXED_SLAT_GROOVE_DEPTH = 8.0
FIXED_SLAT_GROOVE_CLEARANCE = 2.0
# Existing Carinya 3962402 angles: nominal envelope; fixing-hole pattern is illustrative.
SLAT_BRACKET_ARM = 50.0
SLAT_BRACKET_WIDTH = 40.0
SLAT_BRACKET_THICKNESS = 2.0
SLAT_BRACKET_CLEARANCE = 1.0
TABLE_MOUNT_CLEARANCE = 5.0


@dataclass(frozen=True)
class BedLayout:
    slat_ys: tuple[float, ...]
    travel: float
    rear: float
    front: float
    box_front: float
    moving_front: float
    slat_bottom: float
    lid_rear: float
    box_top: float
    rear_panel_y: float
    moving_support_length: float


def lid_slots(p: Parameters, slat_ys: tuple[float, ...]) -> tuple[tuple[float, float], ...]:
    """Shared transverse slot bounds for cutting the lid and placing its supports."""
    width = p.slat_width_mm + 2 * p.slat_side_gap_mm - 2 * COMB_TOOTH_OVERHANG
    starts = (y + COMB_TOOTH_OVERHANG - p.slat_side_gap_mm for y in slat_ys[1::2])
    return tuple((start, start + width) for start in starts)


def rear_wall_corner_cutter(cut: float, height: float) -> Solid:
    """Trim the rear/wall corner to X + Y = cut, through the whole thickness."""
    outline = Wire.make_polygon([(-1, -1, -1), (cut + 1, -1, -1), (-1, cut + 1, -1)])
    return Solid.extrude(Face(outline), (0, 0, height + 2))


def long_bed_layout(p: Parameters) -> BedLayout:
    gap = p.slat_side_gap_mm
    rear = p.long_bench_inset_mm + p.frame_thickness_mm
    # Use one aisle-edge datum for the lid, both slat sets and the moving rail.
    front = rear + p.long_bench_width_mm
    moving_front = front - p.frame_thickness_mm
    # Retain the existing box-wall position while aligning the parts above it.
    box_front = p.long_bench_width_mm + p.frame_thickness_mm - BOX_RAIL_RESERVE
    travel = p.bed_width_mm - front
    count = floor((p.seat_length_mm + gap) / (p.slat_width_mm + gap))
    if count % 2 == 0:
        count -= 1
    if count < 3 or travel <= 0:
        raise ValueError("The slat lid needs at least three interleaving slats and positive extension travel.")
    slat_bottom = p.platform_height_mm - p.slat_thickness_mm
    box_top = slat_bottom - p.frame_thickness_mm
    lid_rear = rear
    if (p.bed_moving_rail_height_mm >= slat_bottom or slat_bottom <= p.frame_thickness_mm
            or box_front <= rear + 2 * p.frame_thickness_mm):
        raise ValueError("The storage box needs positive internal height and width below its lid supports.")
    if p.frame_thickness_mm >= BOX_RAIL_RESERVE:
        raise ValueError("The moving plywood rail must fit within the reserved 20mm beside the box wall.")
    if front - lid_rear - p.bed_slat_rear_setback_mm - HINGE_SLAT_TRIM - 2 * p.frame_thickness_mm <= travel:
        raise ValueError("Shortened sliding slats must retain positive overlap at full bed extension.")
    if 2 * p.bed_lid_strip_width_mm >= p.long_bench_width_mm:
        raise ValueError("The two solid lid bands must leave positive ventilation slot length.")
    if p.bed_lid_strip_width_mm <= p.frame_thickness_mm:
        raise ValueError("The aisle-side lid band must retain wood after the moving rail recess.")
    if p.bed_lid_strip_width_mm - p.frame_thickness_mm < SLAT_BRACKET_ARM + SLAT_BRACKET_CLEARANCE:
        raise ValueError("The aisle-side lid band must accommodate the bracket flanges and clearance.")
    if p.slat_width_mm < SLAT_BRACKET_WIDTH + 2 * SLAT_BRACKET_CLEARANCE:
        raise ValueError("Moving slats must accommodate their angle brackets and side clearances.")
    if p.bed_moving_rail_height_mm < SLAT_BRACKET_ARM:
        raise ValueError("The moving frame top rail must support the complete bracket flange.")
    if p.frame_thickness_mm <= SLAT_BRACKET_THICKNESS + SLAT_BRACKET_CLEARANCE:
        raise ValueError("The lid must retain plywood below its bracket rebates.")
    if (p.frame_thickness_mm <= FIXED_SLAT_GROOVE_DEPTH
            or p.frame_thickness_mm - FIXED_SLAT_END_TRIM > FIXED_SLAT_GROOVE_DEPTH):
        raise ValueError("The shortened fixed slat ends must fit the blind grooves while leaving an outer rail face.")
    if p.slat_thickness_mm + FIXED_SLAT_GROOVE_CLEARANCE >= MOVING_FRAME_UPSTAND:
        raise ValueError("The rail must retain wood above the fixed-slat grooves.")
    if gap >= COMB_TOOTH_OVERHANG or p.slat_width_mm <= 2 * COMB_TOOTH_OVERHANG:
        raise ValueError("Comb ledges need bearing under moving slats and clearance beside their rail spacers.")
    margin = (p.seat_length_mm - count * p.slat_width_mm - (count - 1) * gap) / 2
    ys = tuple(margin + i * (p.slat_width_mm + gap) for i in range(count))
    moving_support_length = p.seat_length_mm - LAGUN_BRACKET_WIDTH - 2 * TABLE_MOUNT_CLEARANCE
    last_bracket_end = ys[-2] + (p.slat_width_mm + SLAT_BRACKET_WIDTH) / 2
    if last_bracket_end + TABLE_MOUNT_CLEARANCE > moving_support_length:
        raise ValueError("The shortened sliding frame must support the last bracket beside the Lagun mount.")
    # Move the rear end wall beyond the rear corner and beneath a complete
    # transverse plywood rib. Its inside-mounted lift rail needs solid wood too.
    slots = lid_slots(p, ys)
    if any(end - start < SLAT_BRACKET_WIDTH + 2 * SLAT_BRACKET_CLEARANCE for start, end in slots):
        raise ValueError("Ventilation slots must be wide enough for the bracket rebates and clearance.")
    solid_starts = (0.0, *(end for _, end in slots))
    solid_ends = (*(start for start, _ in slots), p.seat_length_mm)
    pillar_end = max(0.0, p.rear_corner_radius_mm - p.furniture_rear_gap_mm)
    rear_panel_y = next((start for start, end in zip(solid_starts, solid_ends, strict=True)
                         if start >= pillar_end and end - start >= p.frame_thickness_mm + RAIL_WIDTH
                         and start + p.frame_thickness_mm < (p.seat_length_mm - p.frame_thickness_mm) / 2), None)
    if rear_panel_y is None:
        raise ValueError("Rear box wall and lift rail need a solid lid rib ahead of the rear pillar and behind the divider.")
    return BedLayout(ys, travel, rear, front, box_front, moving_front, slat_bottom,
                     lid_rear, box_top, rear_panel_y, moving_support_length)


def build_bed_slats(p: Parameters, layout: BedLayout, *, moving: bool) -> Compound:
    name = "Moving" if moving else "Fixed"
    # Both slat sets reach back across the space freed by the removed hinge strip.
    slat_length = (layout.front - layout.lid_rear - p.bed_slat_rear_setback_mm
                   - HINGE_SLAT_TRIM - p.frame_thickness_mm)
    if moving:
        slat_length -= p.frame_thickness_mm  # Butt against the raised frame instead of overlapping it.
    else:
        slat_length -= FIXED_SLAT_END_TRIM
    x = p.bed_slat_rear_setback_mm + HINGE_SLAT_TRIM + p.frame_thickness_mm
    slats = []
    for i in range(1 if moving else 0, len(layout.slat_ys), 2):
        slat = panel(slat_length, p.slat_width_mm, p.slat_thickness_mm)
        if not moving and i == 0:
            slat -= rear_wall_corner_cutter(p.slat_width_mm / 2, p.slat_thickness_mm)
        slat.location = Location((x, layout.slat_ys[i], layout.slat_bottom - layout.box_top))
        slat.label, slat.color = f"{name} slat {i + 1:02}", WOOD if moving else FIXED_WOOD
        slats.append(slat)
    return Compound(label=f"{name} slats", children=slats)


def slat_support(p: Parameters, layout: BedLayout, name: str, x: float) -> Part:
    """Smooth-faced frame ending before the cab-end Lagun mounting area."""
    length, member, radius = layout.moving_support_length, p.member_width_mm, p.inside_radius_mm
    rail = frame_panel(length, p.frame_thickness_mm, layout.slat_bottom + MOVING_FRAME_UPSTAND,
                       [(member, length - member, -2 * radius,
                         layout.slat_bottom - p.bed_moving_rail_height_mm)], radius)
    rail = fillet(rail.edges().filter_by(Axis.Y).group_by(Axis.Z)[-1], SIDE_RAIL_END_RADIUS)
    clearance = FIXED_SLAT_GROOVE_CLEARANCE
    for y in layout.slat_ys[::2]:
        if y + p.slat_width_mm + clearance > length:
            continue
        groove = panel(p.slat_width_mm + 2 * clearance, FIXED_SLAT_GROOVE_DEPTH + 1,
                       p.slat_thickness_mm + 2 * clearance)
        groove = fillet(groove.edges().filter_by(Axis.Y), clearance)
        # The rotated frame's inner face is native Y=thickness; leave the outer face intact.
        rail -= groove.moved(Location((y - clearance, p.frame_thickness_mm - FIXED_SLAT_GROOVE_DEPTH,
                                       layout.slat_bottom - clearance)))
    rail.label, rail.color = name, Color(0.88, 0.61, 0.25)
    rail.location = Location((x - layout.lid_rear + p.frame_thickness_mm, 0, -layout.box_top),
                             (0, 0, 90))
    return rail


def slat_brackets(p: Parameters, layout: BedLayout) -> Compound:
    """One angle under each moving slat, attached to the frame's wall-side face."""
    arm, width, thickness = SLAT_BRACKET_ARM, SLAT_BRACKET_WIDTH, SLAT_BRACKET_THICKNESS
    angles = []
    for index, y in enumerate(layout.slat_ys[1::2], start=1):
        angle = panel(arm, width, thickness).moved(Location((0, 0, -thickness)))
        angle += panel(thickness, width, arm).moved(Location((arm - thickness, 0, -arm)))
        # Show two fixings per flange; confirm actual supplied hole positions before drilling timber.
        for hole_y in (width / 4, 3 * width / 4):
            angle -= Cylinder(2.5, thickness + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
                Location((arm / 2, hole_y, -thickness - 1)))
            angle -= Cylinder(2.5, thickness + 2, rotation=(0, 90, 0),
                              align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
                Location((arm - thickness - 1, hole_y, -arm / 2)))
        angle.label, angle.color = f"Slat angle bracket {index:02}", Color(0.64, 0.67, 0.70)
        angle.location = Location((layout.moving_front - layout.lid_rear - arm,
                                   y + (p.slat_width_mm - width) / 2,
                                   layout.slat_bottom - layout.box_top))
        angles.append(angle)
    return Compound(label="Slat angle brackets", children=angles)


def build_sliding_bed(p: Parameters, layout: BedLayout) -> Compound:
    assembly = Compound(
        label="Sliding assembly",
        children=[
            build_bed_slats(p, layout, moving=True),
            Compound(label="Moving front slat support", children=[
                slat_support(p, layout, "Moving support frame", layout.moving_front),
                slat_brackets(p, layout),
            ]),
        ],
    )
    assembly.location = Location((bed_offset(layout.travel, p.bed_extension_percent), 0, 0))
    return Compound(label="Sliding bed", children=[assembly])


def build_lid(p: Parameters, layout: BedLayout) -> Compound:
    width = p.long_bench_width_mm - p.frame_thickness_mm
    strip = panel(width, p.seat_length_mm, p.frame_thickness_mm)
    # Continue the first fixed slat's 45° cut through the plywood, accounting
    # for the slat's wall setback and the rear row margin.
    corner_cut = (p.bed_slat_rear_setback_mm + HINGE_SLAT_TRIM + p.frame_thickness_mm
                  + layout.slat_ys[0] + p.slat_width_mm / 2)
    strip -= rear_wall_corner_cutter(corner_cut, p.frame_thickness_mm)
    band = p.bed_lid_strip_width_mm
    slot_length = p.long_bench_width_mm - 2 * band
    for start, end in lid_slots(p, layout.slat_ys):
        slot = panel(slot_length, end - start, p.frame_thickness_mm + 2)
        strip -= slot.moved(Location((band, start, -1)))
    slot_end = band + slot_length
    notch_depth = width - slot_end
    rebate_depth = SLAT_BRACKET_THICKNESS + SLAT_BRACKET_CLEARANCE
    for start_y, end_y in lid_slots(p, layout.slat_ys):
        notch_width = end_y - start_y
        # Join each slot to the aisle edge with a matching-width shallow rebate.
        rebate = panel(notch_depth + 1, notch_width, rebate_depth + 1)
        strip -= rebate.moved(Location((slot_end, start_y, p.frame_thickness_mm - rebate_depth)))
        # Only the vertical flange needs clearance through the narrow aisle edge.
        edge_relief = panel(rebate_depth + 1, notch_width, p.frame_thickness_mm + 2)
        strip -= edge_relief.moved(Location((width - rebate_depth, start_y, -1)))
    strip.label, strip.color = "Slotted plywood lid", Color(0.88, 0.61, 0.25)
    retainer = panel(p.frame_thickness_mm, p.seat_length_mm - corner_cut, MOVING_FRAME_UPSTAND)
    retainer = fillet(retainer.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], SIDE_RAIL_END_RADIUS)
    retainer.label, retainer.color = "Wall-side cushion rail", Color(0.88, 0.61, 0.25)
    retainer.location = Location((0, corner_cut, p.frame_thickness_mm))
    lid = Compound(
        label="Hinged lid",
        children=[
            strip,
            retainer,
            build_bed_slats(p, layout, moving=False),
            build_sliding_bed(p, layout),
        ],
    )
    lid.location = lid_location(layout.lid_rear, layout.box_top, p.bed_lid_open_percent)
    return lid
