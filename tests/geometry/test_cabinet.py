"""Small carcass fit check; Gert inspects the cabinet layout in the viewer."""

from itertools import combinations

import pytest
from build123d import Edge, GeomType

from campervan.cad.body import ceiling_height, interior_limits
from campervan.cad.cabinet import build_cabinet
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_cabinet_follows_body_and_ceiling_without_part_or_arch_collisions():
    p = Parameters()
    cabinet = build_cabinet(p)
    parts = list(cabinet.children)
    assert len(parts) == 5 and all(part.is_valid and len(part.solids()) == 1 for part in parts)
    assert tuple(cabinet.bounding_box().min) == pytest.approx((1070, 0, 0), abs=1e-5)
    assert cabinet.bounding_box().max.Y == pytest.approx(p.cabinet_length_mm)
    body, ceiling = interior_limits(p, p.cabinet_ceiling_gap_mm)
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
    assert end.bounding_box().max.X == pytest.approx(p.cargo_width_mm)
    vehicle = build_vehicle_references(p)
    arch = vehicle.children[1].children[1]
    roof = next(group for group in vehicle.children if group.label == "Roof")
    ply = next(part for part in roof.children if part.label == "Finished ceiling")
    for part in parts:
        overlap = part & ply
        assert overlap is None or overlap.volume < 1e-4, part.label
    for a, b in [*combinations(parts, 2), *((part, arch) for part in parts)]:
        overlap = a & b
        assert overlap is None or overlap.volume < 1e-4, (a.label, b.label)
