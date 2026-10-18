"""Measured interior envelope with approximate pressed-panel transitions.

Z=0 is the fitted floor; Y=0 is the rear opening at its side pillars.
The opening centre bows aft of that datum. Photo-derived radii remain estimates.
"""

from collections.abc import Sequence
from math import sqrt

from build123d import (
    Align,
    Axis,
    Bezier,
    Box,
    Color,
    Compound,
    Edge,
    Face,
    Location,
    Part,
    Plane,
    Shell,
    Solid,
    ThreePointArc,
    Vector,
    Wire,
    fillet,
)

from campervan.parameters import Parameters

WALL = Color(0.55, 0.62, 0.66, 0.32)


def wheel_arch(p: Parameters, right: bool) -> Part:
    """Shared positioned wheel-house envelope for display and adjoining pillar trim."""
    depth = (p.cargo_width_mm - p.arch_gap_mm) / 2
    block = Box(depth, p.arch_length_mm, p.arch_height_mm, align=(Align.MIN, Align.MIN, Align.MIN))
    arch = fillet(block.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], p.arch_radius_mm)
    crown_edges = [
        edge for edge in arch.edges() if edge.bounding_box().size.X < 1e-6 and edge.bounding_box().min.Z > 1e-6
    ]
    arch = fillet(crown_edges, p.arch_crown_radius_mm)
    arch.color = Color(0.45, 0.49, 0.52, 0.32)
    arch.label = "Right wheel arch" if right else "Left wheel arch"
    arch.location = Location((p.cargo_width_mm - depth if right else 0, p.arch_rear_offset_mm, 0))
    return arch


def body_section(p: Parameters, y: float, inset: float = 0) -> list[Edge]:
    """Seven matching edges, shared by visible walls and cabinet fitting solids."""
    half = p.cargo_width_mm / 2
    shoulder = (p.cargo_width_mm - p.body_upper_width_mm) / 2
    h, crown, start = p.body_height_mm, p.roof_crown_mm, p.wall_taper_start_mm
    # Broad, angled rear pillars, with much less extra intrusion at the roof.
    bottom = inset
    eave = shoulder + inset * 0.20
    span = half - eave
    run = min(shoulder, span / 3)
    weight = inset / max(1, (p.cargo_width_mm - p.rear_opening_floor_width_mm) / 2)

    def point(x: float, z: float) -> tuple[float, float, float]:
        return (x, y + weight * p.rear_opening_rake_mm * z / h, z)

    start = start * (1 - weight) + 390 * weight
    waist = bottom - weight * (p.rear_opening_width_mm - p.rear_opening_floor_width_mm) / 2
    wall = [
        point(waist, start),
        point(waist, start + (h - crown - start) * 0.55),
        point(eave - run * 0.35, h - crown * 1.35),
        point(eave, h - crown),
    ]
    roof = [wall[-1], point(eave + run, h), point(half - span * 0.3, h), point(half, h)]

    def opposite(points: Sequence[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
        return [(p.cargo_width_mm - x, yy, z) for x, yy, z in reversed(points)]

    return [
        Bezier(point(bottom, 0), point(bottom, start * 0.4), point(waist, start * 0.7), wall[0]).edge(),
        Bezier(*wall).edge(),
        Bezier(*roof).edge(),
        Bezier(*opposite(roof)).edge(),
        Bezier(*opposite(wall)).edge(),
        Bezier(*opposite([point(bottom, 0), point(bottom, start * 0.4), point(waist, start * 0.7), wall[0]])).edge(),
        Edge.make_line(point(p.cargo_width_mm - bottom, 0), point(bottom, 0)),
    ]


def rear_stations(p: Parameters) -> list[tuple[float, float]]:
    inset = (p.cargo_width_mm - p.rear_opening_floor_width_mm) / 2
    return [(0, inset), (p.rear_corner_straight_mm, inset), (p.rear_corner_radius_mm, 0)]


def rear_aperture(p: Parameters, margin: float = 0, closed: bool = False) -> Wire:
    """Non-planar hatch outline: measured widths, bowed sill and upper forward rake."""
    half = p.cargo_width_mm / 2
    low = (p.cargo_width_mm - p.rear_opening_floor_width_mm) / 2 - margin
    waist = (p.cargo_width_mm - p.rear_opening_width_mm) / 2 - margin
    upper = (p.cargo_width_mm - p.rear_opening_upper_width_mm) / 2 - margin
    h, r, sill = p.rear_opening_height_mm, p.rear_opening_radius_mm, p.rear_opening_sill_mm

    def pt(x: float, z: float) -> tuple[float, float, float]:
        fraction = max(0.0, min(1.0, (z - sill) / h))
        cross = max(0.0, 1 - ((x - half) / (p.rear_opening_width_mm / 2)) ** 2)
        # Keep the measured centre bow through bed height, then ease it out at the header.
        upper_blend = max(0.0, (fraction - 390 / h) / (1 - 390 / h))
        y = p.rear_opening_rake_mm * upper_blend**2 - p.rear_opening_bow_mm * cross * (1 - upper_blend**2)
        if closed:
            y += (p.rear_opening_bow_mm + p.rear_hatch_centre_y_mm) * cross * (1 - upper_blend**2)
        return (x, y, z)

    # Control points use physical stations: floor, slat height, 60mm below the crown.
    paths = [
        [(low, sill - margin), (low, 150), (waist, 250), (waist, 390)],
        [(waist, 390), (waist, 750), (upper, h - r - 100 + sill), (upper, h - r + sill)],
        [(upper, h - r + sill), (upper, h + sill + margin), (upper + r, h + sill + margin)],
        [(upper + r, h + sill + margin), (half, h + sill + margin)],
    ]
    left = [Bezier(*(pt(x, z) for x, z in points)).edge() for points in paths]
    right = [Bezier(*(pt(p.cargo_width_mm - x, z) for x, z in reversed(points))).edge() for points in reversed(paths)]
    floor = ThreePointArc(
        pt(p.cargo_width_mm - low, sill - margin), pt(half, sill - margin), pt(low, sill - margin)
    ).edge()
    return Wire([*left, *right, floor])


def ceiling_height(p: Parameters, x: float, offset: float = 0) -> float:
    """Bow underside; normal inward offset gives plywood and cabinet clearance."""
    centre = p.body_height_mm - p.roof_bow_depth_mm
    rise = p.roof_bow_crown_mm
    if rise == 0:
        return centre - offset
    radius = ((p.body_upper_width_mm / 2) ** 2 + rise**2) / (2 * rise)
    return centre - radius + sqrt((radius - offset) ** 2 - (x - p.cargo_width_mm / 2) ** 2)


def ceiling_space(p: Parameters, offset: float = 0) -> Part:
    left = (0, 0, ceiling_height(p, 0, offset))
    right = (p.cargo_width_mm, 0, left[2])
    middle = (p.cargo_width_mm / 2, 0, ceiling_height(p, p.cargo_width_mm / 2, offset))
    curve = ThreePointArc(left, middle, right).edge() if p.roof_bow_crown_mm else Edge.make_line(left, right)
    wire = Wire(
        [
            Edge.make_line((0, 0, -1), left),
            curve,
            Edge.make_line(right, (p.cargo_width_mm, 0, -1)),
            Edge.make_line((p.cargo_width_mm, 0, -1), (0, 0, -1)),
        ]
    )
    return Part([Solid.extrude(Face(wire), (0, p.body_length_mm, 0))])


def body_space(p: Parameters) -> Part:
    wires = [Wire(body_section(p, y, inset)) for y, inset in rear_stations(p)]
    rear = Solid.make_loft(wires, ruled=True)
    main = Solid.extrude(Face(wires[-1]), (0, p.body_length_mm - p.rear_corner_radius_mm, 0))
    return Part(rear.fuse(main).solids())


def roof_rails(p: Parameters, body: Part) -> Compound:
    """Exposed roof side members; approximate lower returns from owner photographs."""
    edge = (p.cargo_width_mm - p.body_upper_width_mm) / 2
    parts = []
    for name, x in (("Left roof rail", 0), ("Right roof rail", p.cargo_width_mm - edge)):
        blank = Box(
            edge,
            p.body_length_mm - p.rear_corner_radius_mm,
            p.body_height_mm - p.side_opening_height_mm,
            align=(Align.MIN, Align.MIN, Align.MIN),
        ).moved(Location((x, p.rear_corner_radius_mm, p.side_opening_height_mm)))
        parts.append(Part((body & blank).solids(), label=name, color=WALL))
    return Compound(label="Side rails", children=parts)


def interior_limits(p: Parameters, ceiling_gap: float) -> tuple[Part, Part]:
    body = body_space(p)
    room = body - roof_rails(p, body)
    for offset, right in ((p.left_door_front_offset_mm, False), (p.right_door_front_offset_mm, True)):
        room = room - side_pillar(p, p.body_length_mm - offset, right)
        room = room - side_pillar(p, p.body_length_mm - offset, right, rear=False)
    return Part(room.solids()), ceiling_space(p, p.ceiling_ply_thickness_mm + ceiling_gap)


def build_ceiling(p: Parameters) -> tuple[Compound, Part]:
    body = body_space(p)
    below_bows = ceiling_space(p)
    below_ply = ceiling_space(p, p.ceiling_ply_thickness_mm)
    sheet_width = p.body_upper_width_mm
    sheet_limits = Box(
        sheet_width, p.ceiling_length_mm, p.body_height_mm, align=(Align.MIN, Align.MIN, Align.MIN)
    ).moved(Location(((p.cargo_width_mm - sheet_width) / 2, p.ceiling_rear_y_mm, 0)))
    ply = Part(
        ((below_bows - below_ply) & body & sheet_limits).solids(),
        label="Finished ceiling",
        color=Color(0.76, 0.70, 0.55, 0.45),
    )
    bows = []
    for name, y in (
        ("Rear bow", p.roof_bow_rear_y_mm),
        ("Middle bow", p.roof_bow_middle_y_mm),
        ("Front bow", p.roof_bow_front_y_mm),
    ):
        slab = Box(
            p.cargo_width_mm, p.roof_bow_width_mm, p.body_height_mm, align=(Align.MIN, Align.MIN, Align.MIN)
        ).moved(Location((0, y - p.roof_bow_width_mm / 2, 0)))
        bows.append(Part(((body & slab) - below_bows).solids(), label=name, color=WALL))
    return Compound(label="Roof bows", children=bows), ply


def side_aperture(p: Parameters, front: float) -> Wire:
    """YZ seal outline: lower curve flowing into the photo-derived upper pillar lean."""
    rear, upper = front - p.side_opening_width_mm, front - p.side_opening_upper_width_mm
    bottom, top, r = p.side_opening_sill_mm, p.side_opening_height_mm + p.side_opening_sill_mm, p.side_opening_radius_mm
    start, end = p.side_opening_curve_start_mm, p.side_opening_curve_end_mm
    lean = p.side_opening_upper_lean_mm
    upper_bottom = upper + lean
    slope = lean / (top - r - end)
    handle = (end - start) / 3

    def pt(y: float, z: float) -> tuple[float, float, float]:
        return (-1, y, z)

    def line(a: tuple[float, float], b: tuple[float, float]) -> Edge:
        return Edge.make_line(pt(*a), pt(*b))

    def curve(*points: tuple[float, float]) -> Edge:
        return Bezier(*(pt(*v) for v in points)).edge()

    return Wire(
        [
            line((rear + r, bottom), (front - r, bottom)),
            curve((front - r, bottom), (front, bottom), (front, bottom + r)),
            line((front, bottom + r), (front, top - r)),
            curve((front, top - r), (front, top), (front - r, top)),
            line((front - r, top), (upper + r, top)),
            curve((upper + r, top), (upper - slope * r, top), (upper, top - r)),
            line((upper, top - r), (upper_bottom, end)),
            curve(
                (upper_bottom, end),
                (upper_bottom + slope * handle, end - handle),
                (rear, start + handle),
                (rear, start),
            ),
            line((rear, start), (rear, bottom + r)),
            curve((rear, bottom + r), (rear, bottom), (rear + r, bottom)),
        ]
    )


def side_pillar(p: Parameters, front: float, right: bool, *, rear: bool = True) -> Part:
    """Solid door posts sharing the wall taper and rounded aperture returns."""
    body = body_space(p)
    cut = Solid.extrude(Face(side_aperture(p, front)), (p.cargo_width_mm + 2, 0, 0))
    width = p.side_pillar_intrusion_mm if rear else p.front_pillar_intrusion_mm
    # Intersect a shifted copy of the actual wall profile to follow its transverse taper.
    inward = body.moved(Location((-width if right else width, 0, 0)))
    strip = body - inward
    if rear:
        end = front - p.side_opening_width_mm
        start = end - p.side_pillar_width_mm
    else:
        start = front - p.side_opening_radius_mm
        end = p.body_length_mm
    slab = Box(p.cargo_width_mm, end - start, p.side_opening_height_mm, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((0, start, 0))
    )
    pillar = (strip & slab) - cut
    if rear:
        # The pressed lower return meets the wheel house instead of occupying its volume.
        pillar = pillar - wheel_arch(p, right)
    return Part(pillar.solids(), label="Rear pillar" if rear else "Front pillar", color=WALL)


def sliding_door_offset(p: Parameters, percent: float, right: bool) -> tuple[float, float]:
    """Forward travel, followed by the final inward pull and short forward seating motion."""
    slide = min(percent / 85, 1)
    close = max(0, (percent - 85) / 15)
    final_travel = min(30, p.side_door_clear_width_mm)
    x = (p.side_door_standoff_mm + p.side_door_thickness_mm) * (1 - close) * (1 if right else -1)
    y = -p.side_door_clear_width_mm + (p.side_door_clear_width_mm - final_travel) * slide + final_travel * close
    return x, y


def sliding_door(p: Parameters, front: float, right: bool) -> Compound:
    """Fit the closed aperture, with a movable parent shared by CAD and viewer animation."""
    length = p.side_opening_upper_width_mm + 50
    section = body_section(p, 0)
    # The outer face is exactly the wall surface. Thickness runs into the van;
    # translating the finished door preserves its shape instead of bending it open.
    lower = Edge.make_line(section[0].position_at(0), section[0].position_at(1))
    upper = section[1]
    depth = Vector(p.side_door_thickness_mm, 0, 0)
    profile = Wire(
        [
            lower,
            upper,
            Edge.make_line(upper.position_at(1), upper.position_at(1) + depth),
            upper.moved(Location(depth)).reversed(),
            lower.moved(Location(depth)).reversed(),
            Edge.make_line(lower.position_at(0) + depth, lower.position_at(0)),
        ]
    )
    curved = Solid.extrude(Face(profile), (0, length, 0))
    blank = Solid.extrude(Face(side_aperture(p, length)), (p.cargo_width_mm + 2, 0, 0))
    window_start = length - p.side_opening_width_mm + 60
    window = Box(p.cargo_width_mm + 2, length - window_start - 60, 480, align=(Align.MIN, Align.MIN, Align.MIN))
    window = fillet(window.edges().filter_by(Axis.X), 55).moved(Location((-1, window_start, 610)))
    skin = Part(((curved & blank) - window).solids(), label="Door envelope", color=Color(0.55, 0.62, 0.66, 0.16))
    if right:
        skin = skin.mirror(Plane.YZ).moved(Location((p.cargo_width_mm, 0, 0)))
    skin.move(Location((0, front - length, 0)))
    x, y = sliding_door_offset(p, p.doors_close_percent, right)
    door = Compound(label="Right door" if right else "Left door", children=[skin])
    door.location = Location((x, y, 0))
    return door


def floor_outline_wire(p: Parameters) -> Wire:
    """Straight rear sheet edge and notches around the wheel-house footprints."""
    left = (p.cargo_width_mm - p.rear_opening_floor_width_mm) / 2
    arch_inner = (p.cargo_width_mm - p.arch_gap_mm) / 2
    arch_rear, arch_front = p.arch_rear_offset_mm, p.arch_rear_offset_mm + p.arch_length_mm
    pts = [
        (left, 0, 0),
        (p.cargo_width_mm - left, 0, 0),
        (p.cargo_width_mm - left, p.rear_corner_straight_mm, 0),
        (p.cargo_width_mm, p.rear_corner_radius_mm, 0),
        (p.cargo_width_mm, arch_rear, 0),
        (p.cargo_width_mm - arch_inner, arch_rear, 0),
        (p.cargo_width_mm - arch_inner, arch_front, 0),
        (p.cargo_width_mm, arch_front, 0),
        (p.cargo_width_mm, p.body_length_mm, 0),
        (0, p.body_length_mm, 0),
        (0, arch_front, 0),
        (arch_inner, arch_front, 0),
        (arch_inner, arch_rear, 0),
        (0, arch_rear, 0),
        (0, p.rear_corner_radius_mm, 0),
        (left, p.rear_corner_straight_mm, 0),
    ]
    return Wire.make_polygon(pts)


def build_body(p: Parameters) -> list[Compound]:
    sections = [body_section(p, y, inset) for y, inset in rear_stations(p)]
    # Loft normals oppose extrusion normals for this section order. Keep all
    # interior reference surfaces facing into the van, including the rear roof.
    rear = [-Shell.make_loft([Wire([section[i]]) for section in sections], ruled=True) for i in range(7)]
    main = [Face.extrude(edge, (0, p.body_length_mm - p.rear_corner_radius_mm, 0)) for edge in sections[-1]]
    corners = Compound(
        label="Rear corners",
        children=[
            Compound([rear[0], rear[1]], label="Left rear corner", color=WALL),
            Compound([rear[4], rear[5]], label="Right rear corner", color=WALL),
        ],
    )
    walls, doors = [], []
    for name, indices, offset, right in (
        ("Left wall", (0, 1), p.left_door_front_offset_mm, False),
        ("Right wall", (4, 5), p.right_door_front_offset_mm, True),
    ):
        front = p.body_length_mm - offset
        cutter = Solid.extrude(Face(side_aperture(p, front)), (p.cargo_width_mm + 2, 0, 0))
        wall = Compound([main[i] for i in indices]).cut(cutter)
        walls.append(
            Compound(
                label=name,
                children=[
                    Compound(wall.faces(), label="Side panel", color=WALL),
                    side_pillar(p, front, right),
                    side_pillar(p, front, right, rear=False),
                ],
            )
        )
        doors.append(sliding_door(p, front, right))
    roof = Compound([main[2], main[3], rear[2], rear[3]], label="Bare roof", color=Color(0.67, 0.71, 0.75, 0.2))
    bows, ceiling = build_ceiling(p)
    rails = roof_rails(p, body_space(p))
    header_slab = Box(p.cargo_width_mm, p.ceiling_rear_y_mm, p.body_height_mm, align=(Align.MIN, Align.MIN, Align.MIN))
    header = Part(
        ((body_space(p) & header_slab) - ceiling_space(p, p.ceiling_ply_thickness_mm)).solids(),
        label="Rear header",
        color=WALL,
    )
    aperture = rear_aperture(p)
    surround = Shell.make_loft([aperture, rear_aperture(p, 20)], ruled=True)
    hatch = Face.make_surface(
        rear_aperture(p, closed=True),
        surface_points=[(p.cargo_width_mm / 2, p.rear_hatch_centre_y_mm, 390)],
    )
    floor = Face(floor_outline_wire(p))
    plywood = Solid.extrude(floor, (0, 0, -p.floor_ply_thickness_mm))
    plywood.label, plywood.color = "Finished floor plywood", Color(0.76, 0.70, 0.55, 0.32)
    metal = floor.moved(Location((0, 0, -p.floor_build_up_mm)))
    metal.label, metal.color = "Vehicle floor", WALL
    return [
        corners,
        Compound(label="Side walls", children=walls),
        Compound(label="Roof", children=[roof, bows, ceiling, rails, header]),
        Compound(
            label="Rear opening",
            children=[
                Compound(surround.faces(), label="Hatch surround", color=WALL),
                Wire(aperture.edges(), label="Clear opening", color=Color(0.65, 0.75, 0.85)),
                Compound([hatch], label="Closed hatch inner panel", color=Color(0.55, 0.62, 0.66, 0.16)),
            ],
        ),
        Compound(label="Body floor", children=[metal, plywood]),
        Compound(label="Sliding doors", children=doors),
    ]
