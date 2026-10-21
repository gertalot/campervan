"""Measured storage envelopes, independent of approximate chair/bag detailing."""

import pytest
from build123d import Compound, Location

from campervan.cad.bom import cut_list
from campervan.cad.gear import build_stored_gear
from campervan.parameters import Parameters


def test_owned_gear_preserves_measured_sizes_and_is_not_cut_stock():
    p = Parameters()
    gear = build_stored_gear(p)
    bag, chairs = gear.children
    assert all(part.is_valid and part.volume > 0 for part in gear.leaves)
    assert tuple(bag.bounding_box().size) == pytest.approx((830, 80, 760), abs=1e-5)
    assert len(chairs.children) == 2
    for chair in chairs.children:
        # Chairs are turned edge-on in the aisle; their local envelope remains 600 x 100 x 700.
        assert tuple(chair.located(Location()).bounding_box().size) == pytest.approx((600, 100, 700), abs=1e-5)
        assert tuple(chair.bounding_box().size) == pytest.approx((100, 600, 700), abs=1e-5)
        assert chair.bounding_box().min.Z == pytest.approx(0, abs=1e-5)
    assert bag.bounding_box().min.Z == pytest.approx(0, abs=1e-5)
    assert bag.bounding_box().max.Y < p.furniture_rear_gap_mm
    assert cut_list(Compound(label="Campervan", children=[gear]), p) == []
