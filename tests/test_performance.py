import copy
import hashlib
import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from services.ml.config import DERIVED
from services.ml.performance import report, summarize
from scripts.evidence_bundle import provision


def test_frozen_scores_and_api_download_are_identical():
    from services.ml.app import app
    r = report()
    expected = {"write0_ps": (8,4), "write1_ps": (8,4), "active_energy_fj": (8,4),
                "quiet_power_uw": (8,4), "hold_snm_mv": (6,6), "read_snm_mv": (4,4)}
    for target, (n, groups) in expected.items():
        s = r["targets"][target]
        assert s["models"]["ridge"]["percentage"] == 100
        assert s["models"]["ridge"]["passing"] == s["models"]["ridge"]["evaluated"] == n
        assert s["groups"] == groups and s["final_test_cases"] == 0
    with TestClient(app) as c:
        assert c.get('/performance').json() == c.get('/reports/performance.json').json() == r


def test_split_leakage_duplicates_missing_and_zero_labels():
    evaluation = json.loads((DERIVED/'evaluation.json').read_text(encoding='utf-8'))
    tables = json.loads((DERIVED/'targets.json').read_text(encoding='utf-8'))
    bad = copy.deepcopy(evaluation)
    bad['targets']['active_energy_fj']['splits'][0]['train'].append(bad['targets']['active_energy_fj']['splits'][0]['validation'][0])
    with pytest.raises(ValueError, match='Invalid split'): summarize(bad,tables)
    duplicate = copy.deepcopy(tables)
    duplicate['active_energy_fj']['records'][0]['sha256'] = duplicate['active_energy_fj']['records'][1]['sha256']
    with pytest.raises(ValueError, match='Duplicate source'): summarize(evaluation,duplicate)
    missing = copy.deepcopy(evaluation)
    missing['targets']['active_energy_fj']['models']['ridge']['individual'][0]['measured'] = None
    with pytest.raises(ValueError, match='Missing label'): summarize(missing,tables)
    # Controlled numerical fixture: zero remains an eligible label using the frozen absolute floor.
    fixture = {'model_version':'fixture','dataset_version':'fixture','metric_policy':'fixture','targets':{
        'active_energy_fj': {'status':'exploratory','n_cases':2,'n_groups':2,'features':['vdd_v'],'final_test_cases':0,'deployed_model':'ridge',
            'splits':[{'train':['b'],'validation':['a']},{'train':['a'],'validation':['b']}],
            'models':{'ridge':{'mae':.1,'rmse':.1,'within_10pct':1.,'individual':[
                {'id':i,'group':i,'measured':0.,'predicted':.1,'error':.1} for i in ['a','b']]}}}}}
    labels = {'active_energy_fj':{'features':['vdd_v'],'records':[{'id':i,'group':i,'sha256':i,'active_energy_fj':0.} for i in ['a','b']]}}
    assert summarize(fixture,labels)['targets']['active_energy_fj']['models']['ridge']['passing'] == 2


def test_known_case_is_training_agreement_not_validation():
    from services.ml.app import app
    with TestClient(app) as c:
        before = c.get('/performance').json()
        result = c.post('/predict',json={'target':'active_energy_fj','model_version':before['model_version'],
            'features':{'vdd_v':1.,'temp_c':27.,'mode':1}}).json()
        assert result['measured_case']['file'] == 'sel1updated.vcsv.txt'
        assert result['measured_case']['active_energy_fj'] == pytest.approx(202.83385857169995)
        assert result['value'] == pytest.approx(203.11361956733774)
        assert result['selected_case']['relative_error_pct'] == pytest.approx(.13792618136231624)
        assert result['selected_case']['included_in_training'] is True
        assert c.get('/performance').json() == before


def test_replay_saved_folds_without_touching_artifacts():
    import joblib
    import numpy as np
    from sklearn.base import clone
    from services.ml.config import ARTIFACTS
    evaluation = json.loads((DERIVED/'evaluation.json').read_text(encoding='utf-8'))
    tables = json.loads((DERIVED/'targets.json').read_text(encoding='utf-8'))
    for target, spec in evaluation['targets'].items():
        records = {r['id']:r for r in tables[target]['records']}
        bundle = joblib.load(ARTIFACTS/evaluation['model_version']/f'{target}.joblib')
        saved = {r['id']:r['predicted'] for r in spec['models']['ridge']['individual']}
        for split in spec['splits']:
            model = clone(bundle['model'])
            def features(ids): return [[records[i][f] for f in spec['features']] for i in ids]
            model.fit(features(split['train']), [records[i][target] for i in split['train']])
            predicted = model.predict(features(split['validation']))
            np.testing.assert_allclose(predicted,[saved[i] for i in split['validation']],rtol=0,atol=1e-12)


def test_private_bundle_hash_paths_and_preservation(tmp_path):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload,'w') as z: z.writestr('numeric.txt', b'fixture')
    data = payload.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    records = [{'file':'numeric.txt','sha256':hashlib.sha256(b'fixture').hexdigest()}]
    provision(data,digest,tmp_path,records)
    assert (tmp_path/'numeric.txt').read_bytes() == b'fixture'
    with pytest.raises(ValueError,match='SHA256'): provision(data,'0'*64,tmp_path,records)
    (tmp_path/'numeric.txt').write_bytes(b'preserve')
    with pytest.raises(ValueError,match='preserved unchanged'): provision(data,digest,tmp_path,records)
    assert (tmp_path/'numeric.txt').read_bytes() == b'preserve'


def test_hosted_auth_readiness_and_no_mutations(monkeypatch):
    import importlib
    module = importlib.import_module('services.ml.app')
    monkeypatch.setattr(module,'PRODUCTION',True)
    monkeypatch.setattr(module,'SERVICE_TOKEN','x'*32)
    with TestClient(module.app) as c:
        assert c.get('/ready').status_code == 200
        assert c.get('/performance').status_code == 401
        headers = {'x-sams-service-token':'x'*32}
        assert c.get('/performance',headers=headers).status_code == 200
        assert c.post('/jobs',json={'kind':'train'},headers=headers).status_code == 403
        assert c.post('/uploads',headers=headers).status_code == 403
        assert c.get('/jobs',headers=headers).json() == []
        assert c.get('/health').json()['processing_enabled'] is False
