"""Read-only local production startup checks; does not publish or fit models."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from evidence_bundle import provision

ROOT = Path(__file__).resolve().parents[1]


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


def get(base, path, token=None):
    headers={'x-sams-service-token':token} if token else {}
    try:
        with urlopen(Request(base+path,headers=headers),timeout=5) as response:
            return response.status,json.load(response)
    except HTTPError as exc:
        return exc.code,json.load(exc)


def main():
    ml_port, api_port = port(), port()
    token=secrets.token_hex(32)
    env={**os.environ,'SAMS_DEPLOYMENT':'production','ML_SERVICE_TOKEN':token,
         'WEB_ORIGIN':'https://sams.example','ML_URL':f'https://127.0.0.1:{ml_port}','PORT':str(api_port)}
    processes=[]
    logs=[]
    try:
        for command in ([sys.executable,'-m','uvicorn','services.ml.app:app','--host','0.0.0.0','--port',str(ml_port)],
                        ['node','apps/api/dist/server.js']):
            log=tempfile.TemporaryFile();logs.append(log)
            processes.append(subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
        ml=f'http://127.0.0.1:{ml_port}'
        api=f'http://127.0.0.1:{api_port}'
        for base,path in [(ml,'/ready'),(api,'/health')]:
            deadline=time.monotonic()+30
            while True:
                try:
                    code,_=get(base,path)
                    if code==200:break
                except OSError:pass
                if time.monotonic()>deadline:raise RuntimeError('Production startup did not become healthy in 30 seconds')
                time.sleep(.2)
        assert get(ml,'/performance')[0]==401
        code,r=get(ml,'/performance',token)
        assert code==200 and r==json.loads((ROOT/'reports/performance.json').read_text(encoding='utf-8'))
        assert get(ml,'/jobs',token)==(200,[])
        assert get(ml,'/health')[1]['processing_enabled'] is False
        # Local Uvicorn is HTTP; hosted ML_URL requires HTTPS terminated by Render.
        assert get(api,'/api/ready')[0]==503
        print('PASS: production bindings/assigned ports, readiness, service token, read-only state, HTTPS upstream failure handling')
    finally:
        for process in processes:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        for log in logs:log.close()

    archive=ROOT/'deployment/sams-evidence.zip'
    if not archive.exists():raise RuntimeError('Run python scripts/evidence_bundle.py pack once before release smoke check')
    payload=archive.read_bytes()
    records=json.loads((ROOT/'data/derived/experiments.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='sams-evidence-') as directory:
        provision(payload,hashlib.sha256(payload).hexdigest(),Path(directory),records)
        assert len(list(Path(directory).iterdir()))==len(records)
    print(f'PASS: private archive restores {len(records)} accepted exports byte-for-byte in isolated temporary storage')
    baseline=json.loads((ROOT/'reports/release-preservation-baseline.json').read_text(encoding='utf-8'))
    changed=[name for name,digest in baseline.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    assert not changed, f'Protected evidence changed: {changed}'
    print(f'PASS: {len(baseline)} original/derived/historical-artifact hashes unchanged')


if __name__=='__main__':
    main()
