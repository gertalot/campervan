"""Cutting envelopes from assembly leaves, independent of placement and display state."""

from typing import Any
import logging

from build123d import Location, Shape

from campervan.materials import CutPart
from campervan.parameters import Parameters
from campervan.cad.cut_profiles import flat_profile


def material_for(path: tuple[str, ...]) -> str:
    name = path[-1].lower()
    if name == "finished floor plywood":
        return "floor"
    if name.startswith("point latch"):
        return "cabinet-catches"
    if name.endswith("strike block"):
        return "ledges"
    if "Cabinet" in path and "Doors" in path:
        return "cabinet-doors"
    if "Cabinet" in path and name == "back lining":
        return "cabinet-back"
    if "Cabinet" in path and (
        "frame" in name or "Wall supports" in path or name in {"middle panel", "cab-end panel", "rear upper panel"}
    ):
        return "cabinet-frames"
    if "Angle brackets" in path:
        return "brackets"
    if "Rear drawer" in path and "Rails" in path:
        return "slides"
    if "Guide ledges" in path:
        return "guides"
    if "Shelf ledges" in path or "Corner cleats" in path or "Rail joint blocks" in path:
        return "ledges"
    if "Shelves" in path:
        return "shelves"
    if "Rear drawer" in path and "Tray" in path:
        return "drawer"
    if "skin" in name or name == "separating panel":
        return "skins"
    if "slat" in name:
        return "slats"
    if "frame" in name or name in {"rear header", "tie strip (extension stop)", "rear leg", "cab-end leg"}:
        return "frames"
    return "unassigned"


def cut_list(model: Shape[Any], parameters: Parameters) -> list[CutPart]:
    cuts = []

    def visit(part: Shape[Any], path: tuple[str, ...]) -> None:
        path = (*path, part.label)
        if any(group in path for group in ("Vehicle references", "Cushions", "Stored gear")):
            return
        if "Latch strikes" in path:
            return  # Supplied with the purchased Point latches.
        if part.children:
            for child in part.children:
                visit(child, path)
            return
        # Each leaf retains its construction geometry. Remove its local placement;
        # ancestor transforms (bed motion, lid hinge, mirroring) do not change stock sizes.
        size = part.located(Location()).bounding_box().size
        thickness, width, length = sorted(round(value, 2) for value in size)
        material = material_for(path)
        profile = {}
        if material == "cabinet-back":
            from campervan.cad.cabinet import cabinet_back_profile

            centre = cabinet_back_profile(
                parameters, parameters.cabinet_back_clearance_mm + parameters.cabinet_back_thickness_mm / 2
            )
            length, width = sorted((round(centre.length, 2), round(size.Y, 2)), reverse=True)
            thickness = parameters.cabinet_back_thickness_mm
            profile = {"profile_note": "Developed rectangular blank. Transfer the wheel-arch notch from a van template; confirm flute direction."}
        elif material == "slides":
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
        if material in {"floor", "frames", "cabinet-frames", "skins", "shelves", "drawer", "cabinet-doors", "guides"}:
            try:
                profile = flat_profile(part)
            except (ValueError, RuntimeError, IndexError) as error:
                logging.getLogger(__name__).warning("Cutting profile for %s: %s", part.label, error)
                profile = {"profile_note": f"Rectangle only: CAD outline extraction failed ({error}). Transfer the profile before cutting."}
        cuts.append(
            CutPart(path=" / ".join(path[1:]), material=material, length=length, width=width, thickness=thickness, **profile)
        )

    visit(model, ())
    return cuts
