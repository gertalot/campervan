"""Basic envelope checks; measured fit and appearance are inspected in the viewer."""

import pytest
from build123d import Face, Vector

from campervan.cad.body import rear_aperture
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_vehicle_envelope_and_openings():
    for p in (Parameters(), Parameters(body_length_mm=2000, body_upper_width_mm=1300)):
        vehicle = build_vehicle_references(p)
        groups = {group.label: group for group in vehicle.children}
        assert all(part.is_valid for part in vehicle.leaves)
        assert tuple(groups["Floor outline"].bounding_box().size) == pytest.approx((1500, 1860, 0))
        assert tuple(vehicle.bounding_box().size) == pytest.approx((1500, p.body_length_mm, p.body_height_mm))
        left, right = groups["Wheel arches"].children
        assert right.bounding_box().min.X - left.bounding_box().max.X == pytest.approx(p.arch_gap_mm)
        assert left.bounding_box().max.Z == pytest.approx(p.arch_height_mm)
        # The door openings are holes in the surfaces, not just lines drawn on walls.
        for wall, x, offset in zip(
            groups["Side walls"].children,
            (0, 1500),
            (p.left_door_front_offset_mm, p.right_door_front_offset_mm),
            strict=True,
        ):
            door_centre = Vector(x, p.body_length_mm - offset - p.side_opening_width_mm / 2, 500)
            assert wall.distance_to(door_centre) > 100
            assert wall.distance_to(Vector(x, 500, 500)) < 1e-6
        surround = groups["Rear opening"].children[0]
        overlap = surround & Face(rear_aperture(p))
        assert overlap is None or overlap.area < 1e-5
        assert surround.area > 0
        _, bows, ply = groups["Roof"].children
        assert len(bows.children) == 3 and len(ply.solids()) == 1
        for bow in bows.children:
            assert len(bow.solids()) == 1
            assert bow.distance_to(ply) < 1e-5
            overlap = bow & ply
            assert overlap is None or overlap.volume < 1e-4
        # The sheet has actual thickness, rather than being another roof reference face.
        centre = p.cargo_width_mm / 2
        underside = Vector(centre, 500, p.body_height_mm - p.roof_bow_depth_mm - p.ceiling_ply_thickness_mm)
        assert ply.distance_to(underside) < 1e-5
