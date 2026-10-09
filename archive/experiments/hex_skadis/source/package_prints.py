"""Create portable core-3MF build plates from validated STL parts.

These files contain geometry in millimetres, not printer-specific G-code.
Bambu Studio projects with P2S presets are created separately by its native CLI.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import trimesh

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)


def plate(out,name,placements):
    model=ET.Element(f'{{{NS}}}model',{'unit':'millimeter','xml:lang':'en-US'})
    ET.SubElement(model,f'{{{NS}}}metadata',{'name':'Title'}).text=name
    resources=ET.SubElement(model,f'{{{NS}}}resources')
    build=ET.SubElement(model,f'{{{NS}}}build')
    footprint=[]
    for i,(part,x,y) in enumerate(placements,1):
        mesh=trimesh.load_mesh(out/'stl'/f'{part}.stl',process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,part
        mesh.apply_translation(-mesh.bounds[0])
        lo,hi=mesh.bounds
        assert 0<=x and 0<=y and x+hi[0]<=256 and y+hi[1]<=256,(name,part)
        from shapely.geometry import box
        area=box(x,y,x+hi[0],y+hi[1])
        assert all(area.distance(p)>=3 for p in footprint),(name,'placement collision')
        footprint.append(area)
        obj=ET.SubElement(resources,f'{{{NS}}}object',{'id':str(i),'type':'model','name':part})
        xmlmesh=ET.SubElement(obj,f'{{{NS}}}mesh')
        vertices=ET.SubElement(xmlmesh,f'{{{NS}}}vertices')
        for v in mesh.vertices:
            ET.SubElement(vertices,f'{{{NS}}}vertex',{a:f'{n:.7f}' for a,n in zip('xyz',v)})
        triangles=ET.SubElement(xmlmesh,f'{{{NS}}}triangles')
        for tri in mesh.faces:
            ET.SubElement(triangles,f'{{{NS}}}triangle',{f'v{k+1}':str(v) for k,v in enumerate(tri)})
        ET.SubElement(build,f'{{{NS}}}item',{'objectid':str(i),'transform':f'1 0 0 0 1 0 0 0 1 {x} {y} 0'})
    content_types='<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rels='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    dest=out/'projects'/f'{name}_geometry.3mf'
    with ZipFile(dest,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content_types)
        z.writestr('_rels/.rels',rels)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    print(dest.name)


def build(out):
    out=Path(out)
    plate(out,'01_fit_tests',[(f'fit_slot_plus_{a:.2f}',12+i*80,12) for i,a in enumerate((0,.15,.3))]
          + [(f'bridge_clearance_{a:.1f}',12+i*45,95) for i,a in enumerate((.1,.2,.4))])
    plate(out,'02_horizontal_seam', [('seam_horizontal_1',12,12),('seam_horizontal_2',12,70),('bridge_clearance_0.2',140,12)])
    for n,d in [(3,'diagonal_up'),(4,'diagonal_down')]:
        plate(out,f'{n:02}_{d}_seam',[(f'seam_{d}_1',8,12),(f'seam_{d}_2',136,12),('bridge_clearance_0.2',12,130)])
    plate(out,'05_panel_PROTOTYPE',[('panel_240x200_PROTOTYPE',8,25)])
    plate(out,'06_mounting_parts',[('wall_spacer_20mm',12+i*24,12) for i in range(4)]
          + [('bridge_clearance_0.2',12+i*40,45) for i in range(6)])


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent)
    build(ap.parse_args().out)
