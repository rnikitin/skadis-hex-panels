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
RIM=3.2;FACE=5.;BACK=15.;PAD_DEPTH=6.;PAD_W=9.
SLOT_HALF=1.4;FLOOR=8.8;KEY_Z=9.;KEY_H=2.4
LIP_MIN_N=4.95;LIP_MAX_N=6.15
LIP_LOW=11.7;LIP_PEAK=12.;LIP_HIGH=12.3;LIP_INNER=1.1
ARM=.8;ROOT_N=.7;ARM_L=5.65;TIP_DEFLECTION=.18
HOOK_DROP=3.0  # Extra vertical rear relief, provisional; mirrored for180deg use.
REAR_CLEAR=unary_union([LineString([(x,y-5-HOOK_DROP),(x,y+5+HOOK_DROP)]).buffer(4.65,quad_segs=32) for x,y in d.CENTRES])

def key_plan(half=None):
    p=unary_union([box(-6.35,-1.2,6.35,1.2),box(-7.35,-2.2,-6.35,2.2),box(6.35,-2.2,7.35,2.2)])
    for sign in (-1,1):
        p=p.difference(LineString([(sign*1.1,0),(sign*8,0)]).buffer(.4,quad_segs=16))
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
    fs=d.frames();out=[];diags=diagonal_plan()
    for e in range(3):
        f=fs[e];best=None
        for dist in np.arange(18,f['length']/2-11,.2):
            margin=1000.;ok=True
            for q in (dist,f['length']-dist):
                s={'point':f['a']+f['t']*q,'normal':f['n'],'tangent':f['t']}
                env=world_poly(unary_union([box(-6.15,-4.5,6.15,4.5),key_plan().buffer(.2)]),s)
                margin=min(margin,env.distance(REAR_CLEAR))
                # Key heads must not hit any of the four diagonals in either tile.
                heads=unary_union([box(-7.55,-2.4,-6.2,2.4),box(6.2,-2.4,7.55,2.4)])
                h=world_poly(heads,s)
                from shapely.affinity import translate
                if h.intersects(unary_union([diags,translate(diags,*(2*f['mid']))])):ok=False
            if not ok or margin<.2:continue
            score=(round(margin,5),-abs(dist-f['length']/4))
            if best is None or score>best[0]:best=(score,float(dist))
        if best is None:raise RuntimeError(f'No safe key sites on edge {e}')
        for ei in (e,e+3):
            g=fs[ei]
            for q in (best[1],g['length']-best[1]):
                out.append(dict(edge=ei,point=(g['a']+g['t']*q).tolist(),normal=g['n'].tolist(),tangent=g['t'].tolist(),rear_relief_margin_mm=best[0][0]))
    return sorted(out,key=lambda s:(s['edge'],s['point']))

def lip_shapes(s):
    shapes=[]
    for sign in (-1,1):
        # Triangular ramps: .3 mm projection over .3 mm rise (45deg).
        pts=[cq.Vector(-LIP_MAX_N,sign*1.4,LIP_LOW),cq.Vector(-LIP_MAX_N,sign*LIP_INNER,LIP_PEAK),cq.Vector(-LIP_MAX_N,sign*1.4,LIP_HIGH)]
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
    for s in sites():bodies.append(d.extrude(world_poly(box(-6.15,-4.5,-.15,4.5),s),5,10))
    body=base.fuse(*bodies).clean()
    cuts=[d.cylinder(2.25,-.1,5.2,x,y) for x,y in d.MOUNTS]
    for s in sites():cuts.append(d.extrude(world_poly(box(-6.25,-SLOT_HALF,.25,SLOT_HALF),s),FLOOR,15.1-FLOOR))
    body=body.cut(*cuts).clean()
    if with_lips:body=body.fuse(*[p for s in sites() for p in lip_shapes(s)]).clean()
    assert body.isValid() and len(body.Solids())==1
    return body

def picked_sites():
    # Two different edges of the same new panel, both adjacent to vertex(60,100).
    return [min([s for s in sites() if s['edge']==e],key=lambda s:np.linalg.norm(np.array(s['point'])-np.array([60,100]))) for e in (0,1)]

def corner_coupons():
    chosen=picked_sites();pts=np.array([s['point'] for s in chosen])
    lo=pts.min(axis=0)-18;hi=pts.max(axis=0)+18
    # Retain the common vertex as well as both connectors.
    lo=np.minimum(lo,[48,88]);hi=np.maximum(hi,[72,112])
    crop=d.extrude(box(*lo,*hi),-.1,15.2)
    p=panel();out=[p.intersect(crop).clean()]
    for e in (0,1):
        v=2*d.frames()[e]['mid'];out.append(p.translate((*v,0)).intersect(crop).clean())
    return [max(s.Solids(),key=lambda q:q.Volume()) for s in out]

def export(name,s):
    assert s.isValid() and len(s.Solids())==1,name
    bb=s.BoundingBox();v=[-bb.xmin,-bb.ymin,-bb.zmin]
    cq.exporters.export(s.translate(v),str(ROOT/'stl'/(name+'.stl')),tolerance=.012,angularTolerance=.08)
    return dict(name=name,size_mm=[bb.xlen,bb.ylen,bb.zlen],volume_cm3=s.Volume()/1000,print_shift_mm=v)

def build():
    for folder in ('stl','step','images','projects'): (ROOT/folder).mkdir(exist_ok=True)
    p=panel();print('Panel CAD ready',flush=True)
    cq.exporters.export(p,str(ROOT/'step'/'S01_hidden_joint_PROTOTYPE.step'))
    parts=[export('spring_key',key())]
    for name,s in zip(('corner_NEW','corner_EXISTING_oblique','corner_EXISTING_horizontal'),corner_coupons()):parts.append(export(name,s))
    a=cq.Assembly();a.add(p,name='new_panel',color=cq.Color(.76,.68,.46))
    for e in (0,1):
        v=2*d.frames()[e]['mid'];a.add(p.translate((*v,0)),name=f'existing_{e}',color=cq.Color(.65,.76,.70))
    for i,s in enumerate([s for s in sites() if s['edge'] in (0,1)]):a.add(local_solid(key(),s),name=f'key_{i}',color=cq.Color(.35,.57,.68))
    a.export(str(ROOT/'step'/'three_panels_assembly.step'))
    report=dict(status='CAD prototype; untested physical snap-fit',parts=parts,sites=sites(),test_sites=picked_sites(),
                dimensions=dict(rim_width_mm=RIM,receiver_local_depth_mm=6,key_mm=[14.7,4.4,2.4],key_seated_z_mm=[9,11.4],
                                slot_width_mm=2.8,retainer_throat_mm=2.2,neck_width_mm=2.4,arm_width_mm=.8,arm_length_mm=ARM_L),
                rear_hook_relief_mm=2,extra_hook_vertical_travel_mm=HOOK_DROP,travel_mirrored_for_180_degrees=True,rear_hook_relief_validated=False,wall_shoes='unchanged approved v4',
                keys_per_join=2,working_slots_consumed=0,front_seam_holes=0,additional_depth_mm=0)
    (ROOT/'parameters.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Exported',len(parts),'parts',flush=True)

if __name__=='__main__':build()
