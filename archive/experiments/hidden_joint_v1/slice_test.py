from pathlib import Path
import sys,json,subprocess,zipfile,shutil
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'hex_v3'/'source'))
from package_prints import plate

def main():
    work=ROOT.parents[1]/'work'/'hidden-joint-slicing';work.mkdir(parents=True,exist_ok=True)
    profiles=work/'profiles';profiles.mkdir(exist_ok=True)
    original=ROOT.parent/'hex_v3'/'source'/'print_profiles'
    for name in ('machine','filament'):shutil.copy2(original/f'{name}.json',profiles/f'{name}.json')
    p=json.loads((original/'process.json').read_text())
    p.update(wall_generator='arachne',initial_layer_speed=['25']*3,initial_layer_infill_speed=['40']*3,
             outer_wall_speed=['60']*3,inner_wall_speed=['120']*3)
    (profiles/'process.json').write_text(json.dumps(p,indent=2)+'\n')
    placements=[('corner_NEW',12,12),('corner_EXISTING_oblique',90,12),('corner_EXISTING_horizontal',130,12)]
    placements += [('spring_key',130+20*i,44) for i in range(4)]
    plate(ROOT,'corner_fit_test',placements)
    cmd=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--datadir',str(work/'bambu-data'),
         '--load-settings',str(profiles/'machine.json')+';'+str(profiles/'process.json'),
         '--load-filaments',str(profiles/'filament.json'),'--arrange','0','--orient','0','--slice','0',
         '--export-3mf','corner_fit_test_P2S.3mf','--outputdir',str(work),str(ROOT/'projects'/'corner_fit_test_geometry.3mf')]
    with (work/'cli.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0,work/'cli.log'
    file=work/'corner_fit_test_P2S.3mf'
    with zipfile.ZipFile(file) as z:
        assert z.testzip() is None
        names=[n for n in z.namelist() if n.endswith('.gcode')];assert names
        g=z.read(names[0]).decode()
        stats=[line for line in g.splitlines()[:160] if 'model printing time:' in line or 'total filament weight' in line]
        cfg=json.loads(z.read('Metadata/project_settings.config'))
        assert cfg['wall_generator']=='arachne' and cfg['sparse_infill_density']=='100%'
        (ROOT/'images'/'test_plate.png').write_bytes(z.read('Metadata/plate_1.png'))
    shutil.copy2(file,ROOT/'projects'/file.name)
    (ROOT/'slicing_validation.json').write_text(json.dumps(dict(exit_code=0,toolpaths_generated=True,statistics=stats,settings='P2S0.4/PLA/0.2mm/4walls/100%/Arachne',physical_print_started=False),indent=2)+'\n')
    print(stats)

if __name__=='__main__':main()
