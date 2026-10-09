"""Shared S01 geometry and CadQuery helpers. Units: millimetres; face z=0."""

from pathlib import Path
from functools import lru_cache
import json, math
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.affinity import affine_transform

VERTICES = np.array(
    [(120, 0), (60, 100), (-60, 100), (-120, 0), (-60, -100), (60, -100)], float
)
FACE = 5.0
RIB = 2.4
HEIGHT = 10.0
GAP = 0.3
MOUNTS = [(x, y) for x in (-40.0, 40.0) for y in (-40.0, 40.0)]
CENTRES = [
    (20 * i + 20, 40 * j + 20 * (i % 2)) for i in range(-9, 10) for j in range(-6, 7)
]
P = Polygon(VERTICES).buffer(-GAP / 2, join_style=2)
SLOTS = unary_union(
    [
        LineString([(x, y - 5), (x, y + 5)]).buffer(2.65, quad_segs=32)
        for x, y in CENTRES
    ]
)
FACE_PLAN = P.difference(SLOTS)


def pieces(p):
    return (
        [p]
        if p.geom_type == "Polygon"
        else [x for x in p.geoms if x.geom_type == "Polygon"]
    )


def extrude(p, z, h):
    def wire(r):
        return cq.Wire.makePolygon(
            [cq.Vector(x, y, z) for x, y in list(r.coords)[:-1]], close=True
        )

    return cq.Solid.extrudeLinear(
        wire(p.exterior), [wire(r) for r in p.interiors], cq.Vector(0, 0, h)
    )


def cylinder(r, z, h, x=0, y=0):
    return cq.Solid.makeCylinder(r, h, cq.Vector(x, y, z))


def prism(poly, z, h):
    return extrude(poly, z, h)


def hexagon(af=5.9):
    # AF measured along y; opening channel below is 5.9 mm wide.
    r = af / math.sqrt(3)
    return Polygon(
        [
            (r * math.cos(i * math.pi / 3), r * math.sin(i * math.pi / 3))
            for i in range(6)
        ]
    )


def csk(x, y, z=0, depth=FACE):
    shaft = cylinder(1.7, z - 0.1, depth + 0.2, x, y)
    cone = cq.Solid.makeCone(3.2, 1.7, 1.5, cq.Vector(x, y, z))
    return shaft.fuse(cone)


def frames():
    result = []
    for i, a in enumerate(VERTICES):
        b = VERTICES[(i + 1) % 6]
        length = np.linalg.norm(b - a)
        t = (b - a) / length
        n = np.array([t[1], -t[0]])
        result.append(dict(edge=i, a=a, b=b, t=t, n=n, length=length, mid=(a + b) / 2))
    return result


def transform(poly, point, n, t):
    return affine_transform(poly, [n[0], t[0], n[1], t[1], point[0], point[1]])


def install(shape, s, z=0):
    angle = math.degrees(math.atan2(s["normal"][1], s["normal"][0]))
    return shape.rotate((0, 0, 0), (0, 0, 1), angle).translate((*s["point"], z))
