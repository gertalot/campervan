"""Fixed long-bench plywood, following nv200-interior.fs carcass and drawer supports."""

from math import sqrt

from build123d import Color, Compound, Location, Part

from campervan.cad.cushions import build_cushions
from campervan.cad.drawer import build_rear_drawer, drawer_support_x
from campervan.cad.panels import frame_panel, panel, slide_mount_frame
from campervan.cad.sliding_bed import build_bed_slats, build_sliding_bed, long_bed_layout, relieve_aisle_frame
from campervan.parameters import Parameters


def build_long_bench(p: Parameters) -> Compound:
    layout = long_bed_layout(p)
    width, length = p.long_bench_width_mm, p.seat_length_mm
    height = p.platform_height_mm - p.slat_thickness_mm
    thickness = p.frame_thickness_mm
    member, radius = p.member_width_mm, p.inside_radius_mm
    total = thickness + p.long_bench_inset_mm
    # Build in bed-local coordinates; vehicle references stay at the rear-door datum.
    setback = max(0, p.rear_corner_radius_mm + p.rear_corner_allowance_mm - p.furniture_rear_gap_mm)
    arch_rear = p.arch_rear_offset_mm - p.furniture_rear_gap_mm
    rear_end = max(arch_rear - p.arch_clearance_mm, setback + member)
    post_start = arch_rear + p.arch_length_mm + p.arch_clearance_mm
    post_end = post_start + member
    internal_x = drawer_support_x(p)

    if rear_end >= arch_rear or post_end > length - member:
        raise ValueError("Wheel arch and rear corner leave insufficient room for the bench wall supports.")
    if p.arch_height_mm > height - member:
        raise ValueError("Wheel arch reaches above the underside of the bench top band.")
    end_clearance = min(arch_rear - rear_end, p.arch_clearance_mm)
    if end_clearance < radius:
        corner_height = height - member - radius + sqrt(radius**2 - (radius - end_clearance) ** 2)
        if p.arch_height_mm > corner_height:
            raise ValueError("Wheel arch intersects the rounded wall-frame opening corners.")
    if internal_x <= max(total, setback) or internal_x + thickness >= width - thickness:
        raise ValueError("Internal drawer support must clear the rear corner and leave a rear opening.")

    if p.drawer_frame_height_mm >= height - member:
        raise ValueError("Drawer support must leave room below the guide ledges.")

    parts: list[Part] = []

    def place(part: Part, name: str, x: float, y: float, z: float = 0, rotation: float = 0) -> None:
        part.label = name
        part.color = Color(0.88, 0.61, 0.25)
        part.location = Location((x, y, z), (0, 0, rotation))
        parts.append(part)

    wall_openings = [
        (rear_end - setback, post_start - setback, -2 * radius, height - member),
        (post_end - setback, length - member - setback, -2 * radius, height - member),
    ]
    wall = frame_panel(length - setback, thickness, height, wall_openings, radius)
    place(wall, "Wall-side frame", total, setback, rotation=90)
    aisle = slide_mount_frame(length, thickness, height, member, p.drawer_mount_band_mm, radius)
    place(relieve_aisle_frame(aisle, p, layout), "Aisle frame", width, 0, rotation=90)

    end_width = width - internal_x - 2 * thickness
    end_frame = frame_panel(
        end_width, thickness, height, [(member, end_width - member, -2 * radius, height - member)], radius
    )
    place(end_frame, "Cab-end frame", internal_x + thickness, length - thickness)

    # This stationary bed support stays in place when the drawer module is removed.
    support = slide_mount_frame(
        length, thickness, p.drawer_frame_height_mm, member, p.drawer_mount_band_mm, radius
    )
    support += panel(member, thickness, height - p.drawer_frame_height_mm).moved(
        Location((0, 0, p.drawer_frame_height_mm))
    )
    place(support, "Internal drawer-support frame", internal_x + thickness, 0, rotation=90)

    place(
        panel(width - thickness - internal_x - thickness, thickness, member),
        "Rear header",
        internal_x + thickness,
        0,
        height - member,
    )
    ledges = []
    # Stationary guides extend down to the underside of the frame's top rails.
    bottom = height - member
    for name, y in (
        ("Rear guide ledge", layout.rear_ledge_y),
        ("Cab-end guide ledge", length - total - p.ledge_width_mm),
    ):
        ledge = panel(width - thickness - total, p.ledge_width_mm, height - thickness - bottom)
        ledge.location = Location((total, y, bottom))
        ledge.label, ledge.color = name, Color(0.72, 0.52, 0.32)
        ledges.append(ledge)
    fixed_frame = Compound(
        label="Fixed frame",
        children=[*parts, build_bed_slats(p, layout, moving=False), Compound(label="Guide ledges", children=ledges)],
    )
    return Compound(
        label="Long bench",
        children=[fixed_frame, build_sliding_bed(p, layout), build_rear_drawer(p), build_cushions(p, "Long bench")],
    )
