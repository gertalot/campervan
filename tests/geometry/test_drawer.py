"""A direct dimensional and clearance check; appearance is inspected manually."""

import pytest
from build123d import Location

from campervan.cad.bench import build_long_bench
from campervan.parameters import Parameters


def test_rear_drawer_fit_and_travel():
    bench = build_long_bench(Parameters())
    frame, bed, drawer = bench.children[:3]
    tray, rails = drawer.children
    assert len(tray.children) == 5 and len(rails.leaves) == 6
    assert all(part.is_valid and len(part.solids()) == 1 for part in drawer.leaves)
    bounds = tray.bounding_box()
    assert tuple(bounds.min) == pytest.approx((187, 0, 10))
    assert tuple(bounds.size) == pytest.approx((376, 1250, 290))
    for distance in (0, 1215):
        moved = tray.moved(Location((0, -distance, 0)))
        overlap = moved & frame
        assert overlap is None or overlap.volume < 1e-6
    assert tray.moved(Location((0, -1215, 0))).bounding_box().max.Y == pytest.approx(35)
