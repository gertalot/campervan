"""Nominal section for the Taskmaster 27mm piano hinge; physical drill pattern unconfirmed."""

from build123d import Align, Color, Cylinder, Location, Part

from campervan.cad.panels import panel

HINGE_PROJECTION = 1.8
BACKING_SIZE = 18.0
END_CLEARANCE = 10.0


def piano_leaves(length: float, gap: float, pose: Location) -> tuple[Part, Part]:
    """Folded leaves in local X depth/Y gap/Z length; only the knuckle shows at the front.

    Open width27mm is sourced. The 0.8mm sheet, 2mm pin and 3.6mm knuckles are
    nominal preview dimensions, not Taskmaster drilling or mortising specifications.
    """
    thickness, radius, pin_radius = 0.8, HINGE_PROJECTION, 1.0
    segments = max(3, round(length / 12))
    pitch = length / segments
    halves = []
    for moving in (False, True):
        y = gap / 2 - thickness if moving else -gap / 2
        solids = list(panel(13.5 - radius, thickness, length).moved(Location((radius, y, 0))).solids())
        for index in range(segments):
            if bool(index % 2) != moving:
                continue
            z = index * pitch
            barrel = Cylinder(radius, pitch, align=(Align.CENTER, Align.CENTER, Align.MIN))
            barrel -= Cylinder(pin_radius, pitch, align=(Align.CENTER, Align.CENTER, Align.MIN))
            solids.extend(barrel.moved(Location((0, 0, z))).solids())
            solids.extend(panel(radius, thickness, pitch).moved(Location((0, y, z))).solids())
        if not moving:
            solids.extend(Cylinder(pin_radius, length, align=(Align.CENTER, Align.CENTER, Align.MIN)).solids())
        part = Part(solids, label=f"Piano hinge {'moving' if moving else 'fixed'} leaf (nominal section)",
                    color=Color(0.65, 0.67, 0.69))
        part.location = pose
        halves.append(part)
    return halves[0], halves[1]
