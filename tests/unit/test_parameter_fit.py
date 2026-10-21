import pytest

from campervan.parameter_fit import fit_parameters, parameter_constraints
from campervan.parameters import Parameters


def test_platform_limit_explains_the_current_cabinet_and_tracks_stock_dimensions():
    p = Parameters()
    limit = parameter_constraints(p)["platform_height_mm"]
    assert limit["minimum"] == 358
    assert "Long-bench" in limit["reason"] and "wheel arch" in limit["reason"]
    assert parameter_constraints(Parameters(member_width_mm=55))["platform_height_mm"]["minimum"] == 353
    with pytest.raises(ValueError, match="358.*Long-bench"):
        fit_parameters(Parameters(platform_height_mm=200))


def test_lower_platform_resizes_drawer_and_support_without_changing_stock():
    p = Parameters(platform_height_mm=366, inside_radius_mm=5)
    fitted, adjustments = fit_parameters(p)
    assert fitted.drawer_height_mm == 277
    assert fitted.drawer_frame_height_mm == 287
    assert "drawer_height_mm" in adjustments
    assert fitted.frame_thickness_mm == p.frame_thickness_mm
    assert fitted.platform_height_mm == 366
    assert not fit_parameters(fitted)[1]


def test_cabinet_divider_tracks_mattress_and_limits_inputs_before_cad():
    p = Parameters(platform_height_mm=390)
    assert p.cabinet_lower_rail_top_mm == 530
    assert Parameters(platform_height_mm=370, foam_thickness_mm=80).cabinet_lower_rail_top_mm == 490
    limits = parameter_constraints(p)
    assert limits["platform_height_mm"]["maximum"] == pytest.approx(539.9)
    assert limits["foam_thickness_mm"]["maximum"] == pytest.approx(249.9)
    with pytest.raises(ValueError, match="mattress|Mattress"):
        fit_parameters(Parameters(platform_height_mm=550))
