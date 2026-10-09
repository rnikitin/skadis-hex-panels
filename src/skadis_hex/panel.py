"""Current plain S01 panel: continuous lattice, four diagonals, no seam keys."""

from functools import lru_cache
import cadquery as cq
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from . import geometry as g

RIM_WIDTH = 3.2
HOOK_DROP = 3.0


def diagonal_plan():
    return unary_union(
        [
            line.buffer(1.2, cap_style=2).intersection(g.P)
            for c in (-40, 40)
            for line in (
                LineString([(-400, 400 + c), (400, -400 + c)]),
                LineString([(-400, -400 - c), (400, 400 - c)]),
            )
        ]
    )


def rim_plan():
    ring = g.P.difference(g.P.buffer(-RIM_WIDTH, join_style=2))
    relief = unary_union(
        [
            LineString([(x, y - 8), (x, y + 8)]).buffer(4.65, quad_segs=32)
            for x, y in g.CENTRES
        ]
    )
    return ring.difference(relief)


@lru_cache(None)
def make_panel():
    relevant = [p for p in g.CENTRES if g.P.intersects(Point(p).buffer(12))]
    face = g.extrude(g.P, 0, 5)
    slots = (
        cq.Workplane("XY", origin=(0, 0, -0.1))
        .pushPoints(relevant)
        .slot2D(15.3, 5.3, 90)
        .extrude(5.2)
    )
    face = face.cut(*slots.vals())
    rim = g.extrude(g.P.difference(g.P.buffer(-RIM_WIDTH, join_style=2)), 5, 10)
    relief = (
        cq.Workplane("XY", origin=(0, 0, 4.99))
        .pushPoints(relevant)
        .slot2D(19.3 + 2 * HOOK_DROP, 9.3, 90)
        .extrude(10.02)
    )
    rim = rim.cut(*relief.vals())
    shape = face.fuse(
        rim, *[g.extrude(p, 5, 10) for p in g.pieces(diagonal_plan())]
    ).clean()
    shape = shape.cut(*[g.cylinder(1.7, -0.1, 5.2, x, y) for x, y in g.MOUNTS]).clean()
    assert shape.isValid() and len(shape.Solids()) == 1
    return shape
