"""One plywood storage box with equal bays and a full-length hinged slat lid."""

from build123d import Color, Compound, Location, Part

from campervan.cad.cushions import build_cushions
from campervan.cad.panels import panel
from campervan.cad.sliding_bed import build_lid, long_bed_layout
from campervan.cad.bed_lift import build_lifts
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

    # The plywood comb now bears across the entire box rim.
    place("Wall-side hinge panel", (t, length, layout.box_top), (rear, 0, 0))
    place("Aisle-side panel", (t, length, layout.box_top), (front - t, 0, 0))
    for name, y in (("Rear end panel", 0), ("Centre support divider", (length - t) / 2), ("Cab-end panel", length - t)):
        place(name, (inside_width, t, layout.box_top), (rear + t, y, 0))

    return Compound(
        label="Long bench",
        children=[
            Compound(label="Storage box", children=parts),
            build_lifts(layout.lid_rear, layout.box_top, length, t, p.bed_lid_open_percent),
            build_lid(p, layout),
            build_cushions(p, "Long bench"),
        ],
    )
