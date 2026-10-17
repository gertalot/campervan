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
    # Cabinet geometry is furniture-local; scribe against vehicle geometry
    # translated into the same coordinates before placing the finished assembly.
    gap = p.furniture_rear_gap_mm
    arch_rear = p.arch_rear_offset_mm - gap
    arch_front = arch_rear + p.arch_length_mm
    if length > min(p.seat_length_mm, p.body_length_mm - gap) or length <= 2 * total or width <= thickness + total:
        raise ValueError("Cabinet must fit beside the bed and leave room between its end panels.")
    if arch_rear < total or length - total < arch_front:
        raise ValueError("Cabinet end panels must clear the wheel arch.")

    # A flat frame top below the lowest plywood edge; the skins follow its shallow curve.
    height = ceiling_height(p, p.cargo_width_mm, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
    bed_rail = p.platform_height_mm - p.slat_thickness_mm
    step = p.cabinet_frame_step_height_mm
    upper_rail = (step + height) / 2
    shelf_levels = (bed_rail, step, upper_rail)
    opening_heights = tuple(
        zip(
            (member, *shelf_levels),
            (bed_rail - member, step - member, upper_rail - member, height - member),
            strict=True,
        )
    )
    if any(top - bottom <= 2 * radius for bottom, top in opening_heights):
        raise ValueError("Cabinet shelf rails must leave room for rounded openings below, between and above them.")
    body, ceiling = interior_limits(p, p.cabinet_ceiling_gap_mm)
    room = (body & ceiling).moved(Location((0, -gap, 0)))
    shelf_thickness, ledge = p.cabinet_shelf_thickness_mm, p.cabinet_ledge_size_mm
    if shelf_thickness + ledge > member:
        raise ValueError("Shelf thickness and ledge must fit within the frame cross-beam height.")
    arch_left = (p.cargo_width_mm + p.arch_gap_mm) / 2
    clearance = 3.0
    arch_cutout = panel(
        p.cargo_width_mm - arch_left + 2 * clearance,
        p.arch_length_mm + 2 * clearance,
        p.arch_height_mm + clearance,
    ).moved(Location((arch_left - clearance, arch_rear - clearance, 0)))
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

    middle_y = (length - thickness) / 2
    frame_widths = {}
    for name, frame_y, skin_y in (
        ("Rear", skin, 0),
        ("Middle", middle_y, None),
        ("Cab-end", length - total, length - skin),
    ):
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
        if name == "Middle" and frame_y < arch_front and frame_y + thickness > arch_rear:
            # Narrow the lowest opening so a full-width upright lands beside the arch.
            foot_width = arch_left - clearance - x - thickness
            beam_bottom = bed_rail - member
            if beam_bottom - radius < p.arch_height_mm + clearance:
                raise ValueError("The middle frame's lower cross-beam must clear the wheel arch and corner radius.")
            openings[0] = (member, foot_width - member, member, beam_bottom)
            # Carry the beam's straight underside out to the wall, without a hanging stub.
            openings.append(
                (
                    foot_width,
                    lower_width + 2 * radius,
                    -2 * radius,
                    beam_bottom,
                )
            )
        frame = frame_panel(lower_width, thickness, height, openings, radius)
        place(frame, f"{name} frame", Location((x + thickness, frame_y, 0)))
        frame_widths[name] = (lower_width, upper_width)
        if skin_y is not None:
            blank = panel(width - thickness, skin, p.body_height_mm).moved(Location((x + thickness, skin_y, 0)))
            parts.append(Part((blank & room).solids(), label=f"{name} skin", color=Color(0.75, 0.66, 0.49)))

    shelves, ledges = [], []
    for bay_name, start, end, end_names in (
        ("Rear", total, middle_y, ("Rear", "Middle")),
        ("Cab-end", middle_y + thickness, length - total, ("Middle", "Cab-end")),
    ):
        if end - start <= 2 * ledge:
            raise ValueError("Cabinet bays must leave room between the shelf ledges.")
        for level_name, rail_z in zip(("Lower", "Middle", "Upper"), shelf_levels, strict=True):
            ledge_z = rail_z - member
            shelf_z = ledge_z + ledge
            label = f"{bay_name} {level_name.lower()}"
            blank = panel(width - thickness, end - start, shelf_thickness).moved(
                Location((x + thickness, start, shelf_z))
            )
            shelves.append(Part(((blank & room) - arch_cutout).solids(), label=label, color=Color(0.75, 0.66, 0.49)))
            for frame_name, ledge_y in zip(end_names, (start, end - ledge), strict=True):
                support_width = frame_widths[frame_name][int(rail_z >= step)]
                if frame_name == "Middle" and ledge_z < p.arch_height_mm + clearance + radius:
                    support_width = min(support_width, arch_left - clearance - radius - x - thickness)
                support = panel(support_width, ledge, ledge).moved(Location((x + thickness, ledge_y, ledge_z)))
                support.label, support.color = f"{label} {frame_name.lower()} ledge", Color(0.88, 0.61, 0.25)
                ledges.append(support)
            support = panel(ledge, end - start - 2 * ledge, ledge).moved(
                Location((x + thickness, start + ledge, ledge_z))
            )
            support.label, support.color = f"{label} aisle ledge", Color(0.88, 0.61, 0.25)
            ledges.append(support)
    return Compound(
        label="Cabinet",
        children=[*parts, Compound(label="Shelf ledges", children=ledges), Compound(label="Shelves", children=shelves)],
    )
