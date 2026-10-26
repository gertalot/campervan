"""Local planner editing and portable backups. All writes use the same revision guard."""

import csv
import io
import json
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import Field, field_validator

from campervan.coordinator import Coordinator
from campervan.materials import ROLES, Product, Project, catalogue, resolve, save_project
from campervan.parameter_fit import fit_parameters
from campervan.planning import (
    ContentUpdate, Mutation, PlanningConflict, PlanningDocument, PlanningStore,
    PurchaseFilter, PurchaseRecord, Record, outline_markdown, parse_document,
)
from campervan.purchases import matches, purchase_totals, purchase_view


class Backup(Record):
    version: Literal[1] = 1
    planning: PlanningDocument
    project: Project
    products: list[Product] = Field(default_factory=list)

    @field_validator("planning", mode="before")
    @classmethod
    def read_legacy_plan(cls, value: Any) -> PlanningDocument:
        return value if isinstance(value, PlanningDocument) else parse_document(value)


class Restore(Record):
    revision: int
    backup: Backup


def register_planning(app: FastAPI, project_path: Path) -> None:
    router = APIRouter(prefix="/api/v1")
    store = PlanningStore(project_path.with_name("planning.json"))

    def coordinator(request: Request) -> Coordinator:
        return request.app.state.coordinator  # type: ignore[no-any-return]

    def read() -> PlanningDocument:
        try:
            return store.read()
        except (ValueError, OSError) as error:
            raise HTTPException(422, f"Cannot read planning file: {error}. Restore a backup to recover.") from error

    def backup(request: Request) -> Backup:
        current = coordinator(request)
        return Backup(
            planning=read(), project=Project(parameters=current.parameters, materials=current.materials, cutting=current.cutting),
            products=catalogue(),
        )

    def validate_purchase(record: PurchaseRecord) -> None:
        if record.product_id and record.product_id not in {product.id for product in catalogue()}:
            raise HTTPException(422, "Unknown purchase product")
        if record.role_id and record.role_id not in {role.id for role in ROLES}:
            raise HTTPException(422, "Unknown custom stock role")

    @router.get("/planning")
    async def get_planning() -> PlanningDocument:
        return read()

    @router.post("/planning/operations")
    async def mutate(mutation: Mutation, request: Request) -> PlanningDocument:
        op = mutation.operation
        if op.kind == "delete_purchase":
            row = next((row for row in purchase_view(read(), coordinator(request))["rows"] if row["record"]["id"] == op.id), None)
            if row and row["generated"]:
                raise HTTPException(422, "CAD stock cannot be deleted here. Change its CAD selection or quantities instead.")
        if op.kind == "purchase":
            record = PurchaseRecord.model_validate(op.values | {"id": op.id})
            validate_purchase(record)
        try:
            return store.apply(mutation.revision, op)
        except PlanningConflict as error:
            raise HTTPException(409, str(error)) from error
        except OSError as error:
            raise HTTPException(500, f"Plan was not saved: {error}") from error

    @router.put("/planning/content")
    async def replace_content(update: ContentUpdate) -> PlanningDocument:
        try:
            return store.replace_content(update.revision, update.content)
        except PlanningConflict as error:
            raise HTTPException(409, str(error)) from error
        except OSError as error:
            raise HTTPException(500, f"Plan was not saved: {error}") from error

    @router.get("/purchases")
    async def get_purchases(
        request: Request, category: str = "", tag: str = "", supplier: str = "", status: str = "", search: str = "",
    ) -> dict[str, Any]:
        view = purchase_view(read(), coordinator(request))
        filters = PurchaseFilter(category=category, tag=tag, supplier=supplier, status=status, search=search)
        rows = [row for row in view["rows"] if matches(row, filters)]
        return view | {"rows": rows, "filtered_totals": purchase_totals(rows)}

    @router.get("/planning/export")
    async def export(request: Request, format: Literal["json", "markdown", "csv"] = "json") -> Response:
        bundle = backup(request)
        if format == "json":
            body, media, extension = bundle.model_dump_json(indent=2), "application/json", "json"
        elif format == "markdown":
            body, media, extension = outline_markdown(bundle.planning), "text/markdown", "md"
        else:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["Item", "Category", "Tags", "Supplier", "URL", "Unit", "Required", "Owned", "Bought", "Estimated unit NZD", "Spent NZD", "Remaining NZD", "Status", "Notes"])
            for row in purchase_view(bundle.planning, coordinator(request))["rows"]:
                r = row["record"]
                values = [r["name"], r["category"], ", ".join(r["tags"]), r["supplier"], r["url"], r["unit"], row["required"], r["owned"], r["bought"], r["unit_price"], r["spent"], row["remaining_cost"], row["status"], r["notes"]]
                writer.writerow(["'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value for value in values])
            body, media, extension = buffer.getvalue(), "text/csv", "csv"
        return Response(body, media_type=media, headers={"Content-Disposition": f'attachment; filename="conversion-plan.{extension}"'})

    @router.get("/planning/previous")
    async def previous(request: Request) -> Backup:
        if not store.previous.exists():
            raise HTTPException(404, "No previous save exists yet")
        current = coordinator(request)
        return Backup(
            planning=parse_document(json.loads(store.previous.read_text())),
            project=Project(parameters=current.parameters, materials=current.materials, cutting=current.cutting), products=catalogue(),
        )

    @router.post("/planning/restore")
    async def restore(payload: Restore, request: Request) -> PlanningDocument:
        valid_current = True
        try:
            current_document = store.read()
            revision = current_document.revision
        except ValueError:
            # An explicit restore can recover a corrupt planning file; it never happens on ordinary reads.
            revision = 0
            valid_current = False
        if revision != payload.revision:
            raise HTTPException(409, "Plan changed since the backup was selected. Reload before restoring.")
        current = coordinator(request)
        saved = payload.backup
        for purchase in saved.planning.purchases.values():
            validate_purchase(purchase)
        products = {product.id: product for product in catalogue()}
        snapshots = {product.id: product for product in saved.products}
        referenced = {s.product_id for s in saved.project.materials.values() if s.product_id}
        referenced |= {p.product_id for p in saved.planning.purchases.values() if p.product_id}
        for key in referenced:
            if (key not in products or key not in snapshots
                    or products[key].dimensions != snapshots[key].dimensions
                    or products[key].kind != snapshots[key].kind
                    or products[key].pack_quantity != snapshots[key].pack_quantity
                    or products[key].sale_unit != snapshots[key].sale_unit):
                raise HTTPException(422, f"Product {key} is missing or has changed dimensions; reconcile it before restoring.")
        parameters, _ = fit_parameters(resolve(saved.project.parameters, saved.project.materials))
        project = Project(parameters=parameters, materials=saved.project.materials, cutting=saved.project.cutting)
        restored = saved.planning.model_copy(deep=True)
        restored.revision = max(revision, restored.revision) + 1
        old_plan = store.path.read_bytes() if store.path.exists() else None
        old_project = project_path.read_bytes() if project_path.exists() else None
        changed = project.parameters != current.parameters or project.materials != current.materials
        old_cutting = current.cutting
        await current.stop_cutting()
        try:
            store.write(restored, backup=valid_current)
            current.cutting = project.cutting
            if changed:
                # accept saves before changing live state; it schedules regeneration without yielding.
                await current.accept(project.parameters, project.materials)
            else:
                save_project(project, project_path)
        except OSError:
            current.cutting = old_cutting
            for path, content in ((project_path, old_project), (store.path, old_plan)):
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    temp = path.with_suffix(".tmp")
                    temp.write_bytes(content)
                    temp.replace(path)
            raise
        return restored

    app.include_router(router)
