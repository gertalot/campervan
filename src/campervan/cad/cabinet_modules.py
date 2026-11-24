"""Side module joints with ordinary M6 hex bolts and washers on both faces."""

from build123d import Align, Color, Cylinder, Location, Part, RegularPolygon, Solid

from campervan.parameters import Parameters


def module_fasteners(p: Parameters, split: float, centres: list[tuple[float, float]]) -> tuple[list[Part], list[Part]]:
    depth = p.cabinet_frame_width_mm
    bottom, top = split - depth, split + depth
    length = 90.0
    washer_thickness, nut_height = 1.6, 5.0
    if p.cabinet_frame_thickness_mm < 16:
        raise ValueError("The cabinet cross rails must support the full 16mm module bolt washers.")
    if 2 * depth + 2 * washer_thickness + nut_height >= length:
        raise ValueError("Cabinet module rails leave insufficient thread for the M6 × 90mm bolt and nut.")
    bores: list[Part] = []
    fasteners: list[Part] = []
    for index, (x, y) in enumerate(centres, 1):
        bore = Cylinder(3.25, 2 * depth + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        bores.append(bore.moved(Location((x, y, bottom - 1))))
        shaft = Cylinder(3, length, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
            Location((x, y, bottom - washer_thickness))
        )
        hex_face = RegularPolygon(10 / 3**0.5, 6).faces()[0]
        head = Solid.extrude(hex_face, (0, 0, 4)).moved(Location((x, y, bottom - washer_thickness - 4)))
        washer = (
            Cylinder(8, washer_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
            - Cylinder(3.25, washer_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
        ).moved(Location((x, y, top)))
        lower_washer = washer.moved(Location((0, 0, bottom - washer_thickness - top)))
        nut = (Solid.extrude(hex_face, (0, 0, nut_height))
               - Cylinder(3, nut_height, align=(Align.CENTER, Align.CENTER, Align.MIN))).moved(
            Location((x, y, top + washer_thickness))
        )
        fastener = Part(
            [*shaft.solids(), *head.solids(), *washer.solids(), *lower_washer.solids(), *nut.solids()],
            label=f"Side module bolt {index} · M6 × 90 (estimated envelope)",
        )
        fastener.color = Color(0.43, 0.45, 0.48)
        fasteners.append(fastener)
    return bores, fasteners
