"""Rebated 6mm doors with edge-mounted piano hinges and glued pine backing strips."""

from dataclasses import dataclass

from build123d import Align, Axis, Color, Compound, Cylinder, Face, GeomType, Location, Part, Solid, Wire, fillet

from campervan.cad.panels import panel
from campervan.cad.cabinet_piano import BACKING_SIZE, END_CLEARANCE, HINGE_PROJECTION, piano_leaves
from campervan.cad.cabinet_upper import rear_upper_post_y
from campervan.parameters import Parameters

METAL = Color(0.48, 0.50, 0.53)
DOOR_COLOR = Color(0.84, 0.72, 0.49)
REBATE_WIDTH = 10.0
FINGER_HOLE_DIAMETER = 30.0


def _cylinder_x(radius: float, length: float, x: float, y: float, z: float) -> Part:
    return Cylinder(radius, length, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((x, y, z), (0, 90, 0))
    )


@dataclass
class DoorBuild:
    door: Compound
    fixed: list[Part]
    block: Part
    shelf_clearances: list[Part]
    frame_holes: list[Part]
    rebates: list[Part]


@dataclass
class CabinetDoors:
    assembly: Compound
    blocks: dict[str, list[Part]]
    shelf_clearances: list[Part]
    frame_holes: list[Part]
    rebates: list[Part]


def panel_rebate(p: Parameters, start: float, bottom: float, width: float, height: float) -> Part:
    """Closed-panel pocket, with the same reveal on every framed edge."""
    gap = p.cabinet_door_gap_mm
    face = p.bed_width_mm + p.bed_inward_offset_mm + 6
    if p.cabinet_door_thickness_mm >= p.cabinet_frame_thickness_mm:
        raise ValueError("Cabinet panel rebates must leave timber behind the panels.")
    pocket = panel(width + 2 * gap, p.cabinet_door_thickness_mm, height + 2 * gap)
    pocket = fillet(pocket.edges().filter_by(Axis.Y), p.cabinet_door_corner_radius_mm + gap)
    return pocket.moved(Location((face + p.cabinet_door_thickness_mm, start - gap, bottom - gap), (0, 0, 90)))


def _bolt_x(length: float, grip: float, x: float, y: float, z: float, label: str) -> Part:
    shaft = _cylinder_x(1.5, length, x, y, z)
    head = _cylinder_x(2.7, 1.5, x - 1.5, y, z)
    washer = _cylinder_x(4, 0.5, x + grip, y, z) - _cylinder_x(1.6, 0.5, x + grip, y, z)
    nut = _cylinder_x(2.8, 2.4, x + grip + 0.5, y, z) - _cylinder_x(1.5, 2.4, x + grip + 0.5, y, z)
    return Part([*shaft.solids(), *head.solids(), *washer.solids(), *nut.solids()], label=label, color=METAL)


def _hinged_door(
    p: Parameters,
    label: str,
    start: float,
    bottom: float,
    width: float,
    height: float,
    angle: float,
    *,
    upper: bool = False,
    reverse: bool = False,
) -> DoorBuild:
    face = p.bed_width_mm + p.bed_inward_offset_mm + 6
    reveal, thickness = p.cabinet_door_gap_mm, p.cabinet_door_thickness_mm
    pin_x = face - HINGE_PROJECTION
    pin_y = start + width + reveal / 2 if reverse else start - reveal / 2
    pin_z = bottom - reveal / 2 if upper else bottom
    origin = Location((pin_x, start if upper else pin_y, pin_z))
    wood_pose = Location((face + thickness, start, bottom), (0, 0, 90))
    if reverse:
        wood_pose = Location((face, start + width, bottom), (0, 0, -90))
    corner, edge = p.cabinet_door_corner_radius_mm, p.cabinet_door_edge_radius_mm
    if min(width, height) < 85 or corner <= edge or 2 * edge >= thickness:
        raise ValueError("Inset doors need room for their finger holes, rounded corners and edge easing.")
    wood = panel(width, thickness, height)
    wood = fillet(wood.edges().filter_by(Axis.Y), corner)
    wood = fillet(wood.edges().filter_by(Axis.Y, reverse=True), edge)
    hole_x = width / 2 if upper else (35 if reverse else width - 35)
    hole_z = height - 35 if upper else height / 2
    hole = Cylinder(15, thickness + 2, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((hole_x, thickness + 1, hole_z))
    )
    wood -= hole
    circles = [e for e in wood.edges().filter_by(GeomType.CIRCLE) if abs(e.radius - 15) < 1e-6]
    wood = fillet(circles, edge)
    moving, fixed = [], []
    clearances: list[Part] = []
    frame_holes: list[Part] = []
    rebates = [panel_rebate(p, start, bottom, width, height)]
    hinge_length = (width if upper else height) - 2 * END_CLEARANCE
    if upper:
        hinge_pose = Location((pin_x, start + width - END_CLEARANCE, pin_z), (90, 0, 0))
        backing = panel(BACKING_SIZE, hinge_length, BACKING_SIZE).moved(
            Location((face + thickness, start + END_CLEARANCE, bottom)))
    else:
        hinge_pose = (Location((pin_x, pin_y, bottom + height - END_CLEARANCE), (180, 0, 0))
                      if reverse else Location((pin_x, pin_y, bottom + END_CLEARANCE)))
        backing_y = start + width - BACKING_SIZE if reverse else start
        backing = panel(BACKING_SIZE, BACKING_SIZE, hinge_length).moved(
            Location((face + thickness, backing_y, bottom + END_CLEARANCE)))
    backing.label, backing.color = "Pine hinge backing strip", Color(0.84, 0.64, 0.39)
    backing.location = origin.inverse() * backing.location
    fixed_leaf, moving_leaf = piano_leaves(hinge_length, reveal, hinge_pose)
    fixed_leaf.label = f"{label} piano hinge fixed leaf (nominal section)"
    moving_leaf.location = origin.inverse() * hinge_pose
    fixed.append(fixed_leaf)
    moving.append(moving_leaf)
    keeper_y = start + (width - hole_x if reverse else hole_x)
    header_bottom = bottom + height + reveal
    # The keeper passes through the rear bearing lip. Its local relief leaves the
    # rest of the rebate intact and the block screws in the rail's full-depth band.
    rebates.append(panel(p.cabinet_frame_thickness_mm - thickness + 1, 28, 21 - reveal + 0.5).moved(
        Location((face + thickness, keeper_y - 14, header_bottom - 21))
    ))
    block_x = face + p.cabinet_frame_thickness_mm
    # One square-cut block, grain along Y, fixed broad-face to the back of the front header.
    block = panel(40, 18, 40)
    block.label = f"{label} catch mounting block"
    block.location = (
        Location((block_x, keeper_y - 20, header_bottom))
        * Location((0, 0, 0), (0, 0, 90))
        * Location((0, 0, 0), (90, 0, 0))
    )
    block_pose = block.location
    block_shape = Part(block.solids())
    body_solids = []
    plate = panel(25, 32, 1).moved(Location((block_x, keeper_y - 16, header_bottom - 1)))
    for sign in (-1, 1):
        # Catch base screws enter the 18mm-thick block from below.
        sy = keeper_y + sign * 12
        bore = Cylinder(1.6, 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((block_x + 12.5, sy, header_bottom - 1.5))
        )
        plate -= bore
        pilot = Cylinder(1.15, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((block_x + 12.5, sy, header_bottom))
        )
        block_shape -= pilot
        screw = Cylinder(1.5, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((block_x + 12.5, sy, header_bottom - 1))
        )
        screw_head = Cylinder(2.7, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((block_x + 12.5, sy, header_bottom - 2.5))
        )
        body_solids.extend([*screw.solids(), *screw_head.solids()])
        # Two plain assembly screws attach the block through the 18mm front rail.
        sy = keeper_y + sign * 10
        frame_holes.append(_cylinder_x(1.9, p.cabinet_frame_thickness_mm + 2, face - 1, sy, header_bottom + 9))
        block_shape -= _cylinder_x(1.2, 24, block_x, sy, header_bottom + 9)
        fixing = Part(
            [
                *_cylinder_x(1.75, 40, face, sy, header_bottom + 9).solids(),
                *_cylinder_x(3.2, 1.5, face - 1.5, sy, header_bottom + 9).solids(),
            ],
            label=f"{label} block screw · 6g × 40 (estimated envelope)",
            color=METAL,
        )
        fixed.append(fixing)
        roller_y = keeper_y + sign * 7.5
        roller = Cylinder(3.5, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((block_x + 5, roller_y, header_bottom - 14))
        )
        pin = Cylinder(1.5, 13, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((block_x + 5, roller_y, header_bottom - 14))
        )
        body_solids.extend([*roller.solids(), *pin.solids()])
    body_solids.extend(plate.solids())
    fixed.append(Part(body_solids, label=f"{label} roller catch body (estimated envelope)", color=METAL))
    block = Part(block_shape.moved(block_pose.inverse()).solids(), label=block.label)
    block.location = block_pose

    door_back = face + thickness
    keeper_plate = panel(1.2, 24, 18).moved(Location((door_back, keeper_y - 12, header_bottom - 20)))
    tongue = Face(
        Wire.make_polygon(
            [
                (door_back + 1.2, keeper_y - 2, header_bottom - 9),
                (block_x + 5, keeper_y - 4, header_bottom - 9),
                (block_x + 9, keeper_y - 2, header_bottom - 9),
                (block_x + 9, keeper_y + 2, header_bottom - 9),
                (block_x + 5, keeper_y + 4, header_bottom - 9),
                (door_back + 1.2, keeper_y + 2, header_bottom - 9),
            ]
        )
    )
    keeper_tongue = Solid.extrude(tongue, (0, 0, 2))
    keeper_bolts = []
    for sign in (-1, 1):
        sy, sz = keeper_y + sign * 8, header_bottom - 11
        bore = _cylinder_x(1.6, thickness + 3, face - 1, sy, sz)
        wood -= bore.moved(wood_pose.inverse())
        keeper_plate -= bore
        bolt = _bolt_x(12, thickness + 1.2, face, sy, sz, "Keeper door bolt · M3 × 12 (estimated envelope)")
        bolt.location = origin.inverse()
        keeper_bolts.append(bolt)
    keeper = Part(
        [*keeper_plate.solids(), *keeper_tongue.solids()], label="Roller catch keeper (estimated envelope)", color=METAL
    )
    keeper.location = origin.inverse()
    wood.label, wood.color = "Plywood door", DOOR_COLOR
    wood.location = origin.inverse() * wood_pose
    door = Compound(
        label=label,
        children=[
            wood,
            backing,
            keeper,
            Compound(label="Hinges", children=moving),
            Compound(label="Keeper fixings", children=keeper_bolts),
        ],
    )
    door.location = origin * Location((0, 0, 0), (0, -angle, 0) if upper else (0, 0, angle))
    return DoorBuild(door, fixed, block, clearances, frame_holes, rebates)


def build_cabinet_doors(
    p: Parameters,
    bay_spans: tuple[tuple[float, float], tuple[float, float]],
    opening_heights: list[tuple[float, float]],
    rear_openings: list[tuple[float, float]],
) -> CabinetDoors:
    reveal = p.cabinet_door_gap_mm
    doors = []
    fixed: dict[str, list[Part]] = {name: [] for name in ("Lower module", "Upper module")}
    blocks: dict[str, list[Part]] = {name: [] for name in fixed}
    clearances: list[Part] = []
    frame_holes: list[Part] = []
    rebates: list[Part] = []
    for bay_name, (start, end) in zip(("Rear", "Cab-end"), bay_spans, strict=True):
        openings = rear_openings if bay_name == "Rear" else opening_heights
        for index, (bottom, top) in enumerate(openings):
            door_start = rear_upper_post_y(p) + p.cabinet_frame_width_mm if bay_name == "Rear" and index == 3 else start
            if bay_name == "Rear" and index == 0:
                width = (end - start + 2 * REBATE_WIDTH - 3 * reveal) / 2
                specs = [
                    ("Rear storage aft", start - REBATE_WIDTH + reveal, width, False,
                     p.cabinet_storage_aft_open_percent * 0.9),
                    (
                        "Rear storage fore",
                        start - REBATE_WIDTH + 2 * reveal + width,
                        width,
                        True,
                        -p.cabinet_storage_fore_open_percent * 0.9,
                    ),
                ]
            else:
                number = index - 1 if index >= 2 else index + 1
                label = f"{bay_name} {'upper' if index >= 2 else 'lower'} {number}"
                if bay_name == "Rear" and index == 1:
                    label = "Rear storage upper flap"
                position = (
                    getattr(p, f"cabinet_{'rear' if bay_name == 'Rear' else 'cab_end'}_upper_{number}_open_percent")
                    if index >= 2
                    else p.cabinet_storage_upper_doors_open_percent
                    if bay_name == "Rear"
                    else p.cabinet_lower_doors_open_percent
                    if index == 0
                    else p.cabinet_front_upper_door_open_percent
                )
                specs = [(label, door_start - REBATE_WIDTH + reveal,
                          end - door_start + 2 * REBATE_WIDTH - 2 * reveal, False, position * 0.9)]
            for label, left, width, reverse, angle in specs:
                door_bottom = bottom - REBATE_WIDTH + reveal
                door_height = top - bottom + 2 * REBATE_WIDTH - 2 * reveal
                # The hinge edge fits the original through-opening; only the other
                # three edges overlap their bearing rebates.
                if index > 0:
                    door_bottom += REBATE_WIDTH
                    door_height -= REBATE_WIDTH
                else:
                    if not reverse:
                        left += REBATE_WIDTH
                    width -= REBATE_WIDTH
                built = _hinged_door(
                    p, label, left, door_bottom, width, door_height, angle,
                    upper=index > 0, reverse=reverse,
                )
                doors.append(built.door)
                module = cabinet_door_module(label)
                fixed[module].extend(built.fixed)
                blocks[module].append(built.block)
                clearances.extend(built.shelf_clearances)
                frame_holes.extend(built.frame_holes)
                rebates.extend(built.rebates)
    for module, parts in fixed.items():
        doors.append(Compound(label=f"{module} fixed hardware", children=parts))
    return CabinetDoors(Compound(label="Doors", children=doors), blocks, clearances, frame_holes, rebates)


def cabinet_door_module(label: str) -> str:
    upper = {"Rear upper 1", "Rear upper 2", "Cab-end upper 1", "Cab-end upper 2", "Upper module fixed hardware"}
    return "Upper module" if label in upper else "Lower module"


def cabinet_door_motions(p: Parameters) -> dict[str, object]:
    """Use the same hinge origins and rotations as the CAD assembly."""
    from campervan.cad.mirror import mirror_motion_tracks

    return {
        name: {
            "position": getattr(p, name),
            "tracks": mirror_motion_tracks(
                [
                    {
                        "path": f"/Campervan/Cabinet/{cabinet_door_module(label)}/Doors/{label}",
                        "axis": axis,
                        "kind": "rotation",
                        "travel": travel,
                    }
                ]
            ),
        }
        for name, axis, travel, label in (
            ("cabinet_rear_upper_1_open_percent", "y", -90, "Rear upper 1"),
            ("cabinet_rear_upper_2_open_percent", "y", -90, "Rear upper 2"),
            ("cabinet_cab_end_upper_1_open_percent", "y", -90, "Cab-end upper 1"),
            ("cabinet_cab_end_upper_2_open_percent", "y", -90, "Cab-end upper 2"),
            ("cabinet_lower_doors_open_percent", "z", 90, "Cab-end lower 1"),
            ("cabinet_front_upper_door_open_percent", "y", -90, "Cab-end lower 2"),
            ("cabinet_storage_upper_doors_open_percent", "y", -90, "Rear storage upper flap"),
            ("cabinet_storage_aft_open_percent", "z", 90, "Rear storage aft"),
            ("cabinet_storage_fore_open_percent", "z", -90, "Rear storage fore"),
        )
    }
