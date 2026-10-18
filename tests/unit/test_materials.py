"""Stock dimensions have one owner; custom measurements survive saving."""

import pytest

from campervan.materials import Project, Selection, load_project, resolve, save_project
from campervan.parameters import Parameters


def test_stock_dimensions_and_measured_override(tmp_path):
    original = Parameters()
    path = tmp_path / "project.json"
    # An existing project with unsourced 19mm ledges adopts the sourced thickness on load.
    save_project(
        Project(
            parameters=Parameters(cabinet_ledge_size_mm=19, cabinet_ledge_height_mm=19),
            materials={"slats": Selection(owned=True)},
        ),
        path,
    )
    sourced = load_project(path)
    assert sourced.materials["skins"].product_id == "tigerply-okoume-4"
    assert sourced.parameters.wall_thickness_mm == 4
    assert sourced.materials["ledges"].product_id == "tigerply-18"
    assert sourced.parameters.cabinet_ledge_size_mm == 19  # Strip width is a cut dimension.
    assert sourced.parameters.cabinet_ledge_height_mm == 18
    assert sourced.parameters.ledge_width_mm == 18
    assert all(sourced.materials[role].product_id == "tigerply-18" for role in ("frames", "bearers", "guides"))
    choices = {
        "skins": Selection(product_id="tigerply-okoume-4", measured={"thickness": 3.8}),
        "ledges": Selection(product_id="tigerply-18"),
        "slats": Selection(owned=True),
    }
    resolved = resolve(original, choices)
    assert resolved.wall_thickness_mm == 3.8
    assert resolved.cabinet_ledge_size_mm == resolved.cabinet_ledge_height_mm == 18
    assert resolved.platform_height_mm == original.platform_height_mm
    assert resolved.long_bench_width_mm == original.long_bench_width_mm
    save_project(Project(parameters=resolved, materials=choices), path)
    assert load_project(path).parameters == resolved
    with pytest.raises(ValueError):
        resolve(original, {"skins": Selection(product_id="carinya-50-40")})


def test_cut_envelopes_ignore_parent_motion_and_keep_timber_section():
    from build123d import Box, Compound, Location

    from campervan.cad.bom import cut_list

    ledge = Box(400, 18, 17)
    ledge.label = "Rear ledge"
    group = Compound(label="Shelf ledges", children=[ledge])
    model = Compound(label="Campervan", children=[Compound(label="Cabinet", children=[group])])
    parameters = Parameters(cabinet_ledge_size_mm=18, cabinet_ledge_height_mm=17)
    before = cut_list(model, parameters)
    group.location = Location((100, 200, 300), (70, 0, 0))
    assert cut_list(model, parameters) == before
    assert (before[0].length, before[0].width, before[0].thickness) == (400, 18, 17)


def test_drawer_slide_stages_are_one_purchased_pair():
    from build123d import Box, Compound

    from campervan.cad.bom import cut_list

    stages = []
    for stage in ("Fixed", "Intermediate", "Moving"):
        rails = []
        for side in ("Left", "Right"):
            rail = Box(1200, 53, 19 / 3)
            rail.label = f"{side} rail"
            rails.append(rail)
        stages.append(Compound(label=stage, children=rails))
    drawer = Compound(label="Rear drawer", children=[Compound(label="Rails", children=stages)])
    cuts = cut_list(Compound(label="Campervan", children=[drawer]), Parameters())
    assert len(cuts) == 2
    assert all(c.material == "slides" and c.thickness == 19 for c in cuts)
