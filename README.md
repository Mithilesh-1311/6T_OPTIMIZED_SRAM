# SAMS

Local characterization, exploratory performance prediction and measured setting selection for a schematic 6T SRAM system. SAMS has no expansion. No Cadence simulation was executed by this application.

## Start on Windows PowerShell

Prerequisites: Python **3.10** and Node **22.12 or later** (verified with Python 3.10.9 / Node 22.17.1). From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r services/ml/requirements.txt
npm ci
.\.venv\Scripts\python.exe -m services.ml.pipeline all
npm run dev
```

Open **http://127.0.0.1:5173**. Node listens at 127.0.0.1:3001; Python at 127.0.0.1:8000. Keep the terminal open; Ctrl+C stops development services. Initial dependency installation depends on network speed. Full data regeneration takes approximately 90 seconds on the verification computer; inference usually takes under 1 second after imports.

For an already configured checkout with derived data, **`npm run dev`** is the only startup command. If ports are occupied, stop the previous SAMS terminal first. Services report startup/connection failures rather than supplying sample results.

## Start services separately

Run each command from the repository root in a separate PowerShell terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.ml.app:app --host 127.0.0.1 --port 8000
npm run dev --workspace apps/api
npm run dev --workspace apps/web
```

Environment examples are in `apps/api/.env.example`, `apps/web/.env.example` and `services/ml/.env.example`. Default ports require no environment files. Copy `apps/api/.env.example` to `apps/api/.env` only to change Node settings. Vite's proxy is configured in `apps/web/vite.config.ts`; Python's port comes from the Uvicorn command. Use 127.0.0.1 consistently for the browser origin. `SAMS_PYTHON` can select an alternate Python executable for the single-command launcher.

## Linux / macOS

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -r services/ml/requirements.txt
npm ci
.venv/bin/python -m services.ml.pipeline all
npm run dev
```

These commands are provided for portability; execution was verified on Windows only.

## Reproduce and verify

```powershell
.\.venv\Scripts\python.exe -m services.ml.pipeline verify
.\.venv\Scripts\python.exe -m services.ml.pipeline audit
.\.venv\Scripts\python.exe -m services.ml.pipeline extract
.\.venv\Scripts\python.exe -m services.ml.pipeline train
.\.venv\Scripts\python.exe -m services.ml.pipeline evaluate
.\.venv\Scripts\python.exe -m pytest tests -q
npm test
npm run check
npm run build
.\.venv\Scripts\python.exe scripts/integration_check.py
```

`audit` and `extract` both execute the same audited full-resolution ingestion/extraction pass; `train` and `evaluate` both execute the fixed model fitting and grouped evaluation pass. `all` runs both. Integration checking requires all three services running. Synthetic fixtures test algorithms only and are never used as scientific ML evidence. Browser visual checks require a browser; follow the demonstration procedure in PROJECT_GUIDE.md when automation is unavailable.

## Evidence and scientific status

47 original files are preserved. 30 accepted exports cover 8 active, 4 active-hold, 8 retention, 6 hold-SNM and 4 read-SNM experiments. Independent cases per regression target are **8 / 8 / 8 / 8 / 6 / 4**, respectively for write-0, write-1, active energy, quiet retention power, hold SNM and read SNM. Paired modes/states are grouped for validation. Waveform sample rows are not ML cases.

Six fixed regularized models are provided as **Exploratory**. The application compares constant, linear, ridge, Gaussian-process and forest regressors, a weighted-neighbor baseline and a bounded piecewise-linear interpolation baseline. **≥90% meaningful predictive performance is not established**: there are zero independent final-test cases. Read MODEL_CARD.md and EVALUATION_REPORT.md before interpreting predictions. Measured-only constrained comparison remains available.

Original exports in `CSVs/` are never edited, renamed or removed. The SHA-256 baseline is `data/derived/original_manifest.json`. Changing the original inventory makes regeneration fail until the dataset change is explicitly reviewed. Uploaded previews are temporary, limited to 64 MiB, kept separate from the original dataset, and never executed or automatically used for training.

## Application

React / TypeScript / Vite / Tailwind / Recharts, with self-hosted Inter and IBM Plex Mono fonts. A dark command-centre overview combines selected-run metrics, provenance, historical REPLAY waveforms, functional connectivity and explicitly separate comparisons. The compact shell shows actual polled Node/Python health and stored dataset/model versions, with a refresh/reconnect action. Framer Motion handles brief transitions; GSAP animates circuit branding without blocking loading. Express proxies requests; Python/FastAPI owns numerical extraction, inference, SQLite job state and model artifacts. All defaults bind to loopback. No cloud, paid services, layout, fabrication or automatic circuit control.

Frontend-only checks: `npm run check --workspace apps/web`, `npm run test --workspace apps/web`, `npm run build --workspace apps/web`. These do not retrain models. The scientific repeatability test in the full Python suite does regenerate artifacts; omit it when validating a visual-only change. Browser screenshot verification was unavailable in the redesign session.

The build is available in `apps/web/dist` and `apps/api/dist`. The development workflow serves the application. For a local production-build preview, run `npm exec --workspace apps/web -- vite preview --host 127.0.0.1 --port 5173` alongside the Node and Python services; the Vite proxy also applies to preview.

## Read next

PROJECT_GUIDE.md contains metric definitions, signal mappings, API contracts and a professor demonstration. DATA_AUDIT.md records file decisions. ADDITIONAL_SIMULATIONS_REQUIRED.md specifies the next evidence campaign; it does not claim that campaign was run. `progress.md` records actual checks and remaining work.

## Performance and hosted demonstration
Actual target-specific OOF tolerance scores, final-test separation, production settings and checks are documented in [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md). Run `npm run dev` locally. Hosting is prepared only; nothing has been published. Vercel serves the frontend; two Render services serve immutable evidence/inference. Hosted processing/uploads are disabled; local workflows remain available.
