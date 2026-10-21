"""Check the lower platform boundary against actual furniture solids."""

from campervan.cad.model import build_campervan
from campervan.parameter_fit import fit_parameters, parameter_constraints
from campervan.parameters import Parameters


def test_lower_platform_boundary_builds_and_drawer_adjustment_clears_header():
    baseline = Parameters()
    minimum = parameter_constraints(baseline)["platform_height_mm"]["minimum"]
    for p in (
        Parameters(platform_height_mm=minimum),
        Parameters(platform_height_mm=366, inside_radius_mm=5),
    ):
        p, _ = fit_parameters(p)
        model = build_campervan(p)
        for assembly in model.children[2:]:
            for part in assembly.leaves:
                assert part.is_valid and len(part.solids()) == 1, (p.platform_height_mm, part.label, len(part.solids()))
        bench = model.children[2]
        frame, _, drawer = bench.children[:3]
        overlap = frame & drawer.children[0]
        assert overlap is None or overlap.volume < 1e-6
        overlap = frame.children[4] & frame.children[-1]
        assert overlap is None or overlap.volume < 1e-6
