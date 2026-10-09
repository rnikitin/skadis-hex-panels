"""Split slots are allowed only when they reconstruct the full global pattern."""
from pathlib import Path
import numpy as np
import pytest
import search


def api():
    assert Path(__file__).with_name('symmetric_search.py').exists(), 'Symmetric split-slot mode missing'
    import symmetric_search
    return symmetric_search


def original():
    return np.array([(120,0),(60,100),(-60,100),(-120,0),(-60,-100),(60,-100)],float)


def test_original_shape_recovers_mirrors_and_whole_grid():
    s=api();cfg=search.Settings()
    r=s.assess(original(),(20,0),(180,100),(0,200),cfg)
    assert r['whole_slots']==38 and r['slot_fragments']==14
    assert r['max_slot_owners']==2
    assert r['mirror_x'] and r['mirror_y']
    proof=s.verify_assembly(original(),(20,0),(180,100),(0,200),r['local_centres'],cfg)
    assert proof['nominal_reconstruction_error_mm2']<1e-6
    assert proof['gapped_reconstruction_error_mm2']<1e-6


def test_holes_shared_by_three_modules_are_rejected():
    s=api()
    with pytest.raises(ValueError,match='three|owners'):
        s.assess(original(),(0,0),(180,100),(0,200),search.Settings())


def test_omitted_fragment_is_detected_in_assembly():
    s=api();cfg=search.Settings()
    r=s.assess(original(),(20,0),(180,100),(0,200),cfg)
    removed=r['partial_centres'][0]
    wrong=[p for p in r['local_centres'] if p!=removed]
    with pytest.raises(ValueError,match='reconstruct'):
        s.verify_assembly(original(),(20,0),(180,100),(0,200),wrong,cfg)


def test_asymmetric_grid_phase_is_rejected():
    s=api()
    with pytest.raises(ValueError,match='symmetr'):
        s.assess(original(),(0,10),(180,100),(0,200),search.Settings())
