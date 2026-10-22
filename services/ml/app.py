"""Local scientific service; uploaded files are audited separately, never executed."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal
import os
import secrets
import hashlib
import json
import sqlite3
import threading
import uuid
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator
from .config import ROOT, DERIVED, ARTIFACTS
from .performance import report
from .core import parse
from .pipeline import audit_extract, train

LOCK = threading.Lock()
SCHEMA = 1
PRODUCTION = os.getenv("SAMS_DEPLOYMENT") == "production"
SERVICE_TOKEN = os.getenv("ML_SERVICE_TOKEN", "")

def read(name):
    path = DERIVED/f"{name}.json"
    if not path.exists():
        raise HTTPException(503,"Derived evidence missing. Run python -m services.ml.pipeline all")
    return json.loads(path.read_text(encoding="utf-8"))

def db():
    ARTIFACTS.mkdir(exist_ok=True)
    conn=sqlite3.connect(ARTIFACTS/"jobs.sqlite",timeout=15)
    conn.row_factory=sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, kind TEXT, state TEXT, stage TEXT, detail TEXT, started TEXT, ended TEXT)")
    return conn

@asynccontextmanager
async def lifespan(_app):
    if PRODUCTION:
        if len(SERVICE_TOKEN) < 32:
            raise RuntimeError("Production requires ML_SERVICE_TOKEN of at least 32 characters")
        readiness()
        yield
        return
    with db() as c:
        c.execute("UPDATE jobs SET state='interrupted', detail='Service restarted; rerun job', ended=? WHERE state IN ('running','queued')",(now(),))
    yield

app=FastAPI(title="SAMS",version="1.0.0",lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=["127.0.0.1","localhost","testserver"] + [h for h in [os.getenv("RENDER_EXTERNAL_HOSTNAME", ""), *os.getenv("SAMS_ALLOWED_HOSTS", "").split(",")] if h])

@app.middleware("http")
async def service_boundary(request, call_next):
    if PRODUCTION and request.url.path not in ("/health", "/ready"):
        if not secrets.compare_digest(request.headers.get("x-sams-service-token", ""), SERVICE_TOKEN):
            return JSONResponse({"detail": "Service authentication required"}, status_code=401)
    if PRODUCTION and request.method == "POST" and request.url.path in ("/jobs", "/uploads"):
        return JSONResponse({"detail": "Hosted evidence is read-only. Run processing locally."}, status_code=403)
    return await call_next(request)


@app.get("/ready")
def readiness():
    try:
        evidence = report()
        for target, spec in read("evaluation")["targets"].items():
            if spec["status"] != "unavailable":
                load_model(target, evidence["model_version"])
        missing = [r["file"] for r in read("experiments") if not (ROOT/"CSVs"/r["file"]).is_file()]
        if missing:
            raise ValueError(f"Private waveform evidence missing: {len(missing)} accepted files; provision SAMS_EVIDENCE_URL and SHA256")
        return {"status": "ok", "model_version": evidence["model_version"], "dataset_version": evidence["dataset_version"], "processing_enabled": not PRODUCTION}
    except Exception as exc:
        raise HTTPException(503, f"Scientific readiness failed: {exc}") from exc


@app.get("/performance")
def performance():
    try:
        return report()
    except Exception as exc:
        raise HTTPException(503, f"Evaluation evidence validation failed: {exc}") from exc


def now():
    return datetime.now(timezone.utc).isoformat()

@app.get("/health")
def health():
    return {"status":"ok","service":"SAMS scientific service","schema_version":SCHEMA,"data_ready":(DERIVED/"experiments.json").exists(),"processing_enabled":not PRODUCTION}

@app.get("/audit")
def audit(): return read("audit")

@app.get("/experiments")
def experiments(): return read("experiments")

@app.get("/evaluation")
def evaluation(): return read("evaluation")

@app.get("/dictionary")
def dictionary(): return read("dictionary")

@app.get("/overview")
def overview():
    a,e,r=read("audit"),read("evaluation"),read("experiments")
    pairs=[]
    for run in r:
        if run["kind"]=="active" and run["mode"]==0:
            other=next((o for o in r if o["kind"]=="active" and o["mode"]==1 and o["vdd_v"]==run["vdd_v"] and o["temp_c"]==run["temp_c"]),None)
            if other:
                pairs.append(100*(run["metrics"]["active_energy_fj"]/other["metrics"]["active_energy_fj"]-1))
    retention=[x for x in r if x["kind"]=="retention"]
    return {"dataset_version":a["dataset_version"],"model_version":e["model_version"],"file_counts":a["counts"],"rows":a["accepted_waveform_rows"],
            "targets":{t:{"cases":v["n_cases"],"groups":v["n_groups"],"status":v["status"]} for t,v in e["targets"].items()},
            "findings":{"short_energy_penalty_pct":pairs,"retention_survivals":sum(x["metrics"]["state_survived"] for x in retention),"retention_cases":len(retention)},
            "target_90_established":False,"final_test_cases":0,"provenance_limit":a["provenance_limit"]}

@lru_cache(maxsize=3)
def cached_parse(file, digest):
    return parse(ROOT/"CSVs"/file)[0]

@app.get("/waveforms/{run_id}")
def waveforms(run_id:str, signals:str="Q,QB,net2", start:FiniteFloat|None=None, end:FiniteFloat|None=None,
              points:int=Query(1200,ge=100,le=10000)):
    run=next((r for r in read("experiments") if r["id"]==run_id),None)
    if run is None: raise HTTPException(404,"Unknown accepted experiment")
    requested=signals.split(",")
    if len(requested)>16: raise HTTPException(422,"Select at most 16 signals")
    source=cached_parse(run["file"],run["sha256"])
    output=[]
    if start is not None and end is not None and end<=start: raise HTTPException(422,"end must exceed start")
    for name in requested:
        if name not in source: raise HTTPException(422,f"Signal {name} is absent")
        s=source[name]
        if s.flags: raise HTTPException(422,f"Signal {name}: {s.flags}")
        mask=np.ones(len(s.x),dtype=bool)
        scale=1e9 if s.axis=="s" else 1.
        if start is not None: mask &= s.x*scale>=start
        if end is not None: mask &= s.x*scale<=end
        idx=np.flatnonzero(mask)
        if len(idx)<2: raise HTTPException(422,"Selected interval has fewer than two samples")
        # Preserve local extrema per bucket for plotting; extraction always uses full resolution.
        if len(idx)>points:
            buckets=np.array_split(idx,max(1,points//4))
            idx=np.unique(np.concatenate([np.array([b[0],b[np.argmin(s.y[b])],b[np.argmax(s.y[b])],b[-1]]) for b in buckets]))
        output.append({"name":name,"axis_unit":"ns" if s.axis=="s" else s.axis,"unit":s.unit,"original_samples":len(s.x),"plotted_samples":len(idx),
                       "points":[{"x":float(s.x[i]*scale),"y":float(s.y[i])} for i in idx]})
    return {"run_id":run_id,"file":run["file"],"sha256":run["sha256"],"signals":output,"events":run["events"],"decimation":"Per-bucket min/max/endpoints for display only"}

class Prediction(BaseModel):
    model_config=ConfigDict(extra="forbid")
    target: Literal["write0_ps","write1_ps","active_energy_fj","quiet_power_uw","hold_snm_mv","read_snm_mv"]
    features:dict[str,FiniteFloat]
    model_version:str

    @field_validator("features",mode="before")
    @classmethod
    def numeric_features(cls,value):
        if not isinstance(value,dict) or any(type(v) not in (int,float) for v in value.values()):
            raise ValueError("Features must be JSON numbers, not strings or booleans")
        return value

def load_model(target,version):
    import joblib
    import sklearn
    current=read("evaluation")
    if version!=current["model_version"]: raise HTTPException(409,"Model version changed; reload workspace")
    path=ARTIFACTS/version/f"{target}.joblib"
    if not path.exists(): raise HTTPException(422,"Target model unavailable")
    model=joblib.load(path)
    if model.get("target")!=target or model.get("features")!=current["targets"][target]["features"] or model["schema_version"]!=SCHEMA or model["model_version"]!=version or model["dataset_version"]!=read("audit")["dataset_version"] or model["sklearn_version"]!=sklearn.__version__:
        raise HTTPException(409,"Model/schema/library mismatch; regenerate artifacts")
    return model

@app.post("/predict")
def predict(request:Prediction):
    e=read("evaluation"); spec=e["targets"][request.target]
    if set(request.features)!=set(spec["features"]): raise HTTPException(422,"Features must exactly match target schema")
    if spec["status"]=="unavailable": raise HTTPException(422,"Insufficient independent cases for this target")
    for f,v in request.features.items():
        if f in ("mode","bit") and v not in (0,1): raise HTTPException(422,f"{f} must be 0 or 1")
        low,high=spec["domain"][f]
        if not low<=v<=high:
            return {"status":"unavailable","value":None,"reason":f"Extrapolation: {f} lies outside [{low}, {high}]","model_version":request.model_version}
    bundle=load_model(request.target,request.model_version)
    row=[[request.features[f] for f in bundle["features"]]]
    value=float(bundle["model"].predict(row)[0])
    if not np.isfinite(value) or value<0: raise HTTPException(422,"Model returned nonphysical output")
    measured=read("targets")[request.target]["records"]
    exact=next((r for r in measured if all(abs(r[f]-request.features[f])<1e-9 for f in spec["features"])),None)
    comparison = None
    if exact:
        frozen = json.loads((ARTIFACTS/request.model_version/"targets.json").read_text(encoding="utf-8"))
        included = exact in frozen[request.target]["records"]
        comparison = {"absolute_error": abs(value-exact[request.target]),
                      "relative_error_pct": 100*abs(value-exact[request.target])/abs(exact[request.target]) if exact[request.target] != 0 else None,
                      "included_in_training": included, "case_id": exact["id"], "file": exact["file"],
                      "status": "Selected-case agreement; not held-out validation"}
    return {"selected_case":comparison,"status":"exploratory","value":value,"target":request.target,"model_version":request.model_version,"dataset_version":e["dataset_version"],
            "error_envelope":spec["residual_envelope"],"uncertainty":spec["uncertainty"],"domain":spec["domain"],"measured_case":exact,
            "warning":"No independent final test. Inside bounding domain does not establish interpolation accuracy. Do not use prediction alone to certify safety."}

class Comparison(BaseModel):
    model_config=ConfigDict(extra="forbid")
    kind:Literal["active","retention"]="active"
    temp_c:FiniteFloat
    bit:Literal[0,1]=0
    max_delay_ps:FiniteFloat|None=Field(None,gt=0)
    min_snm_mv:FiniteFloat|None=Field(None,ge=0)
    require_survival:bool=True
    stability:Literal["hold","read"]="hold"

@app.post("/compare")
def compare(request:Comparison):
    runs=read("experiments")
    if request.kind=="active" and request.max_delay_ps is None: raise HTTPException(422,"Supply a maximum acceptable write delay")
    if request.kind=="retention" and request.max_delay_ps is not None: raise HTTPException(422,"Earliest wake/access delay was not measured; omit delay constraint for retention")
    if request.kind=="retention" and request.stability=="read" and request.min_snm_mv is not None: raise HTTPException(422,"Static read SNM at reduced retention rail is unavailable")
    candidates=[]
    for r in runs:
        if r["kind"]!=request.kind or r["temp_c"]!=request.temp_c or (request.kind=="retention" and r["bit"]!=request.bit): continue
        reasons=[]; margin=None
        if request.kind=="active":
            delay=max(r["metrics"]["write0_ps"],r["metrics"]["write1_ps"])
            if delay>request.max_delay_ps: reasons.append("Worst write delay exceeds supplied limit")
            objective=r["metrics"]["active_energy_fj"]
        else:
            delay=None;objective=r["metrics"]["quiet_power_uw"]
            if request.require_survival and not r["metrics"]["state_survived"]: reasons.append("Stored state did not survive the measured sequence")
        if request.min_snm_mv is not None:
            voltage=r["vdd_v"] if request.kind=="active" else r["vret_v"]
            static=next((s for s in runs if s["kind"]==request.stability+"_snm" and s["vdd_v"]==voltage and s["temp_c"]==request.temp_c),None)
            if static is None: reasons.append("Requested static margin has no matching measurement")
            else:
                margin={"value_mv":static["metrics"][request.stability+"_snm_mv"],"source":static["file"],"boundary":"Separate ideal-rail core DC experiment, not a transient instance measurement"}
                if margin["value_mv"]<request.min_snm_mv: reasons.append("Static core margin below supplied limit")
        candidates.append({"id":r["id"],"file":r["file"],"sha256":r["sha256"],"vdd_v":r["vdd_v"],"vret_v":r["vret_v"],"mode":r["mode"],"delay_ps":delay,"objective":objective,"margin":margin,
                           "feasible":not reasons,"reasons":reasons,"metrics":r["metrics"]})
    feasible=sorted((c for c in candidates if c["feasible"]),key=lambda c:c["objective"])
    return {"status":"measured","dataset_version":read("audit")["dataset_version"],"extractor_version":read("audit")["extractor_version"],"selection":feasible[0] if feasible else None,"message":"Lowest measured energy/power satisfying supplied constraints" if feasible else "No supported feasible setting.",
            "objective":"20–60 ns DC energy (fJ)" if request.kind=="active" else "25–65 ns quiet power (uW)","candidates":candidates,
            "limitation":"Measured settings only. Survival applies only to the tested sequence; quiet-power optimum may differ from entry/hold/wake-energy optimum."}

class JobRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    kind:Literal["all","train"]="all"

def execute_job(job_id,kind):
    def update(stage,detail):
        with db() as c:c.execute("UPDATE jobs SET state='running',stage=?,detail=? WHERE id=?",(stage,detail,job_id))
    try:
        if kind=="all":audit_extract(update)
        train(update)
        state,detail="completed","Artifacts and reports regenerated"
    except Exception as exc:
        state,detail="failed",str(exc)
    finally:
        with db() as c:c.execute("UPDATE jobs SET state=?,stage=?,detail=?,ended=? WHERE id=?",(state,state,detail,now(),job_id))
        cached_parse.cache_clear();LOCK.release()

@app.post("/jobs",status_code=202)
def start_job(request:JobRequest,background:BackgroundTasks):
    if not LOCK.acquire(blocking=False): raise HTTPException(409,"A processing job is already running")
    job_id=uuid.uuid4().hex
    with db() as c:c.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?)",(job_id,request.kind,"queued","queued","Waiting for execution",now(),None))
    background.add_task(execute_job,job_id,request.kind)
    return {"id":job_id,"state":"queued"}

@app.get("/jobs")
def jobs():
    if PRODUCTION: return []
    with db() as c:return [dict(r) for r in c.execute("SELECT * FROM jobs ORDER BY started DESC LIMIT 30")]

@app.get("/jobs/{job_id}")
def job(job_id:str):
    if PRODUCTION: raise HTTPException(404,"Hosted mode has no processing jobs; history remains local")
    with db() as c:r=c.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()
    if not r:raise HTTPException(404,"Unknown job")
    return dict(r)

@app.post("/uploads")
async def upload(file:UploadFile=File(...)):
    suffix=Path(file.filename or "").suffix.lower()
    if suffix not in (".csv",".vcsv",".txt"):raise HTTPException(415,"Only CSV, VCSV and text exports supported")
    directory=ROOT/"data/uploads";directory.mkdir(parents=True,exist_ok=True)
    path=directory/(uuid.uuid4().hex+suffix);size=0;digest=hashlib.sha256()
    try:
        with path.open("xb") as out:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>64*1024*1024:raise HTTPException(413,"Maximum upload is 64 MiB")
                digest.update(chunk);out.write(chunk)
        s,rows=parse(path)
        return {"status":"audit_only","sha256":digest.hexdigest(),"rows":rows,"signals":[{"name":v.name,"unit":v.unit,"axis_unit":v.axis,"flags":v.flags} for v in s.values()],"notice":"Separate uploaded evidence. Not accepted into the scientific dataset or training; conditions and provenance require explicit review."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422,f"Upload could not be parsed: {exc}") from exc
    finally:
        await file.close()
        # Uploaded bytes are deliberately temporary; original CSVs are never touched.
        path.unlink(missing_ok=True)

@app.get("/reports/{name}")
def reports(name:str):
    if name=="performance.json":
        return JSONResponse(performance(), headers={"Content-Disposition": "attachment; filename=performance.json"})
    allowed={p.name:p for p in DERIVED.glob("*.csv")}
    allowed.update({f"{n}.json":DERIVED/f"{n}.json" for n in ("original_manifest","audit","experiments","dictionary","targets","evaluation")})
    allowed.update({n:ROOT/n for n in ("PROJECT_GUIDE.md","DATA_AUDIT.md","MODEL_CARD.md","EVALUATION_REPORT.md","ADDITIONAL_SIMULATIONS_REQUIRED.md")})
    if name not in allowed or not allowed[name].exists(): raise HTTPException(404,"Report unavailable")
    return FileResponse(allowed[name],filename=name)
