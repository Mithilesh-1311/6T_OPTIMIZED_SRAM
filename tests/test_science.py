from pathlib import Path
import json
import numpy as np
import pytest
from services.ml.core import Signal, parse, window, crossings, energy, write_delay, snm
from services.ml.config import ROOT, DERIVED

def signal(x,y,name="Q",axis="s",unit="V"):
    return Signal(name,np.array(x,dtype=float),np.array(y,dtype=float),axis,unit,[])

def test_vcsv_independent_grids_and_units(tmp_path):
    p=tmp_path/"example.txt"
    p.write_text(';Version, 1, 0\n;/Q,;/I\n;X,Y,;X,Y\n;Re,Re,;Re,Re\n;time,V,;time,I\n;ns,mV,;ps,uA\n0,0,0,-2\n1,1000,500,-4\n2,0,1000,-6\n')
    s,n=parse(p)
    assert n==3
    assert s['Q'].x[-1]==2e-9 and s['Q'].y[1]==1
    assert s['I'].x[-1]==1e-9
    assert s['I'].unit=='A' and s['I'].axis=='s'
    assert energy(s,{'I':.5},0,1)==pytest.approx(2.)

def test_standard_csv_and_unknown_unit(tmp_path):
    p=tmp_path/'x.csv';p.write_text('time[ns],Q[mV],QB[mV]\n0,0,1000\n1,1000,0\n')
    s,n=parse(p);assert n==2 and s['Q'].y[-1]==1
    p.write_text('dc[V],Q[unknown]\n0,1\n1,0\n')
    s,_=parse(p);assert s['Q'].flags and s['Q'].axis=='V'

def test_nonfinite_nonmonotonic_and_missing(tmp_path):
    p=tmp_path/'x.csv';p.write_text('time[s],Q[V]\n0,1\n0.5,nan\n0.4,0\n')
    s,_=parse(p);assert 'nonmonotonic axis' in s['Q'].flags
    with pytest.raises(ValueError):window(s['Q'],0,.4)

def test_window_roundoff_is_not_missing_data():
    s=signal([0,6e-8],[0,1])
    x,_=window(s,0,60*1e-9);assert x[-1]==6e-8
    with pytest.raises(ValueError,match='Incomplete'):window(s,0,61e-9)

def test_crossing_direction_and_exact_interpolation():
    s=signal([0,1,2,3,4],[0,1,0,1,0])
    assert crossings(s,.5,'rise',0,4).tolist()==[.5,2.5]
    assert crossings(s,.5,'fall',0,4).tolist()==[1.5,3.5]
    with pytest.raises(ValueError):crossings(signal([0,1],[0,1],axis='V'),.5,'rise',0,1)

def test_signed_energy_and_exact_boundaries():
    a=signal([0,1e-9,2e-9],[-1e-6,-3e-6,-1e-6],unit='A')
    assert energy({'main':a},{'main':1},.5,1.5)==pytest.approx(2.5)
    assert energy({'main':a},{'main':-1},.5,1.5)==pytest.approx(-2.5)

def test_write_event_and_persistence():
    x=np.array([23,24,24.1,24.2,26.5,26.6,27,30,32])*1e-9
    wl=signal(x,[0,0,1,1,1,0,0,0,0])
    q=signal(x,[0,0,.1,1,1,1,1,1,1])
    qb=signal(x,1-q.y)
    result=write_delay(wl,q,qb,1,24,1)
    assert 0<result['delay_ps']<200
    q.y[-2]=0
    with pytest.raises(ValueError,match='persist'):write_delay(wl,q,qb,1,24,1)

def test_snm_controlled_piecewise_linear_square():
    # Analytic symmetric VTC: largest square is 0.3 V, including exact intersections.
    x=np.array([0,.2,.4,.5,.6,.8,1.])
    y=np.array([1,1,.9,.5,.1,0,0.])
    vin=signal(x,x,axis='V');q=signal(x,y,axis='V')
    result=snm(vin,q,q)
    assert result['snm_mv']==pytest.approx(300.)
    for lobe in result['lobes']:
        square=np.array(lobe['square']);s=lobe['side_mv']/1000
        assert square[:,0].ptp()==pytest.approx(s)
        assert square[:,1].ptp()==pytest.approx(s)
    bad=signal(x,np.ones_like(x),axis='V')
    with pytest.raises(ValueError,match='transfer'):snm(vin,bad,bad)

def test_measured_labels_and_no_fabricated_join():
    audit=json.loads((DERIVED/'audit.json').read_text())
    assert audit['counts']['accepted']==30
    tables=json.loads((DERIVED/'targets.json').read_text())
    assert [len(tables[t]['records']) for t in tables]==[8,8,8,8,6,4]
    for target,table in tables.items():
        assert len({r['sha256'] for r in table['records']})==len(table['records'])
        assert set(table['features']) <= {'vdd_v','vret_v','temp_c','mode','bit'}
        assert target not in table['features']

def test_grouped_splits_and_baseline_evidence():
    e=json.loads((DERIVED/'evaluation.json').read_text())
    assert not e['target_90_established']
    for t,spec in e['targets'].items():
        table=json.loads((DERIVED/'targets.json').read_text())[t]['records']
        by_id={r['id']:r['group'] for r in table}
        if spec['status']=='unavailable':continue
        assert set(spec['models'])=={'constant','linear','ridge','local_neighbor','gaussian_process','random_forest'}
        observed=[]
        for split in spec['splits']:
            assert not {by_id[i] for i in split['train']} & {by_id[i] for i in split['validation']}
            observed.extend(split['validation'])
        assert sorted(observed)==sorted(by_id)
        assert spec['final_test_cases']==0

def test_extraction_agrees_with_independent_historical_rounding():
    runs=json.loads((DERIVED/'experiments.json').read_text())
    active=next(r for r in runs if r['kind']=='active' and r['vdd_v']==1 and r['temp_c']==27 and r['mode']==0)
    assert active['metrics']['write1_ps']==pytest.approx(27.76,abs=.01)
    assert active['metrics']['write0_ps']==pytest.approx(15.71,abs=.01)
    assert active['metrics']['active_energy_fj']==pytest.approx(204.087,abs=.002)
    ret=next(r for r in runs if r['kind']=='retention' and r['temp_c']==27 and r['bit']==0 and r['vret_v']==.8)
    assert ret['metrics']['quiet_power_uw']==pytest.approx(.19852,abs=.00001)
