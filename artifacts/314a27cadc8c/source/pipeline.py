"""Reproducible audit → extraction → exploratory evaluation and reports."""
import argparse
import hashlib
import json
import platform
import shutil
from collections import Counter
import numpy as np
import pandas as pd
from .config import ROOT, DERIVED, ARTIFACTS, MAPPING, accepted, exclusion
from .core import parse, energy, window, write_delay, survival, snm

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inventory():
    return [{"file": str(p.relative_to(ROOT / "CSVs")).replace("\\", "/"), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted((ROOT/"CSVs").rglob("*")) if p.is_file()]

def audit_extract(callback=lambda stage, detail: None):
    DERIVED.mkdir(parents=True, exist_ok=True)
    callback("hashing", "Hashing every original file")
    manifest = inventory()
    original = DERIVED/"original_manifest.json"
    if original.exists():
        if json.loads(original.read_text()) != manifest:
            raise ValueError("Original inventory changed. Restore bytes or explicitly review a new dataset before rebuilding.")
    else:
        dump(original, manifest)
    configured = accepted()
    missing = sorted(set(configured)-{m["file"] for m in manifest})
    if missing:
        raise ValueError(f"Configured accepted files absent: {missing}")
    mappings = ROOT/"data/signal_mappings.json"
    mapping = json.loads(mappings.read_text()) if mappings.exists() else MAPPING
    version = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:12]
    extractor_version=hashlib.sha256("".join((ROOT/"services/ml"/n).read_text(encoding="utf-8") for n in ("core.py","config.py","pipeline.py")).encode()+json.dumps(mapping,sort_keys=True).encode()).hexdigest()[:12]
    files, experiments = [], []
    signal_digests = {}
    for i, item in enumerate(manifest):
        callback("ingestion", f"File {i+1}/{len(manifest)}: {item['file']}")
        name = item["file"]
        decision, reason = ("accepted", "Final configured revision; signal/window checks applied") if name in configured else exclusion(name)
        entry = {**item, "id": item["sha256"][:16], "decision": decision, "reason": reason, "signals": [], "flags": []}
        try:
            signals, rows = parse(ROOT/"CSVs"/name)
            entry["rows"] = rows
            for s in signals.values():
                digest = hashlib.sha256(s.x.tobytes()+s.y.tobytes()).hexdigest()
                signal_digests.setdefault((s.name,digest), []).append(name)
                entry["signals"].append({"name": s.name, "axis_unit": s.axis, "unit": s.unit, "samples": len(s.x),
                                         "min_x": float(np.nanmin(s.x)), "max_x": float(np.nanmax(s.x)), "flags": s.flags, "sha256": digest})
                entry["flags"].extend(f"{s.name}: {flag}" for flag in s.flags)
            if name in configured:
                callback("extraction", name)
                meta = configured[name]
                run = {**meta, "id": entry["id"], "file": name, "sha256": item["sha256"], "dataset_version": version,
                       "extractor_version":extractor_version,"metrics": {}, "events": {}, "status": "measured", "flags": []}
                vdd, vret = meta["vdd_v"], meta["vret_v"]
                run["group"] = f"{meta['kind']}:{vret if meta['kind']=='retention' else vdd}:{meta['temp_c']}"
                if meta["kind"] in ("hold_snm", "read_snm"):
                    result = snm(signals["VIN"], signals["Q"], signals["QB"])
                    run["metrics"][meta["kind"]+"_mv"] = result["snm_mv"]
                    run["butterfly"] = result
                    run["flags"].append("WL/BL bias and temperature are setup-record conditions; not exported DC signals")
                else:
                    rails = {"V_MIN/PLUS": vdd, "V_RET/PLUS": vret}
                    if "net6" in signals:
                        _, main = window(signals["net6"].valid("s", "V"), 1e-9, 2e-9)
                        if abs(float(np.median(main))-vdd) > .01:
                            raise ValueError("Configured main rail contradicts exported voltage")
                    if meta["kind"] == "active":
                        _,cell_rail=window(signals[mapping["cell"]].valid("s","V"),21e-9,22e-9)
                        if abs(float(np.median(cell_rail))-vdd)>.02:
                            raise ValueError("Configured active supply contradicts measured cell rail")
                        for bit, ns in ((1,24),(0,44)):
                            result = write_delay(signals[mapping["wl"]], signals["Q"], signals["QB"], vdd, ns, bit)
                            for control,expected in ((mapping["wen"],vdd),(mapping["data"],vdd*bit)):
                                trace=signals[control]
                                if not np.all(np.diff(trace.x)>0) or abs(float(np.interp(result["wl_rise_ns"]*1e-9,trace.x,trace.y))-expected)>.1*vdd:
                                    raise ValueError("Write control contradicts configured event")
                            width=result["wl_fall_ns"]-result["wl_rise_ns"]
                            if abs(width-(2.5 if meta["mode"]==0 else 5.))>.6:
                                raise ValueError("Configured wordline mode contradicts measured pulse width")
                            run["metrics"][f"write{bit}_ps"] = result["delay_ps"]
                            run["events"][f"write{bit}"] = result
                        run["metrics"]["active_energy_fj"] = energy(signals, rails, 20, 60)
                        run["metrics"]["active_power_uw"] = run["metrics"]["active_energy_fj"]/40
                        run["windows_ns"] = {"active_energy": [20,60]}
                    else:
                        bit = meta["bit"]
                        if mapping["data"] in signals:
                            data = signals[mapping["data"]]
                            # ViVA sometimes exports digital controls with yunit; raw levels still check identity, not physical units.
                            if not np.allclose(data.y, bit, atol=.01):
                                raise ValueError("Configured stored bit contradicts exported DATA")
                        else:
                            run["flags"].append("DATA absent; stored bit checked from Q/QB and historical setup")
                        run["metrics"]["state_survived"] = survival(signals, bit, mapping["cell"])
                        run["metrics"]["quiet_power_uw"] = energy(signals, rails,25,65)/40
                        run["metrics"]["sequence_energy_fj"] = energy(signals, rails,19,75)
                        run["metrics"]["transition_excess_fj"] = run["metrics"]["sequence_energy_fj"] - run["metrics"]["quiet_power_uw"]*56
                        run["windows_ns"] = {"quiet_power": [25,65], "sequence_energy": [19,75], "survival": [[25,65],[75,100]]}
                        cell = signals[mapping["cell"]]
                        _, c = window(cell,25e-9,65e-9)
                        expected = vret if meta["kind"]=="retention" else vdd
                        if abs(float(np.median(c))-expected) > .02:
                            raise ValueError("Configured hold supply contradicts cell rail")
                    run["flags"].append("DC source polarity from documented positive-terminal convention; ideal control-source energy excluded")
                experiments.append(run)
        except (ValueError, KeyError, UnicodeError, pd.errors.ParserError) as exc:
            entry["flags"].append(str(exc))
            if decision == "accepted":
                entry["decision"] = "rejected"
                entry["reason"] = "Extraction/QC failed; see flags"
            message=str(exc).lower()
            entry["failure_category"]="electrical_failure" if "electrical failure" in message else "missing_data" if any(s in message for s in ("incomplete","missing","no columns")) else "invalid_data"
        files.append(entry)
    duplicates = [[x["file"] for x in files if x["sha256"]==digest] for digest,count in Counter(x["sha256"] for x in files).items() if count>1]
    related = [{"signal": key[0], "files": names} for key,names in signal_digests.items() if len(names)>1]
    audit = {"schema_version":1, "dataset_version":version,"extractor_version":extractor_version,"simulator_convergence":"Unknown: no authoritative Spectre run logs are available; finite curves are not proof of convergence", "files":files, "exact_duplicates":duplicates, "shared_signal_groups":related,
             "counts":dict(Counter(f["decision"] for f in files)), "accepted_waveform_rows":sum(f.get("rows",0) for f in files if f["decision"]=="accepted"),
             "provenance_limit":"Conditions combine historical setup/netlist record and trace checks; raw exports do not independently certify temperature, corner or complete topology."}
    dump(DERIVED/"audit.json", audit)
    dump(DERIVED/"experiments.json", experiments)
    targets = {"write0_ps": ("active",["vdd_v","temp_c","mode"]), "write1_ps": ("active",["vdd_v","temp_c","mode"]),
               "active_energy_fj": ("active",["vdd_v","temp_c","mode"]), "quiet_power_uw": ("retention",["vret_v","temp_c","bit"]),
               "hold_snm_mv": ("hold_snm",["vdd_v","temp_c"]), "read_snm_mv": ("read_snm",["vdd_v","temp_c"])}
    tables = {}
    for target, (kind, features) in targets.items():
        records = [{"id":r["id"],"file":r["file"],"sha256":r["sha256"],"group":r["group"], **{f:r[f] for f in features}, target:r["metrics"][target]} for r in experiments if r["kind"]==kind and target in r["metrics"] and r["metrics"].get("state_survived",True)]
        pd.DataFrame(records, columns=["id","file","sha256","group",*features,target]).to_csv(DERIVED/f"{target}.csv",index=False)
        tables[target] = {"features":features, "records":records}
    dump(DERIVED/"targets.json",tables)
    dictionary = {"schema_version":1, "units":{"write0_ps":"ps","write1_ps":"ps","active_energy_fj":"fJ","quiet_power_uw":"uW","hold_snm_mv":"mV","read_snm_mv":"mV","sequence_energy_fj":"fJ","transition_excess_fj":"fJ"},
                  "definitions":{"active_energy_fj":"Signed main+retention DC delivered energy, 20–60 ns", "quiet_power_uw":"Mean signed DC delivered power, 25–65 ns", "sequence_energy_fj":"Signed DC delivered energy, 19–75 ns, includes entry/hold/wake", "transition_excess_fj":"Sequence energy minus quiet-power × 56 ns; an excess relative to quiet baseline, not isolated switch energy", "snm":"Smaller of largest axis-aligned squares in two butterfly lobes; piecewise-linear VTCs", "state_survived":"Both nodes beyond 80%/20% of instantaneous cell rail throughout 25–65 and 75–100 ns; functional criterion, not SNM"}, "mapping":mapping}
    dump(DERIVED/"dictionary.json", dictionary)
    pd.DataFrame([{**{k:r[k] for k in ("id","file","sha256","kind","vdd_v","temp_c","vret_v","mode","bit","dataset_version","extractor_version")},**r["metrics"]} for r in experiments]).to_csv(DERIVED/"characterization.csv",index=False)
    report = ["# SAMS data audit", "", f"Dataset `{version}`. {len(files)} originals; decisions: {audit['counts']}.", f"Accepted waveform/DC data rows: {audit['accepted_waveform_rows']:,}. These are not independent ML cases.", "", audit["provenance_limit"], "", "| Original | Decision | Rows | Reason / quality flags |", "|---|---|---:|---|"]
    report += [f"| {f['file']} | {f['decision']} | {f.get('rows','unavailable')} | {f['reason']}; {'; '.join(f['flags'])} |" for f in files]
    report += ["", f"Exact duplicate groups: {duplicates}. Shared signal groups are recorded in audit.json; never count these as new runs.", "", "The accepted RETENTION_DATA0_DC export is bit 1 despite its name. Read-SNM files now exist, superseding the older guide's pending status. No public datasets were found or downloaded. Empty/invalid files, related exports and historical revisions remain preserved."]
    (ROOT/"DATA_AUDIT.md").write_text("\n".join(report),encoding="utf-8")
    return audit


def train(callback=lambda stage, detail: None):
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel, RBF
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import LeaveOneGroupOut
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import sklearn
    import joblib
    tables = json.loads((DERIVED/"targets.json").read_text())
    audit = json.loads((DERIVED/"audit.json").read_text())
    code = "".join(p.read_text(encoding="utf-8") for p in sorted((ROOT/"services/ml").glob("*.py"))).encode()
    model_version = hashlib.sha256(code+json.dumps(tables,sort_keys=True).encode()).hexdigest()[:12]
    out = ARTIFACTS/model_version
    out.mkdir(parents=True,exist_ok=True)
    for name in ("targets.json","experiments.json","audit.json","dictionary.json"):
        shutil.copyfile(DERIVED/name,out/name)
    for name in ("core.py","config.py","pipeline.py"):
        (out/"source").mkdir(exist_ok=True)
        shutil.copyfile(ROOT/"services/ml"/name,out/"source"/name)
    shutil.copyfile(ROOT/"data/signal_mappings.json",out/"source/signal_mappings.json")
    results = {}
    for target, table in tables.items():
        callback("training",target)
        records, features = table["records"], table["features"]
        n, groups_count = len(records), len({r["group"] for r in records})
        result = {"n_cases":n, "n_groups":groups_count, "features":features, "status":"unavailable", "final_test_cases":0,
                  "validation":"Leave one complete voltage/temperature condition out; paired modes/states stay together. Exploratory, no independent final test.","models":{}}
        results[target] = result
        if n < 4 or groups_count < 3:
            result["reason"] = "Insufficient independent conditions for even exploratory grouped evaluation"
            continue
        X = np.array([[r[f] for f in features] for r in records]); y = np.array([r[target] for r in records]); groups = np.array([r["group"] for r in records])
        splits = list(LeaveOneGroupOut().split(X,y,groups))
        result["splits"] = [{"train":[records[i]["id"] for i in a], "validation":[records[i]["id"] for i in b]} for a,b in splits]
        from scipy.interpolate import LinearNDInterpolator
        interpolation=[]
        categorical=[i for i,f in enumerate(features) if f in ("mode","bit")]
        continuous=[i for i in range(len(features)) if i not in categorical]
        for a,b in splits:
            for i in b:
                same=a[np.all(X[a][:,categorical]==X[i,categorical],axis=1)] if categorical else a
                value=None
                if len(same)>=3:
                    scaler=StandardScaler().fit(X[same][:,continuous])
                    xx=scaler.transform(X[same][:,continuous])
                    if np.linalg.matrix_rank(xx-xx[0])==len(continuous):
                        p=float(LinearNDInterpolator(xx,y[same])(scaler.transform(X[i:i+1,continuous]))[0])
                        if np.isfinite(p):value=p
                interpolation.append({"id":records[i]["id"],"predicted":value,"measured":float(y[i]),"reason":None if value is not None else "Held-out condition outside training convex hull; extrapolation refused"})
        covered=[p for p in interpolation if p["predicted"] is not None]
        result["interpolation_baseline"]={"method":"Piecewise-linear interpolation within training convex hull, separately per mode/state; scaler fitted only on training cases",
            "supported_cases":len(covered),"total_cases":n,"individual":interpolation,"mae_on_supported_subset":float(np.mean([abs(p["predicted"]-p["measured"]) for p in covered])) if covered else None,
            "status":"Incomplete validation coverage; not comparable to full-coverage regressors" if len(covered)<n else "Complete coverage"}
        # Fixed candidates and parameters; no test-driven tuning. Ridge is the predeclared deployed exploratory model.
        models = {"constant":lambda:DummyRegressor(), "linear":lambda:make_pipeline(StandardScaler(),LinearRegression()),
                  "ridge":lambda:make_pipeline(StandardScaler(),Ridge(alpha=.1)),
                  "local_neighbor":lambda:make_pipeline(StandardScaler(),KNeighborsRegressor(n_neighbors=2,weights="distance")),
                  "gaussian_process":lambda:make_pipeline(StandardScaler(),GaussianProcessRegressor(kernel=ConstantKernel(1.,constant_value_bounds="fixed")*RBF(1.,length_scale_bounds="fixed"),alpha=1e-6,normalize_y=True,optimizer=None,random_state=42)),
                  "random_forest":lambda:RandomForestRegressor(n_estimators=100,min_samples_leaf=2,random_state=42,n_jobs=1)}
        for name, factory in models.items():
            predicted = np.empty(n)
            for a,b in splits:
                model = factory(); model.fit(X[a],y[a]); predicted[b] = model.predict(X[b])
            residual = predicted-y
            tolerance = np.maximum(.1*np.abs(y), {"write0_ps":.1,"write1_ps":.1,"active_energy_fj":.1,"quiet_power_uw":.001,"hold_snm_mv":1.,"read_snm_mv":1.}[target])
            result["models"][name] = {"mae":float(mean_absolute_error(y,predicted)),"rmse":float(mean_squared_error(y,predicted,squared=False)),
                "r2":float(r2_score(y,predicted)) if np.ptp(y)>1e-12 else None,"within_10pct":float(np.mean(np.abs(residual)<=tolerance)),
                "individual":[{"id":r["id"],"measured":float(y[i]),"predicted":float(predicted[i]),"error":float(residual[i]),"group":r["group"]} for i,r in enumerate(records)]}
        deployed = models["ridge"](); deployed.fit(X,y)
        result.update(status="exploratory", deployed_model="ridge", domain={f:[float(X[:,i].min()),float(X[:,i].max())] for i,f in enumerate(features)},
                      residual_envelope=float(max(abs(p["error"]) for p in result["models"]["ridge"]["individual"])),
                      uncertainty="Maximum absolute grouped out-of-fold residual; descriptive error envelope, not a calibrated confidence interval")
        joblib.dump({"schema_version":1,"model_version":model_version,"dataset_version":audit["dataset_version"],"features":features,"target":target,"sklearn_version":sklearn.__version__,"model":deployed},out/f"{target}.joblib")
    evaluation = {"schema_version":1,"model_version":model_version,"dataset_version":audit["dataset_version"],"seed":42,
                  "python":platform.python_version(),"sklearn":sklearn.__version__,"target_90_established":False,
                  "metric_policy":"Primary: MAE in target units. Also RMSE, pooled OOF R² and fraction within ±10% (absolute floors: delay 0.1 ps, energy 0.1 fJ, power 0.001 uW, SNM 1 mV). Frozen before training. 90% target = at least 90% within tolerance on independent final cases; none exist.",
                  "selection_policy":"Fixed ridge alpha=0.1 deployed for exploratory use; all candidates reported, no winner chosen on validation results. No final test set or broad generalization claim.",
                  "targets":results}
    dump(out/"evaluation.json",evaluation)
    dump(ARTIFACTS/"current.json",{"model_version":model_version,"dataset_version":audit["dataset_version"]})
    dump(DERIVED/"evaluation.json",evaluation)
    lines = ["# SAMS evaluation report","",evaluation["metric_policy"],"",evaluation["selection_policy"],"",f"Dataset `{audit['dataset_version']}`; model `{model_version}`; seed 42; Python {platform.python_version()}; scikit-learn {sklearn.__version__}.","", "| Target | Cases / groups | Model | MAE | RMSE | R² | Within tolerance |","|---|---|---|---:|---:|---:|---:|"]
    for target,r in results.items():
        for name,m in r["models"].items():
            lines.append(f"| {target} | {r['n_cases']} / {r['n_groups']} | {name} | {m['mae']:.6g} | {m['rmse']:.6g} | {m['r2']:.4f} | {m['within_10pct']:.1%} |")
    lines += ["", "≥90% meaningful independent predictive performance is NOT established. All numbers above are exploratory grouped cross-validation. Final independent test cases: 0. Individual errors and exact split membership are downloadable in evaluation.json. Waveform samples, synthetic fixtures, older revisions and related exports are never ML observations.","", "Local-neighbor is a sparse interpolation baseline; it does not establish a densely validated surface. Some folds require extrapolation because the existing voltage/temperature matrix contains only boundary levels. Full-data fitted models are provided only for exploratory scenario investigation; setting selection uses measured candidates."]
    lines += ["", "## Bounded interpolation baseline", "", "Piecewise-linear interpolation refuses points outside each training fold's convex hull; categorical mode/state are handled separately. Subset MAE is not compared to full-coverage regressors."]
    for target,r in results.items():
        if "interpolation_baseline" in r:
            b=r["interpolation_baseline"]
            lines.append(f"- {target}: {b['supported_cases']}/{b['total_cases']} validation cases inside the training hull; subset MAE {b['mae_on_supported_subset']}. Full predictions and refusal reasons are in evaluation.json.")
    (ROOT/"EVALUATION_REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    return evaluation

def main():
    arg = argparse.ArgumentParser(); arg.add_argument("command",choices=["audit","extract","train","evaluate","all","verify"])
    command = arg.parse_args().command
    if command == "verify":
        assert inventory() == json.loads((DERIVED/"original_manifest.json").read_text()), "Original bytes changed"
        print("All original hashes and inventory unchanged"); return
    if command in ("audit","extract","all"):
        a = audit_extract(lambda s,d: print(s,d,flush=True)); print(a["counts"])
    if command in ("train","evaluate","all"):
        e = train(lambda s,d: print(s,d,flush=True)); print("Model version",e["model_version"])

if __name__ == "__main__":
    main()
