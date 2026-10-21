"""Six foam blocks and their hand-repositioned day/night layouts from nv200-interior.fs."""

from dataclasses import dataclass
from math import cos, pi, radians, sin

from build123d import Box, Color, Compound, Location

from campervan.cad.bed_motion import BED_EXTENDED, CUSHIONS_POSITIONED
from campervan.parameters import Parameters

Vector3 = tuple[float, float, float]
Pose = tuple[float, Vector3, Vector3]


@dataclass(frozen=True)
class Cushion:
    label: str
    size: Vector3
    day_center: Vector3
    night_center: Vector3
    day_rotation: Vector3
    color: Vector3
    fixed: bool = False

    def poses(self) -> list[Pose]:
        if self.fixed:
            return [(0, self.day_center, self.day_rotation), (100, self.day_center, self.day_rotation)]
        if not any(self.day_rotation):
            # Seats clear the infill spaces before the backrests start descending.
            return [
                (0, self.day_center, self.day_rotation),
                (BED_EXTENDED, self.day_center, self.day_rotation),
                (CUSHIONS_POSITIONED, self.night_center, (0, 0, 0)),
                (100, self.night_center, (0, 0, 0)),
            ]
        # Turn and reposition above the seats, then lower vertically into the infill spaces.
        poses: list[Pose] = [(0, self.day_center, self.day_rotation)]
        seat_top = self.night_center[2] + self.size[2] / 2
        for step in range(14):
            progress = step / 13
            percent = BED_EXTENDED + progress * (CUSHIONS_POSITIONED - BED_EXTENDED)
            ax, ay, az = (angle * (1 - progress) for angle in self.day_rotation)
            rx, ry, rz = radians(ax), radians(ay), radians(az)
            # Z components of the local box axes after intrinsic XYZ rotation.
            vertical = (
                sin(rx) * sin(rz) - cos(rx) * sin(ry) * cos(rz),
                sin(rx) * cos(rz) + cos(rx) * sin(ry) * sin(rz),
                cos(rx) * cos(ry),
            )
            half_height = sum(size * abs(axis) for size, axis in zip(self.size, vertical, strict=True)) / 2
            x = self.day_center[0] + progress * (self.night_center[0] - self.day_center[0])
            y = self.day_center[1] + progress * (self.night_center[1] - self.day_center[1])
            # Small handling clearance also covers interpolation between the sampled poses.
            z = seat_top + half_height + 5 * sin(pi * progress)
            poses.append((percent, (x, y, z), (ax, ay, az)))
        poses.append((100, self.night_center, (0, 0, 0)))
        return poses

    def location(self, percent: float) -> Location:
        poses = self.poses()
        for (start, a, angles_a), (end, b, angles_b) in zip(poses, poses[1:], strict=False):
            if percent <= end:
                fraction = (percent - start) / (end - start)
                center = tuple(a[i] + fraction * (b[i] - a[i]) for i in range(3))
                x, y, z = (angles_a[i] + fraction * (angles_b[i] - angles_a[i]) for i in range(3))
                return Location(center, (x, y, z))
        return Location(self.night_center)


def cushion_layout(p: Parameters, bench: str) -> tuple[Cushion, ...]:
    width, length, end = p.long_bench_width_mm, p.seat_length_mm, p.cargo_length_mm
    foam, height = p.foam_thickness_mm, p.platform_height_mm
    infill = (p.bed_width_mm - width) / 2
    cross_width, cross_length = width + infill, end - length
    rear_length = length - p.cab_backrest_length_mm
    flat_z, upright_z = height + foam / 2, height + foam + infill / 2
    # Fold the wall backrests toward the wall while retaining the same day/night bounds.
    wall_rotation = (0.0, 90.0, 0.0)
    end_rotation = (90.0, 0.0, 90.0)
    flat = (0.0, 0.0, 0.0)
    green = (0.46, 0.61, 0.35)
    if infill <= 0 or not 0 < p.cab_backrest_length_mm < length:
        raise ValueError("Cushions need positive bed infill and a cab-facing backrest shorter than the long bench.")
    if foam >= min(width, cross_width, cross_length, length):
        raise ValueError("Upright backrests must leave room on both seat cushions.")
    if bench == "Long bench":
        return (
            Cushion(
                "Long seat",
                (width, length, foam),
                (width / 2, length / 2, flat_z),
                (infill + width / 2, length / 2, flat_z),
                flat,
                (0.19, 0.47, 0.63),
            ),
            Cushion(
                "Wall backrest",
                (infill, length, foam),
                (foam / 2, length / 2, upright_z),
                (infill / 2, length / 2, flat_z),
                wall_rotation,
                (0.83, 0.52, 0.22),
            ),
            Cushion(
                "Rear end backrest",
                (infill, rear_length, foam),
                (foam + rear_length / 2, foam / 2, upright_z),
                (width + 1.5 * infill, rear_length / 2, flat_z),
                end_rotation,
                green,
                fixed=True,
            ),
        )
    if bench == "Cross bench":
        return (
            Cushion(
                "Cross seat",
                (cross_width, cross_length, foam),
                (cross_width / 2, (length + end) / 2, flat_z),
                (infill + cross_width / 2, (length + end) / 2, flat_z),
                flat,
                (0.26, 0.57, 0.70),
            ),
            Cushion(
                "Wall backrest",
                (infill, cross_length, foam),
                (foam / 2, (length + end) / 2, upright_z),
                (infill / 2, (length + end) / 2, flat_z),
                wall_rotation,
                (0.64, 0.43, 0.66),
            ),
            Cushion(
                "Cab-facing backrest",
                (infill, p.cab_backrest_length_mm, foam),
                (foam + p.cab_backrest_length_mm / 2, end - foam / 2, upright_z),
                (width + 1.5 * infill, rear_length + p.cab_backrest_length_mm / 2, flat_z),
                end_rotation,
                green,
                fixed=True,
            ),
        )
    raise ValueError(f"Unknown cushion bench: {bench}")


def build_cushions(p: Parameters, bench: str) -> Compound:
    pieces = []
    for cushion in cushion_layout(p, bench):
        foam = Box(*cushion.size)
        foam.label, foam.color = "Foam", Color(*cushion.color)
        piece = Compound(label=cushion.label, children=[foam])
        percent = p.bed_extension_percent if bench == "Long bench" else p.cross_bed_extension_percent
        piece.location = cushion.location(percent)
        pieces.append(piece)
    # Keep wall clearance on the parent so CAD poses and live child motion share the offset.
    cushions = Compound(label="Cushions", children=pieces)
    cushions.location = Location((7, 0, 0))
    return cushions


def cushion_motion_tracks(p: Parameters, bench: str) -> list[dict[str, object]]:
    """Share the CAD pose samples with the viewer, including the lift/turn/lower sequence."""
    tracks: list[dict[str, object]] = []
    for cushion in cushion_layout(p, bench):
        path = f"/Campervan/{bench}/Cushions/{cushion.label}"
        poses = cushion.poses()
        for i, axis in enumerate("xyz"):
            for kind in ("translation", "rotation"):
                values = [
                    (percent, (center if kind == "translation" else rotation)[i]) for percent, center, rotation in poses
                ]
                if any(value != values[0][1] for _, value in values[1:]):
                    tracks.append({"path": path, "axis": axis, "kind": kind, "keyframes": values})
    return tracks
