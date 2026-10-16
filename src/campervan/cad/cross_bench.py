"""Cross-bench carcass, divider and fixed deck from nv200-interior.fs."""

from build123d import Color, Compound, Location, Part

from campervan.cad.cross_bed import (
    build_cross_slats,
    build_cross_sliding_assembly,
    build_storage_lid,
    cross_bed_layout,
    relieve_cross_support,
)
from campervan.cad.cushions import build_cushions
from campervan.cad.panels import frame_panel, panel
from campervan.parameters import Parameters


def build_cross_bench(p: Parameters) -> Compound:
    layout = cross_bed_layout(p)
    width = layout.width
    rear, front = p.seat_length_mm, p.cargo_length_mm
    length = front - rear
    thickness, skin = p.frame_thickness_mm, p.wall_thickness_mm
    total = thickness + skin
    height = p.platform_height_mm - p.slat_thickness_mm - p.cross_deck_thickness_mm
    member, radius = p.member_width_mm, p.inside_radius_mm
    aisle_inner = width - thickness
    toilet_face = aisle_inner - p.cross_toilet_bay_depth_mm
    storage_face = toilet_face - total
    divider_length = length - 2 * skin
    deck_start = layout.deck_start

    if width <= p.long_bench_width_mm or length <= 2 * total or height <= 2 * member + 2 * radius:
        raise ValueError("Cross bench needs space behind the long bench and below the deck for its frames.")
    if storage_face <= total or member <= thickness:
        raise ValueError("Toilet bay must leave a storage compartment and material below the divider recesses.")
    if p.cross_storage_lid_gap_mm >= min(thickness / 2, skin):
        raise ValueError("Storage lid gap must leave bearing on the divider and surrounding walls.")

    parts: list[Part | Compound] = []

    def place(part: Part, name: str, x: float, y: float, *, rotation: float = 0, is_skin: bool = False) -> Part:
        part.label = name
        part.color = Color(0.75, 0.66, 0.49) if is_skin else Color(0.88, 0.61, 0.25)
        part.location = Location((x, y, 0), (0, 0, rotation))
        return part

    def open_frame(span: float) -> Part:
        return frame_panel(span, thickness, height, [(member, span - member, -2 * radius, height - member)], radius)

    parts.extend(
        [
            place(open_frame(length), "Wall-side frame", total, rear, rotation=90),
            relieve_cross_support(place(open_frame(length), "Aisle frame", width, rear, rotation=90), p, layout),
        ]
    )
    end_width = aisle_inner - total
    for name, frame_y, skin_y in (
        ("Rear", rear + skin, rear),
        ("Cab-end", front - total, front - skin),
    ):
        parts.append(place(open_frame(end_width), f"{name} frame", total, frame_y))
        parts.append(place(panel(end_width, skin, height), f"{name} skin", total, skin_y, is_skin=True))

    divider = []
    for name, ply, x, is_skin in (
        ("Frame", thickness, toilet_face - skin, False),
        ("Separating panel", skin, toilet_face, True),
    ):
        piece = panel(divider_length, ply, height)
        if not is_skin:
            piece = frame_panel(
                divider_length,
                ply,
                height,
                [(member, divider_length - member, member, height - member)],
                radius,
            )
        # Local X runs along the van. Both layers clear the end frames' top beams.
        for start in (0, divider_length - thickness):
            piece -= panel(thickness, ply + 2, member + 1).moved(Location((start, -1, height - member)))
        divider.append(place(piece, name, x, rear + skin, rotation=90, is_skin=is_skin))
    parts.append(Compound(label="Toilet-storage divider", children=divider))

    deck = panel(width - deck_start, length, p.cross_deck_thickness_mm)
    deck.label, deck.color = "Fixed deck", Color(0.75, 0.66, 0.49)
    deck.location = Location((deck_start, rear, height))
    parts.extend([relieve_cross_support(deck, p, layout), build_cross_slats(p, layout, moving=False)])
    return Compound(
        label="Cross bench",
        children=[
            Compound(label="Fixed frame", children=parts),
            build_cross_sliding_assembly(p, layout),
            build_storage_lid(p, layout),
            build_cushions(p, "Cross bench"),
        ],
    )
