"""Flat cutting silhouettes in each part's construction coordinates."""

from build123d import Location, Plane, Shape, Vector, section


def flat_profile(part: Shape) -> dict:
    local = part.located(Location())
    box = local.bounding_box()
    sizes = list(box.size)
    thin, across, along = sorted(range(3), key=lambda axis: sizes[axis])
    axes = [Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1)]
    normal = axes[along].cross(axes[across])
    # Union the two faces and mid-plane. Blind pockets remain solid in the
    # silhouette; only openings that pass through the stock become nesting holes.
    faces = []
    for fraction in (0.00001, 0.5, 0.99999):
        origin = list(box.min)
        origin[thin] += sizes[thin] * fraction
        plane = Plane(origin=Vector(*origin), x_dir=axes[along], z_dir=normal)
        sketch = plane.to_local_coords(section(local, section_by=plane))
        faces.extend(sketch.faces())
    if not faces:
        raise ValueError(f"No flat section for {part.label}")
    merged = faces[0].fuse(*faces[1:])
    profiles = merged.faces() if isinstance(merged, Shape) else [f for shape in merged for f in shape.faces()]
    if len(profiles) != 1:
        raise ValueError(f"Disconnected cutting profile for {part.label}")
    face = profiles[0]
    offset = face.bounding_box().min

    def points(wire):
        result = [(round(p.X - offset.X, 4), round(p.Y - offset.Y, 4))
                  for p in wire.positions(deflection=0.1)]
        if result and result[0] == result[-1]:
            result.pop()
        area = sum(x * result[(i + 1) % len(result)][1] - result[(i + 1) % len(result)][0] * y
                   for i, (x, y) in enumerate(result))
        return result if area > 0 else list(reversed(result))

    return {
        "outline": points(face.outer_wire()),
        "holes": [points(wire) for wire in face.inner_wires()],
        "profile_axes": f"Length = local {'XYZ'[along]}; width = local {'XYZ'[across]}",
        "profile_note": "CAD outline; curves sampled to 0.1 mm. Blind pockets and edge finishing are separate operations.",
    }
