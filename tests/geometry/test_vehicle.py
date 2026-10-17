"""Basic envelope checks; measured fit and appearance are inspected in the viewer."""

import pytest
from build123d import Align, Box, Face, Location, Vector

from campervan.cad.body import ceiling_height, rear_aperture
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_vehicle_envelope_and_openings():
    for p in (Parameters(), Parameters(body_length_mm=2000, body_upper_width_mm=1300)):
        vehicle = build_vehicle_references(p)
        groups = {group.label: group for group in vehicle.children}
        assert all(part.is_valid for part in vehicle.leaves)
        assert tuple(groups["Floor outline"].bounding_box().size) == pytest.approx((1500, 1860, 0))
        assert groups["Floor outline"].bounding_box().min.Y == pytest.approx(p.furniture_rear_gap_mm)
        assert tuple(vehicle.bounding_box().size) == pytest.approx(
            (1500, p.body_length_mm + p.cab_length_mm, p.body_height_mm)
        )
        floor, seats, headliner = groups["Cab"].children
        roof_z = ceiling_height(p, p.cargo_width_mm / 2, p.ceiling_ply_thickness_mm)
        roof_front = p.body_length_mm + p.cab_length_mm - p.cab_headliner_front_setback_mm
        assert headliner.distance_to(Vector(p.cargo_width_mm / 2, roof_front, roof_z)) < 1e-5
        assert floor.bounding_box().min.Y == pytest.approx(p.body_length_mm)
        assert floor.bounding_box().min.Z == pytest.approx(0)
        assert floor.bounding_box().max.Z == pytest.approx(0)
        driver, passenger = seats.children
        assert driver.bounding_box().min.X > passenger.bounding_box().max.X
        for seat in seats.children:
            cushion = next(part for part in seat.children if part.label == "Cushion")
            assert cushion.bounding_box().max.Z == pytest.approx(p.cab_seat_height_mm + p.cab_seat_front_rise_mm)
            assert tuple(cushion.bounding_box().size)[:2] == pytest.approx((p.cab_seat_width_mm, p.cab_seat_depth_mm))
            back = next(part for part in seat.children if part.label == "Integrated backrest and headrest")
            assert len(back.solids()) == 1
            assert seat.bounding_box().min.Z == pytest.approx(0)
            # The upper backrest can overhang the mattress in plan view. Check
            # actual mattress clearance rather than the whole seat's Y bounds.
            if p.body_length_mm == 1900:
                mattress = Box(
                    p.bed_width_mm,
                    p.cargo_length_mm,
                    p.foam_thickness_mm,
                    align=(Align.MIN, Align.MIN, Align.MIN),
                ).moved(
                    Location((p.cargo_width_mm - p.bed_width_mm - 7, p.furniture_rear_gap_mm, p.platform_height_mm))
                )
                assert 0 < seat.distance_to(mattress) < 20
            assert seat.distance_to(headliner) > 0
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
