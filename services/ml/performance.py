"""Reporting from frozen OOF evidence; does not fit or change a model."""
import json
import math
from .config import DERIVED, ARTIFACTS

# These are the existing pipeline's predeclared floors, not newly tuned thresholds.
FLOORS = dict(write0_ps=.1, write1_ps=.1, active_energy_fj=.1,
              quiet_power_uw=.001, hold_snm_mv=1., read_snm_mv=1.)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(evaluation, tables):
    result = {"model_version": evaluation["model_version"],
              "dataset_version": evaluation["dataset_version"],
              "method": "Leave-one-operating-condition-group-out cross-validation",
              "status": "Exploratory model-selection validation; not an untouched final test",
              "policy": evaluation["metric_policy"], "targets": {}}
    for target, spec in evaluation["targets"].items():
        if spec["status"] == "unavailable":
            result["targets"][target] = {"status": "Not evaluated"}
            continue
        records = tables[target]["records"]
        by_id = {r["id"]: r for r in records}
        require(len(by_id) == len(records) == spec["n_cases"], "Duplicate case IDs")
        require(len({r["sha256"] for r in records}) == len(records), "Duplicate source hashes")
        require(tables[target]["features"] == spec["features"], "Feature schema mismatch")
        require(len({r["group"] for r in records}) == spec["n_groups"], "Group count mismatch")
        held_out = []
        for split in spec["splits"]:
            train, valid = set(split["train"]), set(split["validation"])
            require(train and valid and train.isdisjoint(valid) and train | valid == set(by_id), "Invalid split")
            require({by_id[i]["group"] for i in train}.isdisjoint({by_id[i]["group"] for i in valid}), "Group leakage")
            held_out.extend(split["validation"])
        require(len(held_out) == len(set(held_out)) == len(records), "Incomplete/repeated OOF cases")
        scores = {}
        for model, saved in spec["models"].items():
            rows = saved["individual"]
            require(len(rows) == len({r["id"] for r in rows}) == len(records), "Missing/repeated predictions")
            errors, passed, details = [], 0, []
            for row in rows:
                source = by_id[row["id"]]
                measured, predicted = row["measured"], row["predicted"]
                require(type(measured) in (int, float) and type(predicted) in (int, float), "Missing label/prediction")
                require(math.isfinite(measured) and math.isfinite(predicted), "Nonfinite label/prediction")
                require(measured == source[target] and row["group"] == source["group"], "Label/group mismatch")
                error = predicted - measured
                tolerance = max(.1 * abs(measured), FLOORS[target])
                within = abs(error) <= tolerance
                passed += within
                errors.append(error)
                details.append({**row, "tolerance": tolerance, "within_tolerance": within})
            n = len(errors)
            mae = sum(map(abs, errors)) / n
            rmse = math.sqrt(sum(e*e for e in errors) / n)
            require(math.isclose(mae, saved["mae"], abs_tol=1e-10), "Stored MAE mismatch")
            require(math.isclose(rmse, saved["rmse"], abs_tol=1e-10), "Stored RMSE mismatch")
            require(math.isclose(passed/n, saved["within_10pct"], abs_tol=1e-12), "Stored score mismatch")
            scores[model] = {"passing": passed, "evaluated": n, "percentage": 100*passed/n,
                             "mae": mae, "rmse": rmse, "individual": details}
        result["targets"][target] = {"status": result["status"], "groups": spec["n_groups"],
            "absolute_tolerance_floor": FLOORS[target], "final_test_cases": spec["final_test_cases"],
            "final_test_status": "Not evaluated" if spec["final_test_cases"] == 0 else "Separate evidence required",
            "deployed_model": spec["deployed_model"], "models": scores}
    return result


def report():
    evaluation = json.loads((DERIVED/"evaluation.json").read_text(encoding="utf-8"))
    tables = json.loads((DERIVED/"targets.json").read_text(encoding="utf-8"))
    frozen = ARTIFACTS/evaluation["model_version"]
    require(evaluation == json.loads((frozen/"evaluation.json").read_text(encoding="utf-8")), "Evaluation differs from versioned artifact")
    require(tables == json.loads((frozen/"targets.json").read_text(encoding="utf-8")), "Labels differ from versioned artifact")
    return summarize(evaluation, tables)


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, allow_nan=False))
