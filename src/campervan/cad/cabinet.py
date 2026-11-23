"""Lower cabinet and its separately removable upper rear bay (box 6)."""

from math import hypot

from build123d import Color, Compound, Face, Keep, Location, Part, Plane, Solid, Wire

from campervan.cad.cabinet_layout import cabinet_layout
from campervan.cad.cabinet_doors import build_cabinet_doors
from campervan.cad.cut_profiles import copy_fitting_datums, set_fitting_datums
from campervan.cad.floor import FLOOR_BASE_WIDTH_MM
from campervan.cad.panels import panel
from campervan.cad.scan_scribe_data import CABINET_SCRIBE_FLOOR_Z_MM, CABINET_SCRIBE_REAR_Y_MM
from campervan.parameters import Parameters

WOOD = Color(0.84, 0.64, 0.39)
PLYWOOD = Color(0.91, 0.80, 0.62)
# Highest registered crown in the cab-end arch band: world Z283.485mm, rounded up.
ARCH_CROWN_WORLD_Z_MM = 284.0
# Nearest wall in the complete deep-frame/backing region: X1454.492.
# Reserve 6mm plywood and at least 3mm scan clearance outside the vertical timber face.
DEEP_FRAME_OUTER_X_MM = 1445.0
# The rear bay stops aisleward of the pillar. The deeper bay begins at the shared post station.
BOX6_REAR_WALL_X_MM = 1320.0
PILLAR_ACROSS = 0.93
PILLAR_RISE = 0.33
PILLAR_PLY_DEPTH_Y = 18 * hypot(1, PILLAR_ACROSS, PILLAR_RISE)


def _pillar_wall_y(x: float, z: float) -> float:
    """Registered pillar-facing surface of the 18mm sheet in cabinet coordinates."""
    return 43.3 + PILLAR_ACROSS * (x - 1400) + PILLAR_RISE * (z - 770)


def _rear_pillar_panel(bottom: float, top: float) -> Part:
    """Fit a single 18mm sheet along the scanned pillar at the box 6 step."""
    points = [(x, _pillar_wall_y(x, z), z) for x, z in (
        (BOX6_REAR_WALL_X_MM, bottom), (DEEP_FRAME_OUTER_X_MM, bottom),
        (DEEP_FRAME_OUTER_X_MM, top), (BOX6_REAR_WALL_X_MM, top),
    )]
    face = Face(Wire.make_polygon(points))
    # Extrude toward the cabinet. The Y travel gives 18mm measured normal to the fitted face.
    sheet = Solid.extrude(face, (0, PILLAR_PLY_DEPTH_Y, 0))
    # The cabinet rear is at Y0. Plane.XZ's negative half-space faces into the cabinet.
    trimmed = sheet.split(Plane.XZ, keep=Keep.BOTTOM)
    return Part(trimmed.solids(), label="Rear pillar panel (preview)", color=PLYWOOD)


def build_cabinet(p: Parameters) -> Compound:
    if (abs(p.floor_surface_z_mm - CABINET_SCRIBE_FLOOR_Z_MM) > 0.001
            or abs(p.cabinet_rear_y_mm - CABINET_SCRIBE_REAR_Y_MM) > 0.001):
        raise ValueError("Refit the cabinet frame for the changed floor elevation or rear position.")
    layout = cabinet_layout(p)
    w, t, skin = p.cabinet_frame_width_mm, p.cabinet_frame_thickness_mm, p.cabinet_partition_thickness_mm
    first, split = layout.first, layout.split
    # Keep the complete 40mm bottom rail above the crown; preserve the old mattress door level separately.
    arch_level = max(p.arch_height_mm, ARCH_CROWN_WORLD_Z_MM) - p.floor_surface_z_mm + 3 + w
    # The owner's 1200mm floor physically fits between the arches; align the frame to its edge.
    aisle, shallow = layout.front, (p.cargo_width_mm + FLOOR_BASE_WIDTH_MM) / 2
    deep = DEEP_FRAME_OUTER_X_MM
    rear = 0.0  # Rear frame face is flush with the bed rear datum.
    middle = p.cabinet_rear_bay_length_mm + skin / 2 - w / 2
    cab = p.cabinet_length_mm - skin - w
    if not rear + w < middle < middle + w < cab or deep - shallow <= 2 * t:
        raise ValueError("Lower cabinet needs two clear bays and room for the wall-side depth extension.")
    if not w < arch_level < first - w:
        raise ValueError("The arch-clearance and mattress-access levels must leave a usable compartment.")
    parts = []

    def post(name: str, outer: float, y: float, bottom: float, top: float) -> Part:
        part = panel(w, t, top - bottom)
        part.label, part.color = name, WOOD
        part.location = Location((outer, y, bottom), (0, 0, 90))
        set_fitting_datums(part, 0, 1)
        return part

    def rail(name: str, outer: float, start: float, end: float, top: float, *,
             raked_start: bool = False, top_recess: float = 0) -> Part:
        length = end - start
        if raked_start:
            # start/end are the marks on the top edge; transfer the same post rake onto the mating end.
            shift = w * PILLAR_RISE
            outline = Wire.make_polygon([
                (-shift, 0, 0), (length, 0, 0),
                (length, 0, w - top_recess), (-top_recess * PILLAR_RISE, 0, w - top_recess),
            ])
            part = Part([Solid.extrude(Face(outline), (0, t, 0))])
        else:
            part = panel(length, t, w - top_recess)
        part.label, part.color = name, WOOD
        part.location = Location((outer, start, top - w), (0, 0, 90))
        set_fitting_datums(part, 1, 2)
        return part

    def cross(name: str, start: float, end: float, y: float, top: float, *, top_recess: float = 0) -> Part:
        part = panel(end - start, t, w - top_recess)
        part.label, part.color = name, WOOD
        part.location = Location((start, y, top - w))
        set_fitting_datums(part, 1, 2)
        return part

    # Shared posts establish the same centre line on the aisle and wall sides.
    for name, y in (("Rear", rear), ("Middle", middle), ("Cab-end", cab)):
        parts.append(post(f"{name} aisle post", aisle + t, y, 0, split))
        parts.append(post(f"{name} shallow wall post", shallow, y, 0, arch_level if name == "Cab-end" else split))
    for name, start, end in (("Rear", rear + w, middle), ("Cab-end", middle + w, cab)):
        aisle_levels = (w, split) if name == "Rear" else (w, arch_level, first, split)
        wall_levels = (w, split) if name == "Rear" else (w, arch_level - p.cabinet_shelf_thickness_mm)
        for level in aisle_levels:
            parts.append(rail(f"{name} aisle rail at {level:g}mm", aisle + t, start, end, level))
        for level in wall_levels:
            parts.append(rail(f"{name} shallow wall rail at {level:g}mm", shallow, start, end, level))

    # The centre frame stays centred; exposed end frames are flush for the future end skins.
    inset = (w - t) / 2
    parts.append(cross("Rear top cross rail", aisle + t, shallow - t, rear, split))
    for name, y in (("Middle", middle + inset), ("Cab-end", cab + w - t)):
        for level in (w, arch_level):
            parts.append(cross(f"{name} shallow cross rail at {level:g}mm", aisle + t, shallow - t, y, level))
        parts.append(cross(f"{name} depth-step bottom rail", shallow, deep - t, y, arch_level))
        for level in (first, split):
            if name == "Middle":
                parts.append(cross(f"Middle shallow cross rail at {level:g}mm", aisle + t, shallow - t, y, level))
                parts.append(cross(f"Middle deep cross rail at {level:g}mm", shallow, deep - t, y, level))
            else:
                parts.append(cross(f"Cab-end cross rail at {level:g}mm", aisle + t, deep - t, y, level))

    # Two full-depth compartments share one wall ladder above the arch. Posts and rails meet at
    # reinforced butt joints; the intermediate level retains the original mattress-access opening.
    for name, y in (("Middle", middle), ("Cab-end", cab)):
        parts.append(post(f"{name} deep wall post", deep, y, arch_level - w, split))
    for level in (arch_level, first, split):
        parts.append(rail(f"Deep wall rail at {level:g}mm", deep, middle + w, cab, level))

    # Shelves and their perimeter supports share the same inside frame boundaries.
    ledges = []
    shelves = []
    frame = Compound(parts)
    size = 18.0

    def ledge(name: str, x: float, y: float, length: float, level: float, *, along_y: bool = False) -> Part:
        part = panel(length, size, size)
        part.label, part.color = name, WOOD
        part.location = Location((x + size if along_y else x, y,
                                  level - p.cabinet_shelf_thickness_mm - size),
                                 (0, 0, 90) if along_y else (0, 0, 0))
        set_fitting_datums(part, 1, 2)
        return part

    def inset_shelf(label: str, start: float, end: float, wall: float, level: float,
                    *, clear_frame: Compound) -> Part:
        side = aisle + t
        thickness = p.cabinet_shelf_thickness_mm
        pose = Location((side, start, level - thickness))
        sheet = panel(wall - side, end - start, thickness).moved(pose)
        sheet = sheet - clear_frame
        result = Part(sheet.moved(pose.inverse()).solids(), label=label, color=PLYWOOD)
        result.location = pose
        return result

    def shelf_ledgers(label: str, start: float, end: float, wall: float, level: float,
                      end_names: tuple[str | None, str | None], *,
                      split_start: bool = False, split_end: bool = False, wall_ledger: bool = True) -> list[Part]:
        side = aisle + t
        supports = [ledge(f"{label} · Aisle ledger", side, start, end - start, level, along_y=True)]
        if wall_ledger:
            supports.append(ledge(f"{label} · Wall ledger", wall - size, start, end - start, level, along_y=True))
        left = side + size
        right = wall - size if wall_ledger else wall
        for name, y, divided in ((end_names[0], start, split_start), (end_names[1], end - size, split_end)):
            if name is None:
                continue
            spans = ((left, shallow - t), (shallow, right)) if divided else ((left, right),)
            for index, (x0, x1) in enumerate(spans, 1):
                supports.append(ledge(f"{label} · {name} side ledger {index}", x0, y, x1 - x0, level))
        return supports

    start, end, wall = middle + inset + t, cab + w - t, deep - t
    for level in (arch_level, first):
        label = f"Cab-end {level:g}mm shelf"
        shelves.append(inset_shelf(label, start, end, wall, level, clear_frame=frame))
        ledges.extend(shelf_ledgers(
            label, start, end, wall, level, ("Middle", "Cab-end"), split_start=True, split_end=level == arch_level,
        ))

    door_parts = build_cabinet_doors(
        p, ((rear + w, middle), (middle + w, cab)),
        ((w, arch_level - w), (arch_level, first - w), (first, split - w)), (w, split - w),
    )
    parts.append(Compound(label="Catch mounting blocks", children=door_parts.mounts))
    rebate_cutters = Compound(door_parts.frame_cuts)
    for index, part in enumerate(parts):
        if part.children:
            continue
        pose = part.location
        rebated = Part((part - rebate_cutters).moved(pose.inverse()).solids(), label=part.label, color=part.color)
        rebated.location = pose
        copy_fitting_datums(part, rebated)
        parts[index] = rebated

    # Two rectangular bays share a transverse frame. The shallow wall stops at the step.
    pillar_panel = _rear_pillar_panel(split, layout.upper)
    rear_wall = BOX6_REAR_WALL_X_MM

    def shoulder_y(z: float) -> float:
        # The long point of the bevel is at the inboard edge of the wall post.
        return _pillar_wall_y(deep - t, z) + PILLAR_PLY_DEPTH_Y

    step_width = w * hypot(1, PILLAR_RISE)  # Horizontal footprint of the raked stock.
    upper_frame = [post(f"Box 6 {name} post", x, y, split, layout.upper) for name, x, y in (
        ("rear aisle", aisle + t, rear), ("rear wall", rear_wall, rear),
        ("middle aisle", aisle + t, middle), ("middle wall", deep, middle),
    )]
    foot = shoulder_y(split)
    height = layout.upper - split
    # The pillar ply ends at the shallow wall. Only trim shelf material beyond that wall.
    pillar_face = Plane(origin=(deep - t, foot, split), z_dir=(-PILLAR_ACROSS, 1, -PILLAR_RISE))
    corner = panel(deep - rear_wall, middle + inset - rear, height).moved(Location((rear_wall, rear, split)))
    pillar_space = corner.split(pillar_face, keep=Keep.BOTTOM)
    footprint = Wire.make_polygon([
        (deep - t, foot, split), (deep, foot + t * PILLAR_ACROSS, split),
        (deep, foot + step_width, split), (deep - t, foot + step_width, split),
    ])
    solid = Solid.extrude(Face(footprint), (0, height * PILLAR_RISE, height))
    # Keep the cut list in the axes of the actual 40 × 18 stock.
    pose = Plane(origin=(deep - t, foot, split), x_dir=(1, 0, 0), z_dir=(0, PILLAR_RISE, 1)).location
    stile = Part([solid.moved(pose.inverse())], label="Box 6 step deep wall post", color=WOOD)
    stile.location = pose
    set_fitting_datums(stile, 0, 1)
    upper_frame.append(stile)
    upper_ledges = []
    upper_shelves = []
    # The transverse rail runs from the continuous aisle rail to the pillar-side post.
    for name, level in (("floor", split + w), ("upper shelf", layout.upper)):
        step_back = shoulder_y(level)
        step_front = step_back + step_width
        step_cross = step_front - t
        shelf_recess = p.cabinet_shelf_thickness_mm
        prefix = f"Box 6 {name}"
        upper_frame.extend([
            cross(f"{prefix} rear rail", aisle + t, rear_wall - t, rear, level),
            cross(f"{prefix} step cross rail", aisle + t, deep - t, step_cross, level,
                  top_recess=shelf_recess),
            cross(f"{prefix} middle rail", aisle + t, deep - t, middle + inset, level),
            rail(f"{prefix} aisle rail", aisle + t, rear + w, middle, level),
            rail(f"{prefix} shallow wall rail", rear_wall, rear + w, step_cross, level, top_recess=shelf_recess),
            rail(f"{prefix} deep wall rail", deep, step_front, middle, level, raked_start=True),
        ])
        for bay, wall, start, end, end_names in (
            ("shallow", rear_wall, rear + t, step_cross, ("Rear", None)),
            ("deep", deep, step_front, middle + inset, (None, "Middle")),
        ):
            label = f"{prefix} {bay} panel"
            upper_ledges.extend(shelf_ledgers(
                label, start, end, wall - t, level, end_names, wall_ledger=bay == "deep",
            ))
        upper_shelves.append(inset_shelf(
            f"{prefix} panel", rear, middle + inset, deep - t, level,
            clear_frame=Compound([*upper_frame, pillar_space]),
        ))
    upper_frame.append(Compound(label="Shelf ledges", children=upper_ledges))

    parts.append(Compound(label="Shelf ledges", children=ledges))
    return Compound(label="Cabinet", children=[
        Compound(label="Lower module", children=[
            Compound(label="Frames", children=parts), Compound(label="Shelves", children=shelves),
            door_parts.assembly,
        ]),
        Compound(label="Upper module", children=[
            Compound(label="Frames", children=upper_frame),
            Compound(label="Shelves", children=upper_shelves),
            Compound(label="Skin", children=[pillar_panel]),
        ]),
    ])
