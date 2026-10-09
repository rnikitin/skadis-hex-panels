"""Replaceable spring registration key in rear-open perimeter slots.

PROTOTYPE: analytical arm deflection and geometric paths, not physical fit.
No SKADIS slots consumed, no front seam fasteners. Units mm; front z=0.
"""
from pathlib import Path
from functools import lru_cache
import sys,json,math
import numpy as np
import cadquery as cq
from shapely.geometry import box,LineString,Point,Polygon
from shapely.ops import unary_union,transform as warp
from shapely.affinity import scale
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'hex_v3'/'source'))
import design as d

ROOT=Path(__file__).resolve().parent
RIM=3.2;FACE=5.;BACK=15.
POCKET_CLEAR=.25;FLOOR=8.8;KEY_Z=9.;KEY_H=3.2
LIP_MIN_N=9.1;LIP_MAX_N=10.3
LIP_LOW=12.5;LIP_PEAK=12.85;LIP_HIGH=13.2;LIP_INNER=1.9
ARM=1.;ROOT_N=.8;ARM_L=9.7;TIP_DEFLECTION=.18
HOOK_DROP=3.0  # Extra vertical rear relief, provisional; mirrored for180deg use.
REAR_CLEAR=unary_union([LineString([(x,y-5-HOOK_DROP),(x,y+5+HOOK_DROP)]).buffer(4.65,quad_segs=32) for x,y in d.CENTRES])

def key_outline():
    #24x8 envelope; taper the shoulders to preserve hook clearance.
    return unary_union([box(-10.5,-2,10.5,2),
        Polygon([(10.5,-2.7),(12,-4),(12,4),(10.5,2.7)]),
        Polygon([(-10.5,-2.7),(-12,-4),(-12,4),(-10.5,2.7)])])

def key_plan(half=None):
    p=key_outline()
    for sign in (-1,1):
        p=p.difference(LineString([(sign*1.8,0),(sign*13,0)]).buffer(1,quad_segs=16))
    if half:
        def deform(x,y,z=None):
            x=np.asarray(x);y=np.asarray(y)
            q=np.clip((abs(x)-ROOT_N)/ARM_L,0,1)
            delta=TIP_DEFLECTION*q*q*(3-q)/2
            delta*=np.where(x<0,half in ('negative','both'),half in ('positive','both'))
            return x,y-np.sign(y)*delta
        p=warp(deform,p)
    assert p.is_valid and p.geom_type=='Polygon'
    return p

def key(half=None):return d.extrude(key_plan(half),KEY_Z,KEY_H)

def local_solid(shape,site):return d.install(shape,site)

def world_poly(p,s):return d.transform(p,np.array(s['point']),np.array(s['normal']),np.array(s['tangent']))

def diagonal_plan():
    strips=[]
    for c in (-40,40):
        for line in (LineString([(-400,400+c),(400,-400+c)]),LineString([(-400,-400-c),(400,400-c)])):
            strips.append(line.buffer(1.2,cap_style=2).intersection(d.P))
    return unary_union(strips)

@lru_cache(None)
def sites():
    # On sloping seams the key follows a45deg grid corridor. Its centre is
    # deliberately offset from the seam; opposing panels have matching pockets.
    rows=[(0,45,[(100,20),(80,80)]),(1,90,[(-30,100),(30,100)]),
          (2,135,[(-100,20),(-80,80)]),(3,225,[(-100,-20),(-80,-80)]),
          (4,270,[(-30,-100),(30,-100)]),(5,315,[(100,-20),(80,-80)])]
    out=[]
    from shapely.affinity import translate
    for edge,angle,points in rows:
        a=math.radians(angle);n=np.array([math.cos(a),math.sin(a)]);t=np.array([-n[1],n[0]])
        for point in points:
            s=dict(edge=edge,point=point,normal=n.tolist(),tangent=t.tolist(),key_axis_degrees=angle)
            footprint=world_poly(key_outline().buffer(POCKET_CLEAR,join_style=2),s)
            margin=footprint.distance(REAR_CLEAR)
            assert margin>.05,('hook corridor',s,margin)
            diags=unary_union([diagonal_plan(),translate(diagonal_plan(),*(2*d.frames()[edge]['mid']))])
            assert not footprint.intersects(diags),('diagonal rib',s)
            s['rear_relief_margin_mm']=margin;out.append(s)
    return sorted(out,key=lambda s:(s['edge'],s['point']))

def receiver_plan(s):
    # Grow walls where there is room; never invade the reserved hook path.
    return world_poly(key_outline().buffer(1.2,join_style=2),s).difference(REAR_CLEAR.buffer(.15)).intersection(d.P)

def pocket_plan(s):return world_poly(key_outline().buffer(POCKET_CLEAR,join_style=2),s)

def lip_shapes(s):
    shapes=[]
    for sign in (-1,1):
        # Triangular ramps: .35mm projection over .35mm rise.
        pts=[cq.Vector(-LIP_MAX_N,sign*2.25,LIP_LOW),cq.Vector(-LIP_MAX_N,sign*LIP_INNER,LIP_PEAK),cq.Vector(-LIP_MAX_N,sign*2.25,LIP_HIGH)]
        wire=cq.Wire.makePolygon(pts,close=True)
        shape=cq.Solid.extrudeLinear(wire,[],cq.Vector(LIP_MAX_N-LIP_MIN_N,0,0))
        shapes.append(local_solid(shape,s))
    return shapes

@lru_cache(None)
def panel(with_lips=True):
    base=d.extrude(d.P,0,5)
    relevant=[c for c in d.CENTRES if d.P.intersects(Point(c).buffer(12))]
    slots=cq.Workplane('XY',origin=(0,0,-.1)).pushPoints(relevant).slot2D(15.3,5.3,90).extrude(5.2)
    base=base.cut(*slots.vals())
    ring=d.P.difference(d.P.buffer(-RIM,join_style=2))
    # Compact, slot-shaped rear relief instead of the obsolete16x34 rectangles.
    # Its2mm allowance is provisional until actual hooks are tried.
    rim=d.extrude(ring,5,10)
    relief=cq.Workplane('XY',origin=(0,0,4.99)).pushPoints(relevant).slot2D(19.3+2*HOOK_DROP,9.3,90).extrude(10.02)
    rim=rim.cut(*relief.vals())
    bodies=[rim]+[d.extrude(p,5,10) for p in d.pieces(diagonal_plan())]
    for s in sites():bodies.extend(d.extrude(q,5,10) for q in d.pieces(receiver_plan(s)) if q.area>1e-8)
    body=base.fuse(*bodies).clean()
    cuts=[d.cylinder(2.25,-.1,5.2,x,y) for x,y in d.MOUNTS]
    for s in sites():cuts.append(d.extrude(pocket_plan(s),FLOOR,15.1-FLOOR))
    body=body.cut(*cuts).clean()
    if with_lips:body=body.fuse(*[p for s in sites() for p in lip_shapes(s)]).clean()
    assert body.isValid() and len(body.Solids())==1
    return body

def picked_sites():
    # Two different edges of the same new panel, both adjacent to vertex(60,100).
    return [min([s for s in sites() if s['edge']==e],key=lambda s:np.linalg.norm(np.array(s['point'])-np.array([60,100]))) for e in (0,1)]

def coupon_bounds(expansion=0):
    chosen=picked_sites();pts=np.array([s['point'] for s in chosen])
    lo=np.floor((pts.min(axis=0)-20-10)/20)*20+10-expansion
    hi=np.ceil((pts.max(axis=0)+20-10)/20)*20+10+expansion
    return lo,hi

@lru_cache(None)
def corner_coupons():
    p=panel()
    for expansion in (0,20,40):
        lo,hi=coupon_bounds(expansion);crop=d.extrude(box(*lo,*hi),-.1,15.2)
        out=[p.intersect(crop).clean()]
        for e in (0,1):
            v=2*d.frames()[e]['mid'];out.append(p.translate((*v,0)).intersect(crop).clean())
        if all(s.isValid() and len(s.Solids())==1 for s in out):
            (ROOT/'coupon_crop.json').write_text(json.dumps(dict(bounds_mm=[lo.tolist(),hi.tolist()],components=[len(s.Solids()) for s in out],discarded_components=0,reason='Boundary moved away from slots; no largest-solid filtering'),indent=2)+'\n')
            return out
    raise RuntimeError('Coupon contains disconnected material; do not silently discard it')

def export(name,s):
    assert s.isValid() and len(s.Solids())==1,name
    bb=s.BoundingBox();v=[-bb.xmin,-bb.ymin,-bb.zmin]
    cq.exporters.export(s.translate(v),str(ROOT/'stl'/(name+'.stl')),tolerance=.012,angularTolerance=.08)
    return dict(name=name,size_mm=[bb.xlen,bb.ylen,bb.zlen],volume_cm3=s.Volume()/1000,print_shift_mm=v)

def build():
    for folder in ('stl','step','images','projects'): (ROOT/folder).mkdir(exist_ok=True)
    p=panel();print('Panel CAD ready',flush=True)
    cq.exporters.export(p,str(ROOT/'step'/'S01_hidden_joint_PROTOTYPE.step'))
    parts=[export('spring_key_24x8x3p2',key())]
    for name,s in zip(('corner_NEW','corner_EXISTING_oblique','corner_EXISTING_horizontal'),corner_coupons()):parts.append(export(name,s))
    a=cq.Assembly();a.add(p,name='new_panel',color=cq.Color(.76,.68,.46))
    for e in (0,1):
        v=2*d.frames()[e]['mid'];a.add(p.translate((*v,0)),name=f'existing_{e}',color=cq.Color(.65,.76,.70))
    for i,s in enumerate([s for s in sites() if s['edge'] in (0,1)]):a.add(local_solid(key(),s),name=f'key_{i}',color=cq.Color(.35,.57,.68))
    a.export(str(ROOT/'step'/'three_panels_assembly.step'))
    report=dict(status='CAD prototype; untested physical snap-fit',parts=parts,sites=sites(),test_sites=picked_sites(),
                dimensions=dict(rim_width_mm=RIM,key_mm=[24,8,3.2],key_seated_z_mm=[9,12.2],
                                pocket_clearance_mm=POCKET_CLEAR,retainer_throat_mm=3.8,neck_width_mm=4.,arm_width_mm=ARM,arm_length_mm=ARM_L),
                rear_hook_relief_mm=2,extra_hook_vertical_travel_mm=HOOK_DROP,travel_mirrored_for_180_degrees=True,rear_hook_relief_validated=False,wall_shoes='unchanged approved v4',
                keys_per_join=2,working_slots_consumed=0,front_seam_holes=0,additional_depth_mm=0)
    (ROOT/'parameters.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Exported',len(parts),'parts',flush=True)

if __name__=='__main__':build()
