"""Checks for the user-selected nominal3x16 pointed self-tapping screw."""

import math
import pytest
from skadis_hex import geometry as g, joints, wall_mount


@pytest.mark.parametrize("diameter", [2.2, 2.4, 2.6])
def test_self_tapping_pilot_has_space_below_tip_and_a_solid_blind_floor(diameter):
    shoe = wall_mount.make_self_tapping_wall_shoe(diameter)
    assert shoe.isValid() and len(shoe.Solids()) == 1
    bore_probe = g.cylinder(diameter / 2 - 0.01, 5.7, 12.7)
    assert shoe.intersect(bore_probe).Volume() < 1e-7
    # A3mm major-thread envelope deliberately engages printed material.
    thread_envelope = g.cylinder(1.5, 6, 9.5)
    assert shoe.intersect(thread_envelope).Volume() > 1
    # 16mm under-head length with a5mm face ends at z16, clear of the blind floor.
    bottom_probe = g.cylinder(0.9, 18.6, 4.3)
    assert abs(shoe.intersect(bottom_probe).Volume() - bottom_probe.Volume()) < 1e-7


def test_self_tapping_post_has_no_open_side_nut_channel():
    shoe = wall_mount.make_self_tapping_wall_shoe(2.4)
    probe = g.cylinder(0.3, 8, 2, 4.5, 0)
    assert abs(shoe.intersect(probe).Volume() - probe.Volume()) < 1e-7


def test_self_tapping_pilot_cannot_exceed_the_nominal_thread_diameter():
    with pytest.raises(ValueError):
        wall_mount.make_self_tapping_wall_shoe(3)


def test_ordered_head_has_a_bearing_ledge_around_the_smaller_panel_hole():
    panel = joints.panel(wall_hole_diameter=3.4)
    shaft = g.cylinder(1.5, -0.1, 5.2, 40, 40)
    assert panel.intersect(shaft).Volume() < 1e-7
    bearing_probe = g.cylinder(4.9 / 2, 0.1, 0.2, 40, 40)
    expected = math.pi / 4 * (4.9**2 - 3.4**2) * 0.2
    assert abs(panel.intersect(bearing_probe).Volume() - expected) < 1e-7
