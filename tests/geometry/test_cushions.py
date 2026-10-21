"""Check the six documented foam blocks; intermediate repositioning is a visual preview."""

from itertools import combinations

import pytest
from build123d import Compound

from campervan.cad.cushions import build_cushions, cushion_motion_tracks
from campervan.parameters import Parameters


def test_cushion_day_layout_and_conversion():
    day_bounds = [
        ((0, 0, 400), (600, 1280, 500)),
        ((0, 0, 500), (100, 1280, 735)),
        ((100, 0, 500), (630, 100, 735)),
        ((0, 1280, 400), (835, 1860, 500)),
        ((0, 1280, 500), (100, 1860, 735)),
        ((100, 1760, 500), (850, 1860, 735)),
    ]
    for percent in (0, 20, 40, 100):
        p = Parameters(bed_extension_percent=percent, cross_bed_extension_percent=percent)
        cushions = Compound(children=[build_cushions(p, "Long bench"), build_cushions(p, "Cross bench")])
        pieces = [leaf.located(leaf.global_location) for leaf in cushions.leaves]
        assert len(pieces) == 6 and all(piece.is_valid for piece in pieces)
        if percent <= 40:
            for piece, (lower, upper) in zip(pieces, day_bounds, strict=True):
                bounds = piece.bounding_box()
                assert tuple(bounds.min) == pytest.approx((lower[0] + 7, lower[1], lower[2]))
                assert tuple(bounds.max) == pytest.approx((upper[0] + 7, upper[1], upper[2]))
        else:
            bounds = cushions.bounding_box()
            assert tuple(bounds.min) == pytest.approx((7, 0, 400))
            assert tuple(bounds.max) == pytest.approx((1077, 1860, 735))
            assert sum(piece.volume for piece in pieces) == pytest.approx(1070 * 1860 * 100)
        for a, b in combinations(pieces, 2):
            overlap = a & b
            assert overlap is None or overlap.volume < 1e-6


def test_backrests_turn_above_seats_then_lower():
    # Include points between pose samples, when the viewer interpolates the motion.
    for percent in (47, 60, 75, 80, 90):
        p = Parameters(bed_extension_percent=percent, cross_bed_extension_percent=percent)
        long, cross = build_cushions(p, "Long bench"), build_cushions(p, "Cross bench")
        seats = [long.children[0], cross.children[0]]
        backrests = [long.children[1], cross.children[1]]
        for cushion in backrests:
            bounds = cushion.bounding_box()
            if percent <= 80:
                assert bounds.min.Z >= 500 - 1e-6
            if percent >= 80:
                assert bounds.size.Z == pytest.approx(100)
                assert bounds.min.X == pytest.approx(0 if cushion.label == "Wall backrest" else 835)
            for seat in seats:
                overlap = cushion & seat
                assert overlap is None or overlap.volume < 1e-6


def test_benches_position_their_own_cushions_independently():
    day = Parameters()
    for active, field, stationary in (
        ("Long bench", "bed_extension_percent", "Cross bench"),
        ("Cross bench", "cross_bed_extension_percent", "Long bench"),
    ):
        posed = Parameters.model_validate(day.model_dump() | {field: 100})
        unchanged = build_cushions(posed, stationary).bounding_box()
        expected = build_cushions(day, stationary).bounding_box()
        assert tuple(unchanged.min) == pytest.approx(tuple(expected.min))
        assert tuple(unchanged.max) == pytest.approx(tuple(expected.max))
        seat = build_cushions(posed, active).children[0].bounding_box()
        day_seat = build_cushions(day, active).children[0].bounding_box()
        assert seat.min.X > day_seat.min.X


def test_green_end_cushions_stay_upright_without_live_motion_tracks():
    for bench in ("Long bench", "Cross bench"):
        original = build_cushions(Parameters(), bench).children[2]
        for percent in (40, 60, 80, 100):
            p = Parameters(bed_extension_percent=percent, cross_bed_extension_percent=percent)
            cushion = build_cushions(p, bench).children[2]
            assert cushion.location == original.location
        tracks = cushion_motion_tracks(Parameters(), bench)
        assert not any(track["path"].endswith(f"/{original.label}") for track in tracks)
