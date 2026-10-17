"""Two recessed cross-bed plate stops and their slat pockets."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from build123d import Color, Compound, Location, Part

from campervan.cad.panels import panel
from campervan.parameters import Parameters

if TYPE_CHECKING:
    from campervan.cad.cross_bed import CrossBedLayout


@dataclass(frozen=True)
class StopLayout:
    x: float
    top: float
    bottom: float
    ends: tuple[tuple[float, float, float], ...]  # Slat edge, plate rear, plate front.


def cross_stop_layout(p: Parameters, layout: "CrossBedLayout") -> StopLayout:
    x = (layout.moving_start + layout.width - layout.travel) / 2
    half = p.cross_stop_plate_width_mm / 2
    embed = p.cross_stop_plate_length_mm / 2
    overlap = p.cross_stop_plate_length_mm - embed - layout.slat_gap
    clearance = p.cross_stop_clearance_mm
    height = p.platform_height_mm - p.slat_thickness_mm
    top = height + p.cross_stop_recess_depth_mm - clearance
    bottom = top - p.cross_stop_plate_thickness_mm
    if (
        overlap <= clearance
        or embed + clearance >= p.slat_width_mm
        or overlap + clearance >= min(layout.slats[1][1], layout.slats[-2][1])
        or p.cross_stop_recess_depth_mm >= p.slat_thickness_mm
        or bottom - p.cross_stop_head_allowance_mm < height + clearance
        or x - half - clearance <= layout.moving_start
        or x + layout.travel + half + clearance >= layout.width + p.frame_thickness_mm
    ):
        raise ValueError("Plate stops need closed slat pockets and clearance above the deck.")
    rear_y, rear_width = layout.slats[0]
    rear_edge = rear_y + rear_width
    front_edge = layout.slats[-1][0]
    return StopLayout(
        x,
        top,
        bottom,
        ((rear_edge, rear_edge - embed, rear_edge + embed), (front_edge, front_edge - embed, front_edge + embed)),
    )


def cut_stop_pocket(
    slat: Part, p: Parameters, layout: "CrossBedLayout", stop: StopLayout, index: int, *, moving: bool
) -> Part:
    targets = (0, len(layout.slats) - 1) if moving else (1, len(layout.slats) - 2)
    if index not in targets:
        return slat
    rear = index == targets[0]
    edge, low, high = stop.ends[0 if rear else 1]
    clearance = p.cross_stop_clearance_mm
    half = p.cross_stop_plate_width_mm / 2
    height = p.platform_height_mm - p.slat_thickness_mm
    if moving:
        x0, x1 = stop.x - half - clearance, stop.x + half + clearance
        y0, y1 = (low - clearance, edge + clearance) if rear else (edge - clearance, high + clearance)
        top = stop.top
    else:
        # Exact X end faces contact the plate at the retracted and extended limits.
        x0, x1 = stop.x - half, stop.x + layout.travel + half
        y0, y1 = (edge, high + clearance) if rear else (low - clearance, edge)
        top = height + p.cross_stop_recess_depth_mm
    cutter = panel(x1 - x0, y1 - y0, top - height + 1).moved(Location((x0, y0, height - 1)))
    return slat - cutter


def build_cross_stops(p: Parameters, layout: "CrossBedLayout") -> Compound:
    stop = cross_stop_layout(p, layout)
    plates = []
    for name, (_, low, high) in zip(("Rear plate stop", "Cab-end plate stop"), stop.ends, strict=True):
        plate = panel(p.cross_stop_plate_width_mm, high - low, p.cross_stop_plate_thickness_mm)
        plate.location = Location((stop.x - p.cross_stop_plate_width_mm / 2, low, stop.bottom))
        plate.label, plate.color = name, Color(0.60, 0.65, 0.70)
        plates.append(plate)
    return Compound(label="Extension stops", children=plates)
