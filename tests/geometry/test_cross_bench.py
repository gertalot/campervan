"""Fixed cross-bench supports, foot recess and directly supported slats."""

from itertools import combinations

import pytest

from campervan.cad.bench import build_long_bench
from campervan.cad.bom import cut_list
from campervan.cad.cross_bench import build_cross_bench
from campervan.cad.sliding_bed import build_bed_slats, long_bed_layout
from campervan.parameters import Parameters


def test_fixed_cross_bench_has_two_frames_aft_skin_and_direct_slats():
    p = Parameters(platform_height_mm=390)
    bench = build_cross_bench(p)
    fixed, cushions = bench.children
    assert cushions.label == "Cushions"
    wall, aisle, skin, slats = fixed.children
    assert [piece.label for piece in fixed.children] == ["Wall-side frame", "Aisle frame", "Rear skin", "Fixed slats"]
    assert len(slats.children) == 4
    assert all(part.is_valid and len(part.solids()) == 1 for part in bench.leaves)
    top = p.platform_height_mm - p.slat_thickness_mm
    for frame, x in ((wall, 150), (aisle, 852)):
        bounds = frame.bounding_box()
        assert tuple(bounds.min) == pytest.approx((x, 1284, 0))
        assert tuple(bounds.size) == pytest.approx((p.frame_thickness_mm, 576, top))
    drawer_support = next(
        part for part in build_long_bench(p).children[0].children if part.label == "Internal drawer-support frame"
    ).bounding_box()
    assert (wall.bounding_box().min.X, wall.bounding_box().max.X) == pytest.approx(
        (drawer_support.min.X, drawer_support.max.X)
    )
    assert skin.bounding_box().min.Y == pytest.approx(p.seat_length_mm)
    assert wall.bounding_box().min.Y == pytest.approx(skin.bounding_box().max.Y)
    assert aisle.bounding_box().min.Y == pytest.approx(skin.bounding_box().max.Y)
    assert (skin.bounding_box().min.X, skin.bounding_box().max.X) == pytest.approx((150, 870))
    assert skin.bounding_box().size.Z == pytest.approx(top)
    assert aisle.bounding_box().max.Y == pytest.approx(p.cargo_length_mm)
    bounds = slats.bounding_box()
    assert tuple(bounds.min) == pytest.approx((0, p.seat_length_mm, top))
    assert tuple(bounds.max) == pytest.approx((p.bed_width_mm, p.cargo_length_mm, p.platform_height_mm))
    for a, b in zip(slats.children, slats.children[1:], strict=False):
        assert b.bounding_box().min.Y - a.bounding_box().max.Y == pytest.approx(260 / 3)
    long_slats = build_bed_slats(p, long_bed_layout(p), moving=True).children
    junction_gap = slats.children[0].bounding_box().min.Y - long_slats[-1].bounding_box().max.Y
    assert junction_gap == pytest.approx(90)
    for slat in slats.children:
        bounds = slat.bounding_box()
        assert tuple(bounds.size) == pytest.approx((1070, p.slat_width_mm, p.slat_thickness_mm))
        # Both top rails lie directly under every slat, including the overhanging edge slats.
        for frame in (wall, aisle):
            support = frame.bounding_box()
            assert min(bounds.max.Y, support.max.Y) > max(bounds.min.Y, support.min.Y)
            assert bounds.min.X < support.min.X < support.max.X < bounds.max.X
    for a, b in combinations(fixed.leaves, 2):
        overlap = a & b
        assert overlap is None or overlap.volume < 1e-6
    cuts = cut_list(bench, p)
    assert {cut.material for cut in cuts} == {"frames", "skins", "slats"}
    assert len(cuts) == 7


def test_long_bench_control_does_not_move_cross_bench():
    p = Parameters(cross_bench_overhang_mm=25)
    day = build_cross_bench(p)
    night = build_cross_bench(p.model_copy(update={"bed_extension_percent": 100}))
    for a, b in zip(day.children[0].leaves, night.children[0].leaves, strict=True):
        assert a.location == b.location
        assert a.volume == pytest.approx(b.volume)
    assert day.children[1].children[0].location == night.children[1].children[0].location
    assert day.children[0].children[1].bounding_box().max.X == pytest.approx(p.bed_width_mm - 25)
