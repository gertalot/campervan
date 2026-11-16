"""Cross-bench frame datums and the nominal Lagun bracket width."""

from dataclasses import dataclass

from campervan.parameters import Parameters

LAGUN_BRACKET_WIDTH = 92.0


@dataclass(frozen=True)
class CrossBenchLayout:
    wall_x: float
    aisle_x: float
    rear: float
    length: float
    height: float
    mounting_post_width: float


def cross_bench_layout(p: Parameters) -> CrossBenchLayout:
    aisle_x = p.bed_width_mm - p.cross_bench_overhang_mm - p.frame_thickness_mm
    post = max(p.member_width_mm, LAGUN_BRACKET_WIDTH)
    return CrossBenchLayout(
        wall_x=p.cross_bench_support_x_mm,
        aisle_x=aisle_x,
        rear=p.seat_length_mm,
        length=p.cargo_length_mm - p.seat_length_mm,
        height=p.platform_height_mm - p.slat_thickness_mm,
        mounting_post_width=post,
    )
