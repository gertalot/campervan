"""Vehicle fitting volumes and shelf/door datums for the panel-and-cleat cabinet."""

from dataclasses import dataclass

from build123d import Edge, Face, Location, Part, Plane, Side, Solid, Wire

from campervan.cad.body import body_section, ceiling_height, ceiling_space, interior_limits
from campervan.cad.panels import panel
from campervan.parameters import Parameters


def cabinet_back_profile(p: Parameters, inset: float) -> Wire:
    """One bend across the sheet height, bridging recesses and clearing projecting side posts.

    Construct against the actual left side, then reflect into furniture-local coordinates.
    The top meets the plywood underside. Recesses are bridged, not followed.
    """
    start = max(p.furniture_rear_gap_mm, p.rear_corner_radius_mm + p.cabinet_back_clearance_mm)
    end = p.furniture_rear_gap_mm + p.cabinet_length_mm
    front = p.body_length_mm - p.left_door_front_offset_mm
    rear_post = front - p.side_opening_width_mm
    intrusion = p.roof_rail_intrusion_mm
    if start < rear_post and end > rear_post - p.side_pillar_width_mm:
        intrusion = max(intrusion, p.side_pillar_intrusion_mm)
    if end > front - p.side_opening_radius_mm:
        intrusion = max(intrusion, p.front_pillar_intrusion_mm)
    lower, upper = body_section(p, 0)[:2]
    curve = Wire([Edge.make_line(lower.position_at(0), lower.position_at(1)), upper])
    curve = curve.moved(Location((intrusion, 0, 0))).offset_2d(inset, side=Side.RIGHT, closed=False)
    # Trim each face at the actual curved plywood underside.
    if curve.position_at(0).Z > curve.position_at(1).Z:
        curve = Wire([edge.reversed() for edge in reversed(Wire(curve.edges()).order_edges())])
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        point = curve.position_at(mid)
        if point.Z < ceiling_height(p, point.X, p.ceiling_ply_thickness_mm):
            lo = mid
        else:
            hi = mid
    return Wire(curve.trim(0, (lo + hi) / 2).edges()).mirror(Plane.YZ).moved(Location((p.cargo_width_mm, 0, 0)))


@dataclass
class CabinetLayout:
    front: float
    top: float
    first: float
    split: float
    upper: float
    frame_room: Part
    bays: tuple[tuple[float, float], tuple[float, float]]
    lower_back: float
    plywood_room: Part


def cabinet_layout(p: Parameters) -> CabinetLayout:
    w, t, skin = p.cabinet_frame_width_mm, p.cabinet_frame_thickness_mm, p.cabinet_partition_thickness_mm
    front = p.bed_width_mm + 6.0  # Reserve the visible hinge barrel inside the previous bed envelope.
    curve = cabinet_back_profile(p, p.cabinet_back_clearance_mm)
    # A square-topped frame fits below the lowest wall-side ceiling. Skins supply the scribed trim.
    skin_top = ceiling_height(p, front + t, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
    top = min(
        skin_top, ceiling_height(p, curve.position_at(1).X, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
    )
    first = p.platform_height_mm + p.foam_thickness_mm + p.cabinet_mattress_clearance_mm
    split = p.cabinet_rear_storage_height_mm + w
    upper = (split + top + w) / 2
    middle = p.cabinet_rear_bay_length_mm + skin / 2
    bays = ((w, middle - w / 2), (middle + w / 2, p.cabinet_length_mm - w))
    if min(end - start for start, end in bays) < 120 or not w < first < split - 2 * w < upper < top - w:
        raise ValueError("Cabinet bays and shelves must leave usable inset-door openings.")
    if first - w < p.arch_height_mm + 3:
        raise ValueError("Cabinet lower shelf rail must clear the wheel arch.")
    if w <= p.cabinet_shelf_thickness_mm + 12:
        raise ValueError("Cabinet timber must leave room for the shelf seats and module fixings.")
    body, ceiling = interior_limits(p, p.cabinet_ceiling_gap_mm)
    room = Part(
        ((body & ceiling).mirror(Plane.YZ).moved(Location((p.cargo_width_mm, -p.furniture_rear_gap_mm, 0)))).solids()
    )
    timber_room = Part(room.solids())
    # Plywood follows the actual side/pillars and finished ceiling, independently of timber planes.
    scribe_room = Part(
        (
            (body & ceiling_space(p, p.ceiling_ply_thickness_mm))
            .mirror(Plane.YZ)
            .moved(Location((p.cargo_width_mm, -p.furniture_rear_gap_mm, 0)))
        ).solids()
    )
    # The simpler inboard envelope below is for the timber only.
    curve_bottom, roof = curve.position_at(0), curve.position_at(1)
    section = Face(
        Wire(
            [
                *curve.edges(),
                Edge.make_line(roof, (p.cargo_width_mm + 10, 0, roof.Z)),
                Edge.make_line((p.cargo_width_mm + 10, 0, roof.Z), (p.cargo_width_mm + 10, 0, curve_bottom.Z)),
                Edge.make_line((p.cargo_width_mm + 10, 0, curve_bottom.Z), curve_bottom),
            ]
        )
    )
    room -= Solid.extrude(section, (0, p.cabinet_length_mm + 2, 0)).moved(Location((0, -1, 0)))
    arch = panel((p.cargo_width_mm - p.arch_gap_mm) / 2 + 6, p.arch_length_mm + 6, p.arch_height_mm + 3)
    arch.location = Location(
        ((p.cargo_width_mm + p.arch_gap_mm) / 2 - 3, p.arch_rear_offset_mm - p.furniture_rear_gap_mm - 3, 0)
    )
    # The plane is a fitting datum, not a solid back panel: its lower central
    # opening is bridged over the wheel arch. Check the actual timbers against
    # the arch below, without rejecting the whole plane for crossing that opening.
    vehicle_room = Part(room.solids())
    room -= arch
    scribe_room = Part((scribe_room - arch).solids())
    allowance = skin + 1.0

    def fits(back: float) -> bool:
        stock = panel(w + allowance, p.cabinet_length_mm, split).moved(Location((back - w, 0, 0)))
        return sum(solid.volume for solid in (stock - vehicle_room).solids()) < 0.01

    lo, hi = front + t + w + 230.0, p.cargo_width_mm
    if not fits(lo):
        raise ValueError("The rear jamb cannot retain 230mm chair-loading clearance.")
    for _ in range(16):
        mid = (lo + hi) / 2
        if fits(mid):
            lo = mid
        else:
            hi = mid
    lower_back = lo - 1.0
    return CabinetLayout(
        front,
        top,
        first,
        split,
        upper,
        # Cleats follow the supporting panels, not the old inboard back-frame plane.
        Part((timber_room - arch).solids()),
        bays,
        lower_back,
        scribe_room,
    )
