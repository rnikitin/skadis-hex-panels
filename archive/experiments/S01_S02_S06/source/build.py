#!/usr/bin/env python3
"""S01/S02/S06 ribbed prototypes. mm; face z=0..5, rear ribs z=5..15.

Printed face down, ribs up. Same gap/slot positions as the verified 2D designs.
Rear free corridors are 16x34 mm, including slots belonging to neighbour tiles.
No panel connectors or wall-fastening hardware is part of these prototypes.
"""
from pathlib import Path
from functools import lru_cache
import json
import cadquery as cq
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parent.parent
FACE=5.0
RIB_HEIGHT=10.0
RIB_WIDTH=2.4
SLOT_WIDTH=5.3
SLOT_LENGTH=15.3
GAP=.3


@lru_cache(maxsize=1)
def designs():
    return json.loads(Path(__file__).with_name('designs.json').read_text())


def outline(name):
    return Polygon(designs()[name]['vertices']).buffer(-GAP/2,join_style=2)


def clearance_centres(name):
    p=outline(name);px,py=designs()[name]['phase']
    centres=[]
    for i in range(-9,10):
        for j in range(-6,7):
            x,y=20*i+px,40*j+20*(i%2)+py
            if p.intersects(box(x-8,y-17,x+8,y+17)):centres.append((x,y))
    return centres


def rib_plan(name):
    p=outline(name)
    strips=[p.difference(p.buffer(-RIB_WIDTH,join_style=2))]
    # Continuous vertical webs lie between the 20-mm-spaced slot columns.
    for x in range(-170,171,20):strips.append(box(x-RIB_WIDTH/2,-150,x+RIB_WIDTH/2,150))
    for y in range(-140,141,20):strips.append(box(-150,y-RIB_WIDTH/2,150,y+RIB_WIDTH/2))
    free=unary_union([box(x-8,y-17,x+8,y+17) for x,y in clearance_centres(name)])
    return unary_union(strips).intersection(p).difference(free)


def extrude(polygon,z,height):
    def wire(ring):
        return cq.Wire.makePolygon([cq.Vector(x,y,z) for x,y in list(ring.coords)[:-1]],close=True)
    return cq.Solid.extrudeLinear(wire(polygon.exterior),[wire(h) for h in polygon.interiors],cq.Vector(0,0,height))


@lru_cache(maxsize=3)
def make_panel(name):
    d=designs()[name]
    base=extrude(outline(name),0,FACE)
    cutters=cq.Workplane('XY',origin=(0,0,-.1)).pushPoints(d['local_centres']).slot2D(SLOT_LENGTH,SLOT_WIDTH,90).extrude(FACE+.2)
    base=base.cut(*cutters.vals()).clean()
    ribs=rib_plan(name)
    pieces=[ribs] if ribs.geom_type=='Polygon' else list(ribs.geoms)
    rib_solids=[extrude(p,FACE,RIB_HEIGHT) for p in pieces if p.area>1e-6]
    result=base.fuse(*rib_solids).clean()
    if not result.isValid() or len(result.Solids())!=1:raise RuntimeError(f'{name}: invalid/disconnected solid')
    return result


def build():
    ROOT.mkdir(parents=True,exist_ok=True)
    summary=[]
    for name in ['S01','S02','S06']:
        print('Building',name,flush=True)
        shape=make_panel(name);bb=shape.BoundingBox()
        # STL is placed entirely in positive XY, with the flat face at z=0.
        printable=shape.translate((-bb.xmin,-bb.ymin,0))
        dest=ROOT/f'{name}_ribbed.stl'
        cq.exporters.export(printable,str(dest),tolerance=.015,angularTolerance=.10)
        summary.append({'id':name,'file':dest.name,'size_mm':[bb.xlen,bb.ylen,bb.zlen],
                        'volume_cm3':shape.Volume()/1000,'xy_export_shift_mm':[-bb.xmin,-bb.ymin],
                        'whole_slots':designs()[name]['whole_slots'],'slot_fragments':designs()[name]['slot_fragments']})
        print(name,'exported',flush=True)
    report={'face_thickness_mm':FACE,'rib_height_mm':RIB_HEIGHT,'rib_width_mm':RIB_WIDTH,
            'slot_size_mm':[SLOT_WIDTH,SLOT_LENGTH],'rear_free_corridor_mm':[16,34],
            'nominal_joint_gap_mm':GAP,'physical_fit':'NOT TESTED','parts':summary}
    (ROOT/'parameters.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':build()
