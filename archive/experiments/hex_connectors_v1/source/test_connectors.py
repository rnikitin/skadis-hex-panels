from pathlib import Path
import pytest


def api():
    assert Path(__file__).with_name('build.py').exists(), 'Connector generator missing'
    import build
    return build


@pytest.mark.parametrize('name',['S01','S02','S06'])
def test_twelve_sockets_preserve_symmetry_and_working_clearance(name):
    b=api();s=b.make_panel(name);sites=b.sites(name)
    assert len(sites)==12 and s.isValid() and len(s.Solids())==1
    assert s.cut(s.rotate((0,0,0),(0,0,1),180)).Volume()<1e-5
    for plane in ['XZ','YZ']:
        assert s.cut(s.mirror(plane)).Volume()<1e-5
    assert s.intersect(b.hook_clearance_solid(name)).Volume()<1e-5
    assert min(p['wall_clearance'] for p in sites)>=.399


@pytest.mark.parametrize('name',['S01','S02','S06'])
def test_keys_mate_both_panels_on_every_edge_without_collision(name):
    b=api();panel=b.make_panel(name);key=b.make_key('normal')
    import cadquery as cq
    open_slots=cq.Workplane('XY',origin=(0,0,5.01)).pushPoints(b.clearance_centres(name)).slot2D(15.3,5.3,90).extrude(11.5).val()
    assert key.isValid() and len(key.Solids())==1
    for edge in range(6):
        frame=b.frames(name)[edge]
        neighbour=panel.translate((*[2*x for x in frame['mid']],0))
        for site in [p for p in b.sites(name) if p['edge']==edge]:
            installed=b.install_key(key,site)
            assert installed.intersect(panel).Volume()<1e-5
            assert installed.intersect(neighbour).Volume()<1e-5
            assert installed.intersect(open_slots).Volume()<1e-5
            # Pulling panels apart must load the dovetail shoulders.
            n=frame['normal']
            pulled=panel.translate((-n[0]*.7,-n[1]*.7,0))
            assert installed.intersect(pulled).Volume()>.01


def test_keys_and_coupons_are_single_printable_solids():
    b=api()
    for fit in ['loose','normal','tight']:
        shape=b.make_key(fit)
        assert shape.isValid() and len(shape.Solids())==1
        assert shape.BoundingBox().zmin==pytest.approx(0)
    for name,edge in [('S01',1),('S02',0)]:
        for shape in b.coupons(name,edge):
            assert shape.isValid() and len(shape.Solids())==1
