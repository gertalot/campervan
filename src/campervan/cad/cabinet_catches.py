"""Taskmaster roller catches for cabinet doors; hardware dimensions are nominal previews."""

from dataclasses import dataclass

from build123d import Align, Color, Compound, Cone, Cylinder, Face, Location, Part, Solid, Wire

from campervan.cad.cabinet_layout import cabinet_front
from campervan.cad.panels import panel
from campervan.parameters import Parameters

METAL = Color(0.48, 0.50, 0.53)
MOUNT_HEIGHT = 40.0
MOUNT_DEPTH = 30.0


@dataclass
class DoorCatch:
    keeper: Part
    fixings: Compound
    body: Compound
    mount: Part
    door_holes: list[Part]
    frame_cuts: list[Part]


def _cylinder_x(radius: float, length: float, x: float, y: float, z: float) -> Part:
    return Cylinder(radius, length, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((x, y, z), (0, 90, 0)))


def build_door_catch(p: Parameters, label: str, pose: Location) -> DoorCatch:
    """Build at the free-edge midpoint, with local +Y pointing out of the door opening."""
    face = cabinet_front(p)
    back, mount_x = face + p.cabinet_door_thickness_mm, face + p.cabinet_frame_thickness_mm
    mount_pose = Location((mount_x, 0, -MOUNT_HEIGHT / 2))
    mount = panel(MOUNT_DEPTH, 18, MOUNT_HEIGHT).moved(mount_pose)
    frame_cuts, door_holes, hardware, keeper_fixings = [], [], [], []

    # The base lies against the block's opening-facing side. Rollers face towards the door.
    plate = panel(25, 1, 32).moved(Location((mount_x, -1, -16)))
    for sign in (-1, 1):
        z = sign * 12
        screw_pose = Location((mount_x + 12.5, -1, z), (-90, 0, 0))
        plate -= Cylinder(1.6, 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(screw_pose)
        mount -= Cylinder(1.15, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(screw_pose)
        shaft = Cylinder(1.5, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(screw_pose)
        head = Cylinder(2.7, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((mount_x + 12.5, -2.5, z), (-90, 0, 0)))
        hardware.append(Part([*shaft.solids(), *head.solids()], label="Included catch-base screw · nominal", color=METAL))
        roller_pose = Location((mount_x + 5, -14, sign * 7.5), (-90, 0, 0))
        roller = Cylinder(3.5, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(roller_pose)
        hardware.append(Part(roller.solids(), label="Roller · nominal", color=METAL))

        # Glue the block's broad face to the frame and screw through the unreduced timber band.
        y, z = 9, sign * 10
        frame_cuts.append(_cylinder_x(1.9, p.cabinet_frame_thickness_mm + 2, face - 1, y, z))
        head_pose = Location((face, y, z), (0, 90, 0))
        countersink = Cone(3.3, 1.9, 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(head_pose)
        frame_cuts.append(countersink)
        mount -= _cylinder_x(1.2, 24, mount_x, y, z)
        shaft = _cylinder_x(1.75, 40, face, y, z)
        head = Cone(3.2, 1.75, 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(head_pose)
        hardware.append(Part([*shaft.solids(), *head.solids()], label="Block screw · 6g × 40 nominal", color=METAL))
    plate.label, plate.color = "Catch base plate · nominal", METAL
    hardware.append(plate)
    mount = Part(mount.moved(mount_pose.inverse()).solids(), label=f"{label} catch mounting block", color=Color(0.84, 0.64, 0.39))
    mount.location = mount_pose

    keeper_plate = panel(1.2, 18, 24).moved(Location((back, -20, -12)))
    tongue = Face(Wire.make_polygon([
        (back + 1.2, -9, -2), (mount_x + 5, -9, -4),
        (mount_x + 9, -9, -2), (mount_x + 9, -9, 2),
        (mount_x + 5, -9, 4), (back + 1.2, -9, 2),
    ]))
    tongue_solid = Solid.extrude(tongue, (0, 2, 0))
    for sign in (-1, 1):
        y, z = -11, sign * 8
        bore = _cylinder_x(1.6, p.cabinet_door_thickness_mm + 3, face - 1, y, z)
        door_holes.append(bore)
        keeper_plate -= bore
        grip = p.cabinet_door_thickness_mm + 1.2
        shaft = _cylinder_x(1.5, 12, face, y, z)
        head = _cylinder_x(2.7, 1.5, face - 1.5, y, z)
        washer = _cylinder_x(4, 0.5, face + grip, y, z) - _cylinder_x(1.6, 0.5, face + grip, y, z)
        nut = _cylinder_x(2.8, 2.4, face + grip + 0.5, y, z) - _cylinder_x(1.5, 2.4, face + grip + 0.5, y, z)
        keeper_fixings.append(Part([*shaft.solids(), *head.solids(), *washer.solids(), *nut.solids()],
                                  label="Keeper door bolt · M3 × 12 nominal", color=METAL))
    keeper = Part([*keeper_plate.solids(), *tongue_solid.solids()],
                  label="Roller catch keeper · estimated envelope", color=METAL)
    # Relief is confined to the back lip; the front pocket and outer face retain their existing outline.
    frame_cuts.append(panel(p.cabinet_frame_thickness_mm - p.cabinet_door_thickness_mm + 1, 19.5, 28).moved(
        Location((back, -21, -14))))
    fixings = Compound(label="Keeper fixings", children=keeper_fixings)
    body = Compound(label=f"{label} catch body · nominal", children=hardware)
    for shape in (keeper, fixings, body, mount, *door_holes, *frame_cuts):
        shape.location = pose * shape.location
    return DoorCatch(keeper, fixings, body, mount, door_holes, frame_cuts)
