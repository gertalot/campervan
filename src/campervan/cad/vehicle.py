"""Japanese NV200 interior envelope and provisional wheel-house references.

X runs across the van, Y from rear doors to cab, Z upwards. The floor's
rear-left corner is the origin. References are not manufactured parts.
"""

from build123d import Color, Compound, Location, Polyline, Wire

from campervan.cad.body import build_body, wheel_arch
from campervan.cad.cab import build_cab
from campervan.parameters import Parameters


def floor_outline(width: float, length: float) -> Wire:
    outline = Polyline((0, 0), (width, 0), (width, length), (0, length), close=True).wire()
    outline.label = "Floor outline"
    outline.color = Color(0.65, 0.75, 0.85)
    return outline


def build_vehicle_references(parameters: Parameters) -> Compound:
    p = parameters
    return Compound(
        label="Vehicle references",
        children=[
            floor_outline(p.cargo_width_mm, p.cargo_length_mm).moved(Location((0, p.furniture_rear_gap_mm, 0))),
            Compound(label="Wheel arches", children=[wheel_arch(p, False), wheel_arch(p, True)]),
            *build_body(p),
            build_cab(p),
        ],
    )
