"""Cutting envelopes from assembly leaves, independent of placement and display state."""

import logging
from typing import Any

from build123d import Location, Shape

from campervan.cad.cut_profiles import flat_profile
from campervan.materials import CutPart
from campervan.parameters import Parameters


def material_for(path: tuple[str, ...]) -> str:
    name = path[-1].lower()
    if "Laptop table" in path:
        return "table-plywood" if name in {"fixed tabletop leaf", "folding tabletop leaf"} else "frames"
    if name == "finished floor plywood":
        return "floor"
    if name.startswith("roller catch keeper"):
        return "cabinet-catches"
    if "Module fasteners" in path:
        return "cabinet-module-fasteners"
    if "Cabinet" in path:
        if name == "wheel-arch bridge":
            return "cabinet-bridge"
        if "Frames" in path:
            return "cabinet-frames"
        if "Skin" in path:
            return "cabinet-partitions"
        if name == "plywood door":
            return "cabinet-doors"
    if "Angle brackets" in path:
        return "brackets"
    if "Rear drawer" in path and "Drawer sliders" in path:
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
        if any(group in path for group in ("Vehicle references", "Cushions", "Stored gear", "Lagun hardware")):
            return
        if "Laptop table" in path and "Stowed" in path:
            return  # Another pose of the same two leaves and purchased leg kit.
        if "Laptop table" in path and "Table hinges · Homer HOM006136" in path:
            return  # One purchased pair; the moving halves follow their tabletop leaves.
        if "Hinges" in path or "Keeper fixings" in path or any(name.endswith("fixed hardware") for name in path):
            return  # Purchased hinges/bodies: count the static hinge role and moving catch keeper only.
        if "Roller catch bodies" in path:
            return  # One catch set is counted by its moving keeper.
        if part.children:
            for child in part.children:
                visit(child, path)
            return
        # Each leaf retains its construction geometry. Remove its local placement;
        # ancestor transforms (bed motion, lid hinge, mirroring) do not change stock sizes.
        size = Shape.cast(part.wrapped).located(Location()).bounding_box().size
        thickness, width, length = sorted(round(value, 2) for value in size)
        material = material_for(path)
        profile: dict[str, Any] = {}
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
        if material in {"slats", "cabinet-frames", "cabinet-bridge"}:
            if material == "cabinet-frames":
                width, thickness = parameters.cabinet_frame_width_mm, parameters.cabinet_frame_thickness_mm
            elif material == "cabinet-bridge":
                width, thickness = parameters.cabinet_bridge_height_mm, parameters.cabinet_bridge_thickness_mm
            else:
                width, thickness = parameters.slat_width_mm, parameters.slat_thickness_mm
            dimensions = list(size)
            for section in (width, thickness):
                dimensions.pop(min(range(len(dimensions)), key=lambda i: abs(dimensions[i] - section)))
            length = round(dimensions[0], 2)
            if material in {"cabinet-frames", "cabinet-bridge"}:
                profile = {
                    "profile_note": "Square-cut stock. Side joining rails have shelf seats and solid bolt lands; "
                    "match-drill fixings."
                }
        if material in {
            "floor",
            "frames",
            "cabinet-partitions",
            "skins",
            "shelves",
            "drawer",
            "cabinet-doors",
            "guides",
            "table-plywood",
        }:
            try:
                profile = flat_profile(part)
            except (ValueError, RuntimeError, IndexError) as error:
                logging.getLogger(__name__).warning("Cutting profile for %s: %s", part.label, error)
                profile = {
                    "profile_note": f"Rectangle only: CAD outline extraction failed ({error}). "
                    "Transfer the profile before cutting."
                }
        cuts.append(
            CutPart(
                path=" / ".join(path[1:]), material=material, length=length, width=width, thickness=thickness, **profile
            )
        )

    visit(model, ())
    return cuts
