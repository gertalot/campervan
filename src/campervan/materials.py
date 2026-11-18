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
        id="floor",
        name="Floor plywood",
        kind="sheet",
        fields={"thickness": "floor_ply_thickness_mm"},
        note="The CAD floor is currently one panel. "
        "Its sheet size and division into separate panels still need specifying.",
    ),
    MaterialRole(id="frames", name="Frame plywood", kind="sheet", fields={"thickness": "frame_thickness_mm"}),
    MaterialRole(
        id="table-plywood",
        name="Tabletop panel",
        kind="sheet",
        fields={"thickness": "table_ply_thickness_mm"},
        default_product_id="tigerply-18",
        note="Two 600 × 200 × 18mm plywood leaves share the existing 18mm frame-plywood stock. "
        "Grain follows the 600mm length. Folded wood stack is 36mm. Finish both faces, edges and hinge pockets. "
        "The rear cross-bench mounting frame shares frame plywood.",
    ),
    MaterialRole(
        id="lagun",
        name="Lagun swivel table leg",
        kind="hardware",
        fields={},
        quantity=1,
        note="One 500mm single-arm kit with standard 92 × 170mm bracket and 240 × 200mm tabletop mount. "
        "Confirm bolt lengths and backing against the physical furniture before drilling.",
    ),
    MaterialRole(
        id="table-hinges",
        name="Tabletop fold-over hinges",
        kind="hardware",
        fields={},
        quantity=2,
        note="Two Homer HOM006136 hinges, supplied as one pair, for the 18mm pine leaves. "
        "Fosters specifies horizontal support and a 180° fold-over action. "
        "Hinge positions, capacity, mortises, joint gap and fixings remain unconfirmed.",
    ),
    MaterialRole(
        id="cabinet-frames",
        name="Cabinet front frame and cleats",
        kind="timber",
        fields={"width": "cabinet_frame_width_mm", "thickness": "cabinet_frame_thickness_mm"},
    ),
    MaterialRole(
        id="cabinet-partitions",
        name="Cabinet supporting plywood panels",
        kind="sheet",
        fields={"thickness": "cabinet_partition_thickness_mm"},
    ),
    MaterialRole(id="shelves", name="Shelf plywood", kind="sheet", fields={"thickness": "cabinet_shelf_thickness_mm"}),
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
        "table-hinges": "homer-table-hinge-pair",
        "cabinet-frames": "pinetrim-40-18-1800",
        "cabinet-partitions": "tigerply-okoume-6",
        "shelves": "tigerply-okoume-6",
    }.get(role.id)
    if role.id == "shelves":
        role.note = "6mm pantry shelves bear on face-mounted timber cleats."
    elif role.id == "cabinet-frames":
        role.note = (
            "40 × 18mm untreated pine for the front frame, local shelf cleats, module joints and hardware backing."
        )
    elif role.id == "cabinet-partitions":
        role.note = (
            "6mm supporting end panels and centre divider: scribe side and ceiling edges. Van side closes the back."
        )

ROLES.extend(
    [
        MaterialRole(
            id="bed-slat-brackets",
            name="Moving bed slat-to-frame angles",
            kind="hardware",
            fields={},
            default_product_id="carinya-50-40",
            note="One Carinya 50 × 50 × 40 × 2mm angle per moving slat, fixed to its underside and the frame's inner face. "
            "Seven angles use one eight-pack at the current layout. Lid rebates are 3mm deep with 1mm steel clearance; "
            "only a narrow 3mm edge relief passes through the plywood for each vertical flange. "
            "CAD holes are illustrative; confirm supplied hole positions and screw lengths for 18mm timber before drilling.",
        ),
        MaterialRole(
            id="cabinet-bridge",
            name="Cabinet wheel-arch bridge",
            kind="timber",
            fields={"width": "cabinet_bridge_height_mm", "thickness": "cabinet_bridge_thickness_mm"},
            default_product_id="pinetrim-90-18-1800",
            note="One 90 × 18mm on-edge rail spans the wheel arch between end panels and carries the centre divider. "
            "No middle posts.",
        ),
        MaterialRole(
            id="cabinet-door-bolts",
            name="Cabinet catch-keeper through-bolts",
            kind="hardware",
            fields={},
            quantity=18,
            default_product_id="zenith-m3-12-ss316-8",
            note="M3 × 12 round-head bolt and nut sets: two for each of the nine catch keepers. "
            "Washers separate. Confirm head/hole fit on physical hardware.",
        ),
        MaterialRole(
            id="cabinet-hardware-washers",
            name="Cabinet hardware backing washers",
            kind="hardware",
            fields={},
            quantity=18,
            default_product_id="zenith-m3-flat-washer-ss316-35",
            note="M3 flat backing washers, nominal 8mm outside diameter: 18 catch keeper fixings. "
            "Confirm bearing faces and fit on the physical hardware.",
        ),
        MaterialRole(
            id="cabinet-catch-block-screws",
            name="Cabinet catch-block assembly screws",
            kind="hardware",
            fields={},
            quantity=18,
            default_product_id="zenith-6g-40-100",
            note="Two 6g × 40mm screws through the front header into each square-cut catch block. "
            "Glue the broad mating faces, predrill and countersink. Catch base screws come with the catches.",
        ),
        MaterialRole(
            id="cabinet-module-fasteners",
            name="Cabinet module hex bolts and nuts",
            kind="hardware",
            fields={},
            default_product_id="zenith-m6-90-hex-zinc",
            note="Eight ordinary zinc-plated M6 × 90mm hex bolt-and-nut sets. Nuts included; "
            "two M6 washers per bolt purchased separately. 6.5mm straight clearance holes, no countersinks. "
            "80mm timber stack; confirm actual washer thickness and full nut engagement before assembly.",
        ),
        MaterialRole(
            id="cabinet-module-washers",
            name="Cabinet module washers",
            kind="hardware",
            fields={},
            quantity=16,
            default_product_id="zenith-m6-16-flat-washer-zinc",
            note="Two M6 × 16mm zinc-plated flat washers per module joint, under the hex head and supplied nut.",
        ),
        MaterialRole(
            id="cabinet-glue",
            name="Cabinet wood glue",
            kind="hardware",
            fields={},
            quantity=1,
            default_product_id="selleys-aquadhere-exterior-250",
            note=(
                "One 250ml bottle as an initial cabinet allowance. Glue front-frame joints and "
                "fixed cleat-to-panel mating faces. Keep the module interface unglued. Close-fitting bare wood only; "
                "clamp during curing and leave unstressed for 24 hours. Furniture adhesive, not vehicle anchorage. "
                "Bond the fixed centre divider and end panels to their local timber. "
                "The van side closes the open wall-facing back."
            ),
        ),
        MaterialRole(
            id="cabinet-doors",
            name="Cabinet door plywood",
            kind="sheet",
            fields={"thickness": "cabinet_door_thickness_mm"},
            default_product_id="tigerply-okoume-6",
            note="Nine 6mm inset doors sharing sheets with the shelves. "
            "Six drop-down flaps, one front door and the bottom storage pair. Piano hinges fix into pine-backed edges.",
        ),
        MaterialRole(
            id="cabinet-hinges",
            name="Cabinet door hinges",
            kind="hardware",
            fields={},
            quantity=9,
            default_product_id="taskmaster-piano-610-27-ss",
            note="One 610 × 27mm stainless piano-hinge length per door, trimmed to the backing strip. "
            "Mounting screws are included with the hinges, as shown in the product photo. "
            "Allow approximately 180 screws across the nine trimmed hinges, included in the hinge price; "
            "no separate screw purchase. Supplied screw size and count are not published. "
            "Leaves hidden on the unrebated door/jamb edges. Leaf thickness, pin, gap, mortices and "
            "fixing holes are provisional until checked against the physical hinge.",
        ),
        MaterialRole(
            id="cabinet-hinge-backing",
            name="Cabinet door hinge backing strips",
            kind="timber",
            fields={},
            default_product_id="pinetrim-18-18-1200",
            note="18 × 18mm untreated pine glued behind each 6mm door's hinge edge. "
            "Ends stop 10mm short of perpendicular door edges to clear the remaining rebates. "
            "Glue and clamp the full mating face; allow full cure, then accurately pilot-drill the assembled edge.",
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
            id="bed-lid-hinges",
            name="Storage bed gas-assisted lift pair · 30kg",
            kind="hardware",
            fields={},
            quantity=1,
            default_product_id="instant-panel-bed-lift-30kg-600-pair",
            note="One pair of Instant Panel 600mm bed lifts. Pivot centres and mounting are photo estimates; "
            "30kg version selected. Seven M6 coach bolts per lift: four fixed and three moving. "
            "Confirm actual stroke, fixing holes and supported lid weight.",
        ),
        MaterialRole(
            id="bed-lift-bolts",
            name="Bed lift fixed-rail coach-head through-bolts",
            kind="hardware",
            fields={},
            quantity=8,
            default_product_id="zenith-m6-40-coach-zinc",
            note="Four M6 × 40mm coach bolts per fixed rail, eight for the pair. "
            "Smooth heads face outwards; replace supplied nuts with separate Nylocs. "
            "18mm ply plus 6.7mm steel mounting stack. CAD placement and head dimensions are illustrative; "
            "match-drill physical hardware.",
        ),
        MaterialRole(
            id="bed-lift-lid-bolts",
            name="Bed lift recessed Allen-drive through-bolts",
            kind="hardware",
            fields={},
            quantity=6,
            default_product_id="pinnacle-m6-50-allen-ruspert-6",
            note="Three M6 × 50mm Allen-drive round-head bolts per moving rail, six total (one pack). "
            "Top counterbores in the fixed slats are provisionally 18mm diameter × 6mm deep, "
            "with a 16mm washer beneath each head. Heads sit below the slat surface; Allen access is from above. "
            "Bolt passes through the remaining slat, lid and 6.7mm steel rail. Replace supplied nuts with Nylocs. "
            "Head size, key size and recess dimensions need checking against physical bolts before drilling.",
        ),
        MaterialRole(
            id="bed-lift-washers",
            name="Bed lift washers",
            kind="hardware",
            fields={},
            quantity=20,
            default_product_id="zenith-m6-16-flat-washer-zinc",
            note="Fourteen M6 × 16mm steel washers against the hinge rails under the Nylocs, "
            "plus six beneath the recessed Allen heads to spread load over the wood. "
            "Nominal 1.6mm thickness; confirm against physical washers before boring the slats.",
        ),
        MaterialRole(
            id="bed-lift-lock-nuts",
            name="Bed lift M6 locking nuts",
            kind="hardware",
            fields={},
            quantity=14,
            default_product_id="zenith-m6-nyloc-zinc-12",
            note="Fourteen M6 Nylocs replace the coach bolts' supplied plain nuts; buy two twelve-packs. "
            "Confirm full nylon engagement and clearance from the moving linkage.",
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
    fitting_edges: dict[Literal["left", "right", "top", "bottom"], str] = Field(default_factory=dict)


def active_cuts(cuts: list[CutPart], parameters: Parameters) -> list[CutPart]:
    """Filter manufacturing requirements without removing reference geometry or its hierarchy."""
    excluded = []
    if not parameters.table_included:
        excluded.append("Laptop table")
    return [cut for cut in cuts if not any(cut.path == root or cut.path.startswith(root + " / ") for root in excluded)]


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
    for role in (
        "deck", "bearers", "stops", "lid-hinge", "drawer", "slides", "guides", "brackets", "bracket-screws", "skins",
        "bed-legs",
    ):
        project.materials.pop(role, None)
    # The rejected lift-up layout used this role; individual drop-down flaps use chain instead.
    project.materials.pop("cabinet-hinge-frame-bolts", None)
    if project.materials.get("cabinet-hinges", Selection()).product_id == "zenith-butt-35":
        project.materials["cabinet-hinges"] = Selection(product_id="taskmaster-piano-610-27-ss")
    project.materials.pop("cabinet-stays", None)
    project.materials.pop("lagun-second-bracket", None)
    project.materials.pop("cabinet-storage-latches", None)  # All doors now share one latch product/role.
    project.materials.pop("cabinet-module-nuts", None)  # Ordinary bolt sets include their nuts.
    if project.materials.get("cabinet-module-fasteners", Selection()).product_id in {
        "anzor-m5-90-csk-316", "fortress-m5-90-csk-zinc-100"
    }:
        project.materials["cabinet-module-fasteners"] = Selection(product_id="zenith-m6-90-hex-zinc")
    if project.materials.get("cabinet-module-washers", Selection()).product_id == "pinnacle-m5-flat-washer-ss316-12":
        project.materials["cabinet-module-washers"] = Selection(product_id="zenith-m6-16-flat-washer-zinc")
    # Older sheet-framed cabinets use the current front frame and supporting panels.
    old_frame = project.materials.get("cabinet-frames", Selection()).product_id
    if (
        "cabinet-back" in project.materials
        or "ledges" in project.materials
        or (old_frame and old_frame.startswith("tigerply"))
    ):
        project.materials["cabinet-frames"] = Selection(product_id="pinetrim-40-18-1800")
        if "cabinet-partitions" not in project.materials:
            project.materials["cabinet-partitions"] = Selection(product_id="tigerply-okoume-6")
        project.materials["cabinet-doors"] = Selection(product_id="tigerply-okoume-6")
        project.materials["shelves"] = Selection(product_id="tigerply-okoume-6")
        project.parameters = project.parameters.model_copy(
            update={
                "cabinet_door_corner_radius_mm": 2.0,
                "cabinet_door_edge_radius_mm": 1.0,
                "cabinet_ceiling_gap_mm": 5.0,
            }
        )
    for retired in ("ledges", "cabinet-module-timber", "cabinet-back", "cabinet-pillar"):
        project.materials.pop(retired, None)
    for role, selection in project.materials.items():
        if selection.product_id == "bbi-redline-6-1200-1195":
            project.materials[role] = selection.model_copy(
                update={"product_id": "tigerply-okoume-6", "purchase_quantity": None}
            )
    if project.materials.get("cabinet-partitions", Selection()).product_id == "birch-3-2440":
        project.materials["cabinet-partitions"] = Selection(product_id="tigerply-okoume-6")
    if project.materials.get("table-plywood", Selection()).product_id == "specrite-pine-18-1200-600":
        project.materials["table-plywood"] = project.materials.get(
            "frames", Selection(product_id="tigerply-18")
        ).model_copy(deep=True)
    project.materials = default_selections() | project.materials
    if project.materials["bed-lift-lid-bolts"].product_id == "zenith-m6-55-coach-zinc":
        project.materials["bed-lift-lid-bolts"] = Selection(product_id="pinnacle-m6-50-allen-ruspert-6")
    project.parameters = resolve(project.parameters, project.materials)
    return project


def save_project(project: Project, path: Path = PROJECT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(project.model_dump_json(indent=2) + "\n")
    temporary.replace(path)
