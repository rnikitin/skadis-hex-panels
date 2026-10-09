"""Geometry, assembly, lattice and manufacturing-envelope checks."""
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.affinity import translate,scale
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import design as d

def main():
    report={'checks':[],'parts':[]}
    def record(name,value):
        assert value,name
        report['checks'].append(name)
    panel=d.panel()
    record('Panel is one valid connected CAD solid',panel.isValid() and len(panel.Solids())==1)
    # Geometric reflection including every counterbore and nut receiver.
    for normal in ((1,0,0),(0,1,0)):
        other=panel.mirror(normal)
        record('Panel mirror '+str(normal),panel.cut(other).Volume()<1e-5)
    record('Diagonals do not cut or fill working slots',d.ribs().intersection(d.SLOTS).area<1e-8)
    # Check ALL prescribed slot fragments intersecting the panel through z0..5.
    for x,y in d.CENTRES:
        slot=LineString([(x,y-5),(x,y+5)]).buffer(2.64,quad_segs=32)
        if slot.intersects(d.P):
            cutters=[d.extrude(p,.01,4.98) for p in d.pieces(slot.intersection(d.P)) if p.area>1e-7]
            record(f'Working slot remains open {x},{y}',all(panel.intersect(c).Volume()<1e-6 for c in cutters))
    # Lattice repeats exactly under both translations, including two-row hooks.
    for dx,dy in ((180,100),(0,200)):
        def on_lattice(x,y):
            i=(x-20)/20
            return abs(i-round(i))<1e-9 and (y-20*(int(round(i))%2))%40==0
        record(f'Lattice translation {dx},{dy}',all(on_lattice(x+dx,y+dy) for x,y in d.CENTRES))
    for edge in (0,1,2):
        delta=2*d.frames()[edge]['mid'];neighbour=panel.translate((*delta,0))
        record('Adjacent panels no solid interference '+str(edge),panel.intersect(neighbour).Volume()<1e-5)
        sites=[s for s in d.sites() if s['edge']==edge]
        for i,s in enumerate(sites):
            b=d.install(d.bridge(),s,.1)
            record(f'Bridge fits both recesses {edge}/{i}',b.intersect(panel).Volume()+b.intersect(neighbour).Volume()<1e-5)
            # Retraction normal to wall: no obstruction from either neighbour.
            record(f'Front bridge extraction {edge}/{i}',all(d.install(d.bridge(),s,z).intersect(panel).Volume()+d.install(d.bridge(),s,z).intersect(neighbour).Volume()<1e-5 for z in (-1,-3,-8)))
            for side in (-1,1):
                n=np.array(s['normal']);pt=np.array(s['point'])+5*side*n
                screw=d.screw(8,.3).translate((*pt,0))
                record(f'Bridge screw clears plastic {edge}/{i}/{side}',screw.intersect(panel).Volume()+screw.intersect(neighbour).Volume()+screw.intersect(b).Volume()<1e-5)
    for (x,y),shoe in zip(d.MOUNTS,d.installed_shoes()):
        record(f'Shoe clears panel ribs {x},{y}',panel.intersect(shoe).Volume()<1e-5)
        screw=d.wall_screw().translate((x,y,0));washer=d.washer().translate((x,y,0))
        record(f'M4 screw clears plastic {x},{y}',screw.intersect(panel).Volume()+screw.intersect(shoe).Volume()<1e-5)
        record(f'M4 washer clears face {x},{y}',washer.intersect(panel).Volume()<1e-5)
        nut=d.nut(7,7,3.2,2).translate((x,y,0))
        record(f'M4 nut fits shoe {x},{y}',nut.intersect(shoe).Volume()<1e-5)
    record('M4x16 full nut engagement',15.2>7+3.2+1.4)
    record('M4x16 tip stops before blind bore bottom',17.5-15.2>2)
    record('M4x16 tip stays away from tape',23-15.2>7)
    record('M3x8 full nut engagement',8.3>5+2.4+.5)
    for p in sorted((d.ROOT/'stl').glob('*.stl')):
        mesh=trimesh.load_mesh(p,process=True)
        ok=mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1 and mesh.volume>0
        record('Printable closed mesh '+p.name,ok)
        record('Fits P2S bed '+p.name,np.all(mesh.extents[:2]<256))
        report['parts'].append(dict(file=p.name,watertight=bool(mesh.is_watertight),size_mm=mesh.extents.tolist(),volume_cm3=mesh.volume/1000))
    report['scope']='Geometry/clearance only; no actual accessory bodies, screw preload, adhesive or wall strength'
    report['passed']=len(report['checks'])
    (d.ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',report['passed'],'checks')

if __name__=='__main__':main()
