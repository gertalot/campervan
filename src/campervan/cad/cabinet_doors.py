"""Overlay plywood doors, rotating about face-mounted hinges in the closing gap."""

from build123d import Align, Axis, Color, Compound, Cylinder, GeomType, Location, fillet

from campervan.cad.panels import panel
from campervan.parameters import Parameters

FINGER_HOLE_DIAMETER = 30.0


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
    latch: bool = False,
) -> Compound:
    if min(width, height) <= 2 * p.cabinet_door_corner_radius_mm or (latch and min(width, height) <= 80):
        raise ValueError("Door opening must leave room for its rounded corners and a 30mm finger hole.")
    door = panel(width, p.cabinet_door_thickness_mm, height)
    door = fillet(door.edges().filter_by(Axis.Y), p.cabinet_door_corner_radius_mm)
    door = fillet(door.edges().filter_by(Axis.Y, reverse=True), p.cabinet_door_edge_radius_mm)
    children = []
    if latch:
        centre = (
            width / 2 if upper else (35 if reverse else width - 35),
            0,
            height - p.cabinet_door_overlap_mm - 40,
        )
        thickness = p.cabinet_door_thickness_mm
        bore = Cylinder(
            FINGER_HOLE_DIAMETER / 2, thickness + 2,
            rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((centre[0], thickness + 1, centre[2])))
        door -= bore
        hole_edges = [
            edge for edge in door.edges().filter_by(GeomType.CIRCLE)
            if abs(edge.radius - FINGER_HOLE_DIAMETER / 2) < 1e-6
        ]
        door = fillet(hole_edges, p.cabinet_door_edge_radius_mm)
        # Nominal keeper only: confirm the purchased catch before drilling fixings.
        keeper = panel(12, 30, 12).moved(Location((centre[0] - 6, -30, height - p.cabinet_door_overlap_mm - 16)))
        keeper.label, keeper.color = "Roller catch keeper (estimated envelope)", Color(0.35, 0.38, 0.40)
        children.append(keeper)
    door.label, door.color = "Plywood door", Color(0.84, 0.72, 0.49)
    pose = Location((-p.cabinet_door_gap_mm / 2, -width if reverse else 0, 0)) * Location((0, 0, 0), (0, 0, 90))
    children = [door, *children]
    for child in children:
        child.location = pose * child.location
    hinged = Compound(label=label, children=children)
    pivot_x = p.bed_width_mm + p.cabinet_door_thickness_mm + p.cabinet_door_gap_mm / 2
    hinged.location = Location((pivot_x, start, bottom), (0, -angle, 0) if upper else (0, 0, angle))
    return hinged


def cabinet_door_hardware(p: Parameters, doors: Compound) -> tuple[Compound, Compound]:
    """Fixed catch envelopes and mounting blocks, independent of door opening pose."""
    catches, timber = [], []
    section, depth = p.cabinet_ledge_size_mm, p.cabinet_ledge_height_mm
    for door in doors.children:
        keeper = door.children[1].located(Location(door.location.position) * door.children[1].location)
        y = keeper.bounding_box().center().Y
        opening_top = keeper.bounding_box().max.Z + 4
        # The roller body meets the keeper behind the door; mounting block is
        # glued to the inside of the frame. Both envelopes need a physical fit-up.
        catch = panel(25, 32, 16)
        catch.location = Location((cabinet_aisle_x(p) + p.cabinet_frame_thickness_mm, y - 16, opening_top - 16))
        catch.label, catch.color = f"{door.label} roller body (estimated envelope)", Color(0.35, 0.38, 0.40)
        catches.append(catch)
        if door.label.endswith("upper 2") or door.label in {"Rear storage aft", "Rear storage fore"}:
            block = panel(section, 50, depth)
            block.location = Location((cabinet_aisle_x(p) + p.cabinet_frame_thickness_mm, y - 25, opening_top))
            block.label = f"{door.label} catch mounting block"
            timber.append(block)
    for part in timber:
        part.color = Color(0.88, 0.61, 0.25)
    return Compound(label="Roller catch bodies", children=catches), Compound(label="Catch timber", children=timber)


def cabinet_aisle_x(p: Parameters) -> float:
    """Aisle frame's front face, behind the closed door and its hinge gap."""
    return p.bed_width_mm + p.cabinet_door_thickness_mm + p.cabinet_door_gap_mm


def build_cabinet_doors(
    p: Parameters,
    bay_spans: tuple[tuple[float, float], tuple[float, float]],
    opening_heights: list[tuple[float, float]],
    rear_openings: list[tuple[float, float]],
) -> Compound:
    overlap, corner, edge = p.cabinet_door_overlap_mm, p.cabinet_door_corner_radius_mm, p.cabinet_door_edge_radius_mm
    if overlap * 2 + p.cabinet_door_gap_mm >= p.member_width_mm:
        raise ValueError("Door overlaps must leave a gap across the frame's cross-beams.")
    if edge * 2 >= p.cabinet_door_thickness_mm or edge >= corner or overlap <= edge:
        raise ValueError("Door roundovers must fit the plywood thickness, corner radius and overlap.")
    # The fixed and moving hinge leaves sit face-to-face in the closing gap.
    doors = []
    for bay_name, (start, end) in zip(("Rear", "Cab-end"), bay_spans, strict=True):
        openings = rear_openings if bay_name == "Rear" else opening_heights
        for i, (bottom, top) in enumerate(openings):
            upper = i >= len(openings) - 2
            if bay_name == "Rear" and i == 0:
                left, right = start - overlap, end + overlap
                width = (right - left - p.cabinet_door_gap_mm) / 2
                height = top - bottom + 2 * overlap
                for name, hinge, reverse, sign in (("Aft", left, False, 1), ("Fore", right, True, -1)):
                    angle = getattr(p, f"cabinet_storage_{name.lower()}_open_percent") * 90 / 100
                    doors.append(
                        _hinged_door(
                            p,
                            f"Rear storage {name.lower()}",
                            hinge,
                            bottom - overlap,
                            width,
                            height,
                            sign * angle,
                            reverse=reverse,
                            latch=True,
                        )
                    )
                continue
            number = i - (len(openings) - 2) + 1 if upper else i + 1
            label = f"{bay_name} {'upper' if upper else 'lower'} {number}"
            if bay_name == "Rear" and i == 1:
                label = "Rear storage upper flap"
            width, height = end - start + 2 * overlap, top - bottom + 2 * overlap
            if min(width, height) <= 2 * corner:
                raise ValueError("Cabinet doors must leave room for their rounded corners.")
            position = (
                getattr(p, f"cabinet_{'rear' if bay_name == 'Rear' else 'cab_end'}_upper_{number}_open_percent")
                if upper
                else p.cabinet_storage_upper_doors_open_percent
                if bay_name == "Rear"
                else p.cabinet_lower_doors_open_percent
                if i == 0
                else p.cabinet_front_upper_door_open_percent
            )
            angle = 90 * position / 100
            doors.append(
                _hinged_door(
                    p, label, start - overlap, bottom - overlap, width, height, angle, upper=upper or i == 1, latch=True
                )
            )
    return Compound(label="Doors", children=doors)


def cabinet_door_motions(p: Parameters) -> dict[str, object]:
    """Use the same hinge origins and rotations as the CAD assembly."""
    from campervan.cad.mirror import mirror_motion_tracks

    return {
        name: {
            "position": getattr(p, name),
            "tracks": mirror_motion_tracks(
                [
                    {"path": f"/Campervan/Cabinet/Doors/{label}", "axis": axis, "kind": "rotation", "travel": travel}
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
