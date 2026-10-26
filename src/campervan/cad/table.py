"""Two display poses of one single-arm Lagun table, plus their furniture mounts.

Dimensions follow Lagun's 2026 general drawing. Extrusion grooves, handles and
clamp internals are visual approximations; hole centres require the actual kit.
"""

from build123d import Align, Axis, Color, Compound, Cylinder, Location, fillet

from campervan.cad.cabinet_doors import cabinet_aisle_x
from campervan.cad.panels import panel
from campervan.parameters import Parameters

ROOT = "/Campervan/Laptop table"
MOUNTS = (("Bench mount", "table"), ("Cabinet mount", "cabinet_table"))
SILVER = Color(0.72, 0.75, 0.77)
BLACK = Color(0.12, 0.13, 0.14)
WOOD = Color(0.83, 0.70, 0.46)
LAGUN_BRACKET_WIDTH = 92.0
MOVING_FRAME_CAB_TRIM = 5.0


def mount_poses(p: Parameters) -> tuple[tuple[float, float, float], ...]:
    """Furniture-local bracket faces: outward X at bench, outward Y at cabinet.

    The bench has one frame-ply spacer, flush with the moving frame's outer face.
    The tall cabinet has a separate arm-clearance spacer and internal backing.
    """
    return (
        (p.long_bench_width_mm + p.frame_thickness_mm, p.seat_length_mm - LAGUN_BRACKET_WIDTH / 2, 0),
        (cabinet_aisle_x(p) + p.cabinet_frame_thickness_mm + 60,
         p.cabinet_length_mm + p.frame_thickness_mm + p.cross_bench_skin_thickness_mm, 90),
    )


def _mounted_table(p: Parameters, mount: int) -> Compound:
    def block(name: str, size: tuple[float, float, float], xyz: tuple[float, float, float], color=SILVER):
        part = panel(*size)
        part.label, part.color = name, color
        part.location = Location(xyz)
        return part

    def pin(name: str, radius: float, height: float, xyz: tuple[float, float, float]):
        part = Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        part.label, part.color = name, SILVER
        part.location = Location(xyz)
        return part

    label, prefix = MOUNTS[mount]
    x, y, yaw = mount_poses(p)[mount]
    t = p.frame_thickness_mm
    if mount == 0:
        backing = [block("Drawer frame spacer", (t, LAGUN_BRACKET_WIDTH,
                         p.platform_height_mm - p.slat_thickness_mm),
                         (-t, -LAGUN_BRACKET_WIDTH / 2, 0), WOOD)]
    else:
        thin = p.cross_bench_skin_thickness_mm
        offset = t + thin
        backing = [
            block("Cabinet spacer", (t, LAGUN_BRACKET_WIDTH, 190), (-offset, -46, 170), WOOD),
            block("Thin cabinet spacer", (thin, LAGUN_BRACKET_WIDTH, 190), (-thin, -46, 170), WOOD),
            block("Cabinet inside backing", (t, 120, 190),
                  (-offset - p.cabinet_frame_thickness_mm - t, -60, 170), WOOD),
        ]

    bracket = Compound(label="Lagun hardware", children=[
        block("Standard mounting bracket", (13, LAGUN_BRACKET_WIDTH, 170), (0, -46, 180)),
        block("Height clamp handle", (18, 12, 65), (13, -40, 220), BLACK),
    ])
    # 500mm upright + 7mm joint + 47mm arm + 30mm top fitting = 584mm.
    leg_bottom = getattr(p, f"{prefix}_height_mm") - 584 - p.table_ply_thickness_mm
    upright = Compound(label="Lagun hardware", children=[
        block("500mm upright", (38, 38, 500), (-19, -19, 0)),
        block("Upright groove", (2, 8, 500), (-20, -4, 0), BLACK),
        pin("Arm pivot", 17, 26, (0, 0, 493)),
    ])
    arm = block("400mm arm", (400, 38, 47), (-38, -19, 0))
    # Work on the local blank before applying its placement.
    arm = fillet(arm.located(Location()).edges().filter_by(Axis.Z), 3).moved(arm.location)
    arm.label, arm.color = "400mm arm", SILVER
    arm_hardware = Compound(label="Lagun hardware", children=[
        arm,
        block("Arm swivel handle", (65, 12, 14), (-25, -31, 15), BLACK),
        pin("Tabletop pivot", 17, 30, (324, 0, 47)),
    ])
    top = block("Laptop tabletop", (p.table_depth_mm, p.table_length_mm, p.table_ply_thickness_mm),
                (-p.table_depth_mm / 2, -p.table_length_mm / 2, 0), WOOD)
    top_hardware = Compound(label="Lagun hardware", children=[
        block("Tabletop plate", (240, 200, 4), (-120, -100, -4)),
        block("Tabletop plate centre", (56, 70, 26), (-28, -35, -30)),
        block("Tabletop rotation handle", (12, 65, 14), (28, -35, -23), BLACK),
    ])
    tabletop = Compound(label="Tabletop rotation", children=[top_hardware, top])
    tabletop.location = Location((324, 0, 77), (0, 0, getattr(p, f"{prefix}_top_rotation_deg")))
    swivel = Compound(label="Swivel arm", children=[arm_hardware, tabletop])
    swivel.location = Location((0, 0, 507), (0, 0, getattr(p, f"{prefix}_arm_swivel_deg")))
    # Preserve the arm's heading when comparing the two mounting faces.
    orientation = Compound(label="Arm orientation", children=[swivel])
    orientation.location = Location((0, 0, 0), (0, 0, -yaw))
    height = Compound(label="Height adjustment", children=[upright, orientation])
    height.location = Location((32, 0, leg_bottom))
    result = Compound(label=label, children=[
        Compound(label="Mount backing", children=backing), bracket, height,
    ])
    result.location = Location((x, y, 0), (0, 0, yaw))
    return result


def build_laptop_table(p: Parameters) -> Compound:
    # Both poses exist regardless of which is visible. Stowed geometry awaits its storage design.
    return Compound(label="Laptop table", children=[_mounted_table(p, mount) for mount in range(2)])


def table_motions(p: Parameters) -> dict[str, object]:
    # Selection is applied as group visibility in the viewer, not a CAD transform.
    motions = {"table_mount": {"position": p.table_mount, "tracks": []}}
    for label, prefix in MOUNTS:
        height = f"{ROOT}/{label}/Height adjustment"
        arm = f"{height}/Arm orientation/Swivel arm"
        for suffix, path, kind, travel in (
            ("height_mm", height, "translation", 100),
            ("arm_swivel_deg", arm, "rotation", -100),
            ("top_rotation_deg", f"{arm}/Tabletop rotation", "rotation", -100),
        ):
            name = f"{prefix}_{suffix}"
            motions[name] = {"position": getattr(p, name), "tracks": [
                {"path": path, "axis": "z", "kind": kind, "travel": travel},
            ]}
    return motions
