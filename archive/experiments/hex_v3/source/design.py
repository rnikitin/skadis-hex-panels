"""S01 v3 prototype. Coordinates: front z=0, rear positive. Units mm.

Canonical S01 lattice; no aperture is moved/deleted for ribs or hardware.
Real accessory insertion envelopes and adhesive performance remain unverified.
"""
from pathlib import Path
from functools import lru_cache
import json, math
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.affinity import affine_transform

ROOT=Path(__file__).resolve().parent.parent
VERTICES=np.array([(120,0),(60,100),(-60,100),(-120,0),(-60,-100),(60,-100)],float)
FACE=5.; RIB=2.4; HEIGHT=10.; GAP=.3
MOUNTS=[(x,y) for x in (-40.,40.) for y in (-40.,40.)]
CENTRES=[(20*i+20,40*j+20*(i%2)) for i in range(-9,10) for j in range(-6,7)]
P=Polygon(VERTICES).buffer(-GAP/2,join_style=2)
SLOTS=unary_union([LineString([(x,y-5),(x,y+5)]).buffer(2.65,quad_segs=32) for x,y in CENTRES])
FACE_PLAN=P.difference(SLOTS)
LEGACY_CLEAR=unary_union([box(x-8,y-17,x+8,y+17) for x,y in CENTRES])

def pieces(p):
    return [p] if p.geom_type=='Polygon' else [x for x in p.geoms if x.geom_type=='Polygon']

def extrude(p,z,h):
    def wire(r):return cq.Wire.makePolygon([cq.Vector(x,y,z) for x,y in list(r.coords)[:-1]],close=True)
    return cq.Solid.extrudeLinear(wire(p.exterior),[wire(r) for r in p.interiors],cq.Vector(0,0,h))

def cylinder(r,z,h,x=0,y=0):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))

def prism(poly,z,h):return extrude(poly,z,h)

def hexagon(af=5.9):
    # AF measured along y; opening channel below is 5.9 mm wide.
    r=af/math.sqrt(3)
    return Polygon([(r*math.cos(i*math.pi/3),r*math.sin(i*math.pi/3)) for i in range(6)])

def csk(x,y,z=0,depth=FACE):
    shaft=cylinder(1.7,z-.1,depth+.2,x,y)
    cone=cq.Solid.makeCone(3.2,1.7,1.5,cq.Vector(x,y,z))
    return shaft.fuse(cone)

def frames():
    result=[]
    for i,a in enumerate(VERTICES):
        b=VERTICES[(i+1)%6]; length=np.linalg.norm(b-a); t=(b-a)/length; n=np.array([t[1],-t[0]])
        result.append(dict(edge=i,a=a,b=b,t=t,n=n,length=length,mid=(a+b)/2))
    return result

def transform(poly,point,n,t):
    return affine_transform(poly,[n[0],t[0],n[1],t[1],point[0],point[1]])

@lru_cache(None)
def ribs(variant='diamond'):
    rim=P.difference(P.buffer(-3.2,join_style=2)).difference(LEGACY_CLEAR)
    out=[rim]
    if variant!='rim':
        lines=[]
        for c in (-40,40):
            lines.extend([LineString([(-400,400+c),(400,-400+c)]),LineString([(-400,-400-c),(400,400-c)])])
        out += [l.buffer(RIB/2,cap_style=2).intersection(P) for l in lines]
    if variant=='long':
        out += [box(x-1.2,-150,x+1.2,150).intersection(P).difference(LEGACY_CLEAR) for x in (-50,50)]
    return unary_union(out)

@lru_cache(None)
def sites():
    # Same two positions on opposite edges. Reflection and translation invariant.
    fs=frames(); result=[]
    footprint=box(-10.25,-5.25,10.25,5.25)
    for ei in range(3):
        f=fs[ei]; best=None
        for d in np.arange(17,f['length']/2-9,.1):
            margin=1e6
            for q in (d,f['length']-d):
                pt=f['a']+q*f['t']; fp=transform(footprint,pt,f['n'],f['t'])
                bosses=unary_union([Point(pt+f['n']*s).buffer(5) for s in (-5,5)])
                margin=min(margin,fp.distance(SLOTS),bosses.distance(SLOTS))
            score=(round(margin,5),-abs(d-f['length']/4))
            if margin>=1.5 and (best is None or score>best[0]):best=(score,float(d))
        if best is None:raise ValueError(f'No connector sites on edge {ei}')
        for e in (ei,ei+3):
            g=fs[e]
            for q in (best[1],g['length']-best[1]):
                pt=g['a']+q*g['t']
                result.append(dict(edge=e,point=pt.tolist(),normal=g['n'].tolist(),tangent=g['t'].tolist(),slot_margin=best[0][0]))
    return sorted(result,key=lambda v:(v['edge'],v['point']))

@lru_cache(None)
def panel(variant='diamond'):
    base=extrude(P,0,FACE)
    local=[c for c in CENTRES if P.intersects(Point(c).buffer(8))]
    cuts=cq.Workplane('XY',origin=(0,0,-.1)).pushPoints(local).slot2D(15.3,5.3,90).extrude(5.2)
    base=base.cut(*cuts.vals())
    bodies=[extrude(q,FACE,HEIGHT) for q in pieces(ribs(variant)) if q.area>1e-7]
    # Nut receivers grow only to z=8.0, below ribs at z=15.
    for s in sites():
        pt=np.array(s['point'])-5*np.array(s['normal'])
        bodies.append(cylinder(5,5,3,*pt))
    shape=base.fuse(*bodies).clean()
    # Wall attachment uses a pan-head M4 + flat washer, bearing on full face.
    cuts=[cylinder(2.25,-.1,5.2,x,y) for x,y in MOUNTS]
    for s in sites():
        pt=np.array(s['point']);n=np.array(s['normal']);t=np.array(s['tangent']);nut=pt-5*n
        cuts.append(extrude(transform(box(-10.25,-5.25,10.25,5.25),pt,n,t),-.1,2.6))
        cuts.append(cylinder(1.7,2.4,5.8,*nut))
        cuts.append(extrude(transform(hexagon(),nut,n,t),5,3.1))
    shape=shape.cut(*cuts).clean()
    assert shape.isValid() and len(shape.Solids())==1
    return shape

def bridge():
    # Local normal is X. Front is z=.1 after installation, bottom z=2.5.
    shape=cq.Workplane('XY').rect(20,10).extrude(2.4).edges('|Z').fillet(.65).val()
    shape=shape.cut(*[csk(x,0,0,2.4) for x in (-5,5)]).clean()
    return shape

def install(shape,s,z=0):
    angle=math.degrees(math.atan2(s['normal'][1],s['normal'][0]))
    return shape.rotate((0,0,0),(0,0,1),angle).translate((*s['point'],z))

def shoe():
    # Upper shoe: tape centroid 8 mm ABOVE screw; rotate 180deg for lower.
    # Installed z=5..23. Base rear z=23 accepts 30 x 50 tape.
    base=cq.Workplane('XY',origin=(0,8,20)).rect(34,54).extrude(3).edges('|Z').fillet(2).val()
    post=cylinder(6,5,15)
    # Four local buttresses, entirely behind panel ribs, z=15.5..20.
    gussets=[extrude(box(-12,-2,12,2),15.5,4.5),extrude(box(-2,-16,2,28),15.5,4.5)]
    shape=base.fuse(post,*gussets).clean()
    pocket=unary_union([hexagon(7.4),box(0,-3.7,6.2,3.7)])
    # Side-loaded M4 nut under a 2-mm roof. M4x16 with .8 washer ends z15.2.
    shape=shape.cut(extrude(pocket,7,3.6),cylinder(2.25,4.9,12.6)).clean()
    assert shape.isValid() and len(shape.Solids())==1
    return shape

def screw(length,z=0):
    return cq.Solid.makeCone(3,1.5,1.5,cq.Vector(0,0,z)).fuse(cylinder(1.5,z+1.5,length-1.5))

def nut(z,af=5.5,h=2.4,r=1.5):return extrude(hexagon(af),z,h).cut(cylinder(r,z-.1,h+.2))

def wall_screw():
    # Simplified pan-head envelope. DIN7985 M4x16 shank length under head.
    return cylinder(4,-3.9,3.1).fuse(cylinder(2,-.8,16))

def washer():return cylinder(4.5,-.8,.8).cut(cylinder(2.15,-.9,1))

def installed_shoes():
    return [(shoe() if y>0 else shoe().rotate((0,0,0),(0,0,1),180)).translate((x,y,0)) for x,y in MOUNTS]

def mounted_solid(variant='diamond'):
    # Analysis idealization: panel contact annuli bonded to shoe noses.
    s=panel(variant).fuse(*installed_shoes()).clean()
    assert s.isValid() and len(s.Solids())==1
    return s

def coupon(edge):
    s=[s for s in sites() if s['edge']==edge][0]
    p=np.array(s['point']);n=np.array(s['normal']);t=np.array(s['tangent'])
    region=extrude(transform(box(-21,-18,21,18),p,n,t),-.1,15.2)
    f=frames()[edge];shift=2*f['mid']
    # Cropping may isolate tiny pieces beyond an edge slot. They are not part
    # of the fit coupon; retain the connected plate/receiver component only.
    halves=[panel().intersect(region).clean(),panel().translate((*shift,0)).intersect(region).clean()]
    return tuple(max(s.Solids(),key=lambda p:p.Volume()) for s in halves)

def mount_coupon():
    # Two complete slots at (40,20) and (40,60) for a two-row accessory,
    # plus the mounting screw midway between them.
    return panel().intersect(extrude(box(22,8,58,72),-.1,15.2)).clean()

def export(name,shape,rotation=None):
    if rotation:shape=shape.rotate(*rotation)
    assert shape.isValid() and len(shape.Solids())==1,name
    bb=shape.BoundingBox();shift=[-bb.xmin,-bb.ymin,-bb.zmin]
    placed=shape.translate(shift)
    cq.exporters.export(placed,str(ROOT/'stl'/f'{name}.stl'),tolerance=.012,angularTolerance=.08)
    return dict(name=name,size_mm=[bb.xlen,bb.ylen,bb.zlen],volume_cm3=shape.Volume()/1000,export_shift_mm=shift)

def build():
    for d in ('stl','step','analysis','images','projects'): (ROOT/d).mkdir(parents=True,exist_ok=True)
    params=[]
    for variant in ('rim','diamond','long'):
        print('Build',variant,flush=True)
        s=panel(variant)
        cq.exporters.export(s,str(ROOT/'step'/f'S01_{variant}.step'))
        cq.exporters.export(mounted_solid(variant),str(ROOT/'step'/f'S01_{variant}_mounted.step'))
        if variant=='diamond':params.append(export('S01_diamond_v3',s))
    params.append(export('front_bridge_M3x8',bridge()))
    params.append(export('tape_shoe_M4x16',shoe(),((0,0,0),(1,0,0),180)))
    params.append(export('mount_coupon',mount_coupon()))
    for e,label in ((1,'straight'),(0,'oblique')):
        for k,s in enumerate(coupon(e)):params.append(export(f'seam_{label}_{k+1}',s))
    assembly=cq.Assembly()
    assembly.add(panel(),name='S01',color=cq.Color(.64,.74,.69))
    for i,(x,y) in enumerate(MOUNTS):
        foot=shoe() if y>0 else shoe().rotate((0,0,0),(0,0,1),180)
        assembly.add(foot.translate((x,y,0)),name=f'shoe_{i}',color=cq.Color(.8,.6,.3))
        assembly.add(wall_screw().translate((x,y,0)),name=f'mount_screw_{i}',color=cq.Color(.5,.5,.53))
        assembly.add(washer().translate((x,y,0)),name=f'mount_washer_{i}',color=cq.Color(.5,.5,.53))
        assembly.add(nut(7,7,3.2,2).translate((x,y,0)),name=f'mount_nut_{i}',color=cq.Color(.5,.5,.53))
    assembly.export(str(ROOT/'step'/'S01_mounted_assembly.step'))
    # Neighbours across two non-parallel seams; bridges insert along Z only.
    joint=cq.Assembly();joint.add(panel(),name='A')
    for edge in (0,1):
        f=frames()[edge];delta=2*f['mid']
        joint.add(panel().translate((*delta,0)),name=f'neighbour_{edge}')
        for j,s in enumerate([s for s in sites() if s['edge']==edge]):
            joint.add(install(bridge(),s,.1),name=f'bridge_{edge}_{j}',color=cq.Color(.8,.6,.3))
            for side in (-1,1):
                joint.add(install(screw(8,.3).translate((5*side,0,0)),s),name=f'bridge_screw_{edge}_{j}_{side}',color=cq.Color(.5,.5,.53))
                joint.add(install(nut(5).translate((5*side,0,0)),s),name=f'bridge_nut_{edge}_{j}_{side}',color=cq.Color(.5,.5,.53))
    joint.export(str(ROOT/'step'/'three_panels_joined.step'))
    report=dict(prototype=True,face_mm=FACE,rib_width_mm=RIB,rib_height_mm=HEIGHT,gap_mm=GAP,
                mounts_mm=MOUNTS,tape_shoe_mm=[34,54,18],tape_strip_mm=[30,50],tape_centroid_offset_mm=8,
                front_to_tape_mm=23,connector_sites=sites(),parts=params,
                hook_body_clearance='Actual accessories and installation sweep NOT VERIFIED',
                tape_capacity='NOT ASSIGNED',physical_fit='NOT TESTED')
    (ROOT/'parameters.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Exported',len(params),'printable parts',flush=True)

if __name__=='__main__':build()
