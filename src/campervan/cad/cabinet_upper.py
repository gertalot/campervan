"""Rear top-tier frame and provisional scribe datums from the registered interior scan."""

from build123d import Edge, Face, Solid, Wire

from campervan.parameters import Parameters


BOX8_POST_TOP_WORLD_Z_MM = 1201.0
REAR_END_SKIN_WALL_X_MM = 1371.5


def _roof_edge(p: Parameters, stations: list[tuple[float, float]], start_slope: float) -> Edge:
    """Smooth a jigsaw line through registered Y/Z stations in cabinet coordinates."""
    points = [(0, y - p.cabinet_rear_y_mm, z - p.floor_surface_z_mm) for y, z in stations]
    return Edge.make_spline(points, parameters=[y for y, _ in stations],
                            tangents=[(0, 1, start_slope), (0, 1, 0)], scale=False)


def _scribe_waste(p: Parameters, stations: list[tuple[float, float]], start_slope: float,
                  end_y: float | None = None) -> Solid:
    curve = _roof_edge(p, stations, start_slope)
    first, last = curve.start_point(), curve.end_point()
    corners = [tuple(last)]
    if end_y is not None:  # Level across the thickness of the return.
        corners.append((0, end_y - p.cabinet_rear_y_mm, last.Z))
    corners.extend([(0, corners[-1][1], p.body_height_mm), (0, first.Y, p.body_height_mm), tuple(first)])
    wire = Wire([curve, *(Edge.make_line(a, b) for a, b in zip(corners, corners[1:]))])
    return Solid.extrude(Face(wire), (p.cargo_width_mm, 0, 0))


def cab_pillar_backing_waste(p: Parameters) -> Solid:
    """Cut the box 4 backing around the cab-side pillar at the X1448 outer face."""
    stations = [(909, 1082), (916, 1017), (925, 927), (934, 865), (941, 850), (953, 836),
                (964, 833), (978, 837), (988, 851), (1000, 891), (1009, 921), (1017, 927),
                (1023, 957), (1030, 1017), (1037, 1060), (1045, 1088)]
    return _scribe_waste(p, stations, -8)


def rear_backing_roof_waste(p: Parameters, rear_wall: float, upper_wall: float,
                            step_y: float) -> tuple[Solid, Solid, Solid, Solid]:
    """Jigsaw contours from sections through the installed sheets, in registered vehicle Y/Z."""
    rear_z, upper_z = 1173, 1154  # Heights on opposite sides of the short transverse return.
    step = p.cabinet_rear_y_mm + step_y
    skin = p.cabinet_partition_thickness_mm

    shallow = _scribe_waste(
        p, [(80, 1099), (92, 1094), (108, 1087), (122, 1080), (134, 1078),
            (148, 1092), (162, 1116), (179, 1140), (192, 1149), (216, 1162), (step - skin, rear_z)],
        -0.5, step,
    )
    upper = _scribe_waste(
        p, [(step, upper_z), (260, 1176), (286, 1194), (301, 1208),
            (314, 1226), (331, 1224), (349, 1234), (359, 1243), (370, 1258)],
        1,
    )

    def bevel(inner: float, y: float, depth: float, wall_z: float) -> Solid:
        z0, z1 = rear_z - p.floor_surface_z_mm, wall_z - p.floor_surface_z_mm
        outline = [(inner, y, z0), (upper_wall, y, z1), (p.cargo_width_mm, y, z1),
                   (p.cargo_width_mm, y, p.body_height_mm), (inner, y, p.body_height_mm)]
        return Solid.extrude(Face(Wire.make_polygon(outline)), (0, depth, 0))

    pillar_return = bevel(rear_wall + skin, step_y - skin, skin, upper_z)
    # One straight cut meets the skin height at the high end and clears the right-hand roof on insertion.
    upright = bevel(upper_wall - p.cabinet_frame_width_mm, step_y, p.cabinet_frame_thickness_mm, upper_z - 2)
    return shallow, pillar_return, upper, upright


def rear_upper_post_y(p: Parameters) -> float:
    """Keep the complete post forward of the rear beam's observed Y320 edge."""
    return 325.0 - p.cabinet_rear_y_mm


def rear_face_clearance(p: Parameters) -> Solid:
    """Box 8 aisle front, fitted to both sides of the scan over the 329mm slide from the aisle."""
    curve = _roof_edge(p, [(120, BOX8_POST_TOP_WORLD_Z_MM), (127, 1217), (136, 1226), (149, 1226),
                           (168, 1223), (204, 1222), (225, 1221), (246, 1219), (256, 1218),
                           (271, 1220), (283, 1222), (293, 1229), (303, 1239), (310, 1249),
                           (315, 1258)], 2.5)
    first, last = curve.start_point(), curve.end_point()
    # Continue level over both posts so the front can overlap their rebates.
    end = last.Y + p.cabinet_frame_width_mm
    corners = [last, (0, end, last.Z), (0, end, 0), (0, 0, 0), (0, 0, first.Z), first]
    wire = Wire([curve, *(Edge.make_line(a, b) for a, b in zip(corners, corners[1:]))])
    return Solid.extrude(Face(wire), (p.cargo_width_mm, 0, 0))


def end_skin_waste(p: Parameters, rear: float, cab: float) -> tuple[Solid, Solid]:
    """Registered end outlines in construction X / world Z. The upper sections clear both slide-in paths."""
    def waste(y: float, stations: list[tuple[float, float]]) -> Solid:
        rim = [(x, y, z - p.floor_surface_z_mm) for x, z in stations]
        outline = [(0, y, rim[0][2]), *rim, (p.cargo_width_mm, y, rim[-1][2]),
                   (p.cargo_width_mm, y, p.body_height_mm), (0, y, p.body_height_mm)]
        return Solid.extrude(Face(Wire.make_polygon(outline)), (0, p.cabinet_partition_thickness_mm, 0))

    return (
        waste(rear, [(1134, 1201), (1178, 1201), (1190, 1196), (1216, 1191.5), (1230, 1190),
                     (1258, 1180), (1268, 1164), (1280, 1153), (1287, 1149), (1306, 1122),
                     (1313, 1103), (1318, 1089), (1323, 1067), (1323.5, 1058), (1331, 1020),
                     (1334, 1007), (1339.5, 960), (1347, 911), (1353.5, 850), (1357.5, 828),
                     (1357.5, 803), (REAR_END_SKIN_WALL_X_MM, 780)]),
        # Both cab-facing sheets use this same cut, from the roof to the finished floor.
        waste(cab, [(1329, 1258), (1340, 1237), (1346, 1235), (1355, 1196), (1359, 1189),
                    (1368, 1179), (1378, 1169), (1388.5, 1160), (1413, 1150), (1419, 1140),
                    (1437, 1125), (1438, 1106), (1448.5, 1076), (1458, 1051), (1471, 1007),
                    (1486, 948), (1486.5, 942), (1492, 916), (1492, 855), (1489.5, 823),
                    (1485, 780), (1481, 767), (1464, 750), (1458, 739), (1458, 690),
                    (1449.5, 559), (1454.5, 540), (1454.5, 493), (1449, 435), (1449, 408),
                    (1451.5, 390), (1456.5, 380), (1457, 349), (1458, 320), (1458, 144),
                    (1442, 122), (1438.5, 110), (1419, 10)]),
    )
