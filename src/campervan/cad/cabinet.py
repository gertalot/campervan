"""Scribed plywood sides and divider, face-mounted cleats and a timber front frame."""

from typing import Any

from build123d import Align, Axis, Color, Compound, Cylinder, Face, Location, Part, Plane, Shape, Solid, Wire, fillet, section

from campervan.cad.cabinet_backing import backing_glue_cleats, build_backing
from campervan.cad.cabinet_doors import DOOR_COLOR, REBATE_WIDTH, build_cabinet_doors, cabinet_door_module, panel_rebate
from campervan.cad.cabinet_layout import cabinet_layout
from campervan.cad.cabinet_modules import module_fasteners
from campervan.cad.cut_profiles import set_fitting_datums
from campervan.cad.scan_scribing import scribe_assembly
from campervan.cad.scan_scribe_data import CABINET_SCRIBE_FLOOR_Z_MM, CABINET_SCRIBE_REAR_Y_MM
from campervan.cad.cabinet_upper import rear_face_clearance, rear_panel_clearance, rear_upper_post_y
from campervan.cad.panels import panel
from campervan.parameters import Parameters
from campervan.parameter_fit import FURNITURE_FIT_ENABLED

WOOD = Color(0.84, 0.64, 0.39)
SKIN = Color(0.91, 0.80, 0.62)


def build_cabinet(p: Parameters) -> Compound:
    if (abs(p.floor_surface_z_mm - CABINET_SCRIBE_FLOOR_Z_MM) > 0.001
            or abs(p.cabinet_rear_y_mm - CABINET_SCRIBE_REAR_Y_MM) > 0.001):
        raise ValueError("Regenerate the cabinet scan profiles for the changed floor elevation or rear position.")
    layout = cabinet_layout(p)
    w, t, skin = p.cabinet_frame_width_mm, p.cabinet_frame_thickness_mm, p.cabinet_partition_thickness_mm
    shelf = p.cabinet_shelf_thickness_mm
    middle, length = p.cabinet_rear_bay_length_mm, p.cabinet_length_mm
    upper_post = rear_upper_post_y(p)
    if not w < upper_post < layout.bays[0][1] - w - 120:
        raise ValueError("Rear top door needs at least 120mm beside the roof-beam infill.")
    modules: dict[str, dict[str, list[Shape[Any]]]] = {
        name: {group: [] for group in ("Frames", "Skin", "Shelves", "Doors")}
        for name in ("Lower module", "Upper module")
    }
    timber: list[tuple[str, Part]] = []
    posts: list[Part] = []
    joint_rails: list[tuple[str, Part]] = []
    if FURNITURE_FIT_ENABLED and layout.first - w < p.arch_height_mm + 3:
        raise ValueError("The copied wall-side rail must clear the wheel arch.")

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

    def scribed_sheet(part: Part, axis: int, *, backed: bool = True) -> Part:
        """Intersect face/mid-plane templates, then extrude one square-edged jigsaw outline."""
        pose = part.location
        room = layout.backed_plywood_room if backed else layout.plywood_room
        local_room = room.moved(pose.inverse())
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
        # Section intersections can retain inconsistent surface/vertex locations.
        # Project their exact wires onto one plane before making the constant-thickness sheet.
        box = profile.bounding_box()
        span = 2 * (max(abs(value) for value in (*box.min, *box.max)) + box.diagonal)
        target = Face.make_rect(span, span, Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=normal))

        def planar_wire(wire: Wire) -> Wire:
            projected, = wire.project_to_shape(target, direction=tuple(-value for value in normal))
            return projected

        faces = [Face(planar_wire(face.outer_wire()), [planar_wire(wire) for wire in face.inner_wires()])
                 for face in profile.faces()]
        result = Part(
            [solid for face in faces for solid in Solid.extrude(face, direction).solids()],
            label=part.label,
            color=part.color,
        )
        if abs(tuple(result.bounding_box().size)[axis] - thickness) > 0.01:
            raise ValueError(f"Scribed sheet changed its stock thickness: {part.label}")
        result.location = pose
        return result

    def add(part: Part, module: str, group: str, *, fitted: bool = True) -> Part:
        if fitted:
            fitted_part = (
                scribed_sheet(part, 1, backed=part.label == "Middle supporting panel") if group == "Skin" else fit(part)
            )
            if FURNITURE_FIT_ENABLED and group == "Frames" and part.volume - fitted_part.volume > 0.1:
                raise ValueError(f"Cabinet timber intersects the fitting envelope: {part.label}")
            part = fitted_part
        if group == "Frames" and module == "Upper module" and part.bounding_box().min.Z < layout.split - 0.001:
            raise ValueError(f"Upper cabinet timber crosses the module joint: {part.label}")
        if part is not None:
            modules[module][group].append(part)
        return part

    def joining_rail_end(y: float, panel_y: float) -> float:
        """Keep the original common footprint of both module rails and their bolt lands."""
        start = layout.front + t
        lo, hi = start, p.cargo_width_mm
        band_start, band_end = min(y, panel_y), max(y + t, panel_y + skin)
        for _ in range(12):
            end = (lo + hi) / 2
            stock = panel(end - start, band_end - band_start, 2 * w).moved(
                Location((start, band_start, layout.split - w)))
            if sum(solid.volume for solid in (stock - layout.frame_room).solids()) < 0.01:
                lo = end
            else:
                hi = end
        if lo - start < 120:
            raise ValueError("Cabinet joining rails need at least 120mm of shared bearing.")
        return lo - 1

    def cleat(label: str, y: float, bottom: float, top: float, owner: str, *, end: float | None = None) -> Part:
        start = layout.front + t
        part = panel((p.cargo_width_mm if end is None else end) - start, t, top - bottom)
        part.location = Location((start, y, bottom))
        part.label, part.color = label, WOOD
        # Shelf cleats follow the backing; module rails retain their shared footprint and bolt positions.
        part = add(fit(part), owner, "Frames")
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
            if module == "Upper module" and name == "Rear":
                pose = part.location
                part = Part(
                    (part & rear_face_clearance(p)).moved(pose.inverse()).solids(), label=part.label, color=WOOD
                )
                part.location = pose
            part = add(part, module, "Frames")
            if part is not None:
                posts.append(part)
        for level in levels:
            for bay, (start, end) in zip(("Rear", "Cab-end"), layout.bays, strict=True):
                if module == "Upper module" and bay == "Rear" and level == layout.top:
                    start = upper_post + w
                part = panel(end - start, t, w)
                part.label, part.color = f"{bay} front rail at {level:g}mm", WOOD
                part.location = Location((layout.front + t, start, level - w), (0, 0, 90))
                part = add(part, module, "Frames")
                if part is not None:
                    timber.append((module, part))

    # A fixed inset panel uses the same face, reveals and edge treatment as the doors.
    stile = panel(w, t, layout.top - layout.upper)
    stile.label, stile.color = "Rear top relocated stile", WOOD
    stile.location = Location((layout.front + t, upper_post, layout.upper), (0, 0, 90))
    posts.append(add(stile, "Upper module", "Frames"))
    reveal = p.cabinet_door_gap_mm
    infill_start, infill_bottom = w - REBATE_WIDTH + reveal, layout.upper - REBATE_WIDTH + reveal
    infill_width = upper_post + REBATE_WIDTH - reveal - infill_start
    infill_height = layout.top - infill_bottom
    infill_rebate = panel_rebate(p, infill_start, infill_bottom, infill_width, infill_height)
    infill = panel(infill_width, p.cabinet_door_thickness_mm, infill_height)
    infill = fillet(infill.edges().filter_by(Axis.Y), p.cabinet_door_corner_radius_mm)
    infill = fillet(infill.edges().filter_by(Axis.Y, reverse=True), p.cabinet_door_edge_radius_mm)
    infill.label, infill.color = "Rear top removable infill", DOOR_COLOR
    infill.location = Location((layout.front + p.cabinet_door_thickness_mm, infill_start, infill_bottom), (0, 0, 90))
    pose = infill.location
    infill = Part(
        (infill & rear_face_clearance(p)).moved(pose.inverse()).solids(), label=infill.label, color=DOOR_COLOR
    )
    infill.location = pose
    add(infill, "Upper module", "Skin", fitted=False)

    # Copy the aisle frame inside the unchanged end skins. The arch opening has no bottom rail
    # or floor-standing centre stile; the centre stile bears on the rail at the first shelf level.
    wall_inner = layout.lower_back - t
    if FURNITURE_FIT_ENABLED and wall_inner - (layout.front + t) < 230:
        raise ValueError("Cabinet rear opening must retain 230mm clear width.")
    wall_labels = set()
    for name, y, bottom, top in (
        ("Rear wall stile", skin, 0.0, layout.split),
        ("Cab-end wall stile", length - skin - w, 0.0, layout.split),
        ("Middle wall stile", middle - w, layout.first, layout.split),
    ):
        part = panel(w, t, top - bottom)
        part.label, part.color = name, WOOD
        part.location = Location((layout.lower_back, y, bottom), (0, 0, 90))
        # This repeats the existing wall datum. Do not cut the copied legs with the coarse arch box.
        part = add(part, "Lower module", "Frames", fitted=False)
        wall_labels.add(name)
        posts.append(part)
    for name, start, end, level in (
        ("Wall rail", skin + w, length - skin - w, layout.first),
        ("Rear wall top rail", skin + w, middle - w, layout.split),
        ("Cab-end wall top rail", middle + skin, length - skin - w, layout.split),
    ):
        part = panel(end - start, t, w)
        part.label, part.color = name, WOOD
        part.location = Location((layout.lower_back, start, level - w), (0, 0, 90))
        part = add(part, "Lower module", "Frames", fitted=False)
        timber.append(("Lower module", part))
        wall_labels.add(part.label)

    sides = (
        ("Rear", skin, 0.0),
        ("Middle rear", middle - t, middle),
        ("Middle cab-end", middle + skin, middle),
        ("Cab-end", length - skin - t, length - skin),
    )
    for name, y, panel_y in sides:
        end = joining_rail_end(y, panel_y)
        for owner, bottom in (("Lower module", layout.split - w), ("Upper module", layout.split)):
            rail = cleat(f"{name} joining rail", y, bottom, bottom + w, owner, end=end)
            joint_rails.append((owner, rail))
        if name in {"Middle cab-end", "Cab-end"}:
            bottom = layout.first - w
            cleat(
                f"{name} lower shelf cleat",
                y,
                bottom,
                layout.first,
                "Lower module",
            )
        bottom = layout.upper - shelf - w
        cleat(
            f"{name} upper shelf cleat",
            y,
            bottom,
            layout.upper - shelf,
            "Upper module",
        )

    # Full-profile supporting plywood replaces the old transverse ladders and thin cladding.
    for name, y in (("Middle", middle), ("Cab-end", length - skin)):
        for module, lo, hi in (
            ("Lower module", 0.0, layout.split + p.cabinet_module_guide_height_mm),
            (
                "Upper module",
                layout.split + p.cabinet_module_guide_height_mm + p.cabinet_module_clearance_mm,
                p.body_height_mm - p.floor_surface_z_mm + 10,
            ),
        ):
            part = panel(p.cargo_width_mm - layout.front, skin, hi - lo)
            part.label, part.color = f"{name} supporting panel", SKIN
            part.location = Location((layout.front + t, y, lo))
            if name == "Middle" and module == "Lower module":
                gap = p.cabinet_module_clearance_mm
                # Keep the open divider relief flush with the newly raised wall-side rail.
                clearance = panel(
                    p.cargo_width_mm - wall_inner + gap + t, skin + 2, layout.first + gap + 1
                ).moved(Location((wall_inner - gap, y - 1, -1)))
                part = cut(part, clearance)
            add(part, module, "Skin")
    rear_guide_top = layout.split + p.cabinet_module_guide_height_mm
    for module, lo, hi in (
        ("Lower module", p.cabinet_rear_storage_height_mm, rear_guide_top),
        ("Upper module", rear_guide_top + p.cabinet_module_clearance_mm,
         p.body_height_mm - p.floor_surface_z_mm + 10),
    ):
        rear = panel(p.cargo_width_mm - layout.front, skin, hi - lo)
        rear.label, rear.color = "Rear supporting panel", SKIN
        rear.location = Location((layout.front + t, 0, lo))
        pose = rear.location
        rear = Part((rear & rear_panel_clearance(p)).moved(pose.inverse()).solids(), label=rear.label, color=SKIN)
        rear.location = pose
        add(rear, module, "Skin")

    for owner, back in build_backing(p):
        back.color = SKIN
        add(back, owner, "Skin", fitted=False)

    # Four rails at the interface, including one on each side of the middle skin.
    bolt_centres: list[tuple[float, float]] = []
    lower_joint = [part for module, part in joint_rails if module == "Lower module"]
    for rail in lower_joint:
        box = rail.bounding_box()
        if box.size.X < 120:
            raise ValueError("Cabinet joining rails need two bolt positions clear of their ends.")
        bolt_centres.extend(((box.min.X + 40, box.center().Y), (box.max.X - 40, box.center().Y)))
    for x, y in bolt_centres:
        bearing = Cylinder(8, 2 * w, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((x, y, layout.split - w)))
        supported = 0.0
        for _, rail in joint_rails:
            contact = rail & bearing
            if contact is not None:
                supported += sum(solid.volume for solid in contact.solids())
        if supported < bearing.volume - 0.1:
            raise ValueError(f"Cabinet module bolt lacks mating rail support at X={x:g}, Y={y:g}.")
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

    # Shelves finish flush in continuous rail seats; joint bolts pass through the lower-module shelves.
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
            if any(face.inner_wires() for face in part.faces() if face.normal_at().Z > 0.99):
                raise ValueError(f"Cabinet shelf has an internal framing cutout: {part.label}")
            # Cut the rail seats from the unbored shelf so no bolt-sized timber islands remain.
            seat = part
            if abs(level - layout.split) < 0.01:
                for bore in bores:
                    part = cut(part, bore)
            module = "Lower module" if level <= layout.split else "Upper module"
            modules[module]["Shelves"].append(part)
            for index, (owner, rail) in enumerate(timber):
                box = rail.bounding_box()
                if owner == module and abs(box.max.Z - level) < 0.05:
                    replacement = cut(rail, seat)
                    group = modules[owner]["Frames"]
                    group[next(i for i, item in enumerate(group) if item is rail)] = replacement
                    timber[index] = (owner, replacement)

    # Join the copied wall frame to the existing transverse rails with half-lapped crossings.
    # The lower half remains in the wall member; the upper half remains in the transverse rail.
    frames = modules["Lower module"]["Frames"]
    for i, cross in enumerate(frames):
        if not (cross.label.endswith("joining rail") or cross.label.endswith("lower shelf cleat")):
            continue
        level = layout.split if cross.label.endswith("joining rail") else layout.first
        upper_half = panel(p.cargo_width_mm + 2, length + 2, w / 2 + 1).moved(
            Location((0, -1, level - w / 2)))
        for j, wall in enumerate(frames):
            if wall.label not in wall_labels:
                continue
            overlap = wall & cross
            if overlap is not None and overlap.solids():
                frames[j] = cut(wall, overlap & upper_half)
                cross = cut(cross, overlap - upper_half)
        frames[i] = cross

    # Rebates are cut at the closed pose, independently of the doors' current angles.
    for groups in modules.values():
        frames = groups["Frames"]
        for index, frame in enumerate(frames):
            if frame.children:
                continue
            box = frame.bounding_box()
            for pocket in [*door_parts.rebates, infill_rebate]:
                pb = pocket.bounding_box()
                if all(a < d and c < b for a, b, c, d in zip(box.min, box.max, pb.min, pb.max, strict=True)):
                    frame = cut(frame, pocket)
            frames[index] = frame

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

    for module, parts in modules.items():
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
            if module == "Lower module" and part.label.endswith("lower shelf cleat"):
                # The 40mm rail depth is fixed by the frame levels; only its wall-facing end is scribed.
                set_fitting_datums(part, 2)
            group[index] = part

    glue_cleats = backing_glue_cleats(p, layout.first, layout.split, layout.upper)
    for module, groups in modules.items():
        cleats = [cleat for owner, cleat in glue_cleats if owner == module and module == "Upper module"]
        for cleat in cleats:
            cleat.color = WOOD
        if cleats:
            groups["Frames"].append(Compound(label="Backing glue cleats", children=cleats))

    for module, groups in modules.items():
        labels = {rail.label for owner, rail in joint_rails if owner == module}
        frames = groups["Frames"]
        joint = [part for part in frames if part.label in labels or part.label == "Module fasteners"]
        groups["Frames"] = [part for part in frames if part not in joint]
        groups["Frames"].append(Compound(label="Module joint", children=joint))

    for door in door_parts.assembly.children:
        modules[cabinet_door_module(door.label)]["Doors"].append(door)
    filler = panel(t, length - upper_post, w)
    filler.label, filler.color = "Scribed ceiling filler", WOOD
    filler.location = Location((layout.front, upper_post, layout.top))
    add(filler, "Upper module", "Frames", fitted=False)
    return scribe_assembly(
        Compound(
            label="Cabinet",
            children=[
                Compound(
                    label=module, children=[Compound(label=group, children=parts) for group, parts in groups.items()]
                )
                for module, groups in modules.items()
            ],
        ),
        (0.0, p.cabinet_rear_y_mm, p.floor_surface_z_mm),
        inboard=-1,
    )
