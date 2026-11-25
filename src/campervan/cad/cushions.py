"""Three foam blocks: fixed cross seat and convertible long-bench seat/backrest."""

from dataclasses import dataclass
from math import cos, pi, radians, sin

from build123d import Box, Color, Compound, Location

from campervan.cad.bed_motion import BED_EXTENDED, CUSHIONS_POSITIONED
from campervan.cad.bed_lift import lid_location
from campervan.cad.sliding_bed import long_bed_layout
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
    position_parameter: str | None = "bed_extension_percent"

    def poses(self) -> list[Pose]:
        if not any(self.day_rotation[:2]):
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
    backrest_height = p.bed_width_mm - width
    cross_length = end - length
    flat_z = height + foam / 2
    # Fold the wall backrest toward the wall while retaining the same day/night bounds.
    wall_rotation = (0.0, 90.0, 0.0)
    flat = (0.0, 0.0, 0.0)
    if backrest_height <= 0:
        raise ValueError("Cushions need positive bed infill.")
    if foam >= min(width / 2, cross_length, length):
        raise ValueError("Upright backrests must leave room on both seat cushions.")
    if bench == "Long bench":
        seat_width = width - 1.0  # Recess the foam 1 mm from the aisle face of the rail.
        return (
            Cushion(
                "Long seat",
                (seat_width, length, foam),
                (seat_width / 2, length / 2, flat_z),
                (backrest_height + seat_width / 2, length / 2, flat_z),
                flat,
                (0.19, 0.47, 0.63),
            ),
            Cushion(
                "Wall backrest",
                (backrest_height, length, foam),
                (foam / 2, length / 2, height + foam + backrest_height / 2),
                (backrest_height / 2, length / 2, flat_z),
                wall_rotation,
                (0.83, 0.52, 0.22),
            ),
        )
    if bench == "Cross bench":
        center = (p.bed_width_mm / 2, (length + end) / 2, flat_z)
        return (
            Cushion(
                "Cross seat",
                (p.bed_width_mm, cross_length, foam),
                center,
                center,
                flat,
                (0.26, 0.57, 0.70),
                position_parameter=None,
            ),
        )
    raise ValueError(f"Unknown cushion bench: {bench}")


def build_cushions(p: Parameters, bench: str) -> Compound:
    pieces = []
    lift = lid_cushion_locations(p, p.bed_lid_open_percent) if bench == "Long bench" else {}
    for cushion in cushion_layout(p, bench):
        core = Box(*cushion.size)
        core.label, core.color = "Core", Color(*cushion.color)
        # OCP extracts a box's corner/centring offset onto its mesh node. Animate
        # a real assembly parent so absolute tracks cannot overwrite that offset.
        foam = Compound(label="Foam", children=[core])
        foam.location = lift.get(cushion.label, Location())
        piece = Compound(label=cushion.label, children=[foam])
        percent = getattr(p, cushion.position_parameter) if cushion.position_parameter else 0
        piece.location = cushion.location(percent)
        pieces.append(piece)
    # Only a hierarchy/visibility anchor: cloth geometry and all pillow poses live in the browser.
    pillow = Box(600, 400, 200)
    pillow.label, pillow.color = "Pillow", Color(0.22, 0.22, 0.22)
    pieces.append(Compound(label="Rear pillow" if bench == "Long bench" else "Front pillow", children=[pillow]))
    # Both benches use the wall-side rail as the cushion datum.
    cushions = Compound(label="Cushions", children=pieces)
    cushions.location = Location((long_bed_layout(p).lid_rear, 0, 0))
    return cushions


def lid_cushion_locations(p: Parameters, percent: float) -> dict[str, Location]:
    """Foam-child poses keep storage lifting independent of parent conversion poses.

    The blue seat follows the linkage. The browser preserves its manufactured width
    and raises the upright backrest above its top plane, with only
    slight visual compression. There is no settling or material simulation.
    """
    layout = long_bed_layout(p)
    opened = lid_location(layout.lid_rear, layout.box_top, percent)
    closed = lid_location(layout.lid_rear, layout.box_top, 0)
    delta = opened * closed.inverse()
    seat, back = cushion_layout(p, "Long bench")
    offset = Location((layout.lid_rear, 0, 0))
    seat_base = offset * seat.location(0)
    return {
        seat.label: seat_base.inverse() * delta * seat_base,
        back.label: Location(),
    }


def lid_cushion_tracks(p: Parameters) -> list[dict[str, object]]:
    poses = [(percent, lid_cushion_locations(p, percent)) for percent in range(101)]
    tracks: list[dict[str, object]] = []
    for label in ("Long seat", "Wall backrest"):
        for index, axis in enumerate("xyz"):
            for kind in ("translation", "rotation"):
                tracks.append({
                    "path": f"/Campervan/Long bench/Cushions/{label}/Foam", "axis": axis, "kind": kind,
                    "keyframes": [(percent, round(tuple(getattr(locations[label],
                                      "position" if kind == "translation" else "orientation"))[index], 8))
                                  for percent, locations in poses],
                })
    return tracks


def cushion_motion_tracks(p: Parameters, position_parameter: str) -> list[dict[str, object]]:
    """Group CAD pose samples by their controller; the fixed cross seat has no controller."""
    tracks: list[dict[str, object]] = []
    for bench in ("Long bench", "Cross bench"):
        for cushion in cushion_layout(p, bench):
            if cushion.position_parameter != position_parameter:
                continue
            path = f"/Campervan/{bench}/Cushions/{cushion.label}"
            poses = cushion.poses()
            for i, axis in enumerate("xyz"):
                for kind in ("translation", "rotation"):
                    values = [
                        (percent, (center if kind == "translation" else rotation)[i])
                        for percent, center, rotation in poses
                    ]
                    if any(value != values[0][1] for _, value in values[1:]):
                        tracks.append({"path": path, "axis": axis, "kind": kind, "keyframes": values})
    return tracks
