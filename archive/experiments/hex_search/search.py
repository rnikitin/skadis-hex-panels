#!/usr/bin/env python3
"""Search lattice-compatible hex tiles, then prove that no slots were dropped.

Discrete layer: neighbour translations u,v belong to the actual SKADIS lattice.
Continuous layer: a centrally symmetric convex hexagon with vertices
u-p, p, v-p, -u+p, -p, -v+p; optimise p and the slot-grid origin.
This explores tilted outlines as well as axis-aligned ones.
It is a bounded heuristic search, NOT a proof of global optimality.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
import argparse
import csv
import json
import math
import time
import numpy as np
from scipy.optimize import differential_evolution
from shapely.geometry import Polygon, Point, LineString
from shapely.affinity import translate
from shapely.ops import unary_union


@dataclass(frozen=True)
class Settings:
    max_size: float = 248.0
    min_web: float = 2.0
    min_slots: int = 8
    gap: float = .3
    slot_width: float = 5.3
    slot_length: float = 15.3
    basis_limit: int = 100
    iterations: int = 80
    seed: int = 1729

    def __post_init__(self):
        if not (40<=self.max_size<=500 and self.min_web>=0 and self.min_slots>=1):
            raise ValueError('Invalid size, web or slot-count limits')
        if not (0<=self.gap<5 and 0<self.slot_width<=self.slot_length):
            raise ValueError('Invalid gap or slot dimensions')
        if self.basis_limit<1 or self.iterations<1:raise ValueError('Search budgets must be positive')


def in_lattice(point):
    x,y=point;i=round(x/20)
    return abs(x-20*i)<1e-7 and abs((y-20*(i%2))/40-round((y-20*(i%2))/40))<1e-7


def hexagon(u,v,p):
    u,v,p=map(lambda x:np.asarray(x,float),(u,v,p))
    return np.array([u-p,p,v-p,-u+p,-p,-v+p])


def regularity(vertices):
    """RMS residual / RMS radius after fitting the best regular hexagon."""
    z=np.asarray(vertices)[:,0]+1j*np.asarray(vertices)[:,1]
    z=z-z.mean();reference=np.exp(1j*np.arange(6)*math.pi/3)
    alpha=np.mean(z*np.conj(reference))
    return float(np.linalg.norm(z-alpha*reference)/max(np.linalg.norm(z),1e-12))


@lru_cache(maxsize=8)
def local_lattice(max_size):
    ni=math.ceil(max_size/40)+3;nj=math.ceil(max_size/80)+3
    return np.array([(20*i,40*j+20*(i%2)) for i in range(-ni,ni+1) for j in range(-nj,nj+1)],float)


def points_in_bounds(bounds,phase):
    x0,y0,x1,y1=bounds;px,py=phase
    points=[]
    for i in range(math.floor((x0-px)/20)-1,math.ceil((x1-px)/20)+2):
        for j in range(math.floor((y0-py-20*(i%2))/40)-1,math.ceil((y1-py-20*(i%2))/40)+2):
            points.append((20*i+px,40*j+20*(i%2)+py))
    return points


def evaluate(vertices,phase,cfg):
    v=np.asarray(vertices,float)
    if v.shape!=(6,2) or not np.all(np.isfinite(v)):raise ValueError('Invalid vertices')
    e=np.roll(v,-1,axis=0)-v
    cross=e[:,0]*np.roll(e,-1,axis=0)[:,1]-e[:,1]*np.roll(e,-1,axis=0)[:,0]
    lengths=np.linalg.norm(e,axis=1)
    if np.min(cross)<=1e-7 or np.min(lengths)<5:raise ValueError('Non-convex or degenerate hexagon')
    normals=np.column_stack((e[:,1],-e[:,0]))/lengths[:,None]
    dims=np.ptp(v,axis=0)
    if max(dims)>cfg.max_size+1e-7:raise ValueError('Outside print envelope')
    area=.5*np.sum(v[:,0]*np.roll(v,-1,axis=0)[:,1]-v[:,1]*np.roll(v,-1,axis=0)[:,0])
    points=local_lattice(cfg.max_size)+np.asarray(phase)
    d=np.sum(v*normals,axis=1)[None,:]-points@normals.T
    inside=d.min(axis=1)>1e-8
    support=cfg.slot_width/2+(cfg.slot_length-cfg.slot_width)/2*np.abs(normals[:,1])
    count=int(inside.sum());required=int(round(area/800))
    if abs(area/800-required)>1e-6 or count!=required or count<cfg.min_slots:
        raise ValueError('Missing or boundary-centred lattice positions')
    web=float((d[inside]-support[None,:]).min()-cfg.gap/2)
    angles=180-np.degrees(np.arccos(np.clip(np.sum(e*np.roll(e,-1,axis=0),axis=1)/(lengths*np.roll(lengths,-1)),-1,1)))
    return {'count':count,'web_mm':web,'width_mm':float(dims[0]),'height_mm':float(dims[1]),
            'area_mm2':float(area),'regular_error_pct':100*regularity(v),
            'side_min_mm':float(lengths.min()),'side_max_mm':float(lengths.max()),
            'angle_min_deg':float(angles.min()),'angle_max_deg':float(angles.max()),
            'holes':points[inside].tolist()}


def capsule(point,cfg):
    x,y=point;half=(cfg.slot_length-cfg.slot_width)/2
    return LineString([(x,y-half),(x,y+half)]).buffer(cfg.slot_width/2,quad_segs=64)


def verify(vertices,phase,u,v,cfg):
    """Independent Shapely checks, including holes outside the candidate outline."""
    if not in_lattice(u) or not in_lattice(v):raise ValueError('Translation breaks SKADIS lattice')
    ev=evaluate(vertices,phase,cfg)
    if ev['web_mm']<cfg.min_web-1e-8:raise ValueError('Insufficient material at edge')
    nominal=Polygon(vertices);panel=nominal.buffer(-cfg.gap/2,join_style=2)
    for p in points_in_bounds(nominal.bounds,phase):
        slot=capsule(p,cfg)
        if panel.intersects(slot) and not panel.covers(slot):raise ValueError('Cut receiving slot')
    for p in ev['holes']:
        slot=capsule(p,cfg)
        if not panel.covers(slot) or panel.exterior.distance(slot)<cfg.min_web-1e-6:
            raise ValueError('Missing whole slot or insufficient web')
    offsets=[q*np.array(u)+r*np.array(v) for q in range(-1,2) for r in range(-1,2)]
    tiles=[translate(nominal,*o) for o in offsets]
    joined=unary_union(tiles)
    if abs(joined.area-9*nominal.area)>1e-5:raise ValueError('Overlapping tile bodies')
    key=lambda p:tuple(round(float(a),7) for a in p)
    actual={key(np.asarray(p)+o) for o in offsets for p in ev['holes']}
    expected={key(p) for p in points_in_bounds(joined.bounds,phase) if joined.covers(Point(*p))}
    if actual!=expected or len(actual)!=9*ev['count']:raise ValueError('Missing or duplicated assembly slots')
    # Check real opposite edges and actual normal gap in every neighbour direction.
    gaps=[]
    for t in [np.array(u),np.array(v),np.array(v)-np.array(u)]:
        distance=panel.distance(translate(panel,*t))
        if abs(distance-cfg.gap)>1e-5:raise ValueError('Non-mating tile edges')
        gaps.append(float(distance))
    return {'missing':0,'crossed':0,'slots_3x3':len(actual),'normal_gaps_mm':gaps}


def make_record(vertices,phase,u,v,cfg):
    ev=evaluate(vertices,phase,cfg);proof=verify(vertices,phase,u,v,cfg)
    holes={tuple(np.round(p,7)) for p in ev['holes']}
    return ev|{'vertices':np.asarray(vertices).tolist(),'phase':list(map(float,phase)),
               'u':list(map(float,u)),'v':list(map(float,v)),
               'rotation_180':holes=={(-x,-y) for x,y in holes},'verification':proof}


def optimise_basis(u,v,cfg,seed):
    u,v=np.array(u,float),np.array(v,float)
    centre=(u+v)/3
    delta=.38*np.mean([np.linalg.norm(u),np.linalg.norm(v),np.linalg.norm(v-u)])/math.sqrt(3)
    def objective(x):
        vertices=hexagon(u,v,centre+x[:2])
        try:ev=evaluate(vertices,x[2:],cfg)
        except ValueError:return 1e5+100*regularity(vertices)
        shortage=max(0,cfg.min_web+.08-ev['web_mm'])
        return 1000*shortage*shortage+ev['regular_error_pct']
    bounds=[(-delta,delta),(-delta,delta),(0,20),(0,40)]
    x0=None
    if np.allclose(u,[160,0]) and np.allclose(v,[80,160]):
        x0=[0,-13.3333333333333,6.25,20]
    result=differential_evolution(objective,bounds,seed=seed,popsize=12,
                                 maxiter=cfg.iterations,tol=1e-7,polish=True,x0=x0,workers=1)
    candidates=[result.x]+([np.array(x0)] if x0 is not None else [])
    valid=[]
    for x in candidates:
        try:valid.append(make_record(hexagon(u,v,centre+x[:2]),x[2:],u,v,cfg))
        except ValueError:pass
    if not valid:return None
    return min(valid,key=lambda r:r['regular_error_pct'])


def enumerate_bases(cfg):
    lim=int(math.ceil(cfg.max_size/20))+2
    vectors=[np.array((20*i,20*j),float) for i in range(-lim,lim+1) for j in range(0,lim+1)
             if (i-j)%2==0 and (i or j)]
    buckets={};seen=set()
    for u in vectors:
        a=math.degrees(math.atan2(u[1],u[0]));nu=np.linalg.norm(u)
        if not(0<=a<60 and 50<=nu<=cfg.max_size*1.25):continue
        for v in vectors:
            b=math.degrees(math.atan2(v[1],v[0]));nv=np.linalg.norm(v)
            if not(42<=b-a<=80 and .65<=nu/nv<=1.55):continue
            area=u[0]*v[1]-u[1]*v[0];count=round(area/800)
            if count<cfg.min_slots or area>cfg.max_size**2:continue
            vertices=hexagon(u,v,(u+v)/3)
            if max(np.ptp(vertices,axis=0))>cfg.max_size*1.12:continue
            key=tuple(u)+tuple(v)
            if key in seen:continue
            seen.add(key)
            group=(min(3,count//16),int(a//15))
            buckets.setdefault(group,[]).append((regularity(vertices),tuple(u),tuple(v)))
    for group in buckets:buckets[group].sort()
    # Keep small modules and different orientations in the budget, not just large approximants.
    selected=[];round_=0
    while len(selected)<cfg.basis_limit:
        added=0
        for key in sorted(buckets):
            if round_<len(buckets[key]):
                selected.append(buckets[key][round_][1:]);added+=1
                if len(selected)==cfg.basis_limit:break
        if not added:break
        round_+=1
    control=((160.,0.),(80.,160.))
    try:
        check=evaluate(hexagon(*control,[80,40]),(6.25,20),cfg)
        if check['web_mm']>=cfg.min_web and control not in selected:selected.append(control)
    except ValueError:pass
    return selected,len(seen)


def pareto(records):
    return [r for r in records if not any(
        s['regular_error_pct']<=r['regular_error_pct'] and s['count']>=r['count'] and s['web_mm']>=r['web_mm']
        and (s['regular_error_pct']<r['regular_error_pct'] or s['count']>r['count'] or s['web_mm']>r['web_mm'])
        for s in records if s is not r)]


def gallery(records,control,out,cfg):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch
    ranked=sorted(records,key=lambda r:r['regular_error_pct'])
    chosen=[];bins=set()
    for r in ranked:
        key=(round(r['width_mm']/15),round(r['height_mm']/15),r['count'])
        if key in bins:continue
        bins.add(key);chosen.append(r)
        if len(chosen)==(8 if control else 9):break
    chosen=([control] if control else [])+chosen
    bg='#f4f1e9';ink='#243838'
    rows=max(1,math.ceil(len(chosen)/3))
    fig,axes=plt.subplots(rows,3,figsize=(15,4.5*rows+1),facecolor=bg,squeeze=False)
    fig.subplots_adjust(left=.04,right=.975,top=.88,bottom=.07,hspace=.43,wspace=.16)
    fig.text(.04,.954,'SEARCH FOR A NEAR-REGULAR HEXAGON',fontsize=23,weight='bold',color=ink)
    fig.text(.04,.922,'Lower error is closer to equal sides and120deg angles. All displayed shapes passed lattice checks.',fontsize=11,color=ink)
    for ax in axes.flat:ax.axis('off');ax.set_aspect('equal')
    if not chosen:
        fig.text(.12,.5,'No valid candidates found in this run.',fontsize=18,color=ink)
    for index,(ax,r) in enumerate(zip(axes.flat,chosen)):
        poly=Polygon(r['vertices']).buffer(-cfg.gap/2,join_style=2)
        is_control=r.get('id')=='C_control'
        ax.add_patch(Patch(np.array(poly.exterior.coords),facecolor='#c6a36d' if is_control else '#789995',edgecolor=ink,lw=.7))
        for point in r['holes']:
            ax.add_patch(Patch(np.array(capsule(point,cfg).exterior.coords),facecolor=bg,edgecolor=ink,lw=.35))
        ax.set_xlim(-cfg.max_size/2-8,cfg.max_size/2+8);ax.set_ylim(-cfg.max_size/2-8,cfg.max_size/2+8)
        name='C · control' if is_control else r['id']
        ax.set_title(f"{name} · {r['width_mm']:.1f} × {r['height_mm']:.1f} mm\nShape error {r['regular_error_pct']:.2f}%",fontsize=12,color=ink)
        ax.text(.5,-.08,f"{r['count']} slots · edge >= {r['web_mm']:.2f} mm\nAngles {r['angle_min_deg']:.1f}–{r['angle_max_deg']:.1f}°",ha='center',fontsize=10,color=ink,transform=ax.transAxes)
    fig.text(.04,.025,'Same scale. Limited numerical search results; ribs and physical fit remain untested.',fontsize=10,color=ink)
    fig.savefig(out/'gallery.png',dpi=145,facecolor=bg);plt.close(fig)


def run(cfg,out):
    out.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    bases,total=enumerate_bases(cfg)
    try:
        control=make_record(hexagon([160,0],[80,160],[80,40]),[6.25,20],[160,0],[80,160],cfg)
        control['id']='C_control'
    except ValueError:control=None
    records=[]
    print(f'Enumerated {total} lattice bases; searching {len(bases)}',flush=True)
    for index,(u,v) in enumerate(bases):
        r=optimise_basis(u,v,cfg,cfg.seed+index)
        if r:records.append(r)
        if index%10==0 or index+1==len(bases):
            best=min((x['regular_error_pct'] for x in records),default=control['regular_error_pct'] if control else float('nan'))
            print(f'{index+1}/{len(bases)} bases; feasible {len(records)}; best error {best:.3f}%; elapsed {time.monotonic()-start:.1f}s',flush=True)
    records.sort(key=lambda r:r['regular_error_pct'])
    for i,r in enumerate(records,1):r['id']=f'H{i:02}'
    report={'settings':asdict(cfg),'search_scope':{'enumerated_bases':total,'searched_bases':len(bases),
             'global_optimality_proven':False,'elapsed_seconds':time.monotonic()-start},
             'control':control,'results':records,'pareto_ids':[r['id'] for r in pareto(records)]}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    fields=['id','count','width_mm','height_mm','regular_error_pct','web_mm','angle_min_deg','angle_max_deg','side_min_mm','side_max_mm','rotation_180']
    with (out/'results.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(records)
    gallery(records,control,out,cfg)
    print(json.dumps({'feasible':len(records),'control_error_pct':control['regular_error_pct'] if control else None,
                      'best_error_pct':records[0]['regular_error_pct'] if records else None,
                      'elapsed_seconds':round(time.monotonic()-start,1)},indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--max-size',type=float,default=248)
    p.add_argument('--min-web',type=float,default=2)
    p.add_argument('--min-slots',type=int,default=8)
    p.add_argument('--basis-limit',type=int,default=100)
    p.add_argument('--iterations',type=int,default=80)
    p.add_argument('--seed',type=int,default=1729)
    p.add_argument('--mode',choices=['general','symmetric-split'],default='general')
    p.add_argument('--shape-step',type=float,default=.5)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    cfg=Settings(max_size=a.max_size,min_web=a.min_web,min_slots=a.min_slots,
                 basis_limit=a.basis_limit,iterations=a.iterations,seed=a.seed)
    out=a.out or Path(__file__).resolve().parent/('run' if a.mode=='general' else 'run_symmetric')
    if a.mode=='symmetric-split':
        from symmetric_search import run as run_symmetric
        run_symmetric(cfg,out,a.shape_step)
    else:run(cfg,out)
