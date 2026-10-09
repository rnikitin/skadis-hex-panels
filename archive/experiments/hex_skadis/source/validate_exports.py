"""Validate actual exported meshes and STEP, independently of metadata."""
from pathlib import Path
import json
import numpy as np
import trimesh
import cadquery as cq
from shapely.affinity import translate
import generate as g

ROOT=Path(__file__).resolve().parent.parent


def validate():
    parts=[]
    for path in sorted((ROOT/'stl').glob('*.stl')):
        mesh=trimesh.load_mesh(path,process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,path.name
        assert len(mesh.split())==1,(path.name,'disconnected shell')
        step=cq.importers.importStep(str(ROOT/'step'/f'{path.stem}.step')).val()
        assert step.isValid() and len(step.Solids())==1,path.name
        assert abs(mesh.volume-step.Volume())/step.Volume()<.003,path.name
        parts.append({'file':path.name,'watertight':bool(mesh.is_watertight),'solids':1,
                      'size_mm':np.round(mesh.extents,4).tolist(),
                      'volume_cm3':round(mesh.volume/1000,4),
                      'triangles':len(mesh.faces)})
    c=g.Config()
    panel=trimesh.load_mesh(ROOT/'stl'/'panel_240x200_PROTOTYPE.stl',process=True)
    contours=panel.section(plane_origin=(0,0,2.5),plane_normal=(0,0,1)).discrete
    slots=[]
    for loop in contours:
        lo,hi=loop.min(axis=0),loop.max(axis=0)
        size=hi-lo
        if abs(size[0]-5.15)<.025 and abs(size[1]-15.15)<.025:
            slots.append((lo[:2]+hi[:2])/2)
    assert len(slots)==36,('actual STL receiving slots',len(slots))
    bb=g.make_panel(c).BoundingBox()
    errors=[]
    for x,y in g.slot_centres(c):
        target=np.array([x-bb.xmin,y-bb.ymin])
        errors.append(min(np.linalg.norm(s-target) for s in slots))
    assert max(errors)<.01,('exported slot position error',max(errors))
    # Independently derive spacing across nine positions from the exported loops.
    global_slots=np.array([s+[ox+bb.xmin,oy+bb.ymin] for ox,oy in g.layout(c) for s in slots])
    indices_x=np.rint(global_slots[:,0]/20)
    ideal_x=indices_x*20
    ideal_y=np.rint((global_slots[:,1]-10-20*(indices_x%2))/40)*40+10+20*(indices_x%2)
    drift=np.linalg.norm(global_slots-np.column_stack((ideal_x,ideal_y)),axis=1)
    assert max(drift)<.01
    fixtures={
        'within_panel_40x40_plus_staggered_centre':[[-40,-30],[0,-30],[-40,10],[0,10],[-20,-10]],
        'horizontal_seam_40x40':[[-20,70],[20,70],[-20,110],[20,110]],
        'diagonal_up_seam_80x40':[[60,30],[140,30],[60,70],[140,70]],
        'diagonal_down_seam_80x40':[[60,-50],[140,-50],[60,-10],[140,-10]],
    }
    for name,points in fixtures.items():
        for p in points:
            assert np.min(np.linalg.norm(global_slots-np.array(p),axis=1))<.01,(name,p)
    gap_checks=[]
    p=g.panel_polygon(c)
    for x,y in [(0,200),(180,100),(180,-100)]:
        gap=p.distance(translate(p,xoff=x,yoff=y))
        assert abs(gap-.3)<1e-7
        gap_checks.append({'translation_mm':[x,y],'normal_gap_mm':round(gap,8)})
    report={'status':'PASS — digital geometry only','physical_fit':'NOT TESTED',
            'original_IKEA_compatibility':'NOT TESTED','load_rating':'NOT ESTABLISHED',
            'stl_parts':parts,'slots_per_panel_measured_from_STL':len(slots),
            'slots_in_3x3':len(global_slots),'max_exported_lattice_error_mm':float(max(drift)),
            'two_row_accessory_footprints_verified_from_STL':fixtures,
            'gap_checks':gap_checks,'stl_linear_tessellation_tolerance_mm':.02,
            'cadquery_version':cq.__version__}
    (ROOT/'validation'/'geometry_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='stl_parts'},indent=2))


if __name__=='__main__':validate()
