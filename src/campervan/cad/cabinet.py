"""Straight stepped plywood frames with skins scribed to the van interior."""

from math import floor

from build123d import Color, Compound, Edge, Location, Part

from campervan.cad.body import ceiling_height, interior_limits
from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


def build_cabinet(p: Parameters) -> Compound:
    x = p.bed_width_mm
    width, length = p.cargo_width_mm - x, p.cabinet_length_mm
    thickness, skin, member = p.frame_thickness_mm, p.wall_thickness_mm, p.member_width_mm
    radius = p.inside_radius_mm
    total = thickness + skin
    arch_front = p.arch_rear_offset_mm + p.arch_length_mm
    if length > min(p.seat_length_mm, p.body_length_mm) or length <= 2 * total or width <= thickness + total:
        raise ValueError("Cabinet must fit beside the bed and leave room between its end panels.")
    if p.arch_rear_offset_mm < total or length - total < arch_front:
        raise ValueError("Cabinet end panels must clear the wheel arch.")

    # A flat frame top below the lowest plywood edge; the skins follow its shallow curve.
    height = ceiling_height(p, p.cargo_width_mm, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
    bed_rail = p.platform_height_mm - p.slat_thickness_mm
    step = p.cabinet_frame_step_height_mm
    opening_heights = ((member, bed_rail - member), (bed_rail, step - member), (step, height - member))
    if any(top - bottom <= 2 * radius for bottom, top in opening_heights):
        raise ValueError("Cabinet shelf rails must leave room for rounded openings below, between and above them.")
    body, ceiling = interior_limits(p, p.cabinet_ceiling_gap_mm)
    room = body & ceiling
    parts: list[Part] = []

    def place(part: Part, name: str, placement: Location) -> None:
        part.label = name
        part.color = Color(0.88, 0.61, 0.25)
        part.location = placement
        parts.append(part)

    bay = (length - 3 * member) / 2
    aisle = frame_panel(
        length,
        thickness,
        height,
        [(start, start + bay, bottom, top) for start in (member, 2 * member + bay) for bottom, top in opening_heights],
        radius,
    )
    place(aisle, "Aisle frame", Location((x + thickness, 0, 0), (0, 0, 90)))

    def frame_width(frame_y: float, z: float) -> float:
        # The rear body widens toward the cab. Check both faces of the flat stock,
        # and round inward to whole millimetres instead of scribing a curved edge.
        widths = []
        for y in (frame_y, frame_y + thickness):
            line = Edge.make_line((x + thickness, y, z), (p.cargo_width_mm, y, z))
            section = room & line
            if not section.edges():
                raise ValueError("Cabinet frame lies outside the wall or ceiling profile.")
            widths.append(section.bounding_box().max.X - x - thickness)
        return float(floor(min(widths)))

    for name, frame_y, skin_y in (("Rear", skin, 0), ("Cab-end", length - total, length - skin)):
        lower_width = frame_width(frame_y, step)
        upper_width = frame_width(frame_y, height)
        if upper_width <= 2 * member or lower_width < upper_width:
            raise ValueError("Cabinet is too narrow for the stepped frame and its upper opening.")
        # The same rounded-opening primitive also rounds the step's inside corner.
        openings = [
            (member, (upper_width if bottom >= step else lower_width) - member, bottom, top)
            for bottom, top in opening_heights
        ]
        if lower_width > upper_width:
            openings.append((upper_width, lower_width + 2 * radius, step, height + 2 * radius))
        frame = frame_panel(lower_width, thickness, height, openings, radius)
        place(frame, f"{name} frame", Location((x + thickness, frame_y, 0)))
        blank = panel(width - thickness, skin, p.body_height_mm).moved(Location((x + thickness, skin_y, 0)))
        parts.append(Part((blank & room).solids(), label=f"{name} skin", color=Color(0.75, 0.66, 0.49)))
    return Compound(label="Cabinet", children=parts)
