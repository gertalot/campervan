"""Create the cube without API or viewer dependencies."""

from build123d import Align, Box, Part

from campervan.parameters import Parameters


def make_cube(parameters: Parameters) -> Part:
    size = parameters.size_mm
    cube = Box(size, size, size, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    cube.label = "Cube"
    return cube
