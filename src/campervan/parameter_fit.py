"""Cheap dimensional checks for the bed-height dependency chain, before CAD work."""

from typing import TypedDict

from campervan.parameters import Parameters

# Disable furniture clearance checks and automatic fit adjustments while vehicle
# modelling continues. Furniture geometry, motion and cutting parts remain enabled.
FURNITURE_FIT_ENABLED = False


class Constraint(TypedDict, total=False):
    minimum: float
    maximum: float
    reason: str


class FitError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


def parameter_constraints(p: Parameters) -> dict[str, Constraint]:
    if not FURNITURE_FIT_ENABLED:
        return {}
    minimum = max(
        p.slat_thickness_mm + p.member_width_mm + 0.1,
        p.arch_height_mm + 3 - p.foam_thickness_mm - p.cabinet_mattress_clearance_mm + p.cabinet_frame_width_mm,
    )
    maximum = (
        p.cabinet_rear_storage_height_mm
        - 85
        - 2 * p.cabinet_door_gap_mm
        - 0.1
        - p.foam_thickness_mm
        - p.cabinet_mattress_clearance_mm
    )
    return {
        "platform_height_mm": {
            "minimum": minimum,
            "maximum": maximum,
            "reason": "Cross-bench and cabinet shelf clearances.",
        },
        "cross_bench_overhang_mm": {
            "minimum": 0,
            "maximum": p.bed_width_mm - p.cross_bench_support_x_mm - 2 * p.frame_thickness_mm - 0.1,
            "reason": "Leave room for the cross-bench support frames.",
        },
    }


def fit_parameters(p: Parameters) -> tuple[Parameters, dict[str, str]]:
    if not FURNITURE_FIT_ENABLED:
        return p, {}
    constraints = parameter_constraints(p)
    for name, limit in constraints.items():
        if not limit["minimum"] <= getattr(p, name) <= limit["maximum"]:
            raise FitError(name, limit["reason"])
    return p, {}
