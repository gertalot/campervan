"""A few measured reference checks; Gert inspects shape and fit in the viewer."""

import pytest
from build123d import Compound, Vector

from campervan.cad.body import body_section, ceiling_height, side_aperture, sliding_door, sliding_door_offset
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_measured_vehicle_references():
    p = Parameters()
    vehicle = build_vehicle_references(p)
    groups = {group.label: group for group in vehicle.children}
    assert all(part.is_valid for part in vehicle.leaves)
    assert groups["Floor outline"].bounding_box().min.Y == pytest.approx(p.furniture_rear_gap_mm)
    roof = {part.label: part for part in groups["Roof"].children}
    for corner, sign in zip(groups["Rear corners"].children, (1, -1), strict=True):
        assert all(face.normal_at().X * sign > 0 for face in corner.faces())
    assert all(face.normal_at().Z < 0 for face in roof["Bare roof"].faces())
    for wall in groups["Side walls"].children:
        pillar = next(part for part in wall.children if part.label == "Front pillar")
        assert len(pillar.solids()) == 1 and pillar.volume > 0
        assert pillar.bounding_box().max.Y == pytest.approx(p.body_length_mm)
    ply = roof["Finished ceiling"]
    bounds = ply.bounding_box()
    assert (bounds.min.Y, bounds.max.Y) == pytest.approx((240, 1660))
    centre = p.cargo_width_mm / 2
    edge = centre - p.body_upper_width_mm / 2
    assert ceiling_height(p, centre, p.ceiling_ply_thickness_mm) == pytest.approx(1290)
    assert ceiling_height(p, edge, p.ceiling_ply_thickness_mm) == pytest.approx(1270, abs=0.01)
    for bow in roof["Roof bows"].children:
        assert bow.distance_to(ply) < 1e-5
    opening = groups["Rear opening"].children[1]
    assert opening.distance_to(Vector((1500 - 1265) / 2, 0, 390)) < 1e-5
    assert opening.bounding_box().min.Y == pytest.approx(-120, abs=0.1)
    assert opening.bounding_box().max.Z == pytest.approx(1280)
    hatch = groups["Rear opening"].children[2]
    assert hatch.distance_to(Vector(centre, p.furniture_rear_gap_mm - 130, 390)) < 0.01
    side = side_aperture(p, 1840)
    assert side.distance_to(Vector(-1, 1840 - 740, 490)) < 1e-5
    assert side.distance_to(Vector(-1, 1840 - 820, 900)) < 1e-5
    assert side.bounding_box().max.Z == pytest.approx(1170)
    floor = {part.label: part for part in groups["Body floor"].children}
    assert floor["Finished floor plywood"].bounding_box().max.Z == pytest.approx(0)
    assert floor["Vehicle floor"].bounding_box().max.Z == pytest.approx(-18)
    plywood = floor["Finished floor plywood"]
    assert plywood.bounding_box().min.Y == pytest.approx(0)
    assert plywood.distance_to(Vector(centre, 0, 0)) < 1e-5
    rear_inset = (p.cargo_width_mm - p.rear_opening_floor_width_mm) / 2
    for x in (rear_inset - 10, p.cargo_width_mm - rear_inset + 10):
        assert plywood.distance_to(Vector(x, p.rear_corner_straight_mm / 2, 0)) == pytest.approx(10)
    arch_depth = (p.cargo_width_mm - p.arch_gap_mm) / 2
    for x in (arch_depth / 2, p.cargo_width_mm - arch_depth / 2):
        assert plywood.distance_to(Vector(x, p.arch_rear_offset_mm + p.arch_length_mm / 2, 0)) > 1
    cab = {part.label: part for part in groups["Cab"].children}
    assert cab["Headliner"].bounding_box().min.Y == pytest.approx(1660)
    left, right = groups["Wheel arches"].children
    assert right.bounding_box().min.X - left.bounding_box().max.X == pytest.approx(p.arch_gap_mm)
    # Both open doors retain the exact wall curvature, including the upper taper.
    section = body_section(p, 0)
    for door, edge, sign, offset in zip(
        groups["Sliding doors"].children,
        (section[1], section[4]),
        (-1, 1),
        (p.left_door_front_offset_mm, p.right_door_front_offset_mm),
        strict=True,
    ):
        surface = Compound(door.faces())
        y = p.body_length_mm - offset - p.side_door_clear_width_mm - 30
        for t in (0.3, 0.5):
            point = edge.position_at(t)
            point.X += sign * (p.side_door_standoff_mm + p.side_door_thickness_mm)
            point.Y = y
            assert surface.distance_to(point) < 1e-5
        right = sign == 1
        closed = p.model_copy(update={"doors_close_percent": 100})
        closed_door = sliding_door(closed, p.body_length_mm - offset, right)
        assert closed_door.is_valid
        assert sliding_door_offset(p, 100, right) == (0, 0)
        assert sliding_door_offset(p, 85, right)[0] == sliding_door_offset(p, 0, right)[0]
        point = edge.position_at(0.5)
        point.Y = p.body_length_mm - offset - 30
        assert Compound(closed_door.faces()).distance_to(point) < 1e-5
