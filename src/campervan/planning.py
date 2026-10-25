"""A rich conversion document and purchase records, independent of CAD regeneration."""

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal, Self
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanningConflict(ValueError):
    pass


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PurchaseFilter(Record):
    category: str = ""
    tag: str = ""
    supplier: str = ""
    status: str = ""
    search: str = ""


def validate_document(document: dict[str, Any], *, legacy: bool = False) -> None:
    """Validate the bounded editor schema before saving or hydrating content."""
    inline = {"text", "hardBreak"}
    blocks = {"paragraph", "heading", "bulletList", "orderedList", "blockquote", "codeBlock",
              "horizontalRule", "table", "taskList", "purchaseView"}
    allowed = blocks | inline | {"doc", "listItem", "taskItem", "tableRow", "tableCell", "tableHeader"}
    identities: set[str] = set()

    def visit(node: Any, depth: int = 0) -> None:
        if (not isinstance(node, dict) or depth > 100 or not isinstance(node.get("type"), str)
                or node.get("type") not in allowed):
            raise ValueError("Unsupported or excessively nested document content")
        kind = node["type"]
        if set(node) - {"type", "attrs", "content", "marks", "text"}:
            raise ValueError("Unsupported document element fields")
        attrs, children, marks = node.get("attrs", {}), node.get("content", []), node.get("marks", [])
        if not isinstance(attrs, dict) or not isinstance(children, list) or not isinstance(marks, list):
            raise ValueError("Invalid document attributes, content or formatting")
        permitted = {"id"} if legacy else set()
        permitted |= {
            "heading": {"level"}, "orderedList": {"start", "type"}, "codeBlock": {"language"},
            "table": {"style"}, "tableCell": {"colspan", "rowspan", "colwidth", "align"},
            "tableHeader": {"colspan", "rowspan", "colwidth", "align"},
            "taskItem": {"id", "checked", "collapsed", "needs_review"}, "purchaseView": {"id", "filter"},
        }.get(kind, set())
        if set(attrs) - permitted:
            raise ValueError(f"Unsupported attributes for {kind}")
        if legacy and kind in {"taskList", "taskItem", "purchaseView"}:
            raise ValueError("Unsupported legacy note content")
        if kind in {"taskItem", "purchaseView"}:
            key = attrs.get("id")
            if not isinstance(key, str) or not key or key in identities:
                raise ValueError("Missing or duplicate task/purchase-view ID")
            identities.add(key)
        if kind == "taskItem" and any(not isinstance(attrs.get(key, False), bool)
                                       for key in ("checked", "collapsed", "needs_review")):
            raise ValueError("Invalid task status")
        if kind == "purchaseView":
            PurchaseFilter.model_validate(attrs.get("filter", {}))
        if kind == "text" and (not isinstance(node.get("text"), str) or not node["text"]):
            raise ValueError("Text must be a nonempty string")
        child_types = [child.get("type") if isinstance(child, dict) else None for child in children]
        if any(not isinstance(kind, str) for kind in child_types):
            raise ValueError("Invalid document element type")
        expected = inline if kind in {"paragraph", "heading"} else {"text"} if kind == "codeBlock" else blocks
        if kind in inline | {"horizontalRule", "purchaseView"}:
            if children:
                raise ValueError(f"{kind} cannot contain other elements")
        elif kind in {"bulletList", "orderedList", "taskList", "table", "tableRow"}:
            expected = {"listItem"} if kind in {"bulletList", "orderedList"} else {
                "taskList": {"taskItem"}, "table": {"tableRow"}, "tableRow": {"tableCell", "tableHeader"},
            }[kind]
            if not children or not set(child_types) <= expected:
                raise ValueError(f"Invalid contents in {kind}")
        elif not set(child_types) <= expected:
            raise ValueError(f"Invalid contents in {kind}")
        if kind in {"taskItem", "listItem"} and (not child_types or child_types[0] != "paragraph"):
            raise ValueError("List items must start with a paragraph")
        if not legacy and kind in {"doc", "blockquote", "tableCell", "tableHeader"} and not children:
            raise ValueError(f"{kind} must contain editable content")
        if kind == "heading":
            level = attrs.get("level", 1)
            if not isinstance(level, int) or isinstance(level, bool) or level not in range(1, 7):
                raise ValueError("Invalid heading level")
        if kind == "orderedList":
            start = attrs.get("start", 1)
            if not isinstance(start, int) or isinstance(start, bool):
                raise ValueError("Invalid numbered-list start")
        if kind == "codeBlock" and attrs.get("language") is not None and not isinstance(attrs["language"], str):
            raise ValueError("Invalid code language")
        if kind in {"tableCell", "tableHeader"}:
            for key in ("colspan", "rowspan"):
                value = attrs.get(key, 1)
                if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                    raise ValueError("Invalid table cell span")
            widths = attrs.get("colwidth")
            if widths is not None and (not isinstance(widths, list) or any(
                    not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 for value in widths)):
                raise ValueError("Invalid table column widths")
            if attrs.get("align") not in {None, "left", "center", "right", "justify"}:
                raise ValueError("Invalid table alignment")
        for mark in marks:
            if not isinstance(mark, dict) or mark.get("type") not in {"bold", "italic", "strike", "code", "underline", "link"}:
                raise ValueError("Unsupported text formatting")
            if mark["type"] == "link":
                attributes = mark.get("attrs", {})
                href = attributes.get("href", "") if isinstance(attributes, dict) else None
                if not isinstance(href, str) or not href.lower().startswith(("https://", "http://", "mailto:", "tel:", "#", "/")):
                    raise ValueError("Links must use http, https, mailto or tel")
        for child in children:
            visit(child, depth + 1)

    if document.get("type") != "doc":
        raise ValueError("Expected an editor document")
    visit(document)


class PurchaseRecord(Record):
    id: str
    name: str
    product_id: str | None = None
    role_id: str | None = None
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    supplier: str = ""
    url: str = ""
    notes: str = ""
    unit: str = "each"
    required: float | None = Field(default=None, ge=0)
    owned: float = Field(default=0, ge=0)
    bought: float = Field(default=0, ge=0)
    unit_price: float | None = Field(default=None, ge=0, multiple_of=0.01)
    spent: float | None = Field(default=None, ge=0, multiple_of=0.01)

    @model_validator(mode="after")
    def valid_identity(self) -> Self:
        if self.product_id and self.role_id:
            raise ValueError("Stock must refer to a product or a custom role, not both")
        expected = (f"product-{self.product_id}" if self.product_id else
                    f"custom-{self.role_id}" if self.role_id else None)
        if (expected and self.id != expected) or (not expected and not self.id.startswith("manual-")):
            raise ValueError("Purchase identity must match its product, role or manual item")
        return self


def numbered_content(content: dict[str, Any]) -> dict[str, Any]:
    """Convert former bullet/numbered lists to the one numbered checkbox hierarchy."""
    result = deepcopy(content)
    used: set[str] = set()

    def collect(node: Any) -> None:
        if not isinstance(node, dict):
            return
        identity = node.get("attrs", {}).get("id") if isinstance(node.get("attrs", {}), dict) else None
        if isinstance(identity, str):
            used.add(identity)
        for child in node.get("content", []) if isinstance(node.get("content", []), list) else []:
            collect(child)

    collect(result)

    def convert(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") in {"bulletList", "orderedList"}:
            node["type"] = "taskList"
            node.pop("attrs", None)
        if node.get("type") == "listItem":
            identity = str(uuid5(NAMESPACE_URL, "campervan-checkbox:" + path))
            while identity in used:
                identity = str(uuid5(NAMESPACE_URL, identity))
            used.add(identity)
            node["type"] = "taskItem"
            node["attrs"] = {"id": identity, "checked": False, "collapsed": False, "needs_review": False}
        for index, child in enumerate(node.get("content", []) if isinstance(node.get("content", []), list) else []):
            convert(child, path + "/" + str(index))

    convert(result, "doc")
    return result


class PlanningDocument(Record):
    version: Literal[2] = 2
    revision: int = Field(default=0, ge=0)
    content: dict[str, Any] = Field(default_factory=lambda: {"type": "doc", "content": [{"type": "paragraph"}]})
    purchases: dict[str, PurchaseRecord] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def one_list_type(cls, value: Any) -> Any:
        if isinstance(value, dict) and isinstance(value.get("content"), dict):
            return value | {"content": numbered_content(value["content"])}
        return value

    @model_validator(mode="after")
    def valid_document(self) -> Self:
        validate_document(self.content)
        if any(key != value.id for key, value in self.purchases.items()):
            raise ValueError("Purchase ID does not match its key")
        return self


def parse_document(raw: dict[str, Any]) -> PlanningDocument:
    if not isinstance(raw, dict):
        raise ValueError("Expected a planning document object")
    if raw.get("version") == 1:
        from campervan.planning_migration import convert_v1
        raw = convert_v1(raw)
    return PlanningDocument.model_validate(raw)


class PlanningOperation(Record):
    kind: str
    id: str
    values: dict[str, Any] = Field(default_factory=dict)
    # Accept former shape to return a useful error to a tab opened before the update.
    parent: str | None = None
    index: int | None = None


class Mutation(Record):
    revision: int = Field(ge=0)
    operation: PlanningOperation


class ContentUpdate(Record):
    revision: int = Field(ge=0)
    content: dict[str, Any]


class PlanningStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous = path.with_suffix(".previous.json")

    def read(self) -> PlanningDocument:
        if not self.path.exists():
            from campervan.planning_migration import seed_v1
            self.write(parse_document(seed_v1().model_dump()), backup=False)
        original = self.path.read_bytes()
        raw = json.loads(original)
        document = parse_document(raw)
        if raw.get("version") == 1:
            backup_path = self.path.with_name(self.path.stem + ".v1-backup.json")
            if not backup_path.exists():
                with backup_path.open("xb") as backup:
                    backup.write(original)
            document.revision += 1
            self.write(document)
        elif raw.get("content") != document.content:
            document.revision += 1
            self.write(document)
        return document

    def write(self, document: PlanningDocument, *, backup: bool = True) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if backup and self.path.exists():
            temporary_backup = self.previous.with_suffix(".tmp")
            temporary_backup.write_bytes(self.path.read_bytes())
            temporary_backup.replace(self.previous)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(document.model_dump_json(indent=2) + "\n")
        temporary.replace(self.path)

    def current(self, revision: int) -> PlanningDocument:
        document = self.read()
        if document.revision != revision:
            raise PlanningConflict("The plan changed elsewhere. Download your unsaved edits, then reload before editing again.")
        return document

    def replace_content(self, revision: int, content: dict[str, Any]) -> PlanningDocument:
        document = self.current(revision)
        updated = PlanningDocument.model_validate(document.model_dump() | {"content": content, "revision": revision + 1})
        self.write(updated)
        return updated

    def apply(self, expected_revision: int, operation: PlanningOperation) -> PlanningDocument:
        document = self.current(expected_revision)
        op = operation
        if op.kind == "purchase":
            document.purchases[op.id] = PurchaseRecord.model_validate(op.values | {"id": op.id})
        elif op.kind in {"delete_purchase", "reset_purchase"}:
            if op.id not in document.purchases:
                raise ValueError("Purchase no longer exists")
            del document.purchases[op.id]
        else:
            raise ValueError("The editor format changed. Reload this tab; use the content API to edit tasks and text.")
        document.revision += 1
        self.write(document)
        return document


def outline_markdown(document: PlanningDocument) -> str:
    numbers: dict[str, str] = {}
    counts: dict[str, int] = {}

    def number_items(node: dict[str, Any], parent: str = "") -> None:
        if node["type"] == "taskItem":
            counts[parent] = counts.get(parent, 0) + 1
            parent = f"{parent}.{counts[parent]}" if parent else str(counts[parent])
            numbers[node["attrs"]["id"]] = parent
        for child in node.get("content", []):
            number_items(child, parent)

    number_items(document.content)

    def emit(node: dict[str, Any], depth: int = 0) -> str:
        kind, attrs = node["type"], node.get("attrs", {})
        if kind == "text":
            text = node["text"]
            for mark in node.get("marks", []):
                if mark["type"] == "link":
                    text = f"[{text}]({mark.get('attrs', {}).get('href', '')})"
                elif mark["type"] in {"bold", "italic", "strike", "code"}:
                    wrapper = {"bold": "**", "italic": "*", "strike": "~~", "code": "`"}[mark["type"]]
                    text = wrapper + text + wrapper
            return text
        if kind == "hardBreak":
            return "  \n"
        if kind == "purchaseView":
            return "Purchases: " + json.dumps(attrs.get("filter", {})) + "\n\n"
        children = node.get("content", [])
        if kind in {"taskItem", "listItem"}:
            prefix = f"- [{'x' if attrs.get('checked') else ' '}] **{numbers[attrs['id']]}** " if kind == "taskItem" else "- "
            first = emit(children[0], depth).rstrip()
            result = "  " * depth + prefix + first.replace("\n", "\n" + "  " * (depth + 1)) + "\n"
            if attrs.get("needs_review"):
                result += "  " * (depth + 1) + "Needs review\n"
            for child in children[1:]:
                rendered = emit(child, depth + 1)
                if child["type"] not in {"taskList", "bulletList", "orderedList"}:
                    rendered = "\n".join("  " * (depth + 1) + line if line else "" for line in rendered.split("\n"))
                result += rendered
            return result
        if kind == "orderedList":
            start = attrs.get("start", 1)
            return "".join(emit(child, depth).replace("- ", f"{start + index}. ", 1)
                           for index, child in enumerate(children))
        if kind == "tableRow":
            return "| " + " | ".join(emit(child, depth).strip().replace("\n", "<br>").replace("|", "\\|") for child in children) + " |\n"
        result = "".join(emit(child, depth) for child in children)
        if kind == "table":
            rows = [emit(child, depth) for child in children]
            if rows:
                rows.insert(1, "| " + " | ".join("---" for _ in children[0].get("content", [])) + " |\n")
            return "".join(rows) + "\n"
        if kind == "heading":
            return "#" * attrs.get("level", 2) + " " + result + "\n\n"
        if kind == "paragraph":
            return result + "\n\n"
        if kind == "codeBlock":
            return "```" + (attrs.get("language") or "") + "\n" + result + "\n```\n\n"
        if kind == "horizontalRule":
            return "---\n\n"
        if kind == "blockquote":
            return "\n".join("> " + line for line in result.rstrip().split("\n")) + "\n\n"
        return result

    return "# Conversion plan\n\n" + emit(document.content)
