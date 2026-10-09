from pathlib import Path
import numpy as np
import pytest


def api():
    assert Path(__file__).with_name('build.py').exists(), 'Ribbed CAD generator missing'
    import build
    return build


@pytest.mark.parametrize('name',['S01','S02','S06'])
def test_single_symmetric_solid_with_correct_dimensions(name):
    b=api();design=b.designs()[name];shape=b.make_panel(name)
    assert shape.isValid() and len(shape.Solids())==1
    bb=shape.BoundingBox()
    assert bb.zmin==pytest.approx(0) and bb.zmax==pytest.approx(15)
    assert bb.xlen==pytest.approx(design['width_mm'],abs=.6)
    assert bb.ylen==pytest.approx(design['height_mm'],abs=.6)
    # A 180-degree flip must preserve the whole CAD, including rear ribs.
    rotated=shape.rotate((0,0,0),(0,0,1),180)
    assert shape.cut(rotated).Volume()<1e-5


@pytest.mark.parametrize('name',['S01','S02','S06'])
def test_ribs_leave_hook_clearance_and_front_slots_open(name):
    b=api();import cadquery as cq
    shape=b.make_panel(name)
    for x,y in b.designs()[name]['local_centres']:
        # Independent specified 16x34 clearance corridor, throughout the rear depth.
        free=cq.Workplane('XY',origin=(x,y,5.01)).box(16,34,9.98,centered=(True,True,False)).val()
        assert shape.intersect(free).Volume()<1e-6
    points=[(20,0),(-20,0),(0,20),(0,-20)] if name!='S06' else [(0,0),(40,0),(-40,0),(0,40)]
    for x,y in points:
        assert not shape.isInside((x,y,2.5))
    assert shape.isInside((10,0,10)), 'Missing vertical stiffness rib'
    assert shape.isInside((0,20 if name=='S06' else 0,10)), 'Missing cross brace'
    if name=='S06':
        # A neighbour's slot need not intersect our front contour to need rear clearance.
        neighbour=cq.Workplane('XY',origin=(120,0,5.01)).box(16,34,9.98,centered=(True,True,False)).val()
        assert shape.intersect(neighbour).Volume()<1e-6
