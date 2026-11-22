"""Fixed cross bench: four open-legged plywood frames and directly fastened slats."""

from build123d import Axis, Color, Compound, Location, fillet

from campervan.cad.cushions import build_cushions
from campervan.cad.cross_bench_layout import cross_bench_layout
from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


# Square wall end clearing the registered front-pillar scan across the complete slat thickness.
FRONT_PILLAR_SLAT_END_X_MM = 100.0


def build_cross_bench(p: Parameters) -> Compound:
    width = p.bed_width_mm
    layout = cross_bench_layout(p)
    rear, length, height = layout.rear, layout.length, layout.height
    thickness = p.frame_thickness_mm
    member, radius = p.member_width_mm, p.inside_radius_mm
    wall_x, aisle_x = layout.wall_x, layout.aisle_x
    # Slats run across the van. Their ends overhang two fore/aft support frames.
    parts = []
    for name, x in (("Wall-side frame", wall_x), ("Aisle frame", aisle_x)):
        frame = frame_panel(length, thickness, height, [(member, length - member, -2 * radius, height - member)], radius)
        frame.label, frame.color = name, Color(0.88, 0.61, 0.25)
        frame.location = Location((x + thickness, rear, 0), (0, 0, 90))
        parts.append(frame)
    span = aisle_x - wall_x - thickness
    for name, y in (("Rear mounting frame", rear), ("Front support frame", rear + length - thickness)):
        frame = frame_panel(span, thickness, height,
                            [(member, span - member, -2 * radius, height - member)], radius)
        frame.label, frame.color = name, Color(0.88, 0.61, 0.25)
        frame.location = Location((wall_x + thickness, y, 0))
        parts.append(frame)

    # Keep the previous extended cross bench's four slats, including both end rows.
    count = 4
    gap = (length - count * p.slat_width_mm) / (count - 1)
    if gap <= 0:
        raise ValueError("Cross bench needs room for four full-width slats and ventilation gaps.")
    slats = []
    for i in range(count):
        wall_trim = FRONT_PILLAR_SLAT_END_X_MM - p.bed_inward_offset_mm if i == count - 1 else 0.0
        slat_length = width - (50 if i == 0 else wall_trim)
        slat = panel(slat_length, p.slat_width_mm, p.slat_thickness_mm)
        if i == 0:
            # Ease the aisle corner nearest the long bench, where legs pass.
            corner = [edge for edge in slat.edges().filter_by(Axis.Z)
                      if abs(edge.center().X - slat_length) < 1e-6 and abs(edge.center().Y) < 1e-6]
            slat = fillet(corner, p.slat_width_mm / 2)
        slat.label, slat.color = f"Fixed slat {i + 1:02}", Color(0.87, 0.70, 0.43)
        slat.location = Location((wall_trim, rear + i * (p.slat_width_mm + gap), height))
        slats.append(slat)
    parts.append(Compound(label="Fixed slats", children=slats))
    return Compound(
        label="Cross bench",
        children=[Compound(label="Fixed frame", children=parts), build_cushions(p, "Cross bench")],
    )
