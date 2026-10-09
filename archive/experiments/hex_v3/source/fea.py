"""Conditional solid-elasticity comparison, NOT a printed-part load rating.

N, mm, MPa. Gmsh first-order tetrahedra + scikit-fem elasticity + AMG/CG.
Report refinement, equilibrium, solver residual and cantilever benchmark.
"""
from pathlib import Path
import sys,json,time,argparse
import numpy as np
import gmsh
from scipy.sparse.linalg import cg
from skfem import MeshTet, Basis, FacetBasis, LinearForm, ElementTetP1, ElementTetP2, ElementVector, asm
from skfem.models.elasticity import linear_elasticity,lame_parameters
import pyamg

ROOT=Path(__file__).resolve().parent.parent
E=2000.;NU=.35;WEIGHT=3*9.81;FRONT_WALL=24.;LEVER=100-FRONT_WALL

def mesh_step(path,h):
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    gmsh.model.add('solid');gmsh.model.occ.importShapes(str(path));gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMin',h*.45)
    gmsh.option.setNumber('Mesh.MeshSizeMax',h)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',14)
    gmsh.option.setNumber('Mesh.Algorithm3D',1)
    gmsh.model.mesh.generate(3)
    tags,xyz,_=gmsh.model.mesh.getNodes();types,_,nodes=gmsh.model.mesh.getElements(3)
    tet=np.asarray(nodes[list(types).index(4)]).reshape(-1,4)
    order=np.argsort(tags);idx=order[np.searchsorted(tags[order],tet)]
    m=MeshTet(xyz.reshape(-1,3).T,idx.T).remove_unused_nodes()
    gmsh.finalize();return m

def make_basis(m,order=1):return Basis(m,ElementVector(ElementTetP2() if order==2 else ElementTetP1()),intorder=4 if order==2 else 1)

def all_dofs(basis):return np.hstack([basis.nodal_dofs,basis.edge_dofs]) if basis.edge_dofs.size else basis.nodal_dofs

def elastic_solve(m,forces,fix,order=1):
    basis=make_basis(m,order);dofs=all_dofs(basis);coords=basis.doflocs[:,dofs[0]]
    la,mu=lame_parameters(E,NU)
    K=asm(linear_elasticity(la,mu),basis).tocsr()
    free=np.setdiff1d(np.arange(basis.N),fix);A=K[free][:,free].tocsr();b=forces[free]
    xyz=coords.T-np.mean(coords,axis=1);B=np.zeros((basis.N,6))
    for k in range(3):B[dofs[k],k]=1
    for k in range(3):
        v=np.cross(np.eye(3)[k],xyz)/100
        for c in range(3):B[dofs[c],k+3]=v[:,c]
    ml=pyamg.smoothed_aggregation_solver(A,B=B[free],symmetry='symmetric',max_coarse=100)
    iterations=[0]
    def count(_):iterations[0]+=1
    u=np.zeros(basis.N)
    u[free],info=cg(A,b,M=ml.aspreconditioner(),rtol=1e-8,atol=1e-10,maxiter=1500,callback=count)
    residual=np.linalg.norm((K@u-forces)[free])/max(np.linalg.norm(b),1e-16)
    if info!=0 or residual>2e-7:raise RuntimeError(('solver did not converge',info,residual))
    reaction=K@u-forces
    return basis,u,reaction,dict(iterations=iterations[0],relative_residual=float(residual))

def face_load(m,basis,f,centre,radius,vector,z=0):
    bf=m.boundary_facets();tri=m.facets[:,bf]
    pts=m.p[:,tri];cent=pts.mean(axis=1)
    mask=(np.max(abs(pts[2]-z),axis=0)<1e-5)&((cent[0]-centre[0])**2+(cent[1]-centre[1])**2<radius**2)
    selected=bf[mask];tri=tri[:,mask];pts=m.p[:,tri]
    area=np.linalg.norm(np.cross((pts[:,1]-pts[:,0]).T,(pts[:,2]-pts[:,0]).T),axis=1)/2
    assert len(area)>2,(centre,'empty patch')
    fb=FacetBasis(m,basis.elem,facets=selected,intorder=4)
    @LinearForm
    def traction(v,w):return sum(vector[k]*v[k] for k in range(3))
    f+=asm(traction,fb)/area.sum()
    return float(area.sum()),np.average(pts.mean(axis=1),axis=1,weights=area).tolist()

def panel_run(variant,h,case='centre',mounted=False,order=1):
    start=time.time();suffix='_mounted' if mounted else ''
    m=mesh_step(ROOT/'step'/f'S01_{variant}{suffix}.step',h)
    print('meshed',variant,h,m.p.shape[1],m.t.shape[1],flush=True)
    b=make_basis(m,order);f=np.zeros(b.N);dofs=all_dofs(b);coords=b.doflocs[:,dofs[0]]
    mounts=[(x,y) for x in (-40,40) for y in (-40,40)]
    mountnodes=[]
    support_z=23. if mounted else 5.
    for x,y in mounts:
        if mounted:
            nd=np.flatnonzero((abs(coords[0]-x)<=15+1e-6)&(abs(coords[1]-y-np.sign(y)*8)<=25+1e-6)&(abs(coords[2]-23)<1e-5))
        else:
            nd=np.flatnonzero(((coords[0]-x)**2+(coords[1]-y)**2<6**2+1e-6)&(abs(coords[2]-5)<1e-5))
        assert len(nd)>5;mountnodes.append(nd)
    fix=dofs[:,np.concatenate(mountnodes)].ravel()
    patches=[]
    # Patch centroids shift slightly on an unstructured mesh; rescale couple
    # so the actual nodal loads generate precisely the intended moment.
    upper,lower={'centre':([(-20,40),(20,40)],[(-20,0),(20,0)]),
                 'edge':([(60,40)],[(60,0)]),'top':([(-20,80),(20,80)],[(-20,40),(20,40)])}[case]
    for locations,zforce in ((upper,-1),(lower,1)):
        for x,y in locations:
            a,c=face_load(m,b,f,(x,y),8,(0,0,zforce/len(locations)));patches.append(dict(centre=[x,y],area_mm2=a,centroid_mm=c))
    moment=np.sum(np.cross(coords.T,f[dofs].T),axis=0)[0]
    f*=(-WEIGHT*LEVER)/moment
    for x,y in upper:face_load(m,b,f,(x,y),8,(0,-WEIGHT/len(upper),0))
    volumes=np.abs(np.linalg.det(np.stack([m.p[:,m.t[i]]-m.p[:,m.t[0]] for i in (1,2,3)],axis=-1).transpose(1,0,2)))/6
    # Approximate solid PLA density 1.24 g/cm3; actual print mass depends on infill.
    @LinearForm
    def gravity(v,w):return -1.24e-6*9.81*v[1]
    f+=asm(gravity,b)
    b,u,r,solver=elastic_solve(m,f,fix,order)
    disp=u[dofs];force=f[dofs];react=r[dofs]
    grad=b.interpolate(u).grad;eps=(grad+np.swapaxes(grad,0,1))/2
    la,mu=lame_parameters(E,NU);stress=2*mu*eps
    tr=np.einsum('iieq->eq',eps)
    for k in range(3):stress[k,k]+=la*tr
    dev=stress.copy();st=np.einsum('iieq->eq',stress)/3
    for k in range(3):dev[k,k]-=st
    vm=np.sqrt(1.5*np.sum(dev*dev,axis=(0,1))).mean(axis=-1)
    supports=[]
    for centre,nd in zip(mounts,mountnodes):
        rr=react[:,nd];origin=np.array([centre[0],centre[1]+(np.sign(centre[1])*8 if mounted else 0),support_z])
        supports.append(dict(centre=centre,force_N=rr.sum(axis=1).tolist(),moment_Nmm=np.cross(coords[:,nd].T-origin,rr.T).sum(axis=0).tolist()))
    resultant=(force+react).sum(axis=1);moment_error=np.cross(coords.T,(force+react).T).sum(axis=0)
    volume=volumes.sum()
    report=dict(variant=variant,case=case,mounted=mounted,order=order,dofs=int(b.N),h_mm=h,nodes=m.p.shape[1],tetrahedra=m.t.shape[1],volume_cm3=float(volume/1000),
                max_displacement_mm=float(np.linalg.norm(disp,axis=0).max()),max_out_of_plane_mm=float(abs(disp[2]).max()),
                strain_energy_Nmm=float(u@f/2),peak_element_von_mises_MPa=float(vm.max()),
                stress_p95_MPa=float(np.quantile(vm,.95)),force_balance_error_N=resultant.tolist(),
                moment_balance_error_Nmm=moment_error.tolist(),supports=supports,patches=patches,solver=solver,seconds=time.time()-start,
                E_MPa=E,nu=NU,mass_kg=3,self_mass_kg=float(volume*1.24e-6),projection_from_wall_mm=100,face_to_wall_mm=FRONT_WALL,
                limitations=['isotropic homogeneous solid, not calibrated printed PLA',('shoe/panel contact bonded; tape patches fixed rigidly; adhesive/wall excluded' if mounted else 'rigid clamped mount footprints; shoes/tape/wall excluded'),
                             'loads spread around slots; hook contact/local fracture excluded','no creep, buckling, damage or safety factor','peak stress mesh-sensitive'])
    key=f'{variant}_{h:g}'+('' if case=='centre' and not mounted else f'_{case}{suffix}')+(f'_P{order}' if order!=1 else '')
    (ROOT/'analysis'/f'{key}.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(ROOT/'analysis'/f'{key}_field.npz',points=m.p,tets=m.t,displacement=u[b.nodal_dofs],vm=vm)
    print(json.dumps({k:report[k] for k in ('variant','h_mm','max_out_of_plane_mm','peak_element_von_mises_MPa','seconds','solver')}),flush=True)
    return report

def benchmark(order=1):
    # Slender cantilever: P1 result should approach Euler-Bernoulli + shear.
    reports=[]
    for h in ((2.,1.) if order==2 else (2.,1.,.5)):
        m=MeshTet.init_tensor(np.arange(0,60+h/2,h),np.arange(0,10+h/2,h),np.arange(0,6+h/2,h))
        b=make_basis(m,order);dofs=all_dofs(b);coords=b.doflocs[:,dofs[0]]
        fb=FacetBasis(m,b.elem,facets=m.facets_satisfying(lambda x:abs(x[0]-60)<1e-8),intorder=4)
        @LinearForm
        def endload(v,w):return -10/60*v[2]
        f=asm(endload,fb)
        tip=np.flatnonzero(abs(coords[0]-60)<1e-8)
        fix=dofs[:,np.flatnonzero(abs(coords[0])<1e-8)].ravel()
        b,u,r,solver=elastic_solve(m,f,fix,order)
        measured=-np.mean(u[dofs[2,tip]])
        theory=10*60**3/(3*E*(10*6**3/12))+10*60/((5/6)*(E/(2*(1+NU)))*10*6)
        reports.append(dict(h_mm=h,measured_mm=float(measured),beam_theory_mm=theory,relative_error=float(abs(measured/theory-1)),solver=solver))
    assert reports[-1]['relative_error']<.08 and reports[-1]['relative_error']<reports[0]['relative_error'],reports
    (ROOT/'analysis'/f'benchmark_P{order}.json').write_text(json.dumps(reports,indent=2)+'\n');print(reports,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--variant',default='diamond');ap.add_argument('--h',type=float,default=3);ap.add_argument('--benchmark',action='store_true');ap.add_argument('--case',default='centre');ap.add_argument('--mounted',action='store_true');ap.add_argument('--order',type=int,default=1);a=ap.parse_args()
    if a.benchmark:benchmark(a.order)
    else:panel_run(a.variant,a.h,a.case,a.mounted,a.order)
