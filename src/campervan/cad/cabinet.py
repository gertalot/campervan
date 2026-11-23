"""One lower carcass: a rear bay and three stacked cab-end compartments."""

from build123d import Color, Compound, Location, Part

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

    def post(name: str, outer: float, y: float, bottom: float, top: float) -> None:
        part = panel(w, t, top - bottom)
        part.label, part.color = name, WOOD
        part.location = Location((outer, y, bottom), (0, 0, 90))
        set_fitting_datums(part, 0, 1)
        parts.append(part)

    def rail(name: str, outer: float, start: float, end: float, top: float) -> None:
        part = panel(end - start, t, w)
        part.label, part.color = name, WOOD
        part.location = Location((outer, start, top - w), (0, 0, 90))
        set_fitting_datums(part, 1, 2)
        parts.append(part)

    def cross(name: str, start: float, end: float, y: float, top: float) -> None:
        part = panel(end - start, t, w)
        part.label, part.color = name, WOOD
        part.location = Location((start, y, top - w))
        set_fitting_datums(part, 1, 2)
        parts.append(part)

    # Shared posts establish the same centre line on the aisle and wall sides.
    for name, y in (("Rear", rear), ("Middle", middle), ("Cab-end", cab)):
        post(f"{name} aisle post", aisle + t, y, 0, split)
        post(f"{name} shallow wall post", shallow, y, 0, arch_level if name == "Cab-end" else split)
    for name, start, end in (("Rear", rear + w, middle), ("Cab-end", middle + w, cab)):
        aisle_levels = (w, split) if name == "Rear" else (w, arch_level, first, split)
        wall_levels = (w, split) if name == "Rear" else (w, arch_level - p.cabinet_shelf_thickness_mm)
        for level in aisle_levels:
            rail(f"{name} aisle rail at {level:g}mm", aisle + t, start, end, level)
        for level in wall_levels:
            rail(f"{name} shallow wall rail at {level:g}mm", shallow, start, end, level)

    # The centre frame stays centred; exposed end frames are flush for the future end skins.
    inset = (w - t) / 2
    cross("Rear top cross rail", aisle + t, shallow - t, rear, split)
    for name, y in (("Middle", middle + inset), ("Cab-end", cab + w - t)):
        for level in (w, arch_level):
            cross(f"{name} shallow cross rail at {level:g}mm", aisle + t, shallow - t, y, level)
        cross(f"{name} depth-step bottom rail", shallow, deep - t, y, arch_level)
        for level in (first, split):
            if name == "Middle":
                cross(f"Middle shallow cross rail at {level:g}mm", aisle + t, shallow - t, y, level)
                cross(f"Middle deep cross rail at {level:g}mm", shallow, deep - t, y, level)
            else:
                cross(f"Cab-end cross rail at {level:g}mm", aisle + t, deep - t, y, level)

    # Two full-depth compartments share one wall ladder above the arch. Posts and rails meet at
    # reinforced butt joints; the intermediate level retains the original mattress-access opening.
    for name, y in (("Middle", middle), ("Cab-end", cab)):
        post(f"{name} deep wall post", deep, y, arch_level - w, split)
    for level in (arch_level, first, split):
        rail(f"Deep wall rail at {level:g}mm", deep, middle + w, cab, level)

    # Shelves and their perimeter supports share the same inside frame boundaries.
    ledges = []
    shelves = []
    frame = Compound(parts)
    size = 18.0

    def ledge(name: str, x: float, y: float, length: float, level: float, *, along_y: bool = False) -> None:
        part = panel(length, size, size)
        part.label, part.color = name, WOOD
        part.location = Location((x + size if along_y else x, y,
                                  level - p.cabinet_shelf_thickness_mm - size),
                                 (0, 0, 90) if along_y else (0, 0, 0))
        set_fitting_datums(part, 1, 2)
        ledges.append(part)

    for bay, start, end, wall, levels in (
        ("Cab-end", middle + inset + t, cab + w - t, deep - t, (arch_level, first, split)),
        ("Rear", rear + t, middle + inset, shallow - t, (split,)),
    ):
        for level in levels:
            label = f"{bay} {level:g}mm shelf"
            blank = panel(wall - aisle - t, end - start, p.cabinet_shelf_thickness_mm)
            pose = Location((aisle + t, start, level - p.cabinet_shelf_thickness_mm))
            blank.location = pose
            # Fit around retained posts with open edge cutouts, keeping one constant-thickness sheet.
            shelf = Part((blank - frame).moved(pose.inverse()).solids(), label=label, color=PLYWOOD)
            shelf.location = pose
            shelves.append(shelf)
            for name, x in (("Aisle", aisle + t), ("Wall", wall - size)):
                ledge(f"{label} · {name} ledger", x, start, end - start, level, along_y=True)
            # Butt side ledgers between the longitudinal supports. Leave the retained posts intact.
            left, right = aisle + t + size, wall - size
            if bay == "Cab-end":
                middle_segments = ((left, shallow - t), (shallow, right))
                cab_segments = middle_segments if level == arch_level else ((left, right),)
                sides = (("Middle", middle + inset + t, middle_segments),
                         ("Cab-end", cab + w - t - size, cab_segments))
            else:
                sides = (("Rear", rear + t, ((left, right),)),
                         ("Middle", middle + inset - size, ((left, right),)))
            for name, y, segments in sides:
                for index, (x0, x1) in enumerate(segments, 1):
                    ledge(f"{label} · {name} side ledger {index}", x0, y, x1 - x0, level)
    parts.append(Compound(label="Shelf ledges", children=ledges))

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

    return Compound(label="Cabinet", children=[
        Compound(label="Lower module", children=[
            Compound(label="Frames", children=parts), Compound(label="Shelves", children=shelves),
            door_parts.assembly,
        ])
    ])
