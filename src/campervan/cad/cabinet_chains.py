"""One side restraint per drop-down flap. Coordinates are relative to the piano hinge."""

from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, radians, sin, sqrt

from build123d import Axis, Color, Compound, Edge, Face, Location, Part, Plane, Solid, Wire

from campervan.cad.cabinet_layout import DOOR_FASTENER_INSET_MM
from campervan.cad.cabinet_piano import HINGE_PROJECTION
from campervan.cad.panels import panel

CHAIN = "Jack chain"
METAL = Color(0.65, 0.67, 0.69)
EYE_HEIGHT = 125.0  # Common mounting jig, measured from the hinge axis.
PIN_OFFSET = 8.0  # Distance from the mounting face to the chain pin.
PIN_INSET = 7.0  # Distance from the opening edge to the pin.


@dataclass(frozen=True)
class ChainLayout:
    door_thickness: float
    stile_thickness: float

    @property
    def door_x(self) -> float:
        return HINGE_PROJECTION + self.door_thickness + PIN_OFFSET

    @property
    def frame_x(self) -> float:
        return HINGE_PROJECTION + self.stile_thickness + PIN_OFFSET

    @property
    def length(self) -> float:
        # The door eye moves to (-EYE_HEIGHT, door_x) when the flap is horizontal.
        return hypot(self.frame_x + EYE_HEIGHT, EYE_HEIGHT - self.door_x)

    def angles(self, percent: float) -> tuple[float, float]:
        """Approximate the slack with two equal runs meeting below the line between the pins."""
        angle = 0.9 * percent
        c, s = cos(radians(angle)), sin(radians(angle))
        dx = self.door_x * c - EYE_HEIGHT * s - self.frame_x
        dz = self.door_x * s + EYE_HEIGHT * c - EYE_HEIGHT
        distance = hypot(dx, dz)
        sag = sqrt(max(0.0, self.length**2 - distance**2)) / (2 * distance)
        ex, ez = dx / 2 - dz * sag, dz / 2 + dx * sag
        # The mesh points down at zero rotation. The door run also inherits flap rotation.
        return degrees(atan2(-ez, ex)) - 90, degrees(atan2(dz - ez, ex - dx)) + angle - 90


def _links(span: float, *, quarter_turn: bool) -> Part:
    # The supplier gives the 2mm wire diameter. Pitch and waist are nominal visual dimensions.
    count = max(3, round(span / 13))
    pitch = span / count
    a = pitch / 2 + 2
    path = Edge.make_spline([(a, 0, 0), (a - 3, 0, 3), (0, 0, 2.2), (3 - a, 0, 3),
                             (-a, 0, 0), (3 - a, 0, -3), (0, 0, -2.2), (a - 3, 0, -3)], periodic=True)
    section = Face(Wire.make_circle(1, Plane(origin=path.position_at(0), z_dir=path.tangent_at(0))))
    link = Solid.sweep(section, path)
    solids = []
    for i in range(count):
        twist = 90 if i % 2 else 0
        if quarter_turn:
            twist += 90 * i / (count - 1)
        solids.append(link.moved(Location(((i + 0.5) * pitch, 0, 0), (twist, 0, 0))))
    return Part(solids, color=METAL).rotate(Axis.Y, 90, transform=True)


def _cylinder(x: float, y: float, z: float, direction: tuple[int, int, int], radius: float, length: float) -> Solid:
    return Solid.make_cylinder(radius, length, Plane(origin=(x, y, z), z_dir=direction))


def _anchor(moving: bool, thickness: float) -> tuple[Part, list[Solid]]:
    """Nominal angle lug with a retained transverse pin. Origin is the pin centre."""
    # The frame foot reaches across the opening onto the stile. The door foot points into the flap.
    foot_y = -23 if not moving else -4
    foot = panel(2, 23, 22).moved(Location((-PIN_OFFSET, foot_y, -11)))
    cheek = panel(PIN_OFFSET + 3, 2, 10).moved(Location((-PIN_OFFSET, -4, -5)))
    lug = foot + cheek
    hardware = [_cylinder(0, -4, 0, (0, 1, 0), 1.5, 8),
                _cylinder(0, 4, 0, (0, 1, 0), 3.3, 1)]
    bores = []
    for z in (-6, 6):
        y = DOOR_FASTENER_INSET_MM - PIN_INSET if moving else foot_y + 6
        # Door fixings go through the ply. Frame screws enter from behind the stile.
        depth = thickness if moving else min(10, thickness - 2)
        bore = _cylinder(-PIN_OFFSET - depth, y, z, (1, 0, 0), 1.7 if moving else 1.2, depth)
        bores.append(bore)
        lug -= _cylinder(-PIN_OFFSET, y, z, (1, 0, 0), 1.7, 2)
        hardware.append(_cylinder(-PIN_OFFSET - depth, y, z, (1, 0, 0), 1.5, depth + 2))
        hardware.append(_cylinder(-PIN_OFFSET + 2, y, z, (1, 0, 0), 3, 2))
        if moving:
            hardware.append(_cylinder(-PIN_OFFSET - depth - 1.5, y, z, (1, 0, 0), 3, 1.5))
    return Part([*lug.solids(), *hardware], label="Anchor and fixings (nominal)", color=METAL), bores


def build_chain(
    layout: ChainLayout, percent: float, jamb: float, label: str, *, side: int,
) -> tuple[Compound, Compound, list[Solid], list[Solid]]:
    """Side points from the outer post into the opening along Y."""
    frame_angle, door_angle = layout.angles(percent)
    groups, cut_sets = [], []
    for moving, x, angle, thickness in ((False, layout.frame_x, frame_angle, layout.stile_thickness),
                                        (True, layout.door_x, door_angle, layout.door_thickness)):
        pivot = Location((x, jamb + side * PIN_INSET, EYE_HEIGHT))
        anchor, holes = _anchor(moving, thickness)
        run = _links(layout.length / 2, quarter_turn=moving)
        if side < 0:
            anchor = anchor.mirror(Plane.XZ)
            holes = [hole.mirror(Plane.XZ) for hole in holes]
            run = run.mirror(Plane.XZ)
        run.label = "Door run" if moving else "Frame run"
        run.location = pivot * Location((0, 0, 0), (0, angle, 0))
        groups.append(Compound(label=CHAIN if moving else f"{label} {CHAIN}", children=[anchor.moved(pivot), run]))
        cut_sets.append([hole.moved(pivot) for hole in holes])
    return groups[0], groups[1], cut_sets[0], cut_sets[1]
