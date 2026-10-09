"""Validate the exported STL, not just the CadQuery source."""
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from shapely.affinity import translate,scale
import build

ROOT=Path(__file__).resolve().parent.parent


def section(mesh,height):
    cut=mesh.section(plane_origin=(0,0,height),plane_normal=(0,0,1))
    result=Polygon()
    for path in cut.discrete:
        assert np.linalg.norm(path[0]-path[-1])<1e-5
        result=result.symmetric_difference(Polygon(path[:,:2]))
    return result


def run():
    params=json.loads((ROOT/'parameters.json').read_text());reports=[]
    for p in params['parts']:
        name=p['id'];d=build.designs()[name]
        mesh=trimesh.load_mesh(ROOT/p['file'],process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert len(mesh.split())==1 and mesh.volume>0
        assert mesh.extents[2]==15 and mesh.bounds[0,2]==0
        shift=p['xy_export_shift_mm']
        front=translate(section(mesh,2.5),xoff=-shift[0],yoff=-shift[1])
        rear=translate(section(mesh,10),xoff=-shift[0],yoff=-shift[1])
        assert front.is_valid and front.geom_type=='Polygon'
        assert len(front.interiors)==d['whole_slots']
        cutters=[LineString([(x,y-5),(x,y+5)]).buffer(2.65,quad_segs=64) for x,y in d['local_centres']]
        expected=build.outline(name).difference(unary_union(cutters))
        difference=front.symmetric_difference(expected).area
        assert difference<.02*expected.length
        for opening in cutters:
            probe=opening.buffer(-.03).intersection(build.outline(name).buffer(-.03))
            assert front.intersection(probe).area<1e-5
        # Independent rear-corridor check on STL cross-section; includes neighbouring slots.
        px,py=d['phase'];corridors=[]
        for i in range(-9,10):
            for j in range(-6,7):
                x,y=20*i+px,40*j+20*(i%2)+py
                corridors.append(box(x-8,y-17,x+8,y+17))
        blocked_area=rear.intersection(unary_union(corridors)).area
        assert blocked_area<.05
        for part in [front,rear]:
            for x,y in [(-1,1),(1,-1)]:
                assert part.symmetric_difference(scale(part,xfact=x,yfact=y,origin=(0,0))).area<.1
        reports.append({'id':name,'watertight':True,'single_connected_body':True,
            'triangles':len(mesh.faces),'actual_size_mm':np.round(mesh.extents,4).tolist(),
            'whole_slots_measured_from_STL':len(front.interiors),
            'front_profile_difference_mm2':difference,'rear_corridor_blocked_area_mm2':blocked_area,
            'mirrors_verified_on_STL_sections':True})
    (ROOT/'validation.json').write_text(json.dumps({'parts':reports,'physical_fit':'UNTESTED'},indent=2)+'\n')
    print(json.dumps(reports,indent=2))


if __name__=='__main__':run()
