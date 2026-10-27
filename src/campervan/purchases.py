"""One purchasing row per stock product, shared across outline views and the BOM."""

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Any

from campervan.materials import ROLES, CutPart, Selection, catalogue
from campervan.planning import PlanningDocument, PurchaseFilter, PurchaseRecord


def money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def purchase_view(
    document: PlanningDocument, materials: dict[str, Selection], cuts: list[CutPart], current: bool = True,
) -> dict[str, Any]:
    products = {product.id: product for product in catalogue()}
    groups: dict[str, dict[str, Any]] = {}
    for role in ROLES:
        selection = materials.get(role.id)
        product = products.get(selection.product_id) if selection and selection.product_id else None
        key = f"product-{product.id}" if product else f"custom-{role.id}"
        group = groups.setdefault(key, {"product": product, "uses": [], "counts": [], "owned": [], "quantities": []})
        group["uses"].append(role.name)
        group["owned"].append(bool(selection and selection.owned))
        if not product:
            group["role"] = role.id
        if selection and selection.owned:
            continue
        if selection and selection.purchase_quantity is not None:
            group["quantities"].append(selection.purchase_quantity)
        count = role.quantity
        if count is None and current:
            count = sum(cut.material == role.id for cut in cuts) or None
        group["counts"].append(count if role.kind == "hardware" else None)
    rows = []
    for key in dict.fromkeys([*groups, *document.purchases]):
        group = groups.get(key)
        stored = document.purchases.get(key)
        product = group["product"] if group else None
        if stored is None:
            stored = PurchaseRecord(
                id=key, name=product.name if product else group["uses"][0],
                product_id=product.id if product else None,
                role_id=group.get("role") if group else None,
                category="Furniture", supplier=product.supplier if product else "",
                url=product.url if product else "", unit=product.sale_unit if product else "each",
                unit_price=product.price_nzd if product else None,
            )
        required = stored.required
        legacy = bool(group and any(group["owned"]))
        if required is None and group:
            counts = group["counts"]
            if group["quantities"]:
                # Existing selections describe purchase units per use; explicit planner quantity overrides this.
                required = sum(group["quantities"]) if len(group["quantities"]) == len(counts) else None
            elif not counts:
                required = 0
            elif all(count is not None for count in counts):
                required = ceil(sum(counts) / (product.pack_quantity if product else 1))
        unused = group is None and bool(stored.product_id or stored.role_id)
        if unused:
            required = 0
        remaining = max(required - stored.owned - stored.bought, 0) if required is not None else None
        cost = (
            money(Decimal(str(remaining)) * Decimal(str(stored.unit_price)))
            if remaining is not None and stored.unit_price is not None else (0.0 if remaining == 0 else None)
        )
        if unused:
            status = "Unused stock"
        elif remaining == 0:
            status = "Bought" if stored.bought else "Already owned" if stored.owned or legacy else "Not needed"
        else:
            status = "Partly bought" if stored.bought else "Not bought"
        rows.append({
            "record": stored.model_dump(), "required": required, "remaining": remaining,
            "remaining_cost": cost, "status": status,
            "uses": group["uses"] if group else [], "shared": bool(group and len(group["uses"]) > 1),
            "legacy_owned": legacy, "generated": group is not None or unused,
        })
    return {"rows": rows, "totals": purchase_totals(rows), "revision": document.revision}


def purchase_totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = list({row["record"]["id"]: row for row in rows}.values())
    spent = sum((Decimal(str(row["record"]["spent"])) for row in rows if row["record"]["spent"] is not None), Decimal(0))
    remaining = sum((Decimal(str(row["remaining_cost"])) for row in rows if row["remaining_cost"] is not None), Decimal(0))
    return {
        "spent": money(spent), "remaining": money(remaining), "forecast": money(spent + remaining),
        "unknown_remaining": sum(row["remaining_cost"] is None for row in rows),
        "unknown_spent": sum(row["record"]["bought"] > 0 and row["record"]["spent"] is None for row in rows),
    }


def matches(row: dict[str, Any], filters: PurchaseFilter) -> bool:
    record = row["record"]
    return (
        (not filters.category or record["category"] == filters.category)
        and (not filters.tag or filters.tag in record["tags"])
        and (not filters.supplier or record["supplier"] == filters.supplier)
        and (not filters.status or row["status"] == filters.status)
        and (not filters.search or filters.search.casefold() in " ".join([
            record["name"], record["notes"], record["supplier"], *record["tags"], *row["uses"],
        ]).casefold())
    )
