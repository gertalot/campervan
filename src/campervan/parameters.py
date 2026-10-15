"""Editable vehicle and furniture dimensions in millimetres."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Parameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, allow_inf_nan=False)

    cargo_width_mm: float = Field(
        default=1500.0,
        gt=0,
        title="Cargo width",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Floor outline"]},
    )

    cargo_length_mm: float = Field(
        default=1860.0,
        gt=0,
        title="Cargo length",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Floor outline"]},
    )

    arch_rear_offset_mm: float = Field(
        default=216.0,
        ge=0,
        title="Rear offset",
        description="Distance from the rear floor edge to the wheel arches.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Wheel arches"]},
    )

    arch_length_mm: float = Field(
        default=750.0,
        gt=0,
        title="Length",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Wheel arches"]},
    )

    arch_height_mm: float = Field(
        default=280.0,
        gt=0,
        title="Height",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Wheel arches"]},
    )

    arch_radius_mm: float = Field(
        default=200.0,
        gt=0,
        title="Top radius",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Wheel arches"]},
    )

    arch_gap_mm: float = Field(
        default=1220.0,
        gt=0,
        title="Clear gap",
        description="Clear width between the arches; intrusion is derived from cargo width.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Wheel arches"]},
    )

    rear_corner_radius_mm: float = Field(
        default=100.0,
        gt=0,
        title="Radius",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear corners"]},
    )

    rear_corner_height_mm: float = Field(
        default=1228.0,
        gt=0,
        title="Height",
        description="Reference surface height: the original rear door opening height plus its zero sill.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear corners"]},
    )

    long_bench_width_mm: float = Field(
        default=600.0, gt=0, title="Width", json_schema_extra={"unit": "mm", "group": ["Long bench"]}
    )

    seat_length_mm: float = Field(
        default=1280.0, gt=0, title="Length", json_schema_extra={"unit": "mm", "group": ["Long bench"]}
    )

    platform_height_mm: float = Field(
        default=400.0,
        gt=0,
        title="Platform height",
        description="Finished slat-top height; frame height subtracts slat thickness.",
        json_schema_extra={"unit": "mm", "group": ["Long bench"]},
    )

    frame_thickness_mm: float = Field(
        default=18.0, gt=0, title="Frame thickness", json_schema_extra={"unit": "mm", "group": ["Long bench"]}
    )

    member_width_mm: float = Field(
        default=60.0, gt=0, title="Member width", json_schema_extra={"unit": "mm", "group": ["Long bench"]}
    )

    inside_radius_mm: float = Field(
        default=25.0, gt=0, title="Opening radius", json_schema_extra={"unit": "mm", "group": ["Long bench"]}
    )

    drawer_mount_band_mm: float = Field(
        default=100.0,
        gt=0,
        title="Mounting band",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame"]},
    )

    arch_clearance_mm: float = Field(
        default=50.0,
        ge=0,
        title="Arch clearance",
        description="Target longitudinal clearance; rear corner setback can reduce the rear gap.",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame", "Wall-side frame"]},
    )

    rear_corner_allowance_mm: float = Field(
        default=20.0,
        ge=0,
        title="Corner allowance",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame", "Wall-side frame"]},
    )

    wall_thickness_mm: float = Field(
        default=7.0,
        gt=0,
        title="Skin thickness",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame", "Cab-end skin"]},
    )

    drawer_frame_height_mm: float = Field(
        default=300.0,
        gt=0,
        title="Frame height",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame", "Internal drawer-support frame"]},
    )

    drawer_arch_clearance_mm: float = Field(
        default=10.0,
        gt=0,
        title="Arch clearance",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame", "Internal drawer-support frame"]},
    )

    bed_width_mm: float = Field(
        default=1070.0,
        gt=0,
        title="Bed width",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed"]},
    )

    slat_thickness_mm: float = Field(
        default=18.0,
        gt=0,
        title="Slat thickness",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed"]},
    )

    slat_width_mm: float = Field(
        default=80.0, gt=0, title="Slat width", json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed"]}
    )

    slat_side_gap_mm: float = Field(
        default=5.0, gt=0, title="Slat gap", json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed"]}
    )

    ledge_width_mm: float = Field(
        default=25.0,
        gt=0,
        title="Ledge width",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed", "Guide ledges"]},
    )

    bed_extension_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Bed extension (%)",
        description="0 is the retracted seat; 100 is the fully extended bed.",
        json_schema_extra={
            "unit": "%",
            "group": ["Long bench", "Sliding bed", "Sliding assembly"],
            "control": "position",
        },
    )

    sliding_strip_width_mm: float = Field(
        default=40.0,
        gt=0,
        title="Tie strip width",
        json_schema_extra={
            "unit": "mm",
            "group": ["Long bench", "Sliding bed", "Sliding assembly", "Tie strip / extension stop"],
        },
    )

    strip_end_clearance_mm: float = Field(
        default=2.0,
        ge=0,
        title="Strip end gap",
        json_schema_extra={
            "unit": "mm",
            "group": ["Long bench", "Sliding bed", "Sliding assembly", "Tie strip / extension stop"],
        },
    )

    bracket_arm_mm: float = Field(
        default=50.0,
        gt=0,
        title="Arm length",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed", "Sliding assembly", "Angle brackets"]},
    )

    bracket_width_mm: float = Field(
        default=40.0,
        gt=0,
        title="Width",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed", "Sliding assembly", "Angle brackets"]},
    )

    bracket_thickness_mm: float = Field(
        default=2.0,
        gt=0,
        title="Thickness",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed", "Sliding assembly", "Angle brackets"]},
    )

    bracket_bend_radius_mm: float = Field(
        default=3.0,
        gt=0,
        title="Bend radius",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed", "Sliding assembly", "Angle brackets"]},
    )

    bracket_head_allowance_mm: float = Field(
        default=3.0,
        ge=0,
        title="Head allowance",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed", "Sliding assembly", "Angle brackets"]},
    )

    bracket_clearance_mm: float = Field(
        default=1.0,
        gt=0,
        title="Clearance",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Sliding bed", "Sliding assembly", "Angle brackets"]},
    )

    @model_validator(mode="after")
    def check_geometry(self) -> Self:
        if self.arch_gap_mm >= self.cargo_width_mm:
            raise ValueError("Arch clear gap must be smaller than cargo width.")
        if self.arch_rear_offset_mm + self.arch_length_mm > self.cargo_length_mm:
            raise ValueError("Wheel arches must fit within the cargo length.")
        if self.arch_radius_mm >= self.arch_height_mm or 2 * self.arch_radius_mm >= self.arch_length_mm:
            raise ValueError("Arch top radius must be below its height and half its length.")
        if 2 * self.rear_corner_radius_mm >= self.cargo_width_mm or self.rear_corner_radius_mm >= self.cargo_length_mm:
            raise ValueError("Rear corner radius must fit within the cargo outline.")
        if self.long_bench_width_mm >= self.cargo_width_mm or self.seat_length_mm > self.cargo_length_mm:
            raise ValueError("Long bench must fit within the cargo outline.")
        if self.bed_width_mm >= self.cargo_width_mm:
            raise ValueError("Bed width must leave space within the cargo outline.")
        if self.member_width_mm < self.frame_thickness_mm:
            raise ValueError("Frame members must cover the plywood thickness at joints.")
        if self.platform_height_mm <= self.slat_thickness_mm + 2 * self.member_width_mm:
            raise ValueError("Platform height must leave room for the frame below the slats.")
        return self


def default_parameters() -> Parameters:
    return Parameters()


def parameter_schema() -> dict[str, object]:
    return Parameters.model_json_schema()
