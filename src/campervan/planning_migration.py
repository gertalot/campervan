"""Read the former task tree without maintaining a second editable representation."""

import re
from pathlib import Path
from typing import Any, Literal, Self
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import Field, model_validator

from campervan.planning import PurchaseFilter, PurchaseRecord, Record, validate_document


def validate_rich(content: dict[str, Any]) -> None:
    validate_document(content, legacy=True)


class ContentBlock(Record):
    id: str
    kind: Literal["text", "bom"] = "text"
    content: dict[str, Any] = Field(default_factory=lambda: {"type": "doc", "content": [{"type": "paragraph"}]})
    filter: PurchaseFilter = Field(default_factory=PurchaseFilter)

    @model_validator(mode="after")
    def valid_content(self) -> Self:
        validate_rich(self.content)
        return self


class PlanNode(Record):
    id: str
    title: str = "New step"
    completed: bool = False
    needs_review: bool = False
    collapsed: bool = False
    children: list[str] = Field(default_factory=list)
    blocks: list[ContentBlock] = Field(default_factory=list)


class LegacyDocument(Record):
    version: Literal[1] = 1
    revision: int = Field(default=0, ge=0)
    roots: list[str] = Field(default_factory=list)
    nodes: dict[str, PlanNode] = Field(default_factory=dict)
    purchases: dict[str, PurchaseRecord] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_tree(self) -> Self:
        seen: set[str] = set()
        blocks: set[str] = set()

        def visit(ids: list[str], depth: int = 0) -> None:
            if depth > 100:
                raise ValueError("Outline is too deeply nested")
            for key in ids:
                if key in seen or key not in self.nodes or self.nodes[key].id != key:
                    raise ValueError("Outline contains a cycle, duplicate or missing item")
                seen.add(key)
                for block in self.nodes[key].blocks:
                    if block.id in blocks:
                        raise ValueError("Duplicate content block ID")
                    blocks.add(block.id)
                visit(self.nodes[key].children, depth + 1)

        visit(self.roots)
        if seen != set(self.nodes):
            raise ValueError("Outline contains detached items")
        if any(key != value.id for key, value in self.purchases.items()):
            raise ValueError("Purchase ID does not match its key")
        return self


def seed_v1() -> LegacyDocument:
    document = LegacyDocument()
    stack: list[str] = []
    for line in Path(__file__).with_name("planning-seed.md").read_text().splitlines():
        if line.startswith("## "):
            stack = []
            if line[3:] not in {"Finalise van design", "Squabs", "Build"}:
                continue
            key = str(uuid4())
            document.nodes[key] = PlanNode(id=key, title=line[3:])
            document.roots.append(key)
            stack.append(key)
        match = re.match(r"^( *)- \[ \] (.+)$", line)
        if match and stack:
            depth = len(match[1]) // 2 + 1
            stack = stack[:depth]
            key = str(uuid4())
            document.nodes[key] = PlanNode(id=key, title=match[2])
            document.nodes[stack[-1]].children.append(key)
            stack.append(key)
    return document


def convert_v1(raw: dict[str, Any]) -> dict[str, Any]:
    legacy = LegacyDocument.model_validate(raw)
    used = set(legacy.nodes)

    def convert(key: str) -> dict[str, Any]:
        task = legacy.nodes[key]
        text: list[dict[str, Any]] = []
        for index, line in enumerate(task.title.split("\n")):
            if index:
                text.append({"type": "hardBreak"})
            if line:
                text.append({"type": "text", "text": line})
        contents: list[dict[str, Any]] = [{"type": "paragraph", "content": text}]
        for block in task.blocks:
            if block.kind == "text":
                contents.extend(block.content.get("content") or [{"type": "paragraph"}])
            else:
                identity = block.id
                while identity in used:
                    identity = str(uuid5(NAMESPACE_URL, "campervan-purchase-view:" + identity))
                used.add(identity)
                contents.append({"type": "purchaseView", "attrs": {"id": identity, "filter": block.filter.model_dump()}})
        if task.children:
            contents.append({"type": "taskList", "content": [convert(child) for child in task.children]})
        return {"type": "taskItem", "attrs": {"id": key, "checked": task.completed,
                "collapsed": task.collapsed, "needs_review": task.needs_review}, "content": contents}

    content = [{"type": "taskList", "content": [convert(key) for key in legacy.roots]}] if legacy.roots else []
    content.append({"type": "paragraph"})
    return {"version": 2, "revision": legacy.revision, "content": {"type": "doc", "content": content},
            "purchases": {key: value.model_dump() for key, value in legacy.purchases.items()}}
