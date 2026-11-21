"""Independent flat plywood backs and the matching interior fitting limits."""

from build123d import Compound, Face, Location, Part, Plane, Solid, Wire

from campervan.cad.cabinet_scribe_data import BACKING_PROFILES
from campervan.cad.panels import panel
from campervan.parameters import Parameters


def fit_to_backings(room: Part, p: Parameters, first: float, split: float, upper: float) -> Part:
    """Fit interiors to row-wise backing planes, retaining the exposed rear corner."""
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
        ("Upper cab-end top backing", middle, end, upper, p.body_height_mm + 10),
        ("Upper rear top backing", rear + skin, middle, upper, p.body_height_mm + 10),
    )
    for row in ("top", "bottom"):
        front = BACKING_PROFILES[f"Upper cab-end {row} backing"]
        rear_back = BACKING_PROFILES[f"Upper rear {row} backing"]
        offset = sum(n * (a - b) for n, a, b in zip(front[2], front[0], rear_back[0], strict=True))
        if front[2] != rear_back[2] or abs(offset) > 0.001:
            raise ValueError(f"Front and rear {row} backings must share one plane.")
    masks, allowed = [], []
    for name, y0, y1, z0, z1 in regions:
        origin, x_dir, normal, outline, _ = BACKING_PROFILES[name]
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

    for name, (origin, x_dir, normal, outline, holes) in BACKING_PROFILES.items():
        face = Face(wire(outline), [wire(hole) for hole in holes])
        back = Part(Solid.extrude(face, (0, 0, p.cabinet_partition_thickness_mm)).solids(), label=name)
        plane = Plane(origin=origin, x_dir=x_dir, z_dir=normal)
        back.location = Location((0, -p.cabinet_rear_y_mm, 0)) * plane.location
        module = "Lower module" if name.startswith("Lower") else "Upper module"
        backs.append((module, back))
    return backs
