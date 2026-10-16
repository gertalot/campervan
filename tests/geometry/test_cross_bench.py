"""Small dimensional and intersection check; Gert inspects the construction visually."""

from math import pi

import pytest
from build123d import Compound, Location

from campervan.cad.bench import build_long_bench
from campervan.cad.cross_bed import cross_bed_layout
from campervan.cad.cross_bench import build_cross_bench
from campervan.parameters import Parameters


def test_cross_bench_frame_and_divider_fit():
    p = Parameters()
    bench = build_cross_bench(p)
    fixed, moving, lid = bench.children[:3]
    assert bench.label == "Cross bench" and fixed.label == "Fixed frame"
    assert "Wall-side skin" not in [part.label for part in fixed.children]
    assert len(fixed.leaves) == 12 and len(moving.leaves) == 10 and len(lid.leaves) == 4
    layout = cross_bed_layout(p)
    assert layout.slat_gap == pytest.approx(20 / 6)
    fixed_slats = next(group for group in fixed.children if group.label == "Fixed slats")
    assert len(fixed_slats.children) == 3 and len(moving.children[0].children) == 4
    for slat in [*fixed_slats.children, *moving.children[0].children, *lid.children[1:]]:
        assert slat.bounding_box().size.Y == pytest.approx(80)
    for lid_slat, fixed_slat in zip(lid.children[1:], fixed_slats.children, strict=True):
        lid_bounds = lid_slat.located(lid_slat.global_location).bounding_box()
        fixed_bounds = fixed_slat.located(fixed_slat.global_location).bounding_box()
        assert (lid_bounds.min.Y, lid_bounds.max.Y) == pytest.approx((fixed_bounds.min.Y, fixed_bounds.max.Y))
    assert all(part.is_valid and len(part.solids()) == 1 for part in bench.leaves)
    bounds = Compound(bench.children[:3]).bounding_box()
    assert tuple(bounds.min) == pytest.approx((2, 1280, 0))
    assert tuple(bounds.max) == pytest.approx((853, 1860, 400))
    assert tuple(lid.bounding_box().min) == pytest.approx((2, 1282, 370))
    assert tuple(lid.bounding_box().size) == pytest.approx((358, 576, 30))
    divider = next(part for part in fixed.children if part.label == "Toilet-storage divider")
    frame, skin = divider.children
    assert tuple(frame.bounding_box().min) == pytest.approx((352, 1287, 0))
    assert tuple(frame.bounding_box().size) == pytest.approx((18, 566, 370))
    opening_area = 446 * 250 - (4 - pi) * 25**2
    assert frame.volume == pytest.approx((566 * 370 - opening_area - 2 * 18 * 60) * 18)
    assert skin.volume == pytest.approx((566 * 370 - 2 * 18 * 60) * 7)
    for extension in (0, 100):
        posed = (
            bench
            if extension == 0
            else build_cross_bench(Parameters(bed_extension_percent=100, cross_lid_open_percent=100))
        )
        fixed, moving, lid = posed.children[:3]
        assert moving.bounding_box().max.X == pytest.approx(853 + 217 * extension / 100)
        if extension:
            assert lid.bounding_box().max.Z > 900
            long_bench = build_long_bench(Parameters(bed_extension_percent=100))
            assert long_bench.bounding_box().max.X == pytest.approx(moving.bounding_box().max.X)
            long_moving_slats = long_bench.children[1].children[0].children[0]
            junction_gap = moving.children[0].bounding_box().min.Y - long_moving_slats.bounding_box().max.Y
            assert junction_gap == pytest.approx(90)
        for a, b in ((moving, fixed), (lid, fixed), (lid, moving)):
            overlap = a & b
            assert overlap is None or overlap.volume < 1e-6, (extension, a.label, b.label)
        moving_slats = moving.children[0].located(moving.children[0].global_location)
        stops = next(group for group in moving.children if group.label == "Extension stops")
        for plate in stops.children:
            placed = plate.located(plate.global_location)
            assert tuple(placed.bounding_box().size) == pytest.approx((22, 100, 2))
            overlap = placed & moving_slats
            assert overlap is None or overlap.volume < 1e-6
            # A small move beyond either travel limit must hit the closed end of its guide pocket.
            past_stop = placed.moved(Location((0.5 if extension else -0.5, 0, 0)))
            contact = past_stop & fixed
            assert contact is not None and contact.volume > 1
