"""Apply measured scan scribes to furniture wood, preserving placements and hardware."""

from typing import Any

from build123d import Compound, Face, Location, Part, Shape, Solid, Wire

from campervan.cad.scan_scribe_data import SCAN_SCRIBES, Loop, Scribe


def scan_clearance_mm(path: tuple[str, ...]) -> float | None:
    if "/".join(path[1:]) not in SCAN_SCRIBES:
        return None
    return {"Cabinet": 3.0, "Long bench": 5.0}[path[1]]


def _cutter(scribe: Scribe, offset: tuple[float, float, float]) -> Compound:
    axis, (start, finish), polygons = scribe
    other = [i for i in range(3) if i != axis]

    def wire(loop: Loop) -> Wire:
        points = []
        for u, v in loop:
            point = [0.0, 0.0, 0.0]
            point[axis], point[other[0]], point[other[1]] = start, u, v
            points.append([value - shift for value, shift in zip(point, offset, strict=True)])
        return Wire.make_polygon(points)

    direction = [0.0, 0.0, 0.0]
    direction[axis] = finish - start
    return Compound(
        [Solid.extrude(Face(wire(outer), [wire(hole) for hole in holes]), direction) for outer, holes in polygons]
    )


def scribe_assembly(assembly: Compound, offset: tuple[float, float, float], *, inboard: int) -> Compound:
    def visit(shape: Shape[Any], parent: Location, path: tuple[str, ...]) -> Shape[Any]:
        # Reparenting children rebuilds the old compound and can clear its location.
        # Capture metadata before recursion or constructing the replacement parent.
        label, color, pose = shape.label, shape.color, shape.location
        path = (*path, label)
        world = parent * pose
        if shape.children:
            result = Compound(children=[visit(child, world, path) for child in shape.children])
            result.label, result.color, result.location = label, color, pose
            return result
        scribe = SCAN_SCRIBES.get("/".join(path))
        if scribe is None:
            return shape
        original = Shape.cast(shape.wrapped).located(world)
        pieces = (original - _cutter(scribe, offset)).solids()
        if not pieces:
            raise ValueError(f"Scan scribe removes the entire furniture part: {shape.label}")
        # Keep the main piece attached to the original joint land. For the
        # filler that is its bottom face; the larger roof offcut sits above it.
        if shape.label == "Scribed ceiling filler":
            bottom = original.bounding_box().min.Z
            attached = [piece for piece in pieces if piece.bounding_box().min.Z < bottom + 0.1]
        else:
            if inboard < 0:
                land = min(piece.bounding_box().min.X for piece in pieces)
                attached = [piece for piece in pieces if piece.bounding_box().min.X < land + 0.1]
            else:
                land = max(piece.bounding_box().max.X for piece in pieces)
                attached = [piece for piece in pieces if piece.bounding_box().max.X > land - 0.1]
        kept = max(attached, key=lambda piece: piece.volume)
        result = Part(kept.moved(world.inverse()).solids(), label=shape.label, color=shape.color)
        result.location = pose
        return result

    return Compound(children=visit(assembly, Location(), ()).children, label=assembly.label, color=assembly.color)
