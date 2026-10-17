"""Japanese NV200 interior envelope and provisional wheel-house references.

X runs across the van, Y from rear doors to cab, Z upwards. The floor's
rear-left corner is the origin. References are not manufactured parts.
"""

from build123d import Align, Axis, Box, Color, Compound, Location, Part, Polyline, Wire, fillet

from campervan.cad.body import build_body
from campervan.cad.cab import build_cab
from campervan.parameters import Parameters


def floor_outline(width: float, length: float) -> Wire:
    outline = Polyline((0, 0), (width, 0), (width, length), (0, length), close=True).wire()
    outline.label = "Floor outline"
    outline.color = Color(0.65, 0.75, 0.85)
    return outline


def wheel_arch(depth: float, length: float, height: float, radius: float, crown_radius: float) -> Part:
    """Rounded longitudinal ends and crown edges, retaining the full base footprint."""
    block = Box(depth, length, height, align=(Align.MIN, Align.MIN, Align.MIN))
    arch = fillet(block.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], radius)
    crown_edges = [
        edge for edge in arch.edges() if edge.bounding_box().size.X < 1e-6 and edge.bounding_box().min.Z > 1e-6
    ]
    arch = fillet(crown_edges, crown_radius)
    arch.color = Color(0.45, 0.49, 0.52, 0.32)
    return arch


def build_vehicle_references(parameters: Parameters) -> Compound:
    p = parameters
    intrusion = (p.cargo_width_mm - p.arch_gap_mm) / 2
    arches = []
    for name, right in (("Left", False), ("Right", True)):
        arch = wheel_arch(intrusion, p.arch_length_mm, p.arch_height_mm, p.arch_radius_mm, p.arch_crown_radius_mm)
        arch.label = f"{name} wheel arch"
        arch.location = Location((p.cargo_width_mm - intrusion if right else 0, p.arch_rear_offset_mm, 0))
        arches.append(arch)
    return Compound(
        label="Vehicle references",
        children=[
            floor_outline(p.cargo_width_mm, p.cargo_length_mm).moved(Location((0, p.furniture_rear_gap_mm, 0))),
            Compound(label="Wheel arches", children=arches),
            *build_body(p),
            build_cab(p),
        ],
    )
