"""Split storage leaves have separate live controls and clear the made-up bed."""

import pytest

from campervan.cad.cabinet_doors import build_cabinet_doors, cabinet_door_motions, cabinet_door_strikes
from campervan.parameters import Parameters


def test_split_storage_and_front_access_clear_mattress_with_independent_live_hinges():
    p = Parameters(platform_height_mm=390)
    rail = p.cabinet_lower_rail_top_mm
    assert rail == 530
    bays = ((60, 626), (686, 940))
    openings = [(60, rail - 60), (rail, 730), (790, 944), (1004, 1198)]
    doors = build_cabinet_doors(p, bays, openings, openings)
    assert len(doors.children) == 10
    assert all(len(door.children) == 2 for door in doors.children)
    pair = [door for door in doors.children if door.label.startswith("Rear storage")]
    assert len(pair) == 4
    for door in pair:
        plywood = door.children[0]
        assert plywood.bounding_box().size.Y == pytest.approx(297)
        assert plywood.bounding_box().size.Z == pytest.approx(230 if "upper" in door.label else 440)
        latch = door.children[1].located(door.children[1].global_location)
        assert latch.bounding_box().max.X == pytest.approx(p.bed_width_mm + 50)
        overlap = door.children[0] & door.children[1]
        assert overlap is None or overlap.volume < 1e-5
    motions = cabinet_door_motions(p)
    lower = motions["cabinet_storage_doors_open_percent"]["tracks"]
    upper = motions["cabinet_storage_upper_doors_open_percent"]["tracks"]
    assert sorted(track["travel"] for track in lower) == [-90, 90]
    assert sorted(track["travel"] for track in upper) == [-90, 90]
    assert {track["path"] for track in lower}.isdisjoint(track["path"] for track in upper)
    posed = Parameters(
        platform_height_mm=390,
        cabinet_storage_upper_doors_open_percent=100,
        cabinet_front_upper_door_open_percent=100,
    )
    opened = build_cabinet_doors(posed, bays, openings, openings)
    for closed, door in zip(doors.children, opened.children, strict=True):
        accessible = "storage upper" in door.label or door.label == "Cab-end lower 2"
        if accessible:
            assert door.bounding_box().min.X < p.bed_width_mm - 250
            assert door.bounding_box().min.Z >= p.platform_height_mm + p.foam_thickness_mm + 10
        else:
            assert door.location == closed.location
    closed_strikes, blocks = cabinet_door_strikes(p, doors)
    opened_strikes, _ = cabinet_door_strikes(posed, opened)
    assert len(closed_strikes.children) == 10 and len(blocks.children) == 4
    assert opened_strikes.bounding_box().min == closed_strikes.bounding_box().min
