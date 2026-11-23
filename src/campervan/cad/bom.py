"""Cutting envelopes from assembly leaves, independent of placement and display state."""

import logging
from typing import Any

from build123d import Location, Shape

from campervan.cad.scan_scribing import scan_clearance_mm
from campervan.cad.cut_profiles import cutting_axes, fitting_datums, flat_profile
from campervan.cad.fitting import VehicleFitting
from campervan.materials import CutPart
from campervan.parameters import Parameters


def material_for(path: tuple[str, ...]) -> str:
    name = path[-1].lower()
    if "Storage box" in path:
        return "frames"
    if "Slat angle brackets" in path:
        return "bed-slat-brackets"
    if "Moving front slat support" in path:
        return "frames"
    if name in {"slotted plywood lid", "wall-side cushion rail"}:
        return "frames"
    if "Lid hinges" in path:
        return "bed-lid-hinges"
    if "Laptop table" in path:
        return "table-plywood" if name in {"fixed tabletop leaf", "folding tabletop leaf"} else "frames"
    if "Finished floor plywood" in path:
        if "Floor insulation" in path:
            return "floor-insulation"
        return "floor-ribs" if "Pine rib frame" in path else "floor"
    if name.startswith("roller catch keeper"):
        return "cabinet-catches"
    if "Module fasteners" in path:
        return "cabinet-module-fasteners"
    if "Cabinet" in path:
        if name == "cabinet 3 fixed cover":
            return "cabinet-partitions"
        if "Shelf ledges" in path:
            return "cabinet-shelf-ledges"
        if "Backing glue cleats" in path:
            return "cabinet-backing-cleats"
        if name == "pine hinge backing strip":
            return "cabinet-hinge-backing"
        if name == "rear top removable infill":
            return "cabinet-doors"
        if name == "wheel-arch bridge":
            return "cabinet-bridge"
        if "Frames" in path:
            return "cabinet-frames"
        if "Skin" in path:
            return "cabinet-partitions"
        if name == "plywood door":
            return "cabinet-doors"
    if "Shelf ledges" in path or "Corner cleats" in path or "Rail joint blocks" in path:
        return "ledges"
    if "Shelves" in path:
        return "shelves"
    if "slat" in name:
        return "slats"
    if "frame" in name or name in {"rear header", "tie strip (extension stop)", "rear leg", "cab-end leg"}:
        return "frames"
    return "unassigned"


def cut_list(model: Shape[Any], parameters: Parameters) -> list[CutPart]:
    cuts = []
    fitting = VehicleFitting(parameters.cargo_width_mm, parameters.floor_surface_z_mm)

    def visit(part: Shape[Any], path: tuple[str, ...], parent: Location) -> None:
        world = parent * part.location
        path = (*path, part.label)
        if any(group in path for group in ("Vehicle references", "Cushions", "Stored gear", "Lagun hardware")):
            return
        if "Lid hinges" in path:
            return  # Whole purchased items use explicit role quantities, not component envelopes.
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
                visit(child, path, world)
            return
        # Each leaf retains its construction geometry. Remove its local placement;
        # ancestor transforms (bed motion, lid hinge, mirroring) do not change stock sizes.
        size = Shape.cast(part.wrapped).located(Location()).bounding_box().size
        thickness, width, length = sorted(round(value, 2) for value in size)
        material = material_for(path)
        clearance = scan_clearance_mm(path)
        scribed = clearance is not None
        profile: dict[str, Any] = {}
        axes = cutting_axes(part)
        if material in {"slats", "cabinet-frames", "cabinet-bridge", "cabinet-hinge-backing",
                        "cabinet-backing-cleats", "cabinet-shelf-ledges", "floor-ribs"}:
            if material == "cabinet-frames":
                width, thickness = parameters.cabinet_frame_width_mm, parameters.cabinet_frame_thickness_mm
            elif material == "cabinet-bridge":
                width, thickness = parameters.cabinet_bridge_height_mm, parameters.cabinet_bridge_thickness_mm
            elif material == "floor-ribs":
                width, thickness = parameters.floor_rib_width_mm, parameters.floor_rib_thickness_mm
            elif material in {"cabinet-hinge-backing", "cabinet-backing-cleats", "cabinet-shelf-ledges"}:
                width, thickness = 18.0, 18.0
            else:
                width, thickness = parameters.slat_width_mm, parameters.slat_thickness_mm
            axes = (2, 1, 0) if material == "floor-ribs" else cutting_axes(part, width, thickness)
            if material == "floor-ribs":
                length = round(size.X, 2)
            else:
                dimensions = list(size)
                for section in (width, thickness):
                    dimensions.pop(min(range(len(dimensions)), key=lambda i: abs(dimensions[i] - section)))
                length = round(dimensions[0], 2)
            if material in {"cabinet-frames", "cabinet-bridge"}:
                profile = {
                    "profile_note": "Shelf cleats have bevelled backing ends; joining rails retain their shared footprint and flush shelf seats; "
                    "match-drill fixings. Door and fixed-panel openings have 10mm-wide front rebates, "
                    "depth equal to panel thickness, with local rear relief for catch keepers. "
                    "Rear upper stile has a scribed top to clear the vehicle beam."
                }
        if (
            material
            in {
                "floor",
                "floor-insulation",
                "cabinet-frames",
                "cabinet-backing-cleats",
                "cabinet-shelf-ledges",
                "floor-ribs",
                "slats",
                "frames",
                "cabinet-partitions",
                "shelves",
                "cabinet-doors",
                "table-plywood",
            }
            or scribed
        ):
            try:
                profile = flat_profile(part, axes)
            except (ValueError, RuntimeError, IndexError) as error:
                logging.getLogger(__name__).warning("Cutting profile for %s: %s", part.label, error)
                profile = {
                    "profile_note": f"Rectangle only: CAD outline extraction failed ({error}). "
                    "Transfer the profile before cutting."
                }
        if material == "cabinet-frames":
            profile["profile_note"] = (
                f"{profile.get('profile_note', '')} Square-ended frame stock; glue and reinforce rail-to-post butt "
                "joints with dowels or screws. Front panel rebates are 10mm wide and one plywood thickness deep; "
                "door hinge edges remain unrebated. Shelf panels fit flush on separate face-mounted ledgers. "
                "Joint drilling and vehicle attachments remain to detail."
            ).strip()
        elif material == "cabinet-backing-cleats":
            profile["profile_note"] = (
                f"{profile.get('profile_note', '')} Backing glue cleats have bevelled ends at horizontal "
                "shelf/rail joints. Stock lengths include the long points; transfer bevels from CAD before assembly."
            ).strip()
        if material in {"floor-ribs", "floor-insulation"}:
            profile["profile_note"] = (
                f"{profile.get('profile_note', '')} Floor assembly follows the existing floor panels on an assumed flat, "
                "horizontal floor; ignore scan-floor noise when preparing these stock cuts."
            ).strip()
        elif material != "unassigned":
            edges, template_fit = fitting.edges(
                part, world, axes, profile.get("outline", []), furniture=path[1] != "Finished floor plywood",
                datum_axes=fitting_datums(part),
            )
            profile.update(fitting_edges=edges, template_fit=template_fit)
        if scribed:
            profile["profile_note"] = (
                f"{profile.get('profile_note', '')} Scan-scribed edge: at least {clearance:g}mm clearance from the "
                "registered photographic scan. Preserve rebates and blind fixing holes."
            ).strip()
        cuts.append(
            CutPart(
                path=" / ".join(path[1:]), material=material, length=length, width=width, thickness=thickness, **profile
            )
        )

    visit(model, (), Location())
    return cuts
