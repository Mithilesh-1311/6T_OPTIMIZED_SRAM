# SAMS progress

## Completed
- Phases1–4 implemented: hashed immutable evidence, audited30/47 accepted exports, full-resolution metrics, six exploratory targets, local Python/Node services and all eight React views.
- Clean Python3.10.9 virtual environment installed from33 pinned requirements; `pip check` passed. Node22.17.1, npm10.9.2; resolved npm lockfile. No original application or Git changes existed; initialized a local repository for requested lockfile/code versioning.
- Numerical validation: units, paired independent grids, finite/monotone axes, crossing direction, persistence, signed integration, analytic largest-square SNM and historical measurement rounding. Grouping/leakage and repeatable evaluation checked.
- Backend and live integration: validation, stale models, schema compatibility, missing data, upload boundaries, measured feasibility, HTTP proxy, inference, waveforms and byte-identical report downloads. Production build and TypeScript checks passed. Two Node tests passed. All18 clean-environment Python tests passed, including job metadata and single-writer behavior.
- Required audit, model card, evaluation, additional-simulation plan, setup guide, API contracts and professor demonstration written without personal details. Original historical guide and architecture image remain untouched and excluded from the application/version control.

## Implementation status
Phases1?5 complete for the evidence-supported local software. All18 Python tests,2 Node tests, TypeScript checks, production builds and live integration checks pass. A full real processing job completed in66.36 seconds with hashing/ingestion/extraction/training stages and concurrent-job rejection. Original SHA-256 inventory reverified unchanged. Source, lockfiles, documentation, derived evidence and the current versioned artifacts are included in the local implementation commit; originals/private history/caches/dependencies are excluded. No push or publication.

## Scientific blockers / remaining work
No independent final-test evidence:≥90% meaningful predictive performance is not established. New simulation campaign is specified but unexecuted. Original ADE/netlist/log packages would strengthen condition and convergence provenance. Browser-control inventory was empty; in-app browser creation returned unavailable, so rendered visual/browser smoke tests remain unrun. Manual demonstration procedure is in PROJECT_GUIDE.md. Linux/macOS commands are documented but not executed.

## Versions and actual evaluation
Dataset `56fd2a89b9e4`;1,693,678 accepted waveform/DC sample rows. Current model `314a27cadc8c` (also in artifacts/current.json); schema1; scikit-learn1.3.2; seed42. Separate targets: write0/write1/active energy/retention power each8 cases and4 groups; hold SNM6 cases/6 groups; read SNM4 cases/4 groups. All six deployed models are Exploratory ridge. Read-output delay and failure classification remain unavailable.

Ridge OOF MAE:0.4044 ps /0.7681 ps /2.5003 fJ /0.005791 uW /1.1951 mV /0.2381 mV in the target order above. OOF within-tolerance fractions are100%, with **zero final-test cases**. Constant baselines already pass the SNM tolerance, so these tiny fractions are not proof of useful generalization. Complete RMSE/R², every baseline, interpolation coverage, split membership and individual errors are stored in EVALUATION_REPORT.md and evaluation.json.

## Meaningful commands / outcomes
`python -m services.ml.pipeline all`:30 accepted,14 superseded,1 ambiguous,2 rejected; six target tables and versioned models. `python -m services.ml.pipeline verify`: all original hashes/inventory unchanged. `python -m pytest tests -q`:18 passed,2 nonblocking dependency/environment warnings. `npm test`:2 passed. `npm run check`:both workspaces passed. `npm run build`:frontend and backend passed, no chunk-size warning after bundle splitting. `python scripts/integration_check.py`:live Vite→Node→Python, inference, measured choices, waveforms, documentation/table/report equality passed.

Nonblocking environment warnings: Starlette's legacy multipart import emits a deprecation warning; joblib cannot query physical cores via removed Windows tooling and falls back to logical cores. Models remain deterministic in repeated evaluation. Initial sandbox process restrictions required approved build/test execution outside the sandbox.

## Exact next action
Open http://127.0.0.1:5173. Services are running locally. On a later session, read this file and PROJECT_GUIDE.md first, then use `npm run dev` if services are stopped. Independent final validation requires the separately specified Cadence campaign; do not claim it has run.
