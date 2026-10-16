"""Stages of the shared seat-to-bed slider, used by CAD and viewer motion."""

BED_EXTENDED = 40
CUSHIONS_POSITIONED = 80


def bed_offset(travel: float, percent: float) -> float:
    return travel * min(percent / BED_EXTENDED, 1)


def bed_keyframes(travel: float) -> list[tuple[float, float]]:
    return [(percent, bed_offset(travel, percent)) for percent in (0, BED_EXTENDED, 100)]
