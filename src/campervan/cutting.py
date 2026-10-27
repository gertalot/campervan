"""PackingSolver adapters for saw blanks and actual flat-profile nesting."""

import hashlib
import io
import json
from collections.abc import Callable
from datetime import UTC, datetime
from math import ceil, cos, floor, radians, sin
from typing import Any

from campervan.cutting_models import CuttingOptions, CuttingSettings, Mode, Stock, StockOptions
from campervan.materials import ROLES, CutPart, Selection, catalogue

PROFILE_ALLOWANCE = 0.2  # Twice the 0.1 mm curve sampling tolerance.
SCALE = 100  # Integer hundredths of a millimetre for the saw solver.


def stock_groups(cuts: list[CutPart], selections: dict[str, Selection]) -> list[dict[str, Any]]:
    products = {product.id: product for product in catalogue()}
    roles = {role.id: role for role in ROLES}
    groups: dict[str, dict[str, Any]] = {}
    for index, cut in enumerate(cuts):
        role = roles.get(cut.material)
        if role is None or role.kind == "hardware":
            continue
        product = products.get(selections.get(role.id, Selection()).product_id)
        key = f"product-{product.id}" if product else f"custom-{role.id}"
        # Measured thicknesses/sections may differ even when the catalogue product is shared.
        key += f"-{cut.thickness:g}" + (f"-{cut.width:g}" if role.kind == "timber" else "")
        if key not in groups:
            dimensions = product.dimensions if product else {}
            groups[key] = {
                "key": key, "name": product.name if product else role.name,
                "kind": role.kind, "thickness": cut.thickness, "parts": [],
                "stock_sourced": product is not None,
                "stock": [Stock(length=dimensions.get("length", 2440 if role.kind == "sheet" else 2400),
                                width=dimensions.get("width", 1220) if role.kind == "sheet" else cut.width,
                                name="Full sheet" if role.kind == "sheet" else "Timber length").model_dump()],
                "price": product.price_nzd if product else None,
            }
        groups[key]["parts"].append(cut.model_dump() | {"id": f"P{index + 1:03d}"})
    return list(groups.values())


def _profile_key(points: list) -> tuple:
    """Ignore wire ordering and redundant points without changing the sampled shape."""
    # CAD profiles are recorded to four decimal places. Integer coordinates make
    # collinearity exact, including extra edge samples produced on another OS.
    ring = []
    for x, y in points:
        point = (round(x * 10000), round(y * 10000))
        if not ring or point != ring[-1]:
            ring.append(point)
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring.pop()
    corners = []
    for i, (x, y) in enumerate(ring):
        ax, ay = ring[i - 1]
        bx, by = ring[(i + 1) % len(ring)]
        collinear = (x - ax) * (by - ay) == (y - ay) * (bx - ax)
        between = (x - ax) * (x - bx) + (y - ay) * (y - by) <= 0
        if not (collinear and between):
            corners.append((x, y))
    if not corners:
        return tuple(ring)
    return min(tuple(order[i:] + order[:i])
               for order in (corners, list(reversed(corners))) for i in range(len(order)))


def _source_hash(group: dict, options: CuttingOptions, version: int) -> str:
    payload = {"version": version, "group": group, "options": options.model_dump()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def source_key(group: dict, options: CuttingOptions) -> str:
    parts = [part | {"outline": _profile_key(part["outline"]),
                     "holes": sorted(_profile_key(hole) for hole in part["holes"])} for part in group["parts"]]
    return _source_hash(group | {"parts": parts}, options, 4)


def refresh_layout_source(result: dict, group: dict, options: CuttingOptions) -> dict:
    """Migrate a saved fingerprint only when all original inputs still match."""
    source = source_key(group, options)
    if result.get("source") == source or "parts" not in result:
        return result
    saved_group = group | {"parts": result["parts"]}
    if (result.get("source") == _source_hash(saved_group, options, 3)
            and source_key(saved_group, options) == source):
        return result | {"source": source}
    return result


def effective_options(group: dict, settings: CuttingSettings, stock: StockOptions | None) -> CuttingOptions:
    selected = stock or StockOptions(stock=group["stock"])
    return CuttingOptions(**selected.model_dump(), **settings.model_dump(exclude={"algorithm"}))


def layout_score(result: dict) -> tuple:
    """Rank candidates by stock use, offcut area/perimeter, then saw-cut count."""
    offcut = result.get("best_offcut")
    return (len(result["unplaced"]), result["full_stock_count"], result["offcut_count"], result["stock_area"],
            offcut["perimeter_area_ratio"] if offcut else float("inf"),
            sum(len(sheet["cuts"]) for sheet in result["sheets"]))


def rectangle(length: float, width: float) -> list[list[float]]:
    return [[0, 0], [length, 0], [length, width], [0, width]]


def polygon_area(points: list) -> float:
    return abs(sum(x * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * y
                   for i, (x, y) in enumerate(points))) / 2


def transform(points: list, angle: float, x: float, y: float) -> list[list[float]]:
    c, s = cos(radians(angle)), sin(radians(angle))
    return [[round(px * c - py * s + x, 4), round(px * s + py * c + y, 4)] for px, py in points]


def layout(group: dict, options: CuttingOptions, mode: Mode, on_update: Callable[[dict], None] | None = None) -> dict:
    """Solve a snapshot; no CAD work or project mutation occurs in this worker thread."""
    from packingsolver import irregular, rectangleguillotine

    if not options.stock:
        raise ValueError("Add a stock sheet or timber length.")
    timber = group["kind"] == "timber"
    nesting = mode == "nesting" and not timber
    trim_y = 0 if timber else options.trim
    stocks = [stock.model_dump() for stock in options.stock]
    for stock in stocks:
        if stock["length"] <= 2 * options.trim or stock["width"] <= 2 * trim_y:
            raise ValueError("Edge trim leaves no usable stock.")
        if stock["offcut"] and stock["copies"] == 0:
            raise ValueError("Enter the quantity available for each offcut.")
        if timber and abs(stock["width"] - group["parts"][0]["width"]) > 0.01:
            raise ValueError("Timber stock must have the same width as the modelled section.")
    parts = group["parts"]
    grains = ["length" if timber else options.orientations.get(p["path"], options.grain) for p in parts]
    instance_data: dict = {
        "objective": ("variable-sized-bin-packing" if len(stocks) > 1 else
                      "bin-packing-with-leftovers" if not nesting and not timber else "bin-packing"),
        "bin_types": [], "item_types": [],
    }
    if nesting:
        instance_data["parameters"] = {"item_item_minimum_spacing": options.kerf + PROFILE_ALLOWANCE}
    else:
        instance_data.update(number_of_stages=3, cut_type="non-exact", first_stage_orientation="any",
                             cut_thickness=ceil(options.kerf * SCALE))
    for stock in stocks:
        length = floor((stock["length"] - 2 * options.trim) * SCALE) / SCALE
        width = floor((stock["width"] - 2 * trim_y) * SCALE) / SCALE
        bin_data = {"width": length if nesting else round(length * SCALE),
                    "height": round(width * SCALE), "copies": stock["copies"] or len(parts),
                    "cost": 0.000001 if stock["offcut"] else 1}
        if nesting:
            bin_data.update(type="rectangle", height=width)
        instance_data["bin_types"].append(bin_data)
    for part, grain in zip(parts, grains):
        if nesting:
            def polygon(points):
                return {"type": "polygon", "vertices": [{"x": x, "y": y} for x, y in points]}
            item = polygon(part["outline"] or rectangle(part["length"], part["width"]))
            item["holes"] = [polygon(hole) for hole in part["holes"]]
            angles = [0, 90, 180, 270] if grain == "free" else [90, 270] if grain == "width" else [0, 180]
            item["allowed_rotations"] = [{"start": angle, "end": angle} for angle in angles]
        else:
            length, width = part["length"], part["width"]
            if grain == "width":
                length, width = width, length
            item = {"width": ceil(length * SCALE), "height": ceil(width * SCALE), "oriented": grain != "free"}
        item["copies"] = 1
        instance_data["item_types"].append(item)
    solver = irregular if nesting else rectangleguillotine
    builder = solver.InstanceBuilder()
    builder.read(io.StringIO(json.dumps(instance_data)))
    instance = builder.build()
    parameters = solver.OptimizeParameters()
    parameters.verbosity_level = 0
    if on_update is not None:
        def publish(progress):
            if progress.solution.number_of_items():
                on_update(_read_layout(progress, group, options, mode, stocks, grains, nesting, trim_y))
        parameters.new_solution_callback = publish
    output = solver.optimize(instance, parameters)
    return _read_layout(output, group, options, mode, stocks, grains, nesting, trim_y)


def _read_layout(output, group, options, mode, stocks, grains, nesting, trim_y) -> dict:
    parts = group["parts"]
    solution = output.solution
    sheets = []
    placed = set()
    if nesting:
        certificate = io.StringIO()
        solution.write(certificate)
        bins = (json.loads(certificate.getvalue()) or {}).get("bins") or []
        for bin in bins:
            stock = stocks[bin["id"]]
            placements = []
            for item in bin.get("items", []):
                part = parts[item["id"]]
                shape = item["item_shapes"][0]
                def points(elements):
                    return [[e["xs"] + options.trim, e["ys"] + trim_y] for e in elements]
                placements.append({"id": part["id"], "path": part["path"],
                                   "outline": points(shape["shape"]),
                                   "holes": [points(h) for h in shape.get("holes", [])],
                                   "angle": item["angle"]})
                placed.add(part["id"])
            for _ in range(bin["copies"]):
                sheets.append({"stock": stock, "parts": placements, "cuts": [], "remnants": []})
    else:
        for bin_index in range(solution.number_of_different_bins()):
            bin = solution.bin(bin_index)
            stock = stocks[bin.bin_type_id]
            placements, cut_lines, remnants = [], [], []
            nodes = bin.nodes
            for node in nodes:
                x, y = node.l / SCALE + options.trim, node.b / SCALE + trim_y
                width, height = (node.r - node.l) / SCALE, (node.t - node.b) / SCALE
                if node.f >= 0 and node.item_type_id >= 0:
                    part = parts[node.item_type_id]
                    grain = grains[node.item_type_id]
                    rotated = grain == "width" or (grain == "free" and abs(width - part["length"]) > 0.02)
                    angle = 90 if rotated else 0
                    # A 90 degree rotation extends into negative X; translate it back into its blank.
                    dx = x + (part["width"] if rotated else 0)
                    outline = part["outline"] or rectangle(part["length"], part["width"])
                    placements.append({"id": part["id"], "path": part["path"],
                                       "outline": transform(outline, angle, dx, y),
                                       "holes": [transform(h, angle, dx, y) for h in part["holes"]],
                                       "blank": [x, y, width, height], "angle": angle})
                    placed.add(part["id"])
                elif not node.children and node.f >= 0 and node.item_type_id in (-1, -3):
                    remnants.append([x, y, width, height])

            def cuts_in_order(index):
                parent = nodes[index]
                children = [nodes[i] for i in parent.children]
                for child in children:
                    # Children partition the parent along one axis. Cut on the far
                    # side of the child; any kerf lies outside the finished child.
                    if child.r < parent.r and child.b == parent.b and child.t == parent.t:
                        cut_lines.append([child.r / SCALE + options.trim, parent.b / SCALE + trim_y,
                                          child.r / SCALE + options.trim, parent.t / SCALE + trim_y])
                    elif child.t < parent.t and child.l == parent.l and child.r == parent.r:
                        cut_lines.append([parent.l / SCALE + options.trim, child.t / SCALE + trim_y,
                                          parent.r / SCALE + options.trim, child.t / SCALE + trim_y])
                for child_index in parent.children:
                    cuts_in_order(child_index)

            if nodes:
                cuts_in_order(0)
            for _ in range(bin.copies):
                sheets.append({"stock": stock, "parts": placements, "cuts": cut_lines, "remnants": remnants})
    stock_area = sum(s["stock"]["length"] * s["stock"]["width"] for s in sheets)
    used_parts = [p for p in parts if p["id"] in placed]
    blank_area = sum(p["length"] * p["width"] for p in used_parts)
    profile_area = sum(polygon_area(p["outline"] or rectangle(p["length"], p["width"]))
                       - sum(polygon_area(h) for h in p["holes"]) for p in used_parts)
    unplaced = [p["id"] for p in parts if p["id"] not in placed]
    offcuts = [
        {"sheet": index, "x": x, "y": y, "length": length, "width": width,
         "area": length * width, "perimeter_area_ratio": 2 * (length + width) / (length * width)}
        for index, sheet in enumerate(sheets) for x, y, length, width in sheet["remnants"]
        if length > 0 and width > 0
    ]
    best_offcut = min(offcuts, key=lambda offcut: (offcut["perimeter_area_ratio"], -offcut["area"]), default=None)
    optimise_offcuts = not nesting and group["kind"] != "timber" and len(stocks) == 1
    stock_count_optimal = output.is_proven_optimal()
    if optimise_offcuts and not unplaced and sheets:
        usable_area = (stocks[0]["length"] - 2 * options.trim) * (stocks[0]["width"] - 2 * trim_y)
        lower_bound = max(ceil(blank_area / usable_area), output.bin_packing_bound)
        stock_count_optimal = len(sheets) == lower_bound
    return {
        "mode": mode, "source": source_key(group, options), "created": datetime.now(UTC).isoformat(),
        "options": options.model_dump(), "name": group["name"], "parts": parts, "sheets": sheets,
        "unplaced": unplaced,
        "stock_area": stock_area, "blank_area": blank_area, "profile_area": profile_area,
        "full_stock_count": sum(not s["stock"]["offcut"] for s in sheets),
        "offcut_count": sum(s["stock"]["offcut"] for s in sheets),
        "estimated_cost": (sum(not s["stock"]["offcut"] for s in sheets) * group["price"]
                           if group["price"] is not None else None),
        "algorithm": output.solution_label, "profile_allowance": PROFILE_ALLOWANCE if nesting else 0,
        "optimal": output.is_proven_optimal(),
        "stock_count_optimal": stock_count_optimal, "optimises_offcuts": optimise_offcuts,
        "best_offcut": best_offcut,
        "objective": ("Fewest full stock pieces" if len(stocks) > 1 else
                      "Fewest sheets, then useful rectangular offcuts" if optimise_offcuts else "Fewest stock pieces"),
    }
