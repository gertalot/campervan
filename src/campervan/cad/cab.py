"""Adjustable cab reference geometry; dimensions are estimates pending measurement."""

from build123d import (
    Bezier,
    Color,
    Compound,
    Edge,
    Face,
    Location,
    RectangleRounded,
    Shell,
    Solid,
    ThreePointArc,
    Wire,
)

from campervan.cad.body import ceiling_height
from campervan.parameters import Parameters


def build_seat(p: Parameters, name: str, x: float, offset: float, recline: float) -> Compound:
    """Local origin is the backrest pivot, at the rear of a forward-facing cushion."""
    width, depth, foam = p.cab_seat_width_mm, p.cab_seat_depth_mm, p.cab_seat_thickness_mm
    height, back_height = p.cab_seat_height_mm, p.cab_backrest_height_mm
    upholstery = Color(0.30, 0.34, 0.39, 0.32)

    # Cross-sections follow the older Japanese cushion outline. Keep the nose
    # raised without rotating a flat slab or changing the projected seat depth.
    cushion_sections = []
    for fraction, width_ratio, thickness_ratio in (
        (0, 0.82, 0.65),
        (0.12, 0.97, 0.95),
        (0.55, 1.0, 1.0),
        (0.88, 0.96, 0.95),
        (1, 0.84, 0.55),
    ):
        thickness = foam * thickness_ratio
        top = height + p.cab_seat_front_rise_mm * fraction
        section = RectangleRounded(width * width_ratio, thickness, thickness * 0.45).wire()
        section.location = Location((0, depth * fraction, top - thickness / 2), (90, 0, 0))
        cushion_sections.append(section)
    cushion = Solid.make_loft(cushion_sections)
    # Smooth lofts can bulge past their sections; preserve the specified envelope.
    cushion = cushion.scale((width / cushion.bounding_box().size.X, 1, 1))
    cushion.label, cushion.color = "Cushion", upholstery

    # One continuous upholstered highback: lumbar fullness, rounded shoulders,
    # then the narrower integrated head support. No separate pad or metal posts.
    back_sections = []
    head_height = p.cab_headrest_height_mm
    for z, width_ratio, thickness_ratio, forward in (
        (0, 0.80, 0.70, 0),
        (back_height * 0.18, 0.98, 1.10, foam * 0.12),
        (back_height * 0.58, 0.96, 1.0, 0),
        (back_height * 0.82, 0.84, 0.85, -foam * 0.04),
        (back_height, 0.51, 0.85, 0),
        (back_height + head_height * 0.70, 0.49, 0.85, foam * 0.07),
        (back_height + head_height, 0.40, 0.60, foam * 0.09),
    ):
        thickness = foam * thickness_ratio
        section = RectangleRounded(width * width_ratio, thickness, thickness * 0.45).wire()
        section.location = Location((0, forward, z))
        back_sections.append(section)
    back = Solid.make_loft(back_sections)
    back = back.scale((width / back.bounding_box().size.X, 1, 1))
    back.label, back.color = "Integrated backrest and headrest", upholstery
    back.location = Location((0, 0, height - 20), (recline, 0, 0))

    # Open side brackets under the cushion; dimensions are visual estimates.
    # The sloping upper rail follows the cushion underside, with two floor feet.
    supports = []
    rear_y, front_y = depth * 0.15, depth * 0.85
    rear_z = height - foam + p.cab_seat_front_rise_mm * 0.15
    front_z = height - foam + p.cab_seat_front_rise_mm * 0.85
    leg = min(45, depth * 0.12)
    rail = min(25, rear_z / 4)
    for side, support_x in (("Left", -width * 0.32), ("Right", width * 0.32)):
        outline = Wire.make_polygon(
            [
                (support_x - 12, rear_y, 0),
                (support_x - 12, rear_y, rear_z),
                (support_x - 12, front_y, front_z),
                (support_x - 12, front_y, 0),
                (support_x - 12, front_y - leg, 0),
                (support_x - 12, front_y - leg, front_z - rail),
                (support_x - 12, rear_y + leg, rear_z - rail),
                (support_x - 12, rear_y + leg, 0),
            ]
        )
        support = Solid.extrude(Face(outline), (24, 0, 0))
        support.label, support.color = f"{side} support", Color(0.25, 0.28, 0.31, 0.32)
        supports.append(support)
    base = Compound(label="Seat supports", children=supports)
    seat = Compound(label=name, children=[base, cushion, back])
    seat.location = Location((x, p.body_length_mm + offset, 0))
    return seat


def build_cab(p: Parameters) -> Compound:
    centre, rear = p.cargo_width_mm / 2, p.body_length_mm
    if p.cab_headliner_front_setback_mm >= p.cab_length_mm:
        raise ValueError("Cab length must exceed its headliner front setback.")
    if p.cab_seat_height_mm <= p.cab_seat_thickness_mm:
        raise ValueError("Cab seat height must leave room below its cushion.")

    # Owner-confirmed: cab and cargo share one level floor.
    front = rear + p.cab_length_mm
    floor = Face(
        Wire.make_polygon(
            [
                (0, rear, 0),
                (p.cargo_width_mm, rear, 0),
                (centre + p.cab_front_width_mm / 2, front, 0),
                (centre - p.cab_front_width_mm / 2, front, 0),
            ]
        )
    )
    floor.label, floor.color = "Floor", Color(0.45, 0.49, 0.52, 0.32)

    # Broad central headliner with rounded side returns. Any front drop happens
    # near the windscreen header, rather than across the driver's whole headroom.
    roof_end = rear + p.cab_length_mm - p.cab_headliner_front_setback_mm
    rear_height = ceiling_height(p, centre, p.ceiling_ply_thickness_mm)
    rear_edge = ceiling_height(p, centre - p.body_upper_width_mm / 2, p.ceiling_ply_thickness_mm)
    headliner_rear = p.ceiling_rear_y_mm + p.ceiling_length_mm
    profiles = []
    for y, width, z, crown in (
        (headliner_rear, p.body_upper_width_mm, rear_height, rear_height - rear_edge),
        (rear, p.body_upper_width_mm + 90, rear_height, 100),
        (
            rear + (roof_end - rear) * 0.65,
            p.body_upper_width_mm,
            rear_height,
            p.cab_headliner_crown_mm,
        ),
        (
            roof_end,
            p.cab_headliner_front_width_mm,
            rear_height - p.cab_headliner_front_drop_mm,
            p.cab_headliner_crown_mm,
        ),
    ):
        half = width / 2
        if crown == 0:
            left_edge = Edge.make_line((centre - half, y, z), (centre, y, z))
            right_edge = Edge.make_line((centre, y, z), (centre + half, y, z))
        elif y == headliner_rear:
            left = (centre - half, y, z - crown)
            middle = (centre, y, z)
            quarter_z = ceiling_height(p, centre - half / 2, p.ceiling_ply_thickness_mm)
            left_edge = ThreePointArc(left, (centre - half / 2, y, quarter_z), middle).edge()
            right_edge = ThreePointArc(middle, (centre + half / 2, y, quarter_z), (centre + half, y, z - crown)).edge()
        else:
            left_edge = Bezier(
                (centre - half, y, z - crown),
                (centre - half, y, z),
                (centre - half * 0.5, y, z),
                (centre, y, z),
            ).edge()
            right_edge = Bezier(
                (centre, y, z),
                (centre + half * 0.5, y, z),
                (centre + half, y, z),
                (centre + half, y, z - crown),
            ).edge()
        profiles.append(Wire([left_edge, right_edge]))
    headliner = Shell.make_loft(profiles, ruled=True)
    headliner.label, headliner.color = "Headliner", Color(0.66, 0.68, 0.66, 0.32)

    seats = Compound(
        label="Seats",
        children=[
            build_seat(
                p, "Driver seat", centre + p.cab_seat_spacing_mm / 2, p.cab_driver_offset_mm, p.cab_driver_recline_deg
            ),
            build_seat(
                p,
                "Passenger seat",
                centre - p.cab_seat_spacing_mm / 2,
                p.cab_passenger_offset_mm,
                p.cab_passenger_recline_deg,
            ),
        ],
    )
    return Compound(label="Cab", children=[floor, seats, headliner])
