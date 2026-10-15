"""Long-bench sliding comb and bracket reliefs, ported from nv200-interior.fs."""

from dataclasses import dataclass
from math import floor, sqrt

from build123d import Color, Compound, Face, Location, Part, Polyline, ThreePointArc, Wire, extrude

from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


@dataclass(frozen=True)
class BedLayout:
    slat_ys: tuple[float, ...]
    bracket_ys: tuple[float, ...]
    travel: float
    strip_x: float
    rear_ledge_y: float
    strip_rear: float
    strip_front: float


def long_bed_layout(p: Parameters) -> BedLayout:
    wall_inner = p.wall_thickness_mm + p.frame_thickness_mm
    travel = p.bed_width_mm - p.long_bench_width_mm - p.frame_thickness_mm
    strip_x = p.long_bench_width_mm - p.frame_thickness_mm - p.sliding_strip_width_mm - travel
    setback = max(wall_inner, p.rear_corner_radius_mm + p.rear_corner_allowance_mm)
    rear, front = setback + p.strip_end_clearance_mm, p.seat_length_mm - wall_inner - p.strip_end_clearance_mm
    pitch = p.slat_width_mm + p.slat_side_gap_mm
    count = floor((p.seat_length_mm - p.slat_side_gap_mm) / pitch)
    if count % 2 == 0:
        count -= 1
    if count < 7 or count > 101:
        raise ValueError("Long bench needs 7–101 interleaving slats, including three moving slats for the brackets.")
    margin = (p.seat_length_mm - (count * p.slat_width_mm + (count - 1) * p.slat_side_gap_mm)) / 2
    ys = tuple(margin + i * pitch for i in range(count))
    if travel <= 0 or strip_x < wall_inner + p.slat_side_gap_mm:
        raise ValueError(
            "Bed width must allow extension while keeping the retracted tie strip between the fixed frames."
        )
    if p.strip_end_clearance_mm >= p.ledge_width_mm or setback + 2 * p.ledge_width_mm >= p.seat_length_mm - wall_inner:
        raise ValueError("Guide ledges need clear space between them and positive bearing under the tie strip.")
    if any(p.member_width_mm <= y < setback for y in ys[::2]):
        raise ValueError("A shortened rear fixed slat misses the rear support; adjust slat spacing or bench length.")
    if ys[1] + p.slat_width_mm <= rear or ys[-2] >= front:
        raise ValueError("The first and last moving slats must overlap the tie strip.")
    height = p.platform_height_mm - p.slat_thickness_mm
    if 2 * p.frame_thickness_mm > p.member_width_mm or height - 2 * p.frame_thickness_mm <= p.arch_height_mm:
        raise ValueError("Tie strip and ledges need room in the top band and above the wheel arch.")
    depth = p.bracket_thickness_mm + max(p.bracket_head_allowance_mm, p.bracket_bend_radius_mm) + p.bracket_clearance_mm
    if strip_x + p.sliding_strip_width_mm + p.bracket_clearance_mm > p.long_bench_width_mm - p.bracket_arm_mm:
        raise ValueError("Bracket arms must clear the moving tie strip.")
    if (
        p.bracket_width_mm + 2 * p.bracket_clearance_mm > p.slat_width_mm
        or p.bracket_arm_mm + p.bracket_clearance_mm >= p.member_width_mm
        or depth >= p.frame_thickness_mm
        or p.bracket_thickness_mm + p.bracket_bend_radius_mm >= p.bracket_arm_mm
    ):
        raise ValueError("Bracket dimensions must fit the slats and leave material below and behind the frame reliefs.")
    moving_ys = ys[1::2]
    centers = tuple(moving_ys[i] + p.slat_width_mm / 2 for i in (0, (len(moving_ys) - 1) // 2, len(moving_ys) - 1))
    return BedLayout(ys, centers, travel, strip_x, setback, rear, front)


def relieve_aisle_frame(frame: Part, p: Parameters, layout: BedLayout) -> Part:
    """Cut the fixed frame in panel-local coordinates, before its 90-degree placement."""
    height = p.platform_height_mm - p.slat_thickness_mm
    clearance = p.bracket_clearance_mm
    depth = p.bracket_thickness_mm + max(p.bracket_head_allowance_mm, p.bracket_bend_radius_mm) + clearance
    notch_width = p.bracket_width_mm + 2 * clearance
    for y in layout.bracket_ys:
        # Local Y=0 becomes the outer aisle face; local X follows the van's Y axis.
        frame -= panel(notch_width, p.frame_thickness_mm + 2 * clearance, depth + clearance).moved(
            Location((y - notch_width / 2, -clearance, height - depth))
        )
        frame -= panel(notch_width, depth + clearance, p.bracket_arm_mm + 2 * clearance).moved(
            Location((y - notch_width / 2, -clearance, height - p.bracket_arm_mm - clearance))
        )
    return frame


def angle_bracket(p: Parameters) -> Part:
    """Unmeasured steel envelope; origin at the outer top corner, arm extending in -X/-Z."""
    arm, thickness, radius = p.bracket_arm_mm, p.bracket_thickness_mm, p.bracket_bend_radius_mm
    start = (-thickness - radius, 0, -thickness)
    end = (-thickness, 0, -thickness - radius)
    top = Polyline((0, 0, 0), (-arm, 0, 0), (-arm, 0, -thickness), start)
    bend = ThreePointArc(
        start,
        (-thickness - radius + radius / sqrt(2), 0, -thickness - radius + radius / sqrt(2)),
        end,
    )
    side = Polyline(end, (-thickness, 0, -arm), (0, 0, -arm), (0, 0, 0))
    profile = Face(Wire([*top.edges(), *bend.edges(), *side.edges()]))
    return extrude(profile, amount=p.bracket_width_mm, dir=(0, 1, 0))


def build_sliding_bed(p: Parameters, layout: BedLayout) -> Compound:
    height = p.platform_height_mm - p.slat_thickness_mm
    thickness = p.frame_thickness_mm
    closed_width = p.long_bench_width_mm + thickness
    wall_inner = p.wall_thickness_mm + thickness
    fixed_inner = p.long_bench_width_mm - thickness
    fixed_slats: list[Part] = []
    moving_slats: list[Part] = []
    wood, moving_wood = Color(0.72, 0.52, 0.32), Color(0.87, 0.70, 0.43)

    for i, y in enumerate(layout.slat_ys):
        moving = i % 2 == 1
        start = p.wall_thickness_mm
        if not moving and y < layout.rear_ledge_y:
            start = (p.cargo_width_mm - p.arch_gap_mm) / 2 + p.drawer_arch_clearance_mm
        slat = panel(closed_width - start, p.slat_width_mm, p.slat_thickness_mm)
        slat.location = Location((start, y, height))
        slat.label = f"{'Moving' if moving else 'Fixed'} slat {i + 1:02}"
        slat.color = moving_wood if moving else wood
        (moving_slats if moving else fixed_slats).append(slat)

    bay = (p.seat_length_mm - 3 * p.member_width_mm) / 2
    frame = frame_panel(
        p.seat_length_mm,
        thickness,
        height,
        [
            (x, x + bay, -2 * p.inside_radius_mm, height - p.member_width_mm)
            for x in (p.member_width_mm, 2 * p.member_width_mm + bay)
        ],
        p.inside_radius_mm,
    )
    frame.location = Location((closed_width, 0, 0), (0, 0, 90))
    frame.label, frame.color = "Moving aisle frame", Color(0.88, 0.61, 0.25)
    strip = panel(p.sliding_strip_width_mm, layout.strip_front - layout.strip_rear, thickness)
    strip.location = Location((layout.strip_x, layout.strip_rear, height - thickness))
    strip.label, strip.color = "Tie strip / extension stop", moving_wood

    ledges = []
    # Both ledges reach the underside of the adjoining frame top rails.
    bottom = height - p.member_width_mm
    for name, y in (
        ("Rear guide ledge", layout.rear_ledge_y),
        ("Cab-end guide ledge", p.seat_length_mm - wall_inner - p.ledge_width_mm),
    ):
        ledge = panel(fixed_inner - wall_inner, p.ledge_width_mm, height - thickness - bottom)
        ledge.location = Location((wall_inner, y, bottom))
        ledge.label, ledge.color = name, wood
        ledges.append(ledge)
    brackets = []
    for i, y in enumerate(layout.bracket_ys):
        bracket = angle_bracket(p)
        bracket.location = Location((p.long_bench_width_mm, y - p.bracket_width_mm / 2, height))
        bracket.label, bracket.color = f"Angle bracket {i + 1}", Color(0.62, 0.66, 0.70)
        brackets.append(bracket)

    moving_assembly = Compound(
        label="Sliding assembly",
        children=[
            Compound(label="Moving slats", children=moving_slats),
            frame,
            strip,
            Compound(label="Angle brackets", children=brackets),
        ],
    )
    moving_assembly.location = Location((layout.travel * p.bed_extension_percent / 100, 0, 0))
    return Compound(
        label="Sliding bed",
        children=[
            Compound(label="Fixed slats", children=fixed_slats),
            Compound(label="Guide ledges", children=ledges),
            moving_assembly,
        ],
    )
