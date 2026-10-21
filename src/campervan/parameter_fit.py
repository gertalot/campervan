"""Cheap dimensional checks for the bed-height dependency chain, before CAD work."""

from math import sqrt
from typing import TypedDict

from campervan.parameters import Parameters


class Constraint(TypedDict, total=False):
    minimum: float
    maximum: float
    reason: str


class FitError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


def parameter_constraints(p: Parameters) -> dict[str, Constraint]:
    slat, member, radius = p.slat_thickness_mm, p.member_width_mm, p.inside_radius_mm
    # Match the rounded wall-frame opening at the rear of the wheel arch.
    setback = max(0, p.rear_corner_radius_mm + p.rear_corner_allowance_mm - p.furniture_rear_gap_mm)
    arch_rear = p.arch_rear_offset_mm - p.furniture_rear_gap_mm
    rear_end = max(arch_rear - p.arch_clearance_mm, setback + member)
    gap = min(arch_rear - rear_end, p.arch_clearance_mm)
    corner = radius - sqrt(radius**2 - (radius - gap) ** 2) if 0 <= gap < radius else 0
    limits = [
        (
            slat + member + p.arch_height_mm + corner,
            "Long-bench wall frame: the top rail and its rounded opening must clear the wheel arch.",
        ),
        (
            slat + 2 * p.frame_thickness_mm + p.arch_height_mm + 0.1,
            "Sliding-bed tie strip must remain above the wheel arch.",
        ),
        (
            slat + member + 0.1,
            "Cross-bench frames need room for their top rails and open legs.",
        ),
        (
            slat + p.drawer_mount_band_mm + 2 * member + 2 * radius + 1.1,
            "Internal drawer-support frame needs room for its slide mounting band and rounded openings.",
        ),
        (
            slat + member + p.drawer_floor_clearance_mm + p.drawer_side_band_mm + radius + 1.1,
            "Drawer needs room for its floor clearance, slide mounting band and rounded side openings.",
        ),
    ]
    limits.append(
        (
            p.arch_height_mm
            + 3
            - p.foam_thickness_mm
            - p.cabinet_mattress_clearance_mm
            + p.cabinet_ledge_height_mm
            + p.cabinet_shelf_thickness_mm,
            "Cabinet shelf rail: its underside must clear the wheel arch by 3mm.",
        )
    )
    minimum, reason = max(limits, key=lambda item: item[0])
    # The raised lower divider must leave a usable rounded opening below the
    # next shelf. Its height follows the uncompressed mattress and sourced stock.
    maximum = (
        p.cabinet_rear_storage_height_mm
        - 2 * radius
        - 0.1
        - p.foam_thickness_mm
        - p.cabinet_mattress_clearance_mm
        - member
        + p.cabinet_ledge_height_mm
        + p.cabinet_shelf_thickness_mm
    )
    member_minimum, member_reason = max(
        (
            (2 * p.frame_thickness_mm, "the tie strip and guide thicknesses"),
            (p.bracket_arm_mm + p.bracket_clearance_mm + 0.1, "the bed angle brackets and their clearance"),
            (
                p.cabinet_shelf_thickness_mm + p.cabinet_ledge_height_mm + p.cabinet_door_overlap_mm,
                "the shelf, its ledge and door overlap above the mattress",
            ),
            (2 * p.cabinet_door_overlap_mm + p.cabinet_door_gap_mm + 0.1, "the cabinet door overlaps and gap"),
        ),
        key=lambda item: item[0],
    )
    member_maximum = min(
        arch_rear - setback - 0.1,
        p.seat_length_mm - arch_rear - p.arch_length_mm - p.arch_clearance_mm,
    )
    return {
        "cross_bench_overhang_mm": {
            "minimum": 0,
            "maximum": p.bed_width_mm - p.drawer_support_x_mm - 2 * p.frame_thickness_mm - 0.1,
            "reason": "Leave room between the drawer-aligned wall-side frame and the aisle support frame.",
        },
        "platform_height_mm": {
            "minimum": minimum,
            "maximum": maximum,
            "reason": f"Minimum {minimum:g}mm. {reason} Maximum {maximum:g}mm keeps the mattress-height "
            "cabinet divider below the next shelf opening.",
        },
        "foam_thickness_mm": {
            "minimum": 0.1,
            "maximum": maximum + p.foam_thickness_mm - p.platform_height_mm,
            "reason": "Mattress thickness raises the cabinet divider; leave room for the opening above it.",
        },
        "cabinet_mattress_clearance_mm": {
            "minimum": 0,
            "maximum": maximum + p.cabinet_mattress_clearance_mm - p.platform_height_mm,
            "reason": "Shelf clearance raises the cabinet divider; leave room for the opening above it.",
        },
        "drawer_height_mm": {
            "minimum": p.drawer_side_band_mm + radius + 0.1,
            "maximum": p.platform_height_mm - slat - member - p.drawer_floor_clearance_mm - 1,
            "reason": "Tray height reduces automatically to leave 1mm below the rear header.",
        },
        "drawer_frame_height_mm": {
            "minimum": p.drawer_mount_band_mm + member + 2 * radius + 0.1,
            "maximum": p.platform_height_mm - slat - member - 1,
            "reason": "Support height reduces automatically to leave 1mm below the sliding-bed guides.",
        },
        "member_width_mm": {
            "minimum": member_minimum,
            "maximum": member_maximum,
            "reason": f"Minimum {member_minimum:g}mm fits {member_reason}. Maximum {member_maximum:g}mm "
            "leaves room for the wall-side posts beside the wheel arch.",
        },
    }


def fit_parameters(p: Parameters) -> tuple[Parameters, dict[str, str]]:
    constraints = parameter_constraints(p)
    member = constraints["member_width_mm"]
    if not member["minimum"] <= p.member_width_mm <= member["maximum"]:
        raise FitError("member_width_mm", f"Member width: {member['reason']}")
    platform = constraints["platform_height_mm"]
    if not platform["minimum"] <= p.platform_height_mm <= platform["maximum"]:
        raise FitError("platform_height_mm", f"Platform height: {platform['reason']}")
    values = p.model_dump()
    adjustments = {}
    for name in ("drawer_height_mm", "drawer_frame_height_mm"):
        limit = constraints[name]
        if values[name] < limit["minimum"]:
            raise FitError(
                name, f"{Parameters.model_fields[name].title}: minimum {limit['minimum']:g}mm. {limit['reason']}"
            )
        if values[name] > limit["maximum"]:
            values[name] = limit["maximum"]
            adjustments[name] = (
                f"{Parameters.model_fields[name].title}: {getattr(p, name):g} → {values[name]:g}mm. {limit['reason']}"
            )
    return Parameters.model_validate(values), adjustments
