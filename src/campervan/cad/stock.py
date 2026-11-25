"""Stock roles shared by the cutting list and the viewer. Assembly paths identify physical parts."""

HATCH_FOAM = "Lift-out EPS"


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
        if name in {"fixed tabletop leaf", "folding tabletop leaf"}:
            return "table-plywood"
        if name == "bench mounting pad":
            return "frames"
        return "unassigned"
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
    if "slat" in name and ("Fixed slats" in path or "Moving slats" in path):
        return "slats"
    if "Cross bench" in path and "Fixed frame" in path:
        return "frames"
    return "unassigned"
