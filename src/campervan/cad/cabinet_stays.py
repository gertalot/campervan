"""Two trial folding stays. Coordinates are relative to the top piano-hinge pin, in mm."""

from dataclasses import dataclass
from math import acos, asin, atan2, cos, degrees, hypot, pi, radians, sin, sqrt
from typing import NamedTuple

from build123d import Axis, Color, Compound, Face, Location, Part, Plane, Solid, Wire

from campervan.cad.cabinet_piano import HINGE_PROJECTION
from campervan.cad.panels import panel

PENN = "Penn Elcom P1240"
VINTIQUE = "Vintique left-hand stay"
# Keep the Penn arms on the opening side of both timber pads.
PENN_MOUNT_FACE_INSET = 20.0
PENN_LONG_LEG, PENN_SHORT_LEG = 80.0, 18.0
FLAP_STAYS = {"Box 5 flap": PENN, "Box 7 flap": VINTIQUE}
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
    product: str
    pitch: float
    frame_x: float
    frame_z: float
    door_x: float
    door_z: float

    # Penn motion phase in radians. A quarter turn is dead centre.
    stop_phase: float | None

    def pose(self, percent: float) -> StayPose:
        angle = percent * 0.9
        past_centre = False
        if self.stop_phase is not None:
            phase = self.stop_phase * percent / 100
            # The flap reverses smoothly at horizontal as the elbow continues through centre.
            angle = 90 * sin(phase)
            past_centre = phase > pi / 2
        c, s = cos(radians(angle)), sin(radians(angle))
        x, z = self.door_x * c + self.door_z * s, self.door_z * c - self.door_x * s
        dx, dz = x - self.frame_x, z - self.frame_z
        separation = hypot(dx, dz)
        rise_sq = self.pitch**2 - (separation / 2)**2
        if rise_sq < -1e-7 or separation < 1e-6:
            raise ValueError(f"{self.product} cannot reach its mounting points at {angle:g} degrees.")
        k = sqrt(max(0, rise_sq)) / separation
        if past_centre:
            k = -k
        ex, ez = dx / 2 + dz * k, dz / 2 - dx * k
        # Arms are drawn at -75 and -35 degrees to keep their local viewer rotations within ±90.
        return StayPose(angle, degrees(atan2(-ez, ex)) - FRAME_ARM_REFERENCE,
                        degrees(atan2(dz - ez, ex - dx)) - angle - DOOR_ARM_REFERENCE)


def stay_layout(product: str, door_thickness: float, stile_thickness: float) -> StayLayout:
    if product == PENN:
        # The 80 x 18 dogleg locates the elbow pin. Full extension uses both eye-to-pin pitches.
        pitch = hypot(PENN_LONG_LEG, PENN_SHORT_LEG)
        ax = HINGE_PROJECTION + stile_thickness + 9
        bx, bz = HINGE_PROJECTION + door_thickness + 9, -83.0
    else:
        # Vintique lists swivel-to-tip. Eye centres estimated from the extended product photo.
        pitch = 98.5
        ax, bx, bz = HINGE_PROJECTION + stile_thickness + 34, HINGE_PROJECTION + door_thickness + 18 + 9, -114.0
    # At horizontal the moving eye is at (bz, -bx) relative to the piano hinge.
    az = -bx - sqrt((2 * pitch)**2 - (ax - bz)**2)
    stop_phase = None
    if product == PENN:
        # At the assumed stop the long webs line up and the eyes span two long legs.
        frame_radius, door_radius = hypot(ax, az), hypot(bx, bz)
        included = acos((frame_radius**2 + door_radius**2 - (2 * PENN_LONG_LEG)**2) / (2 * frame_radius * door_radius))
        rest_angle = degrees(atan2(bz, bx) - atan2(az, ax) + included)
        stop_phase = pi - asin(rest_angle / 90)
    return StayLayout(product, pitch, ax, az, bx, bz, stop_phase)


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
    penn = layout.product == PENN
    gauge = 1.5 if penn else 1.2
    y = (3.5 if penn else 1.2) + (gauge if moving else 0)
    if penn:
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
    else:
        link = _strap((0, 0), (pitch, 0), y, gauge, 12)
        if not moving:
            # Formed elbow stop visible in the product photo. Engagement is provisional.
            link += panel(3, 2 * gauge, 3).moved(Location((pitch - 8, y, 4)))
    if not moving:
        link += _disc(pitch, y - 0.6, 0, 3.5, 2 * gauge + 1.2)
    # Bake the reference orientation into the geometry; animate about the actual end eye.
    shape = link.rotate(Axis.Y, DOOR_ARM_REFERENCE if moving else FRAME_ARM_REFERENCE, transform=True)
    return Part(shape.solids(), label="Door arm" if moving else "Frame arm", color=STEEL)


def _vintique_plates() -> tuple[Part, Part]:
    # Nominal hole pattern; both plates have their origin at the end rivet.
    fixed = _strap((0, -14), (0, 14), 0, 1.2, 12)
    for z in (-15, 15):
        fixed -= _disc(0, -1, z, 1.8, 4)
    fixed += _disc(0, 0, 0, 3, 3)
    cheek = panel(9, 1.2, 12).moved(Location((-9, 3.6, -6))) + _disc(0, 3.6, 0, 6, 1.2)
    flange = panel(1.2, 12, 40).moved(Location((-9, 3.6, -20)))
    for z in (-15, 15):
        flange -= Solid.make_cylinder(1.8, 3, Plane(origin=(-10, 10, z), z_dir=(1, 0, 0)))
    moving = cheek + flange + _disc(0, 1.8, 0, 3, 3.4)
    return (Part(fixed.solids(), label="Cabinet pivot plate", color=STEEL),
            Part(moving.solids(), label="Bent door pivot plate", color=STEEL))


def build_stay(
    layout: StayLayout, pose: StayPose, jamb: float, door_thickness: float, stile_thickness: float,
) -> tuple[Compound, Compound, Part, Part]:
    """Local to hinge pin. Jamb is the opening-side face of the left stile."""
    penn = layout.product == PENN
    mount_y = jamb + PENN_MOUNT_FACE_INSET if penn else jamb
    frame_pose = Location((layout.frame_x, mount_y, layout.frame_z))
    door_pose = Location((layout.door_x, mount_y, layout.door_z))
    frame_arm, door_arm = _arm(layout, False), _arm(layout, True)
    frame_arm.location = frame_pose * Location((0, 0, 0), (0, pose.frame_arm, 0))
    door_arm.location = door_pose * Location((0, 0, 0), (0, pose.door_arm, 0))
    fixed, moving = [frame_arm], [door_arm]

    def pivot(label: str) -> Part:
        # Nominal shoulder and head, so the eye is free to pivot on its fixing.
        shape = _disc(0, -8.5, 0, 2, 10) + _disc(0, 1.5, 0, 3.5, 2)
        return Part(shape.solids(), label=label, color=STEEL)

    if penn:
        fixed.append(pivot("Stile pivot").moved(frame_pose))
        moving.append(pivot("Door pivot").moved(door_pose))
    else:
        plate, flange = _vintique_plates()
        fixed.append(plate.moved(frame_pose))
        moving.append(flange.moved(door_pose))
    depth, width = (18, 40) if penn else (40, 18)
    block = panel(depth, width, 50)
    block.label, block.color = f"{layout.product} stile extension", PINE
    block.location = Location((HINGE_PROJECTION + stile_thickness, mount_y - width, layout.frame_z - 25))
    pad = panel(18, 18, 50)
    pad.label, pad.color = "Pine stay door pad", PINE
    pad.location = Location((HINGE_PROJECTION + door_thickness, mount_y - 18 if penn else jamb + 4.8, layout.door_z - 25))
    return Compound(label=layout.product, children=fixed), Compound(label=layout.product, children=moving), pad, block
