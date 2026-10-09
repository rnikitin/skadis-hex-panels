"""Make reviewable P2S projects; never send to printer."""
from pathlib import Path
import sys,json,subprocess,zipfile,shutil
ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT.parents[1]/'work'/'v3-slicing'
from package_prints import plate

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    profile=ROOT/'source'/'print_profiles';profile.mkdir(exist_ok=True)
    # Bundled resolved presets make this directory portable.
    process=json.loads((profile/'process.json').read_text())
    process.update(sparse_infill_density='100%',sparse_infill_pattern='zig-zag',enable_prime_tower='0',brim_type='no_brim')
    (profile/'process.json').write_text(json.dumps(process,indent=2)+'\n')
    params=json.loads((ROOT/'parameters.json').read_text());parts={x['name']:x for x in params['parts']}
    names=['seam_straight_1','seam_straight_2','seam_oblique_1','seam_oblique_2','mount_coupon','tape_shoe_M4x16','front_bridge_M3x8','front_bridge_M3x8']
    placements=[];x=y=10.;row=0
    for name in sorted(names,key=lambda n:-parts[n]['size_mm'][1]):
        w,h,_=parts[name]['size_mm']
        if x+w>245:x=10;y+=row+7;row=0
        assert y+h<245
        placements.append((name,x,y));x+=w+7;row=max(row,h)
    plate(ROOT,'01_fit_tests',placements)
    plate(ROOT,'02_panel',[('S01_diamond_v3',8,26)])
    plate(ROOT,'03_four_shoes',[('tape_shoe_M4x16',10+i*44,12) for i in range(4)])
    report=[]
    for name in ('01_fit_tests','02_panel','03_four_shoes'):
        folder=WORK/name;folder.mkdir(exist_ok=True)
        cmd=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--datadir',str(WORK/'bambu-data'),
             '--load-settings',str(profile/'machine.json')+';'+str(profile/'process.json'),'--load-filaments',str(profile/'filament.json'),
             '--arrange','0','--orient','0','--slice','0','--export-3mf',name+'_P2S.3mf','--outputdir',str(folder),str(ROOT/'projects'/f'{name}_geometry.3mf')]
        with (folder/'cli.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        assert r.returncode==0,(name,folder/'cli.log')
        output=folder/(name+'_P2S.3mf')
        with zipfile.ZipFile(output) as z:
            assert z.testzip() is None
            gnames=[n for n in z.namelist() if n.endswith('.gcode')];assert gnames
            g=z.read(gnames[0]).decode()
            stats=[l for l in g.splitlines()[:160] if 'model printing time:' in l or 'total filament weight' in l]
            (ROOT/'images'/f'{name}_slicer.png').write_bytes(z.read('Metadata/plate_1.png'))
        shutil.copy2(output,ROOT/'projects'/output.name)
        report.append(dict(name=name,exit_code=0,toolpaths=True,statistics=stats))
        print(name,stats,flush=True)
    (ROOT/'slicing_validation.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
