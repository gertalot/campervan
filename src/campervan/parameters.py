"""Editable vehicle and furniture dimensions in millimetres."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Parameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, allow_inf_nan=False)

    cargo_width_mm: float = Field(
        default=1500.0,
        gt=0,
        title="Width (body and layout)",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Floor outline"]},
    )

    cargo_length_mm: float = Field(
        default=1860.0,
        gt=0,
        title="Furniture layout length",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Floor outline"]},
    )

    furniture_rear_gap_mm: float = Field(
        default=100.0,
        ge=0,
        title="Furniture gap to rear door",
        description="Furniture setback from the rear opening at the pillar; the opening centre bows farther aft.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Floor outline"]},
    )

    arch_rear_offset_mm: float = Field(
        default=310.0,
        ge=0,
        title="Rear offset",
        description="Approx. 310mm from closed rear door beside pillar, along wall; aligned to measured door opening.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Wheel arches"]},
    )

    arch_length_mm: float = Field(
        default=760.0,
        gt=0,
        title="Length",
        description="Wall-side span: measured front 1070mm minus rear 310mm from the same rear-door reference.",
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

    arch_crown_radius_mm: float = Field(
        default=20.0,
        gt=0,
        title="Crown edge radius",
        description="Estimated transverse rounding of the wheel-house crown; preserves its footprint and clear gap.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Wheel arches"]},
    )

    rear_corner_radius_mm: float = Field(
        default=200.0,
        gt=0,
        title="Corner transition depth",
        description="Rear pillar-to-side-panel depth from the pillar datum; also sets furniture clearance.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear corners"]},
    )

    body_length_mm: float = Field(
        default=1900.0,
        gt=0,
        title="Body length",
        description="Japanese catalogue cargo length. Independent of furniture layout; cab endpoint needs measuring.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references"]},
    )

    body_height_mm: float = Field(
        default=1347.0,
        gt=0,
        title="Bare roof height",
        description="Estimated bare roof above finished floor: catalogue 1365mm minus about 18mm floor build-up.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references"]},
    )

    body_upper_width_mm: float = Field(
        default=1250.0,
        gt=0,
        title="Roof shoulder width",
        description="Estimated interior width where the walls meet the roof; measure at the roof shoulders.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    wall_taper_start_mm: float = Field(
        default=490.0,
        gt=0,
        title="Taper starts above floor",
        description="Estimated height where the upright lower walls begin curving inward.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_opening_width_mm: float = Field(
        default=680.0,
        gt=0,
        title="Door opening width",
        description="Measured lower opening width along the van; the rear edge flares outward higher up.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_opening_height_mm: float = Field(
        default=1170.0,
        gt=0,
        title="Door opening height",
        description="Measured opening centre height above finished plywood floor; 1170mm with zero sill offset.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_opening_sill_mm: float = Field(
        default=0.0,
        ge=0,
        title="Door sill height",
        description="Estimated height above the floor; opening positions and corner radii need measuring.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_opening_radius_mm: float = Field(
        default=60.0,
        gt=0,
        title="Door opening corner radius",
        description="Estimated rounded aperture corners, not a measured pressed-panel radius.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    left_door_front_offset_mm: float = Field(
        default=10.0,
        gt=0,
        title="Door setback from cab end",
        description="1900mm body boundary minus measured front rubber-seal position at 1890mm.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls", "Left wall"]},
    )

    right_door_front_offset_mm: float = Field(
        default=10.0,
        gt=0,
        title="Door setback from cab end",
        description="1900mm body boundary minus measured front rubber-seal position at 1890mm.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls", "Right wall"]},
    )

    roof_crown_mm: float = Field(
        default=55.0,
        gt=0,
        title="Crown rise",
        description="Estimated rise from the roof shoulders to the centre of the bare roof.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Bare roof"]},
    )

    roof_bow_depth_mm: float = Field(
        default=54.0,
        gt=0,
        title="Centre depth",
        description="Estimated bow depth at the roof centre; the top follows the bare roof.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Roof bows"]},
    )

    roof_bow_crown_mm: float = Field(
        default=20.0,
        ge=0,
        title="Underside crown rise",
        description="Measured plywood rise from wall to centre: 20mm. Bows follow the same shallow curve.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Roof bows"]},
    )

    roof_bow_width_mm: float = Field(
        default=80.0,
        gt=0,
        title="Fore–aft width",
        description="Estimated envelope width of each bow, including its flanges.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Roof bows"]},
    )

    roof_bow_rear_y_mm: float = Field(
        default=400.0,
        gt=0,
        title="Rear bow position",
        description="Estimated centre distance from the model rear datum toward the cab.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Roof bows"]},
    )

    roof_bow_middle_y_mm: float = Field(
        default=950.0,
        gt=0,
        title="Middle bow position",
        description="Estimated centre distance from the model rear datum toward the cab.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Roof bows"]},
    )

    roof_bow_front_y_mm: float = Field(
        default=1500.0,
        gt=0,
        title="Front bow position",
        description="Estimated centre distance from the model rear datum toward the cab.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Roof bows"]},
    )

    ceiling_ply_thickness_mm: float = Field(
        default=3.0,
        gt=0,
        title="Plywood thickness",
        description="Plywood attached directly to the bow undersides; thickness measured normal to its curve.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Finished ceiling"]},
    )

    rear_opening_width_mm: float = Field(
        default=1265.0,
        gt=0,
        title="Opening width",
        description="Measured width at 390mm above finished floor, at the slat tops of the existing bed.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    rear_opening_height_mm: float = Field(
        default=1280.0,
        gt=0,
        title="Opening height",
        description="Measured centre seal-to-seal height; sill offset from finished floor remains an estimate.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    rear_opening_upper_width_mm: float = Field(
        default=1115.0,
        gt=0,
        title="Upper opening width",
        description="Measured width one top-corner height below the highest point (60mm at defaults).",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    rear_opening_radius_mm: float = Field(
        default=60.0,
        gt=0,
        title="Top corner size",
        description="Height from the upper-width measurement to the opening top; rounded top shoulders.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    cab_length_mm: float = Field(
        default=1100.0,
        gt=0,
        title="Cab length",
        description="Estimated cab floor extension forward from the cargo body endpoint.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Floor"]},
    )
    cab_front_width_mm: float = Field(
        default=1400.0,
        gt=0,
        title="Front floor width",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Floor"]},
    )
    cab_seat_width_mm: float = Field(
        default=475.0,
        gt=0,
        title="Seat width",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_seat_depth_mm: float = Field(
        default=455.0,
        gt=0,
        title="Cushion depth",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_seat_height_mm: float = Field(
        default=300.0,
        gt=0,
        title="Cushion rear height",
        description="Rear cushion top above the shared floor. The front rises separately.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_seat_front_rise_mm: float = Field(
        default=80.0,
        ge=0,
        title="Cushion front rise",
        description="Front lip above the rear cushion top; estimated from the older Japanese side drawing.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_seat_thickness_mm: float = Field(
        default=90.0,
        gt=0,
        title="Padding thickness",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_backrest_height_mm: float = Field(
        default=600.0,
        gt=0,
        title="Backrest to shoulders",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_headrest_height_mm: float = Field(
        default=180.0,
        gt=0,
        title="Integrated headrest height",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_seat_spacing_mm: float = Field(
        default=760.0,
        gt=0,
        title="Seat centre spacing",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats"]},
    )
    cab_driver_offset_mm: float = Field(
        default=175.0,
        ge=0,
        title="Forward offset",
        description="Pivot forward of cargo boundary; calibrated to rear surface at Z=490. Right (+X).",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats", "Driver seat"]},
    )
    cab_driver_recline_deg: float = Field(
        default=10.437,
        ge=0,
        le=45,
        title="Recline",
        json_schema_extra={"unit": "°", "group": ["Vehicle references", "Cab", "Seats", "Driver seat"]},
    )
    cab_passenger_offset_mm: float = Field(
        default=175.0,
        ge=0,
        title="Forward offset",
        description="Pivot forward of cargo boundary; calibrated to rear surface at Z=490. Left (−X).",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Seats", "Passenger seat"]},
    )
    cab_passenger_recline_deg: float = Field(
        default=10.437,
        ge=0,
        le=45,
        title="Recline",
        json_schema_extra={"unit": "°", "group": ["Vehicle references", "Cab", "Seats", "Passenger seat"]},
    )
    cab_headliner_front_setback_mm: float = Field(
        default=200.0,
        ge=0,
        title="Front setback",
        description="Headliner front edge behind the front end of the cab floor.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Headliner"]},
    )
    cab_headliner_front_drop_mm: float = Field(
        default=0.0,
        ge=0,
        title="Front drop",
        description="Below the rear headliner centre. Zero keeps it level along the cab.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Headliner"]},
    )
    cab_headliner_front_width_mm: float = Field(
        default=1150.0,
        gt=0,
        title="Front width",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Headliner"]},
    )
    cab_headliner_crown_mm: float = Field(
        default=35.0,
        ge=0,
        title="Crown rise",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Cab", "Headliner"]},
    )

    floor_build_up_mm: float = Field(
        default=18.0,
        ge=0,
        title="Floor build-up",
        description="Finished floor above vehicle floor; owner estimate.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Body floor"]},
    )

    floor_ply_thickness_mm: float = Field(
        default=12.0,
        ge=0,
        title="Floor plywood",
        description="Owner reports 11–12mm; use 12mm within the 18mm total build-up.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Body floor"]},
    )

    rear_corner_straight_mm: float = Field(
        default=60.0,
        ge=0,
        title="Straight section",
        description="Distance forward at constant width before the corner flares into the side panel.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear corners"]},
    )

    rear_opening_floor_width_mm: float = Field(
        default=1250.0,
        ge=0,
        title="Width at floor",
        description="Measured clear width between rear pillars at finished-floor height.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    rear_opening_bow_mm: float = Field(
        default=120.0,
        ge=0,
        title="Centre rearward bow",
        description="Centreline opening is 120mm aft of the pillar at slat height.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    rear_opening_rake_mm: float = Field(
        default=80.0,
        ge=0,
        title="Upper forward rake",
        description="Unmeasured estimate from owner photos; upper opening leans forward.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    rear_opening_sill_mm: float = Field(
        default=0.0,
        title="Seal sill offset",
        description="Bottom seal relative to finished floor; zero is provisional.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    rear_hatch_centre_y_mm: float = Field(
        default=-30.0,
        title="Closed inner panel position",
        description="100mm bed setback minus 130mm closed-door clearance at centreline.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )

    side_opening_upper_width_mm: float = Field(
        default=760.0,
        ge=0,
        title="Upper opening width",
        description="Estimated from the revised 680mm lower opening plus the original 80mm rearward transition.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_opening_curve_start_mm: float = Field(
        default=630.0,
        ge=0,
        title="Curve start height",
        description="140mm above the existing 490mm mattress top.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_opening_upper_lean_mm: float = Field(
        default=20.0,
        ge=0,
        title="Upper pillar lean",
        description="Photo estimate: upper opening edge leans rearward toward the roof, above the lower curve.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_opening_curve_end_mm: float = Field(
        default=770.0,
        ge=0,
        title="Curve end height",
        description="280mm above the existing 490mm mattress top.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_pillar_width_mm: float = Field(
        default=180.0,
        gt=0,
        title="Rear pillar fore–aft width",
        description="Measured at the existing mattress height, from rear side panel to sliding-door opening.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    side_pillar_intrusion_mm: float = Field(
        default=40.0,
        ge=0,
        title="Rear pillar intrusion",
        description="1500mm panel width minus 1420mm pillar width at mattress height, shared equally between sides.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    front_pillar_intrusion_mm: float = Field(
        default=40.0,
        gt=0,
        title="Front pillar intrusion",
        description="Estimated inward depth of the pillars behind the cab doors, following the wall curvature.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    ceiling_rear_y_mm: float = Field(
        default=240.0,
        ge=0,
        title="Rear edge position",
        description="Measured rear opening to plywood rear edge; using pillar datum provisionally.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Finished ceiling"]},
    )

    ceiling_length_mm: float = Field(
        default=1420.0,
        ge=0,
        title="Plywood length",
        description="Measured fore–aft length to the cab headliner.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Finished ceiling"]},
    )

    side_door_clear_width_mm: float = Field(
        default=680.0,
        ge=0,
        title="Open clear width",
        description="Measured front pillar to the edge of the open sliding door.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Sliding doors"]},
    )

    doors_close_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Doors closed (%)",
        description="Both doors slide forward, then pull inward during the final 15%. Zero is fully open.",
        json_schema_extra={"unit": "%", "group": ["Vehicle references", "Sliding doors"], "control": "position"},
    )

    side_door_standoff_mm: float = Field(
        default=60.0,
        ge=0,
        title="Open door standoff",
        description="170mm mattress-to-inner-door minus 110mm mattress-to-outer-pillar.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Sliding doors"]},
    )

    side_door_thickness_mm: float = Field(
        default=100.0,
        ge=0,
        title="Door envelope thickness",
        description="270mm to outer face minus 170mm to inner face; approximate overall envelope.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Sliding doors"]},
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
        title="Slide mounting band",
        description="Height of the lower drawer-slide mounting rails in the long bench and cross-bench end frames.",
        json_schema_extra={"unit": "mm", "group": ["Long bench"]},
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
        default=4.0,
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
        json_schema_extra={"unit": "mm", "group": ["Long bench"]},
    )

    slat_width_mm: float = Field(
        default=80.0,
        gt=0,
        title="Slat width",
        description="Reused stock width for both benches; cross-bench spacing adjusts to fit without narrowing slats.",
        json_schema_extra={"unit": "mm", "group": ["Long bench"]},
    )

    slat_side_gap_mm: float = Field(
        default=5.0,
        gt=0,
        title="Slat gap",
        description="Long-bench gap. Cross-bench gaps are distributed evenly to fit the available depth.",
        json_schema_extra={"unit": "mm", "group": ["Long bench"]},
    )

    ledge_width_mm: float = Field(
        default=18.0,
        gt=0,
        title="Ledge width",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame", "Guide ledges"]},
    )

    bed_extension_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Bed conversion (%)",
        description="0–40 extends both beds; 40–80 repositions cushions; 80–100 lowers the backrests into place.",
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
            "group": ["Long bench", "Sliding bed", "Sliding assembly", "Tie strip (extension stop)"],
        },
    )

    strip_end_clearance_mm: float = Field(
        default=2.0,
        ge=0,
        title="Strip end gap",
        json_schema_extra={
            "unit": "mm",
            "group": ["Long bench", "Sliding bed", "Sliding assembly", "Tie strip (extension stop)"],
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

    drawer_ply_mm: float = Field(
        default=12.0,
        gt=0,
        title="Plywood thickness",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Tray"]},
    )

    drawer_height_mm: float = Field(
        default=290.0,
        gt=0,
        title="Tray height",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Tray"]},
    )

    drawer_side_band_mm: float = Field(
        default=90.0,
        gt=0,
        title="Side lower band",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Tray"]},
    )

    drawer_floor_clearance_mm: float = Field(
        default=10.0,
        gt=0,
        title="Floor clearance",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Tray"]},
    )

    drawer_length_mm: float = Field(
        default=1200.0,
        gt=0,
        title="Closed rail length",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Rails"]},
    )

    drawer_rear_setback_mm: float = Field(
        default=50.0,
        ge=50,
        title="Rear allowance",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Rails"]},
    )

    slide_thickness_mm: float = Field(
        default=19.0,
        gt=0,
        title="Mounting gap",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Rails"]},
    )

    slide_height_mm: float = Field(
        default=53.0,
        gt=0,
        title="Rail height",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Rails"]},
    )

    slide_travel_mm: float = Field(
        default=1215.0,
        gt=0,
        title="Travel",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Rails"]},
    )

    drawer_extension_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Drawer extension (%)",
        json_schema_extra={"unit": "%", "group": ["Long bench", "Rear drawer"], "control": "position"},
    )

    cross_toilet_bay_depth_mm: float = Field(
        default=440.0,
        gt=0,
        title="Toilet bay depth",
        description="Clear width across the van. Onshape baseline: assumed 420 mm toilet plus 20 mm allowance.",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Fixed frame", "Toilet-storage divider"]},
    )

    cross_deck_thickness_mm: float = Field(
        default=12.0,
        gt=0,
        title="Deck thickness",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Fixed frame", "Fixed deck"]},
    )

    cross_bearer_height_mm: float = Field(
        default=18.0,
        gt=0,
        title="Bearer thickness",
        description="Plywood thickness of the fixed and moving support rails. Both use the shared member width.",
        json_schema_extra={"unit": "mm", "group": ["Cross bench"]},
    )

    cross_leg_clearance_mm: float = Field(
        default=2.0,
        gt=0,
        title="Leg nesting gap",
        description="Gap between the retracted legs/bearer and the shortened fixed supports and deck.",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Sliding assembly"]},
    )

    cross_stop_plate_length_mm: float = Field(
        default=100.0,
        gt=0,
        title="Plate length",
        description="Across the neighbouring slats; half is attached beneath the moving slat.",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Sliding assembly", "Extension stops"]},
    )

    cross_stop_plate_width_mm: float = Field(
        default=22.0,
        gt=0,
        title="Plate width",
        description="Along the direction of bed extension.",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Sliding assembly", "Extension stops"]},
    )

    cross_stop_plate_thickness_mm: float = Field(
        default=2.0,
        gt=0,
        title="Plate thickness",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Sliding assembly", "Extension stops"]},
    )

    cross_stop_recess_depth_mm: float = Field(
        default=4.0,
        gt=0,
        title="Recess depth",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Sliding assembly", "Extension stops"]},
    )

    cross_stop_clearance_mm: float = Field(
        default=0.5,
        gt=0,
        title="Running clearance",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Sliding assembly", "Extension stops"]},
    )

    cross_stop_head_allowance_mm: float = Field(
        default=1.0,
        ge=0,
        title="Screw-head allowance",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Sliding assembly", "Extension stops"]},
    )

    cross_storage_lid_gap_mm: float = Field(
        default=2.0,
        gt=0,
        title="Storage lid gap",
        description="Gap reserved between the fixed deck and the storage lid, centred over the divider frame.",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Storage lid"]},
    )

    cross_lid_finger_diameter_mm: float = Field(
        default=25.0,
        gt=0,
        title="Finger hole diameter",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Storage lid"]},
    )

    cross_lid_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Storage lid opening (%)",
        description="0 is closed; 100 opens the lid 70 degrees toward the cab.",
        json_schema_extra={"unit": "%", "group": ["Cross bench", "Storage lid"], "control": "position"},
    )

    foam_thickness_mm: float = Field(
        default=100.0,
        gt=0,
        title="Foam thickness (all)",
        description="Shared thickness of all six seat and backrest cushions.",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Cushions"]},
    )

    cab_backrest_length_mm: float = Field(
        default=750.0,
        gt=0,
        title="Cab backrest length",
        description="Rear backrest length is the remaining long-bench length. Both form the aisle-side bed infill.",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Cushions"]},
    )

    cabinet_ceiling_gap_mm: float = Field(
        default=3.0,
        ge=0,
        title="Ceiling gap",
        description="Cabinet height follows the finished ceiling. Zero reaches it; this gap leaves fitting clearance.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet"]},
    )

    cabinet_length_mm: float = Field(
        default=1000.0,
        gt=0,
        title="Length",
        description="Along the van from the furniture rear gap. Default ends at the sliding door's rear edge.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet"]},
    )

    cabinet_frame_step_height_mm: float = Field(
        default=750.0,
        gt=0,
        title="Upper shelf rail height",
        description="Top of the upper shelf rail and frame step. The lower shelf rail follows the bed support height.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet"]},
    )

    cabinet_shelf_thickness_mm: float = Field(
        default=12.0,
        gt=0,
        title="Shelf thickness",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Shelves"]},
    )

    cabinet_ledge_size_mm: float = Field(
        default=18.0,
        gt=0,
        title="Ledge width",
        description="Horizontal width of the timber supporting the shelves.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Shelf ledges"]},
    )

    cabinet_ledge_height_mm: float = Field(
        default=18.0,
        gt=0,
        title="Ledge height",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Shelf ledges"]},
    )

    @model_validator(mode="after")
    def check_geometry(self) -> Self:
        if self.arch_gap_mm >= self.cargo_width_mm:
            raise ValueError("Arch clear gap must be smaller than cargo width.")
        if self.arch_rear_offset_mm + self.arch_length_mm > self.cargo_length_mm:
            raise ValueError("Wheel arches must fit within the cargo length.")
        if self.arch_radius_mm >= self.arch_height_mm or 2 * self.arch_radius_mm >= self.arch_length_mm:
            raise ValueError("Arch top radius must be below its height and half its length.")
        if self.arch_crown_radius_mm >= min((self.cargo_width_mm - self.arch_gap_mm) / 4, self.arch_radius_mm):
            raise ValueError("Arch crown edge radius must be below half its depth and its top radius.")
        if 2 * self.rear_corner_radius_mm >= self.cargo_width_mm or self.rear_corner_radius_mm >= self.cargo_length_mm:
            raise ValueError("Rear corner radius must fit within the cargo outline.")
        if not 2 * self.rear_corner_radius_mm < self.body_upper_width_mm < self.cargo_width_mm:
            raise ValueError("Roof shoulder width must exceed twice the rear corner radius and be below body width.")
        if self.body_length_mm <= self.rear_corner_radius_mm:
            raise ValueError("Body length must extend beyond the rear corners.")
        if self.arch_rear_offset_mm + self.arch_length_mm > self.body_length_mm:
            raise ValueError("Wheel arches must fit within the body length.")
        if self.wall_taper_start_mm >= self.body_height_mm - self.roof_crown_mm * 1.35:
            raise ValueError("Wall taper must start below the roof shoulders and their control points.")
        if self.roof_bow_crown_mm >= self.roof_crown_mm:
            raise ValueError("Bow underside crown must be shallower than the bare roof crown.")
        if self.roof_bow_depth_mm <= self.roof_crown_mm - self.roof_bow_crown_mm:
            raise ValueError("Bow depth must leave material beneath the roof shoulders.")
        if self.roof_bow_depth_mm + self.ceiling_ply_thickness_mm >= (
            self.body_height_mm - self.roof_crown_mm - self.wall_taper_start_mm
        ):
            raise ValueError("Finished ceiling must remain above the wall taper start.")
        bow_positions = (self.roof_bow_rear_y_mm, self.roof_bow_middle_y_mm, self.roof_bow_front_y_mm)
        if any(
            not self.roof_bow_width_mm / 2 < y < self.body_length_mm - self.roof_bow_width_mm / 2 for y in bow_positions
        ):
            raise ValueError("Roof bows must fit within the cargo body length.")
        if any(b - a <= self.roof_bow_width_mm for a, b in zip(bow_positions, bow_positions[1:], strict=False)):
            raise ValueError("Roof bows must be ordered rear to front without overlap.")
        if self.side_opening_height_mm + self.side_opening_sill_mm >= self.body_height_mm - self.roof_crown_mm:
            raise ValueError("Sliding-door openings must end below the roof shoulders.")
        if 2 * self.side_opening_radius_mm >= min(self.side_opening_width_mm, self.side_opening_height_mm):
            raise ValueError("Sliding-door corner radius must be below half the aperture width and height.")
        for offset in (self.left_door_front_offset_mm, self.right_door_front_offset_mm):
            if self.body_length_mm - offset - self.side_opening_width_mm <= self.rear_corner_radius_mm:
                raise ValueError("Sliding-door openings must fit between the rear corners and the cab boundary.")
        if self.rear_opening_width_mm >= self.cargo_width_mm:
            raise ValueError("Rear opening must leave space for the rear pillars.")
        if not 2 * self.rear_opening_radius_mm < self.rear_opening_upper_width_mm <= self.rear_opening_width_mm:
            raise ValueError("Rear upper opening must fit its corners and be no wider than the lower opening.")
        if self.rear_opening_radius_mm >= self.rear_opening_height_mm * 0.3:
            raise ValueError("Rear top corners must fit above the tapered sides.")
        if self.rear_opening_height_mm >= self.body_height_mm:
            raise ValueError("Rear opening must leave space below the roof.")
        if self.long_bench_width_mm >= self.cargo_width_mm or self.seat_length_mm > self.cargo_length_mm:
            raise ValueError("Long bench must fit within the cargo outline.")
        if self.bed_width_mm >= self.cargo_width_mm:
            raise ValueError("Bed width must leave space within the cargo outline.")
        if self.member_width_mm < self.frame_thickness_mm:
            raise ValueError("Frame members must cover the plywood thickness at joints.")
        if self.platform_height_mm <= self.slat_thickness_mm + 2 * self.member_width_mm:
            raise ValueError("Platform height must leave room for the frame below the slats.")
        if not 0 < self.rear_corner_straight_mm < self.rear_corner_radius_mm:
            raise ValueError("Rear corner straight section must end before the side-panel junction.")
        if (
            not self.side_opening_sill_mm
            < self.side_opening_curve_start_mm
            < self.side_opening_curve_end_mm
            < self.side_opening_height_mm - self.side_opening_radius_mm
        ):
            raise ValueError("Sliding-door curve must fit between sill and upper corners.")
        if self.side_opening_upper_width_mm < self.side_opening_width_mm:
            raise ValueError("Sliding-door upper opening must be at least as wide as its lower opening.")
        if self.side_opening_upper_lean_mm > self.side_opening_upper_width_mm - self.side_opening_width_mm:
            raise ValueError("Upper pillar lean must fit within the opening's rearward transition.")
        if self.ceiling_rear_y_mm + self.ceiling_length_mm > self.body_length_mm:
            raise ValueError("Cargo plywood must end before the cab floor boundary.")
        if self.floor_ply_thickness_mm > self.floor_build_up_mm:
            raise ValueError("Floor plywood must fit within the total floor build-up.")
        return self


def default_parameters() -> Parameters:
    return Parameters()


def parameter_schema() -> dict[str, object]:
    return Parameters.model_json_schema()
