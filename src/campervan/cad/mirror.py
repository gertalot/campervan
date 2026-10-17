"""Reflect furniture geometry, local placements and viewer motion through X = 0."""

from typing import Any, cast

from build123d import Compound, Location, Plane, Shape


def mirror_assembly(source: Shape[Any]) -> Shape[Any]:
    """Keep named children and proper rotations; reflect each leaf's native geometry.

    For reflection S, each local pose becomes S T S and each leaf becomes S G.
    The factors cancel through the hierarchy, giving S times the original assembly.
    A final translation by the van width places the mirror plane at its centreline.
    """
    if source.children:
        mirrored: Shape[Any] = Compound(children=[mirror_assembly(child) for child in source.children])
    else:
        # Start with a detached topology wrapper so copying a leaf doesn't also
        # copy its ancestor tree. A Compound.mirror alone leaves named children unchanged.
        mirrored = Shape.cast(source.wrapped).located(Location()).mirror(Plane.YZ)
    position, angles = source.location.position, source.location.orientation
    mirrored.location = Location((-position.X, position.Y, position.Z), (angles.X, -angles.Y, -angles.Z))
    mirrored.label, mirrored.color = source.label, source.color
    return mirrored


def mirror_motion_tracks(tracks: list[dict[str, object]]) -> list[dict[str, object]]:
    """Reflect local translation vectors and rotation axes, including absolute keyframes."""
    result = []
    for track in tracks:
        mirrored = track.copy()
        axis, kind = track["axis"], track.get("kind", "translation")
        reverse = axis in ("y", "z") if kind == "rotation" else axis == "x"
        if reverse:
            if "travel" in track:
                mirrored["travel"] = -cast(float, track["travel"])
            if "keyframes" in track:
                mirrored["keyframes"] = [
                    (percent, -value) for percent, value in cast(list[tuple[float, float]], track["keyframes"])
                ]
        result.append(mirrored)
    return result
