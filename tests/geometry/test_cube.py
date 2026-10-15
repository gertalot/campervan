import pytest

from campervan.cad.cube import make_cube
from campervan.parameters import Parameters


def test_cube_is_one_named_valid_centered_solid() -> None:
    size = 150.0
    cube = make_cube(Parameters(size_mm=size))
    assert cube.label == "Cube"
    assert cube.is_valid
    assert len(cube.solids()) == 1
    bounds = cube.bounding_box()
    for axis in ("X", "Y", "Z"):
        assert getattr(bounds.min, axis) == pytest.approx(-size / 2, rel=1e-9, abs=1e-6)
        assert getattr(bounds.max, axis) == pytest.approx(size / 2, rel=1e-9, abs=1e-6)
    assert cube.volume == pytest.approx(size**3, rel=1e-9, abs=1e-6)
