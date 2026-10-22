"""Run after npm run dev: verify real web → Node → Python contracts."""
import json
from urllib.request import urlopen, Request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:5173/api/'
def get(path):
    with urlopen(BASE+path,timeout=120) as response:return json.load(response)
def post(path,body):
    req=Request(BASE+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=120) as response:return json.load(response)

assert get('health')['status']=='ok'
stored=json.loads((ROOT/'data/derived/evaluation.json').read_text(encoding='utf-8'))
assert get('evaluation')==stored
assert get('reports/evaluation.json')==stored
performance=get('performance')
assert performance==get('reports/performance.json')==json.loads((ROOT/'reports/performance.json').read_text(encoding='utf-8'))
example=post('predict',{'target':'active_energy_fj','features':{'vdd_v':1,'temp_c':27,'mode':1},'model_version':stored['model_version']})
assert example['selected_case']['included_in_training'] is True
assert abs(example['selected_case']['relative_error_pct']-.13792618136231624)<1e-10
result=post('predict',{'target':'write1_ps','features':{'vdd_v':.95,'temp_c':55,'mode':1},'model_version':stored['model_version']})
assert result['status']=='exploratory' and result['value']>0
selection=post('compare',{'kind':'active','temp_c':27,'max_delay_ps':40})
assert selection['selection']['mode']==1 and selection['selection']['vdd_v']==.9
assert post('compare',{'kind':'active','temp_c':27,'max_delay_ps':1})['selection'] is None
ret=post('compare',{'kind':'retention','temp_c':27,'bit':0})
assert ret['selection']['vret_v']==.8
run=next(r for r in get('experiments') if r['kind']=='active')
wave=get(f"waveforms/{run['id']}?signals=Q,net2&start=23&end=25&points=100")
assert len(wave['signals'])==2 and wave['signals'][0]['original_samples']>50000
with urlopen('http://127.0.0.1:5173/',timeout=10) as response:assert b'<title>SAMS</title>' in response.read()
for name in ('MODEL_CARD.md','PROJECT_GUIDE.md','DATA_AUDIT.md','EVALUATION_REPORT.md','ADDITIONAL_SIMULATIONS_REQUIRED.md','characterization.csv'):
    with urlopen(BASE+'reports/'+name,timeout=10) as response:
        assert response.read()==(ROOT/name if name.endswith('.md') else ROOT/'data/derived'/name).read_bytes()
print('PASS: live frontend proxy -> Node -> Python; inference; measured comparison; waveform; stored/downloaded evaluation equality')
print(f"Live exploratory write1: {result['value']:.6f} ps; model {stored['model_version']}")
