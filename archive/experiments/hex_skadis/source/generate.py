#!/usr/bin/env python3
"""Hex SKADIS prototype. Millimetres; +Y is UP; front z=0, rear z=5.

The lattice is invariant under (0,200), (180,100), (180,-100).
Only the outer contour is inset for a gap. NEVER scale the finished STL.
Run: python generate.py --out ../
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from functools import lru_cache
import argparse
import json
import math
import csv

import cadquery as cq
from shapely.geometry import Polygon, Point, LineString, box
from shapely.affinity import translate


@dataclass(frozen=True)
class Config:
    width: float = 240.0
    height: float = 200.0
    gap: float = 0.3
    thickness: float = 5.0
    slot_allowance: float = 0.15  # TOTAL increase in width and overall length
    min_web: float = 2.0
    socket_diameter: float = 4.2
    socket_depth: float = 2.1
    pin_clearance: float = 0.2  # diametral, not per side
    pin_height: float = 1.8
    bridge_thickness: float = 3.5
    wall_gap: float = 20.0

    def __post_init__(self):
        for dx, dy in [(0, self.height), (self.width * .75, self.height / 2)]:
            i = dx / 20
            j = (dy - 20 * (round(i) % 2)) / 40
            if abs(i-round(i)) > 1e-8 or abs(j-round(j)) > 1e-8:
                raise ValueError('Module translations must preserve the SKADIS lattice')
        if not (0.15 <= self.gap <= 0.6 and 0 <= self.slot_allowance <= 0.3):
            raise ValueError('Prototype range: gap 0.15..0.6; slot allowance 0..0.3')
        if not (0.1 <= self.pin_clearance <= 0.4):
            raise ValueError('Pin diametral clearance must be 0.1..0.4')
        if self.thickness < 4.5 or self.socket_depth < self.pin_height + 0.2:
            raise ValueError('Insufficient front skin or socket depth')
        if self.socket_depth > self.thickness - 2.4:
            raise ValueError('Blind sockets must leave at least 2.4 mm front skin')
        if self.width != 240 or self.height != 200:
            raise ValueError('Mount and test geometry is validated only for 240 x 200')


def nominal_vertices(c):
    w, h = c.width, c.height
    return [(w/2,0),(w/4,h/2),(-w/4,h/2),(-w/2,0),(-w/4,-h/2),(w/4,-h/2)]


def panel_polygon(c):
    return Polygon(nominal_vertices(c)).buffer(-c.gap/2, join_style=2)


def layout(c):
    return [(q*c.width*.75, r*c.height + q*c.height/2) for q in range(-1,2) for r in range(-1,2)]


def slot_polygon(x, y, c):
    # Increasing both dimensions equally keeps the straight section at 10 mm.
    return LineString([(x,y-5),(x,y+5)]).buffer((5+c.slot_allowance)/2, quad_segs=32)


def edge_frames(c):
    vertices = nominal_vertices(c)
    frames = []
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        length = math.dist(a,b)
        tx,ty = (b[0]-a[0])/length, (b[1]-a[1])/length
        frames.append({'mid':((a[0]+b[0])/2,(a[1]+b[1])/2),
                       'normal':(ty,-tx), 'tangent':(tx,ty)})
    return frames


def edge_point(frame, n, t):
    m, u, v = frame['mid'], frame['normal'], frame['tangent']
    return (m[0]+n*u[0]+t*v[0], m[1]+n*u[1]+t*v[1])


def edge_pin_centres(frame):
    return [edge_point(frame,-8,t) for t in (-7.5,7.5)]


def bridge_world_pins(frame):
    return [edge_point(frame,n,t) for n in (-8,8) for t in (-7.5,7.5)]


def mount_centres():
    # Centres of empty lattice cells: 20 mm from nearest slot centres.
    return [(-60,-70),(60,-70),(-60,50),(60,50)]


def hardware_keepouts(c):
    keep = [Point(x,y).buffer(7) for x,y in mount_centres()]
    for f in edge_frames(c):
        # Keep the full rear connector footprint clear of hooks, not only bores.
        keep.append(Polygon([edge_point(f,n,t) for n,t in [(-15,-14),(0,-14),(0,14),(-15,14)]]))
    return keep


@lru_cache(maxsize=20)
def slot_centres(c):
    # Reserve for the largest supplied slot, so all allowance variants share positions.
    envelope = replace(c, slot_allowance=0.3)
    boundary = panel_polygon(c)
    exclusions = hardware_keepouts(c)
    points=[]
    for i in range(-6,7):
        x=20*i
        for j in range(-4,5):
            y=40*j + 20*(i%2) + 10
            slot=slot_polygon(x,y,envelope)
            if not boundary.covers(slot) or boundary.exterior.distance(slot) < c.min_web-1e-8:
                continue
            if any(slot.distance(k) < c.min_web-1e-8 for k in exclusions):
                continue
            points.append((x,y))
    return tuple(points)


def extrude_polygon(polygon, height, z=0):
    return cq.Workplane('XY',origin=(0,0,z)).polyline(list(polygon.exterior.coords)[:-1]).close().extrude(height).val()


def cylinder(x,y,r,z,height):
    return cq.Solid.makeCylinder(r,height,cq.Vector(x,y,z))


def cut_slots(shape, points, c):
    if not points:
        return shape
    cutters=cq.Workplane('XY',origin=(0,0,-.1)).pushPoints(list(points)).slot2D(15+c.slot_allowance,5+c.slot_allowance,90).extrude(c.thickness+.2)
    return shape.cut(cutters.val()).clean() if len(cutters.vals())==1 else shape.cut(*cutters.vals()).clean()


def engrave(shape, text, x,y,z,size=3.0,depth=.35):
    letters=cq.Workplane('XY',origin=(x,y,z-depth)).text(text,size,depth+.05,combine=False,font='Arial').vals()
    return shape.cut(*letters).clean()


@lru_cache(maxsize=12)
def make_panel(c):
    shape=extrude_polygon(panel_polygon(c),c.thickness)
    shape=cut_slots(shape,slot_centres(c),c)
    cuts=[]
    for f in edge_frames(c):
        for x,y in edge_pin_centres(f):
            cuts.append(cylinder(x,y,c.socket_diameter/2,c.thickness-c.socket_depth,c.socket_depth+.1))
        x,y=edge_point(f,-8,0)
        cuts.append(cylinder(x,y,1.7,-.1,c.thickness+.2))
    for x,y in mount_centres():
        cuts += [cylinder(x,y,2.25,-.1,c.thickness+.2), cylinder(x,y,4.25,-.1,1.6)]
    shape=shape.cut(*cuts).clean()
    # Engrave only the rear. Arrow and text must not intrude into any receiving slot.
    shape=engrave(shape,'UP',0,80,c.thickness,3)
    return shape


def make_bridge(c):
    # Printed flat, pins upwards. Install upside-down against the panel's rear.
    shape=cq.Workplane('XY').rect(30,28).extrude(c.bridge_thickness).edges('|Z').fillet(2).val()
    r=(c.socket_diameter-c.pin_clearance)/2
    pins=[cylinder(n,t,r,c.bridge_thickness,c.pin_height) for n in (-8,8) for t in (-7.5,7.5)]
    shape=shape.fuse(*pins).clean()
    cuts=[]
    for x in (-8,8):
        cuts.append(cylinder(x,0,1.7,-.1,c.bridge_thickness+.2))
        # Across flats 5.7 mm for an ordinary M3 hex nut, 2.5 mm-deep open pocket.
        cuts.append(cq.Workplane('XY',origin=(x,0,-.1)).polygon(6,5.7/math.cos(math.pi/6)).extrude(2.6).val())
    shape=shape.cut(*cuts).clean()
    return engrave(shape,f'{c.pin_clearance:.1f}',0,0,c.bridge_thickness,2.6)


def install_bridge(key, frame, c):
    angle=math.degrees(math.atan2(frame['normal'][1],frame['normal'][0]))
    return key.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),angle).translate((*frame['mid'],c.thickness+c.bridge_thickness))


def make_spacer(c):
    return cq.Workplane('XY').circle(7).circle(2.25).extrude(c.wall_gap).val()


def make_fit_coupon(c):
    base=cq.Workplane('XY').rect(70,70).extrude(c.thickness).edges('|Z').fillet(3).val()
    base=cut_slots(base,[(-20,-20),(20,-20),(0,0),(-20,20),(20,20)],c)
    return engrave(base,f'+{c.slot_allowance:.2f}  UP',0,31,c.thickness,2.7)


def seam_info(direction):
    return {
        'horizontal':(1,(0,200),(-55,60,55,140)),
        'diagonal_up':(0,(180,100),(30,0,150,100)),
        'diagonal_down':(5,(180,-100),(30,-100,150,0)),
    }[direction]


def make_seam_coupons(c,direction):
    edge, shift, bounds=seam_info(direction)
    crop=extrude_polygon(box(*bounds),c.thickness+2,-1)
    panel=make_panel(c)
    pieces=[panel.intersect(crop).clean(),panel.translate((*shift,0)).intersect(crop).clean()]
    # Keep assembly coordinates in CAD. Exporters shift parts onto individual beds.
    return pieces


def on_bed(shape):
    bb=shape.BoundingBox()
    return shape.translate((-bb.xmin,-bb.ymin,-bb.zmin))


def write_part(out,name,shape):
    if not shape.isValid() or len(shape.Solids())!=1:
        raise RuntimeError(f'{name}: invalid or disconnected solid')
    cq.exporters.export(on_bed(shape),str(out/'stl'/f'{name}.stl'),tolerance=.02,angularTolerance=.12)
    cq.exporters.export(shape,str(out/'step'/f'{name}.step'))


def build(out):
    out=Path(out)
    for sub in ['stl','step','validation','projects']:
        (out/sub).mkdir(parents=True,exist_ok=True)
    c=Config()
    panel=make_panel(c)
    write_part(out,'panel_240x200_PROTOTYPE',panel)
    write_part(out,'wall_spacer_20mm',make_spacer(c))
    for allowance in (0.0,.15,.3):
        config=replace(c,slot_allowance=allowance)
        write_part(out,f'fit_slot_plus_{allowance:.2f}',make_fit_coupon(config))
    for clearance in (.1,.2,.4):
        config=replace(c,pin_clearance=clearance)
        write_part(out,f'bridge_clearance_{clearance:.1f}',make_bridge(config))
    for direction in ['horizontal','diagonal_up','diagonal_down']:
        for index,piece in enumerate(make_seam_coupons(c,direction),1):
            write_part(out,f'seam_{direction}_{index}',piece)
    assembly=cq.Assembly(name='Hex_SKADIS_3x3_PROTOTYPE')
    colors=[cq.Color(.86,.73,.47),cq.Color(.24,.37,.39),cq.Color(.76,.79,.75)]
    for i,(x,y) in enumerate(layout(c)):
        assembly.add(panel,loc=cq.Location(cq.Vector(x,y,0)),name=f'panel_{i+1}',color=colors[i%3])
    assembly.export(str(out/'step'/'assembly_3x3.step'))
    with (out/'validation'/'slot_centres.csv').open('w') as file:
        writer=csv.writer(file);writer.writerow(['tile','x_mm','y_mm'])
        for i,(ox,oy) in enumerate(layout(c)):
            writer.writerows((i+1,x+ox,y+oy) for x,y in slot_centres(c))
    (out/'parameters.json').write_text(json.dumps(asdict(c),indent=2)+'\n')
    print(json.dumps({'output':str(out.resolve()),'slots_per_panel':len(slot_centres(c)),
                      'panel_volume_cm3':round(panel.Volume()/1000,2)},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    build(args.out)
