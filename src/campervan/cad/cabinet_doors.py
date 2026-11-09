"""Inset 6mm doors with exposed hinges and through-face fastener envelopes."""

from dataclasses import dataclass

from build123d import Align, Axis, Color, Compound, Cylinder, Face, GeomType, Location, Part, Solid, Wire, fillet

from campervan.cad.panels import panel
from campervan.parameters import Parameters

METAL = Color(0.48, 0.50, 0.53)
FINGER_HOLE_DIAMETER = 30.0
HINGE_PROJECTION = 3.0


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


@dataclass
class CabinetDoors:
    assembly: Compound
    blocks: dict[str, list[Part]]
    shelf_clearances: list[Part]
    frame_holes: list[Part]


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
    face = p.bed_width_mm + 6
    reveal, thickness = p.cabinet_door_gap_mm, p.cabinet_door_thickness_mm
    if thickness + 1.2 + 0.5 + 2.4 + 1.5 > 12 or p.cabinet_frame_thickness_mm + 1.2 + 0.5 + 2.4 + 1.5 > 25:
        raise ValueError("Selected door/frame thickness needs longer hinge bolts than the modelled M3 × 12 / 25 sets.")
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
    moving, fixed, bolts = [], [], []
    clearances: list[Part] = []
    frame_holes: list[Part] = []
    centres = (start + 60, start + width - 60) if upper else (bottom + 60, bottom + height - 60)
    for number, centre in enumerate(centres, 1):
        sign = -1 if reverse else 1
        if upper:
            moving_leaf = panel(1.2, 35, 14).moved(Location((face - 1.2, centre - 17.5, pin_z)))
            fixed_leaf = panel(1.2, 35, 14).moved(Location((face - 1.2, centre - 17.5, pin_z - 14)))
            along = Location((pin_x, centre - 17.5, pin_z), (-90, 0, 0))
            hole_points = [(centre + delta, pin_z + 7) for delta in (-8, 8)]
            level = bottom - reveal
            clearances.append(
                panel(p.cabinet_frame_thickness_mm + 8, 37, 2 * p.cabinet_shelf_thickness_mm + 2).moved(
                    Location((face - 1, centre - 18.5, level - p.cabinet_shelf_thickness_mm - 1))
                )
            )
        else:
            moving_leaf = panel(1.2, 14, 35).moved(
                Location((face - 1.2, pin_y - (14 if reverse else 0), centre - 17.5))
            )
            fixed_leaf = panel(1.2, 14, 35).moved(Location((face - 1.2, pin_y - (0 if reverse else 14), centre - 17.5)))
            along = Location((pin_x, pin_y, centre - 17.5))
            hole_points = [(pin_y + sign * 7, centre + delta) for delta in (-8, 8)]
        for y, z in hole_points:
            bore = _cylinder_x(1.6, thickness + 4, face - 2, y, z)
            wood -= bore.moved(wood_pose.inverse())
            moving_leaf -= bore
            fixed_y, fixed_z = (y, pin_z - 7) if upper else (pin_y - sign * 7, z)
            fixed_leaf -= _cylinder_x(1.6, 4, face - 2, fixed_y, fixed_z)
            bolt = _bolt_x(
                12, thickness + 1.2, face - 1.2, y, z, f"Hinge {number} door bolt · M3 × 12 (estimated envelope)"
            )
            bolt.location = origin.inverse()
            bolts.append(bolt)
            fixed.append(
                _bolt_x(
                    25,
                    p.cabinet_frame_thickness_mm + 1.2,
                    face - 1.2,
                    fixed_y,
                    fixed_z,
                    f"{label} fixed hinge {number} frame bolt · M3 × 25 (estimated envelope)",
                )
            )
            frame_holes.append(_cylinder_x(1.6, p.cabinet_frame_thickness_mm + 2, face - 1, fixed_y, fixed_z))
        moving_solids = list(moving_leaf.solids())
        fixed_solids = list(fixed_leaf.solids())
        for offset, span, moving_half in ((0, 7, False), (7, 21, True), (28, 7, False)):
            barrel = Cylinder(2.7, span, align=(Align.CENTER, Align.CENTER, Align.MIN))
            barrel -= Cylinder(1.5, span, align=(Align.CENTER, Align.CENTER, Align.MIN))
            barrel = barrel.moved(along * Location((0, 0, offset)))
            (moving_solids if moving_half else fixed_solids).extend(barrel.solids())
        fixed_solids.extend(Cylinder(1.5, 35, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(along).solids())
        leaf = Part(moving_solids, label=f"Hinge {number} moving leaf (estimated 35mm envelope)", color=METAL)
        leaf.location = origin.inverse()
        moving.append(leaf)
        fixed.append(Part(fixed_solids, label=f"{label} fixed hinge {number} (estimated envelope)", color=METAL))
    keeper_y = start + (width - hole_x if reverse else hole_x)
    header_bottom = bottom + height + reveal
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
    wood.label, wood.color = "Plywood door", Color(0.84, 0.72, 0.49)
    wood.location = origin.inverse() * wood_pose
    door = Compound(
        label=label,
        children=[
            wood,
            keeper,
            Compound(label="Hinges", children=[*moving, *bolts]),
            Compound(label="Keeper fixings", children=keeper_bolts),
        ],
    )
    door.location = origin * Location((0, 0, 0), (0, -angle, 0) if upper else (0, 0, angle))
    return DoorBuild(door, fixed, block, clearances, frame_holes)


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
    for bay_name, (start, end) in zip(("Rear", "Cab-end"), bay_spans, strict=True):
        openings = rear_openings if bay_name == "Rear" else opening_heights
        for index, (bottom, top) in enumerate(openings):
            if bay_name == "Rear" and index == 0:
                width = (end - start - 3 * reveal) / 2
                specs = [
                    ("Rear storage aft", start + reveal, width, False, p.cabinet_storage_aft_open_percent * 0.9),
                    (
                        "Rear storage fore",
                        start + 2 * reveal + width,
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
                specs = [(label, start + reveal, end - start - 2 * reveal, False, position * 0.9)]
            for label, left, width, reverse, angle in specs:
                built = _hinged_door(
                    p,
                    label,
                    left,
                    bottom + reveal,
                    width,
                    top - bottom - 2 * reveal,
                    angle,
                    upper=index > 0,
                    reverse=reverse,
                )
                doors.append(built.door)
                module = cabinet_door_module(label)
                fixed[module].extend(built.fixed)
                blocks[module].append(built.block)
                clearances.extend(built.shelf_clearances)
                frame_holes.extend(built.frame_holes)
    for module, parts in fixed.items():
        doors.append(Compound(label=f"{module} fixed hardware", children=parts))
    return CabinetDoors(Compound(label="Doors", children=doors), blocks, clearances, frame_holes)


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
