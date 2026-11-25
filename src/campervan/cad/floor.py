"""Lengthwise plywood flooring on a flat pine frame with routed perimeter blocks."""

from math import ceil

from build123d import Align, Color, Compound, Cylinder, Face, Location, Part, Plane, Solid, Wire

from campervan.cad.mirror import mirror_assembly
from campervan.cad.panels import countersunk_clearance, panel
from campervan.parameters import Parameters

FLOOR_BASE_WIDTH_MM = 1200.0
FLOOR_REAR_Y_MM = -15.0
ROUTED_BLOCKS = "Routed perimeter blocks"
PINE = Color(0.84, 0.64, 0.39)
PLY = Color(0.76, 0.70, 0.55, 0.32)
EPS = Color(0.94, 0.94, 0.90)
# Centre of the factory pump cover in the registered scan. Floor construction Y starts at the rear sheet edge.
HATCH_X, HATCH_Y = 1075.0, 1720.0 - FLOOR_REAR_Y_MM
HATCH_CLEAR = 300.0
HATCH_GAP = 1.0  # Each edge of the removable plywood and EPS.
HATCH_FOAM = "Lift-out EPS"


def routed_block(label: str, profile: list[tuple[float, float]], p: Parameters) -> Compound:
    """A flush-trimmed glue-up in blank coordinates: X along the grain, Y across the strips."""
    length = max(x for x, _ in profile)
    width, depth = p.floor_rib_width_mm, p.floor_rib_thickness_mm
    finished = Solid.extrude(Face(Wire.make_polygon([(x, y, 0) for x, y in profile])), (0, 0, depth))
    strips = []
    for i in range(ceil(max(y for _, y in profile) / width)):
        stock = panel(length, width, depth).moved(Location((0, i * width, 0)))
        strips.append(Part((finished & stock).solids(), label=f"Strip {i + 1}", color=PINE))
    return Compound(label=label, children=strips)


def rib_frame(outline: list[tuple[float, float]], centre: float, seam_x: float, length: float,
              rear_pocket: list[tuple[float, float]], door_side: list[tuple[float, float]],
              p: Parameters) -> Compound:
    width, depth = p.floor_rib_width_mm, p.floor_rib_thickness_mm
    bottom = -p.floor_ply_thickness_mm - depth
    half_core = FLOOR_BASE_WIDTH_MM / 2
    rear_shoulder = door_side[:4]
    wing, wing_start = rear_shoulder[-1]
    (_, taper_start), (cab_side, taper_end) = door_side[4:6]
    door_start = rear_shoulder[0][1]
    members = []

    def rib(name: str, x: float, y: float, span: float, *, along_y: bool = False) -> None:
        member = panel(span, width, depth)
        member.label, member.color = name, PINE
        member.location = Location((x, y, bottom), (0, 0, 90 if along_y else 0))
        members.append(member)

    # The end rails span the full floor width. Each side rail butts against an end rail and a door shoulder.
    for index, (x0, y0) in enumerate(outline):
        x1, y1 = outline[(index + 1) % len(outline)]
        start, end = sorted((y0, y1))
        if door_start <= start and end <= taper_end:
            continue
        label = f"Perimeter rib {index + 1:02}"
        if y0 == y1:
            rib(label, centre + min(x0, x1), min(y0, length - width), abs(x1 - x0))
        else:
            start, end = max(start, width), min(end, length - width)
            right_edge = centre + x0 + (width if x0 < 0 else 0)
            rib(label, right_edge, start, end - start, along_y=True)

    pocket_end = rear_pocket[-1][1]
    pocket = routed_block("Right rear pocket", [(pocket_end - y, extra) for extra, y in rear_pocket], p)
    pocket.location = Location((half_core, pocket_end, 0), (0, 0, -90))
    inner = half_core - width
    # Carry the long wing rail into the taper. A stock-width crosspiece then closes the return.
    # For narrower stock, retain at least half the rail width at the butt joint.
    taper_run = taper_end - taper_start
    slope = (wing - cab_side) / taper_run
    extension = min(max(0, taper_run - width), width / (2 * slope))
    joint_y = taper_start + extension
    trim = extension * slope
    wing_length = joint_y - wing_start
    rail_profile = [(0, 0), (wing_length, 0), (wing_length, width)]
    if extension:
        rail_profile.append((extension, width))
    rail_profile.append((0, width - trim))
    wing_rail = routed_block("Right door-wing rail", rail_profile, p)
    wing_rail.location = Location((wing - width, joint_y, 0), (0, 0, -90))

    right_blocks = [pocket, wing_rail]
    cab_shoulder = [(wing - trim, joint_y), (cab_side, taper_end)]
    for name, shoulder in (("Right door shoulder", rear_shoulder), ("Right cab-side door shoulder", cab_shoulder)):
        start, end = shoulder[0][1], shoulder[-1][1]
        profile = [(x - inner, y - start) for x, y in shoulder]
        step = routed_block(name, [(0, 0), *profile, (0, end - start)], p)
        if shoulder is rear_shoulder:
            # The first strip at each shoulder is the profiled end of the same cross rib.
            tip, *remaining = step.children
            right_tip = tip.solid().moved(Location((inner, 0, 0)))
            centre_span = panel(2 * inner, width, depth).moved(Location((-inner, 0, 0)))
            cross_rib = centre_span.fuse(right_tip, right_tip.mirror(Plane.YZ)).solid()
            cross_rib.label, cross_rib.color = "Cross rib 2", PINE
            members.append(cross_rib.moved(Location((centre, start, bottom))))
            if not remaining:
                continue
            step = Compound(label=name, children=remaining)
        step.location = Location((inner, start, 0))
        right_blocks.append(step)
    blocks = []
    for right in right_blocks:
        left = mirror_assembly(right)
        left.label = right.label.replace("Right", "Left")
        blocks.extend((left, right))
    members.append(Compound(label=ROUTED_BLOCKS, children=blocks).moved(Location((centre, 0, bottom))))
    half = HATCH_CLEAR / 2
    rear, front = HATCH_Y - half, HATCH_Y + half
    left, right = HATCH_X - half, HATCH_X + half
    if not (seam_x + width / 2 < left - width
            and right + width <= centre + half_core - width and front + width < length - width):
        raise ValueError("The pump hatch frame must clear the seam rib and perimeter ribs.")
    # Keep the rear rib in place. The door shoulder and the hatch locate the next two ribs.
    hatch_rib_y = rear - width
    bay_length = (hatch_rib_y - 3 * width) / 3
    if bay_length <= 0:
        raise ValueError("The floor must have room for three bays behind the pump hatch.")
    pitch = width + bay_length
    rib("Cross rib 1", centre - inner, pitch, 2 * inner)
    rib("Cross rib 3", centre - wing + width, hatch_rib_y, 2 * (wing - width))
    start = width
    for index, end in enumerate((pitch, door_start, hatch_rib_y, length - width), 1):
        for name, x in (("Seam rib", seam_x + width / 2), ("Hatch-side rib", left)):
            rib(f"{name} {index}", x, start, end - start, along_y=True)
        start = end + width
    rib("Pump hatch wall rail", right + width, rear, HATCH_CLEAR, along_y=True)
    rib("Pump hatch cab rail", left, front, HATCH_CLEAR + width)
    return Compound(label="Pine rib frame", children=members)


def build_floor_plywood(p: Parameters) -> Compound:
    """Two full-length sheets share the centreline of the rib under both benches."""
    centre = p.cargo_width_mm / 2
    length = 2030.0
    half_width, wing = FLOOR_BASE_WIDTH_MM / 2, 725.0
    # Half-width and distance from the plywood rear edge. The door wings retain the physical floor outline.
    door_side = [
        (half_width, 1050), (650, 1080), (650, 1130), (wing, 1180),
        (wing, 1850), (half_width, 1900), (half_width, length),
    ]
    # Extra width beyond the original straight edge, fitted to both rear pillars and arches
    # across the plywood thickness (registered Z8–20).
    rear_pocket = [(0, 0), (10, 15), (16, 58), (105, 150), (105, 279), (25, 295), (15, 305), (0, 330)]
    ply_side = [(half_width + extra, y) for extra, y in rear_pocket] + door_side
    # Gert's cabinet is on the right. The left rib runs beneath both benches.
    seam_x = centre - (FLOOR_BASE_WIDTH_MM - p.floor_rib_width_mm) / 6
    cut = HATCH_CLEAR + p.floor_rib_width_mm
    ply = p.floor_ply_thickness_mm
    cut_origin = (HATCH_X - cut / 2, HATCH_Y - cut / 2, -ply)
    cutout = panel(cut, cut, ply).moved(Location(cut_origin))
    panels = []
    for name, sign in (("Bench-side panel", -1), ("Aisle panel", 1)):
        wire = Wire.make_polygon([(seam_x, 0, 0), *((centre + sign * x, y, 0) for x, y in ply_side),
                                  (seam_x, length, 0)])
        part = Solid.extrude(Face(wire), (0, 0, -ply))
        if sign == 1:
            part = (part - cutout).solid()
        part.label, part.color = name, PLY
        panels.append(part)
    outer = [(-half_width, 0), (half_width, 0), *door_side, *((-x, y) for x, y in reversed(door_side))]
    frame = rib_frame(outer, centre, seam_x, length, rear_pocket, door_side, p)
    if p.floor_insulation_thickness_mm > p.floor_rib_thickness_mm:
        raise ValueError("Floor insulation must fit within the pine rib depth.")
    full_outline = [*ply_side, *((-x, y) for x, y in reversed(ply_side))]
    envelope = Solid.extrude(
        Face(Wire.make_polygon([(centre + x, y, -p.floor_ply_thickness_mm) for x, y in full_outline])),
        (0, 0, -p.floor_insulation_thickness_mm),
    )
    # Reserve the entire service aperture before deriving the fixed EPS pieces.
    depth = p.floor_insulation_thickness_mm
    hole = panel(HATCH_CLEAR, HATCH_CLEAR, depth).moved(
        Location((HATCH_X - HATCH_CLEAR / 2, HATCH_Y - HATCH_CLEAR / 2, -ply - depth)))
    cavities = sorted((envelope - frame - hole).solids(),
                      key=lambda solid: (round(solid.bounding_box().center().Y), solid.bounding_box().min.X))
    if len(cavities) != 12:
        raise ValueError("The floor frame must leave twelve fixed insulation bays around the pump hatch.")
    infill = []
    for index, solid in enumerate(cavities):
        row = ("Rear", "Rear middle", "Front middle", "Front")[index // 3]
        column = ("left", "centre", "right")[index % 3]
        infill.append(Part([solid], label=f"{row} {column} infill", color=EPS))
    insulation = Compound(label="Floor insulation", children=infill)
    lid_side = cut - 2 * HATCH_GAP
    foam_side = HATCH_CLEAR - 2 * HATCH_GAP
    lid = panel(lid_side, lid_side, ply).moved(Location((-lid_side / 2, -lid_side / 2, -ply)))
    foam = panel(foam_side, foam_side, depth).moved(Location((-foam_side / 2, -foam_side / 2, -ply - depth)))
    screw_offset = HATCH_CLEAR / 2 + p.floor_rib_width_mm / 4
    for x in (-screw_offset, screw_offset):
        lid -= countersunk_clearance(ply).moved(Location((x, 0, 0)))
    # Leave space behind the finger hole so fingers can hook the underside of the plywood.
    grip_x = -foam_side / 2 + 24
    grip = Cylinder(12.5, ply, align=(Align.CENTER, Align.CENTER, Align.MAX))
    lid -= grip.moved(Location((grip_x, 0, 0)))
    foam -= panel(48, 50, depth).moved(Location((-foam_side / 2, -25, -ply - depth)))
    lid.label, lid.color = "Lift-out plywood lid", PLY
    foam.label, foam.color = HATCH_FOAM, EPS
    hatch = Compound(label="Fuel pump hatch", children=[lid, foam]).moved(Location((HATCH_X, HATCH_Y, 0)))
    return Compound(label="Finished floor plywood", children=[*panels, frame, insulation, hatch]).moved(
        Location((0, FLOOR_REAR_Y_MM, p.floor_surface_z_mm)))

