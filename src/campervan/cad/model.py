"""Assemble the campervan from native build123d component trees."""

from build123d import Compound, Location

from campervan.cad.bench import build_long_bench
from campervan.cad.body import build_floor_plywood
from campervan.cad.cabinet import build_cabinet
from campervan.cad.cross_bench import build_cross_bench
from campervan.cad.gear import build_stored_gear
from campervan.cad.mirror import mirror_assembly
from campervan.cad.vehicle import build_vehicle_references
from campervan.parameters import Parameters


def build_campervan(parameters: Parameters) -> Compound:
    placement = Location((parameters.cargo_width_mm, parameters.furniture_rear_gap_mm, 0))
    furniture = [build_long_bench(parameters), build_cross_bench(parameters), build_cabinet(parameters)]
    return Compound(
        label="Campervan",
        children=[
            build_vehicle_references(parameters),
            build_floor_plywood(parameters),
            build_stored_gear(parameters),
            *(mirror_assembly(assembly).moved(placement) for assembly in furniture),
        ],
    )
