"""A few measured reference checks; Gert inspects shape and fit in the viewer."""

import pytest
from build123d import Compound, Plane, Vector

from campervan.cad.body import (
    body_section,
    body_space,
    ceiling_height,
    rear_aperture_sections,
    side_aperture,
    side_wall_depth,
    sliding_door,
    sliding_door_offset,
)
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_measured_vehicle_references():
    p = Parameters()
    vehicle = build_vehicle_references(p)
    groups = {group.label: group for group in vehicle.children}
    assert all(part.is_valid for part in vehicle.leaves)
    assert groups["Floor outline"].bounding_box().min.Y == pytest.approx(p.furniture_rear_gap_mm)
    roof = {part.label: part for part in groups["Roof"].children}
    for corner in groups["Rear corners"].children:
        assert corner.solids() and corner.volume > 0
    assert all(face.normal_at().Z < 0 for face in roof["Bare roof"].faces())
    envelope = body_space(p)
    depth = side_wall_depth(p)
    for wall, arch in zip(groups["Side walls"].children, groups["Wheel arches"].children, strict=True):
        window = next(part for part in wall.children if part.label == "Rear window")
        metal, glass = window.children
        assert metal.volume > 0
        assert (metal & envelope).volume < 1e-4  # Reveals extend outward, never into the cabin.
        assert (glass & envelope).area < 1e-4
        assert metal.distance_to(glass) < 1e-4
        panel = next(part for part in wall.children if part.label == "Side panel")
        assert panel.solids() and panel.volume > 0
        assert (panel & envelope).volume < 1e-4
        assert panel.distance_to(metal) < 1e-4
        sign = -1 if wall.label.startswith("Left") else 1
        base = 0 if sign == -1 else p.cargo_width_mm
        for x in (base, base + sign * depth):
            assert Compound(panel.faces()).distance_to(Vector(x, 500, 390)) < 1e-4
        rear_pillar = next(part for part in wall.children if part.label == "Rear pillar")
        assert (rear_pillar & arch).volume < 1e-4
        assert rear_pillar.distance_to(arch) < 1e-5
        section = rear_pillar.intersect(Plane(origin=(0, 0, 490)))
        assert Compound(section).bounding_box().size.Y == pytest.approx(180)
        upper_section = rear_pillar.intersect(Plane(origin=(0, 0, 900)))
        assert 100 < Compound(upper_section).bounding_box().size.Y < 120
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
    # Door sides and header must meet the body along their entire shared boundary.
    body_rear = Compound([*groups["Rear corners"].faces(), *roof["Bare roof"].faces()])
    for section in rear_aperture_sections(p, closed=True)[:6]:
        for edge in section.edges():
            for t in (0, 0.25, 0.5, 0.75, 1):
                point = edge.position_at(t)
                assert body_rear.distance_to(point) < 1e-4
                assert Compound(hatch.faces()).distance_to(point) < 1e-4
    assert Compound(hatch.faces()).distance_to(Vector(centre, p.furniture_rear_gap_mm - 130, 390)) < 0.01
    hatch_metal, hatch_glass = hatch.children
    assert len(hatch_metal.solids()) == 1
    assert hatch_glass.bounding_box().size.Z == pytest.approx(p.rear_hatch_window_height_mm)
    assert hatch_metal.distance_to(hatch_glass) < 1e-4
    front = p.body_length_mm - p.left_door_front_offset_mm
    assert front == pytest.approx(1890)
    side = side_aperture(p, front)
    assert side.distance_to(Vector(-1, 1210, 490)) < 1e-5
    assert side.distance_to(Vector(-1, 1890 - 760, 1110)) < 1e-5
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
    for arch in (left, right):
        bounds = arch.bounding_box()
        assert (bounds.min.Y, bounds.max.Y) == pytest.approx((310, 1070))
    assert front - p.side_opening_width_mm - 1070 == pytest.approx(140)
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
            point.X += sign * (depth + p.side_door_standoff_mm + p.side_door_thickness_mm)
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
        point.X += sign * depth
        assert Compound(closed_door.faces()).distance_to(point) < 1e-5
        point.X -= sign * p.side_door_thickness_mm
        assert Compound(closed_door.faces()).distance_to(point) < 1e-5
        waist = Compound(closed_door.intersect(Plane(origin=(0, 0, 490)))).bounding_box()
        assert (waist.min.X, waist.max.X) == pytest.approx((1460, 1560) if right else (-60, 40))
        assert waist.size.X == pytest.approx(p.side_door_thickness_mm)
