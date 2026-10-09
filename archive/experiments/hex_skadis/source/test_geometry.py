"""Regression tests for the original failure: local grids drift across seams.

Run with: python -m pytest -q test_geometry.py
"""
import importlib.util
from pathlib import Path
import math
import pytest

SOURCE = Path(__file__).with_name('generate.py')


def module():
    assert SOURCE.exists(), 'Parametric generator has not been implemented'
    import generate
    return generate


def test_nine_tiles_keep_one_global_grid_and_no_duplicate_slots():
    g = module()
    c = g.Config()
    pts = g.slot_centres(c)
    assert len(pts) >= 30, 'Panel must retain useful storage area'
    seen = set()
    positions = g.layout(c)
    assert len(positions) == 9
    for ox, oy in positions:
        for x, y in pts:
            gx, gy = x + ox, y + oy
            # Independently check the two standard subgrids, with y-origin +10.
            assert abs(gx / 20 - round(gx / 20)) < 1e-9
            assert abs(((gy-10) / 20 - gx / 20) % 2) < 1e-8
            assert (gx, gy) not in seen
            seen.add((gx, gy))


def test_wrong_hex_proportions_are_rejected_instead_of_scaling_slots():
    g = module()
    with pytest.raises(ValueError, match='lattice'):
        g.Config(height=240 * math.sqrt(3) / 2)
    with pytest.raises(ValueError):
        g.Config(slot_allowance=3)


def test_gap_does_not_change_grid_or_module_pitch():
    g = module()
    a, b = g.Config(gap=0.2), g.Config(gap=0.6)
    assert g.layout(a) == g.layout(b)
    assert set(g.slot_centres(a)) == set(g.slot_centres(b))
    p = g.panel_polygon(b)
    from shapely.affinity import translate
    for x, y in [(0, 200), (180, 100), (180, -100)]:
        assert p.distance(translate(p, xoff=x, yoff=y)) == pytest.approx(0.6)


def test_slots_have_edge_and_hardware_clearance():
    g = module()
    c = g.Config(slot_allowance=0.3)
    p = g.panel_polygon(c)
    for x, y in g.slot_centres(c):
        slot = g.slot_polygon(x, y, c)
        assert p.covers(slot)
        assert p.exterior.distance(slot) >= 2 - 1e-7
        for keepout in g.hardware_keepouts(c):
            assert slot.distance(keepout) >= 2 - 1e-7


def test_all_six_edges_mate_with_the_same_bridge():
    g = module()
    c = g.Config()
    edges = g.edge_frames(c)
    shifts = [(180, 100), (0, 200), (-180, 100), (-180, -100), (0, -200), (180, -100)]
    # Every mating locator must coincide with a pin on the universal connector.
    for k, shift in enumerate(shifts):
        edge = edges[k]
        opposite = edges[(k + 3) % 6]
        holes = g.edge_pin_centres(edge)
        holes += [(x + shift[0], y + shift[1]) for x, y in g.edge_pin_centres(opposite)]
        pins = g.bridge_world_pins(edge)
        for p in pins:
            assert min(math.dist(p, q) for q in holes) < 1e-8


def test_real_cad_has_through_slots_and_blind_pin_sockets():
    g = module()
    c = g.Config()
    shape = g.make_panel(c)
    assert shape.isValid() and len(shape.Solids()) == 1
    bb = shape.BoundingBox()
    assert 239 < bb.xlen < 240 and 199 < bb.ylen < 200
    assert bb.zlen == pytest.approx(5)
    for x, y in g.slot_centres(c):
        assert not shape.isInside((x, y, 2.5))
    for frame in g.edge_frames(c):
        for x, y in g.edge_pin_centres(frame):
            assert shape.isInside((x, y, 1))
            assert not shape.isInside((x, y, 4.5))


def test_bridge_fits_without_boolean_interference():
    g = module()
    c = g.Config()
    panel = g.make_panel(c)
    key = g.make_bridge(c)
    assert key.isValid() and len(key.Solids()) == 1
    for k, shift in [(0, (180, 100)), (1, (0, 200)), (5, (180, -100))]:
        installed = g.install_bridge(key, g.edge_frames(c)[k], c)
        for ox, oy in [(0, 0), shift]:
            overlap = installed.intersect(panel.translate((ox, oy, 0)))
            assert overlap.Volume() < 1e-5


def test_printable_coupons_retain_two_and_three_peg_patterns():
    g = module()
    c = g.Config()
    coupon = g.make_fit_coupon(c)
    assert coupon.isValid() and len(coupon.Solids()) == 1
    for x, y in [(-20, -20), (20, -20), (0, 0), (-20, 20), (20, 20)]:
        assert not coupon.isInside((x, y, 2.5))
    for direction in ['horizontal', 'diagonal_up', 'diagonal_down']:
        pieces = g.make_seam_coupons(c, direction)
        assert len(pieces) == 2
        for shape in pieces:
            assert shape.isValid() and len(shape.Solids()) == 1
            assert shape.Volume() > 1000


def test_sample_outer_cuts_do_not_leave_partial_receiving_slots():
    g = module()
    from shapely.geometry import box
    c = g.Config()
    for direction in ['horizontal', 'diagonal_up', 'diagonal_down']:
        _, shift, bounds = g.seam_info(direction)
        crop = box(*bounds)
        for ox, oy in [(0,0), shift]:
            for x, y in g.slot_centres(c):
                slot = g.slot_polygon(x+ox, y+oy, c)
                assert not crop.intersects(slot) or crop.covers(slot), (direction,x+ox,y+oy)


def test_two_row_accessory_footprints_exist_inside_and_across_every_seam():
    g = module()
    c = g.Config()
    # Literal 40-mm vertical spans, not recomputed from the implementation.
    fixtures = [
        ((0,0), [(-40,-30),(0,-30),(-40,10),(0,10),(-20,-10)]),
        ((0,200), [(-20,70),(20,70),(-20,110),(20,110)]),
        ((180,100), [(60,30),(140,30),(60,70),(140,70)]),
        ((180,-100), [(60,-50),(140,-50),(60,-10),(140,-10)]),
    ]
    local = set(g.slot_centres(c))
    for (ox,oy), points in fixtures:
        available = local | {(x+ox,y+oy) for x,y in local}
        assert set(points) <= available
