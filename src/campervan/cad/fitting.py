"""Identify cutting edges near the registered van, excluding its horizontal floor."""

import json
from pathlib import Path

import numpy as np
import open3d as o3d
from build123d import Location, Shape

# Includes the deliberate 3–5mm fitting gaps and outward rounding of clean notches.
CONTACT_MM = 10.0
SAMPLE_MM = 5.0
REFERENCE = Path("data/scan-reference")


class VehicleFitting:
    def __init__(self, width: float, floor_z: float):
        self.width = width
        self.floor_z = floor_z
        reference = json.loads((REFERENCE / "reference.json").read_text())
        pose = np.eye(4)
        pose[:3, :3] = reference["cad_reference"]["rotation"]
        pose[:3, 3] = np.array(reference["cad_reference"]["translation_mm"]) / 1000
        pose = pose @ np.array(reference["alignment"]["matrix"])
        mesh = o3d.io.read_triangle_mesh(str(REFERENCE / "mesh.ply"))
        mesh.transform(pose)
        vertices = np.asarray(mesh.vertices) * 1000
        triangles = np.asarray(mesh.triangles)
        xyz = vertices[triangles]
        normals = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
        horizontal = np.abs(normals[:, 2]) > 0.8 * np.linalg.norm(normals, axis=1)
        floor = horizontal & (xyz[:, :, 2].max(axis=1) <= floor_z)
        # This hanging strap is removable, not a ceiling fitting boundary.
        strap = ((vertices[:, 0] > 1080) & (vertices[:, 0] < 1140)
                 & (vertices[:, 1] > 635) & (vertices[:, 1] < 677)
                 & (vertices[:, 2] > 1240) & (vertices[:, 2] < 1280))
        triangles = triangles[~floor & ~strap[triangles].any(axis=1)]
        self.scene = o3d.t.geometry.RaycastingScene(nthreads=4)
        self.scene.add_triangles(o3d.core.Tensor(vertices.astype(np.float32)),
                                 o3d.core.Tensor(triangles.astype(np.uint32)))

    def edges(self, part: Shape, world: Location, axes: tuple[int, int, int], outline: list,
              *, furniture: bool, datum_axes: tuple[int, ...] = ()) -> tuple[dict[str, str], bool]:
        thin, across, along = axes
        datum_sides = {side for axis, labels in ((along, ("left", "right")), (across, ("top", "bottom")))
                       if axis in datum_axes for side in labels}
        box = Shape.cast(part.wrapped).located(Location()).bounding_box()
        low, high = np.array(tuple(box.min)), np.array(tuple(box.max))
        if not outline:
            length, width = high[along] - low[along], high[across] - low[across]
            outline = [(0, 0), (length, 0), (length, width), (0, width)]
        samples, sides, directions = [], [], []
        for a, b in zip(outline, [*outline[1:], outline[0]], strict=True):
            a, b = np.array(a), np.array(b)
            delta = b - a
            if np.linalg.norm(delta) < 1e-6:
                continue
            outward = np.array([delta[1], -delta[0]])
            outward /= np.linalg.norm(outward)
            direction = np.zeros(3)
            direction[along], direction[across] = outward
            axis = int(np.argmax(np.abs(outward)))
            side = (("left", "right"), ("top", "bottom"))[axis][int(outward[axis] > 0)]
            for fraction in np.linspace(0, 1, max(2, int(np.ceil(np.linalg.norm(delta) / SAMPLE_MM)) + 1)):
                uv = a + fraction * delta
                # Interior notches retain a rectangular template blank, but do not enlarge unrelated outer edges.
                end = (high if outward[axis] > 0 else low)[(along, across)[axis]]
                at_edge = abs(low[(along, across)[axis]] + uv[axis] - end) < CONTACT_MM
                for depth in (0.0, 0.5, 1.0):
                    point = low.copy()
                    point[along] += uv[0]
                    point[across] += uv[1]
                    point[thin] += depth * (high[thin] - low[thin])
                    samples.append(point)
                    directions.append(direction)
                    sides.append(side if at_edge else None)
        transform = world.wrapped.Transformation()
        matrix = np.array([[transform.Value(row, col) for col in range(1, 5)] for row in range(1, 4)])
        points = np.array(samples) @ matrix[:, :3].T + matrix[:, 3]
        directions = np.array(directions) @ matrix[:, :3].T
        # Furniture construction is reflected by model.py. Registered scribe data uses the construction side.
        if furniture:
            points[:, 0] = self.width - points[:, 0]
            directions[:, 0] *= -1
        query = o3d.core.Tensor(points.astype(np.float32))
        contacts = self.scene.compute_closest_points(query, nthreads=4)
        closest = contacts["points"].numpy()
        normals = contacts["primitive_normals"].numpy()
        # The registered mesh faces inward. Match the opposite-facing board edge,
        # so a wall contact at a corner cannot mark its perpendicular floor/joint edge.
        near = ((np.linalg.norm(closest - points, axis=1) <= CONTACT_MM)
                & ((directions * normals).sum(axis=1) < -0.5))
        # Assembly datums constrain outer stock dimensions, not interior vehicle notches.
        near &= np.array([side not in datum_sides for side in sides])
        # Scan geometry below the finished floor cannot define a furniture fitting edge.
        near &= closest[:, 2] > self.floor_z
        # Board bottoms resting on the assumed horizontal floor are datum edges,
        # even where noisy scan triangles rise just above the floor filter.
        near &= ~((points[:, 2] <= self.floor_z + 1e-5) & (directions[:, 2] < -0.5))
        fitting = {}
        for index in np.flatnonzero(near):
            if sides[index] is not None:
                label = "Ceiling" if normals[index, 2] < -0.7 and closest[index, 2] > 1000 else "Sidewall / wheel arch"
                fitting[sides[index]] = label
        return fitting, bool(near.any())
