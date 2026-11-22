"""Independent flat plywood backs and the matching interior fitting limits."""

from build123d import Compound, Face, Location, Part, Plane, Solid, Wire

from campervan.cad.scan_scribe_data import BACKING_PROFILES, BackingProfile
from campervan.cad.panels import panel
from campervan.parameters import Parameters


def backing_profiles(p: Parameters) -> dict[str, BackingProfile]:
    """Recorded profiles stay vehicle-fixed; consumers build in floor-relative coordinates."""
    return {name: ((origin[0], origin[1], origin[2] - p.floor_surface_z_mm), x_dir, normal, outline, holes)
            for name, (origin, x_dir, normal, outline, holes) in BACKING_PROFILES.items()}


def fit_to_backings(room: Part, p: Parameters, first: float, split: float, upper: float) -> Part:
    """Fit interiors to row-wise backing planes, retaining the exposed rear corner."""
    profiles = backing_profiles(p)
    rear = p.cabinet_rear_y_mm
    skin = p.cabinet_partition_thickness_mm
    middle = rear + p.cabinet_rear_bay_length_mm + skin
    end = rear + p.cabinet_length_mm - skin
    regions = (
        (
            "Lower cab-end backing",
            middle - skin,
            end,
            first - p.cabinet_shelf_thickness_mm - p.cabinet_frame_width_mm,
            split,
        ),
        ("Upper cab-end bottom backing", middle, end, split, upper),
        ("Upper rear bottom backing", rear + skin, middle, split - p.cabinet_shelf_thickness_mm, upper),
        ("Upper cab-end top backing", middle, end, upper, p.body_height_mm - p.floor_surface_z_mm + 10),
        ("Upper rear top backing", rear + skin, middle, upper, p.body_height_mm - p.floor_surface_z_mm + 10),
    )
    for row in ("top", "bottom"):
        front = profiles[f"Upper cab-end {row} backing"]
        rear_back = profiles[f"Upper rear {row} backing"]
        offset = sum(n * (a - b) for n, a, b in zip(front[2], front[0], rear_back[0], strict=True))
        if front[2] != rear_back[2] or abs(offset) > 0.001:
            raise ValueError(f"Front and rear {row} backings must share one plane.")
    masks, allowed = [], []
    for name, y0, y1, z0, z1 in regions:
        origin, x_dir, normal, outline, _ = profiles[name]
        plane = Plane(origin=origin, x_dir=x_dir, z_dir=normal)
        if abs(normal[1]) > 1e-9:
            raise ValueError("Cabinet backings must not rotate around the Z axis.")

        def back_x(z: float) -> float:
            return origin[0] - normal[2] * (z - origin[2]) / normal[0]

        face = Face(
            Wire.make_polygon(
                [
                    (0, y0 - rear, z0),
                    (back_x(z0), y0 - rear, z0),
                    (back_x(z1), y0 - rear, z1),
                    (0, y0 - rear, z1),
                ]
            )
        )
        plane_room = Solid.extrude(face, (0, y1 - y0, 0))
        mask = panel(p.cargo_width_mm + 10, y1 - y0, z1 - z0).moved(Location((0, y0 - rear, z0)))
        sheet_y = [origin[1] + plane.x_dir.Y * u + plane.y_dir.Y * v for u, v in outline]
        start, finish = max(y0, min(sheet_y)), min(y1, max(sheet_y))
        # Include the receiving middle panel, while leaving the exterior pillar regions contoured.
        if name == "Lower cab-end backing":
            start = y0
        covered = panel(p.cargo_width_mm + 10, finish - start, z1 - z0).moved(Location((0, start - rear, z0)))
        allowed.extend(((room & mask & plane_room), (covered & plane_room)))
        masks.append(mask)
    return Part(((room - Compound(masks)) + Compound(allowed)).solids())


def build_backing(p: Parameters) -> list[tuple[str, Part]]:
    backs = []

    def wire(points: list[tuple[float, float]]) -> Wire:
        return Wire.make_polygon([(u, v, 0) for u, v in points])

    for name, (origin, x_dir, normal, outline, holes) in backing_profiles(p).items():
        face = Face(wire(outline), [wire(hole) for hole in holes])
        back = Part(Solid.extrude(face, (0, 0, p.cabinet_partition_thickness_mm)).solids(), label=name)
        plane = Plane(origin=origin, x_dir=x_dir, z_dir=normal)
        back.location = Location((0, -p.cabinet_rear_y_mm, 0)) * plane.location
        module = "Lower module" if name.startswith("Lower") else "Upper module"
        backs.append((module, back))
    return backs


def backing_glue_cleats(p: Parameters, first: float, split: float, upper: float) -> list[tuple[str, Part]]:
    """18mm pine at skin joints, bevelled to meet the horizontal shelves and rails."""
    size = 18.0
    cleats = []
    for name, (origin, x_dir, normal, outline, _) in backing_profiles(p).items():
        plane = Plane(origin=origin, x_dir=x_dir, z_dir=normal)
        pose = Location((0, -p.cabinet_rear_y_mm, 0)) * plane.location
        module = "Lower module" if name.startswith("Lower") else "Upper module"
        middle = p.cabinet_rear_y_mm + p.cabinet_rear_bay_length_mm
        joints = [("Middle", middle - origin[1] - size)] if "rear" in name else [
            ("Middle", middle + p.cabinet_partition_thickness_mm - origin[1]),
            ("Cab-end", p.cabinet_rear_y_mm + p.cabinet_length_mm
             - p.cabinet_partition_thickness_mm - origin[1] - size),
        ]
        for side, u in joints:
            # A common interval across the full strip keeps both ends square and inside the back's outline.
            stations = [u + 1e-6, u + size - 1e-6]
            stations.extend(x for x, _ in outline if u < x < u + size)
            intervals = []
            for station in stations:
                crossings = [a[1] + (b[1] - a[1]) * (station - a[0]) / (b[0] - a[0])
                             for a, b in zip(outline, outline[1:] + outline[:1])
                             if min(a[0], b[0]) <= station < max(a[0], b[0])]
                if len(crossings) < 2:
                    raise ValueError(f"No backing glue face at {name} / {side}.")
                intervals.append((min(crossings), max(crossings)))
            low = max(a for a, _ in intervals)
            high = min(b for _, b in intervals)
            if name.startswith("Lower"):
                bottom, top = first, split - p.cabinet_frame_width_mm
            elif "bottom" in name:
                bottom, top = split + p.cabinet_frame_width_mm, upper - p.cabinet_shelf_thickness_mm - p.cabinet_frame_width_mm
            else:
                bottom, top = upper, p.body_height_mm - p.floor_surface_z_mm + 10
            # Start with long points, then bevel both ends at the actual horizontal joint planes.
            low = max(low, (bottom - origin[2]) / plane.y_dir.Z)
            high = min(high, (top - origin[2] + size * normal[2]) / plane.y_dir.Z)
            if high <= low:
                raise ValueError(f"No room for backing glue cleat: {name} / {side}.")
            cleat = panel(size, high - low, size)
            cleat.label = f"{name} · {side} glue cleat"
            cleat.location = pose * Location((u, low, -size))
            clip = panel(p.cargo_width_mm + 10, p.cabinet_length_mm + 2, top - bottom).moved(
                Location((0, -1, bottom)))
            placement = cleat.location
            cleat = Part((cleat & clip).moved(placement.inverse()).solids(), label=cleat.label)
            cleat.location = placement
            cleats.append((module, cleat))
    return cleats
