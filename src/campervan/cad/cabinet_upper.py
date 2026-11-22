"""Rear top-tier frame and provisional scribe datums from the registered interior scan."""

from build123d import Face, Location, Solid, Wire

from campervan.parameters import Parameters


def rear_upper_post_y(p: Parameters) -> float:
    """Keep the complete post forward of the rear beam's observed Y320 edge."""
    return 325.0 - p.cabinet_rear_y_mm


def rear_face_clearance(p: Parameters) -> Solid:
    """Space below a conservative roof outline across the aisle-face thickness.

    Registered corrected-7605be9e mesh, both CAD X370–410 and X1090–1130, Y100–340. These working
    jigsaw landmarks include about 5mm clearance; they are not surveyed dimensions.
    """
    roof = [(90, 1210), (110, 1210), (130, 1225), (150, 1230), (170, 1230),
            (190, 1230), (210, 1220), (230, 1215), (250, 1212), (270, 1213),
            (290, 1220), (310, 1252), (330, 1280), (350, 1280)]
    points = [(0, -200, -1), (0, 3000, -1), (0, 3000, 2000), (0, 351, 2000)]
    points.extend((0, y - p.cabinet_rear_y_mm, z) for y, z in reversed(roof))
    points.append((0, -200, 1210))
    return Solid.extrude(Face(Wire.make_polygon(points)), (p.cargo_width_mm + 10, 0, 0)).moved(
        Location((0, 0, -p.floor_surface_z_mm)))


def rear_panel_clearance(p: Parameters) -> Solid:
    """Rear panel's roof return through its full thickness, CAD Y90–120."""
    roof = [(150, 1040), (180, 1040), (200, 1082), (220, 1149), (240, 1173),
            (260, 1183), (280, 1196), (300, 1199), (320, 1202), (340, 1208),
            (360, 1207), (380, 1209), (400, 1208), (430, 1210)]
    # CAD X is reflected into the cabinet's native construction coordinates.
    points = [(0, -1, -1), (p.cargo_width_mm, -1, -1), (p.cargo_width_mm, -1, 1040)]
    points.extend((p.cargo_width_mm - x, -1, z) for x, z in roof)
    points.append((0, -1, 1210))
    return Solid.extrude(Face(Wire.make_polygon(points)), (0, p.cabinet_partition_thickness_mm + 2, 0)).moved(
        Location((0, 0, -p.floor_surface_z_mm)))
