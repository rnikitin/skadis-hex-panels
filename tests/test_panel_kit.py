"""The full panel must have no abandoned key geometry and accept the chosen mounts."""

import numpy as np
from skadis_hex import panel, geometry as g, alignment, wall_mount


def test_panel_restores_rim_and_removes_receiver_pads():
    shape = panel.make_panel()
    assert shape.isValid() and len(shape.Solids()) == 1
    filled = g.cylinder(0.4, 9.5, 2, 30, 98.2)
    absent = g.cylinder(0.3, 9.5, 2, 34.7, 89.2)
    assert abs(shape.intersect(filled).Volume() - filled.Volume()) < 1e-7
    assert shape.intersect(absent).Volume() < 1e-7
    for normal in ((1, 0, 0), (0, 1, 0)):
        assert shape.cut(shape.mirror(normal)).Volume() < 1e-5


def test_selected_shoes_and_screw_tips_clear_the_panel():
    shape = panel.make_panel()
    for x, y in g.MOUNTS:
        shoe = wall_mount.make_self_tapping_wall_shoe(2.2)
        if y < 0:
            shoe = shoe.rotate((0, 0, 0), (0, 0, 1), 180)
        shoe = shoe.translate((x, y, 0))
        assert shape.intersect(shoe).Volume() < 1e-7
        assert shape.intersect(g.cylinder(1.5, -0.1, 5.2, x, y)).Volume() < 1e-7
    pilot = wall_mount.make_self_tapping_wall_shoe(2.2)
    assert pilot.intersect(g.cylinder(1.09, 5.7, 12.7)).Volume() < 1e-7


def test_flat_jig_preserves_fit_and_stops_before_back_face():
    jig = alignment.make_flat_jig()
    assert jig.isValid() and len(jig.Solids()) == 1
    bb = jig.BoundingBox()
    np.testing.assert_allclose(
        [bb.xlen, bb.ylen, bb.zmin, bb.zmax], [92, 60, 0, 8.4], atol=1e-6
    )
    top = (
        alignment.make_locator(5.2, 4.4)
        .intersect(g.extrude(g.box(-8, -15, 8, 15), 7.8, 0.1))
        .BoundingBox()
    )
    np.testing.assert_allclose([top.xlen, top.ylen], [5.2, 15.2], atol=1e-6)
    assert 5 - (bb.zmax - 4) > 0.59


def test_complete_projects_keep_single_material_and_disable_supports():
    from skadis_hex.kit_printing import assembly_list

    plates = assembly_list()["plates"]
    assert [len(p["objects"]) for p in plates] == [1, 1, 8, 1]
    assert [p["objects"][0]["filaments"][0] for p in plates] == [1, 1, 1, 1]
    assert all(p["plate_params"]["filament_map"] == "1" for p in plates)
    for i, p in enumerate(plates):
        assert all(o["print_params"]["enable_support"] == "0" for o in p["objects"])
    alternative = assembly_list(panel_only=True)["plates"]
    assert len(alternative) == 1 and len(alternative[0]["objects"]) == 1
    assert alternative[0]["objects"][0]["path"] == plates[0]["objects"][0]["path"]
