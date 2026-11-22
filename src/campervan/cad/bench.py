"""Plywood storage box with a pillar-clearing rear end wall and a lifting lid."""

from build123d import Color, Compound, Location, Part

from campervan.cad.cushions import build_cushions
from campervan.cad.scan_scribing import scribe_assembly
from campervan.cad.panels import panel
from campervan.cad.sliding_bed import build_lid, long_bed_layout
from campervan.cad.bed_lift import build_lifts, lift_notches
from campervan.parameters import Parameters


def build_long_bench(p: Parameters) -> Compound:
    layout = long_bed_layout(p)
    t, length = p.frame_thickness_mm, p.seat_length_mm
    rear = layout.rear
    front = layout.box_front
    inside_width = front - rear - 2 * t
    parts: list[Part] = []

    def place(name: str, size: tuple[float, float, float], xyz: tuple[float, float, float]) -> None:
        part = panel(*size)
        part.label, part.color = name, Color(0.88, 0.61, 0.25)
        part.location = Location(xyz)
        parts.append(part)

    # The slotted plywood lid bears on the box rim.
    for name, x, rear_y in (("Wall-side hinge panel", rear, layout.rear_panel_y),
                            ("Aisle-side panel", front - t, 0.0)):
        wall = panel(t, length - rear_y, layout.box_top)
        for start, end, depth in lift_notches(length, t, layout.rear_panel_y):
            cutter = panel(t + 2, end - start, depth + 1)
            wall -= cutter.moved(Location((-1, start - rear_y, layout.box_top - depth)))
        wall.label, wall.color = name, Color(0.88, 0.61, 0.25)
        wall.location = Location((x, rear_y, 0))
        parts.append(wall)
    for name, y in (("Rear end panel", layout.rear_panel_y),
                    ("Centre support divider", (length - t) / 2), ("Cab-end panel", length - t)):
        place(name, (inside_width, t, layout.box_top), (rear + t, y, 0))

    assembly = Compound(
        label="Long bench",
        children=[
            Compound(label="Storage box", children=parts),
            build_lifts(layout.lid_rear, layout.box_top, length, t, p.bed_lid_open_percent,
                        rear_panel_y=layout.rear_panel_y),
            build_lid(p, layout),
            build_cushions(p, "Long bench"),
        ],
    )
    return scribe_assembly(assembly, (p.bed_inward_offset_mm, p.furniture_rear_gap_mm, p.floor_surface_z_mm), inboard=1)
