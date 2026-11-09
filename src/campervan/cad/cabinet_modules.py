"""Side-only countersunk module bolts, flush below the chair-loading opening."""

from build123d import Align, Color, Cone, Cylinder, Location, Part

from campervan.parameters import Parameters


def module_fasteners(p: Parameters, split: float, centres: list[tuple[float, float]]) -> tuple[list[Part], list[Part]]:
    depth = p.cabinet_frame_width_mm
    bottom, top = split - depth, split + depth
    length = 90.0
    if 2 * depth + 1 + 5 + 2 > length:
        raise ValueError("Cabinet module rails are too deep for the nominal M5 × 90mm joint screws.")
    bores: list[Part] = []
    fasteners: list[Part] = []
    for index, (x, y) in enumerate(centres, 1):
        bore = Cylinder(2.75, 2 * depth + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        countersink = Cone(5.2, 2.75, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
        bores.extend((bore.moved(Location((x, y, bottom - 1))), countersink.moved(Location((x, y, bottom)))))
        shaft = Cylinder(2.5, length - 3, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((x, y, bottom + 3))
        )
        head = Cone(5, 2.5, 3, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, bottom)))
        washer = (
            Cylinder(7.5, 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
            - Cylinder(2.75, 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        ).moved(Location((x, y, top)))
        nut = (
            Cylinder(4.5, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
            - Cylinder(2.5, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        ).moved(Location((x, y, top + 1)))
        fastener = Part(
            [*shaft.solids(), *head.solids(), *washer.solids(), *nut.solids()],
            label=f"Side module screw {index} · M5 × 90 (estimated envelope)",
        )
        fastener.color = Color(0.43, 0.45, 0.48)
        fasteners.append(fastener)
    return bores, fasteners
