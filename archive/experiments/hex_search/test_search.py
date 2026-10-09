"""Independent geometry contracts: no dropped slots disguised as success."""
from pathlib import Path
import numpy as np
import pytest


def api():
    assert Path(__file__).with_name('search.py').exists(), 'Search algorithm not implemented'
    import search
    return search


def test_translations_preserve_staggered_rows():
    s=api()
    for p in [(40,0),(0,40),(20,20),(180,100)]:assert s.in_lattice(p)
    for p in [(20,0),(0,20),(180,80)]:assert not s.in_lattice(p)


def test_regular_hex_is_the_aesthetic_reference():
    s=api()
    h=50*np.sqrt(3)
    regular=np.array([(100,0),(50,h),(-50,h),(-100,0),(-50,-h),(50,-h)])
    assert s.regularity(regular)<1e-10
    elongated=regular*np.array([1,1.5])
    assert s.regularity(elongated)>.1


def test_control_c_has_all_32_slots_and_real_material_margin():
    s=api();cfg=s.Settings()
    v=s.hexagon(np.array([160.,0.]),np.array([80.,160.]),np.array([80.,40.]))
    result=s.evaluate(v,(6.25,20),cfg)
    assert result['count']==32
    assert result['web_mm']==pytest.approx(3.387184335,abs=1e-6)
    checked=s.verify(v,(6.25,20),(160,0),(80,160),cfg)
    assert checked['slots_3x3']==288
    assert checked['missing']==checked['crossed']==0


def test_pretty_but_crossed_original_is_rejected():
    s=api();cfg=s.Settings()
    v=np.array([(120,0),(60,100),(-60,100),(-120,0),(-60,-100),(60,-100)],float)
    with pytest.raises(ValueError):s.verify(v,(0,10),(180,100),(0,200),cfg)


def test_bad_module_translation_cannot_pass_verification():
    s=api();cfg=s.Settings()
    v=s.hexagon(np.array([160.,0.]),np.array([80.,160.]),np.array([80.,40.]))
    with pytest.raises(ValueError,match='lattice'):
        s.verify(v,(6.25,20),(160,0),(80,159.9),cfg)


def test_search_is_reproducible_and_returns_verified_geometry():
    s=api();cfg=s.Settings(iterations=18)
    first=s.optimise_basis((160,0),(80,160),cfg,42)
    second=s.optimise_basis((160,0),(80,160),cfg,42)
    assert first is not None and second is not None
    np.testing.assert_allclose(first['vertices'],second['vertices'],atol=1e-9)
    assert first['web_mm']>=cfg.min_web
    assert first['verification']['missing']==0


def test_tight_user_constraints_return_empty_report_not_control_outside_limits(tmp_path):
    s=api()
    report=s.run(s.Settings(max_size=80,min_slots=20,basis_limit=1,iterations=1),tmp_path)
    assert report['control'] is None
    assert report['results']==[]
    assert (tmp_path/'results.json').exists()
