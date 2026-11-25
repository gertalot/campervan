"""Rebated aisle doors and fixed cover, with pine-backed piano hinges."""

from dataclasses import dataclass

from build123d import Align, Axis, Color, Compound, Cylinder, GeomType, Location, Part, Solid, fillet

from campervan.cad.cabinet_chains import CHAIN, EYE_HEIGHT, ChainLayout, build_chain
from campervan.cad.cabinet_catches import MOUNT_HEIGHT, DoorCatch, build_door_catch
from campervan.cad.cabinet_piano import BACKING_SIZE, END_CLEARANCE, HINGE_PROJECTION, piano_leaves
from campervan.cad.cabinet_layout import cabinet_front
from campervan.cad.cabinet_stays import PENN, STAY_SIDES, build_stay, stay_layout
from campervan.cad.panels import panel
from campervan.parameters import Parameters

DOOR_COLOR = Color(0.84, 0.72, 0.49)
REBATE_WIDTH = 10.0
FINGER_HOLE_DIAMETER = 30.0
# CAD and the live viewer use the same control names and assembly labels.
DOOR_CONTROLS = {
    "Lower module": (
        ("cabinet_lower_doors_open_percent", "Cab-end bottom door"),
        ("cabinet_front_middle_door_open_percent", "Cab-end middle flap"),
        ("cabinet_front_upper_door_open_percent", "Cab-end above-bed flap"),
    ),
    "Upper module": (
        ("cabinet_rear_upper_1_open_percent", "Box 6 flap"),
        ("cabinet_cab_end_upper_1_open_percent", "Box 4 flap"),
        ("cabinet_cab_end_upper_2_open_percent", "Box 5 flap"),
        ("cabinet_rear_upper_2_open_percent", "Box 7 flap"),
    ),
}


@dataclass
class DoorBuild:
    door: Compound
    fixed: Part
    rebate: Part
    catch: DoorCatch
    fixed_restraint: Compound
    restraint_bores: list[Solid]


@dataclass
class CabinetDoors:
    parts: list[Compound | Part]
    frame_cuts: list[Part | Solid]
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
    p: Parameters, label: str, start: float, bottom: float, width: float, height: float, percent: float,
) -> DoorBuild:
    face = cabinet_front(p)
    reveal, thickness = p.cabinet_door_gap_mm, p.cabinet_door_thickness_mm
    pin_x = face - HINGE_PROJECTION
    stay_side = STAY_SIDES.get(label)
    sign = -1 if stay_side else 1
    hinge_edge = bottom + height if stay_side else bottom
    pin_z = hinge_edge - sign * reveal / 2
    origin = Location((pin_x, start, pin_z))
    wood_pose = Location((face + thickness, start, bottom), (0, 0, 90))
    corner, edge = p.cabinet_door_corner_radius_mm, p.cabinet_door_edge_radius_mm
    if min(width, height) < 85 or corner <= edge or 2 * edge >= thickness:
        raise ValueError("Inset doors need room for their finger holes, rounded corners and edge easing.")
    wood = panel(width, thickness, height)
    wood = fillet(wood.edges().filter_by(Axis.Y), corner)
    wood = fillet(wood.edges().filter_by(Axis.Y, reverse=True), edge)
    hole_x = width / 2
    finger_offset = 45 if stay_side or label == "Box 4 flap" else 35
    hole_z = finger_offset if stay_side else height - finger_offset
    hole = Cylinder(FINGER_HOLE_DIAMETER / 2, thickness + 2, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((hole_x, thickness + 1, hole_z))
    )
    wood -= hole
    circles = [e for e in wood.edges().filter_by(GeomType.CIRCLE) if abs(e.radius - FINGER_HOLE_DIAMETER / 2) < 1e-6]
    wood = fillet(circles, edge)
    # The folded link passes the end of the backing as the door approaches horizontal.
    stay_clearance = max(END_CLEARANCE, REBATE_WIDTH - reveal + 12)
    left_clearance = stay_clearance if stay_side == 1 else END_CLEARANCE
    right_clearance = stay_clearance if stay_side == -1 else END_CLEARANCE
    hinge_length = width - left_clearance - right_clearance
    hinge_start = left_clearance if stay_side else width - right_clearance
    hinge_pose = Location((pin_x, start + hinge_start, pin_z), (sign * 90, 0, 0))
    backing = panel(BACKING_SIZE, hinge_length, BACKING_SIZE).moved(
        Location((face + thickness, start + left_clearance, hinge_edge - (BACKING_SIZE if stay_side else 0))))
    backing.label, backing.color = "Pine hinge backing strip", Color(0.84, 0.64, 0.39)
    backing.location = origin.inverse() * backing.location
    fixed_leaf, moving_leaf = piano_leaves(hinge_length, reveal, hinge_pose)
    fixed_leaf.label = f"{label} piano hinge fixed leaf (nominal section)"
    moving_leaf.location = origin.inverse() * hinge_pose
    overlap = REBATE_WIDTH - reveal
    if stay_side:
        outer_jamb = start + (width - overlap if stay_side > 0 else overlap)
        shelf_top = bottom + overlap
        catch_z = shelf_top + reveal + MOUNT_HEIGHT / 2
        catch_pose = Location((0, outer_jamb, catch_z), (0 if stay_side > 0 else 180, 0, 0))
        catch = build_door_catch(p, label, catch_pose, screw_inset=13.5)
    else:
        catch_z = bottom + height + reveal
        if label == "Box 4 flap":
            catch_z -= REBATE_WIDTH
        catch_pose = Location((0, start + hole_x, catch_z), (90, 0, 0))
        catch = build_door_catch(p, label, catch_pose, screw_inset=13.5 if label == "Box 4 flap" else 9)
    for hole in catch.door_holes:
        wood -= hole.moved(wood_pose.inverse())
    catch.keeper.location = origin.inverse() * catch.keeper.location
    catch.fixings.location = origin.inverse() * catch.fixings.location
    children = [backing, catch.keeper, catch.fixings, Compound(label="Hinges", children=[moving_leaf])]
    angle = percent * 0.9
    if stay_side:
        layout = stay_layout(thickness, p.cabinet_frame_thickness_mm)
        pose = layout.pose(percent)
        angle = pose.flap
        jamb = overlap if stay_side > 0 else width - overlap
        restraint, moving_stay, pad, bore = build_stay(label, layout, pose, jamb, stay_side, thickness)
        restraint_bores = [bore.moved(origin)]
        children.extend([moving_stay, pad])
    else:
        if height + reveal / 2 < EYE_HEIGHT + 12:
            raise ValueError(f"{label} is too short for the chain mounting holes.")
        chain = ChainLayout(thickness, p.cabinet_frame_thickness_mm)
        side = 1 if label == "Box 6 flap" else -1
        jamb = overlap if side > 0 else width - overlap
        restraint, moving_chain, frame_holes, door_holes = build_chain(chain, percent, jamb, label, side=side)
        restraint_bores = [hole.moved(origin) for hole in frame_holes]
        for bore in door_holes:
            wood -= bore.moved(wood_pose.inverse() * origin)
        children.append(moving_chain)
    wood.label, wood.color, wood.location = "Plywood door", DOOR_COLOR, origin.inverse() * wood_pose
    restraint.location = origin
    door = Compound(label=label, children=[wood, *children])
    door.location = origin * Location((0, 0, 0), (0, -sign * angle, 0))
    return DoorBuild(door, fixed_leaf, panel_rebate(p, start, bottom, width, height), catch, restraint, restraint_bores)


def build_cabinet_doors(
    p: Parameters, module: str, openings: tuple[tuple[float, float, float, float], ...],
    *, fixed_cover: tuple[float, float, float, float], cover_label: str,
    roof_clearance: Solid | None = None,
) -> CabinetDoors:
    """Frame openings are (start Y, end Y, sill Z, head Z) at the aisle face."""
    gap, rebate = p.cabinet_door_gap_mm, REBATE_WIDTH
    overlap = rebate - gap
    doors, hinges, frame_cuts, mounts, catches = [], [], [], [], []
    for (parameter, label), (start, end, bottom, top) in zip(DOOR_CONTROLS[module], openings, strict=True):
        left = start - overlap
        low = bottom - overlap if label in STAY_SIDES else bottom + gap
        width = end - start + 2 * overlap
        height = top - bottom + rebate - 2 * gap
        built = _hinged_door(p, label, left, low, width, height, getattr(p, parameter))
        doors.append(built.door)
        doors.append(built.fixed_restraint)
        hinges.append(built.fixed)
        frame_cuts.extend([built.rebate, *built.catch.frame_cuts, *built.restraint_bores])
        mounts.append(built.catch.mount)
        catches.append(built.catch.body)
    doors.append(Compound(label="Fixed hardware", children=[Compound(label="Hinges", children=hinges),
                                                              Compound(label="Roller catch bodies", children=catches)]))

    start, end, bottom, top = fixed_cover
    left = start - overlap
    low = bottom - overlap
    width = end - start + 2 * overlap
    high = top if roof_clearance is not None else top + overlap
    cover = panel(width, p.cabinet_door_thickness_mm, high - low)
    cover = fillet(cover.edges().filter_by(Axis.Y), p.cabinet_door_corner_radius_mm)
    pose = Location((cabinet_front(p) + p.cabinet_door_thickness_mm, left, low), (0, 0, 90))
    if roof_clearance is not None:
        cover = Part((cover & roof_clearance.moved(pose.inverse())).solids())
    cover.label, cover.color, cover.location = cover_label, DOOR_COLOR, pose
    # At an open top the same pocket runs out through the ends of the jambs.
    frame_cuts.append(panel_rebate(p, left, low, width, top + overlap - low))
    doors.append(cover)
    return CabinetDoors(doors, frame_cuts, mounts)


def cabinet_door_motions(p: Parameters) -> dict[str, object]:
    from campervan.cad.mirror import mirror_motion_tracks

    motions = {}
    for module, controls in DOOR_CONTROLS.items():
        for parameter, label in controls:
            root = f"/Campervan/Cabinet/{module}/Doors"
            stay_side = STAY_SIDES.get(label)
            door = f"{root}/{label}"
            if stay_side:
                layout = stay_layout(p.cabinet_door_thickness_mm, p.cabinet_frame_thickness_mm)
                positions = range(101)
                poses = [layout.pose(percent) for percent in positions]
                paths = (door, f"{root}/{label} {PENN}/Frame arm", f"{door}/{PENN}/Door arm")
                tracks = [
                    {"path": path, "axis": "y", "kind": "rotation",
                     "keyframes": [(percent, pose[index]) for percent, pose in zip(positions, poses, strict=True)]}
                    for index, path in enumerate(paths)
                ]
            else:
                chain = ChainLayout(p.cabinet_door_thickness_mm, p.cabinet_frame_thickness_mm)
                tracks = [{"path": door, "axis": "y", "kind": "rotation", "travel": -90}]
                positions = [*range(100), 99.5, 99.9, 99.99, 100]
                poses = [chain.angles(percent) for percent in positions]
                for index, path in enumerate((f"{root}/{label} {CHAIN}/Frame run", f"{door}/{CHAIN}/Door run")):
                    tracks.append({"path": path, "axis": "y", "kind": "rotation",
                                   "keyframes": [(pct, pose[index]) for pct, pose in zip(positions, poses, strict=True)]})
            motions[parameter] = {"position": getattr(p, parameter), "tracks": mirror_motion_tracks(tracks)}
    return motions
