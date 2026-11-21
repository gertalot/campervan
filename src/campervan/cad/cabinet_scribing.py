"""Apply measured scan scribes to cabinet wood, preserving leaf placements and hardware."""

from typing import Any

from build123d import Compound, Face, Location, Part, Shape, Solid, Wire

from campervan.cad.cabinet_scribe_data import SCAN_SCRIBES, Loop, Scribe
from campervan.parameters import Parameters


def is_scan_scribed(path: tuple[str, ...]) -> bool:
    return "Cabinet" in path and "/".join(path[path.index("Cabinet") :]) in SCAN_SCRIBES


def _cutter(scribe: Scribe, rear_y: float) -> Compound:
    axis, (start, finish), polygons = scribe
    other = [i for i in range(3) if i != axis]

    def wire(loop: Loop) -> Wire:
        points = []
        for u, v in loop:
            point = [0.0, 0.0, 0.0]
            point[axis], point[other[0]], point[other[1]] = start, u, v
            point[1] -= rear_y
            points.append(point)
        return Wire.make_polygon(points)

    direction = [0.0, 0.0, 0.0]
    direction[axis] = finish - start
    return Compound(
        [Solid.extrude(Face(wire(outer), [wire(hole) for hole in holes]), direction) for outer, holes in polygons]
    )


def scribe_cabinet(cabinet: Compound, p: Parameters) -> Compound:
    def visit(shape: Shape[Any], parent: Location, path: tuple[str, ...]) -> Shape[Any]:
        path = (*path, shape.label)
        world = parent * shape.location
        if shape.children:
            result = Compound(children=[visit(child, world, path) for child in shape.children])
            result.label, result.color, result.location = shape.label, shape.color, shape.location
            return result
        scribe = SCAN_SCRIBES.get("/".join(path))
        if scribe is None:
            return shape
        original = Shape.cast(shape.wrapped).located(world)
        pieces = (original - _cutter(scribe, p.cabinet_rear_y_mm)).solids()
        if not pieces:
            raise ValueError(f"Scan scribe removes the entire cabinet part: {shape.label}")
        # Keep the main piece attached to the original joint land. For the
        # filler that is its bottom face; the larger roof offcut sits above it.
        if shape.label == "Scribed ceiling filler":
            bottom = original.bounding_box().min.Z
            attached = [piece for piece in pieces if piece.bounding_box().min.Z < bottom + 0.1]
        else:
            inboard = min(piece.bounding_box().min.X for piece in pieces)
            attached = [piece for piece in pieces if piece.bounding_box().min.X < inboard + 0.1]
        kept = max(attached, key=lambda piece: piece.volume)
        result = Part(kept.moved(world.inverse()).solids(), label=shape.label, color=shape.color)
        result.location = shape.location
        return result

    return Compound(children=visit(cabinet, Location(), ()).children, label=cabinet.label, color=cabinet.color)
