"""Mirror-symmetric contours AND hole patterns; split slots may have two owners.

This mode preserves every cutout, including fragments whose centre is outside
the tile. It verifies both the ideal assembled plane and the actual 0.3 mm seams.
Seam openings are geometrically reconstructed, not mechanically certified.
"""
from pathlib import Path
from dataclasses import asdict
import json
import math
import time
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.affinity import translate, scale
from shapely.ops import unary_union
from search import Settings, in_lattice, points_in_bounds, capsule, regularity

EPS=1e-6


def assess(vertices,phase,u,v,cfg):
    nominal=Polygon(vertices)
    if not nominal.is_valid or nominal.area<=0 or nominal.convex_hull.area-nominal.area>EPS:
        raise ValueError('Contour must be convex')
    if max(np.ptp(vertices,axis=0))>cfg.max_size+1e-8:raise ValueError('Outside print envelope')
    if not in_lattice(u) or not in_lattice(v):raise ValueError('Translation breaks lattice')
    if not (in_lattice((2*phase[0],0)) and in_lattice((0,2*phase[1]))):
        raise ValueError('Grid lacks mirror symmetry')
    for x,y in [(-1,1),(1,-1)]:
        if nominal.symmetric_difference(scale(nominal,xfact=x,yfact=y,origin=(0,0))).area>EPS:
            raise ValueError('Contour lacks mirror symmetry')
    equivalent=round(nominal.area/800)
    if abs(nominal.area/800-equivalent)>1e-7 or equivalent<cfg.min_slots:
        raise ValueError('Insufficient lattice area')
    panel=nominal.buffer(-cfg.gap/2,join_style=2)
    centres=[];slots=[];whole=[];partial=[];maxowners=0
    u,v=np.array(u),np.array(v)
    neighbours=[translate(nominal,*o) for o in [np.zeros(2),u,-u,v,-v,v-u,u-v]]
    for p in points_in_bounds(nominal.bounds,phase):
        slot=capsule(p,cfg)
        if nominal.intersection(slot).area<=EPS:continue
        owners=sum(t.intersection(slot).area>EPS for t in neighbours)
        maxowners=max(maxowners,owners)
        if owners>2:raise ValueError('Slot has three or more owners')
        if panel.intersection(slot).area<=EPS:raise ValueError('Gap consumes a slot fragment')
        centres.append(list(p));slots.append(slot)
        if nominal.covers(slot):
            if not panel.covers(slot) or panel.exterior.distance(slot)<cfg.min_web-1e-7:
                raise ValueError('Whole slot too close to edge')
            whole.append(slot)
        else:
            if owners!=2:raise ValueError('Split slot must have exactly two owners')
            partial.append(list(p))
    if not centres:raise ValueError('No openings')
    body=panel.difference(unary_union(slots))
    if body.geom_type!='Polygon':raise ValueError('Cutouts create detached material')
    vertex_clearance=min(Point(*p).distance(slot) for p in vertices for slot in slots)
    if vertex_clearance<cfg.min_web:raise ValueError('Cutout too close to a corner')
    for x,y in [(-1,1),(1,-1)]:
        if body.symmetric_difference(scale(body,xfact=x,yfact=y,origin=(0,0))).area>EPS:
            raise ValueError('Perforated body lacks symmetry')
    dims=np.ptp(vertices,axis=0)
    return {'vertices':np.asarray(vertices).tolist(),'phase':list(phase),'u':u.tolist(),'v':v.tolist(),
            'width_mm':float(dims[0]),'height_mm':float(dims[1]),
            'equivalent_slots_per_tile':equivalent,'whole_slots':len(whole),'slot_fragments':len(partial),
            'local_centres':centres,'partial_centres':partial,'max_slot_owners':maxowners,
            'mirror_x':True,'mirror_y':True,'rotation_180':True,
            'whole_slot_min_web_mm':min((panel.exterior.distance(p) for p in whole),default=None),
            'min_corner_clearance_mm':vertex_clearance,'regular_error_pct':100*regularity(vertices)}


def verify_assembly(vertices,phase,u,v,local_centres,cfg):
    if not in_lattice(u) or not in_lattice(v):raise ValueError('Translation breaks lattice')
    nominal=Polygon(vertices);inset=nominal.buffer(-cfg.gap/2,join_style=2)
    actual_cutters=unary_union([capsule(p,cfg) for p in local_centres])
    offsets=[q*np.array(u)+r*np.array(v) for q in range(-1,2) for r in range(-1,2)]
    nominal_tiles=[translate(nominal,*o) for o in offsets]
    nominal_union=unary_union(nominal_tiles)
    if abs(nominal_union.area-9*nominal.area)>EPS:raise ValueError('Overlapping tiles')
    gapped_union=unary_union([translate(inset,*o) for o in offsets])
    reference_slots=[capsule(p,cfg) for p in points_in_bounds(nominal_union.bounds,phase)]
    global_cutters=unary_union([s for s in reference_slots if nominal_union.intersects(s)])
    actual_nominal=unary_union([translate(nominal.difference(actual_cutters),*o) for o in offsets])
    actual_gapped=unary_union([translate(inset.difference(actual_cutters),*o) for o in offsets])
    nominal_error=actual_nominal.symmetric_difference(nominal_union.difference(global_cutters)).area
    gapped_error=actual_gapped.symmetric_difference(gapped_union.difference(global_cutters)).area
    if nominal_error>EPS or gapped_error>EPS:raise ValueError('Missing slot fragment: reconstruction failed')
    return {'nominal_reconstruction_error_mm2':nominal_error,'gapped_reconstruction_error_mm2':gapped_error,
            'complete_openings_inside_3x3':sum(nominal_union.covers(s) for s in reference_slots),
            'physical_seam_fit':'UNTESTED; seam creates an open slit through shared holes'}


def family(C,H,A,orientation):
    B=C-A
    v=np.array([(A,0),(B,H/2),(-B,H/2),(-A,0),(-B,-H/2),(B,-H/2)],float)
    if orientation=='flat_top':return v,(C,H/2),(0,H)
    return np.column_stack((-v[:,1],v[:,0])),(H,0),(H/2,C)


def run(cfg,out,step=.5):
    if step<=0:raise ValueError('shape-step must be positive')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();records=[];tried=0
    for m in range(1,int(cfg.max_size//40)+1):
        H=40*m
        for n in range(1,int(cfg.max_size//20)+1):
            if (m-n)%2 or m*n<cfg.min_slots:continue
            C=20*n;low=C/2+3;high=min(C-5,cfg.max_size/2)
            if low>=high:continue
            values=list(np.arange(low,high+1e-8,step))+[min(high,max(low,2*C/3))]
            values=sorted(set(values),key=lambda a:regularity(family(C,H,a,'flat_top')[0]))
            for orientation in ['flat_top','point_top']:
                for phase in [(0,0),(20,0)]:
                    for A in values:
                        vertices,u,v=family(C,H,A,orientation);tried+=1
                        try:r=assess(vertices,phase,u,v,cfg)
                        except ValueError:continue
                        try:r['verification']=verify_assembly(vertices,phase,u,v,r['local_centres'],cfg)
                        except ValueError:continue
                        r['orientation']=orientation;records.append(r);break
    records.sort(key=lambda r:(round(r['regular_error_pct'],8),r['slot_fragments']/r['equivalent_slots_per_tile'],-r['equivalent_slots_per_tile']))
    for i,r in enumerate(records,1):r['id']=f'S{i:02}'
    report={'mode':'symmetric-split','settings':asdict(cfg),'shape_step_mm':step,
            'scope':'Horizontal/vertical mirror axes; both flat-top and point-top contours; fixed symmetric grid phases',
            'tested_configurations':tried,'elapsed_seconds':time.monotonic()-start,
            'global_optimality_proven':False,'results':records}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    draw_results(records,out,cfg)
    print(json.dumps({'tested':tried,'feasible_families':len(records),
                     'best':{k:records[0][k] for k in ['id','width_mm','height_mm','whole_slots','slot_fragments','regular_error_pct']} if records else None,
                     'seconds':round(time.monotonic()-start,2)},indent=2),flush=True)
    return report


def draw_results(records,out,cfg):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as MPath
    from matplotlib.patches import PathPatch
    bg='#f4f1e9';ink='#233939';colors=['#7d9d98','#c5a56d','#a7b6a2','#99aca6']
    def body(r):
        return Polygon(r['vertices']).buffer(-cfg.gap/2,join_style=2).difference(unary_union([capsule(p,cfg) for p in r['local_centres']]))
    def patch(ax,shape,color):
        paths=[]
        for ring in [shape.exterior,*shape.interiors]:
            xy=np.array(ring.coords);codes=[MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY]
            paths.append(MPath(xy,codes))
        ax.add_patch(PathPatch(MPath.make_compound_path(*paths),facecolor=color,edgecolor=ink,lw=.55))
    chosen=[];seen=set()
    for r in records:
        key=(round(r['width_mm']),round(r['height_mm']))
        if key in seen:continue
        seen.add(key);chosen.append(r)
        if len(chosen)==6:break
    fig,axes=plt.subplots(2,3,figsize=(15,10),facecolor=bg)
    fig.subplots_adjust(left=.04,right=.97,top=.84,bottom=.10,hspace=.40,wspace=.13)
    fig.text(.04,.951,'SYMMETRIC HEXES · SPLIT SEAM SLOTS',fontsize=25,weight='bold',color=ink)
    fig.text(.04,.906,'Symmetric outline and hole pattern. Each split slot belongs to exactly two tiles.',fontsize=11,color=ink)
    for ax in axes.flat:ax.axis('off');ax.set_aspect('equal')
    for ax,r in zip(axes.flat,chosen):
        patch(ax,body(r),colors[0]);ax.set_xlim(-132,132);ax.set_ylim(-132,132)
        ax.set_title(f"{r['id']} · {r['width_mm']:.1f} × {r['height_mm']:.1f} mm\nDeviation from a regular hexagon {r['regular_error_pct']:.2f}%",fontsize=12,color=ink,pad=9)
        ax.text(.5,-.10,f"{r['whole_slots']} complete slots + {r['slot_fragments']} fragments\nA180deg rotation preserves the outline and lattice",ha='center',fontsize=10,color=ink,transform=ax.transAxes)
    fig.text(.04,.045,'All candidates reconstruct the lattice in a3x3 assembly. Fragments are parts of slots.',fontsize=10,color=ink)
    fig.text(.04,.020,'The0.30mm seam leaves a gap in split slots. Fixation, ribs and physical fit remain to verify.',fontsize=10,color=ink)
    fig.savefig(out/'gallery.png',dpi=145,facecolor=bg);plt.close(fig)
    if not records:return
    r=records[0];shape=body(r)
    fig,axes=plt.subplots(1,2,figsize=(13,7),facecolor=bg)
    fig.subplots_adjust(left=.035,right=.97,top=.79,bottom=.13,wspace=.18)
    fig.text(.04,.94,f"{r['id']} · NEAR-ORIGINAL OUTLINE, COMPLETE LATTICE",fontsize=23,weight='bold',color=ink)
    for ax in axes:ax.axis('off');ax.set_aspect('equal')
    patch(axes[0],shape,colors[0]);axes[0].set_xlim(-140,140);axes[0].set_ylim(-140,140)
    axes[0].set_title('One tile · mirror symmetry',fontsize=12,color=ink)
    offsets=[q*np.array(r['u'])+t*np.array(r['v']) for q in range(2) for t in range(2)]
    tiles=[translate(shape,*o) for o in offsets]
    for i,tile in enumerate(tiles):patch(axes[1],tile,colors[i%4])
    bounds=unary_union(tiles).bounds
    axes[1].set_xlim(bounds[0]-10,bounds[2]+10);axes[1].set_ylim(bounds[1]-10,bounds[3]+10)
    axes[1].set_title('2x2 assembly · slot fragments join',fontsize=11,color=ink)
    fig.text(.04,.060,f"{r['whole_slots']} complete slots + {r['slot_fragments']} fragments per tile · no slot crosses three tiles",fontsize=11,color=ink)
    fig.text(.04,.025,'Geometry checked. Ribs and a two-row accessory test on a fixed seam are still required.',fontsize=10,color=ink)
    fig.savefig(out/'assembly.png',dpi=150,facecolor=bg);plt.close(fig)
