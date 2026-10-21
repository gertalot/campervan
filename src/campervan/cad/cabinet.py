"""Bonded plywood cabinet with independent rear rails, a rear upright and fixed shelves."""

from build123d import Color, Compound, Edge, Face, Location, Part, Plane, Side, Solid, Wire

from campervan.cad.body import body_section, ceiling_height, ceiling_space, interior_limits
from campervan.cad.cabinet_doors import build_cabinet_doors, cabinet_aisle_x, cabinet_door_strikes
from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


def cabinet_back_profile(p: Parameters, inset: float) -> Wire:
    """One bend across the sheet height, bridging recesses and clearing projecting side posts.

    Construct against the actual left side, then reflect into furniture-local coordinates.
    The top meets the plywood underside. Recesses are bridged, not followed.
    """
    start = max(p.furniture_rear_gap_mm, p.rear_corner_radius_mm + p.cabinet_back_clearance_mm)
    end = p.furniture_rear_gap_mm + p.cabinet_length_mm
    front = p.body_length_mm - p.left_door_front_offset_mm
    rear_post = front - p.side_opening_width_mm
    intrusion = p.roof_rail_intrusion_mm
    if start < rear_post and end > rear_post - p.side_pillar_width_mm:
        intrusion = max(intrusion, p.side_pillar_intrusion_mm)
    if end > front - p.side_opening_radius_mm:
        intrusion = max(intrusion, p.front_pillar_intrusion_mm)
    lower, upper = body_section(p, 0)[:2]
    curve = Wire([Edge.make_line(lower.position_at(0), lower.position_at(1)), upper])
    curve = curve.moved(Location((intrusion, 0, 0))).offset_2d(inset, side=Side.RIGHT, closed=False)
    # Trim each face at the actual curved plywood underside.
    if curve.position_at(0).Z > curve.position_at(1).Z:
        curve = Wire([edge.reversed() for edge in reversed(Wire(curve.edges()).order_edges())])
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        point = curve.position_at(mid)
        if point.Z < ceiling_height(p, point.X, p.ceiling_ply_thickness_mm):
            lo = mid
        else:
            hi = mid
    return Wire(curve.trim(0, (lo + hi) / 2).edges()).mirror(Plane.YZ).moved(Location((p.cargo_width_mm, 0, 0)))


def build_cabinet(p: Parameters) -> Compound:
    x = cabinet_aisle_x(p)
    width, length = p.cargo_width_mm - x, p.cabinet_length_mm
    thickness, member = p.cabinet_frame_thickness_mm, p.member_width_mm
    radius = p.inside_radius_mm
    # Cabinet geometry is furniture-local; scribe against vehicle geometry
    # translated into the same coordinates before placing the finished assembly.
    gap = p.furniture_rear_gap_mm
    arch_rear = p.arch_rear_offset_mm - gap
    if length > min(p.seat_length_mm, p.body_length_mm - gap) or length <= 2 * thickness or width <= 2 * thickness:
        raise ValueError("Cabinet must fit beside the bed and leave room between its end panels.")
    # Rear top rails and door openings use this datum; the aisle frame itself
    # extends upward to meet the plywood ceiling.
    height = ceiling_height(p, p.cargo_width_mm, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
    lower_rail = p.cabinet_lower_rail_top_mm
    if lower_rail - member < p.arch_height_mm + 3:
        raise ValueError("Cabinet wall rail must clear the wheel arch by 3mm.")
    step = p.cabinet_frame_step_height_mm
    upper_rail = (step + height) / 2
    storage_rail = p.cabinet_rear_storage_height_mm + member
    shelf_levels = (lower_rail, storage_rail, upper_rail)
    rear_shelf_levels = (storage_rail, upper_rail)

    def openings_between(rails: tuple[float, ...]) -> list[tuple[float, float]]:
        # Shelf supports and their frames share the same rail elevations in both bays.
        openings = []
        bottom = member
        if any(rail <= member or rail >= height - member for rail in rails):
            raise ValueError("Cabinet shelf rails must fit between the bottom and top frame members.")
        for rail in sorted((*rails, height)):
            top = rail - member
            if top > bottom:
                if top - bottom <= 2 * radius:
                    raise ValueError("Cabinet shelf rails must leave room for rounded openings.")
                openings.append((bottom, top))
            bottom = max(bottom, rail)
        return openings

    opening_heights = openings_between(shelf_levels)
    rear_openings = openings_between(shelf_levels)
    body, ceiling = interior_limits(p, p.cabinet_ceiling_gap_mm)
    room = (body & ceiling).mirror(Plane.YZ).moved(Location((p.cargo_width_mm, -gap, 0)))
    shelf_thickness, ledge = p.cabinet_shelf_thickness_mm, p.cabinet_ledge_size_mm
    ledge_height = p.cabinet_ledge_height_mm
    if shelf_thickness + ledge_height > member:
        raise ValueError("Shelf thickness and ledge must fit within the frame cross-beam height.")
    arch_left = (p.cargo_width_mm + p.arch_gap_mm) / 2
    clearance = 3.0
    arch_cutout = panel(
        p.cargo_width_mm - arch_left + 2 * clearance,
        p.arch_length_mm + 2 * clearance,
        p.arch_height_mm + clearance,
    ).moved(Location((arch_left - clearance, arch_rear - clearance, 0)))

    outer = cabinet_back_profile(p, p.cabinet_back_clearance_mm)
    inner = cabinet_back_profile(p, p.cabinet_back_clearance_mm + p.cabinet_back_thickness_mm)
    back_start = max(0.0, p.rear_corner_radius_mm + p.cabinet_back_clearance_mm - gap)
    if back_start >= length:
        raise ValueError("Cabinet backing must have space ahead of the rear corner pillar.")
    back_section = Face(
        Wire(
            [
                *outer.edges(),
                Edge.make_line(outer.position_at(1), inner.position_at(1)),
                *(edge.reversed() for edge in reversed(inner.order_edges())),
                Edge.make_line(inner.position_at(0), outer.position_at(0)),
            ]
        )
    )
    backing = Part(
        (
            Solid.extrude(back_section, (0, length - back_start, 0)).moved(Location((0, back_start, 0))) - arch_cutout
        ).solids(),
        label="Back lining",
        color=Color(0.9, 0.9, 0.88),
    )
    # Reserve everything behind the sheet, not just its 3mm material.
    back_bottom, back_top = inner.position_at(0), inner.position_at(1)
    fitting_section = Face(
        Wire(
            [
                *inner.edges(),
                Edge.make_line(back_top, (back_top.X, 0, p.body_height_mm)),
                Edge.make_line((back_top.X, 0, p.body_height_mm), (0, 0, p.body_height_mm)),
                Edge.make_line((0, 0, p.body_height_mm), (0, 0, back_bottom.Z)),
                Edge.make_line((0, 0, back_bottom.Z), back_bottom),
            ]
        )
    )
    room = room & Solid.extrude(fitting_section, (0, length, 0))
    parts: list[Part] = []

    def place(part: Part, name: str, placement: Location) -> None:
        part.label = name
        part.color = Color(0.88, 0.61, 0.25)
        part.location = placement
        parts.append(part)

    middle_y = p.cabinet_rear_bay_length_mm
    middle_centre = middle_y + thickness / 2
    bay_spans = ((member, middle_centre - member / 2), (middle_centre + member / 2, length - member))
    if any(end - start <= 2 * radius for start, end in bay_spans):
        raise ValueError("Rear storage length must leave room for both cabinet bays and their frame openings.")
    aisle = frame_panel(
        length,
        thickness,
        p.body_height_mm,
        [
            (start, end, bottom, top)
            for (start, end), openings in zip(bay_spans, (rear_openings, opening_heights), strict=True)
            for bottom, top in openings
        ],
        radius,
    )
    aisle_pose = Location((x + thickness, 0, 0), (0, 0, 90))
    to_furniture = Location((p.cargo_width_mm, -gap, 0))
    ceiling_contact = ceiling_space(p, p.ceiling_ply_thickness_mm).mirror(Plane.YZ).moved(to_furniture)
    aisle_fitted = aisle.moved(aisle_pose) & body.mirror(Plane.YZ).moved(to_furniture) & ceiling_contact
    aisle = Part(aisle_fitted.moved(aisle_pose.inverse()).solids())
    place(aisle, "Aisle frame", aisle_pose)

    # The lining is only containment. Separate straight rails carry the shelf
    # backs; a narrow transverse upright transfers their rear ends to the floor.
    def wall_x(z: float) -> float:
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if inner.position_at(mid).Z < z:
                lo = mid
            else:
                hi = mid
        return float(inner.position_at((lo + hi) / 2).X)

    upright_pose = Location((0, back_start, 0))
    upright_blank = panel(p.cargo_width_mm, thickness, height).moved(upright_pose)
    # A 60mm-wide strip in a transverse plywood sheet, not a broad sheet bent
    # around the van. Its wall-facing edge is a real-van templating allowance.
    upright_inside = Solid.extrude(fitting_section, (0, length, 0)).moved(Location((-member, 0, 0)))
    rear_upright = Part(
        ((upright_blank & room) - upright_inside).moved(upright_pose.inverse()).solids(),
        label="Rear upright",
        color=Color(0.88, 0.61, 0.25),
    )
    rear_upright.location = upright_pose
    wall_rails = []
    rail_blocks = []
    rail_faces: dict[tuple[str, float], float] = {}
    rail_names = {lower_rail: "lower", storage_rail: "middle", upper_rail: "upper", height: "top"}
    for bay_name, start, end, rail_levels in (
        ("Rear", back_start + thickness, middle_y, (*rear_shelf_levels, height)),
        ("Cab-end", middle_y + thickness, length - thickness, (*shelf_levels, height)),
    ):
        if end <= start:
            raise ValueError("Cabinet bays must leave room for the rear upright and shelf rails.")
        for rail_z in rail_levels:
            bottom = rail_z - member
            # Keep each rail vertical and rectangular, inboard of the most
            # projecting point over its height. No bevel or wall fixing needed.
            outer_x = min(wall_x(bottom), wall_x(rail_z))
            rail_faces[bay_name, rail_z] = outer_x - thickness
            rail = panel(thickness, end - start, member)
            rail.location = Location((outer_x - thickness, start, bottom))
            rail.label, rail.color = f"{bay_name} {rail_names[rail_z]} rail", Color(0.88, 0.61, 0.25)
            wall_rails.append(rail)
            # A vertical pine block bonds the broad rail face to the transverse
            # upright/partition face. Use the selected square batten stock.
            for end_name, block_y in (("rear", start), ("fore", end - ledge_height)):
                block = panel(ledge, ledge_height, member)
                block.location = Location((outer_x - thickness - ledge, block_y, bottom))
                block.label, block.color = f"{rail.label} {end_name} block", Color(0.88, 0.61, 0.25)
                rail_blocks.append(block)

    block_cutout = Compound(children=[block.moved(Location()) for block in rail_blocks])

    for name, panel_y in (("Middle", middle_y), ("Cab-end", length - thickness)):
        panel_height = height if name == "Middle" else p.body_height_mm
        placement = Location((x + thickness, panel_y, 0))
        blank = panel(width - thickness, thickness, panel_height).moved(placement)
        fitted = (blank & room) - arch_cutout
        partition = Part(fitted.moved(placement.inverse()).solids(), color=Color(0.75, 0.66, 0.49))
        place(partition, f"{name} panel", placement)

    # Close only the upper rear compartments. The lower edge follows the
    # storage-height parameter so the full chair-loading opening stays clear.
    rear_pose = Location((x + thickness, 0, p.cabinet_rear_storage_height_mm))
    rear_blank = panel(width - thickness, thickness, p.body_height_mm - p.cabinet_rear_storage_height_mm)
    rear_fitted = (rear_blank.moved(rear_pose) & room) - rear_upright
    rear_panel = Part(rear_fitted.moved(rear_pose.inverse()).solids(), color=Color(0.75, 0.66, 0.49))
    place(rear_panel, "Rear upper panel", rear_pose)

    shelves, ledges = [], []
    for bay_name, start, end, end_names, levels in (
        (
            "Rear",
            thickness,
            middle_y,
            ("Rear", "Middle"),
            tuple(zip(("Middle", "Upper"), rear_shelf_levels, strict=True)),
        ),
        (
            "Cab-end",
            middle_y + thickness,
            length - thickness,
            ("Middle", "Cab-end"),
            tuple(zip(("Lower", "Middle", "Upper"), shelf_levels, strict=True)),
        ),
    ):
        if end - start <= 2 * ledge:
            raise ValueError("Cabinet bays must leave room between the shelf ledges.")
        for level_name, rail_z in levels:
            ledge_z = rail_z - member
            shelf_z = ledge_z + ledge_height
            label = f"{bay_name} {level_name.lower()}"
            shelf_width = rail_faces[bay_name, rail_z] - x - thickness
            blank = panel(shelf_width, end - start, shelf_thickness).moved(Location((x + thickness, start, shelf_z)))
            shelves.append(
                Part(
                    ((blank & room) - arch_cutout - rear_upright - block_cutout).solids(),
                    label=label,
                    color=Color(0.75, 0.66, 0.49),
                )
            )
            ledge_ends = (start, end - ledge)
            for frame_name, ledge_y in zip(end_names, ledge_ends, strict=True):
                support = panel(shelf_width - ledge, ledge, ledge_height).moved(
                    Location((x + thickness, ledge_y, ledge_z))
                )
                if frame_name == "Rear":
                    # The rear pillar narrows the panel here. Scribe only this
                    # ledge's outer end to the same vehicle fitting envelope.
                    support = Part((support & room).solids())
                support.label, support.color = f"{label} {frame_name.lower()} ledge", Color(0.88, 0.61, 0.25)
                ledges.append(support)
            aisle_start = start + ledge
            support = panel(ledge, end - ledge - aisle_start, ledge_height).moved(
                Location((x + thickness, aisle_start, ledge_z))
            )
            support.label, support.color = f"{label} aisle ledge", Color(0.88, 0.61, 0.25)
            ledges.append(support)
            wall_start = max(start + ledge_height, aisle_start, back_start + thickness + ledge_height)
            wall_end = end - max(ledge, ledge_height)
            support = panel(ledge, wall_end - wall_start, ledge_height)
            support.location = Location((rail_faces[bay_name, rail_z] - ledge, wall_start, ledge_z))
            support.label, support.color = f"{label} wall ledge", Color(0.88, 0.61, 0.25)
            ledges.append(support)
    # The two aisle cleats remain; the full-height rail joint blocks replace
    # the former short wall cleats above the lowest forward shelf.
    corner_cleats = []
    cleat_z = lower_rail - member + ledge_height + shelf_thickness
    for name, cleat_y in (("Middle", middle_y + thickness), ("Cab-end", length - thickness - ledge_height)):
        aisle = panel(ledge, ledge_height, member)
        aisle.location = Location((x + thickness, cleat_y, cleat_z))
        aisle.label, aisle.color = f"{name} aisle corner cleat", Color(0.88, 0.61, 0.25)
        corner_cleats.append(aisle)
    doors = build_cabinet_doors(p, bay_spans, opening_heights, rear_openings)
    strikes, strike_blocks = cabinet_door_strikes(p, doors)
    return Compound(
        label="Cabinet",
        children=[
            *parts,
            Compound(label="Wall supports", children=[rear_upright, *wall_rails]),
            Compound(label="Rail joint blocks", children=rail_blocks),
            backing,
            doors,
            strikes,
            strike_blocks,
            Compound(label="Corner cleats", children=corner_cleats),
            Compound(label="Shelf ledges", children=ledges),
            Compound(label="Shelves", children=shelves),
        ],
    )
