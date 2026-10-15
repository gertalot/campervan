from math import pi

import pytest

from campervan.cad.model import build_campervan
from campervan.parameters import Parameters


def test_vehicle_references_have_named_parts_and_follow_dimensions():
    for p in (Parameters(), Parameters(cargo_width_mm=1600, cargo_length_mm=2000)):
        model = build_campervan(p)
        references = model.children[0]
        floor, arches, corners = references.children
        assert model.label == "Campervan" and references.label == "Vehicle references"
        assert [group.label for group in references.children] == ["Floor outline", "Wheel arches", "Rear corners"]
        assert [part.label for part in arches.children] == ["Left wheel arch", "Right wheel arch"]
        assert [part.label for part in corners.children] == ["Left rear corner", "Right rear corner"]
        assert len(references.leaves) == 5 and all(part.is_valid for part in references.leaves)
        size = floor.bounding_box().size
        assert (size.X, size.Y, size.Z) == pytest.approx((p.cargo_width_mm, p.cargo_length_mm, 0))
        left, right = arches.children
        intrusion = (p.cargo_width_mm - p.arch_gap_mm) / 2
        profile_area = p.arch_length_mm * p.arch_height_mm - 2 * p.arch_radius_mm**2 * (1 - pi / 4)
        for arch in (left, right):
            assert arch.volume == pytest.approx(intrusion * profile_area)
            assert arch.bounding_box().min.Y == pytest.approx(p.arch_rear_offset_mm)
            assert arch.bounding_box().max.Z == pytest.approx(p.arch_height_mm)
        assert right.bounding_box().min.X - left.bounding_box().max.X == pytest.approx(p.arch_gap_mm)
        for corner in corners.children:
            assert len(corner.solids()) == 0  # References are surfaces, not wall stock.
            assert corner.area == pytest.approx(pi / 2 * p.rear_corner_radius_mm * p.rear_corner_height_mm)
            assert corner.bounding_box().min.Z == pytest.approx(0, abs=1e-7)
            assert corner.bounding_box().max.Z == pytest.approx(p.rear_corner_height_mm)
