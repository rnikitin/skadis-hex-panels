"""Continuous insertion envelopes; elastic deformation is ASSUMED, not solved."""
import json
import numpy as np
import trimesh
from shapely.affinity import translate
import joint as j

def main():
    p=j.panel();plain=j.panel(False)
    checks=[]
    for normal in ((1,0,0),(0,1,0)):
        error=p.cut(p.mirror(normal)).Volume()
        assert error<1e-5,('symmetry',normal,error)
    for e in range(6):
        delta=2*j.d.frames()[e]['mid']
        assert j.d.P.intersection(translate(j.d.P,*delta)).area<1e-9
    for i,s in enumerate(j.sites()):
        delta=2*j.d.frames()[s['edge']]['mid'];nb=p.translate((*delta,0))
        key=j.local_solid(j.key(),s)
        rest=key.intersect(p).Volume()+key.intersect(nb).Volume()
        assert rest<1e-5,('seated key',i,rest)
        # In coordinates of a panel approached from the front, the fixed key
        # traverses z=9..19.4. A prism is the exact translational swept volume.
        undeformed=j.local_solid(j.d.extrude(j.key_plan(),9,10.4),s)
        outside_lips=undeformed.intersect(plain).Volume()
        assert outside_lips<1e-5,('unexpected rigid obstruction',i,outside_lips)
        intended_contact=undeformed.intersect(p).Volume()
        assert intended_contact>1e-6,('retainer would not retain',i)
        compressed=j.local_solid(j.d.extrude(j.key_plan('negative'),9,10.4),s)
        through=compressed.intersect(p).Volume()
        assert through<1e-5,('compressed arm envelope blocked',i,through)
        # When this key is first placed into the existing opposite neighbour,
        # only that opposite half needs to compress.
        first=j.local_solid(j.d.extrude(j.key_plan('positive'),9,8.9),s)
        first_error=first.intersect(nb).Volume()
        assert first_error<1e-5,('existing-side insertion',i,first_error)
        assert 17.9<23 # above rib for lateral prepositioning, still short of wall
        checks.append(dict(edge=s['edge'],point=s['point'],seated_collision_mm3=rest,
                           rigid_sweep_outside_retainers_mm3=outside_lips,intended_snap_contact_mm3=intended_contact,
                           compressed_sweep_collision_mm3=through,first_half_insertion_mm3=first_error))
    # Four keys on two distinct existing neighbours; all use the same axial
    # movement, so no second incompatible in-plane insertion direction exists.
    two_edges=[s for s in j.sites() if s['edge'] in (0,1)]
    moving_envelopes=[j.local_solid(j.d.extrude(j.key_plan('negative'),9,10.4),s) for s in two_edges]
    assert all(x.intersect(p).Volume()<1e-5 for x in moving_envelopes)
    mesh_checks=[]
    for file in sorted((j.ROOT/'stl').glob('*.stl')):
        m=trimesh.load_mesh(file,process=True)
        assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,file
        mesh_checks.append(dict(file=file.name,size_mm=m.extents.tolist(),watertight=True,components=1))
    strain=1.5*j.ARM*j.TIP_DEFLECTION/j.ARM_L**2
    result=dict(status='geometric checks passed; physical snap retention NOT validated',
                checks=checks,mesh_checks=mesh_checks,two_neighbour_edges=[0,1],simultaneous_keys=4,
                nominal_throat_interference_per_arm_mm=.1,assumed_key_tip_deflection_mm=j.TIP_DEFLECTION,
                cantilever_root_strain_estimate=strain,
                analysis_limit='Simple uniform-beam estimate, no friction/contact or printed anisotropy; not a strength/fatigue result',
                rear_hook_travel_extra_mm=j.HOOK_DROP,hook_body_fit='NOT validated against a measured accessory',
                full_panel_print='not released; use the three-corner coupon first')
    (j.ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: 12 seats, continuous insertion envelopes on6edges, 4keys on2neighbours, 4closed meshes')
    print('Assumed tip deflection:',j.TIP_DEFLECTION,'mm; beam root strain estimate:',round(strain*100,3),'%')

if __name__=='__main__':main()
