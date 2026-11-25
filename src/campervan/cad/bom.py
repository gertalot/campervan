"""Cutting envelopes from assembly leaves, independent of placement and display state."""

import logging
from typing import Any

from build123d import Location, Shape

from campervan.cad.cabinet_chains import CHAIN
from campervan.cad.cabinet_stays import PENN
from campervan.cad.scan_scribing import scan_clearance_mm
from campervan.cad.cut_profiles import cutting_axes, fitting_datums, flat_profile
from campervan.cad.fitting import VehicleFitting
from campervan.cad.floor import HATCH_FOAM, ROUTED_BLOCKS
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
        if "Floor insulation" in path or path[-1] == HATCH_FOAM:
            return "floor-insulation"
        return "floor-ribs" if "Pine rib frame" in path else "floor"
    if name.startswith("roller catch keeper"):
        return "cabinet-catches"
    if "Module fasteners" in path:
        return "cabinet-module-fasteners"
    if "Cabinet" in path:
        if "Shelf ledges" in path:
            return "cabinet-shelf-ledges"
        if "Backing glue cleats" in path or "Divider stops" in path:
            return "cabinet-backing-cleats"
        if name in {"pine hinge backing strip", "pine stay door pad"}:
            return "cabinet-hinge-backing"
        if name == "rear top removable infill":
            return "cabinet-doors"
        if "Frames" in path:
            return "cabinet-frames"
        if "Skin" in path:
            return "cabinet-partitions"
        if name in {"plywood door", "cabinet 3 fixed cover", "box 8 fixed front"}:
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
        if part.label == CHAIN or part.label.endswith(f" {CHAIN}"):
            return  # Both runs come from one purchased pack for the five flaps.
        if PENN in path or any(group.endswith(f" {PENN}") for group in path):
            return  # One purchased stay per top-row flap, counted in the materials list.
        if "Hinges" in path or "Keeper fixings" in path or any(name.endswith("fixed hardware") for name in path):
            return  # Purchased hinges/bodies: count the static hinge role and moving catch keeper only.
        if "Roller catch bodies" in path:
            return  # One catch set is counted by its moving keeper.
        if part.children:
            for child in part.children:
                visit(child, path, world)
            return
        if ROUTED_BLOCKS in path and part.parent is not None:
            # Every strip is square-cut to the length of its glue-up before the outside edge is routed.
            blank = Shape.cast(part.parent.wrapped).located(Location()).bounding_box().size
            cuts.append(CutPart(
                path=" / ".join(path[1:]), material="floor-ribs", length=round(blank.X, 2),
                width=parameters.floor_rib_width_mm, thickness=parameters.floor_rib_thickness_mm,
                profile_note=("Square-cut the strips and edge-glue them side by side. Rough-cut the assembled "
                              "block, then flush-trim its outside edge to the fitted floor plywood."
                              if len(part.parent.children) > 1 else
                              "Square-cut one batten. Butt it against the adjoining rails and flush-trim "
                              "the outside edge to the fitted floor plywood."),
            ))
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
        if material in {"slats", "cabinet-frames", "cabinet-hinge-backing",
                        "cabinet-backing-cleats", "cabinet-shelf-ledges", "floor-ribs"}:
            if material == "cabinet-frames":
                width, thickness = parameters.cabinet_frame_width_mm, parameters.cabinet_frame_thickness_mm
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
            if material == "cabinet-frames":
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
        if material == "cabinet-frames" and "Lower module" in path:
            profile["profile_note"] = (
                f"{profile.get('profile_note', '')} Square-ended frame stock; glue and reinforce rail-to-post butt "
                "joints with dowels or screws. Front panel rebates are 10mm wide and one plywood thickness deep; "
                "door hinge edges remain unrebated. Shelf panels fit flush on separate face-mounted ledgers. "
                "Joint drilling and vehicle attachments remain to detail."
            ).strip()
        elif "Upper module" in path and "aisle" in part.label and (
            part.label.endswith(" post") or part.label.endswith("upper shelf aisle rail")
        ):
            edges = "both opening edges" if part.label == "Box 6 middle aisle post" else "the opening edge"
            profile["profile_note"] += f" Rebate {edges} 10mm wide and {parameters.cabinet_door_thickness_mm:g}mm deep."
        elif "Backing glue cleats" in path and "Lower module" in path:
            profile["profile_note"] = (
                f"{profile.get('profile_note', '')} Square-cut backing cleat. Glue to the shallow post "
                "with its glue face flush with the inside face of the wall rail."
            ).strip()
        if material in {"floor-ribs", "floor-insulation"}:
            profile["profile_note"] = (
                f"{profile.get('profile_note', '')} Subfloor follows the plywood perimeter on an assumed flat, "
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
