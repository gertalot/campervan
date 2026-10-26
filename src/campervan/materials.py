"""Selected stock resolves into the same dimensions used by CAD and the BOM."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from campervan.cutting_models import CuttingState
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
    MaterialRole(
        id="floor", name="Floor plywood", kind="sheet", fields={"thickness": "floor_ply_thickness_mm"},
        note="The CAD floor is currently one panel. Its sheet size and division into separate panels still need specifying.",
    ),
    MaterialRole(id="frames", name="Frame plywood", kind="sheet", fields={"thickness": "frame_thickness_mm"}),
    MaterialRole(
        id="table-plywood", name="Laptop tabletop plywood", kind="sheet",
        fields={"thickness": "table_ply_thickness_mm"}, default_product_id="tigerply-18",
        note="600 × 360mm solid top; share the 18mm sheets with the bench frames. Mount backing also uses frame plywood.",
    ),
    MaterialRole(
        id="lagun", name="Lagun swivel table leg", kind="hardware", fields={}, quantity=1,
        note="One 500mm single-arm kit with standard 92 × 170mm bracket. Both CAD mount positions use this one kit. "
             "Confirm bolt lengths and backing against the physical furniture before drilling.",
    ),
    MaterialRole(
        id="lagun-second-bracket", name="Second Lagun mounting bracket", kind="hardware", fields={}, quantity=1,
        note="Additional standard 92 × 170mm bracket for the second mounting location. One table moves between the mounts.",
    ),
    MaterialRole(
        id="cabinet-frames",
        name="Cabinet structure plywood",
        kind="sheet",
        fields={"thickness": "cabinet_frame_thickness_mm"},
    ),
    MaterialRole(
        id="skins", name="Cross-bench rear plywood", kind="sheet",
        fields={"thickness": "cross_bench_skin_thickness_mm"},
    ),
    MaterialRole(id="shelves", name="Shelf plywood", kind="sheet", fields={"thickness": "cabinet_shelf_thickness_mm"}),
    MaterialRole(id="drawer", name="Drawer plywood", kind="sheet", fields={"thickness": "drawer_ply_mm"}),
    MaterialRole(
        id="ledges",
        name="Cabinet battens",
        kind="timber",
        fields={"width": "cabinet_ledge_size_mm", "thickness": "cabinet_ledge_height_mm"},
        note=(
            "Ready-made 18 × 18mm untreated clear pine for shelf ledges, corner cleats and latch strike blocks. "
            "Square crosscuts only: wall ledges now meet straight rear rails, with no wall-facing bevels. "
            "No plywood strips to rip. Plan crosscuts with kerf/waste before buying lengths."
        ),
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
        "table-plywood": "tigerply-18",
        "cabinet-frames": "tigerply-12",
        "skins": "tigerply-okoume-9",
        "shelves": "tigerply-12",
        "drawer": "tigerply-12",
        "ledges": "pinetrim-18-18-2400",
    }.get(role.id)
    if role.id in {"cabinet-frames", "shelves", "drawer"}:
        role.note = "Share 12mm sheets across cabinet partitions/frames, shelves and drawer; plan cuts together."
    elif role.id == "skins":
        role.note = "One cross-bench rear skin; share the 9mm sheet with the cabinet doors."

ROLES.extend(
    [
        MaterialRole(
            id="cabinet-glue",
            name="Cabinet wood glue",
            kind="hardware",
            fields={},
            quantity=1,
            default_product_id="selleys-aquadhere-exterior-250",
            note=(
                "One 250ml bottle as an initial cabinet allowance. Glue shelf-to-ledge, ledge-to-panel and "
                "corner-cleat mating faces, including the panel/frame seams. Close-fitting bare wood only; "
                "clamp during curing and leave unstressed for 24 hours. Furniture adhesive, not vehicle anchorage. "
                "Flute-board lining remains non-structural and is not bonded with this PVA."
            ),
        ),
        MaterialRole(
            id="cabinet-doors",
            name="Cabinet door plywood",
            kind="sheet",
            fields={"thickness": "cabinet_door_thickness_mm"},
            default_product_id="tigerply-okoume-9",
            note="Nine overlay doors: six drop-down flaps, one front door and the bottom storage pair.",
        ),
        MaterialRole(
            id="cabinet-hinges",
            name="Cabinet door hinges",
            kind="hardware",
            fields={},
            quantity=18,
            default_product_id="zenith-butt-35",
            note=(
                "Two per door. Face-mount the leaves between door rear and aisle frame, within the closing gap. "
                "Use countersunk through-fixings on the 9mm door, not screws into its edge. "
                "Hole sizes, leaf thickness and fixings still require checking against the physical hinge."
            ),
        ),
        MaterialRole(
            id="cabinet-catches",
            name="Cabinet door catches",
            kind="hardware",
            fields={},
            default_product_id="vanlifer-point-ll016",
            note=(
                "One positive push latch per door, including its supplied striker. 50mm from front face to body rear "
                "means 41mm projects behind 9mm plywood. Five strikers mount under shelf ledges; four 70mm pine "
                "blocks support the topmost and bottom-storage strikers. No centre post in the storage openings. "
                "Body/bore dimensions follow the supplier drawing, but striker size, flange thickness "
                "and fixings need checking on receipt."
            ),
        ),
        MaterialRole(
            id="cabinet-chains",
            name="Drop-down door chain restraints",
            kind="hardware",
            fields={},
            quantity=2,
            default_product_id="pinnacle-double-jack-2",
            note=(
                "Two 3m packs for twelve short restraints: two per drop-down door. "
                "Allow roughly 240–300mm each at default door sizes; cut to the actual anchor positions "
                "so each door stops horizontally. Through-fix the door anchors and fasten cabinet anchors "
                "to plywood frame members, not the 4mm skin. Chains, anchors and fixings are not modelled. "
                "Confirm link openings, anchor details and closing clearance before buying fixings."
            ),
        ),
        MaterialRole(
            id="cabinet-back",
            name="Cabinet back lining",
            kind="sheet",
            fields={"thickness": "cabinet_back_thickness_mm"},
            default_product_id="tunnelcore-white-3",
            note=(
                "Curved backing to the plywood ceiling, clear of the rear corner, with a wheel-arch notch. "
                "Cut rectangle uses developed curve length; confirm flute orientation before cutting."
            ),
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
            note=(
                "Three on the long bench; the fixed cross bench has no angle brackets. "
                "Check hole positions and bend radius on receipt."
            ),
        ),
        MaterialRole(
            id="slides",
            name="Locking drawer sliders",
            kind="hardware",
            fields={
                "length": "drawer_length_mm",
                "width": "slide_height_mm",
                "thickness": "slide_thickness_mm",
                "travel": "slide_travel_mm",
            },
            default_product_id="instantpanel-locking-1200",
            note=(
                "One complete pair, locking fully closed and fully open. Includes all three telescoping stages. "
                "Levers project toward the rear doors; allow 50mm operating clearance. M5 fixings not included."
            ),
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
    outline: list[tuple[float, float]] = Field(default_factory=list)
    holes: list[list[tuple[float, float]]] = Field(default_factory=list)
    profile_note: str = ""
    profile_axes: str = ""


def default_selections() -> dict[str, Selection]:
    return {role.id: Selection(product_id=role.default_product_id) for role in ROLES if role.default_product_id} | {
        "slats": Selection(owned=True)
    }


class Project(BaseModel):
    parameters: Parameters = Field(default_factory=default_parameters)
    materials: dict[str, Selection] = Field(default_factory=default_selections)
    cutting: CuttingState = Field(default_factory=CuttingState)


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
    if path.exists():
        saved = json.loads(path.read_text())
        parameters = saved.get("parameters", {})
        # Previously one saved position controlled both benches.
        project = Project.model_validate(saved | {"parameters": parameters})
    else:
        project = Project()
    for role in ("deck", "bearers", "stops", "lid-hinge"):
        project.materials.pop(role, None)
    # The rejected lift-up layout used this role; individual drop-down flaps use chain instead.
    project.materials.pop("cabinet-stays", None)
    project.materials.pop("cabinet-storage-latches", None)  # All doors now share one latch product/role.
    if project.materials.get("cabinet-catches", Selection()).product_id == "taskmaster-roller-4":
        project.materials["cabinet-catches"] = Selection(product_id="vanlifer-point-ll016")
    if project.materials.get("ledges", Selection()).product_id == "tigerply-18":
        project.materials["ledges"] = Selection(product_id="pinetrim-18-18-2400")
    if project.materials.get("skins", Selection()).product_id == "tigerply-okoume-4":
        project.materials["skins"] = Selection(product_id="tigerply-okoume-9")
    if project.materials.get("slides", Selection()).product_id == "instantpanel-1200":
        project.materials["slides"] = Selection(product_id="instantpanel-locking-1200")
    project.materials = default_selections() | project.materials
    project.parameters = resolve(project.parameters, project.materials)
    return project


def save_project(project: Project, path: Path = PROJECT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(project.model_dump_json(indent=2) + "\n")
    temporary.replace(path)
