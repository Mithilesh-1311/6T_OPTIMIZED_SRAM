# SAMS deployment readiness

Local preparation only. Nothing has been pushed, published or purchased. The configurations are a reviewable demonstration release, not a claim of cloud deployment or production capacity. Publication requires explicit instruction.

## Release evidence

Dataset `56fd2a89b9e4`; model `314a27cadc8c`; Python 3.10.9; scikit-learn 1.3.2; Node 22.17.1. Original exports, derived labels, all historical models and their source snapshots are unchanged: 137 SHA-256 checks passed against `reports/release-preservation-baseline.json`.

All six ridge targets score 100% within the frozen tolerance on exploratory grouped OOF validation: write0/write1/active energy/quiet retention power 8/8 each, 4 groups; hold SNM 6/6, 6 groups; read SNM 4/4, 4 groups. Independent final test: 0 cases for every target, Not evaluated. Constant SNM baselines also score 100%. No cross-target average or selected-case pseudo-accuracy. Complete MAE/RMSE/baselines/counts are in EVALUATION_REPORT.md and `reports/performance.json`.

## Exact local checks and results

Vercel configuration guard also passed explicit valid-HTTPS, missing-value, HTTP-localhost and embedded-credentials cases.

| Check | Command | Result |
|---|---|---|
| Scientific/parser/units/energy/SNM, API/model loading and inference, OOF evidence, fold replay, zero/missing labels, private bundle and hosted authentication | `.venv/Scripts/python.exe -m pytest tests/test_science.py tests/test_api.py tests/test_performance.py -q` | 23 passed; one existing multipart import deprecation warning |
| API contracts, strict origins/hosts, hosted write refusal, server token forwarding | `npm test` | 3 passed |
| Dashboard/report consistency, baseline, conservative rounding, unavailable state, context and contrast | `npm run test --workspace apps/web` | 7 passed |
| Frontend/backend TypeScript | `npm run check` |Passed |
| Frontend/backend production build | `npm run build` |Passed; no chunk-size warning |
| Actual frontend proxy to Node to Python; real inference, comparisons, waveforms, artifact/report equality | `.venv/Scripts/python.exe scripts/integration_check.py` |Passed |
| Local production processes with assigned ports and 0.0.0.0 binding; Python readiness/auth/read-only state; Node liveness and upstream failure; isolated restoration of all private exports; preservation hashes | `.venv/Scripts/python.exe scripts/release_smoke.py` |Passed; 30 accepted exports restored byte-for-byte; 137 protected hashes unchanged |
| Render HTTPS Node-to-ML proxy | `npm test` forwarding contract; local production failure check |Token/header path verified by mocked HTTPS upstream. Actual hosted TLS/health checks unrun until publication |
| Browser, desktop/narrow screenshots, interactive error-state smoke | Browser inventory |Unavailable:apps=[] and browsers=[]; no visual/browser result claimed |
| Linux/Render clean build and Vercel cloud build | Not executed |Local Windows builds passed; first authorized deployment must verify native wheels, provisioning, SPA deep links and capacity |

A missing/invalid performance report now leaves measured-data routes available, with explicit Not evaluated and the reporting error; no placeholder score is substituted. The reviewer approved this error-state behavior.

The read-only replay test clones each trusted ridge+scaler pipeline, fits only saved training IDs and reproduces each stored held-out vector within 1e-12. It never saves a fitted model. `tests/test_reproducibility.py` is deliberately not invoked because its historical train() tests rewrite authoritative artifacts; repeatability here is checked through read-only fold replay.

## Reviewer findings and resolutions

A single reused read-only reviewer independently reconstructed every ridge OOF vector exactly, checked group separation, preprocessing inside training folds, unique source hashes per target, finite labels and selected-case training membership. Initial findings:

| Severity | Evidence/location | Impact | Correction |
|---|---|---|---|
|High |Node localhost binding/host list; Python TrustedHost |Render unreachable |Node production 0.0.0.0/PORT; Python start command 0.0.0.0/$PORT; explicit Render hostname; local restrictions retained |
|High |waveforms requires ignored CSVs |Fresh clone loses replay |Private accepted-only archive provisioner, per-file manifest hashes, whole-archive checksum; startup fails if evidence is missing |
|High |public jobs/uploads mutations |Uncontrolled processing/model writes |Hosted mode rejects both routes at Node and Python; service token; UI controls disabled from actual capabilities |
|Medium |generic overview card |Available OOF results hidden |Shared verified Python report and target-specific cards with denominator/groups/MAE/RMSE/baseline/final status |
|Medium |selected case has no training membership/error |Fit mistaken for validation |Python computes selected-case relative error and verifies versioned training-table membership; UI labels it separately |
|Medium |apps/web/src/api.ts contained extra Unicode bytes in unit/temperature labels |Displayed units were corrupted |Explicit UTF-8 fix and exact-codepoint assertions for ?W and ?C |

Focused re-review closed: no unresolved critical/high findings for local preparation. The reviewer independently verified report/API/snapshot equality, selected-case provenance, conservative percentage formatting, strict HTTPS origins and corrected unit codepoints. An additional medium finding (mojibake in power/temperature labels) was fixed with explicit UTF-8 handling and regression assertions. Browser/cloud/capacity checks remain unrun. Reviewer cannot independently certify the historical timing of predeclaration; UI/report therefore use exploratory model-selection validation wording.

## Vercel configuration

Project root:repository root. `vercel.json` installs with `npm ci`, verifies public API configuration, runs `npm run build --workspace apps/web`, publishes only `apps/web/dist`, and rewrites SPA deep links to index.html. Use the existing package-lock.json; do not publish original exports, model files or private notes. `.vercelignore` excludes evidence, scientific code, archives and environment files from Vercel uploads. No frontend secret is required.

Set **VITE_API_BASE_URL=https://<approved-node-service>.onrender.com/api** in the Vercel build environment. Rebuild when it changes. The build rejects missing/HTTP/local/credentialed URLs on Vercel. The API client, reports, uploads and health calls all use the same base URL. Preview deployments are not automatically allowed through production CORS; approve an exact preview origin separately if needed. Do not add wildcard access.

## Render configuration and variables

`render.yaml` prepares two **free web-service** demonstrations, automatic deploys off; no paid disk/database/private service selected. Set repository root as each service root.

| Service | Build | Start | Health/readiness |
|---|---|---|---|
|Node |`npm ci && npm run build --workspace apps/api` |`node apps/api/dist/server.js` |`/health` liveness; `/api/ready` proxied scientific readiness |
|Python |`pip install -r services/ml/requirements.txt && python scripts/evidence_bundle.py provision` |`python -m uvicorn services.ml.app:app --host 0.0.0.0 --port $PORT` |`/health` liveness; `/ready` checks frozen evidence, all models/schema/library versions and raw-file availability |

| Variable | Where | Required value |
|---|---|---|
|SAMS_DEPLOYMENT |Both servers |production |
|NODE_ENV / NODE_VERSION |Node |production / 22.17.1 |
|PYTHON_VERSION |Python |3.10.9, matching current verified environment |
|PORT |Both |Render-assigned; do not replace with localhost defaults |
|RENDER_EXTERNAL_HOSTNAME |Both |Render-supplied hostname; allowed explicitly |
|WEB_ORIGIN |Node |Exact approved HTTPS frontend origin, no trailing slash/path/wildcards |
|ML_URL |Node |Exact Python service HTTPS URL, no trailing slash, e.g.https://<service>.onrender.com |
|ML_SERVICE_TOKEN |Both |Same cryptographically random secret, 32+ characters; server-only, never VITE_ |
|SAMS_EVIDENCE_URL |Python build only |Private HTTPS archive URL with credentials kept in Render secrets; must remain available for authorized rebuilds |
|SAMS_EVIDENCE_SHA256 |Python build only |SHA256 of that exact private archive |

Python environment examples are not loaded implicitly. Configure real platform variables. Render free web services cannot receive private-network traffic, so this free demonstration uses HTTPS plus a shared token for service-to-service requests. Python scientific endpoints reject direct unauthenticated requests; public health/readiness reveal status/version only. Node deliberately exposes read-only analysis and inference to the approved frontend. CORS is not user authentication; this is a public demonstration, not a confidential multi-user application.

## Evidence provisioning and persistence

The private archive has been generated locally at `deployment/sams-evidence.zip` (148483119 bytes), SHA256 `6e80b450bb2252a10314c9dc81a5876331f6e2fe98e4b79fda4775a8f6e4bc73`. It contains exactly 30 accepted exports, 804801432 expanded bytes, without renaming or editing any original. Archive is ignored by Git and Vercel. Never put it in frontend/public assets. `pack` opens a new archive exclusively and refuses overwriting an existing archive. Provisioning accepts exactly the manifest names, rejects traversal/duplicates/nonmatching hashes, verifies every file before writing, and refuses to overwrite a differing existing export. Limits: 256 MiB archive and 1 GiB expanded content. Unaccepted originals remain preserved locally.

After publication authorization, provision a **private** HTTPS download location for this archive using an existing authorized storage arrangement; no provider or paid storage has been purchased. Set the URL/checksum as Python build secrets. This is a remaining external setup requirement. The Render build restores it to the private server filesystem; no raw-file download endpoint exists. The committed current artifact directory and derived tables must also be included in the private backend source checkout; `git ls-files artifacts/314a27cadc8c` confirms current artifacts are tracked. Do not expose historical personal notes in a public repository.

Hosted mode is immutable: it writes no jobs SQLite DB, does not accept audit uploads and cannot retrain or switch current artifacts. GET jobs returns an empty list because processing is local-only, not a fabricated completed history. The UI states these limitations and disables controls based on live service capabilities. Measurements, all charts, inference, setting comparison and report downloads remain supported. Local mode retains uploads, processing, SQLite history and existing model history. Runtime filesystem changes are **not** assumed durable. Frozen models/data and the private archive are build inputs restored on each deployment. No database is needed for this read-only demonstration. Durable hosted processing would require separately authorized persistent storage/database and access control; do not enable mutations on ephemeral SQLite.

## Costs and remaining blockers

The draft selects free compute only and no paid resources. Free Render services sleep after 15 minutes, may take about 60 seconds to wake and share 750 instance hours per workspace/month; two continuously awake services exceed that shared monthly allowance. Build/bandwidth limits apply. No cost guarantee is made; do not attach a payment method, enable overage or upgrade without authorization. Free instances are demonstration capacity; actual ML waveform memory/latency has not been tested on Render. An 805 MB raw dataset and Python parsing may exceed available memory under concurrent/cached replay. No paid capacity is selected to mask this uncertainty.

Before publication:explicit user instruction, private source/evidence storage and URL/checksum provisioning, approved Vercel/Render domains and matching server token, focused review closure, manual browser desktop/mobile/error checks. After publication:clean native Linux build, HTTPS end-to-end/auth/CORS, all eight SPA routes and downloads, cold starts and measured memory/latency. Final scientific validation requires new independent Cadence cases; see ADDITIONAL_SIMULATIONS_REQUIRED.md. No Cadence simulation was run here.

## Rollback

Keep automatic deployment off. Preserve this working tree, package-lock, Python pins, `artifacts/current.json`, the entire current version directory, frozen derived evidence and the private archive/checksum before an authorized release. If the release fails, restore the previous Vercel frontend deployment and both previous Render service deployments together. Restore matching environment URLs/token and immutable model/dataset versions; verify `/api/ready`, `/api/performance`, one inference, replay and report equality before reopening the demonstration. No database migration is involved. Never overwrite original exports or replace historical artifacts. Render Free retains only its two most recent prior deploys, so keep a local/private source release snapshot too.

## Reproduction and local launch

Windows PowerShell from the project root, using the already installed environment:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_science.py tests/test_api.py tests/test_performance.py -q
npm test
npm run test --workspace apps/web
npm run check
npm run build
npm run dev
```

In a second terminal while local services run:

```powershell
.venv/Scripts/python.exe scripts/integration_check.py
.venv/Scripts/python.exe scripts/release_smoke.py
```

To create the private archive on a new checkout with original exports already provisioned: `.venv/Scripts/python.exe scripts/evidence_bundle.py pack` (run once; do not overwrite the prepared archive). To print the verified report without modifying scientific artifacts: `.venv/Scripts/python.exe -m services.ml.performance`. Linux/macOS equivalents use `.venv/bin/python`; npm commands are identical. Fresh environment setup remains in README.md. Do not run `pipeline all/train` during this release verification.

## Official platform references inspected

Configuration follows [Vercel Vite SPA documentation](https://vercel.com/docs/frameworks/frontend/vite), [Vercel project configuration](https://vercel.com/docs/project-configuration/vercel-json), [Render web service port binding](https://render.com/docs/web-services), [Render Blueprint fields](https://render.com/docs/blueprint-spec), [Render Python versions](https://render.com/docs/python-version), [Render ephemeral and persistent filesystems](https://render.com/docs/disks), and [Render Free limitations](https://render.com/docs/free). These were checked during local preparation; recheck terms before an authorized publication.
