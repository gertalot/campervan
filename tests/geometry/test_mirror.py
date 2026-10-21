"""Small reflection and live-pose check; appearance remains a manual viewer check."""

import pytest
from build123d import Location, Shape

from campervan.cad.cushions import build_cushions, cushion_motion_tracks
from campervan.cad.mirror import mirror_assembly, mirror_motion_tracks
from campervan.parameters import Parameters


def vertices(part):
    placed = Shape.cast(part.wrapped).located(part.global_location)
    return sorted(tuple(round(v, 5) for v in vertex.center()) for vertex in placed.vertices())


def test_native_mirror_and_live_cushion_poses_agree():
    p = Parameters()
    for bench, field in (("Long bench", "bed_extension_percent"), ("Cross bench", "cross_bed_extension_percent")):
        tracks = mirror_motion_tracks(cushion_motion_tracks(p, bench))
        assert tracks and all(track["path"].startswith(f"/Campervan/{bench}/Cushions/") for track in tracks)
        for percent in (0, 60, 100):
            original = build_cushions(Parameters.model_validate(p.model_dump() | {field: percent}), bench)
            mirrored = mirror_assembly(original).moved(Location((p.cargo_width_mm, p.furniture_rear_gap_mm, 0)))
            for source, target in zip(original.leaves, mirrored.leaves, strict=True):
                assert source.label == target.label and target.is_valid
                assert target.volume == pytest.approx(source.volume)
                expected = sorted(
                    (round(p.cargo_width_mm - x, 5), round(y + p.furniture_rear_gap_mm, 5), z)
                    for x, y, z in vertices(source)
                )
                assert vertices(target) == expected
            # Apply the viewer's absolute local tracks to a day-time assembly,
            # then compare against CAD regenerated at the same slider position.
            live = mirror_assembly(build_cushions(p, bench)).moved(
                Location((p.cargo_width_mm, p.furniture_rear_gap_mm, 0))
            )
            for piece in live.children:
                position, rotation = list(piece.location.position), list(piece.location.orientation)
                for track in tracks:
                    if track["path"] != f"/Campervan/{bench}/Cushions/{piece.label}":
                        continue
                    points = track["keyframes"]
                    for (start, a), (end, b) in zip(points, points[1:], strict=False):
                        if start <= percent <= end:
                            values = rotation if track["kind"] == "rotation" else position
                            values["xyz".index(track["axis"])] = a + (b - a) * (percent - start) / (end - start)
                            break
                piece.location = Location(tuple(position), tuple(rotation))
            for posed, rebuilt in zip(live.leaves, mirrored.leaves, strict=True):
                assert vertices(posed) == vertices(rebuilt)
