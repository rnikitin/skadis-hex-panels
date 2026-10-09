#!/usr/bin/env python3
"""Hidden replaceable butterfly keys in reinforced perimeter ribs.

Prototypes, not load-rated hardware. Rear key withdrawal is friction-retained;
the dovetail shoulders resist in-plane separation. Assemble face down first.
"""
from pathlib import Path
from functools import lru_cache
import json,math
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parent.parent
FACE=5.;RIB_HEIGHT=10.;RIB_WIDTH=2.4;PERIMETER_WIDTH=3.2;GAP=.3
SOCKET_DEPTH=5.2;SOCKET_CLEARANCE=.10;KEY_DEPTH=5.;CAP_HEIGHT=1.4
KEY_VERTICES=[(-1.8,-1.2),(-.15,-.55),(.15,-.55),(1.8,-1.2),(1.8,1.2),(.15,.55),(-.15,.55),(-1.8,1.2)]
FITS={'loose':-.06,'normal':0.,'tight':.06}


@lru_cache(maxsize=1)
def designs():return json.loads(Path(__file__).with_name('designs.json').read_text())


def outline(name):return Polygon(designs()[name]['vertices']).buffer(-GAP/2,join_style=2)


@lru_cache(maxsize=3)
def clearance_centres(name):
    p=outline(name);px,py=designs()[name]['phase']
    return [(20*i+px,40*j+20*(i%2)+py) for i in range(-9,10) for j in range(-6,7)
            if p.intersects(box(20*i+px-8,40*j+20*(i%2)+py-17,20*i+px+8,40*j+20*(i%2)+py+17))]


@lru_cache(maxsize=3)
def clear_plan(name):return unary_union([box(x-8,y-17,x+8,y+17) for x,y in clearance_centres(name)])


@lru_cache(maxsize=3)
def rib_plan(name):
    p=outline(name)
    strips=[p.difference(p.buffer(-PERIMETER_WIDTH,join_style=2))]
    strips += [box(x-RIB_WIDTH/2,-150,x+RIB_WIDTH/2,150) for x in range(-170,171,20)]
    strips += [box(-150,y-RIB_WIDTH/2,150,y+RIB_WIDTH/2) for y in range(-140,141,20)]
    return unary_union(strips).intersection(p).difference(clear_plan(name))


def extrude(poly,z,height):
    def wire(r):return cq.Wire.makePolygon([cq.Vector(x,y,z) for x,y in list(r.coords)[:-1]],close=True)
    return cq.Solid.extrudeLinear(wire(poly.exterior),[wire(r) for r in poly.interiors],cq.Vector(0,0,height))


def polygon_parts(poly):return [poly] if poly.geom_type=='Polygon' else list(poly.geoms)


def frames(name):
    vs=np.array(designs()[name]['vertices']);result=[]
    for k in range(6):
        a,b=vs[k],vs[(k+1)%6];length=float(np.linalg.norm(b-a));t=(b-a)/length
        result.append({'a':a,'b':b,'length':length,'tangent':t,'normal':np.array([t[1],-t[0]]),'mid':(a+b)/2})
    return result


def transform_poly(poly,point,normal,tangent):
    return Polygon([np.array(point)+normal*x+tangent*y for x,y in poly.exterior.coords])


@lru_cache(maxsize=3)
def sites(name):
    fs=frames(name);free=clear_plan(name);p=outline(name);rib=rib_plan(name)
    body=Polygon(KEY_VERTICES).buffer(SOCKET_CLEARANCE,join_style=2)
    choices=[]
    for edge in range(3):
        f=fs[edge];L=f['length'];best=None
        for d in np.arange(12,L/2-8,.025):
            distances=[float(d),float(L-d)];margins=[];ok=True
            for loc in distances:
                point=f['a']+loc*f['tangent']
                pocket=transform_poly(body,point,f['normal'],f['tangent'])
                margin=pocket.distance(free)
                if margin<.4-1e-8:ok=False;break
                if pocket.intersection(p).difference(rib).area>1e-7:ok=False;break
                margins.append(margin)
            if not ok:continue
            # Quantised score makes reflected edges select identical sites.
            score=(round(min(margins),7),-abs(d-L/4))
            if best is None or score>best[0]:best=(score,distances)
        if best is None:raise RuntimeError(f'{name} edge {edge}: no safe socket positions')
        choices.append(best[1])
    result=[]
    for edge in range(6):
        f=fs[edge]
        for loc in choices[edge%3]:
            point=f['a']+loc*f['tangent']
            pocket=transform_poly(body,point,f['normal'],f['tangent'])
            result.append({'edge':edge,'point':point.tolist(),'normal':f['normal'].tolist(),
                           'tangent':f['tangent'].tolist(),'wall_clearance':float(pocket.distance(free))})
    return result


@lru_cache(maxsize=3)
def make_panel(name):
    base=extrude(outline(name),0,FACE)
    cuts=cq.Workplane('XY',origin=(0,0,-.1)).pushPoints(designs()[name]['local_centres']).slot2D(15.3,5.3,90).extrude(FACE+.2)
    base=base.cut(*cuts.vals()).clean()
    ribs=[extrude(p,FACE,RIB_HEIGHT) for p in polygon_parts(rib_plan(name)) if p.area>1e-6]
    shape=base.fuse(*ribs).clean()
    pocket=Polygon(KEY_VERTICES).buffer(SOCKET_CLEARANCE,join_style=2)
    sockets=[extrude(transform_poly(pocket,s['point'],np.array(s['normal']),np.array(s['tangent'])),FACE+RIB_HEIGHT-SOCKET_DEPTH,SOCKET_DEPTH+.1) for s in sites(name)]
    shape=shape.cut(*sockets).clean()
    if not shape.isValid() or len(shape.Solids())!=1:raise RuntimeError(name+' is not a single valid solid')
    return shape


def make_key(fit='normal'):
    cap=cq.Workplane('XY').rect(6.8,8).extrude(CAP_HEIGHT).edges('|Z').fillet(.7).val()
    body=extrude(Polygon(KEY_VERTICES).buffer(FITS[fit],join_style=2),CAP_HEIGHT,KEY_DEPTH)
    body=cq.Workplane(obj=body).faces('>Z').edges().chamfer(.10).val()
    result=cap.fuse(body).clean()
    label={'loose':'L','normal':'N','tight':'T'}[fit]
    text=cq.Workplane('XY',origin=(0,0,-.05)).text(label,3,.35,combine=False,font='Arial').vals()
    return result.cut(*text).clean()


def install_key(key,site):
    n=site['normal'];angle=math.degrees(math.atan2(n[1],n[0]))
    return key.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),angle).translate((*site['point'],FACE+RIB_HEIGHT+CAP_HEIGHT))


def hook_clearance_solid(name):
    return cq.Compound.makeCompound([extrude(box(x-8,y-17,x+8,y+17),FACE+.01,RIB_HEIGHT-.02) for x,y in clearance_centres(name)])


def coupons(name,edge):
    f=frames(name)[edge];panel=make_panel(name)
    local=[s for s in sites(name) if s['edge']==edge]
    t=[float(np.dot(np.array(s['point'])-f['mid'],f['tangent'])) for s in local]
    rect=transform_poly(box(-16,min(t)-12,16,max(t)+12),f['mid'],f['normal'],f['tangent'])
    crop=extrude(rect,-.1,FACE+RIB_HEIGHT+.2)
    shift=[2*x for x in f['mid']]
    return [panel.intersect(crop).clean(),panel.translate((*shift,0)).intersect(crop).clean()]


def export_part(name,shape):
    if not shape.isValid() or len(shape.Solids())!=1:raise RuntimeError(name+' invalid or disconnected')
    bb=shape.BoundingBox();onbed=shape.translate((-bb.xmin,-bb.ymin,-bb.zmin))
    cq.exporters.export(onbed,str(ROOT/(name+'.stl')),tolerance=.015,angularTolerance=.10)
    return {'file':name+'.stl','size_mm':[bb.xlen,bb.ylen,bb.zlen],'volume_cm3':shape.Volume()/1000,
            'export_shift_mm':[-bb.xmin,-bb.ymin,-bb.zmin]}


def build():
    parts=[]
    for name in ['S01','S02','S06']:
        print('Panel',name,flush=True)
        parts.append(export_part(name+'_connectable',make_panel(name)))
    for fit in FITS:parts.append(export_part('key_'+fit,make_key(fit)))
    for kind,name,edge in [('straight','S01',1),('diagonal','S02',0)]:
        for i,s in enumerate(coupons(name,edge),1):parts.append(export_part('fit_'+kind+'_'+str(i),s))
    report={'prototype':True,'face_mm':FACE,'rib_height_mm':RIB_HEIGHT,'perimeter_rib_width_mm':PERIMETER_WIDTH,
            'internal_rib_width_mm':RIB_WIDTH,'socket_depth_mm':SOCKET_DEPTH,'key_depth_mm':KEY_DEPTH,
            'installed_height_mm':FACE+RIB_HEIGHT+CAP_HEIGHT,'rear_working_corridor_mm':[16,34,10],
            'retention':'Dovetail shoulders resist in-plane separation; removal toward rear is friction-retained.',
            'physical_fit':'NOT TESTED','parts':parts,'sites':{n:sites(n) for n in designs()}}
    (ROOT/'parameters.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Exported',len(parts),'parts',flush=True)


if __name__=='__main__':build()
