"""Bench-mounted Lagun table, using the current manufacturer's nominal dimensions.

Dimensions follow Lagun's 2026 general drawing. Extrusion grooves, handles and
clamp internals are visual approximations; hole centres require the actual kit.
"""

from build123d import Align, Axis, Color, Compound, Cone, Cylinder, Face, Location, Part, Solid, Wire, fillet

from campervan.cad.panels import panel
from campervan.parameters import Parameters

ROOT = "/Campervan/Laptop table"
SILVER = Color(0.72, 0.75, 0.77)
BLACK = Color(0.12, 0.13, 0.14)
WOOD = Color(0.83, 0.70, 0.46)
LAGUN_BRACKET_WIDTH = 92.0
MOVING_FRAME_CAB_TRIM = 5.0
LAGUN_TOP_LENGTH = 240.0
LAGUN_TOP_WIDTH = 200.0
LAGUN_TOP_DEPTH = 30.0
# Fosters HOM006136: open length, maximum width and width across the pins.
HOMER_LENGTH = 114.0
HOMER_WIDTH = 42.0
HOMER_PIN_WIDTH = 38.0
# Photo-based visual details, NOT machining dimensions. The supplier does not
# publish thickness, pivot centres, hole sizes/centres or a recess drawing.
HOMER_VISUAL_THICKNESS = 3.0
HOMER_VISUAL_PIVOT_OFFSET = 4.0
HOMER_VISUAL_PIN_RADIUS = 3.0


def tabletop_offset_travel(p: Parameters) -> float:
    """Keep the 240mm plate footprint inside either short edge of the tabletop."""
    return (p.table_length_mm - LAGUN_TOP_LENGTH) / 2


def tabletop_leaf(p: Parameters, label: str):
    """Round the blank before placement so its cutting outline stays pose-independent."""
    width, length, thickness = p.table_depth_mm, p.table_length_mm, p.table_ply_thickness_mm
    corner, edge = p.table_corner_radius_mm, p.table_edge_radius_mm
    if 2 * corner >= min(width, length) or 2 * edge >= min(thickness, width, length):
        raise ValueError("Tabletop corner and edge radii must fit within each bamboo leaf.")
    leaf = panel(width, length, thickness)
    if corner:
        leaf = fillet(leaf.edges().filter_by(Axis.Z), corner)
    if edge:
        leaf = fillet(leaf.edges().filter_by(Axis.Z, reverse=True), edge)
    leaf.label, leaf.color = label, Color(0.77, 0.62, 0.36)
    return leaf


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


def _upright() -> Compound:
    return Compound(label="Lagun hardware", children=[
        block("500mm upright", (38, 38, 500), (-19, -19, 0)),
        block("Upright groove", (2, 8, 500), (-20, -4, 0), BLACK),
        # USA lists 21¾ inches overall, including the tap. Its diameter and
        # handle section remain illustrative; they are not fabrication dimensions.
        pin("Arm pivot", 17, 21.75 * 25.4 - 500, (0, 0, 500)),
        block("Height clamp handle", (12, 18, 65), (-6, -40, 130), BLACK),
    ])


def _arm() -> Compound:
    arm = fillet(panel(400, 38, 47).edges().filter_by(Axis.Z), 3)
    arm.label, arm.color = "400mm arm", SILVER
    arm.location = Location((-38, -19, 0))
    return Compound(label="Lagun hardware", children=[
        arm,
        block("Arm swivel handle", (65, 12, 14), (-25, -31, 15), BLACK),
        pin("Tabletop pivot", 17, 30, (324, 0, 47)),
    ])


def _top_mount() -> Compound:
    # Published outer envelope; the dovetail section is not dimensioned.
    return Compound(label="Lagun hardware", children=[
        block("Tabletop mount · 240 × 200 × 30mm envelope",
              (LAGUN_TOP_WIDTH, LAGUN_TOP_LENGTH, LAGUN_TOP_DEPTH),
              (-LAGUN_TOP_WIDTH / 2, -LAGUN_TOP_LENGTH / 2, -LAGUN_TOP_DEPTH)),
    ])


def _homer_hinge_half(side: int) -> tuple[Compound, Part]:
    """One photo-based half at the tabletop seam, with its top face at Z=0.

    Keep the published 114 × 42mm open footprint and 38mm pin width. Other
    details and the seating solid only illustrate the selected hardware.
    """
    depth, pivot = HOMER_VISUAL_THICKNESS, HOMER_VISUAL_PIVOT_OFFSET
    outline = Wire.make_polygon([
        (side * x, y, -depth) for x, y in (
            (pivot, -HOMER_PIN_WIDTH / 2), (45, -HOMER_WIDTH / 2),
            (HOMER_LENGTH / 2, -HOMER_WIDTH / 2), (HOMER_LENGTH / 2, HOMER_WIDTH / 2),
            (45, HOMER_WIDTH / 2), (pivot, HOMER_PIN_WIDTH / 2),
        )
    ])
    blank = Part([Solid.extrude(Face(outline), (0, 0, depth))])
    blank = fillet(blank.edges().filter_by(Axis.Z), 2)
    plate = blank
    # Four countersunk holes on each half, matching the product photograph.
    # Positions and diameters are illustrative; no bamboo pilot holes are cut.
    for x in (20, 46):
        for y in (-12, 12):
            bore = Cylinder(2.2, depth + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
            sink = Cone(2.2, 4.2, 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
            plate -= bore.moved(Location((side * x, y, -depth - 1)))
            plate -= sink.moved(Location((side * x, y, -2)))
    plate.label, plate.color = "Tapered plate · approximate holes", SILVER
    barrel = Cylinder(HOMER_VISUAL_PIN_RADIUS, HOMER_PIN_WIDTH, rotation=(90, 0, 0),
                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    barrel = barrel.moved(Location((side * pivot, HOMER_PIN_WIDTH / 2, -depth)))
    barrel.label, barrel.color = "Pivot barrel · approximate section", SILVER
    bridge = block("Centre link · schematic articulation", (pivot, 14, depth),
                   (min(0, side * pivot), -7, -depth))
    # Nominal seats prevent the visual metal from overlapping the bamboo.
    # They remain blind pockets and do not change the cutting silhouette.
    seat = blank.fuse(barrel, bridge)
    hardware = Compound(label="Fixed half" if side < 0 else "Folding half", children=[plate, barrel, bridge])
    return hardware, seat


def _leaves(p: Parameters, open_percent: float) -> Compound:
    width, length, thickness = p.table_depth_mm, p.table_length_mm, p.table_ply_thickness_mm
    fixed = tabletop_leaf(p, "Fixed bamboo leaf")
    folding = tabletop_leaf(p, "Folding bamboo leaf")
    fixed_halves, folding_halves = [], []
    for number, y in enumerate((-0.3 * length, 0.3 * length), start=1):
        fixed_half, fixed_seat = _homer_hinge_half(-1)
        folding_half, folding_seat = _homer_hinge_half(1)
        fixed -= fixed_seat.moved(Location((width, y + length / 2, thickness)))
        folding -= folding_seat.moved(Location((0, y + length / 2, thickness)))
        fixed_half.label = folding_half.label = f"Homer hinge {number} · approximate details"
        fixed_half.location = Location((width / 2, y, thickness))
        folding_half.location = Location((0, y, 0))
        fixed_halves.append(fixed_half)
        folding_halves.append(folding_half)
    fixed.label, fixed.color = "Fixed bamboo leaf", Color(0.77, 0.62, 0.36)
    folding.label, folding.color = "Folding bamboo leaf", Color(0.77, 0.62, 0.36)
    fixed.location = Location((-width / 2, -length / 2, 0))
    folding.location = Location((0, -length / 2, -thickness))
    hinge = Compound(label="Folding leaf", children=[
        folding, Compound(label="Table hinges · Homer HOM006136", children=folding_halves),
    ])
    hinge.location = Location((width / 2, 0, thickness), (0, -180 * (1 - open_percent / 100), 0))
    return Compound(label="Offset tabletop", children=[
        fixed, Compound(label="Table hinges · Homer HOM006136", children=fixed_halves), hinge,
    ])


def _fixed_mount(p: Parameters) -> Compound:
    x = p.long_bench_width_mm + p.frame_thickness_mm
    y = p.seat_length_mm - LAGUN_BRACKET_WIDTH / 2
    t = p.frame_thickness_mm
    backing = [block("Drawer frame spacer", (t, LAGUN_BRACKET_WIDTH,
                     p.platform_height_mm - p.slat_thickness_mm),
                     (-t, -LAGUN_BRACKET_WIDTH / 2, 0), WOOD)]

    bracket = Compound(label="Lagun hardware", children=[
        block("Standard mounting bracket", (13, LAGUN_BRACKET_WIDTH, 170), (0, -46, 180)),
    ])
    result = Compound(label="Fixed mount", children=[Compound(label="Mount backing", children=backing), bracket])
    result.location = Location((x, y, 0))
    return result


def _mounted_table(p: Parameters) -> Compound:
    # 500mm upright + 7mm joint + 47mm arm + 30mm top fitting = 584mm.
    leg_bottom = p.table_height_mm - 584 - p.table_ply_thickness_mm
    offset_top = _leaves(p, p.table_fold_open_percent)
    offset_top.location = Location((0, -tabletop_offset_travel(p) * p.table_top_offset_percent / 100, 0))
    tabletop = Compound(label="Tabletop rotation", children=[_top_mount(), offset_top])
    tabletop.location = Location((324, 0, 77), (0, 0, p.table_top_rotation_deg))
    swivel = Compound(label="Swivel arm", children=[_arm(), tabletop])
    swivel.location = Location((0, 0, 507), (0, 0, p.table_arm_swivel_deg))
    orientation = Compound(label="Arm orientation", children=[swivel])
    height = Compound(label="Height adjustment", children=[_upright(), orientation])
    height.location = Location((32, 0, leg_bottom))
    result = Compound(label="Bench mount", children=[height])
    result.location = Location((p.long_bench_width_mm + p.frame_thickness_mm,
                                p.seat_length_mm - LAGUN_BRACKET_WIDTH / 2, 0))
    return result


def _stowed_table(p: Parameters) -> Compound:
    # Arm stays on the tabletop pivot and swivels along its length. The upright
    # detaches and lies alongside, with its groove facing the tabletop channel.
    # The solid plate envelope stands in for that undimensioned channel.
    leaves = _leaves(p, 0)
    offset = -tabletop_offset_travel(p) * p.table_top_offset_percent / 100
    leaves.location = Location((0, offset, 0))
    arm = _arm()
    arm.location = Location((-324, 0, -77))
    stored_arm = Compound(label="Stored arm", children=[arm])
    stored_arm.location = Location((0, 0, 0), (0, 0, 90 if p.table_top_offset_percent >= 0 else -90))
    upright = _upright()
    upright.location = Location((0, 0, 0), (0, 0, -90))
    alignment = Compound(label="Leg alignment", children=[upright])
    alignment.location = Location((-55, 250, -49), (90, 0, 0))
    stored_leg = Compound(label="Stored upright", children=[alignment])
    stored_leg.location = Location((0, offset, 0))
    packed = Compound(label="Packed tabletop", children=[leaves, _top_mount(), stored_arm, stored_leg])
    # Upright preview: 250mm high, with the wood and hardware normal to X.
    packed.location = Location((0, 0, p.table_depth_mm / 2), (0, 90, 0))
    heading = Compound(label="Facing", children=[packed])
    heading.location = Location((0, 0, 0), (0, 0, -p.table_stowed_yaw_deg))
    result = Compound(label="Stowed", children=[heading])
    result.location = Location((p.cargo_width_mm - p.table_stowed_x_mm,
                                p.table_stowed_y_mm - p.furniture_rear_gap_mm, p.table_stowed_z_mm))
    return result


def build_laptop_table(p: Parameters) -> Compound:
    return Compound(label="Laptop table", children=[_fixed_mount(p), _mounted_table(p), _stowed_table(p)])


def table_motions(p: Parameters) -> dict[str, object]:
    # Selection is applied as group visibility in the viewer, not a CAD transform.
    motions = {"table_mount": {"position": p.table_mount, "tracks": []}}
    height = f"{ROOT}/Bench mount/Height adjustment"
    arm = f"{height}/Arm orientation/Swivel arm"
    for name, path, axis, kind, travel in (
        ("table_height_mm", height, "z", "translation", 100),
        ("table_arm_swivel_deg", arm, "z", "rotation", -100),
        ("table_top_rotation_deg", f"{arm}/Tabletop rotation", "z", "rotation", -100),
        ("table_top_offset_percent", f"{arm}/Tabletop rotation/Offset tabletop", "y", "translation",
         -tabletop_offset_travel(p)),
        ("table_stowed_x_mm", f"{ROOT}/Stowed", "x", "translation", 100),
        ("table_stowed_y_mm", f"{ROOT}/Stowed", "y", "translation", 100),
        ("table_stowed_z_mm", f"{ROOT}/Stowed", "z", "translation", 100),
        ("table_stowed_yaw_deg", f"{ROOT}/Stowed/Facing", "z", "rotation", 100),
    ):
        motions[name] = {"position": getattr(p, name), "tracks": [
            {"path": path, "axis": axis, "kind": kind, "travel": travel},
        ]}
    for child in ("Offset tabletop", "Stored upright"):
        motions["table_top_offset_percent"]["tracks"].append({
            "path": f"{ROOT}/Stowed/Facing/Packed tabletop/{child}",
            "axis": "y", "kind": "translation", "travel": -tabletop_offset_travel(p),
        })
    # The arm extends from its tabletop pivot towards the displaced wood.
    # Angles here are reflected into viewer coordinates, as with the other tracks.
    motions["table_top_offset_percent"]["tracks"].append({
        "path": f"{ROOT}/Stowed/Facing/Packed tabletop/Stored arm",
        "axis": "z", "kind": "rotation", "interpolation": "step",
        "keyframes": [(-100, 90), (0, -90), (100, -90)],
    })
    # Absolute Euler tracks keep the fold above the fixed leaf, including when
    # a cached 180° pose decomposes into rotations about X and Z instead of Y.
    fold = f"{arm}/Tabletop rotation/Offset tabletop/Folding leaf"
    motions["table_fold_open_percent"] = {
        "position": p.table_fold_open_percent,
        "tracks": [{"path": fold, "axis": axis, "kind": "rotation",
                    "keyframes": [(0, 180 if axis == "y" else 0), (100, 0)]}
                   for axis in ("x", "y", "z")],
    }
    return motions
