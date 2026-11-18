"""Instant Panel 600mm bed lift: photo-derived four-bar geometry, not drilling dimensions.

Published: A600, B110 overall height, C270, D340 and E420mm. The generic
photograph is not uniformly to scale. Pivot spacings, short arm and mounting
offsets below are estimates fitted to it; B is not treated as a link length.
Source: instantpanel.co.nz/product_img/OriginalPhotos/BIDX1PS26/gas-struts-frame-assembly-7.jpg
"""

from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, radians, sin, sqrt

from build123d import Align, Color, Compound, Cylinder, Location, Part, RegularPolygon, Solid, Sphere

from campervan.cad.panels import panel

TOP_RAIL = 600.0
TOP_RAIL_END_TRIM = 18.0
BASE_RAIL = 420.0
LONG_ARM = 270.0
STRUT_OPEN = 340.0
# Estimated pivot-centre dimensions and pin offsets, in mm.
GROUND_SPACING = 350.0
UPPER_SPACING = 155.0
SHORT_ARM = 95.0
UPPER_REAR_OFFSET = 25.0
UPPER_PIVOT_DROP = 20.0
UPPER_FLANGE_DEPTH = UPPER_PIVOT_DROP + 8.0
STRUT_TOP_OFFSET = 500.0
STRUT_ARM_OFFSET = 125.0
RAIL_WIDTH = 30.0
MOUNT_STEEL = 6.7
# Illustrative mounting centres, clear of the linkage and spring pivots.
FIXED_BOLT_XS = (55.0, 155.0, 255.0, 395.0)
LID_BOLT_XS = (85.0, 285.0, 465.0)
LID_COUNTERBORE_RADIUS = 9.0
LID_COUNTERBORE_DEPTH = 6.0
GAS_AXIS_Y = 24.0
BLACK = Color(0.14, 0.15, 0.16)
SILVER = Color(0.7, 0.72, 0.74)
ROOT = "/Campervan/Long bench/Lid hinges"


@dataclass(frozen=True)
class LiftPose:
    angle: float
    rear_pin: tuple[float, float]
    front_pin: tuple[float, float]
    lid_rear: tuple[float, float]
    strut_pin: tuple[float, float]
    strut_angle: float
    strut_length: float


def lift_pose(angle: float) -> LiftPose:
    """Intersect the two arm circles for a given upper-rail angle (XZ plane)."""
    a = radians(angle)
    ux, uz = cos(a), sin(a)
    dx, dz = GROUND_SPACING - UPPER_SPACING * ux, -UPPER_SPACING * uz
    distance = hypot(dx, dz)
    along = (SHORT_ARM**2 - LONG_ARM**2 + distance**2) / (2 * distance)
    height_squared = SHORT_ARM**2 - along**2
    if height_squared < 0:
        raise ValueError("Bed lift angle is outside the four-bar's reachable branch.")
    height = sqrt(height_squared)
    px = (along * dx - height * dz) / distance
    pz = (along * dz + height * dx) / distance
    qx, qz = px + UPPER_SPACING * ux, pz + UPPER_SPACING * uz
    rear = (px - UPPER_REAR_OFFSET * ux - UPPER_PIVOT_DROP * uz,
            pz - UPPER_REAR_OFFSET * uz + UPPER_PIVOT_DROP * ux)
    fraction = STRUT_ARM_OFFSET / LONG_ARM
    sx = GROUND_SPACING + fraction * (qx - GROUND_SPACING)
    sz = fraction * qz
    tx, tz = px + STRUT_TOP_OFFSET * ux, pz + STRUT_TOP_OFFSET * uz
    return LiftPose(angle, (px, pz), (qx, qz), rear, (sx, sz),
                    degrees(atan2(tz - sz, tx - sx)), hypot(tx - sx, tz - sz))


def opening_angle() -> float:
    """Working stop: interpret the illustrated D340 as the extended strut length.

    Actual stroke/stops are unpublished. This inferred half-open envelope must
    be checked against the purchased hardware, rather than assuming a 75° lift.
    """
    low, high = 0.0, 45.0
    for _ in range(40):
        middle = (low + high) / 2
        if lift_pose(middle).strut_length < STRUT_OPEN:
            low = middle
        else:
            high = middle
    return (low + high) / 2


OPEN_ANGLE = opening_angle()
CLOSED = lift_pose(0)


def lid_location(rear: float, bottom: float, percent: float) -> Location:
    pose = lift_pose(OPEN_ANGLE * percent / 100)
    return Location((rear + pose.lid_rear[0] - CLOSED.lid_rear[0], 0,
                     bottom + pose.lid_rear[1] - CLOSED.lid_rear[1]), (0, -pose.angle, 0))


def bar(name: str, length: float, y: float) -> Compound:
    arm = panel(length, 5, 20)
    arm.location = Location((0, y, -10))
    arm.label, arm.color = "Steel arm (estimated section)", BLACK
    pins = []
    for i, x in enumerate((0, length)):
        pin = Cylinder(5, 30, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.CENTER))
        pin.location = Location((x, -12 if y < 0 else 12, 0))
        pin.label, pin.color = f"Pivot {i + 1}", SILVER
        pins.append(pin)
    return Compound(label=name, children=[arm, *pins])


def strut_pin(name: str, x: float, z: float, mirrored: bool) -> Cylinder:
    """Estimated through-pin spans flange, arm and the outboard gas-spring eye."""
    pin = Cylinder(5, 40, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.CENTER))
    pin.location = Location((x, -12 if mirrored else 12, z))
    pin.label, pin.color = name, SILVER
    return pin


def lift_members(pose: LiftPose) -> dict[str, tuple[float, float, float]]:
    """Local X/Z/rotation-Y poses, shared by CAD and browser keyframes."""
    px, pz = pose.rear_pin
    qx, qz = pose.front_pin
    return {
        "Upper rail": (*pose.lid_rear, -pose.angle),
        "Rear arm": (0, 0, -degrees(atan2(pz, px))),
        "Front arm": (GROUND_SPACING, 0, -degrees(atan2(qz, qx - GROUND_SPACING))),
        "Gas spring": (*pose.strut_pin, -pose.strut_angle),
    }


def lift_mounts(length: float, wall: float, rear_panel_y: float) -> tuple[tuple[str, float, bool], ...]:
    """Fixed mounting faces, also used to position the wall-panel clearance cuts."""
    return (("Rear lift", rear_panel_y + wall, False), ("Cab-end lift", length - wall, True))


def lift_notches(length: float, wall: float, rear_panel_y: float) -> tuple[tuple[float, float, float], ...]:
    """Y bounds and depth shared by the box walls and the sliding support rail."""
    clearance = 5.0
    depth = UPPER_FLANGE_DEPTH + 12.0  # Previous 30mm cuts, deepened by 10mm.
    return tuple((y - (RAIL_WIDTH if mirrored else 0) - clearance,
                  y + (0 if mirrored else RAIL_WIDTH) + clearance, depth)
                 for _, y, mirrored in lift_mounts(length, wall, rear_panel_y))


def mounting_bolt(wood: float, length: float, *, allen: bool = False) -> Part:
    """Nominal M6 bolt, M6 × 16 washer and Nyloc; shaft points along +Z.

    Head underside is Z=0. Allen heads have a washer at Z=0..1.6;
    coach heads bear directly on wood. Physical head dimensions remain to confirm.
    """
    head_radius, head_height = (5.25, 3.3) if allen else (8.3, 3.5)
    sphere_radius = (head_radius**2 + head_height**2) / (2 * head_height)
    sphere = Sphere(sphere_radius).moved(Location((0, 0, sphere_radius - head_height)))
    cap = sphere & panel(2 * head_radius, 2 * head_radius, head_height).moved(
        Location((-head_radius, -head_radius, -head_height)))
    if allen:
        # Provisional button-head envelope: Pinnacle publishes the hex drive,
        # but not the head or key dimensions. Confirm before machining pockets.
        socket_face = RegularPolygon(4 / 3**0.5, 6).faces()[0]
        cap -= Solid.extrude(socket_face, (0, 0, 2)).moved(Location((0, 0, -head_height)))
    shaft = Cylinder(3, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    neck = panel(6, 6, 4).moved(Location((-3, -3, 0)))
    washer_z = wood + MOUNT_STEEL
    washer = (Cylinder(8, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
              - Cylinder(3.25, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    washer = washer.moved(Location((0, 0, washer_z)))
    hex_face = RegularPolygon(10 / 3**0.5, 6).faces()[0]
    nut = (Solid.extrude(hex_face, (0, 0, 6))
           - Cylinder(3, 6, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    nut = nut.moved(Location((0, 0, washer_z + 1.6)))
    pieces = [*shaft.solids(), *cap.solids(), *washer.solids(), *nut.solids()]
    if allen:
        head_washer = washer.moved(Location((0, 0, -washer_z)))
        pieces.extend(head_washer.solids())
    else:
        pieces.extend(neck.solids())
    bolt = Part(pieces)
    bolt.color = SILVER
    return bolt


def build_lifts(rear: float, bottom: float, length: float, wall: float, percent: float,
                *, rear_panel_y: float, slat_thickness: float) -> Compound:
    pose = lift_pose(OPEN_ANGLE * percent / 100)
    assemblies = []
    bolt = mounting_bolt(wall, 40)
    # The head washer bears on the counterbore floor; its 1.6mm thickness
    # raises the head's bearing plane above that floor.
    lid_grip = wall + slat_thickness - LID_COUNTERBORE_DEPTH + 1.6
    lid_bolt = mounting_bolt(lid_grip, 50, allen=True)
    for name, y, mirrored in lift_mounts(length, wall, rear_panel_y):
        base = panel(BASE_RAIL, MOUNT_STEEL, 20)
        base.location = Location((-16, -MOUNT_STEEL if mirrored else 0, -10))
        base.label, base.color = "Fixed mounting rail", BLACK
        upper = panel(TOP_RAIL - TOP_RAIL_END_TRIM, RAIL_WIDTH, MOUNT_STEEL)
        upper.location = Location((0, -RAIL_WIDTH if mirrored else 0, -MOUNT_STEEL))
        flange = panel(TOP_RAIL - TOP_RAIL_END_TRIM, 3, UPPER_FLANGE_DEPTH)
        flange.location = Location((0, -3 if mirrored else 0, -UPPER_FLANGE_DEPTH))
        upper += flange
        upper.label, upper.color = "Lid mounting rail (estimated section)", BLACK
        body = Cylinder(8, 180, rotation=(0, 90, 0), align=(Align.CENTER, Align.CENTER, Align.MIN))
        body.label, body.color = "Cylinder (estimated envelope)", BLACK
        shaft = Cylinder(4, 160, rotation=(0, 90, 0), align=(Align.CENTER, Align.CENTER, Align.MIN))
        shaft.label, shaft.color = "Rod (estimated envelope)", SILVER
        rod = Compound(label="Sliding rod", children=[shaft])
        rod.location = Location((pose.strut_length - 160, 0, 0))
        spring = Compound(label="Gas spring", children=[body, rod])
        fixed_bolts, lid_bolts = [], []
        for index, x in enumerate(FIXED_BOLT_XS, 1):
            fixing = bolt.moved(Location((x, wall if mirrored else -wall, 0),
                                         (90 if mirrored else -90, 0, 0)))
            fixing.label = f"Fixed rail coach bolt {index} · M6 × 40 with washer and Nyloc (nominal)"
            fixed_bolts.append(fixing)
        for index, x in enumerate(LID_BOLT_XS, 1):
            fixing = lid_bolt.moved(Location((x, -RAIL_WIDTH / 2 if mirrored else RAIL_WIDTH / 2,
                                             lid_grip),
                                         (180, 0, 0)))
            fixing.label = f"Lid rail Allen bolt {index} · M6 × 50 with two washers and Nyloc (nominal)"
            lid_bolts.append(fixing)
        members = {
            "Upper rail": Compound(label="Upper rail", children=[upper,
                Compound(label="Lid mounting bolts", children=lid_bolts),
                strut_pin("Upper gas-spring attachment", UPPER_REAR_OFFSET + STRUT_TOP_OFFSET,
                          -UPPER_PIVOT_DROP, mirrored)]),
            "Rear arm": bar("Rear arm", SHORT_ARM, -MOUNT_STEEL - 5 if mirrored else MOUNT_STEEL),
            "Front arm": bar("Front arm", LONG_ARM, -MOUNT_STEEL - 10 if mirrored else MOUNT_STEEL + 5),
            "Gas spring": spring,
        }
        members["Front arm"].children = [*members["Front arm"].children,
                                        strut_pin("Lower gas-spring attachment", STRUT_ARM_OFFSET, 0, mirrored)]
        for key, (x, z, angle) in lift_members(pose).items():
            members[key].location = Location((x, (-GAS_AXIS_Y if mirrored else GAS_AXIS_Y)
                                             if key == "Gas spring" else 0, z),
                                             (0, angle, 0))
        assembly = Compound(label=name, children=[base,
            Compound(label="Fixed mounting bolts", children=fixed_bolts), *members.values()])
        assembly.location = Location((rear - CLOSED.lid_rear[0], y, bottom - CLOSED.lid_rear[1]))
        assemblies.append(assembly)
    return Compound(label="Lid hinges", children=assemblies)


def lift_motion_tracks(rear: float, bottom: float) -> list[dict[str, object]]:
    poses = [(percent, lift_pose(OPEN_ANGLE * percent / 100)) for percent in range(101)]
    tracks: list[dict[str, object]] = []
    for axis, index in (("x", 0), ("z", 1)):
        start = rear if axis == "x" else bottom
        tracks.append({"path": "/Campervan/Long bench/Hinged lid", "axis": axis,
                       "keyframes": [(percent, start + pose.lid_rear[index] - CLOSED.lid_rear[index])
                                     for percent, pose in poses]})
    tracks.append({"path": "/Campervan/Long bench/Hinged lid", "axis": "y", "kind": "rotation",
                   "keyframes": [(percent, -pose.angle) for percent, pose in poses]})
    for lift in ("Rear lift", "Cab-end lift"):
        for member in lift_members(CLOSED):
            # Three.js decomposes Y angles beyond 90° into an equivalent XYZ
            # rotation with X/Z = 180°. Set all three Euler components so an
            # absolute Y track does not retain those decomposition flips.
            for axis in ("x", "z"):
                tracks.append({"path": f"{ROOT}/{lift}/{member}", "axis": axis, "kind": "rotation",
                               "keyframes": [(0, 0), (100, 0)]})
            for index, (axis, kind) in enumerate((("x", "translation"), ("z", "translation"), ("y", "rotation"))):
                tracks.append({"path": f"{ROOT}/{lift}/{member}", "axis": axis, "kind": kind,
                               "keyframes": [(percent, lift_members(pose)[member][index]) for percent, pose in poses]})
        tracks.append({"path": f"{ROOT}/{lift}/Gas spring/Sliding rod", "axis": "x",
                       "keyframes": [(percent, pose.strut_length - 160) for percent, pose in poses]})
    return tracks
