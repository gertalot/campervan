import pytest
from build123d import Compound

from campervan.cad.bench import build_long_bench
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def test_sliding_bed_endpoints_and_sampled_clearance():
    for extension in (0, 50, 100):
        p = Parameters(bed_extension_percent=extension)
        bench = build_long_bench(p)
        fixed_frame, bed = bench.children
        fixed_slats, ledges, moving = bed.children
        moving_slats, moving_frame, strip, brackets = moving.children
        assert len(fixed_slats.children) == 8 and len(moving_slats.children) == 7
        assert len(brackets.children) == 3
        assert all(part.is_valid and len(part.solids()) == 1 for part in bench.leaves)
        assert moving.bounding_box().max.X == pytest.approx(618 + 452 * extension / 100)
        assert bench.bounding_box().max.Z == pytest.approx(400)
        assert fixed_slats.children[0].bounding_box().min.X == pytest.approx(150)
        assert strip.bounding_box().size.X == pytest.approx(40)
        assert moving_frame.bounding_box().size.X == pytest.approx(18)
        for ledge in ledges.children:
            assert ledge.bounding_box().min.Z == pytest.approx(322)
            assert ledge.bounding_box().max.Z == pytest.approx(364)
            ledge_overlap = ledge & fixed_frame
            assert ledge_overlap is None or ledge_overlap.volume < 1e-6
        if extension == 100:
            first_moving = moving_slats.children[0]
            placed_slat = first_moving.located(first_moving.global_location)
            assert fixed_slats.bounding_box().max.X - placed_slat.bounding_box().min.X == pytest.approx(159)
            placed_strip = strip.located(strip.global_location)
            assert placed_strip.bounding_box().max.X == pytest.approx(582)  # Stop meets the fixed aisle frame.
        arch = build_vehicle_references(p).children[1].children[0]
        stationary = Compound([fixed_frame, fixed_slats, ledges, arch])
        overlap = moving & stationary
        assert overlap is None or overlap.volume < 1e-6, (extension, overlap.volume)
