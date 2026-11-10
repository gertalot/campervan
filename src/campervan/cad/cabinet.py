"""Scribed plywood sides and divider, face-mounted cleats and a timber front frame."""

from typing import Any

from build123d import Align, Color, Compound, Cylinder, Location, Part, Plane, Shape, Solid, section

from campervan.cad.cabinet_doors import build_cabinet_doors, cabinet_door_module
from campervan.cad.cabinet_layout import cabinet_layout
from campervan.cad.cabinet_modules import module_fasteners
from campervan.cad.panels import panel
from campervan.parameters import Parameters

WOOD = Color(0.84, 0.64, 0.39)
SKIN = Color(0.91, 0.80, 0.62)


def build_cabinet(p: Parameters) -> Compound:
    layout = cabinet_layout(p)
    w, t, skin = p.cabinet_frame_width_mm, p.cabinet_frame_thickness_mm, p.cabinet_partition_thickness_mm
    shelf = p.cabinet_shelf_thickness_mm
    middle, length = p.cabinet_rear_bay_length_mm, p.cabinet_length_mm
    modules: dict[str, dict[str, list[Shape[Any]]]] = {
        name: {group: [] for group in ("Frames", "Skin", "Shelves", "Doors")}
        for name in ("Lower module", "Upper module")
    }
    timber: list[tuple[str, Part]] = []
    posts: list[Part] = []
    joint_rails: list[tuple[str, Part]] = []
    bridge_top = layout.first - shelf - w
    if bridge_top - p.cabinet_bridge_height_mm < p.arch_height_mm + 3:
        raise ValueError("The wheel-arch bridge beneath the lower shelf cleats must clear the wheel arch.")

    def fit(part: Part) -> Part:
        pose = part.location
        shape = part & layout.frame_room
        if not shape.solids():
            raise ValueError(f"Cabinet part does not fit the vehicle: {part.label}")
        result = Part(shape.moved(pose.inverse()).solids(), label=part.label, color=part.color)
        result.location = pose
        return result

    def cut(part: Shape[Any], cutter: Shape[Any]) -> Part:
        pose = part.location
        result = Part((part - cutter).moved(pose.inverse()).solids(), label=part.label, color=part.color)
        result.location = pose
        return result

    def scribed_sheet(part: Part, axis: int) -> Part:
        """Intersect face/mid-plane templates, then extrude one square-edged jigsaw outline."""
        pose = part.location
        local_room = layout.plywood_room.moved(pose.inverse())
        size = part.bounding_box().size
        # These panels are translated only; the thin dimension is Y for skins and Z for shelves.
        thickness = size.Y if axis == 1 else size.Z
        profile = None
        for fraction in (0.000001, 0.5, 0.999999):
            distance = thickness * fraction
            origin = (0.0, distance, 0.0) if axis == 1 else (0.0, 0.0, distance)
            normal = (0.0, 1.0, 0.0) if axis == 1 else (0.0, 0.0, 1.0)
            plane = Plane(origin=origin, x_dir=(1, 0, 0), z_dir=normal)
            template = section(local_room & part.located(Location()), section_by=plane).moved(
                Location((0, -distance, 0) if axis == 1 else (0, 0, -distance))
            )
            profile = template if profile is None else profile & template
        if profile is None or not profile.faces():
            raise ValueError(f"No scribed plywood outline remains for {part.label}.")
        direction = (0, thickness, 0) if axis == 1 else (0, 0, thickness)
        result = Part(
            [solid for face in profile.faces() for solid in Solid.extrude(face, direction).solids()],
            label=part.label,
            color=part.color,
        )
        result.location = pose
        return result

    def add(part: Part, module: str, group: str, *, fitted: bool = True) -> Part:
        if fitted:
            fitted_part = scribed_sheet(part, 1) if group == "Skin" else fit(part)
            if group == "Frames" and part.volume - fitted_part.volume > 0.1:
                raise ValueError(f"Cabinet timber intersects the fitting envelope: {part.label}")
            part = fitted_part
        if group == "Frames" and module == "Upper module" and part.bounding_box().min.Z < layout.split - 0.001:
            raise ValueError(f"Upper cabinet timber crosses the module joint: {part.label}")
        if part is not None:
            modules[module][group].append(part)
        return part

    def cleat_end(y: float, panel_y: float, bottom: float, top: float) -> float:
        """Square-cut stock fits the complete receiving band, not a single wall sample."""
        start = layout.front + t
        lo, hi = start, p.cargo_width_mm
        band_start, band_end = min(y, panel_y), max(y + t, panel_y + skin)
        for _ in range(12):
            end = (lo + hi) / 2
            stock = panel(end - start, band_end - band_start, top - bottom).moved(Location((start, band_start, bottom)))
            if sum(solid.volume for solid in (stock - layout.frame_room).solids()) < 0.01:
                lo = end
            else:
                hi = end
        if lo - start < 120:
            raise ValueError("Cabinet panel has insufficient depth for a shelf cleat.")
        return lo - 1

    def cleat(label: str, y: float, bottom: float, top: float, owner: str, end: float) -> Part:
        start = layout.front + t
        part = panel(end - start, t, top - bottom)
        part.location = Location((start, y, bottom))
        part.label, part.color = label, WOOD
        part = add(part, owner, "Frames")
        timber.append((owner, part))
        return part

    # End panels butt behind the front frame; shelf cleats provide face-grain fixing lands.
    centre = middle + skin / 2
    front_posts = (0.0, centre - w / 2, length - w)
    for module, bottom, top in (("Lower module", 0.0, layout.split), ("Upper module", layout.split, layout.top)):
        levels: tuple[float, ...] = (
            (w, layout.first, layout.split)
            if module == "Lower module"
            else (layout.split + w, layout.upper, layout.top)
        )
        for name, y in zip(("Rear", "Middle", "Cab-end"), front_posts, strict=True):
            part = panel(w, t, top - bottom)
            part.label, part.color = f"{name} front stile", WOOD
            part.location = Location((layout.front + t, y, bottom), (0, 0, 90))
            part = add(part, module, "Frames")
            if part is not None:
                posts.append(part)
        for level in levels:
            for bay, (start, end) in zip(("Rear", "Cab-end"), layout.bays, strict=True):
                part = panel(end - start, t, w)
                part.label, part.color = f"{bay} front rail at {level:g}mm", WOOD
                part.location = Location((layout.front + t, start, level - w), (0, 0, 90))
                part = add(part, module, "Frames")
                if part is not None:
                    timber.append((module, part))

    # Wall-side end uprights give the bridge timber attachments at both ends.
    # The rear jamb preserves the loading opening; the cab-end upright stops under its shelf cleat.
    bridge_inner = layout.lower_back - p.cabinet_bridge_thickness_mm
    jamb_inner = layout.lower_back - w
    if jamb_inner - (layout.front + t) < 230:
        raise ValueError("Cabinet rear opening must retain 230mm clear width.")
    jamb = panel(w, t, p.cabinet_rear_storage_height_mm)
    jamb.label, jamb.color = "Rear loading jamb", WOOD
    jamb.location = Location((jamb_inner, skin, 0))
    add(jamb, "Lower module", "Frames")
    cab_end_upright = panel(w, t, bridge_top)
    cab_end_upright.label, cab_end_upright.color = "Cab-end bridge upright", WOOD
    cab_end_upright.location = Location((jamb_inner, length - skin - t, 0))
    add(cab_end_upright, "Lower module", "Frames")
    bridge = panel(length - skin - t - (skin + t), p.cabinet_bridge_thickness_mm, p.cabinet_bridge_height_mm)
    bridge.label, bridge.color = "Wheel-arch bridge", WOOD
    bridge.location = Location((layout.lower_back, skin + t, bridge_top - p.cabinet_bridge_height_mm), (0, 0, 90))
    add(bridge, "Lower module", "Frames")

    sides = (
        ("Rear", skin, 0.0),
        ("Middle rear", middle - t, middle),
        ("Middle cab-end", middle + skin, middle),
        ("Cab-end", length - skin - t, length - skin),
    )
    for name, y, panel_y in sides:
        end = cleat_end(y, panel_y, layout.split - w, layout.split + w)
        for owner, bottom in (("Lower module", layout.split - w), ("Upper module", layout.split)):
            rail = cleat(f"{name} joining rail", y, bottom, bottom + w, owner, end)
            joint_rails.append((owner, rail))
        if name in {"Middle cab-end", "Cab-end"}:
            bottom = layout.first - shelf - w
            cleat(
                f"{name} lower shelf cleat",
                y,
                bottom,
                layout.first - shelf,
                "Lower module",
                cleat_end(y, panel_y, bottom, layout.first - shelf),
            )
        bottom = layout.upper - shelf - w
        cleat(
            f"{name} upper shelf cleat",
            y,
            bottom,
            layout.upper - shelf,
            "Upper module",
            cleat_end(y, panel_y, bottom, layout.upper - shelf),
        )

    # Full-profile supporting plywood replaces the old transverse ladders and thin cladding.
    for name, y in (("Middle", middle), ("Cab-end", length - skin)):
        for module, lo, hi in (
            ("Lower module", 0.0, layout.split + p.cabinet_module_guide_height_mm),
            (
                "Upper module",
                layout.split + p.cabinet_module_guide_height_mm + p.cabinet_module_clearance_mm,
                p.body_height_mm + 10,
            ),
        ):
            part = panel(p.cargo_width_mm - layout.front, skin, hi - lo)
            part.label, part.color = f"{name} supporting panel", SKIN
            part.location = Location((layout.front + t, y, lo))
            if name == "Middle" and module == "Lower module":
                arch_inner = (p.cargo_width_mm + p.arch_gap_mm) / 2 - 3
                clearance = panel(p.cargo_width_mm, skin + 2, bridge_top).moved(
                    Location((min(bridge_inner, arch_inner), y - 1, 0))
                )
                part = cut(part, clearance)
            add(part, module, "Skin")
    rear = panel(p.cargo_width_mm - layout.front, skin, p.body_height_mm - p.cabinet_rear_storage_height_mm + 10)
    rear.label, rear.color = "Rear supporting panel", SKIN
    rear.location = Location((layout.front + t, 0, p.cabinet_rear_storage_height_mm))
    add(rear, "Upper module", "Skin")

    # Four rails at the interface, including one on each side of the middle skin.
    bolt_centres: list[tuple[float, float]] = []
    lower_joint = [part for module, part in joint_rails if module == "Lower module"]
    for rail in lower_joint:
        box = rail.bounding_box()
        if box.size.X < 120:
            raise ValueError("Cabinet joining rails need two bolt positions clear of their ends.")
        bolt_centres.extend(((box.min.X + 40, box.center().Y), (box.max.X - 40, box.center().Y)))
    bores, fasteners = module_fasteners(p, layout.split, bolt_centres)
    modules["Lower module"]["Frames"].append(Compound(label="Module fasteners", children=fasteners))

    openings = (
        (w, layout.first - w),
        (layout.first, layout.split - w),
        (layout.split + w, layout.upper - w),
        (layout.upper, layout.top - w),
    )
    door_parts = build_cabinet_doors(p, layout.bays, list(openings), list(openings))
    for module, blocks in door_parts.blocks.items():
        for block in blocks:
            block.color = WOOD
            add(block, module, "Frames")

    # Perimeter rebates are cut from the actual shelf solids. Solid pads remain around every module bolt.
    pad_cuts = [
        panel(24, 24, 2 * w + 2).moved(Location((x - 12, y - 12, layout.split - w - 1))) for x, y in bolt_centres
    ]
    for bay, start, end, levels in (
        ("Rear", skin, middle, (layout.split, layout.upper)),
        ("Cab-end", middle + skin, length - skin, (layout.first, layout.split, layout.upper)),
    ):
        for level in levels:
            part = panel(p.cargo_width_mm - (layout.front + t), end - start, shelf)
            part.label, part.color = f"{bay} shelf at {level:g}mm", SKIN
            part.location = Location((layout.front + t, start, level - shelf))
            part = scribed_sheet(part, 2)
            for clearance in door_parts.shelf_clearances:
                part = cut(part, clearance)
            for post in posts:
                if post.bounding_box().max.Z > level - shelf and post.bounding_box().min.Z < level:
                    part = cut(part, post)
            if abs(level - layout.split) < 0.01:
                for pad in pad_cuts:
                    part = cut(part, pad)
            if any(face.inner_wires() for face in part.faces() if face.normal_at().Z > 0.99):
                raise ValueError(f"Cabinet shelf has an internal framing cutout: {part.label}")
            module = "Lower module" if level <= layout.split else "Upper module"
            modules[module]["Shelves"].append(part)
            for index, (owner, rail) in enumerate(timber):
                box = rail.bounding_box()
                if owner == module and abs(box.max.Z - level) < 0.05:
                    replacement = cut(rail, part)
                    group = modules[owner]["Frames"]
                    group[next(i for i, item in enumerate(group) if item is rail)] = replacement
                    timber[index] = (owner, replacement)

    # Verify full timber surrounds every frame fixing before drilling its clearance hole.
    frame_parts = [part for groups in modules.values() for part in groups["Frames"] if not part.children]
    face = layout.front
    for hole in door_parts.frame_holes:
        hole_centre = hole.bounding_box().center()
        probe = Cylinder(2.5, t, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((face, hole_centre.Y, hole_centre.Z), (0, 90, 0))
        )
        box = probe.bounding_box()
        supported = 0.0
        for frame in frame_parts:
            fb = frame.bounding_box()
            if all(a < d + 1e-6 and c < b + 1e-6 for a, b, c, d in zip(box.min, box.max, fb.min, fb.max, strict=True)):
                contact = frame & probe
                if contact is not None:
                    supported += sum(solid.volume for solid in contact.solids())
        if supported < probe.volume - 0.1:
            raise ValueError(
                f"Cabinet door fixing lacks full timber support at Y={hole_centre.Y:g}, Z={hole_centre.Z:g}."
            )
    bores.extend(door_parts.frame_holes)

    for parts in modules.values():
        group = parts["Frames"]
        for index, part in enumerate(group):
            if part.children:
                continue
            box = part.bounding_box()
            for bore in bores:
                bb = bore.bounding_box()
                if all(
                    a < d + 1e-6 and c < b + 1e-6 for a, b, c, d in zip(box.min, box.max, bb.min, bb.max, strict=True)
                ):
                    part = cut(part, bore)
            group[index] = part

    for module, groups in modules.items():
        labels = {rail.label for owner, rail in joint_rails if owner == module}
        frames = groups["Frames"]
        joint = [part for part in frames if part.label in labels or part.label == "Module fasteners"]
        groups["Frames"] = [part for part in frames if part not in joint]
        groups["Frames"].append(Compound(label="Module joint", children=joint))

    for door in door_parts.assembly.children:
        modules[cabinet_door_module(door.label)]["Doors"].append(door)
    return Compound(
        label="Cabinet",
        children=[
            Compound(label=module, children=[Compound(label=group, children=parts) for group, parts in groups.items()])
            for module, groups in modules.items()
        ],
    )
