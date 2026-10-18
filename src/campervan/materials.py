"""Selected stock resolves into the same dimensions used by CAD and the BOM."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from campervan.parameters import Parameters, default_parameters

CATALOGUE_PATH = Path(__file__).with_name("materials.json")
PROJECT_PATH = Path(".local/project.json")


class Product(BaseModel):
    id: str
    name: str
    supplier: str
    url: str
    kind: Literal["sheet", "timber", "hardware"]
    dimensions: dict[str, float]
    specification: str
    checked: str
    price_nzd: float | None = None
    sale_unit: str = "sheet"
    pack_quantity: int = Field(default=1, ge=1)
    availability: str = "Stock not checked"


class MaterialRole(BaseModel):
    id: str
    name: str
    kind: Literal["sheet", "timber", "hardware"]
    fields: dict[str, str]
    default_product_id: str | None = None
    note: str = ""
    quantity: int | None = None  # Only for needed items not represented by assembly leaves.


ROLES = [
    MaterialRole(id="frames", name="Frame plywood", kind="sheet", fields={"thickness": "frame_thickness_mm"}),
    MaterialRole(id="skins", name="Skin plywood", kind="sheet", fields={"thickness": "wall_thickness_mm"}),
    MaterialRole(id="shelves", name="Shelf plywood", kind="sheet", fields={"thickness": "cabinet_shelf_thickness_mm"}),
    MaterialRole(id="drawer", name="Drawer plywood", kind="sheet", fields={"thickness": "drawer_ply_mm"}),
    MaterialRole(
        id="deck", name="Cross-bench deck / lid", kind="sheet", fields={"thickness": "cross_deck_thickness_mm"}
    ),
    MaterialRole(
        id="ledges",
        name="Shelf ledges",
        kind="sheet",
        fields={"thickness": "cabinet_ledge_height_mm"},
        note="Rip strips from the frame plywood; strip width is a cut dimension.",
    ),
    MaterialRole(
        id="slats",
        name="Existing bed slats",
        kind="timber",
        fields={"width": "slat_width_mm", "thickness": "slat_thickness_mm"},
    ),
]

# Sourced products provide the default stock dimensions for the CAD model.
for role in ROLES:
    role.default_product_id = {
        "frames": "tigerply-18",
        "skins": "tigerply-okoume-4",
        "shelves": "tigerply-12",
        "drawer": "tigerply-12",
        "deck": "tigerply-12",
        "ledges": "tigerply-18",
    }.get(role.id)
    if role.id in {"shelves", "drawer", "deck"}:
        role.note = "Share 12mm sheets across shelves, drawer and deck/lid; plan the cuts together."

ROLES.extend(
    [
        MaterialRole(
            id="bearers",
            name="Cross-bench support rails",
            kind="sheet",
            fields={"thickness": "cross_bearer_height_mm"},
            default_product_id="tigerply-18",
            note="Cut the fixed and sliding support rails from the same plywood stock as the frames.",
        ),
        MaterialRole(
            id="guides",
            name="Bed guide ledges",
            kind="sheet",
            fields={"thickness": "ledge_width_mm"},
            default_product_id="tigerply-18",
            note="Cut upright strips from the same plywood stock as the frames.",
        ),
        MaterialRole(
            id="brackets",
            name="Bed angle brackets",
            kind="hardware",
            fields={"length": "bracket_arm_mm", "width": "bracket_width_mm", "thickness": "bracket_thickness_mm"},
            default_product_id="carinya-50-40",
            note="Three on the long bench, two on the cross bench. Check hole positions and bend radius on receipt.",
        ),
        MaterialRole(
            id="stops",
            name="Cross-bed stop plates",
            kind="hardware",
            fields={"length": "cross_stop_plate_length_mm", "width": "cross_stop_plate_width_mm"},
            default_product_id="zenith-100-22",
            note=(
                "Model assumes 2mm steel; supplier does not state thickness. "
                "Measure plate and screw heads before cutting recesses. Screws included."
            ),
        ),
        MaterialRole(
            id="slides",
            name="Rear drawer slides",
            kind="hardware",
            fields={
                "length": "drawer_length_mm",
                "width": "slide_height_mm",
                "thickness": "slide_thickness_mm",
                "travel": "slide_travel_mm",
            },
            default_product_id="instantpanel-1200",
            note=(
                "One complete pair, including all three rail stages. "
                "Non-locking; drawer restraint and M5 fixings still to specify."
            ),
        ),
        MaterialRole(
            id="lid-hinge",
            name="Storage lid hinge",
            kind="hardware",
            fields={},
            quantity=1,
            default_product_id="taskmaster-610",
            note="Candidate continuous hinge; cut to lid hinge edge. Mounting recess and short screws still to detail.",
        ),
        MaterialRole(
            id="bracket-screws",
            name="Bracket screws",
            kind="hardware",
            fields={},
            default_product_id="zenith-8g-15",
            note=(
                "Candidate for brackets into 18mm ply: 15mm screw through 2mm steel. "
                "Check holes and 3mm head allowance; fixing count not modelled."
            ),
        ),
    ]
)


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    product_id: str | None = None
    measured: dict[str, float] = Field(default_factory=dict)
    owned: bool = False
    purchase_quantity: int | None = Field(default=None, ge=0)


class MaterialUpdate(BaseModel):
    role: str
    selection: Selection
    custom: dict[str, float] = Field(default_factory=dict)


class CutPart(BaseModel):
    path: str
    material: str
    length: float
    width: float
    thickness: float


def default_selections() -> dict[str, Selection]:
    return {role.id: Selection(product_id=role.default_product_id) for role in ROLES if role.default_product_id} | {
        "slats": Selection(owned=True)
    }


class Project(BaseModel):
    parameters: Parameters = Field(default_factory=default_parameters)
    materials: dict[str, Selection] = Field(default_factory=default_selections)


def catalogue() -> list[Product]:
    return [Product.model_validate(item) for item in json.loads(CATALOGUE_PATH.read_text())]


def resolve(parameters: Parameters, selections: dict[str, Selection]) -> Parameters:
    products = {product.id: product for product in catalogue()}
    roles = {role.id: role for role in ROLES}
    values = parameters.model_dump()
    for name, selection in selections.items():
        if name not in roles:
            raise ValueError(f"Unknown material role: {name}")
        role = roles[name]
        if set(selection.measured) - role.fields.keys():
            raise ValueError(f"Unknown measured dimension for {role.name}")
        if selection.product_id is None:
            if selection.measured:
                raise ValueError("Use custom dimensions when no product is selected.")
            continue
        product = products.get(selection.product_id)
        if product is None or product.kind != role.kind or not role.fields.keys() <= product.dimensions.keys():
            raise ValueError(f"Product does not provide the stock dimensions required for {role.name}")
        for dimension, parameter in role.fields.items():
            values[parameter] = selection.measured.get(dimension, product.dimensions[dimension])
    return Parameters.model_validate(values)


def load_project(path: Path = PROJECT_PATH) -> Project:
    project = Project.model_validate_json(path.read_text()) if path.exists() else Project()
    project.materials = default_selections() | project.materials
    project.parameters = resolve(project.parameters, project.materials)
    return project


def save_project(project: Project, path: Path = PROJECT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(project.model_dump_json(indent=2) + "\n")
    temporary.replace(path)
