"""Adjustable interior reference surfaces, not a sheet-metal reconstruction.

One transverse profile joins the walls and roof. Rear sections narrow together
around the hatch pillars; the main cargo section is constant along the van.
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
    Shell,
    Solid,
    ThreePointArc,
    Wire,
    fillet,
)

from campervan.parameters import Parameters


def body_section(p: Parameters, y: float, inset: float = 0) -> list[Edge]:
    """Ordered perimeter: left wall, roof, right wall, floor (viewed from rear)."""
    half = p.cargo_width_mm / 2
    shoulder = (p.cargo_width_mm - p.body_upper_width_mm) / 2
    eave = shoulder + inset
    span = half - eave
    tangent_run = min(shoulder, span / 3)
    h, crown, start = p.body_height_mm, p.roof_crown_mm, p.wall_taper_start_mm
    wall = [
        (inset, y, start),
        (inset, y, start + (h - crown - start) * 0.55),
        (eave - tangent_run * 0.35, y, h - crown * 1.35),
        (eave, y, h - crown),
    ]
    roof = [(eave, y, h - crown), (eave + tangent_run, y, h), (half - span * 0.3, y, h), (half, y, h)]

    def opposite(points: Sequence[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
        return [(p.cargo_width_mm - x, y, z) for x, y, z in reversed(points)]

    return [
        Edge.make_line((inset, y, 0), wall[0]),
        Bezier(*wall).edge(),
        Bezier(*roof).edge(),
        Bezier(*opposite(roof)).edge(),
        Bezier(*opposite(wall)).edge(),
        Edge.make_line((p.cargo_width_mm - inset, y, start), (p.cargo_width_mm - inset, y, 0)),
        Edge.make_line((p.cargo_width_mm - inset, y, 0), (inset, y, 0)),
    ]


def rear_aperture(p: Parameters) -> Wire:
    """Maximum width low down, gently tapered sides and rounded top shoulders."""
    left = (p.cargo_width_mm - p.rear_opening_width_mm) / 2
    upper = (p.cargo_width_mm - p.rear_opening_upper_width_mm) / 2
    h, r = p.rear_opening_height_mm, p.rear_opening_radius_mm
    side = [(left, 0, 0), (left, 0, h * 0.5), (left, 0, h * 0.7), (upper, 0, h - r)]
    corner = [(upper, 0, h - r), (upper, 0, h), (upper + r, 0, h)]

    def mirror(points: Sequence[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
        return [(p.cargo_width_mm - x, y, z) for x, y, z in reversed(points)]

    return Wire(
        [
            Bezier(*side).edge(),
            Bezier(*corner).edge(),
            Edge.make_line(corner[-1], (p.cargo_width_mm - upper - r, 0, h)),
            Bezier(*mirror(corner)).edge(),
            Bezier(*mirror(side)).edge(),
            Edge.make_line((p.cargo_width_mm - left, 0, 0), (left, 0, 0)),
        ]
    )


def rear_stations(p: Parameters) -> list[tuple[float, float]]:
    """Y and inward offset shared by the visible body and furniture fitting volumes."""
    r = p.rear_corner_radius_mm
    return [(r * t, r * (1 - sqrt(1 - (1 - t) ** 2))) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]


def ceiling_height(p: Parameters, x: float, offset: float = 0) -> float:
    """Bow underside, offset inward normally for plywood thickness or fitting clearance."""
    centre = p.body_height_mm - p.roof_bow_depth_mm
    rise = p.roof_bow_crown_mm
    if rise == 0:
        return centre - offset
    radius = ((p.body_upper_width_mm / 2) ** 2 + rise**2) / (2 * rise)
    return centre - radius + sqrt((radius - offset) ** 2 - (x - p.cargo_width_mm / 2) ** 2)


def ceiling_space(p: Parameters, offset: float = 0) -> Part:
    """Construction volume below the shared, shallow circular ceiling profile."""
    left = (0, 0, ceiling_height(p, 0, offset))
    right = (p.cargo_width_mm, 0, left[2])
    middle = (p.cargo_width_mm / 2, 0, ceiling_height(p, p.cargo_width_mm / 2, offset))
    curve = ThreePointArc(left, middle, right).edge() if p.roof_bow_crown_mm else Edge.make_line(left, right)
    section = Wire(
        [
            Edge.make_line((0, 0, -1), left),
            curve,
            Edge.make_line(right, (p.cargo_width_mm, 0, -1)),
            Edge.make_line((p.cargo_width_mm, 0, -1), (0, 0, -1)),
        ]
    )
    return Part([Solid.extrude(Face(section), (0, p.body_length_mm, 0))])


def interior_limits(p: Parameters, ceiling_gap: float) -> tuple[Part, Part]:
    """Body space and space below the plywood underside, for scribing furniture."""
    wires = [Wire(body_section(p, y, inset)) for y, inset in rear_stations(p)]
    rear = Solid.make_loft(wires)
    main = Solid.extrude(Face(wires[-1]), (0, p.body_length_mm - p.rear_corner_radius_mm, 0))
    return Part(rear.fuse(main).solids()), ceiling_space(p, p.ceiling_ply_thickness_mm + ceiling_gap)


def build_ceiling(p: Parameters) -> tuple[Compound, Part]:
    """Solid bow envelopes and a constant-thickness bent plywood sheet touching their undersides."""
    body, below_ply = interior_limits(p, 0)
    below_bows = ceiling_space(p)
    ply = Part(
        ((below_bows - below_ply) & body).solids(), label="Finished ceiling", color=Color(0.76, 0.70, 0.55, 0.45)
    )
    bows = []
    for name, y in (
        ("Rear bow", p.roof_bow_rear_y_mm),
        ("Middle bow", p.roof_bow_middle_y_mm),
        ("Front bow", p.roof_bow_front_y_mm),
    ):
        slab = Box(p.cargo_width_mm, p.roof_bow_width_mm, p.body_height_mm, align=(Align.MIN, Align.MIN, Align.MIN))
        slab = slab.moved(Location((0, y - p.roof_bow_width_mm / 2, 0)))
        bow = Part(((body & slab) - below_bows).solids(), label=name, color=Color(0.55, 0.62, 0.66, 0.32))
        bows.append(bow)
    return Compound(label="Roof bows", children=bows), ply


def build_body(p: Parameters) -> list[Compound]:
    radius = p.rear_corner_radius_mm
    sections = [body_section(p, y, inset) for y, inset in rear_stations(p)]
    rear = [Shell.make_loft([Wire([section[i]]) for section in sections]) for i in range(7)]
    main = [Face.extrude(edge, (0, p.body_length_mm - radius, 0)) for edge in sections[-1]]
    wall_color = Color(0.55, 0.62, 0.66, 0.32)
    roof_color = Color(0.67, 0.71, 0.75, 0.2)

    corners = Compound(
        label="Rear corners",
        children=[
            Compound([rear[0], rear[1]], label="Left rear corner", color=wall_color),
            Compound([rear[4], rear[5]], label="Right rear corner", color=wall_color),
        ],
    )
    walls = []
    for name, indices, offset in (
        ("Left wall", (0, 1), p.left_door_front_offset_mm),
        ("Right wall", (4, 5), p.right_door_front_offset_mm),
    ):
        cutter = Box(
            p.cargo_width_mm + 2,
            p.side_opening_width_mm,
            p.side_opening_height_mm,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
        cutter = fillet(cutter.edges().filter_by(Axis.X), p.side_opening_radius_mm)
        cutter = cutter.moved(
            Location((-1, p.body_length_mm - offset - p.side_opening_width_mm, p.side_opening_sill_mm))
        )
        wall = Compound([main[i] for i in indices]).cut(cutter)
        walls.append(Compound(wall.faces(), label=name, color=wall_color))

    roof = Compound([main[2], main[3], rear[2], rear[3]], label="Bare roof", color=roof_color)
    bows, ceiling = build_ceiling(p)
    aperture = rear_aperture(p)
    rear_face = Face(Wire(sections[0]))
    opening_face = Face(aperture)
    if opening_face.cut(rear_face).area > 1e-4:
        raise ValueError(
            "Rear aperture extends outside the body profile; adjust its taper, height or the rear corners."
        )
    surround = rear_face.cut(opening_face)
    return [
        corners,
        Compound(label="Side walls", children=walls),
        Compound(label="Roof", children=[roof, bows, ceiling]),
        Compound(
            label="Rear opening",
            children=[
                Compound(surround.faces(), label="Hatch surround", color=wall_color),
                Wire(aperture.edges(), label="Clear opening", color=Color(0.65, 0.75, 0.85)),
            ],
        ),
        Compound([main[6], rear[6]], label="Body floor", color=Color(0.45, 0.49, 0.52, 0.3)),
    ]
