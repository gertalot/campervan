"""Rear storage tray and simplified rail envelopes from nv200-interior.fs."""

from build123d import Color, Compound, Location, Part

from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


def build_rear_drawer(p: Parameters) -> Compound:
    ply = p.drawer_ply_mm
    left = (p.cargo_width_mm - p.arch_gap_mm) / 2 + p.drawer_arch_clearance_mm + p.frame_thickness_mm
    left += p.slide_thickness_mm
    right = p.long_bench_width_mm - p.frame_thickness_mm - p.slide_thickness_mm
    width = right - left
    length = p.drawer_length_mm + p.drawer_rear_setback_mm
    bottom = p.drawer_floor_clearance_mm
    height = p.drawer_height_mm
    shift = p.slide_travel_mm * p.drawer_extension_percent / 100
    header_bottom = p.platform_height_mm - p.slat_thickness_mm - p.member_width_mm
    if width <= 2 * ply or p.drawer_side_band_mm <= ply or height <= p.drawer_side_band_mm + p.inside_radius_mm:
        raise ValueError("Drawer dimensions leave insufficient room inside the tray or its open sides.")
    if length >= p.seat_length_mm - p.frame_thickness_mm - p.wall_thickness_mm:
        raise ValueError("Closed drawer must clear the cab-end frame.")
    if bottom + height >= header_bottom:
        raise ValueError("Drawer must fit below the rear header.")
    if bottom + ply + p.slide_height_mm > min(p.drawer_mount_band_mm, bottom + p.drawer_side_band_mm):
        raise ValueError("Drawer rails must fit on both continuous mounting bands.")
    if not p.drawer_length_mm <= p.slide_travel_mm < 2 * p.drawer_length_mm:
        raise ValueError("Rail travel must provide full extension while retaining telescoping overlap.")

    pieces: list[Part] = []

    def place(part: Part, name: str, x: float, y: float, z: float, rotation: float = 0) -> None:
        part.label, part.color = name, Color(0.78, 0.65, 0.44)
        part.location = Location((x, y, z), (0, 0, rotation))
        pieces.append(part)

    place(panel(width - 2 * ply, length - 2 * ply, ply), "Bottom", left + ply, ply, bottom)
    for name, x in (("Wall-side panel", left), ("Aisle-side panel", right - ply)):
        side = frame_panel(
            length,
            ply,
            height,
            [(p.member_width_mm, length - p.member_width_mm, p.drawer_side_band_mm, height + 2 * p.inside_radius_mm)],
            p.inside_radius_mm,
        )
        place(side, name, x + ply, 0, bottom, rotation=90)
    place(panel(width - 2 * ply, ply, height), "Rear end panel", left + ply, 0, bottom)
    place(panel(width - 2 * ply, ply, height), "Cab-facing end panel", left + ply, length - ply, bottom)
    tray = Compound(label="Tray", children=pieces)
    tray.location = Location((0, -shift, 0))

    stages = []
    for stage, name in enumerate(("Fixed", "Intermediate", "Moving")):
        rails = []
        for side_index, gap_start in ((0, left - p.slide_thickness_mm), (1, right)):
            x = gap_start + (stage if side_index == 0 else 2 - stage) * p.slide_thickness_mm / 3
            rail = panel(p.slide_thickness_mm / 3, p.drawer_length_mm, p.slide_height_mm)
            rail.label = "Left rail" if side_index == 0 else "Right rail"
            rail.color = Color(0.52, 0.56, 0.60)
            rail.location = Location((x, p.drawer_rear_setback_mm, bottom + ply))
            rails.append(rail)
        group = Compound(label=name, children=rails)
        group.location = Location((0, -shift * stage / 2, 0))
        stages.append(group)
    return Compound(label="Rear drawer", children=[tray, Compound(label="Rails", children=stages)])
