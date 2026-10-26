"""Owned, folded gear: measured outer sizes with approximate visual details."""

from build123d import Axis, Color, Compound, Face, Location, Part, Plane, RectangleRounded, Solid, Wire, fillet

from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


def folded_chair(p: Parameters, name: str) -> Compound:
    """Photo-based folded chair, including armrests and fittings within the measured envelope."""
    width, depth, height = p.chair_width_mm, p.chair_depth_mm, p.chair_height_mm
    tube = min(width / 30, depth / 5, height / 35)
    metal = Color(0.64, 0.69, 0.72)
    parts = []
    for label, frame_width, frame_height, y in (
        ("Back frame", width * 0.90, height, depth * 0.20),
        ("Folded leg frame", width * 0.93, height * 0.93, depth * 0.80),
    ):
        path = RectangleRounded(frame_width - tube, frame_height - tube, tube * 1.5).wire()
        path = path.moved(Location((width / 2, y, frame_height / 2), (90, 0, 0)))
        section = Face(Wire.make_circle(tube / 2, Plane(origin=path.position_at(0), z_dir=path.tangent_at(0))))
        parts.append(Part([Solid.sweep(section, path)], label=label, color=metal))

    for label, y, bottom, top in (
        ("Blue back fabric", depth * 0.20, height * 0.14, height * 0.87),
        ("Folded seat fabric", depth * 0.76, height * 0.08, height * 0.78),
    ):
        fabric = panel(width * 0.84, depth * 0.04, top - bottom)
        fabric.location = Location((width * 0.08, y, bottom))
        fabric.label, fabric.color = label, Color(0.03, 0.49, 0.69)
        parts.append(fabric)
    for side, x in (("Left", 0), ("Right", width * 0.93)):
        arm = panel(width * 0.07, depth * 0.35, height * 0.66)
        arm = fillet(arm.edges().filter_by(Axis.Y), width * 0.008)
        arm.location = Location((x, depth * 0.325, height * 0.31))
        arm.label, arm.color = f"{side} wooden armrest", Color(0.68, 0.58, 0.40)
        parts.append(arm)
        for label, z in (("Lower hinge", height * 0.12), ("Arm hinge", height * 0.30)):
            hinge = panel(width * 0.07, depth, height * 0.05)
            hinge = fillet(hinge.edges().filter_by(Axis.X), min(depth, height * 0.05) * 0.2)
            hinge.location = Location((x, 0, z))
            hinge.label, hinge.color = f"{side} {label.lower()}", Color(0.42, 0.46, 0.48)
            parts.append(hinge)
    # Rotation/position controls use the footprint centre, with the feet at local Z=0.
    return Compound(
        label=name,
        children=[part.moved(Location((-width / 2, -depth / 2, 0))) for part in parts],
    )


def solar_panel_bag(p: Parameters) -> Compound:
    """Closed padded bag; seams and folded handle are illustrative, not measured."""
    width, depth, height = p.solar_bag_width_mm, p.solar_bag_depth_mm, p.solar_bag_height_mm
    bag = panel(width, depth, height)
    bag = fillet(bag.edges(), min(width, depth, height) * 0.10)
    bag.label, bag.color = "Padded bag", Color(0.19, 0.22, 0.20)
    parts = [bag]
    for fraction in (0.23, 0.74):
        strap = panel(width * 0.03, depth * 0.025, height * 0.78)
        strap.location = Location((width * fraction, 0, height * 0.11))
        strap.label, strap.color = f"Webbing {len(parts)}", Color(0.10, 0.12, 0.11)
        parts.append(strap)
    handle = frame_panel(
        width * 0.20,
        depth * 0.05,
        height * 0.08,
        [(width * 0.02, width * 0.18, height * 0.015, height * 0.065)],
        min(width, height) * 0.008,
    )
    handle.location = Location((width * 0.40, 0, height * 0.84))
    handle.label, handle.color = "Folded carry handle", Color(0.10, 0.12, 0.11)
    parts.append(handle)
    return Compound(
        label="Solar panel bag",
        children=[part.moved(Location((-width / 2, -depth / 2, 0))) for part in parts],
    )


def chilly_bin(p: Parameters) -> Compound:
    """Owner's measured closed bin; mouldings and handle proportions follow the photos."""
    width, depth, height = p.chilly_bin_width_mm, p.chilly_bin_depth_mm, p.chilly_bin_height_mm
    scale = min(width, depth, height)
    red, white = Color(0.66, 0.035, 0.08), Color(0.91, 0.90, 0.85)
    body_top, rim_top, lid_bottom = height * 0.80, height * 0.855, height * 0.86

    def outline(w: float, d: float, z: float, radius: float) -> Wire:
        return RectangleRounded(w, d, radius).wire().moved(Location((0, 0, z)))

    body = Part([Solid.make_loft([
        outline(width * 0.92, depth * 0.89, 0, scale * 0.10),
        outline(width * 0.94, depth * 0.93, height * 0.07, scale * 0.12),
        outline(width * 0.99, depth * 0.99, body_top, scale * 0.14),
    ], ruled=True)])
    # Shallow underside recesses leave four moulded corner feet at Z=0.
    feet = panel(width * 0.68, depth * 1.1, height * 0.06)
    feet = fillet(feet.edges().filter_by(Axis.Y), height * 0.015)
    body -= feet.moved(Location((-width * 0.34, -depth * 0.55, -height * 0.03)))
    feet = panel(width * 1.1, depth * 0.55, height * 0.06)
    feet = fillet(feet.edges().filter_by(Axis.X), height * 0.015)
    body -= feet.moved(Location((-width * 0.55, -depth * 0.275, -height * 0.03)))
    for x in (-width * 0.545, width * 0.445):
        grip = panel(width * 0.10, depth * 0.58, height * 0.24)
        grip = fillet(grip.edges().filter_by(Axis.X), scale * 0.05)
        body -= grip.moved(Location((x, -depth * 0.29, height * 0.27)))
    front = panel(width * 0.70, depth * 0.08, height * 0.42)
    front = fillet(front.edges().filter_by(Axis.Y), scale * 0.12)
    body -= front.moved(Location((-width * 0.35, -depth * 0.51, height * 0.13)))
    body.label, body.color = "Red moulded body", red

    rim = Part([Solid.extrude(Face(outline(width, depth, body_top, scale * 0.14)), (0, 0, rim_top - body_top))],
               label="White rim", color=white)
    seam = Part([Solid.extrude(Face(outline(width * 0.997, depth * 0.997, rim_top, scale * 0.14)),
                               (0, 0, lid_bottom - rim_top))], label="Lid seam", color=Color(0.15, 0.13, 0.13))
    lid = Solid.make_loft([
        outline(width, depth, lid_bottom, scale * 0.14),
        outline(width * 0.90, depth * 0.82, height * 0.985, scale * 0.12),
    ], ruled=True)
    lid = fillet(lid.edges().group_by(Axis.Z)[-1], scale * 0.015)
    lid.label, lid.color = "Rounded white lid", white
    top = Solid.extrude(Face(outline(width * 0.68, depth * 0.64, height * 0.985, scale * 0.05)),
                        (0, 0, height * 0.015))
    top = fillet(top.edges(), min(scale * 0.008, height * 0.006))
    top.label, top.color = "Raised lid panel", Color(0.94, 0.93, 0.88)

    member = scale * 0.045
    handle_width, handle_depth = width + 3 * member, scale * 0.09
    pivot_z = height * 0.63
    handle_height = height - pivot_z + scale * 0.24
    handle = frame_panel(handle_width, handle_depth, handle_height,
                         [(member, handle_width - member, -4 * member, handle_height - member)], 2 * member)
    handle = fillet(handle.edges().filter_by(Axis.Y).group_by(Axis.Z)[-1], 3 * member)
    handle.location = Location((-handle_width / 2, -handle_depth / 2, 0))
    handle.label, handle.color = "White carry handle", white
    moving = Compound(label="Handle", children=[handle])
    moving.location = Location((0, 0, pivot_z), (p.chilly_bin_handle_angle_deg, 0, 0))
    pivots = []
    for side, sign in (("Left", -1), ("Right", 1)):
        start, end = width / 2 - member, handle_width / 2 + member * 0.25
        face = Face(Wire.make_circle(scale * 0.085,
                    Plane(origin=(sign * start, 0, pivot_z), z_dir=(sign, 0, 0))))
        pivots.append(Part([Solid.extrude(face, (sign * (end - start), 0, 0))],
                          label=f"{side} handle pivot", color=white))
    return Compound(label="Chilly bin", children=[body, rim, seam, lid, top, *pivots, moving])


def build_stored_gear(p: Parameters) -> Compound:
    bag = solar_panel_bag(p)
    bag.location = Location((p.solar_bag_x_mm, p.solar_bag_y_mm, p.solar_bag_z_mm), (0, 0, p.solar_bag_yaw_deg))
    chairs = []
    for number, x, y, z, yaw in (
        (1, p.chair_1_x_mm, p.chair_1_y_mm, p.chair_1_z_mm, p.chair_1_yaw_deg),
        (2, p.chair_2_x_mm, p.chair_2_y_mm, p.chair_2_z_mm, p.chair_2_yaw_deg),
    ):
        chair = folded_chair(p, f"Chair {number}")
        chair.location = Location((x, y, z), (0, 0, yaw))
        chairs.append(chair)
    bin = chilly_bin(p)
    bin.location = Location((p.chilly_bin_x_mm, p.chilly_bin_y_mm, p.chilly_bin_z_mm), (0, 0, p.chilly_bin_yaw_deg))
    return Compound(label="Stored gear", children=[bag, Compound(label="Chairs", children=chairs), bin])


def gear_motions(p: Parameters) -> dict[str, object]:
    """Use the existing live tracks: 100 units per 100 input units gives direct mm/degrees."""
    motions: dict[str, object] = {}
    for prefix, path in (
        ("solar_bag", "Solar panel bag"),
        ("chair_1", "Chairs/Chair 1"),
        ("chair_2", "Chairs/Chair 2"),
        ("chilly_bin", "Chilly bin"),
    ):
        for suffix, axis, kind in (
            ("x_mm", "x", "translation"),
            ("y_mm", "y", "translation"),
            ("z_mm", "z", "translation"),
            ("yaw_deg", "z", "rotation"),
        ):
            name = f"{prefix}_{suffix}"
            motions[name] = {
                "position": getattr(p, name),
                "tracks": [{"path": f"/Campervan/Stored gear/{path}", "axis": axis, "kind": kind, "travel": 100}],
            }
    motions["chilly_bin_handle_angle_deg"] = {
        "position": p.chilly_bin_handle_angle_deg,
        "tracks": [{"path": "/Campervan/Stored gear/Chilly bin/Handle", "axis": "x", "kind": "rotation", "travel": 100}],
    }
    return motions
