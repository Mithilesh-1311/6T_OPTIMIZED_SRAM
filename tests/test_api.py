import json
import pytest
from fastapi.testclient import TestClient
from services.ml.app import app
from services.ml.config import DERIVED

@pytest.fixture
def client():
    with TestClient(app) as c:yield c

def test_health_reports_and_path_restriction(client):
    assert client.get('/health').json()['status']=='ok'
    assert client.get('/reports/evaluation.json').json()==json.loads((DERIVED/'evaluation.json').read_text())
    assert client.get('/reports/SAMS_End_to_End_Master_Guide%20(2).md').status_code==404
    assert client.get('/reports/..%2F..%2Fpackage.json').status_code==404

def test_prediction_validation_live_model_and_version(client):
    e=client.get('/evaluation').json()
    req={'target':'write0_ps','features':{'vdd_v':.95,'temp_c':55,'mode':0},'model_version':e['model_version']}
    result=client.post('/predict',json=req)
    assert result.status_code==200 and result.json()['status']=='exploratory'
    assert result.json()['value']>0
    req['features']['mode']=.5;assert client.post('/predict',json=req).status_code==422
    req['features']['mode']=0;req['features']['vdd_v']=1.5
    assert client.post('/predict',json=req).json()['value'] is None
    req['features']['vdd_v']=.95;req['model_version']='outdated'
    assert client.post('/predict',json=req).status_code==409
    req['model_version']=e['model_version'];req['features']['write0_ps']=10
    assert client.post('/predict',json=req).status_code==422

def test_prediction_schema_mismatch_and_boolean_inputs(client,monkeypatch):
    import joblib
    e=client.get('/evaluation').json()
    request={'target':'write0_ps','features':{'vdd_v':.95,'temp_c':55,'mode':0},'model_version':e['model_version']}
    original=joblib.load
    def incompatible(path):
        bundle=original(path);bundle['schema_version']=999;return bundle
    monkeypatch.setattr(joblib,'load',incompatible)
    assert client.post('/predict',json=request).status_code==409
    request['features']['mode']=True
    assert client.post('/predict',json=request).status_code==422

def test_measured_comparison_constraints_and_missing(client):
    result=client.post('/compare',json={'temp_c':27,'max_delay_ps':40,'min_snm_mv':250}).json()
    assert result['selection']['mode']==1 and result['selection']['vdd_v']==.9
    assert result['selection']['margin']['source'].startswith('SNM_HOLD')
    fail=client.post('/compare',json={'temp_c':27,'max_delay_ps':1}).json()
    assert fail['message']=='No supported feasible setting.' and fail['selection'] is None
    assert client.post('/compare',json={'temp_c':27}).status_code==422
    assert client.post('/compare',json={'temp_c':55,'max_delay_ps':40}).json()['selection'] is None
    ret=client.post('/compare',json={'kind':'retention','temp_c':27,'bit':0}).json()
    assert ret['selection']['vret_v']==.8

def test_waveforms_and_upload_boundaries(client):
    run=next(r for r in client.get('/experiments').json() if r['kind']=='active')
    result=client.get(f"/waveforms/{run['id']}?signals=Q,net2&start=23&end=25&points=100").json()
    assert len(result['signals'])==2 and result['signals'][0]['original_samples']>50000
    assert result['signals'][0]['plotted_samples']<=100
    assert client.get(f"/waveforms/{run['id']}?signals=absent").status_code==422
    assert client.post('/uploads',files={'file':('script.py',b'print(1)')}).status_code==415
    response=client.post('/uploads',files={'file':('../../x.csv',b'time[ns],Q[V]\n0,0\n1,1\n')})
    assert response.status_code==200 and response.json()['status']=='audit_only'

def test_job_state_persistence_and_single_writer(tmp_path,monkeypatch):
    import importlib
    module=importlib.import_module('services.ml.app')
    monkeypatch.setattr(module,'ARTIFACTS',tmp_path)
    monkeypatch.setattr(module,'train',lambda callback:callback('training','Metadata fixture only; no scientific data'))
    with TestClient(app) as client:
        job=client.post('/jobs',json={'kind':'train'}).json()
        stored=client.get('/jobs/'+job['id']).json()
        assert stored['state']=='completed' and stored['ended'] is not None
        assert client.get('/jobs').json()[0]['id']==job['id']
        module.LOCK.acquire()
        try:assert client.post('/jobs',json={'kind':'train'}).status_code==409
        finally:module.LOCK.release()
