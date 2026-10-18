"""Cutting envelopes from assembly leaves, independent of placement and display state."""

from typing import Any

from build123d import Location, Shape

from campervan.materials import CutPart
from campervan.parameters import Parameters


def material_for(path: tuple[str, ...]) -> str:
    name = path[-1].lower()
    if "Angle brackets" in path:
        return "brackets"
    if "Extension stops" in path and "plate" in name:
        return "stops"
    if "Rear drawer" in path and "Rails" in path:
        return "slides"
    if "Guide ledges" in path:
        return "guides"
    if name in {"fixed bearer", "bearer"}:
        return "bearers"
    if "Shelf ledges" in path:
        return "ledges"
    if "Shelves" in path:
        return "shelves"
    if "Rear drawer" in path and "Tray" in path:
        return "drawer"
    if "skin" in name or name == "separating panel":
        return "skins"
    if name in {"fixed deck", "plywood lid"}:
        return "deck"
    if "slat" in name:
        return "slats"
    if "frame" in name or name in {"rear header", "tie strip (extension stop)", "rear leg", "cab-end leg"}:
        return "frames"
    return "unassigned"


def cut_list(model: Shape[Any], parameters: Parameters) -> list[CutPart]:
    cuts = []

    def visit(part: Shape[Any], path: tuple[str, ...]) -> None:
        path = (*path, part.label)
        if "Vehicle references" in path or "Cushions" in path:
            return
        if part.children:
            for child in part.children:
                visit(child, path)
            return
        # Each leaf retains its construction geometry. Remove its local placement;
        # ancestor transforms (bed motion, lid hinge, mirroring) do not change stock sizes.
        size = part.located(Location()).bounding_box().size
        thickness, width, length = sorted(round(value, 2) for value in size)
        material = material_for(path)
        if material == "slides":
            # The fixed, intermediate and moving leaves describe the same two purchased slides.
            if "Fixed" not in path:
                return
            length, width, thickness = (
                parameters.drawer_length_mm,
                parameters.slide_height_mm,
                parameters.slide_thickness_mm,
            )
        elif material == "brackets":
            length, width, thickness = (
                parameters.bracket_arm_mm,
                parameters.bracket_width_mm,
                parameters.bracket_thickness_mm,
            )
        if material in {"ledges", "slats"}:
            width, thickness = (
                (parameters.cabinet_ledge_size_mm, parameters.cabinet_ledge_height_mm)
                if material == "ledges"
                else (parameters.slat_width_mm, parameters.slat_thickness_mm)
            )
            dimensions = list(size)
            for section in (width, thickness):
                dimensions.pop(min(range(len(dimensions)), key=lambda i: abs(dimensions[i] - section)))
            length = round(dimensions[0], 2)
        cuts.append(
            CutPart(path=" / ".join(path[1:]), material=material, length=length, width=width, thickness=thickness)
        )

    visit(model, ())
    return cuts
