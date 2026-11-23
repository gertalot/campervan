"""The owner's plywood panels, flat pine frame and insulation infill."""

from math import atan2, degrees, hypot

from build123d import Color, Compound, Face, Location, Part, Solid, Wire

from campervan.cad.panels import panel
from campervan.parameters import Parameters

FLOOR_BASE_WIDTH_MM = 1200.0


def rib_frame(outline: list[tuple[float, float]], centre: float, seam: float,
              length: float, p: Parameters) -> Compound:
    width, depth = p.floor_rib_width_mm, p.floor_rib_thickness_mm
    bottom = -p.floor_ply_thickness_mm - depth
    colour = Color(0.84, 0.64, 0.39)
    members = []

    def inward(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        dx, dy = b[0] - a[0], b[1] - a[1]
        distance = hypot(dx, dy)
        return -dy / distance, dx / distance

    # Intersections of adjacent inward-offset edges give exact mitred joints.
    joints = []
    for index, point in enumerate(outline):
        before = inward(outline[index - 1], point)
        after = inward(point, outline[(index + 1) % len(outline)])
        scale = width / (1 + before[0] * after[0] + before[1] * after[1])
        joints.append((point[0] + scale * (before[0] + after[0]),
                       point[1] + scale * (before[1] + after[1])))
    for index, a in enumerate(outline):
        following = (index + 1) % len(outline)
        b = outline[following]
        dx, dy = b[0] - a[0], b[1] - a[1]
        distance = hypot(dx, dy)
        ux, uy = dx / distance, dy / distance
        corners = (a, b, joints[following], joints[index])
        local = [((x - a[0]) * ux + (y - a[1]) * uy,
                  -(x - a[0]) * uy + (y - a[1]) * ux, 0) for x, y in corners]
        member = Part(Solid.extrude(Face(Wire.make_polygon(local)), (0, 0, depth)).solids(),
                      label=f"Perimeter rib {index + 1:02}", color=colour)
        member.location = Location((centre + a[0], a[1], bottom), (0, 0, degrees(atan2(dy, dx))))
        members.append(member)

    half_core = FLOOR_BASE_WIDTH_MM / 2
    if 4 * width >= 2 * half_core or 2 * width >= min(seam, length - seam):
        raise ValueError("Floor ribs must leave three clear spans and room beside the panel seam.")
    left = centre - half_core
    pitch = (2 * half_core - width) / 3
    centres = [left + width / 2 + pitch * index for index in (1, 2)]
    for index, x in enumerate(centres, 1):
        member = panel(length - 2 * width, width, depth)
        member.label, member.color = f"Longitudinal rib {index}", colour
        member.location = Location((x + width / 2, width, bottom), (0, 0, 90))
        members.append(member)
    half_wide = max(x for x, _ in outline)
    wing_ends = [y for x, y in outline if abs(x) == half_wide]
    wing_middle = (min(wing_ends) + max(wing_ends)) / 2
    for name, y, half in (("Panel seam batten", seam, half_core),
                          ("Door-wing cross-batten", wing_middle, half_wide)):
        intervals = [(centre - half + width, centres[0] - width / 2),
                     (centres[0] + width / 2, centres[1] - width / 2),
                     (centres[1] + width / 2, centre + half - width)]
        for index, (start, end) in enumerate(intervals, 1):
            member = panel(end - start, width, depth)
            member.label, member.color = f"{name} {index}", colour
            member.location = Location((start, y - width / 2, bottom))
            members.append(member)
    return Compound(label="Pine rib frame", children=members)


def build_floor_plywood(p: Parameters) -> Compound:
    """Owner's two existing panels; stepped door-wing contours are provisional photo estimates."""
    centre = p.cargo_width_mm / 2
    rear_length, front_length = 830.0, 1200.0
    half_width, wing = FLOOR_BASE_WIDTH_MM / 2, 725.0
    rear_outline = [(-half_width, 0), (half_width, 0),
                    (half_width, rear_length), (-half_width, rear_length)]
    # Front piece is reversed end-for-end from the photograph: two rear steps, one front chamfer.
    # Keep its narrow base beyond the wheel arches; full-width door wings span world Y1165–1835 after placement.
    front_outline = [
        (-half_width, 0), (half_width, 0),
        (half_width, 220), (650, 250), (650, 300), (wing, 350),
        (wing, 1020), (half_width, 1070), (half_width, front_length),
        (-half_width, front_length), (-half_width, 1070), (-wing, 1020),
        (-wing, 350), (-650, 300), (-650, 250), (-half_width, 220),
    ]
    panels = []
    for name, outline, y in (("Rear panel", rear_outline, 0), ("Front panel", front_outline, rear_length)):
        wire = Wire.make_polygon([(centre + x, y + along, 0) for x, along in outline])
        part = Solid.extrude(Face(wire), (0, 0, -p.floor_ply_thickness_mm))
        part.label, part.color = name, Color(0.76, 0.70, 0.55, 0.32)
        panels.append(part)
    outer = rear_outline[:2] + [(x, rear_length + y) for x, y in front_outline[2:]]
    frame = rib_frame(outer, centre, rear_length, rear_length + front_length, p)
    if p.floor_insulation_thickness_mm > p.floor_rib_thickness_mm:
        raise ValueError("Floor insulation must fit within the pine rib depth.")
    envelope = Solid.extrude(
        Face(Wire.make_polygon([(centre + x, y, -p.floor_ply_thickness_mm) for x, y in outer])),
        (0, 0, -p.floor_insulation_thickness_mm),
    )
    cavities = sorted((envelope - frame).solids(),
                      key=lambda solid: (round(solid.bounding_box().center().Y), solid.bounding_box().min.X))
    if len(cavities) != 9:
        raise ValueError("The floor frame must leave nine insulation bays.")
    infill = []
    for index, solid in enumerate(cavities):
        row = ("Rear", "Middle", "Front")[index // 3]
        column = ("left", "centre", "right")[index % 3]
        infill.append(Part([solid], label=f"{row} {column} infill", color=Color(0.94, 0.94, 0.90)))
    insulation = Compound(label="Floor insulation", children=infill)
    return Compound(label="Finished floor plywood", children=[*panels, frame, insulation]).moved(
        Location((0, -15, p.floor_surface_z_mm)))

