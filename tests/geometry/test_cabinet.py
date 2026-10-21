"""Small carcass fit check; Gert inspects the cabinet layout in the viewer."""

from itertools import combinations

import pytest
from build123d import Edge, GeomType, Location, Plane

from campervan.cad.body import ceiling_height, interior_limits
from campervan.cad.bom import cut_list
from campervan.cad.cabinet import build_cabinet, cabinet_back_profile
from campervan.cad.cabinet_doors import cabinet_aisle_x, cabinet_door_motions
from campervan.cad.panels import panel
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_cabinet_follows_body_and_ceiling_without_part_or_arch_collisions():
    p = Parameters()
    cabinet = build_cabinet(p)
    parts = list(cabinet.children)
    aisle = next(part for part in parts if part.label == "Aisle frame")
    assert aisle.bounding_box().max.Z == pytest.approx(
        ceiling_height(p, cabinet_aisle_x(p), p.ceiling_ply_thickness_mm), abs=1e-5
    )
    rear_panel = next(part for part in parts if part.label == "Rear upper panel")
    assert rear_panel.bounding_box().min.Z == pytest.approx(p.cabinet_rear_storage_height_mm, abs=1e-5)
    assert rear_panel.bounding_box().min.Y == pytest.approx(0, abs=1e-5)
    assert rear_panel.bounding_box().size.Y == pytest.approx(p.cabinet_frame_thickness_mm, abs=1e-5)
    wall_supports = next(part for part in parts if part.label == "Wall supports")
    rear_upright = next(part for part in wall_supports.children if part.label == "Rear upright")
    wall_rails = [part for part in wall_supports.children if part.label.endswith("rail")]
    assert rear_upright.bounding_box().min.Z == pytest.approx(0, abs=1e-5)
    assert all(rail.distance_to(rear_upright) < 1e-5 for rail in wall_rails if rail.label.startswith("Rear"))
    middle = next(part for part in parts if part.label == "Middle panel")
    end = next(part for part in parts if part.label == "Cab-end panel")
    rail_blocks = next(part for part in parts if part.label == "Rail joint blocks")
    for rail in wall_rails:
        for end_name, vertical in (
            ("rear", rear_upright if rail.label.startswith("Rear") else middle),
            ("fore", middle if rail.label.startswith("Rear") else end),
        ):
            block = next(piece for piece in rail_blocks.children if piece.label == f"{rail.label} {end_name} block")
            assert block.distance_to(rail) < 1e-5
            assert block.distance_to(vertical) < 1e-5
            assert tuple(block.located(Location()).bounding_box().size) == pytest.approx((18, 18, p.member_width_mm))
    assert len(rail_blocks.children) == 2 * len(wall_rails)
    for rail in wall_rails:
        assert rail.distance_to(middle) < 1e-5
        if rail.label.startswith("Cab-end"):
            assert rail.distance_to(end) < 1e-5
        assert all(edge.geom_type == GeomType.LINE for edge in rail.edges())
    assert not any("skin" in part.label.lower() for part in cabinet.descendants)
    for name in ("Middle panel", "Cab-end panel"):
        partition = next(part for part in parts if part.label == name)
        assert partition.bounding_box().size.Y == pytest.approx(p.cabinet_frame_thickness_mm)
    # Door leaves retain stock coordinates below hinge-centred parents.
    leaves = [leaf.located(leaf.global_location) for leaf in cabinet.descendants if not leaf.children]
    assert all(part.is_valid and len(part.solids()) == 1 for part in leaves)
    backing = next(part for part in parts if part.label == "Back lining")
    assert backing.bounding_box().min.Y == pytest.approx(
        p.rear_corner_radius_mm + p.cabinet_back_clearance_mm - p.furniture_rear_gap_mm, abs=1e-5
    )
    assert backing.bounding_box().max.Y == pytest.approx(p.cabinet_length_mm)
    outer = cabinet_back_profile(p, p.cabinet_back_clearance_mm)
    inner = cabinet_back_profile(p, p.cabinet_back_clearance_mm + p.cabinet_back_thickness_mm)
    assert outer.distance_to(inner) == pytest.approx(p.cabinet_back_thickness_mm, abs=1e-4)
    cuts = cut_list(cabinet, p)
    back_cut = next(cut for cut in cuts if cut.material == "cabinet-back")
    assert back_cut.thickness == 3
    assert back_cut.length > backing.bounding_box().size.Z  # Developed length, not curved bounding-box height.
    shelves = next(part for part in parts if part.label == "Shelves")
    assert len(shelves.children) == 5
    assert "Rear lower" not in [shelf.label for shelf in shelves.children]
    assert all(shelf.bounding_box().size.Z == pytest.approx(p.cabinet_shelf_thickness_mm) for shelf in shelves.children)
    height = ceiling_height(p, p.cargo_width_mm, p.ceiling_ply_thickness_mm + p.cabinet_ceiling_gap_mm)
    rail_heights = (
        p.cabinet_lower_rail_top_mm,
        p.cabinet_rear_storage_height_mm + p.member_width_mm,
        (p.cabinet_frame_step_height_mm + height) / 2,
    )
    all_rails = (p.cabinet_rear_storage_height_mm + p.member_width_mm, rail_heights[-1], *rail_heights)
    assert [shelf.bounding_box().max.Z for shelf in shelves.children] == pytest.approx(
        [z - p.member_width_mm + p.cabinet_ledge_height_mm + p.cabinet_shelf_thickness_mm for z in all_rails]
    )
    ledges = next(part for part in parts if part.label == "Shelf ledges")
    assert len(ledges.children) == 20
    blocks = next(part for part in parts if part.label == "Latch strike blocks")
    assert len(blocks.children) == 4
    assert len([cut for cut in cuts if cut.material == "cabinet-catches"]) == 10
    assert [ledge.bounding_box().min.Z for ledge in ledges.children] == pytest.approx(
        [z - p.member_width_mm for z in all_rails for _ in range(4)]
    )
    for shelf in shelves.children:
        supports = [ledge for ledge in ledges.children if ledge.label.lower().startswith(shelf.label.lower())]
        assert len(supports) == 4
        if shelf.label.startswith("Rear"):
            assert shelf.distance_to(rear_panel) < 1e-5
        for support in supports:
            assert support.distance_to(shelf) < 1e-5, support.label
            if support.label.endswith("wall ledge"):
                assert min(support.distance_to(rail) for rail in wall_rails) < 1e-5, support.label
    frame_cuts = [cut for cut in cuts if cut.material == "cabinet-frames"]
    assert len(frame_cuts) == 4 + len(wall_supports.children)
    assert all(cut.thickness == 12 for cut in frame_cuts)
    assert not any(cut.material in {"skins", "unassigned"} for cut in cuts)
    cleats = next(part for part in parts if part.label == "Corner cleats")
    assert len(cleats.children) == 2
    rail_block_cuts = [cut for cut in cuts if "Rail joint blocks" in cut.path]
    assert len(rail_block_cuts) == len(rail_blocks.children)
    assert all(cut.material == "ledges" and cut.length == p.member_width_mm for cut in rail_block_cuts)
    for piece in [*ledges.children, *cleats.children, *blocks.children, *rail_blocks.children]:
        dimensions = sorted(piece.located(Location()).bounding_box().size)
        assert dimensions[0] <= p.cabinet_ledge_height_mm + 1e-5, piece.label
        assert dimensions[1] <= p.cabinet_ledge_size_mm + 1e-5, piece.label
    for cleat in cleats.children:
        partition = next(part for part in parts if part.label == cleat.label.split()[0] + " panel")
        frame = (
            next(part for part in parts if part.label == "Aisle frame")
            if "aisle" in cleat.label
            else next(rail for rail in wall_rails if rail.label == "Cab-end lower rail")
        )
        assert cleat.distance_to(partition) < 1e-5
        assert cleat.distance_to(frame) < 1e-5
    door_cuts = [cut for cut in cuts if cut.material == "cabinet-doors"]
    assert len(door_cuts) == 10
    assert all(cut.thickness == 9 for cut in door_cuts)
    doors = next(part for part in parts if part.label == "Doors")
    assert len(doors.children) == 10
    door_panels = [door.children[0].located(door.children[0].global_location) for door in doors.children]
    assert min(door.bounding_box().min.X for door in door_panels) == pytest.approx(p.bed_width_mm)
    assert max(door.bounding_box().max.X for door in door_panels) == pytest.approx(
        p.bed_width_mm + p.cabinet_door_thickness_mm
    )
    assert "Rear bay aisle skin" not in [part.label for part in parts]
    aisle = next(part for part in parts if part.label == "Aisle frame")
    assert min(aisle.distance_to(door) for door in door_panels) == pytest.approx(p.cabinet_door_gap_mm)
    upper = [door for door in doors.children if "upper" in door.label and not door.label.startswith("Rear storage")]
    assert len(upper) == 4
    assert sorted(round(door.bounding_box().size.Z) for door in upper) == [184, 184, 224, 224]
    for door in doors.children:
        opened = door.moved(Location())
        angle = -90 if door.label.startswith("Rear storage") and door.label.endswith("fore") else 90
        opened.location = Location(
            door.location.position,
            (0, -90, 0) if "upper" in door.label and not door.label.startswith("Rear storage") else (0, 0, angle),
        )
        assert opened.bounding_box().min.X < p.bed_width_mm  # Opens into the aisle.
        if "upper" in door.label and not door.label.startswith("Rear storage"):
            opened_panel = opened.children[0].located(opened.location * opened.children[0].location)
            assert opened_panel.bounding_box().size.Z == pytest.approx(p.cabinet_door_thickness_mm)
            assert opened_panel.bounding_box().max.Z < door.bounding_box().min.Z  # Drops below its bottom hinge.
        for fixed in parts:
            if fixed.label != "Doors":
                assert (opened & fixed).volume < 1e-4, (door.label, fixed.label)
    tracks = cabinet_door_motions(p)["cabinet_upper_doors_open_percent"]["tracks"]
    assert len(tracks) == 4
    assert all(track["travel"] == 90 and track["axis"] == "y" for track in tracks)  # Mirrored rotation.
    assert tuple(cabinet.bounding_box().min) == pytest.approx((1068.5, 0, 0), abs=1e-5)  # Estimated flange thickness.
    assert cabinet.bounding_box().max.Y == pytest.approx(p.cabinet_length_mm)
    body, ceiling = interior_limits(p, p.cabinet_ceiling_gap_mm)
    to_furniture = Location((0, -p.furniture_rear_gap_mm, 0))
    reflection = Location((p.cargo_width_mm, -p.furniture_rear_gap_mm, 0))
    body, ceiling = body.mirror(Plane.YZ).moved(reflection), ceiling.mirror(Plane.YZ).moved(reflection)
    placed = cabinet.moved(Location((0, p.furniture_rear_gap_mm, 0)))
    assert placed.bounding_box().min.Y == pytest.approx(p.furniture_rear_gap_mm)
    assert placed.bounding_box().max.Y == pytest.approx(p.furniture_rear_gap_mm + p.cabinet_length_mm)
    assert placed.bounding_box().max.Y <= (p.body_length_mm - p.left_door_front_offset_mm - p.side_opening_width_mm)
    middle = next(part for part in parts if part.label == "Middle panel")
    arch_left = (p.cargo_width_mm + p.arch_gap_mm) / 2
    beam_bottom = p.platform_height_mm - p.slat_thickness_mm - p.member_width_mm
    bounds = middle.bounding_box()
    assert "Rear frame" not in [part.label for part in parts]
    rear_inside = 0
    assert bounds.min.Y - rear_inside == pytest.approx(p.cabinet_rear_bay_length_mm)
    # Sweep the full loading envelope from the rear aperture into the storage bay.
    storage = panel(
        230, p.furniture_rear_gap_mm + p.cabinet_rear_bay_length_mm, p.cabinet_rear_storage_height_mm
    ).moved(Location((p.bed_width_mm + 50 + 3, -p.furniture_rear_gap_mm, 0)))
    for part in parts:
        assert (storage & part).volume < 1e-4, part.label
    upright = Edge.make_line(
        (arch_left - 3 - p.member_width_mm / 2, bounds.center().Y, 0),
        (arch_left - 3 - p.member_width_mm / 2, bounds.center().Y, beam_bottom),
    )
    assert sum(edge.length for edge in (middle & upright).edges()) == pytest.approx(upright.length)
    forward = next(shelf for shelf in shelves.children if shelf.label == "Cab-end middle")
    assert forward.bounding_box().size.Y == pytest.approx(
        p.cabinet_length_mm - p.cabinet_rear_bay_length_mm - 2 * p.cabinet_frame_thickness_mm
    )
    # Nothing hangs below the shared beam underside anywhere over the arch.
    below_beam = panel(p.cargo_width_mm - arch_left, p.arch_length_mm, beam_bottom).moved(
        Location((arch_left, p.arch_rear_offset_mm - p.furniture_rear_gap_mm, 0))
    )
    assert (wall_supports & below_beam).volume < 1e-4
    for part in parts:
        assert (part - body).volume < 1e-4, part.label
        if part not in (backing, aisle):  # Lining and door frame meet the ply; other parts retain their fitting gap.
            assert (part - ceiling).volume < 1e-4, part.label
        if part.label.endswith("frame"):
            allowed = (GeomType.LINE, GeomType.CIRCLE)
            for edge in part.edges():
                if edge.geom_type not in allowed:
                    # The rear roof/body loft trims the new top rail before it
                    # meets the ply. These short curves must stay above the old rail.
                    assert edge.geom_type in (GeomType.BSPLINE, GeomType.BEZIER)
                    assert edge.bounding_box().min.Z >= height - 1e-5
            corners = [
                edge
                for edge in part.edges()
                if edge.geom_type == GeomType.CIRCLE and abs(edge.radius - p.inside_radius_mm) < 1e-5
            ]
            assert corners
            assert part.located(Location()).bounding_box().size.Y == pytest.approx(p.cabinet_frame_thickness_mm)
            assert part.bounding_box().max.Z == pytest.approx(
                ceiling_height(p, cabinet_aisle_x(p), p.ceiling_ply_thickness_mm)
            )
    # The aisle frame follows and touches the plywood underside across its thickness.
    panel_x = cabinet_aisle_x(p)
    assert cabinet.bounding_box().max.Z == pytest.approx(
        ceiling_height(p, panel_x, p.ceiling_ply_thickness_mm), abs=0.01
    )
    # Flat end-panel stock is scribed into a narrower outline at its upper edge.
    end = next(part for part in parts if part.label == "Cab-end panel")
    assert end.bounding_box().max.X < p.cargo_width_mm  # Scribed around the sliding-door pillar.
    vehicle = build_vehicle_references(p)
    arch = vehicle.children[1].children[1].moved(to_furniture)
    roof = next(group for group in vehicle.children if group.label == "Roof")
    wall = next(group for group in vehicle.children if group.label == "Side walls").children[1]
    pillar = next(part for part in wall.children if part.label == "Rear pillar").moved(to_furniture)
    assert backing.distance_to(pillar) == pytest.approx(p.cabinet_back_clearance_mm, abs=1e-4)
    rail = next(group for group in roof.children if group.label == "Side rails").children[1].moved(to_furniture)
    assert backing.distance_to(rail) >= p.cabinet_back_clearance_mm - 1e-4
    assert backing.distance_to(arch) >= 2.99
    ply = next(part for part in roof.children if part.label == "Finished ceiling").moved(to_furniture)
    assert backing.distance_to(ply) < 1e-4
    assert aisle.distance_to(ply) < 1e-4
    for part in parts:
        overlap = part & ply
        assert overlap is None or overlap.volume < 1e-4, part.label
    rear_pillar = (
        next(group for group in vehicle.children if group.label == "Rear corners").children[1].moved(to_furniture)
    )
    assert (storage & rear_pillar).volume < 1e-4
    assert (storage & arch).volume < 1e-4
    for a, b in [*combinations(leaves, 2), *((part, arch) for part in leaves)]:
        overlap = a & b
        assert overlap is None or overlap.volume < 1e-4, (a.label, b.label)
