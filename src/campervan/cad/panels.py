"""Plywood panels in local coordinates: X along, Y thickness, Z up."""

from build123d import Align, Axis, Box, Location, Part, fillet


def panel(length: float, thickness: float, height: float) -> Part:
    return Box(length, thickness, height, align=(Align.MIN, Align.MIN, Align.MIN))


def frame_panel(
    length: float,
    thickness: float,
    height: float,
    openings: list[tuple[float, float, float, float]],
    radius: float,
) -> Part:
    """Cut rounded openings (left, right, bottom, top); negative bottoms make open feet."""
    result = panel(length, thickness, height)
    for left, right, bottom, top in openings:
        if right - left <= 2 * radius or top - bottom <= 2 * radius:
            raise ValueError("Frame opening is too small for its corner radius.")
        cutter = panel(right - left, thickness + 2, top - bottom)
        cutter = fillet(cutter.edges().filter_by(Axis.Y), radius)
        result -= cutter.moved(Location((left, -1, bottom)))
    return result


def slide_mount_frame(
    length: float, thickness: float, height: float, member: float, band: float, radius: float,
    *, cab_end_width: float | None = None,
) -> Part:
    """Two openings above a continuous rail mounting band."""
    bay = (length - 3 * member) / 2
    return frame_panel(
        length,
        thickness,
        height,
        [(member, member + bay, band, height - member),
         (2 * member + bay, length - (cab_end_width if cab_end_width is not None else member), band, height - member)],
        radius,
    )
