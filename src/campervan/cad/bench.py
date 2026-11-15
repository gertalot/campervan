"""One plywood storage box with equal bays and a full-length hinged slat lid."""

from build123d import Align, Color, Compound, Cylinder, Location, Part

from campervan.cad.cushions import build_cushions
from campervan.cad.panels import panel
from campervan.cad.sliding_bed import build_lid, long_bed_layout
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

    # All five panels stand on the van floor and carry the slats directly.
    place("Wall-side hinge panel", (t, length, layout.slat_bottom), (rear, 0, 0))
    place("Aisle-side panel", (t, length, layout.slat_bottom), (front - t, 0, 0))
    for name, y in (("Rear end panel", 0), ("Centre support divider", (length - t) / 2), ("Cab-end panel", length - t)):
        place(name, (inside_width, t, layout.slat_bottom), (rear + t, y, 0))

    hinges = []
    for index, y in enumerate((length * 0.1, length / 2, length * 0.9), start=1):
        # A schematic barrel locates each hinge. Leaves and fixings await hardware selection.
        hinge = Cylinder(3, 50, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.CENTER))
        hinge.label, hinge.color = f"Provisional lid hinge {index}", Color(0.62, 0.66, 0.70)
        hinge.location = Location((layout.rear, y, layout.slat_bottom))
        hinges.append(hinge)
    return Compound(
        label="Long bench",
        children=[
            Compound(label="Storage box", children=parts),
            Compound(label="Lid hinges", children=hinges),
            build_lid(p, layout),
            build_cushions(p, "Long bench"),
        ],
    )
