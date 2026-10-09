"""Protect the accepted dimensions/volumes while moving the code into a package."""

import json
from pathlib import Path

import numpy as np

from skadis_hex import geometry, joints
from skadis_hex.wall_mount import make_wall_shoe

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/current_geometry.json").read_text()
)


def test_key_matches_pre_migration_geometry():
    key = joints.key()
    box = key.BoundingBox()
    np.testing.assert_allclose(
        [box.xlen, box.ylen, box.zlen], FIXTURE["key"]["size_mm"], atol=1e-7
    )
    assert abs(key.Volume() / 1000 - FIXTURE["key"]["volume_cm3"]) < 1e-7


def test_wall_shoe_matches_approved_geometry():
    shoe = make_wall_shoe()
    assert shoe.isValid() and len(shoe.Solids()) == 1
    assert abs(shoe.Volume() / 1000 - FIXTURE["wall_shoe"]["volume_cm3"]) < 1e-7
    for length in (16, 19, 20):
        screw = geometry.cylinder(2, -0.8, length)
        assert screw.intersect(shoe).Volume() < 1e-7


def test_lattice_supports_two_row_accessories_and_tile_translations():
    def on_grid(x, y):
        i = (x - 20) / 20
        return i == int(i) and (y - 20 * (int(i) % 2)) % 40 == 0

    for x, y in geometry.CENTRES:
        assert on_grid(x, y + 40)
        assert on_grid(x + 180, y + 100)
        assert on_grid(x, y + 200)
