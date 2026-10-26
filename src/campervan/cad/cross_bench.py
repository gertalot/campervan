"""Fixed cross bench: two open-legged plywood frames, aft skin and directly fastened slats."""

from build123d import Color, Compound, Location

from campervan.cad.cushions import build_cushions
from campervan.cad.drawer import drawer_support_x
from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


def build_cross_bench(p: Parameters) -> Compound:
    width = p.bed_width_mm
    rear, front = p.seat_length_mm, p.cargo_length_mm
    length = front - rear
    overhang, thickness, skin = p.cross_bench_overhang_mm, p.frame_thickness_mm, p.cross_bench_skin_thickness_mm
    span = length - skin
    height = p.platform_height_mm - p.slat_thickness_mm
    member, radius = p.member_width_mm, p.inside_radius_mm
    wall_x = drawer_support_x(p)
    aisle_x = width - overhang - thickness
    # Slats run across the van. Their ends overhang two fore/aft support frames.
    frame_rear = rear + skin
    parts = []
    for name, x in (("Wall-side frame", wall_x), ("Aisle frame", aisle_x)):
        frame = frame_panel(span, thickness, height, [(member, span - member, -2 * radius, height - member)], radius)
        frame.label, frame.color = name, Color(0.88, 0.61, 0.25)
        frame.location = Location((x + thickness, frame_rear, 0), (0, 0, 90))
        parts.append(frame)
    back = panel(aisle_x + thickness - wall_x, skin, height)
    back.label, back.color = "Rear skin", Color(0.75, 0.66, 0.49)
    back.location = Location((wall_x, rear, 0))
    parts.append(back)

    # Keep the previous extended cross bench's four slats, including both end rows.
    count = 4
    gap = (length - count * p.slat_width_mm) / (count - 1)
    if gap <= 0:
        raise ValueError("Cross bench needs room for four full-width slats and ventilation gaps.")
    slats = []
    for i in range(count):
        slat = panel(width, p.slat_width_mm, p.slat_thickness_mm)
        slat.label, slat.color = f"Fixed slat {i + 1:02}", Color(0.87, 0.70, 0.43)
        slat.location = Location((0, rear + i * (p.slat_width_mm + gap), height))
        slats.append(slat)
    parts.append(Compound(label="Fixed slats", children=slats))
    return Compound(
        label="Cross bench",
        children=[Compound(label="Fixed frame", children=parts), build_cushions(p, "Cross bench")],
    )
