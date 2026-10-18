"""Small carcass fit check; Gert inspects the cabinet layout in the viewer."""

from itertools import combinations

import pytest
from build123d import Edge, GeomType, Location

from campervan.cad.body import ceiling_height, interior_limits
from campervan.cad.cabinet import build_cabinet
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_cabinet_follows_body_and_ceiling_without_part_or_arch_collisions():
    p = Parameters()
    cabinet = build_cabinet(p)
    parts = list(cabinet.children)
    leaves = [leaf for leaf in cabinet.descendants if not leaf.children]
    assert all(part.is_valid and len(part.solids()) == 1 for part in leaves)
    shelves = next(part for part in parts if part.label == "Shelves")
    assert len(shelves.children) == 6
    assert all(shelf.bounding_box().size.Z == pytest.approx(p.cabinet_shelf_thickness_mm) for shelf in shelves.children)
    height = ceiling_height(p, p.cargo_width_mm, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
    rail_heights = (
        p.platform_height_mm - p.slat_thickness_mm,
        p.cabinet_frame_step_height_mm,
        (p.cabinet_frame_step_height_mm + height) / 2,
    )
    assert [shelf.bounding_box().max.Z for shelf in shelves.children] == pytest.approx(
        [z - p.member_width_mm + p.cabinet_ledge_size_mm + p.cabinet_shelf_thickness_mm for z in rail_heights] * 2
    )
    ledges = next(part for part in parts if part.label == "Shelf ledges")
    assert len(ledges.children) == 18
    assert [ledge.bounding_box().min.Z for ledge in ledges.children] == pytest.approx(
        [z - p.member_width_mm for z in rail_heights for _ in range(3)] * 2
    )
    assert tuple(cabinet.bounding_box().min) == pytest.approx((1070, 0, 0), abs=1e-5)
    assert cabinet.bounding_box().max.Y == pytest.approx(p.cabinet_length_mm)
    body, ceiling = interior_limits(p, p.cabinet_ceiling_gap_mm)
    to_furniture = Location((0, -p.furniture_rear_gap_mm, 0))
    body, ceiling = body.moved(to_furniture), ceiling.moved(to_furniture)
    placed = cabinet.moved(Location((0, p.furniture_rear_gap_mm, 0)))
    assert placed.bounding_box().min.Y == pytest.approx(p.furniture_rear_gap_mm)
    assert placed.bounding_box().max.Y == pytest.approx(p.furniture_rear_gap_mm + p.cabinet_length_mm)
    assert placed.bounding_box().max.Y == pytest.approx(
        p.body_length_mm - p.left_door_front_offset_mm - p.side_opening_width_mm
    )
    middle = next(part for part in parts if part.label == "Middle frame")
    arch_left = (p.cargo_width_mm + p.arch_gap_mm) / 2
    beam_bottom = p.platform_height_mm - p.slat_thickness_mm - p.member_width_mm
    bounds = middle.bounding_box()
    assert bounds.center().Y == pytest.approx(p.cabinet_length_mm / 2)
    upright = Edge.make_line(
        (arch_left - 3 - p.member_width_mm / 2, bounds.center().Y, 0),
        (arch_left - 3 - p.member_width_mm / 2, bounds.center().Y, beam_bottom),
    )
    assert sum(edge.length for edge in (middle & upright).edges()) == pytest.approx(upright.length)
    # The outer end stops at the beam underside, with no dangling wall-side upright.
    wall_side = Edge.make_line(
        (bounds.max.X - p.member_width_mm / 2, bounds.center().Y, 0),
        (bounds.max.X - p.member_width_mm / 2, bounds.center().Y, beam_bottom - 0.01),
    )
    assert not (middle & wall_side).edges()
    for part in parts:
        assert (part - body).volume < 1e-4, part.label
        assert (part - ceiling).volume < 1e-4, part.label
        if part.label.endswith("frame"):
            assert all(edge.geom_type in (GeomType.LINE, GeomType.CIRCLE) for edge in part.edges()), part.label
            corners = [edge for edge in part.edges() if edge.geom_type == GeomType.CIRCLE]
            assert corners and all(edge.radius == pytest.approx(p.inside_radius_mm) for edge in corners)
            assert part.bounding_box().max.Z == pytest.approx(
                ceiling_height(p, p.cargo_width_mm, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
            )
            bounds = part.bounding_box()
            for z in (
                p.member_width_mm / 2,
                p.platform_height_mm - p.slat_thickness_mm - p.member_width_mm / 2,
                p.cabinet_frame_step_height_mm - p.member_width_mm / 2,
            ):
                if (
                    part.label != "Aisle frame"
                    and bounds.min.Y < p.arch_rear_offset_mm - p.furniture_rear_gap_mm + p.arch_length_mm
                    and bounds.max.Y > p.arch_rear_offset_mm - p.furniture_rear_gap_mm
                    and z < p.arch_height_mm
                ):
                    continue  # Its wall-side foot is cut away around the wheel arch.
                if part.label == "Aisle frame":
                    rail = Edge.make_line((bounds.center().X, bounds.min.Y, z), (bounds.center().X, bounds.max.Y, z))
                else:
                    rail = Edge.make_line((bounds.min.X, bounds.center().Y, z), (bounds.max.X, bounds.center().Y, z))
                assert sum(edge.length for edge in (part & rail).edges()) == pytest.approx(rail.length)
    # The skins follow the plywood underside; the straight frames sit below its shallow crown.
    skin_x = p.bed_width_mm + p.frame_thickness_mm
    assert cabinet.bounding_box().max.Z == pytest.approx(
        ceiling_height(p, skin_x, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm), abs=0.01
    )
    # Flat end-panel stock is scribed into a narrower outline at its upper edge.
    end = next(part for part in parts if part.label == "Cab-end skin")
    assert end.bounding_box().max.X < p.cargo_width_mm  # Scribed around the sliding-door pillar.
    vehicle = build_vehicle_references(p)
    arch = vehicle.children[1].children[1].moved(to_furniture)
    roof = next(group for group in vehicle.children if group.label == "Roof")
    ply = next(part for part in roof.children if part.label == "Finished ceiling").moved(to_furniture)
    for part in parts:
        overlap = part & ply
        assert overlap is None or overlap.volume < 1e-4, part.label
    for a, b in [*combinations(parts, 2), *((part, arch) for part in parts)]:
        overlap = a & b
        assert overlap is None or overlap.volume < 1e-4, (a.label, b.label)
