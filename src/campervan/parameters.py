"""Editable vehicle and furniture dimensions in millimetres."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

RETIRED_PARAMETERS = frozenset(
    {
        "cross_toilet_bay_depth_mm",
        "cross_deck_thickness_mm",
        "cross_bearer_height_mm",
        "cross_leg_clearance_mm",
        "cross_stop_plate_length_mm",
        "cross_stop_plate_width_mm",
        "cross_stop_plate_thickness_mm",
        "cross_stop_recess_depth_mm",
        "cross_stop_clearance_mm",
        "cross_stop_head_allowance_mm",
        "cross_storage_lid_gap_mm",
        "cross_lid_finger_diameter_mm",
        "cross_lid_open_percent",
        "cross_bed_extension_percent",
        "cab_backrest_length_mm",
        "drawer_rear_setback_mm",
        "cabinet_table_height_mm",
        "cabinet_table_arm_swivel_deg",
        "cabinet_table_top_rotation_deg",
        "table_stowed_arm_deg",
        "cabinet_upper_doors_open_percent",
        "cabinet_storage_doors_open_percent",
    }
)


class Parameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, allow_inf_nan=False)

    table_mount: float = Field(
        default=0, ge=0, le=2, multiple_of=2, title="Show table",
        description="Switch instantly between the working table and the folded, disassembled storage preview.",
        json_schema_extra={"unit": "", "group": ["Laptop table"], "control": "position", "options": [
            {"value": 0, "label": "Bench mount"},
            {"value": 2, "label": "Stowed"},
        ]},
    )
    table_height_mm: float = Field(
        default=700, ge=620, le=780, title="Tabletop height (open)",
        description="Open surface above the wooden floor. Folding the leaf onto the top adds one panel thickness.",
        json_schema_extra={"unit": "mm", "group": ["Laptop table", "Bench mount"], "control": "position"},
    )
    table_arm_swivel_deg: float = Field(
        default=180, ge=0, le=360, title="Arm swivel",
        json_schema_extra={"unit": "°", "group": ["Laptop table", "Bench mount"], "control": "position"},
    )
    table_top_rotation_deg: float = Field(
        default=0, ge=0, le=360, title="Tabletop rotation",
        json_schema_extra={"unit": "°", "group": ["Laptop table", "Bench mount"], "control": "position"},
    )
    table_top_offset_percent: float = Field(
        default=0, ge=-100, le=100, title="Mount towards short edge",
        description="0 centres the mount. ±100 places the 240mm plate's end flush with either short tabletop edge. "
                    "The plate's 240mm axis runs along the tabletop length. This previews mounting positions.",
        json_schema_extra={"unit": "%", "group": ["Laptop table", "Bench mount"], "control": "position"},
    )
    table_fold_open_percent: float = Field(
        default=0, ge=0, le=100, title="Unfold tabletop",
        description="0: two leaves stacked, 250mm wide. 100: flat, 500mm wide. Uses a 180° fold-over hinge axis.",
        json_schema_extra={"unit": "%", "group": ["Laptop table", "Bench mount"], "control": "position"},
    )
    table_stowed_x_mm: float = Field(
        default=800, ge=-1000, le=2500, title="X position",
        description="Storage preview position across the van; final storage location remains undecided.",
        json_schema_extra={"unit": "mm", "group": ["Laptop table", "Stowed"], "control": "position"},
    )
    table_stowed_y_mm: float = Field(
        default=450, ge=-1000, le=2500, title="Y position",
        json_schema_extra={"unit": "mm", "group": ["Laptop table", "Stowed"], "control": "position"},
    )
    table_stowed_z_mm: float = Field(
        default=0, ge=0, le=1500, title="Bottom above floor",
        json_schema_extra={"unit": "mm", "group": ["Laptop table", "Stowed"], "control": "position"},
    )
    table_stowed_yaw_deg: float = Field(
        default=0, ge=0, le=360, title="Facing",
        json_schema_extra={"unit": "°", "group": ["Laptop table", "Stowed"], "control": "position"},
    )
    table_length_mm: float = Field(
        default=600, ge=240, title="Tabletop length",
        json_schema_extra={"unit": "mm", "group": ["Laptop table"]},
    )
    table_depth_mm: float = Field(
        default=250, ge=200, title="Folded width",
        description="Width of each leaf; the open tabletop is twice this width.",
        json_schema_extra={"unit": "mm", "group": ["Laptop table"]},
    )
    table_ply_thickness_mm: float = Field(
        default=25, gt=0, le=25, title="Bamboo thickness",
        json_schema_extra={"unit": "mm", "group": ["Laptop table"]},
    )
    table_corner_radius_mm: float = Field(
        default=20, ge=0, le=80, title="Corner radius",
        json_schema_extra={"unit": "mm", "group": ["Laptop table"]},
    )
    table_edge_radius_mm: float = Field(
        default=3, ge=0, le=10, title="Edge round-over",
        json_schema_extra={"unit": "mm", "group": ["Laptop table"]},
    )

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

    roof_rail_intrusion_mm: float = Field(
        default=20.0,
        gt=0,
        title="Side rail inward depth",
        description="Estimated depth from the curved inner wall, capped at the plywood ceiling edge; not measured.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Roof", "Side rails"]},
    )

    roof_skin_thickness_mm: float = Field(
        default=10.0,
        gt=0,
        title="Roof thickness",
        description="Vertical thickness above the existing inner roof profile.",
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
        json_schema_extra={"unit": "mm", "group": ["Finished floor plywood"]},
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

    rear_hatch_window_width_mm: float = Field(
        default=1000.0,
        gt=120,
        title="Window bottom width",
        description="Photo estimate of rear-door glass width; insulation obscures its inner boundary.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )
    rear_hatch_window_taper_mm: float = Field(
        default=60.0,
        ge=0,
        title="Window top narrowing",
        description="Photo estimate: total reduction in glass width at the top.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )
    rear_hatch_window_height_mm: float = Field(
        default=450.0,
        gt=120,
        title="Window height",
        description="Photo estimate of rear-door glass height.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )
    rear_hatch_window_top_gap_mm: float = Field(
        default=100.0,
        gt=0,
        title="Window top gap",
        description="Photo estimate below the top of the rear opening.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Rear opening"]},
    )
    rear_hatch_window_recess_mm: float = Field(
        default=30.0,
        gt=0,
        title="Window recess",
        description="Estimated outward recess from measured inner door surface; exterior is another 8mm outward.",
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

    front_pillar_width_mm: float = Field(
        default=100.0,
        gt=0,
        title="Front pillar fore–aft width",
        description="Extends toward the cab from the front edge of each sliding-door opening.",
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
        default=620.0,
        ge=0,
        title="Open clear width",
        description=(
            "Front pillar to the leading edge of the fully open door. Smaller values increase overlap. "
            "Default 620mm leaves a provisional 60mm overlap across the 680mm lower opening."
        ),
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
        gt=0,
        title="Door thickness",
        description="Owner-measured approximate transverse depth. Exterior walls align with closed door outer faces.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Sliding doors"]},
    )

    side_window_height_mm: float = Field(
        default=280.0,
        gt=110,
        title="Window height",
        description="Photo estimate for the wide, shallow glass opening; not owner-measured.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Sliding doors"]},
    )

    side_window_top_gap_mm: float = Field(
        default=80.0,
        gt=0,
        title="Window top gap",
        description="Estimated distance below the opening header to the glass edge.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Sliding doors"]},
    )

    side_window_surround_mm: float = Field(
        default=30.0,
        gt=0,
        title="Window surround width",
        description="Photo estimate for the metal slope from the inner door panel toward the glass.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Sliding doors"]},
    )

    rear_side_window_width_mm: float = Field(
        default=600.0,
        gt=110,
        title="Rear window width",
        description="Photo estimate for the fixed rear side windows, centred between the pillars.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    rear_side_window_height_mm: float = Field(
        default=300.0,
        gt=110,
        title="Rear window height",
        description="Photo estimate: slightly taller than the 280mm sliding-door glass.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    rear_side_window_top_gap_mm: float = Field(
        default=60.0,
        gt=0,
        title="Rear window top gap",
        description="Photo estimate: top edge 20mm above the sliding-door glass, with approximately aligned bottoms.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
    )

    rear_side_window_recess_mm: float = Field(
        default=30.0,
        ge=0,
        title="Rear window recess",
        description="Estimated outward depth from the measured inner side wall to glass, within the body thickness.",
        json_schema_extra={"unit": "mm", "group": ["Vehicle references", "Side walls"]},
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

    long_bench_inset_mm: float = Field(
        default=4.0,
        gt=0,
        title="Construction inset",
        description="Retained wall-side and cab-end layout allowance, independent of cross-bench skin thickness.",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Fixed frame"]},
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
        description="Reused stock width for both benches; four full-width slats span the fixed cross bench.",
        json_schema_extra={"unit": "mm", "group": ["Long bench"]},
    )

    slat_side_gap_mm: float = Field(
        default=5.0,
        gt=0,
        title="Slat gap",
        description=(
            "Running gap between interleaving long-bench slats. Cross-bench gaps follow its four slats and depth."
        ),
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
        title="Long bench conversion (%)",
        description="0–40 extends the long bed; 40–80 repositions its cushions; 80–100 lowers its backrests.",
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
        title="Closed drawer slider length",
        description="Also sets the drawer side length; the two end panels cap the sides.",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Drawer sliders"]},
    )

    slide_thickness_mm: float = Field(
        default=19.0,
        gt=0,
        title="Mounting gap",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Drawer sliders"]},
    )

    slide_height_mm: float = Field(
        default=53.0,
        gt=0,
        title="Drawer slider height",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Drawer sliders"]},
    )

    slide_travel_mm: float = Field(
        default=1215.0,
        gt=0,
        title="Travel",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Rear drawer", "Drawer sliders"]},
    )

    drawer_extension_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Drawer extension (%)",
        json_schema_extra={"unit": "%", "group": ["Long bench", "Rear drawer"], "control": "position"},
    )

    cross_bench_skin_thickness_mm: float = Field(
        default=9.0,
        gt=0,
        title="Rear skin thickness",
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Rear skin"]},
    )

    cross_bench_overhang_mm: float = Field(
        default=200.0,
        ge=0,
        title="Aisle slat overhang / foot recess",
        description=(
            "Overhang at the aisle end. The wall-side cross-bench frame aligns with the internal drawer support."
        ),
        json_schema_extra={"unit": "mm", "group": ["Cross bench", "Fixed frame"]},
    )

    foam_thickness_mm: float = Field(
        default=100.0,
        gt=0,
        title="Foam thickness (all)",
        description="Shared thickness of all five seat and backrest cushions.",
        json_schema_extra={"unit": "mm", "group": ["Long bench", "Cushions"]},
    )

    cabinet_frame_thickness_mm: float = Field(
        default=12.0,
        gt=0,
        title="Structure plywood thickness",
        description="Cabinet partitions, aisle frame, rear rails and upright share 12mm plywood.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Frames"]},
    )

    cabinet_door_thickness_mm: float = Field(
        default=9.0,
        gt=0,
        title="Door plywood thickness",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Doors"]},
    )
    cabinet_door_gap_mm: float = Field(
        default=2.0,
        gt=0,
        title="Closing gap",
        description="Between each closed door and the aisle frame; the carcass moves wallward to retain bed clearance.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Doors"]},
    )
    cabinet_door_overlap_mm: float = Field(
        default=15.0,
        gt=0,
        title="Opening overlap",
        description="Overlap beyond each individual opening; each shelf compartment has its own door.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Doors"]},
    )
    cabinet_door_corner_radius_mm: float = Field(
        default=12.0,
        gt=0,
        title="Door corner radius",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Doors"]},
    )
    cabinet_door_edge_radius_mm: float = Field(
        default=2.0,
        gt=0,
        title="Door edge roundover",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Doors"]},
    )
    cabinet_rear_upper_1_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Rear bay lower flap",
        description="Lower the first rear upper-shelf flap to horizontal, held by paired chains.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Upper flaps"], "control": "position"},
    )
    cabinet_rear_upper_2_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Rear bay top flap",
        description="Lower the top rear-shelf flap to horizontal, held by paired chains.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Upper flaps"], "control": "position"},
    )
    cabinet_cab_end_upper_1_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Cab-end bay lower flap",
        description="Lower the first cab-end upper-shelf flap to horizontal, held by paired chains.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Upper flaps"], "control": "position"},
    )
    cabinet_cab_end_upper_2_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Cab-end bay top flap",
        description="Lower the top cab-end-shelf flap to horizontal, held by paired chains.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Upper flaps"], "control": "position"},
    )
    cabinet_lower_doors_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Cab-end bottom door",
        description="Open the bottom front compartment independently of the door above the mattress.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Lower compartments"], "control": "position"},
    )
    cabinet_storage_aft_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Aft door",
        description="Swing the rearward bottom-storage door outward on its own hinge.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Bottom storage"], "control": "position"},
    )
    cabinet_storage_fore_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Fore door",
        description="Swing the forward bottom-storage door outward on its own hinge.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Bottom storage"], "control": "position"},
    )
    cabinet_front_upper_door_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Cab-end above-bed flap",
        description="Open the raised front compartment while the bed is made up, independently of the bottom door.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Lower compartments"], "control": "position"},
    )
    cabinet_storage_upper_doors_open_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        title="Rear above-bed flap",
        description="Lower the full-width rear storage flap above the mattress.",
        json_schema_extra={"unit": "%", "group": ["Cabinet", "Doors", "Lower compartments"], "control": "position"},
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
        description=(
            "Along the van from the furniture rear gap. "
            "Original 1000mm cabinet length puts its cab-end panel 1100mm from the rear pillar datum."
        ),
        json_schema_extra={"unit": "mm", "group": ["Cabinet"]},
    )

    cabinet_frame_step_height_mm: float = Field(
        default=750.0,
        gt=0,
        title="Upper shelf reference height",
        description="The upper shelf rail is halfway from this reference level to the cabinet top.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet"]},
    )

    cabinet_rear_bay_length_mm: float = Field(
        default=560.0,
        gt=0,
        title="Rear storage bay length",
        description="Rear end to centre divider. The forward bay uses the remainder of the cabinet length.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet"]},
    )

    cabinet_rear_storage_height_mm: float = Field(
        default=730.0,
        gt=0,
        title="Rear storage clear height",
        description="Floor to the lowest shelf supports in the rear bay; the rear entrance is open.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet"]},
    )

    cabinet_shelf_thickness_mm: float = Field(
        default=12.0,
        gt=0,
        title="Shelf thickness",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Shelves"]},
    )

    cabinet_mattress_clearance_mm: float = Field(
        default=10.0,
        ge=0,
        title="Lower shelf above mattress",
        description="Lower front shelf top above the uncompressed mattress. The storage-door split follows it.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Shelves"]},
    )

    @property
    def cabinet_lower_rail_top_mm(self) -> float:
        return (
            self.platform_height_mm
            + self.foam_thickness_mm
            + self.cabinet_mattress_clearance_mm
            + self.member_width_mm
            - self.cabinet_ledge_height_mm
            - self.cabinet_shelf_thickness_mm
        )

    cabinet_back_thickness_mm: float = Field(
        default=3.0,
        gt=0,
        title="Thickness",
        description="Selected flute-board stock thickness, measured normal to the curved backing.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Back lining"]},
    )

    cabinet_back_clearance_mm: float = Field(
        default=1.0,
        gt=0,
        title="Vehicle clearance",
        description="Gap to the projecting wall/pillar contour and rear corner. The top meets the plywood ceiling.",
        json_schema_extra={"unit": "mm", "group": ["Cabinet", "Back lining"]},
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

    solar_bag_width_mm: float = Field(
        default=830.0,
        gt=0,
        title="Folded width",
        description="Owner-measured overall bag width.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Solar panel bag"]},
    )
    solar_bag_height_mm: float = Field(
        default=760.0,
        gt=0,
        title="Folded height",
        description="Owner-measured overall bag height.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Solar panel bag"]},
    )
    solar_bag_depth_mm: float = Field(
        default=80.0,
        gt=0,
        title="Folded thickness",
        description="Approximate owner-measured packed thickness.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Solar panel bag"]},
    )
    solar_bag_x_mm: float = Field(
        default=750.0,
        ge=-1000,
        le=2500,
        title="Centre X",
        description="Footprint centre across the van, from the left inner wall.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Solar panel bag"]},
    )
    solar_bag_y_mm: float = Field(
        default=45.0,
        ge=-1000,
        le=3000,
        title="Centre Y",
        description="Footprint centre forward of the rear opening at its side pillars.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Solar panel bag"]},
    )
    solar_bag_z_mm: float = Field(
        default=0.0,
        ge=0,
        le=1300,
        title="Bottom above floor",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Solar panel bag"]},
    )
    solar_bag_yaw_deg: float = Field(
        default=0.0,
        ge=-180,
        le=180,
        title="Rotation",
        description="0 faces the rear door; 90 turns the wide face along the van.",
        json_schema_extra={"control": "position", "unit": "°", "group": ["Stored gear", "Solar panel bag"]},
    )
    chilly_bin_width_mm: float = Field(
        default=470.0, gt=0, title="Width",
        description="Owner-measured closed bin width, excluding the carry handle.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Chilly bin"]},
    )
    chilly_bin_depth_mm: float = Field(
        default=280.0, gt=0, title="Depth",
        description="Owner-measured closed bin depth, excluding the carry handle.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Chilly bin"]},
    )
    chilly_bin_height_mm: float = Field(
        default=410.0, gt=0, title="Height",
        description="Owner-measured height including the closed lid, excluding the carry handle.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Chilly bin"]},
    )
    chilly_bin_x_mm: float = Field(
        default=750.0, ge=-1000, le=2500, title="Centre X",
        description="Footprint centre across the van, from the left inner wall.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chilly bin"]},
    )
    chilly_bin_y_mm: float = Field(
        default=1050.0, ge=-1000, le=3000, title="Centre Y",
        description="Footprint centre forward of the rear opening; initial aisle placement.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chilly bin"]},
    )
    chilly_bin_z_mm: float = Field(
        default=0.0, ge=0, le=1300, title="Bottom above floor",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chilly bin"]},
    )
    chilly_bin_yaw_deg: float = Field(
        default=90.0, ge=-180, le=180, title="Rotation",
        description="0 faces the wide red side toward the rear; 90 turns it along the van.",
        json_schema_extra={"control": "position", "unit": "°", "group": ["Stored gear", "Chilly bin"]},
    )
    chilly_bin_handle_angle_deg: float = Field(
        default=0.0, ge=0, le=135, title="Handle folded",
        description="0 is upright; 135 folds forward beside the bin. Handle dimensions and travel are photo estimates.",
        json_schema_extra={"control": "position", "unit": "°", "group": ["Stored gear", "Chilly bin", "Handle"]},
    )
    chair_width_mm: float = Field(
        default=600.0,
        gt=0,
        title="Folded width",
        description="Overall width including armrests and hinge fittings.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Chairs"]},
    )
    chair_height_mm: float = Field(
        default=700.0,
        gt=0,
        title="Folded height",
        description="Owner-measured overall folded height.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Chairs"]},
    )
    chair_depth_mm: float = Field(
        default=100.0,
        gt=0,
        title="Folded thickness",
        description="Approximate overall depth of each folded chair.",
        json_schema_extra={"unit": "mm", "group": ["Stored gear", "Chairs"]},
    )
    chair_1_x_mm: float = Field(
        default=520.0,
        ge=-1000,
        le=2500,
        title="Centre X",
        description="Footprint centre across the van; provisional aisle placement.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chairs", "Chair 1"]},
    )
    chair_1_y_mm: float = Field(
        default=600.0,
        ge=-1000,
        le=3000,
        title="Centre Y",
        description="Footprint centre forward of the rear opening at its side pillars.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chairs", "Chair 1"]},
    )
    chair_1_z_mm: float = Field(
        default=0.0,
        ge=0,
        le=1300,
        title="Bottom above floor",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chairs", "Chair 1"]},
    )
    chair_1_yaw_deg: float = Field(
        default=90.0,
        ge=-180,
        le=180,
        title="Rotation",
        description="90 stores the chair edge-on, with its wide face along the van.",
        json_schema_extra={"control": "position", "unit": "°", "group": ["Stored gear", "Chairs", "Chair 1"]},
    )
    chair_2_x_mm: float = Field(
        default=640.0,
        ge=-1000,
        le=2500,
        title="Centre X",
        description="Footprint centre across the van; provisional aisle placement.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chairs", "Chair 2"]},
    )
    chair_2_y_mm: float = Field(
        default=600.0,
        ge=-1000,
        le=3000,
        title="Centre Y",
        description="Footprint centre forward of the rear opening at its side pillars.",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chairs", "Chair 2"]},
    )
    chair_2_z_mm: float = Field(
        default=0.0,
        ge=0,
        le=1300,
        title="Bottom above floor",
        json_schema_extra={"control": "position", "unit": "mm", "group": ["Stored gear", "Chairs", "Chair 2"]},
    )
    chair_2_yaw_deg: float = Field(
        default=90.0,
        ge=-180,
        le=180,
        title="Rotation",
        description="90 stores the chair edge-on, with its wide face along the van.",
        json_schema_extra={"control": "position", "unit": "°", "group": ["Stored gear", "Chairs", "Chair 2"]},
    )

    @property
    def drawer_support_x_mm(self) -> float:
        """Shared wall-side face of the drawer support and cross-bench leg frame."""
        return (self.cargo_width_mm - self.arch_gap_mm) / 2 + self.drawer_arch_clearance_mm

    @model_validator(mode="before")
    @classmethod
    def migrate_saved_parameters(cls, data: object) -> object:
        """Preserve construction datums while retiring superseded controls."""
        if isinstance(data, dict):
            data = data.copy()
            for legacy, fields in (
                (
                    "cabinet_upper_doors_open_percent",
                    (
                        "cabinet_rear_upper_1_open_percent",
                        "cabinet_rear_upper_2_open_percent",
                        "cabinet_cab_end_upper_1_open_percent",
                        "cabinet_cab_end_upper_2_open_percent",
                    ),
                ),
                (
                    "cabinet_storage_doors_open_percent",
                    ("cabinet_storage_aft_open_percent", "cabinet_storage_fore_open_percent"),
                ),
            ):
                if legacy in data:
                    for field in fields:
                        data.setdefault(field, data[legacy])
            data = {name: value for name, value in data.items() if name not in RETIRED_PARAMETERS}
            if data.get("table_mount") == 1:
                data["table_mount"] = 0  # The cabinet mounting option has been removed.
            # The removed cab-end skin also supplied these long-bench layout offsets.
            # Preserve the slats, guides and frame positions when reading older projects.
            if "wall_thickness_mm" in data:
                data.setdefault("long_bench_inset_mm", data.pop("wall_thickness_mm"))
            return data
        return data

    @model_validator(mode="after")
    def check_geometry(self) -> Self:
        if (
            self.bed_width_mm - self.cross_bench_overhang_mm - self.drawer_support_x_mm <= 2 * self.frame_thickness_mm
            or self.cargo_length_mm - self.seat_length_mm - self.cross_bench_skin_thickness_mm
            <= 2 * self.member_width_mm + 2 * self.inside_radius_mm
        ):
            raise ValueError("Cross-bench overhang must leave room for two support frames and their rounded openings.")
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
