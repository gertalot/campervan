"""Rebated lower-cabinet doors and cover, with pine-backed piano hinges."""

from dataclasses import dataclass

from build123d import Align, Axis, Color, Compound, Cylinder, GeomType, Location, Part, fillet

from campervan.cad.cabinet_catches import MOUNT_HEIGHT, DoorCatch, build_door_catch
from campervan.cad.cabinet_piano import BACKING_SIZE, END_CLEARANCE, HINGE_PROJECTION, piano_leaves
from campervan.cad.cabinet_layout import cabinet_front
from campervan.cad.panels import panel
from campervan.parameters import Parameters

DOOR_COLOR = Color(0.84, 0.72, 0.49)
REBATE_WIDTH = 10.0
FINGER_HOLE_DIAMETER = 30.0
# Parameter, assembly label and opening direction are shared by CAD and live viewer motion.
DOOR_CONTROLS = (
    ("cabinet_lower_doors_open_percent", "Cab-end bottom door", False),
    ("cabinet_front_middle_door_open_percent", "Cab-end middle flap", True),
    ("cabinet_front_upper_door_open_percent", "Cab-end above-bed flap", True),
)


@dataclass
class DoorBuild:
    door: Compound
    fixed: Part
    rebate: Part
    catch: DoorCatch


@dataclass
class CabinetDoors:
    assembly: Compound
    frame_cuts: list[Part]
    mounts: list[Part]


def panel_rebate(p: Parameters, start: float, bottom: float, width: float, height: float) -> Part:
    """Closed-panel pocket, with the same reveal on every framed edge."""
    gap = p.cabinet_door_gap_mm
    face = cabinet_front(p)
    if p.cabinet_door_thickness_mm >= p.cabinet_frame_thickness_mm:
        raise ValueError("Cabinet panel rebates must leave timber behind the panels.")
    pocket = panel(width + 2 * gap, p.cabinet_door_thickness_mm, height + 2 * gap)
    pocket = fillet(pocket.edges().filter_by(Axis.Y), p.cabinet_door_corner_radius_mm + gap)
    return pocket.moved(Location((face + p.cabinet_door_thickness_mm, start - gap, bottom - gap), (0, 0, 90)))


def _hinged_door(
    p: Parameters, label: str, start: float, bottom: float, width: float, height: float, angle: float,
    *, flap: bool = False,
) -> DoorBuild:
    face = cabinet_front(p)
    reveal, thickness = p.cabinet_door_gap_mm, p.cabinet_door_thickness_mm
    pin_x = face - HINGE_PROJECTION
    pin_y = start - reveal / 2
    pin_z = bottom - reveal / 2 if flap else bottom
    origin = Location((pin_x, start if flap else pin_y, pin_z))
    wood_pose = Location((face + thickness, start, bottom), (0, 0, 90))
    corner, edge = p.cabinet_door_corner_radius_mm, p.cabinet_door_edge_radius_mm
    if min(width, height) < 85 or corner <= edge or 2 * edge >= thickness:
        raise ValueError("Inset doors need room for their finger holes, rounded corners and edge easing.")
    wood = panel(width, thickness, height)
    wood = fillet(wood.edges().filter_by(Axis.Y), corner)
    wood = fillet(wood.edges().filter_by(Axis.Y, reverse=True), edge)
    hole_x = width / 2 if flap else width - 35
    hole_z = height - 35 if flap else height / 2
    hole = Cylinder(FINGER_HOLE_DIAMETER / 2, thickness + 2, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((hole_x, thickness + 1, hole_z))
    )
    wood -= hole
    circles = [e for e in wood.edges().filter_by(GeomType.CIRCLE) if abs(e.radius - FINGER_HOLE_DIAMETER / 2) < 1e-6]
    wood = fillet(circles, edge)
    hinge_length = (width if flap else height) - 2 * END_CLEARANCE
    if flap:
        hinge_pose = Location((pin_x, start + width - END_CLEARANCE, pin_z), (90, 0, 0))
        backing = panel(BACKING_SIZE, hinge_length, BACKING_SIZE).moved(
            Location((face + thickness, start + END_CLEARANCE, bottom)))
    else:
        hinge_pose = Location((pin_x, pin_y, bottom + END_CLEARANCE))
        backing_y = start
        backing = panel(BACKING_SIZE, BACKING_SIZE, hinge_length).moved(
            Location((face + thickness, backing_y, bottom + END_CLEARANCE)))
    backing.label, backing.color = "Pine hinge backing strip", Color(0.84, 0.64, 0.39)
    backing.location = origin.inverse() * backing.location
    fixed_leaf, moving_leaf = piano_leaves(hinge_length, reveal, hinge_pose)
    fixed_leaf.label = f"{label} piano hinge fixed leaf (nominal section)"
    moving_leaf.location = origin.inverse() * hinge_pose
    catch_height = bottom + height - (REBATE_WIDTH - reveal) - MOUNT_HEIGHT / 2 if flap else bottom + height / 2
    catch = build_door_catch(p, label, start + width + reveal, catch_height)
    for hole in catch.door_holes:
        wood -= hole.moved(wood_pose.inverse())
    catch.keeper.location = origin.inverse()
    catch.fixings.location = origin.inverse()
    wood.label, wood.color = "Plywood door", DOOR_COLOR
    wood.location = origin.inverse() * wood_pose
    door = Compound(label=label, children=[wood, backing, catch.keeper, catch.fixings, Compound(label="Hinges", children=[moving_leaf])])
    door.location = origin * Location((0, 0, 0), (0, -angle, 0) if flap else (0, 0, angle))
    return DoorBuild(door, fixed_leaf, panel_rebate(p, start, bottom, width, height), catch)


def build_cabinet_doors(
    p: Parameters,
    bay_spans: tuple[tuple[float, float], tuple[float, float]],
    opening_heights: tuple[tuple[float, float], ...],
    rear_opening: tuple[float, float],
) -> CabinetDoors:
    gap, rebate = p.cabinet_door_gap_mm, REBATE_WIDTH
    start, end = bay_spans[1]
    doors, hinges, frame_cuts, mounts, catches = [], [], [], [], []
    for (parameter, label, flap), (bottom, top) in zip(DOOR_CONTROLS, opening_heights, strict=True):
        left = start - rebate + gap + (0 if flap else rebate)
        low = bottom - rebate + gap + (rebate if flap else 0)
        width = end - start + 2 * rebate - 2 * gap - (0 if flap else rebate)
        height = top - bottom + 2 * rebate - 2 * gap - (rebate if flap else 0)
        built = _hinged_door(p, label, left, low, width, height, getattr(p, parameter) * 0.9, flap=flap)
        doors.append(built.door)
        hinges.append(built.fixed)
        frame_cuts.extend([built.rebate, *built.catch.frame_cuts])
        mounts.append(built.catch.mount)
        catches.append(built.catch.body)
    doors.append(Compound(label="Fixed hardware", children=[Compound(label="Hinges", children=hinges),
                                                              Compound(label="Roller catch bodies", children=catches)]))

    start, end = bay_spans[0]
    bottom, top = rear_opening
    left, low = start - rebate + gap, bottom - rebate + gap
    width, height = end - start + 2 * (rebate - gap), top - bottom + 2 * (rebate - gap)
    cover = panel(width, p.cabinet_partition_thickness_mm, height)
    cover = fillet(cover.edges().filter_by(Axis.Y), p.cabinet_door_corner_radius_mm)
    cover.label, cover.color = "Cabinet 3 fixed cover", DOOR_COLOR
    face = cabinet_front(p)
    cover.location = Location((face + p.cabinet_partition_thickness_mm, left, low), (0, 0, 90))
    frame_cuts.append(panel_rebate(p, left, low, width, height))
    return CabinetDoors(Compound(label="Doors", children=[*doors, cover]), frame_cuts, mounts)


def cabinet_door_motions(p: Parameters) -> dict[str, object]:
    from campervan.cad.mirror import mirror_motion_tracks

    return {
        parameter: {
            "position": getattr(p, parameter),
            "tracks": mirror_motion_tracks([{
                "path": f"/Campervan/Cabinet/Lower module/Doors/{label}",
                "axis": "y" if flap else "z", "kind": "rotation", "travel": -90 if flap else 90,
            }]),
        }
        for parameter, label, flap in DOOR_CONTROLS
    }
