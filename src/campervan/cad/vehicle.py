"""Provisional NV200 reference geometry ported from nv200-interior.fs.

X runs across the van, Y from rear doors to cab, Z upwards. The floor's
rear-left corner is the origin. References are not manufactured parts.
"""

from math import sqrt

from build123d import Align, Axis, Box, Color, Compound, Face, Location, Part, Polyline, ThreePointArc, Wire, fillet

from campervan.parameters import Parameters


def floor_outline(width: float, length: float) -> Wire:
    outline = Polyline((0, 0), (width, 0), (width, length), (0, length), close=True).wire()
    outline.label = "Floor outline"
    outline.color = Color(0.65, 0.75, 0.85)
    return outline


def wheel_arch(depth: float, length: float, height: float, radius: float) -> Part:
    """Keep the full base footprint; round only the two upper ends."""
    block = Box(depth, length, height, align=(Align.MIN, Align.MIN, Align.MIN))
    arch = fillet(block.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], radius)
    arch.color = Color(0.45, 0.49, 0.52)
    return arch


def rear_corner(radius: float, height: float) -> Face:
    """Quarter-cylinder reference surface, with no invented wall thickness."""
    k = 1 - 1 / sqrt(2)
    arc = ThreePointArc((radius, 0, 0), (k * radius, k * radius, 0), (0, radius, 0))
    corner = Face.extrude(arc.edge(), (0, 0, height))
    corner.color = Color(0.55, 0.58, 0.61)
    return corner


def build_vehicle_references(parameters: Parameters) -> Compound:
    p = parameters
    intrusion = (p.cargo_width_mm - p.arch_gap_mm) / 2
    arches = []
    corners = []
    for name, right in (("Left", False), ("Right", True)):
        arch = wheel_arch(intrusion, p.arch_length_mm, p.arch_height_mm, p.arch_radius_mm)
        arch.label = f"{name} wheel arch"
        arch.location = Location((p.cargo_width_mm - intrusion if right else 0, p.arch_rear_offset_mm, 0))
        arches.append(arch)
        corner = rear_corner(p.rear_corner_radius_mm, p.rear_corner_height_mm)
        corner.label = f"{name} rear corner"
        # Rotate the right reference about Y to mirror X while keeping the same local geometry.
        corner.location = Location((p.cargo_width_mm, 0, p.rear_corner_height_mm), (0, 180, 0)) if right else Location()
        corners.append(corner)
    return Compound(
        label="Vehicle references",
        children=[
            floor_outline(p.cargo_width_mm, p.cargo_length_mm),
            Compound(label="Wheel arches", children=arches),
            Compound(label="Rear corners", children=corners),
        ],
    )
