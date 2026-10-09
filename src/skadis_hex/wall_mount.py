"""Accepted adhesive shoe for M4x16..20 and a0.8mm washer."""

import cadquery as cq
from shapely.ops import unary_union
from .geometry import cylinder, extrude, hexagon, box


def make_wall_shoe():
    # Upper shoe: tape centroid 8 mm ABOVE screw; rotate 180deg for lower.
    # Installed z=5..23. Base rear z=23 accepts 30 x 50 tape.
    base = (
        cq.Workplane("XY", origin=(0, 8, 20))
        .rect(34, 54)
        .extrude(3)
        .edges("|Z")
        .fillet(2)
        .val()
    )
    post = cylinder(6, 5, 15)
    # Four local buttresses, entirely behind panel ribs, z=15.5..20.
    gussets = [
        extrude(box(-12, -2, 12, 2), 15.5, 4.5),
        extrude(box(-2, -16, 2, 28), 15.5, 4.5),
    ]
    shape = base.fuse(post, *gussets).clean()
    pocket = unary_union([hexagon(7.4), box(0, -3.7, 6.2, 3.7)])
    # Side-loaded M4 nut under a 2-mm roof. M4x16 with .8 washer ends z15.2.
    shape = shape.cut(extrude(pocket, 7, 3.6), cylinder(2.25, 4.9, 15.6)).clean()
    assert shape.isValid() and len(shape.Solids()) == 1
    return shape
