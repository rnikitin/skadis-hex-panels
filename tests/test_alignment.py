"""Fit-trial geometry must preserve the lattice and release from the front."""

import numpy as np
import pytest
from skadis_hex import alignment as a


@pytest.mark.parametrize("width", [4.9, 5.1, 5.2])
def test_jig_and_strip_are_single_solids_with_short_locators(width):
    for builder, xy in [(a.make_jig, (92, 60)), (a.make_fit_strip, (16, 60))]:
        shape = builder(width)
        bb = shape.BoundingBox()
        assert shape.isValid() and len(shape.Solids()) == 1
        np.testing.assert_allclose([bb.xlen, bb.ylen, bb.zlen], [*xy, 7.5], atol=1e-6)
        # At z=5 the section must still have the stated full locating width.
        section = a.make_locator(width).intersect(
            a.g.extrude(a.box(-10, -20, 10, 20), 5, 0.1)
        )
        sb = section.BoundingBox()
        np.testing.assert_allclose([sb.xlen, sb.ylen], [width, width + 10], atol=1e-6)


def test_one_jig_uses_whole_slots_and_clears_heads_on_every_seam():
    rows = a.verify_placements()
    assert {r["edge"] for r in rows} == set(range(6))
    for row in rows:
        assert row["panel_ownership"].count(0) == 2
        assert row["panel_ownership"].count(1) == 2
        assert row["minimum_head_clearance_mm"] >= 7.5
        assert row["minimum_slot_to_edge_mm"] > 4.9


def test_fit_sizes_must_leave_nominal_clearance():
    for invalid in (0, -1, 5.3, 6):
        with pytest.raises(ValueError):
            a.make_locator(invalid)


def test_tightest_jig_withdraws_straight_out_of_five_mm_face():
    import cadquery as cq

    face = a.g.extrude(a.box(-60, -40, 60, 40), 0, 5)
    apertures = (
        cq.Workplane("XY", origin=(0, 0, -0.1))
        .pushPoints(a.PIN_POINTS)
        .slot2D(15.3, 5.3, 90)
        .extrude(5.2)
    )
    face = face.cut(*apertures.vals())
    for distance in (0, 0.5, 2, 3.5, 4):
        jig = a.make_jig(5.2).translate((0, 0, -4 - distance))
        assert jig.intersect(face).Volume() < 1e-7


def test_petg_profile_is_resolved_and_has_petg_material_values():
    import json
    from pathlib import Path
    from skadis_hex import printing

    p = json.loads(
        (
            Path(printing.__file__).with_name("print_profiles") / "filament_petg.json"
        ).read_text()
    )
    assert p["filament_type"] == ["PETG"]
    assert p["filament_density"] == ["1.27"]
    assert p["nozzle_temperature"] == ["255"] * 3
    assert p["textured_plate_temp"] == ["70"]
    assert "inherits" not in p and "include" not in p
