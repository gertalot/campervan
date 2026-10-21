"""Overlay plywood doors, rotating about face-mounted hinges in the closing gap."""

from build123d import Align, Axis, Color, Compound, Cylinder, Location, fillet

from campervan.cad.panels import panel
from campervan.parameters import Parameters

# Vanlifer LL016 section drawing: 50mm behind the front face, 27mm bore with
# 23.5mm flats, 32mm flange, catch station 35.5mm back and 20mm above the axis.
# Striker overall size and flange thickness are conservative visual estimates.
STRIKE_HEIGHT = 8.0


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
    if min(width, height) <= 2 * p.cabinet_door_corner_radius_mm or (latch and width <= 51):
        raise ValueError("Door opening must leave room for its rounded corners and the storage latch flange.")
    door = panel(width, p.cabinet_door_thickness_mm, height)
    door = fillet(door.edges().filter_by(Axis.Y), p.cabinet_door_corner_radius_mm)
    door = fillet(door.edges().filter_by(Axis.Y, reverse=True), p.cabinet_door_edge_radius_mm)
    children = []
    if latch:
        if not 5 <= p.cabinet_door_thickness_mm <= 25:
            raise ValueError("The Point storage-door latch requires 5–25mm door plywood.")
        centre = (
            width / 2 if upper else (35 if reverse else width - 35),
            0,
            height - p.cabinet_door_overlap_mm - 20 - STRIKE_HEIGHT,
        )
        thickness = p.cabinet_door_thickness_mm
        bore = Cylinder(13.5, thickness + 2, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN))
        bore = bore.moved(Location((0, thickness + 1, 0)))
        bore &= panel(23.5, thickness + 2, 27).moved(Location((-11.75, -1, -13.5)))
        door -= bore.moved(Location(centre))
        body = Cylinder(13.5, 50, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN))
        body = body.moved(Location((0, thickness, 0)))
        body &= panel(23.5, 50, 27).moved(Location((-11.75, thickness - 50, -13.5)))
        flange = Cylinder(16, 1.5, rotation=(-90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN))
        body += flange.moved(Location((0, thickness, 0)))
        body = body.moved(Location(centre))
        body.label, body.color = "Point latch (clearance envelope)", Color(0.35, 0.38, 0.40)
        children.append(body)
    door.label, door.color = "Plywood door", Color(0.84, 0.72, 0.49)
    pose = Location((-p.cabinet_door_gap_mm / 2, -width if reverse else 0, 0)) * Location((0, 0, 0), (0, 0, 90))
    children = [door, *children]
    for child in children:
        child.location = pose * child.location
    hinged = Compound(label=label, children=children)
    pivot_x = p.bed_width_mm + p.cabinet_door_thickness_mm + p.cabinet_door_gap_mm / 2
    hinged.location = Location((pivot_x, start, bottom), (0, -angle, 0) if upper else (0, 0, angle))
    return hinged


def cabinet_door_strikes(p: Parameters, doors: Compound) -> tuple[Compound, Compound]:
    """Use each closed leaf's bore centre to align estimated strikers and top-rail blocks."""
    strikes = []
    blocks = []
    for door in doors.children:
        # Keep the hinge translation and remove its opening rotation. Child
        # geometry then supplies the closed bore centre, even in an open build.
        latch = door.children[1].located(Location(door.location.position) * door.children[1].location)
        y = latch.bounding_box().center().Y
        # The 32mm flange sets the vertical envelope symmetrically about the bore.
        top = latch.bounding_box().center().Z + 20 + STRIKE_HEIGHT
        strike = panel(15, 70, STRIKE_HEIGHT)
        strike.location = Location((p.bed_width_mm + 35.5 - 7.5, y - 35, top - STRIKE_HEIGHT))
        strike.label, strike.color = f"{door.label} strike (estimated envelope)", Color(0.25, 0.27, 0.29)
        strikes.append(strike)
        if door.label.endswith("upper 2") or door.label in {"Rear storage aft", "Rear storage fore"}:
            block = panel(p.cabinet_ledge_size_mm, 70, p.cabinet_ledge_height_mm)
            block.location = Location(
                (
                    cabinet_aisle_x(p) + p.cabinet_frame_thickness_mm,
                    y - 35,
                    top,
                )
            )
            block.label, block.color = f"{door.label} strike block", Color(0.88, 0.61, 0.25)
            blocks.append(block)
    return Compound(label="Latch strikes", children=strikes), Compound(label="Latch strike blocks", children=blocks)


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
                position = p.cabinet_storage_doors_open_percent
                angle = position * 90 / 100
                for name, hinge, reverse, sign in (("Aft", left, False, 1), ("Fore", right, True, -1)):
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
                p.cabinet_upper_doors_open_percent
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

    motions: dict[str, object] = {
        name: {
            "position": getattr(p, name),
            "tracks": mirror_motion_tracks(
                [
                    {"path": f"/Campervan/Cabinet/Doors/{label}", "axis": axis, "kind": "rotation", "travel": travel}
                    for label in labels
                ]
            ),
        }
        for name, axis, travel, labels in (
            (
                "cabinet_upper_doors_open_percent",
                "y",
                -90,
                ("Rear upper 1", "Rear upper 2", "Cab-end upper 1", "Cab-end upper 2"),
            ),
            ("cabinet_lower_doors_open_percent", "z", 90, ("Cab-end lower 1",)),
            ("cabinet_front_upper_door_open_percent", "y", -90, ("Cab-end lower 2",)),
            ("cabinet_storage_upper_doors_open_percent", "y", -90, ("Rear storage upper flap",)),
        )
    }
    for field, tier in (("cabinet_storage_doors_open_percent", ""),):
        motions[field] = {
            "position": getattr(p, field),
            "tracks": mirror_motion_tracks(
                [
                    {
                        "path": f"/Campervan/Cabinet/Doors/Rear storage {tier}{name}",
                        "axis": "z",
                        "kind": "rotation",
                        "travel": angle,
                    }
                    for name, angle in (("aft", 90), ("fore", -90))
                ]
            ),
        }
    return motions
