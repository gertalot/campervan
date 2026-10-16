"""Assemble the campervan from native build123d component trees."""

from build123d import Compound

from campervan.cad.bench import build_long_bench
from campervan.cad.cabinet import build_cabinet
from campervan.cad.cross_bench import build_cross_bench
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def build_campervan(parameters: Parameters) -> Compound:
    return Compound(
        label="Campervan",
        children=[
            build_vehicle_references(parameters),
            build_long_bench(parameters),
            build_cross_bench(parameters),
            build_cabinet(parameters),
        ],
    )
