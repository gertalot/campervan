from itertools import combinations

import pytest
from build123d import Compound, Location

from campervan.cad.bench import build_long_bench
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_fixed_bench_parts_fit_together_and_clear_wheel_arch():
    for p in (Parameters(), Parameters(long_bench_width_mm=650, seat_length_mm=1350)):
        bench = build_long_bench(p)
        parts = bench.children[0].children[:-2]
        assert bench.label == "Long bench" and bench.children[0].label == "Fixed frame"
        assert [part.label for part in parts] == [
            "Wall-side frame",
            "Aisle frame",
            "Cab-end frame",
            "Cab-end skin",
            "Internal drawer-support frame",
            "Rear header",
        ]
        assert all(part.is_valid and len(part.solids()) == 1 for part in parts)
        for part in parts[2:4]:
            assert part.bounding_box().min.X == pytest.approx(parts[4].bounding_box().min.X)
        bounds = Compound(parts).bounding_box()
        assert (bounds.max.X, bounds.max.Y, bounds.max.Z) == pytest.approx(
            (p.long_bench_width_mm, p.seat_length_mm, p.platform_height_mm - p.slat_thickness_mm)
        )
        header = parts[-1].bounding_box()
        assert header.min.Y == pytest.approx(0)
        assert header.min.Z == pytest.approx(322)
        arch = build_vehicle_references(p).children[1].children[0].moved(Location((0, -p.furniture_rear_gap_mm, 0)))
        parts = list(bench.children[0].leaves)
        for a, b in [*combinations(parts, 2), *((part, arch) for part in parts)]:
            overlap = a & b
            assert overlap is None or overlap.volume < 1e-6, (a.label, b.label)
