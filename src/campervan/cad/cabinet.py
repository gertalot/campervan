"""Lower cabinet and the removable upper frame shared by boxes 4–7."""

from collections.abc import Sequence

from build123d import Color, Compound, Location, Part, Solid

from campervan.cad.cabinet_catches import MOUNT_HEIGHT
from campervan.cad.cabinet_layout import cabinet_layout
from campervan.cad.cabinet_modules import module_fasteners
from campervan.cad.cabinet_doors import CabinetDoors, build_cabinet_doors
from campervan.cad.cabinet_upper import (
    BOX8_POST_TOP_WORLD_Z_MM, REAR_END_SKIN_WALL_X_MM, cab_pillar_backing_waste, end_skin_waste,
    rear_backing_roof_waste, rear_face_clearance,
)
from campervan.cad.cut_profiles import copy_fitting_datums, set_fitting_datums
from campervan.cad.floor import FLOOR_BASE_WIDTH_MM
from campervan.cad.panels import panel
from campervan.cad.scan_scribe_data import CABINET_SCRIBE_FLOOR_Z_MM, CABINET_SCRIBE_REAR_Y_MM
from campervan.parameters import Parameters

WOOD = Color(0.84, 0.64, 0.39)
PLYWOOD = Color(0.91, 0.80, 0.62)
# Highest registered crown in the cab-end arch band: world Z283.485mm, rounded up.
ARCH_CROWN_WORLD_Z_MM = 284.0
# Finished wall-side plywood faces in construction coordinates.
DEEP_BACK_OUTER_X_MM = 1448.0
BOX6_REAR_BACK_OUTER_X_MM = 1323.0
BOX6_PILLAR_RETURN_OUTER_Y_MM = 157.0
BOX5_BACK_OUTER_X_MM = 1359.0
BOX5_TOP_WORLD_Z_MM = 1258.0
# Rear face of the full-height compartment clears the rear roof beam on the slide-in path.
BOX7_MIN_REAR_Y_MM = 300.0
# The aisle jamb can reach farther rearward under the roof beam than the wall corner.
BOX7_AISLE_REAR_Y_MM = 235.0


def build_cabinet(p: Parameters) -> Compound:
    if (min(abs(p.floor_surface_z_mm - z) for z in (CABINET_SCRIBE_FLOOR_Z_MM, 20.0)) > 0.001
            or abs(p.cabinet_rear_y_mm - CABINET_SCRIBE_REAR_Y_MM) > 0.001):
        raise ValueError("Refit the cabinet frame for the changed floor elevation or rear position.")
    layout = cabinet_layout(p)
    w, t, skin = p.cabinet_frame_width_mm, p.cabinet_frame_thickness_mm, p.cabinet_partition_thickness_mm
    first, split = layout.first, layout.split
    # Keep the complete 40mm bottom rail above the crown; preserve the old mattress door level separately.
    arch_level = max(p.arch_height_mm, ARCH_CROWN_WORLD_Z_MM) - p.floor_surface_z_mm + 3 + w
    # The owner's 1200mm floor physically fits between the arches; align the frame to its edge.
    aisle, shallow = layout.front, (p.cargo_width_mm + FLOOR_BASE_WIDTH_MM) / 2
    deep = DEEP_BACK_OUTER_X_MM - skin
    rear = 0.0  # Rear frame face is flush with the bed rear datum.
    middle, cab = layout.bays[0][1], layout.bays[1][1]
    if not rear + w < middle < middle + w < cab or deep - shallow <= 2 * t:
        raise ValueError("Lower cabinet needs two clear bays and room for the wall-side depth extension.")
    if not w < arch_level < first - w:
        raise ValueError("The arch-clearance and mattress-access levels must leave a usable compartment.")
    parts = []

    def post(name: str, outer: float, y: float, bottom: float, top: float, *, transverse: bool = False,
             roof_waste: Solid | None = None) -> Part:
        pose = (Location((outer - w, y, bottom)) if transverse
                else Location((outer, y, bottom), (0, 0, 90)))
        part = panel(w, t, top - bottom)
        if roof_waste is not None:
            part = Part((part - roof_waste.moved(pose.inverse())).solids())
        part.label, part.color = name, WOOD
        part.location = pose
        set_fitting_datums(part, 0, 1)
        return part

    def rail(name: str, outer: float, start: float, end: float, top: float) -> Part:
        part = panel(end - start, t, w)
        part.label, part.color = name, WOOD
        part.location = Location((outer, start, top - w), (0, 0, 90))
        set_fitting_datums(part, 1, 2)
        return part

    def cross(name: str, start: float, end: float, y: float, top: float) -> Part:
        part = panel(end - start, t, w)
        part.label, part.color = name, WOOD
        part.location = Location((start, y, top - w))
        set_fitting_datums(part, 1, 2)
        return part

    # The two shallow posts under the deep compartments sit directly beneath their cross rails.
    rail_y = middle + (w - t) / 2
    # The aisle stiles conceal each end sheet. Cross frames sit against the plywood's inside face.
    rear_end_y = rear + skin
    cab_end_y = cab + w - skin - t
    for name, y in (("Rear", rear), ("Middle", middle), ("Cab-end", cab)):
        parts.append(post(f"{name} aisle post", aisle + t, y, 0, split))
    parts.append(post("Rear shallow wall post", shallow, rear_end_y, 0, split, transverse=True))
    for name, y in (("Middle", rail_y), ("Cab-end", cab_end_y)):
        parts.append(post(f"{name} shallow wall post", shallow, y, 0, arch_level - w, transverse=True))
        parts.append(cross(f"{name} shallow cross rail at {w:g}mm", aisle + t, shallow - w, y, w))
        for level in (arch_level, first, split):
            parts.append(cross(f"{name} cross rail at {level:g}mm", aisle + t, deep - w, y, level))
    parts.append(cross("Rear top cross rail", aisle + t, shallow - w, rear_end_y, split))
    for name, start, end, levels in (
        ("Rear", rear + w, middle, (w, split)),
        ("Cab-end", middle + w, cab, (w, arch_level, first, split)),
    ):
        for level in levels:
            parts.append(rail(f"{name} aisle rail at {level:g}mm", aisle + t, start, end, level))
    for name, start, end, levels in (
        ("Rear", rear_end_y + t, rail_y, (w, split)),
        ("Cab-end", rail_y + t, cab_end_y, (w,)),
    ):
        for level in levels:
            parts.append(rail(f"{name} shallow wall rail at {level:g}mm", shallow, start, end, level))

    # Two full-depth compartments share one wall ladder above the arch. Posts and rails meet at
    # reinforced butt joints; the intermediate level retains the original mattress-access opening.
    for name, y in (("Middle", rail_y), ("Cab-end", cab_end_y)):
        parts.append(post(f"{name} deep wall post", deep, y, arch_level - w, split, transverse=True))
    for level in (arch_level, first, split):
        parts.append(rail(f"Deep wall rail at {level:g}mm", deep, rail_y + t, cab_end_y, level))

    # Shelves and their perimeter supports share the same inside frame boundaries.
    ledges = []
    shelves = []
    frame = Compound(parts)
    size = 18.0
    ledger_drop = p.cabinet_shelf_thickness_mm + size

    def cleat(name: str, x: float, y: float, length: float, bottom: float, *, along_y: bool = False) -> Part:
        part = panel(length, size, size)
        part.label, part.color = name, WOOD
        part.location = Location((x + size if along_y else x, y, bottom),
                                 (0, 0, 90) if along_y else (0, 0, 0))
        set_fitting_datums(part, 1, 2)
        return part

    def skin_sheet(name: str, length: float, height: float, pose: Location, clear: Sequence[Part | Solid]) -> Part:
        sheet = panel(length, skin, height)
        if clear:
            sheet = sheet - Compound(clear).moved(pose.inverse())
        result = Part(sheet.solids(), label=name, color=PLYWOOD)
        result.location = pose
        return result

    def divider(name: str, x: float, end: float, y: float, bottom: float, top: float,
                *, clear: Sequence[Part | Solid] = ()) -> Part:
        return skin_sheet(name, end - x, top - bottom, Location((x, y, bottom)), clear)

    def backing(name: str, x: float, start: float, end: float, bottom: float, top: float,
                *, clear: Sequence[Part | Solid] = ()) -> Part:
        pose = Location((x + skin, start, bottom), (0, 0, 90))
        return skin_sheet(name, end - start, top - bottom, pose, clear)

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

    lower_doors = build_cabinet_doors(
        p, "Lower module", tuple((middle + w, cab, sill, head) for sill, head in
                                 ((w, arch_level - w), (arch_level, first - w), (first, split - w))),
        fixed_cover=(rear + w, middle, w, split - w), cover_label="Cabinet 3 fixed cover",
    )
    box5_top = min(layout.top, BOX5_TOP_WORLD_Z_MM - p.floor_surface_z_mm)
    # The post and its bearer share a station just clear of the box 6 catch block.
    box6_catch_end = (rear + w + middle + MOUNT_HEIGHT) / 2
    box7_rear = max(BOX7_MIN_REAR_Y_MM, box6_catch_end)
    step_y = BOX6_PILLAR_RETURN_OUTER_Y_MM + skin
    if not step_y + t < BOX7_AISLE_REAR_Y_MM < box7_rear < middle - w:
        raise ValueError("Box 7 needs space over the deep part of box 6 for its rear frame and aisle opening.")
    upper_doors = build_cabinet_doors(
        p, "Upper module", ((rear + w, middle, split + w, layout.upper - w),
                            (middle + w, cab, split + w, layout.upper - w),
                            (middle + w, cab, layout.upper, box5_top - w),
                            (BOX7_AISLE_REAR_Y_MM + w, middle, layout.upper, box5_top - w)),
        fixed_cover=(rear + w, BOX7_AISLE_REAR_Y_MM, layout.upper, box5_top),
        cover_label="Box 8 fixed front", roof_clearance=rear_face_clearance(p),
    )
    catch_bounds = sorted((mount.bounding_box() for mount in lower_doors.mounts + upper_doors.mounts),
                          key=lambda bounds: bounds.min.Y)

    def shelf_ledgers(label: str, start: float, end: float, wall: float, level: float,
                      end_names: tuple[str, str], *, ends_to_rail: bool = False) -> list[Part]:
        side = aisle + t
        bottom = level - ledger_drop
        # Square-cut the ledger either side of each block mounted on the same rail.
        spans = []
        cursor = start
        blocks = [b for b in catch_bounds if b.min.Z < bottom + size and b.max.Z > bottom
                  and b.min.Y < end and b.max.Y > start]
        for block in blocks:
            if block.max.Y <= cursor:
                continue
            if cursor < block.min.Y:
                spans.append((cursor, block.min.Y))
            cursor = max(cursor, block.max.Y)
        if cursor < end:
            spans.append((cursor, end))
        supports = []
        for index, (y0, y1) in enumerate(spans, 1):
            suffix = f" {index}" if len(spans) > 1 else ""
            supports.append(cleat(f"{label} · Aisle ledger{suffix}", side, y0, y1 - y0, bottom, along_y=True))
        y0, y1 = (start + size, end - size) if ends_to_rail else (start, end)
        supports.append(cleat(f"{label} · Wall ledger", wall - size, y0, y1 - y0, bottom, along_y=True))
        right = wall if ends_to_rail else wall - size
        for name, y in ((end_names[0], start), (end_names[1], end - size)):
            # A catch block at this corner projects farther into the shelf than the aisle ledger.
            left = max([side + size] + [b.max.X for b in blocks if b.min.Y < y + size and b.max.Y > y])
            supports.append(cleat(f"{label} · {name} side ledger 1", left, y, right - left, bottom))
        return supports

    start, end, wall = rail_y + t, cab_end_y, deep - t
    for level in (arch_level, first):
        label = f"Cab-end {level:g}mm shelf"
        shelves.append(inset_shelf(label, start, end, wall, level, clear_frame=frame))
        ledges.extend(shelf_ledgers(label, start, end, wall, level, ("Middle", "Cab-end")))

    rear_wall = BOX6_REAR_BACK_OUTER_X_MM - skin
    # Measure from the common exposed timber. The box 4 wall post stands on its floor rail.
    bolt_inset = 40.0
    aisle_bolt = aisle + t + bolt_inset
    middle_wall_bolt = deep - w - bolt_inset
    bolt_centres = []
    for y, wall_bolt in ((rear_end_y, min(shallow, rear_wall) - w - bolt_inset),
                         (rail_y, middle_wall_bolt), (cab_end_y, middle_wall_bolt)):
        if wall_bolt - aisle_bolt < bolt_inset:
            raise ValueError("The cabinet cross rails need room for two module bolts clear of their end joints.")
        bolt_centres.extend(((aisle_bolt, y + t / 2), (wall_bolt, y + t / 2)))
    bores, bolts = module_fasteners(p, split, bolt_centres)

    def machine_frame(timbers: list[Part], doors: CabinetDoors) -> None:
        cutters = Compound([*doors.frame_cuts, *bores])
        for index, part in enumerate(timbers):
            pose = part.location
            machined = Part((part - cutters).moved(pose.inverse()).solids(), label=part.label, color=part.color)
            machined.location = pose
            copy_fitting_datums(part, machined)
            timbers[index] = machined
        timbers.append(Compound(label="Catch mounting blocks", children=doors.mounts))

    machine_frame(parts, lower_doors)
    parts.append(Compound(label="Module fasteners", children=bolts))

    # Two rectangular bays share a transverse frame. The shallow wall stops at the step.
    if not rear + w < step_y < middle - w:
        raise ValueError("Box 6 needs room for both wall rails at the rear pillar step.")
    upper_frame = [
        post("Box 6 rear wall post", rear_wall, rear_end_y, split, layout.upper, transverse=True),
        post("Box 6 middle wall post", deep, rail_y, split, layout.upper - w, transverse=True),
        post("Box 6 step deep wall post", deep, step_y, split, layout.upper - w, transverse=True),
    ]
    # Box 4 uses the existing middle aisle post and both middle cross rails.
    upper_frame.extend([
        post("Box 6 rear aisle post", aisle + t, rear, split, BOX8_POST_TOP_WORLD_Z_MM - p.floor_surface_z_mm),
        post("Box 6 middle aisle post", aisle + t, middle, split, box5_top),
        post("Box 4 cab-end wall post", deep, cab_end_y, split + w, layout.upper - w, transverse=True),
        post("Box 4 cab-end aisle post", aisle + t, cab, split, box5_top),
    ])
    upper_ledges = []
    upper_shelves = []
    wall5 = BOX5_BACK_OUTER_X_MM - skin
    shallow_roof, return_roof, upper_roof, upright_roof = rear_backing_roof_waste(p, rear_wall, wall5, step_y)
    upper_frame.extend([
        post("Box 8 pillar step upright", wall5, step_y, layout.upper, box5_top,
             transverse=True, roof_waste=upright_roof),
        cross("Box 6 upper shelf bearer for box 7", aisle + t, wall5 - t, box7_rear, layout.upper),
        post("Box 7 rear wall upright", wall5, box7_rear, layout.upper, box5_top - w, transverse=True),
    ])
    # The upper cross rails bear on the deep posts; the floor rails butt into their sides.
    for name, level in (("floor", split + w), ("upper shelf", layout.upper)):
        prefix = f"Box 6 {name}"
        upper_level = name == "upper shelf"
        wall_rail_x = wall5 if upper_level else deep
        cross_end = deep if upper_level else deep - w
        upper_frame.extend([
            cross(f"{prefix} rear rail", aisle + t, rear_wall - w, rear_end_y, level),
            cross(f"{prefix} step cross rail", aisle + t, cross_end, step_y, level),
            cross(f"{prefix} middle rail", aisle + t, cross_end, rail_y, level),
            rail(f"{prefix} aisle rail", aisle + t, rear + w, middle, level),
            rail(f"{prefix} shallow wall rail", rear_wall, rear_end_y + t, step_y, level),
            rail(f"{prefix} deep wall rail", wall_rail_x, step_y + t, rail_y, level),
        ])
        shallow_label, deep_label = f"{prefix} shallow panel", f"{prefix} deep panel"
        openings = [(shallow_label, "Box 8 rear shelf" if upper_level else shallow_label,
                     rear_end_y + t, step_y, rear_wall, ("Rear", "Step"))]
        if upper_level:
            openings.extend([
                (f"{deep_label} rear section", "Box 8 forward shelf", step_y + t, box7_rear,
                 wall_rail_x, ("Step", "Bearer")),
                (deep_label, "Box 7 shelf", box7_rear + t, rail_y, wall_rail_x, ("Bearer", "Middle")),
            ])
        else:
            openings.append((deep_label, deep_label, step_y + t, rail_y, wall_rail_x, ("Step", "Middle")))
        shelf_frame = Compound([*upper_frame, *upper_doors.mounts])
        for ledger_label, shelf_label, start, end, wall, end_names in openings:
            upper_ledges.extend(shelf_ledgers(ledger_label, start, end, wall - t, level, end_names,
                                              ends_to_rail=upper_level))
            upper_shelves.append(inset_shelf(shelf_label, start, end, wall - t, level, clear_frame=shelf_frame))

    # Box 5 shares box 4's shelf and sill. Its wall posts land on the two transverse
    # rails below the shelf, with their entire 40 × 18mm end faces on timber.
    start, end = rail_y + t, cab_end_y
    upper_frame.extend([
        post("Box 5 middle wall upright", wall5, rail_y, layout.upper, box5_top - w, transverse=True),
        post("Box 5 cab-end wall upright", wall5, end, layout.upper, box5_top - w, transverse=True),
        cross("Box 5 upper shelf middle rail", aisle + t, wall5, rail_y, box5_top),
        cross("Box 5 upper shelf cab-end rail", aisle + t, wall5, end, box5_top),
        rail("Box 5 upper shelf aisle rail", aisle + t, middle + w, cab, box5_top),
        rail("Box 5 upper shelf wall rail", wall5, start, end, box5_top),
        post("Box 7 rear aisle post", aisle + t, BOX7_AISLE_REAR_Y_MM, layout.upper, box5_top),
        cross("Box 7 upper shelf rear rail", aisle + t, wall5, box7_rear, box5_top),
        rail("Box 7 upper shelf aisle rail", aisle + t, BOX7_AISLE_REAR_Y_MM + w, middle, box5_top),
        rail("Box 7 upper shelf wall rail", wall5, box7_rear + t, rail_y, box5_top),
    ])
    for prefix, level in (("Box 4 floor", split + w), ("Box 4 upper shelf", layout.upper)):
        wall = wall5 if level == layout.upper else deep
        shelf_wall = wall - t
        upper_frame.extend([
            cross(f"{prefix} cab-end rail", aisle + t, deep, end, level),
            rail(f"{prefix} aisle rail", aisle + t, middle + w, cab, level),
            rail(f"{prefix} wall rail", wall, start, end, level),
        ])
        upper_ledges.extend(shelf_ledgers(prefix, start, end, shelf_wall, level, ("Middle", "Cab-end"),
                                          ends_to_rail=level == layout.upper))
        upper_shelves.append(inset_shelf(
            f"{prefix} panel", start, end, shelf_wall, level, clear_frame=Compound([*upper_frame, *upper_doors.mounts]),
        ))
    machine_frame(upper_frame, upper_doors)
    upper_frame.append(Compound(label="Shelf ledges", children=upper_ledges))

    # The two sheets meet above the arch. The top wall rail crosses the corner of the extension.
    extension = divider("Above-arch centre divider", shallow - t, deep - t, rail_y - skin, arch_level - w, split)
    relief = panel(t, skin, w).moved(Location((0, 0, split - arch_level)))
    trimmed = Part((extension.located(Location()) - relief).solids(), label=extension.label, color=PLYWOOD)
    trimmed.location = extension.location
    # The box 1 back meets the inside face of the shallow wall rails.
    shallow_back = shallow - t - skin
    cab_face = cab_end_y + t
    side = aisle + t
    rear_end_waste, cab_end_waste = end_skin_waste(p, rear, cab_face)
    lower_skin = [
        divider("Lower cab end skin", side, p.cargo_width_mm, cab_face, 0, split, clear=(cab_end_waste,)),
        divider("Box 3 centre divider", aisle + t, shallow - t, rail_y - skin, 0, split),
        trimmed,
        backing("Box 1 backing", shallow_back, rail_y + t, cab_end_y, 0,
                arch_level - p.cabinet_shelf_thickness_mm, clear=ledges),
        backing("Box 2 backing", deep, rail_y, cab_face, arch_level - w, split),
    ]
    def backing_cleat(label: str, x: float, y: float, bottom: float, top: float) -> Part:
        timber = panel(size, size, top - bottom)
        timber.label, timber.color = label, WOOD
        timber.location = Location((x, y, bottom))
        set_fitting_datums(timber, 0, 1)
        return timber

    # Box 1 has no shallow top rail. Give each end of its back a glue face on the shallow post.
    backing_cleats = [backing_cleat(f"Box 1 {name} backing cleat", shallow - t, y, w, arch_level - w)
                     for name, y in (("middle", rail_y + t), ("cab-end", cab_end_y - size))]
    parts.append(Compound(label="Backing glue cleats", children=backing_cleats))
    # World Z1147 keeps the square end clear of the pillar through the 329mm installation slide.
    step_cleat = backing_cleat("Box 6 pillar corner backing cleat", rear_wall + skin, step_y - skin - size,
                               split, 1147 - p.floor_surface_z_mm)
    front_cleat = cleat("Box 8 fixed front sill cleat", aisle + p.cabinet_door_thickness_mm, rear + w,
                        BOX7_AISLE_REAR_Y_MM - (rear + w), layout.upper, along_y=True)
    upper_frame.append(Compound(label="Backing glue cleats", children=[step_cleat, front_cleat]))
    sill, head = split + w, layout.upper - w
    # Above box 6 the return only bridges the shallow back to the boxes 5/7 wall plane.
    return_waste = panel(deep - wall5, skin, box5_top - layout.upper).moved(
        Location((wall5 + skin, step_y - skin, layout.upper)))
    # One square notch clears both the middle cross beam and the divider fixed to its rear face.
    divider_allowance = panel(skin, skin, w).moved(Location((wall5, rail_y - skin, head)))
    upper_skin = [
        divider("Upper rear end skin", side, REAR_END_SKIN_WALL_X_MM, rear, split,
                BOX8_POST_TOP_WORLD_Z_MM - p.floor_surface_z_mm, clear=(rear_end_waste,)),
        divider("Upper cab end skin", side, p.cargo_width_mm, cab_face, split, box5_top, clear=(cab_end_waste,)),
        divider("Box 4 centre divider", aisle + t, deep - t, rail_y - skin, sill, layout.upper - ledger_drop,
                clear=upper_frame),
        divider("Box 5 centre divider", aisle + t, wall5 - t, rail_y - skin, layout.upper, box5_top - ledger_drop),
        backing("Box 6 shallow backing", rear_wall, rear_end_y, step_y, split, box5_top, clear=(shallow_roof,)),
        divider("Box 6 pillar step return", rear_wall + skin, deep + skin, step_y - skin, split, box5_top,
                clear=(return_roof, return_waste)),
        backing("Boxes 4 and 6 deep backing", deep, step_y, cab_face, split, layout.upper,
                clear=(cab_pillar_backing_waste(p),)),
        backing("Boxes 5 and 7 backing", wall5, step_y, cab_face, head, box5_top,
                clear=(upper_roof, divider_allowance, *upper_frame)),
    ]
    stops = [cleat("Box 5 sill divider stop", aisle + t, rail_y, wall5 - w - (aisle + t), layout.upper)]
    # Keep the sill stop in one piece between the nuts, with room at each end for a socket.
    socket_clearance = 15.0
    stops.append(cleat("Sill divider stop", aisle_bolt + socket_clearance, rail_y,
                       middle_wall_bolt - aisle_bolt - 2 * socket_clearance, sill))
    stops.append(cleat("Head divider stop", aisle + t, rail_y, deep - w - (aisle + t), head - size))
    upper_frame.append(Compound(label="Divider stops", children=stops))

    parts.append(Compound(label="Shelf ledges", children=ledges))
    return Compound(label="Cabinet", children=[
        Compound(label="Lower module", children=[
            Compound(label="Frames", children=parts), Compound(label="Shelves", children=shelves),
            Compound(label="Skin", children=lower_skin),
            Compound(label="Doors", children=lower_doors.parts),
        ]),
        Compound(label="Upper module", children=[
            Compound(label="Frames", children=upper_frame),
            Compound(label="Shelves", children=upper_shelves),
            Compound(label="Skin", children=upper_skin),
            Compound(label="Doors", children=upper_doors.parts),
        ]),
    ])
