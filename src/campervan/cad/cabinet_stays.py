"""Penn Elcom P1240 folding stay. Coordinates are relative to the top piano-hinge pin, in mm."""

from dataclasses import dataclass
from math import acos, atan2, cos, degrees, hypot, radians, sin, sqrt
from typing import NamedTuple

from build123d import Axis, Color, Compound, Face, Location, Part, Plane, Solid, Wire

from campervan.cad.cabinet_piano import HINGE_PROJECTION
from campervan.cad.panels import panel

PENN = "Penn Elcom P1240"
SPACER_LENGTH = 10.0
ARM_GAUGE = 1.5
PENN_LONG_LEG, PENN_SHORT_LEG = 80.0, 18.0
# Direction from the centre stile into each opening, along the cabinet Y axis.
STAY_SIDES = {"Box 5 flap": 1, "Box 7 flap": -1}
FRAME_ARM_REFERENCE = -75
DOOR_ARM_REFERENCE = -35
STEEL = Color(0.68, 0.70, 0.72)
PINE = Color(0.84, 0.64, 0.39)


class StayPose(NamedTuple):
    flap: float
    frame_arm: float
    door_arm: float


@dataclass(frozen=True)
class StayLayout:
    pitch: float
    frame_x: float
    frame_z: float
    door_x: float
    door_z: float

    open_angle: float

    def pose(self, percent: float) -> StayPose:
        # Keep the elbow on its folding side so a downward drag always closes the flap.
        angle = self.open_angle * percent / 100
        c, s = cos(radians(angle)), sin(radians(angle))
        x, z = self.door_x * c + self.door_z * s, self.door_z * c - self.door_x * s
        dx, dz = x - self.frame_x, z - self.frame_z
        separation = hypot(dx, dz)
        rise_sq = self.pitch**2 - (separation / 2)**2
        if rise_sq < -1e-7 or separation < 1e-6:
            raise ValueError(f"{PENN} cannot reach its mounting points at {angle:g} degrees.")
        k = sqrt(max(0, rise_sq)) / separation
        ex, ez = dx / 2 + dz * k, dz / 2 - dx * k
        # Arms are drawn at -75 and -35 degrees to keep their local viewer rotations within ±90.
        return StayPose(angle, degrees(atan2(-ez, ex)) - FRAME_ARM_REFERENCE,
                        degrees(atan2(dz - ez, ex - dx)) - angle - DOOR_ARM_REFERENCE)


def stay_layout(door_thickness: float, stile_thickness: float) -> StayLayout:
    pitch = hypot(PENN_LONG_LEG, PENN_SHORT_LEG)
    # Keep the screw centre 5 mm from the back edge of the rebated stile.
    ax = HINGE_PROJECTION + stile_thickness - 5
    if ax - 6 <= HINGE_PROJECTION + door_thickness:
        raise ValueError("The fixed stay eye needs clearance behind the closed flap.")
    bx, bz = HINGE_PROJECTION + door_thickness + 9, -83.0
    # At horizontal the moving eye is at (bz, -bx) relative to the piano hinge.
    az = -bx - sqrt((2 * pitch)**2 - (ax - bz)**2)
    # At the assumed stop the long webs line up and the eyes span two long legs.
    frame_radius, door_radius = hypot(ax, az), hypot(bx, bz)
    included = acos((frame_radius**2 + door_radius**2 - (2 * PENN_LONG_LEG)**2) / (2 * frame_radius * door_radius))
    open_angle = degrees(atan2(bz, bx) - atan2(az, ax) + included)
    return StayLayout(pitch, ax, az, bx, bz, open_angle)


def _disc(x: float, y: float, z: float, r: float, depth: float) -> Solid:
    return Solid.make_cylinder(r, depth, Plane(origin=(x, y, z), z_dir=(0, 1, 0)))


def _strap(start: tuple[float, float], end: tuple[float, float], y: float, gauge: float, width: float) -> Part:
    x, z = start
    u, v = end
    r = width / 2
    length = hypot(u - x, v - z)
    nx, nz = (z - v) * r / length, (u - x) * r / length
    web = Face(Wire.make_polygon([(x + nx, y, z + nz), (u + nx, y, v + nz),
                                  (u - nx, y, v - nz), (x - nx, y, z - nz)]))
    return Part([Solid.extrude(web, (0, gauge, 0))]) + _disc(x, y, z, r, gauge) + _disc(u, y, v, r, gauge)


def _arm(layout: StayLayout, moving: bool) -> Part:
    pitch = layout.pitch
    gauge = ARM_GAUGE
    y = 3.5 + (gauge if moving else 0)
    # Each pressed arm has an offset end eye and a dogleg at the elbow.
    ux, uz = PENN_LONG_LEG / pitch, (1 if moving else -1) * PENN_SHORT_LEG / pitch
    tip = (PENN_LONG_LEG * ux, PENN_LONG_LEG * uz)
    tab_y = 0.0  # Both pressed tabs step back onto the same mounting plane.
    link = _strap((0, 0), (10 * ux, 10 * uz), tab_y, gauge, 12)
    ramp = Face(Wire.make_polygon([
        (10*ux-6*uz, tab_y, 10*uz+6*ux), (10*ux+6*uz, tab_y, 10*uz-6*ux),
        (15*ux+6*uz, y, 15*uz-6*ux), (15*ux-6*uz, y, 15*uz+6*ux)]))
    link += Solid.extrude(ramp, (0, gauge, 0))
    link += _strap((15 * ux, 15 * uz), tip, y, gauge, 12)
    link += _strap(tip, (pitch, 0), y, gauge, 12)
    link -= _disc(0, tab_y - 1, 0, 2.1, gauge + 2)
    if not moving:
        link += _disc(pitch, y - 0.6, 0, 3.5, 2 * gauge + 1.2)
    # Bake the reference orientation into the geometry; animate about the actual end eye.
    shape = link.rotate(Axis.Y, DOOR_ARM_REFERENCE if moving else FRAME_ARM_REFERENCE, transform=True)
    return Part(shape.solids(), label="Door arm" if moving else "Frame arm", color=STEEL)


def build_stay(
    label: str, layout: StayLayout, pose: StayPose, jamb: float, side: int, door_thickness: float,
) -> tuple[Compound, Compound, Part, Solid]:
    """Locate the reversed arms between the stile and the flap pad. Jamb is relative to the door origin."""
    mount_y = jamb + side * (SPACER_LENGTH + ARM_GAUGE)
    frame_pose = Location((layout.frame_x, mount_y, layout.frame_z))
    door_pose = Location((layout.door_x, mount_y, layout.door_z))

    def handed(part: Part) -> Part:
        if side < 0:
            return part
        return Part(part.mirror(Plane.XZ).solids(), label=part.label, color=part.color)

    frame_arm, door_arm = handed(_arm(layout, False)), handed(_arm(layout, True))
    frame_arm.location = frame_pose * Location((0, 0, 0), (0, pose.frame_arm, 0))
    door_arm.location = door_pose * Location((0, 0, 0), (0, pose.door_arm, 0))

    # In arm coordinates +Y points towards the stile. The screws enter opposite faces.
    spacer = _disc(0, ARM_GAUGE, 0, 4, SPACER_LENGTH) - _disc(0, ARM_GAUGE, 0, 2.2, SPACER_LENGTH)
    frame_screw = _disc(0, 0, 0, 2, 25) + _disc(0, -2, 0, 3.5, 2)
    door_screw = _disc(0, ARM_GAUGE - 12, 0, 2, 12) + _disc(0, ARM_GAUGE, 0, 3.5, 2)

    def hardware(shape: Solid | Part, name: str, placement: Location) -> Part:
        return handed(Part(shape.solids(), label=name, color=STEEL)).moved(placement)

    fixed = Compound(label=f"{label} {PENN}", children=[
        frame_arm, hardware(spacer, "10 mm pivot spacer", frame_pose),
        hardware(frame_screw, "Stile pivot screw (nominal)", frame_pose),
    ])
    moving = Compound(label=PENN, children=[door_arm, hardware(door_screw, "Door pivot screw (nominal)", door_pose)])
    # Drill from the compartment into the post, and from the stile side into the loose flap pad.
    bite = 25 - ARM_GAUGE - SPACER_LENGTH
    bore_y = jamb - bite if side > 0 else jamb
    frame_bore = _disc(layout.frame_x, bore_y, layout.frame_z, 1.25, bite)
    pad_bore_y = 0 if side > 0 else 18 - (12 - ARM_GAUGE)
    pad = panel(18, 18, 50) - _disc(9, pad_bore_y, 25, 1.25, 12 - ARM_GAUGE)
    pad.label, pad.color = "Pine stay door pad", PINE
    pad.location = Location((HINGE_PROJECTION + door_thickness, mount_y - (18 if side < 0 else 0), layout.door_z - 25))
    return fixed, moving, pad, frame_bore
