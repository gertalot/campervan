"""Fixed long-bench plywood, following nv200-interior.fs carcass and drawer supports."""

from math import sqrt

from build123d import Color, Compound, Location, Part

from campervan.cad.panels import frame_panel, panel
from campervan.cad.sliding_bed import build_sliding_bed, long_bed_layout, relieve_aisle_frame
from campervan.parameters import Parameters


def build_long_bench(p: Parameters) -> Compound:
    layout = long_bed_layout(p)
    width, length = p.long_bench_width_mm, p.seat_length_mm
    height = p.platform_height_mm - p.slat_thickness_mm
    thickness, skin = p.frame_thickness_mm, p.wall_thickness_mm
    member, radius = p.member_width_mm, p.inside_radius_mm
    total = thickness + skin
    setback = p.rear_corner_radius_mm + p.rear_corner_allowance_mm
    rear_end = max(p.arch_rear_offset_mm - p.arch_clearance_mm, setback + member)
    post_start = p.arch_rear_offset_mm + p.arch_length_mm + p.arch_clearance_mm
    post_end = post_start + member
    internal_x = (p.cargo_width_mm - p.arch_gap_mm) / 2 + p.drawer_arch_clearance_mm
    internal_length = length - total

    if rear_end >= p.arch_rear_offset_mm or post_end > length - member:
        raise ValueError("Wheel arch and rear corner leave insufficient room for the bench wall supports.")
    if p.arch_height_mm > height - member:
        raise ValueError("Wheel arch reaches above the underside of the bench top band.")
    end_clearance = min(p.arch_rear_offset_mm - rear_end, p.arch_clearance_mm)
    if end_clearance < radius:
        corner_height = height - member - radius + sqrt(radius**2 - (radius - end_clearance) ** 2)
        if p.arch_height_mm > corner_height:
            raise ValueError("Wheel arch intersects the rounded wall-frame opening corners.")
    if internal_x <= max(total, setback) or internal_x + thickness >= width - thickness:
        raise ValueError("Internal drawer support must clear the rear corner and leave a rear opening.")
    if p.drawer_frame_height_mm >= height - 2 * thickness or member >= setback:
        raise ValueError("Drawer support must leave room below the bed and behind the rear corner setback.")

    parts: list[Part] = []

    def place(part: Part, name: str, x: float, y: float, z: float = 0, rotation: float = 0) -> None:
        part.label = name
        part.color = Color(0.88, 0.61, 0.25)
        part.location = Location((x, y, z), (0, 0, rotation))
        parts.append(part)

    def slide_frame(span: float, top: float) -> Part:
        bay = (span - 3 * member) / 2
        return frame_panel(
            span,
            thickness,
            top,
            [(start, start + bay, p.drawer_mount_band_mm, top - member) for start in (member, 2 * member + bay)],
            radius,
        )

    wall_openings = [
        (rear_end - setback, post_start - setback, -2 * radius, height - member),
        (post_end - setback, length - member - setback, -2 * radius, height - member),
    ]
    wall = frame_panel(length - setback, thickness, height, wall_openings, radius)
    place(wall, "Wall-side frame", total, setback, rotation=90)
    place(relieve_aisle_frame(slide_frame(length, height), p, layout), "Aisle frame", width, 0, rotation=90)

    end_width = width - total - thickness
    end_frame = frame_panel(
        end_width, thickness, height, [(member, end_width - member, -2 * radius, height - member)], radius
    )
    place(end_frame, "Cab-end frame", total, length - total)
    place(panel(end_width, skin, height), "Cab-end skin", total, length - skin)
    parts[-1].color = Color(0.75, 0.66, 0.49)

    # The raised rear post and mounting frame are one cut plywood piece in the source.
    internal = slide_frame(internal_length, p.drawer_frame_height_mm)
    internal += panel(member, thickness, height - p.drawer_frame_height_mm).moved(
        Location((0, 0, p.drawer_frame_height_mm))
    )
    place(internal, "Internal drawer-support frame", internal_x + thickness, 0, rotation=90)
    place(
        panel(width - thickness - internal_x - thickness, thickness, member),
        "Rear header",
        internal_x + thickness,
        0,
        height - member,
    )
    return Compound(
        label="Long bench",
        children=[Compound(label="Fixed frame", children=parts), build_sliding_bed(p, layout)],
    )
