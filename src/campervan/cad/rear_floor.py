"""Flat rear-floor boundary: rear door and fixed rear pillar-base footprints.

The detailed down-looking photograph supplies the long straight housing face and
short rounded shoulder contours. Its 80mm tag calibrates the along-edge lengths;
registered scan sections supply main-panel Y and housing-front Y. Local quadratic
shoulders follow selected silver-edge pixels and meet the observed straight front
tangentially. They do not smooth or bow either main door run.

Evidence: .local/experiments/rear-door-edge/photo-contour/local-shoulder-fit.json.
The rear-door contour is retained. The lower boundary keeps the brace's separate
leading edge and return, then the rear pillar, diagonal pillar and straight wall.
The flat flange seam and the rejected continuous blend are excluded.
Pillar evidence: .local/experiments/rear-floor-user-trace/identified-face-lines.json.
"""

from build123d import Color, Compound, Edge, Face, Location, Solid, Wire

from campervan.parameters import Parameters

REAR_FLOOR_FRONT_Y = 250.0
# Registered CAD millimetres. Main panel and local housing are separate features.
MAIN_DOOR_Y = -33.849214
LOCK_FRONT_Y = -21.829018
# Photo-defined feature lengths; the previous mesh fit erased the long straight front.
LOCK_FRONT_HALF_WIDTH = 98.654602
LOCK_SHOULDER_HALF_WIDTH = 182.629897
# Fitted to the selected local photo contour, with its tangent along the straight front.
LOCK_SHOULDER_CONTROL_X = 130.236056
REVIEW_HALF_WIDTH = 450.0


def _pillar_base_edges(p: Parameters, right: bool = False) -> list[Edge]:
    """Separate lower-face boundaries: brace leading edge/return, pillar, sidewall.

    The brace has an offset leading edge and a return into the rear pillar face.
    That rear face, the diagonal face and the longitudinal wall are distinct
    straight runs. A single height-slice or tangent blend would erase the jog.
    Lines are measured independently in the unmarked photo and mesh; their
    intersections establish the corners. The user's sketch checks the feature
    arrangement rather than supplying copied CAD vertices.

    Evidence: .local/experiments/rear-floor-user-trace/unmarked-feature-positions.json
    and identified-face-lines.json. Small unmeasured corner radii are not invented.
    """
    def point(x: float, y: float) -> tuple[float, float, float]:
        return (p.cargo_width_mm - x if right else x, y, 0)

    brace_x, rear_x, side_x = 189.0, 146.0, 41.0
    # Independent straight-line fits to the return and diagonal lower-face boundaries.
    return_slope, return_intercept = -0.3300819563, 58.00323347
    diagonal_slope, diagonal_intercept = -1.4045771038, 236.31130805
    points = [
        (p.cargo_width_mm / 2 - REVIEW_HALF_WIDTH, MAIN_DOOR_Y),
        (brace_x, MAIN_DOOR_Y),
        (brace_x, return_slope * brace_x + return_intercept),
        (rear_x, return_slope * rear_x + return_intercept),
        (rear_x, (rear_x - diagonal_intercept) / diagonal_slope),
        (side_x, (side_x - diagonal_intercept) / diagonal_slope),
        (side_x, REAR_FLOOR_FRONT_Y),
    ]
    return [Edge.make_line(point(*a), point(*b)) for a, b in zip(points, points[1:])]


def rear_floor_sections(p: Parameters) -> Compound:
    """Rear-door and pillar-base outline with a flat, closed 1mm solid floor section."""
    centre = p.cargo_width_mm / 2
    left = centre - REVIEW_HALF_WIDTH
    right = centre + REVIEW_HALF_WIDTH
    outer_left = (centre - LOCK_SHOULDER_HALF_WIDTH, MAIN_DOOR_Y, 0)
    inner_left = (centre - LOCK_FRONT_HALF_WIDTH, LOCK_FRONT_Y, 0)
    inner_right = (centre + LOCK_FRONT_HALF_WIDTH, LOCK_FRONT_Y, 0)
    outer_right = (centre + LOCK_SHOULDER_HALF_WIDTH, MAIN_DOOR_Y, 0)
    rear_edges = [
        Edge.make_line((left, MAIN_DOOR_Y, 0), outer_left),
        Edge.make_bezier(outer_left, (centre - LOCK_SHOULDER_CONTROL_X, LOCK_FRONT_Y, 0), inner_left),
        Edge.make_line(inner_left, inner_right),
        Edge.make_bezier(inner_right, (centre + LOCK_SHOULDER_CONTROL_X, LOCK_FRONT_Y, 0), outer_right),
        Edge.make_line(outer_right, (right, MAIN_DOOR_Y, 0)),
    ]
    rear = Wire(rear_edges)
    left_pillar = _pillar_base_edges(p)
    right_pillar = _pillar_base_edges(p, right=True)
    # The forward line closes this increment at the existing baseline's clipping plane.
    # It is not a proposed front boundary of the van floor.
    outline = Wire([
        *rear_edges,
        *right_pillar,
        Edge.make_line((p.cargo_width_mm - 41, REAR_FLOOR_FRONT_Y, 0), (41, REAR_FLOOR_FRONT_Y, 0)),
        *(edge.reversed() for edge in reversed(left_pillar)),
    ])
    placement = Location((0, 0, -p.floor_build_up_mm))
    strip = Solid.extrude(Face(outline), (0, 0, -1)).moved(placement)
    strip.label, strip.color = "Rear floor review section", Color(0.55, 0.62, 0.66)
    edge = rear.moved(placement)
    edge.label, edge.color = "Rear edge", Color(0.15, 0.9, 1)
    pillar_left = Wire(left_pillar).moved(placement)
    pillar_right = Wire(right_pillar).moved(placement)
    pillar_left.label, pillar_left.color = "Left rear pillar base", Color(0.15, 0.9, 1)
    pillar_right.label, pillar_right.color = "Right rear pillar base", Color(0.15, 0.9, 1)
    return Compound(label="Rear floor", children=[strip, edge, pillar_left, pillar_right])
