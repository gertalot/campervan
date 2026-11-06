"""Selected stock resolves into the same dimensions used by CAD and the BOM."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from campervan.cutting_models import CuttingState
from campervan.mannequins import MannequinSettings
from campervan.parameters import Parameters, default_parameters
from campervan.paths import PROJECT_PATH

CATALOGUE_PATH = Path(__file__).with_name("materials.json")


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
        id="table-plywood", name="Tabletop panel", kind="sheet",
        fields={"thickness": "table_ply_thickness_mm"}, default_product_id="specrite-pine-18-1200-600",
        note="Two 700 × 250 × 18mm pine leaves fit side by side on one 1200 × 600mm panel, including kerf. "
             "Grain follows the 700mm length. Folded wood stack is 36mm. Finish both faces, edges and hinge pockets. "
             "The mounting spacer remains frame plywood.",
    ),
    MaterialRole(
        id="lagun", name="Lagun swivel table leg", kind="hardware", fields={}, quantity=1,
        note="One 500mm single-arm kit with standard 92 × 170mm bracket and 240 × 200mm tabletop mount. "
             "Confirm bolt lengths and backing against the physical furniture before drilling.",
    ),
    MaterialRole(
        id="table-hinges", name="Tabletop fold-over hinges", kind="hardware", fields={}, quantity=2,
        note="Two Homer HOM006136 hinges, supplied as one pair, for the 18mm pine leaves. "
             "Fosters specifies horizontal support and a 180° fold-over action. "
             "Hinge positions, capacity, mortises, joint gap and fixings remain unconfirmed.",
    ),
    MaterialRole(
        id="cabinet-frames",
        name="Cabinet frame plywood",
        kind="sheet",
        fields={"thickness": "cabinet_frame_thickness_mm"},
    ),
    MaterialRole(
        id="cabinet-partitions",
        name="Cabinet solid vertical plywood",
        kind="sheet",
        fields={"thickness": "cabinet_partition_thickness_mm"},
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
            "Ready-made 18 × 18mm untreated clear pine for shelf ledges, corner cleats and catch blocks. "
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
        "table-plywood": "specrite-pine-18-1200-600",
        "table-hinges": "homer-table-hinge-pair",
        "cabinet-frames": "tigerply-okoume-9",
        "cabinet-partitions": "tigerply-okoume-9",
        "skins": "tigerply-okoume-9",
        "shelves": "tigerply-okoume-6",
        "drawer": "tigerply-12",
        "ledges": "pinetrim-18-18-2400",
    }.get(role.id)
    if role.id == "drawer":
        role.note = "Drawer sides, ends and bottom share 12mm sheets; plan cuts together."
    elif role.id == "shelves":
        role.note = "6mm plywood on continuous glued and screwed perimeter ledges for pantry storage."
    elif role.id in {"cabinet-frames", "cabinet-partitions", "skins"}:
        role.note = "Share 9mm sheets across cabinet frames, solid vertical panels and cross-bench rear skin."

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
            default_product_id="tigerply-okoume-6",
            note="Nine 6mm overlay doors, sharing Tigerply Okoume sheets with the shelves. "
                 "Six drop-down flaps, one front door and the bottom storage pair. Through-fix hinges on thin plywood.",
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
                "Use countersunk through-fixings on the thin plywood door. "
                "Hole sizes, leaf thickness and fixings still require checking against the physical hinge."
            ),
        ),
        MaterialRole(
            id="cabinet-catches",
            name="Cabinet door catches",
            kind="hardware",
            fields={},
            default_product_id="taskmaster-roller-4",
            note=(
                "One double roller catch with keeper per door; nine sets need three four-packs. "
                "30mm finger holes have eased rims. CAD catch envelopes are estimates: align the physical "
                "keepers and rollers before drilling. Check supplied screw lengths against thin plywood; "
                "use short screws or through-fixings. Roller catches have no verified vehicle holding rating. "
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
                "to plywood frame members. Chains, anchors and fixings are not modelled. "
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


def active_roles(parameters: Parameters) -> list[MaterialRole]:
    """Keep optional component selections saved, but omit their purchasing requirements."""
    excluded = set()
    if not parameters.drawer_included:
        excluded.update({"drawer", "slides"})
    if not parameters.table_included:
        excluded.update({"table-plywood", "lagun", "table-hinges"})
    return [role for role in ROLES if role.id not in excluded]


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


def active_cuts(cuts: list[CutPart], parameters: Parameters) -> list[CutPart]:
    """Filter manufacturing requirements without removing reference geometry or its hierarchy."""
    excluded = []
    if not parameters.drawer_included:
        excluded.append("Long bench / Rear drawer")
    if not parameters.table_included:
        excluded.append("Laptop table")
    return [cut for cut in cuts if not any(
        cut.path == root or cut.path.startswith(root + " / ") for root in excluded
    )]


def default_selections() -> dict[str, Selection]:
    return {role.id: Selection(product_id=role.default_product_id) for role in ROLES if role.default_product_id} | {
        "slats": Selection(owned=True)
    }


class Project(BaseModel):
    parameters: Parameters = Field(default_factory=default_parameters)
    materials: dict[str, Selection] = Field(default_factory=default_selections)
    cutting: CuttingState = Field(default_factory=CuttingState)
    mannequins: MannequinSettings | None = None


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
    project.materials.pop("lagun-second-bracket", None)
    project.materials.pop("cabinet-storage-latches", None)  # All doors now share one latch product/role.
    if project.materials.get("ledges", Selection()).product_id == "tigerply-18":
        project.materials["ledges"] = Selection(product_id="pinetrim-18-18-2400")
    if project.materials.get("skins", Selection()).product_id == "tigerply-okoume-4":
        project.materials["skins"] = Selection(product_id="tigerply-okoume-9")
    if project.materials.get("slides", Selection()).product_id == "instantpanel-1200":
        project.materials["slides"] = Selection(product_id="instantpanel-locking-1200")
    if project.materials.get("table-plywood", Selection()).product_id in {"tigerply-18", "tigerply-12", "tigerply-okoume-9"}:
        # Replace the superseded single plywood top with the two-leaf pine design.
        project.materials["table-plywood"] = Selection(product_id="specrite-pine-18-1200-600")
        project.parameters = project.parameters.model_copy(update={"table_depth_mm": 250.0})
    project.materials = default_selections() | project.materials
    project.parameters = resolve(project.parameters, project.materials)
    return project


def save_project(project: Project, path: Path = PROJECT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(project.model_dump_json(indent=2) + "\n")
    temporary.replace(path)
