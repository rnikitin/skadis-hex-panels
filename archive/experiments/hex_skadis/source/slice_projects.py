"""Use Bambu Studio's CLI to create and slice P2S prototype projects.

No printer connection or print command is used. Runtime files go to --work.
"""
from pathlib import Path
import argparse
import subprocess
import shutil
import zipfile
import json
import xml.etree.ElementTree as ET


def run(root,work,executable,only=None):
    root=root.resolve();work=work.resolve();work.mkdir(parents=True,exist_ok=True)
    profiles=root/'source'/'print_profiles'
    reports=[]
    for input_path in sorted((root/'projects').glob('*_geometry.3mf')):
        stem=input_path.stem.removesuffix('_geometry')
        if only and not stem.startswith(only):continue
        dest=work/stem;dest.mkdir(parents=True,exist_ok=True)
        output_name=stem+'_P2S.3mf'
        cmd=[str(executable),'--datadir',str(work/'bambu-data'),
             '--load-settings',str(profiles/'machine.json')+';'+str(profiles/'process.json'),
             '--load-filaments',str(profiles/'filament.json'),
             '--arrange','0','--orient','0','--slice','0',
             '--export-3mf',output_name,'--outputdir',str(dest),str(input_path)]
        print('Slicing',stem,flush=True)
        with (dest/'cli.log').open('w') as log:
            result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        target=dest/output_name
        if result.returncode or not target.exists():
            raise RuntimeError(f'Bambu export failed: {dest / "cli.log"}')
        with zipfile.ZipFile(target) as z:
            assert z.testzip() is None
            assert 'Metadata/project_settings.config' in z.namelist()
            config=json.loads(z.read('Metadata/project_settings.config'))
            assert config['printer_model']=='Bambu Lab P2S'
            assert str(config['wall_loops'])=='4'
            assert config['curr_bed_type']=='Textured PEI Plate'
            gcode=[n for n in z.namelist() if n.endswith('.gcode')]
            # Native projects may keep slice cache outside the project.
            external=list(dest.glob('*.gcode'))
            assert gcode or external,('No sliced toolpaths',stem)
            data=z.read(gcode[0]).decode() if gcode else external[0].read_text()
            statistics=[line for line in data.splitlines()[:120] if any(k in line.lower() for k in ('estimated','filament used','total filament','total layer','model printing time','total estimated time'))]
            reports.append({'project':output_name,'exit_code':result.returncode,
                            'printer':config['printer_model'],'wall_loops':config['wall_loops'],
                            'bed_type':config['curr_bed_type'],
                            'layer_height':config['layer_height'],'toolpaths_verified':True,'statistics':statistics})
        shutil.copy2(target,root/'projects'/output_name)
        print('Verified',output_name,flush=True)
    (root/'validation'/'slicing_report.json').write_text(json.dumps(reports,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--bambu',type=Path,default=Path('/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'))
    p.add_argument('--only')
    a=p.parse_args()
    run(Path(__file__).resolve().parent.parent,a.work,a.bambu,a.only)
