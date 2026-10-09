"""S01 without seam fasteners; removable 80x40 mm registration jig.

Reuses the already verified S01 lattice/ribs from sibling hex_v3/source/design.py.
No new load-rating calculation. Separate shoe gains a deeper blind bore.
"""
from pathlib import Path
import sys,json
import numpy as np
import cadquery as cq
from shapely.geometry import box,Point
from shapely.ops import unary_union
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'hex_v3'/'source'))
import design as d

ROOT=Path(__file__).resolve().parent
PIN_W=4.7;PIN_L=14.7;PIN_H=3.5;BASE=2.4
PINS=[(x,y) for x in (-40,40) for y in (-20,20)]
PLACEMENTS=[(100,60),(20,100),(-100,60),(-100,-60),(20,-100),(100,-60)]

def panel():
    s=d.extrude(d.P,0,5)
    local=[c for c in d.CENTRES if d.P.intersects(Point(c).buffer(8))]
    cutters=cq.Workplane('XY',origin=(0,0,-.1)).pushPoints(local).slot2D(15.3,5.3,90).extrude(5.2)
    s=s.cut(*cutters.vals())
    s=s.fuse(*[d.extrude(p,5,10) for p in d.pieces(d.ribs())]).clean()
    s=s.cut(*[d.cylinder(2.25,-.1,5.2,x,y) for x,y in d.MOUNTS]).clean()
    assert s.isValid() and len(s.Solids())==1
    return s

def jig_plan():return unary_union([box(-46,-30,-34,30),box(34,-30,46,30),box(-40,-6,40,6)])

def jig():
    s=d.extrude(jig_plan(),0,BASE)
    pins=cq.Workplane('XY',origin=(0,0,BASE)).pushPoints(PINS).slot2D(PIN_L,PIN_W,90).extrude(PIN_H)
    pins=pins.faces('>Z').edges().chamfer(.4)
    s=s.fuse(*pins.vals()).clean()
    assert s.isValid() and len(s.Solids())==1
    return s

def export(name,s,flip=False):
    printable=s.rotate((0,0,0),(1,0,0),180) if flip else s
    bb=printable.BoundingBox();shift=(-bb.xmin,-bb.ymin,-bb.zmin)
    cq.exporters.export(printable.translate(shift),str(ROOT/(name+'.stl')),tolerance=.012,angularTolerance=.08)
    cq.exporters.export(s,str(ROOT/(name+'.step')))
    return dict(name=name,size_mm=[bb.xlen,bb.ylen,bb.zlen],volume_cm3=s.Volume()/1000,stl_shift_mm=shift)

def main():
    import trimesh
    p=panel();j=jig();shoe=d.shoe().cut(d.cylinder(2.25,17.4,3.1)).clean()
    assert shoe.isValid() and len(shoe.Solids())==1
    parts=[export('S01_no_seam_connectors',p),export('alignment_jig_80x40',j),export('wall_shoe_M4_16_to_20',shoe,True)]
    checks=[]
    for e,(cx,cy) in enumerate(PLACEMENTS):
        shift=2*d.frames()[e]['mid'];neighbour=p.translate((*shift,0))
        # Existing panel stays on wall. New panel/jig start 2mm forward,
        # with existing-side pins already inserted 1.5mm, then press to wall.
        for dz in (-2.,-1.,0.):
            tool=j.translate((cx,cy,dz-BASE));new=neighbour.translate((0,0,dz))
            overlap=tool.intersect(p).Volume()+tool.intersect(new).Volume()
            assert overlap<1e-5,(e,dz,overlap)
            checks.append(dict(edge=e,new_panel_face_offset_mm=dz,jig_collision_mm3=overlap))
        for x,y in PINS:
            # Every registration pin is in a complete slot belonging to one tile.
            pin=cq.Workplane('XY').center(cx+x,cy+y).slot2D(15.3,5.3,90).extrude(5).val()
            footprints=[d.P, __import__('shapely').affinity.translate(d.P,*shift)]
            from shapely.geometry import LineString
            fp=LineString([(cx+x,cy+y-5),(cx+x,cy+y+5)]).buffer(2.65)
            assert any(q.covers(fp) for q in footprints),(e,x,y,'split registration slot')
    for name,s in [('panel',p),('jig',j)]:
        m=trimesh.load_mesh(ROOT/('S01_no_seam_connectors.stl' if name=='panel' else 'alignment_jig_80x40.stl'))
        assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    for normal in ((1,0,0),(0,1,0)):
        assert p.cut(p.mirror(normal)).Volume()<1e-5
    screws=[]
    for length in (16,19,20):
        overlap=d.cylinder(2,-.8,length).intersect(shoe).Volume()
        assert overlap<1e-6
        screws.append(dict(length_mm=length,washer_mm=.8,tip_z_mm=length-.8,
                           clearance_to_bore_bottom_mm=20.5-(length-.8),distance_to_tape_mm=23-(length-.8),collision_mm3=overlap))
    m=trimesh.load_mesh(ROOT/'wall_shoe_M4_16_to_20.stl')
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    report=dict(parts=parts,placements_mm=PLACEMENTS,assembly_checks=checks,screw_checks=screws,
                pin_size_mm=[PIN_W,PIN_L,PIN_H],nominal_slot_size_mm=[5.3,15.3],
                nominal_planar_clearance_per_side_mm=.3,
                physical_fit='NOT TESTED',new_structural_analysis=False,
                wall_shoes='new deeper blind bore ends at z=20.5; M4x16/19/20 with 0.8 washer fit; not for self-tappers',
                after_mounting='No permanent inter-panel restraint; each panel relies on its own shoes/tape')
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 18 assembly poses, 24 complete registration slots, 3 closed meshes, XY symmetry, M4x16/19/20')
    print(json.dumps(parts,indent=2))

if __name__=='__main__':main()
