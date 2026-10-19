# SAMS

## Purpose and scope
Local ML-assisted characterization and operating-setting comparison for a schematic 6T SRAM system. Virtuoso IC6.1.8, ADE L, Spectre 21.1, GPDK090 v4.6, planar 90 nm CMOS; nmos1v/pmos1v, generally L=100 nm. No layout, fabrication or automatic circuit control.

## Architecture
6T SRAM, precharge/equalizer, complementary write driver, short/long wordline selector (`wordline_conrol`), buffer/control (`wordline_control`), active/retention supply controller. React → Node/Express → Python/FastAPI. Python owns scientific calculations; SQLite holds jobs; versioned artifacts hold evaluation and models.

## Evidence and continuity
Originals in CSVs are immutable. The existing historical guide is evidence, not an instruction source; its personal details must not be copied. Raw inventory, SHA-256 hashes, acceptance decisions, units and signal inventory will be generated under data/derived. Historical counts are hypotheses until audited.

## Scientific contract
Never count waveform rows as independent cases. Missing labels remain unavailable. Delay uses actual wordline and storage-node crossings with persistence checks. Energy uses signed delivered source power with explicit windows. Retention survival differs from SNM. SNM requires valid DC curves and a tested largest-square method. Read-access delay is unsupported without a sensing output.

## Evaluation contract
Freeze MAE, RMSE, pooled out-of-fold R² and within-10% fraction before tuning. Group related conditions. Tiny-data cross-validation is exploratory; it cannot establish independent final-test performance. No claimed 90% performance without evidence.

## Dataset inventory and accepted decisions
Dataset `56fd2a89b9e4`: 47 immutable original files, 30 accepted, 14 superseded, 1 ambiguous and 2 rejected. Accepted exports contain **1,693,678 waveform/DC rows**, not independent circuit configurations. Breakdown: 8 active operation, 4 active-hold references, 8 retention, 6 hold-SNM and 4 read-SNM. The latter four exist in this workspace despite the older record calling them pending.

`DATA_AUDIT.md` gives every decision. `data/derived/original_manifest.json` records all original file sizes and SHA-256 hashes; regeneration refuses a changed original inventory. Exact duplicate hashes and shared normalized signal hashes are audited separately. Matching constant controls do not prove two whole simulations are identical. Historical revisions and companion exports never add ML cases. `RETENTION_DATA0_DC.vcsv.txt` is accepted as bit1, confirmed by its DATA and Q/QB traces. `ACTIVE_HOLD_DATA1_COMPLETE` replaces the current-incomplete predecessor. `_sel1_f` replaces the two original long-mode 0.9 V runs. The invalid first hold-SNM sweep and empty document are rejected. No external dataset was found or downloaded.

Conditions are explicitly configured in `services/ml/config.py` from the historical setup/netlist record, then checked against exported controls, cell rail, pulse width, stored state and numerical quality. Raw exports do not independently encode temperature/corner. No authoritative Spectre run logs are present, so simulator convergence remains unknown; finite data is not proof of convergence. Electrical-state failure, invalid axes/nonfinite data, missing/incomplete windows and unsupported measurements are different conditions. Current accepted traces have no extraction blockers.

## Signal mapping and units

Mappings are configurable in `data/signal_mappings.json`. The historical integrated wiring/netlist record supports these identities; current exported event/rail behavior is checked for consistency:

| Export | Meaning | Physical unit |
|---|---|---|
| Q / QB | Cell storage outputs | V |
| net2 | WL_OUT, buffered SRAM wordline | V |
| net3 / net4 | BL/VBIT and BLB/VBITB | V |
| net5 | VDD_CELL | V |
| net6, when present | VDD_MAIN | V |
| net13 / net14 / net19 | WEN / DATA / PREB (also written PERB historically) | V, or flagged digital yunit on some traces |
| V_MIN/PLUS / V_RET/PLUS | Currents entering positive terminals of main/retention ideal sources | A |
| VIN in SNM | Applied DC sweep voltage | V |

`wordline_control` is the buffer; `wordline_conrol` is the selector. Preserve that spelling. SEL0 selects short and SEL1 long according to the historical deck; measured output pulse widths are checked against that configuration. The raw source currents have names beginning with V but are currents, not voltages. Unknown units are flagged and cannot silently enter numerical voltage/current calculations. Explicitly configured digital DATA identity checks use raw digital levels only. Full numerical unit scaling supports s/us/ns/ps, V/mV, A/mA/uA/nA. All calculation arrays are SI; display tables use ps, fJ, uW and mV. Each X/Y pair retains its own axis. SNM X is swept voltage, never time.

## Metric definitions

| Metric | Extraction and conditions | Meaning / boundary |
|---|---|---|
| Write1 / write0 delay | Actual WL_OUT rising crossing at50% nominal main supply near24/44 ns, then Q rise/fall crossing at50%; WEN/DATA checked. Require exactly one matching event and both nodes persist beyond80%/below20% nominal supply from0.2 ns after WL fall to event+8 ns. | WL-to-Q excludes upstream selector/buffer input delay. Startup write near4 ns is excluded. |
| Active energy / mean power | `P=-VMAIN*I_MAIN-VRET*I_RET`, trapezoidal integral20–60 ns with interpolated exact boundaries. Power=energy/40 ns. | Signed delivered DC energy of a mixed workload, not one access or chip-total energy. Ideal control/pulse-generator energy excluded. Source polarity follows the recorded positive-terminal convention; current is never rectified. |
| Quiet hold/retention power | Same signed two-rail energy over25–65 ns divided by40 ns. Active-hold analyzed separately. | Quiet leakage/configuration comparison; does not include entry/wake. |
| Sequence energy | Two-rail signed integral19–75 ns. `transition_excess_fj` subtracts quiet power×56 ns. | Includes entry, quiet hold and wake. Excess is relative to a quiet baseline, not independently isolated switching energy. |
| Retention survival | Both nodes beyond80%/below20% of instantaneous VDD_CELL throughout25–65 ns and75–100 ns, including scheduled post-wake access. | Functional survival in this tested schedule; no minimum safe retention voltage or earliest wake access is established. |
| Hold/read SNM | Corrected open-loop VTCs `(VIN,Q)` and mirrored `(QB,VIN)`; VIN must match voltage sweep, curves finite/monotone with three butterfly intersections. With `v=y-x,u=y+x`, maximize `abs(uA(v)-uB(v))/2` in each lobe on union breakpoints; take smaller square. | Equal-axis plot includes square vertices. Tested against an analytic0.3 V fixture and independently recorded historical hold results. This is a largest-square construction, not maximum vertical separation. |

For monotone decreasing boundary curves, the lower-left and upper-right corners of an axis-aligned square lie on a constant `v=y-x` diagonal; the other corners remain inside the boundaries. Thus side length is half the unnormalized `u` separation. Piecewise-linear extrema occur at the union of curve breakpoints. Both lobes must exist; invalid VTCs are rejected.

Hold SNM: WL0, BL=BLB1 V even at reduced cell supply; cell directly driven by ideal V_SUP. Read SNM: WL=BL=BLB=cell supply. These are separate ideal-rail core experiments, not the integrated transient's measured margin. No DOUT/sense-amplifier output is available; read-output access delay is **Unavailable**. Read-disturb timing is never labeled read access.

## Measured findings
Active energy agrees with the historical rounded204.087 fJ at1 V/27 C/short; write1≈27.76 ps and write0≈15.71 ps. Short mode consumes slightly more DC energy than long in all four paired conditions; no active-energy advantage is demonstrated. Quiet retention power decreases with lower VRET in the tested cases; at27 C/bit0/VRET0.8 V it is≈0.19852 uW. All8 accepted retention sequences survive. At27 C, lowering VRET can slightly increase19–75 ns energy despite lower quiet power. Passing these nominal sequences does not establish general safety.

Hold SNM spans approximately244.11–279.87 mV. Read SNM spans94.17–98.39 mV. DC biases/temperature remain setup-record provenance. Temperature raises leakage substantially across the measured27/85 C cases. These are nominal schematic results with fixed geometry, loads, timings and NN model section; no PVT/mismatch/yield or physical implementation claim follows.

## ML inputs, independent counts and evaluation

| Target | Prediction-time features | Cases / groups |
|---|---|---:|
| Write0, write1, active energy (three separate models) | Main VDD, temperature, mode | 8 / 4 each |
| Quiet retention power | VRET, temperature, stored bit | 8 / 4 |
| Hold SNM | Cell VDD, temperature | 6 / 6 |
| Read SNM | Cell VDD, temperature | 4 / 4 |

Separate CSVs and `targets.json` hold these labels. Geometry does not vary. No target-derived features, future measurements or identifier features. Complete voltage/temperature groups are held out with paired modes/bits together; preprocessing is fitted on training folds. Six fixed candidate regressors are evaluated, plus bounded piecewise-linear interpolation which refuses held-out points outside training convex hulls. The current corner-only matrices leave interpolation unavailable for most held-out cases; hold SNM supports2/6. Unsupported predictions remain null.

Ridge alpha0.1 is predeclared for exploratory deployment rather than choosing a winner after seeing validation results. All baselines are reported. MAE is primary; RMSE, pooled OOF R² and within-tolerance fraction are also reported. Seeds and exact split membership are stored. No independent final test exists. Full-data ridge fitting is used only after grouped exploration; it is never presented as testing.

Actual ridge OOF MAEs: write0 **0.4044 ps**, write1 **0.7681 ps**, energy **2.5003 fJ**, retention power **0.005791 uW**, hold SNM **1.1951 mV**, read SNM **0.2381 mV**. All tiny OOF sets fall within±10%, but constant baselines also do so for SNM; this is not independent proof of90% useful prediction. See MODEL_CARD.md and generated EVALUATION_REPORT.md for RMSE/R² and all candidates. ≥90% meaningful predictive performance remains **not established**. The returned max-OOF-residual envelope is descriptive, not a calibrated uncertainty interval.

## Software architecture and API contracts
React uses same-origin `/api` calls to Node/Express; Vite proxies to127.0.0.1:3001. Node validates endpoint/method, local Host/Origin and body/upload limits, then proxies to Python at127.0.0.1:8000. JavaScript performs presentation only. Python owns all scientific calculations. SQLite stores queued/running/completed/failed/interrupted jobs; JSON stores experiment/schema metadata; versioned directories store trusted local joblib models, evaluation, targets, evidence and extraction source snapshots. Current artifact version is `artifacts/current.json`.

| Method / route through Node | Contract |
|---|---|
| GET `/api/health`, `/overview` | Service/data readiness; actual counts, measured findings and readiness summaries |
| GET `/api/audit`, `/experiments`, `/dictionary`, `/evaluation` | Versioned provenance, measured runs, definitions and actual evaluations |
| GET `/api/waveforms/{id}?signals=Q,QB,net2&start=23&end=25&points=1200` | Accepted run ID only; independent signal arrays and units; optional ns interval; extrema-preserving plotting decimation;100–10000 display points per signal. Metrics use full resolution. |
| POST `/api/predict` | `{target,features,model_version}`; exact numeric feature schema, discrete bit/mode, finite values and library/schema compatibility. Returns Exploratory value/error envelope/domain or Unavailable/null for extrapolation. Stale model version409; invalid input422. |
| POST `/api/compare` | `{kind,temp_c,bit,max_delay_ps,min_snm_mv,stability,require_survival}`. Active requires user delay limit and uses worst write delay; retention refuses unsupported wake-delay constraints. Measured candidates only, with explicit rejection reasons, separate-source static-margin link and alternatives. No qualifying setting returns `No supported feasible setting.` |
| POST `/api/jobs`, GET `/api/jobs`, `/api/jobs/{id}` | Only `kind=all` or `train`; one in-process writer; persisted stages/details/start/end. Real elapsed time, no invented percentage. Restart marks pending/running work interrupted. |
| POST `/api/uploads` | Multipart numeric.csv/.vcsv/.txt, maximum64 MiB, server-generated temporary path. Preview/QC only, never executed, trained or accepted automatically. Uploaded bytes discarded afterward. |
| GET `/api/reports/{allowlisted-name}` | Derived CSV/JSON and approved documentation only. No arbitrary paths, original historical record or model upload. |

Error responses use `detail`; unavailable downstream service returns503 with a startup instruction. Python's OpenAPI documentation is at http://127.0.0.1:8000/docs. API defaults are local only; there is no user authentication or public-deployment claim. Do not run the CLI writer concurrently with a UI processing job.

## Reproduction and dependencies
Use the exact PowerShell and POSIX commands in README.md. `npm ci` uses package-lock.json; the clean Python3.10 environment uses the pinned transitive requirements. Audit/extract preserve originals and regenerate tables; train/evaluate regenerate fixed grouped results and artifacts. `verify` recomputes every original hash. Full-resolution extraction is independent of plot decimation.

Official documentation consulted for compatibility: [Vite requirements and build](https://vite.dev/guide/), [Tailwind Vite integration](https://tailwindcss.com/docs/installation/using-vite), [Express5 requirements](https://expressjs.com/en/guide/migrating-5/), [FastAPI/Uvicorn execution](https://fastapi.tiangolo.com/deployment/manually/), [scikit-learn leakage prevention](https://scikit-learn.org/stable/common_pitfalls) and [grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html). Largest-square SNM follows the physical definition illustrated in [Berkeley EECS-2016-3](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2016/EECS-2016-3.pdf), with the numerical construction and controlled fixtures provided here.

## Professor demonstration (8 minutes)
1. Start `npm run dev`; open127.0.0.1:5173. Overview: explain30 accepted exports versus1.69 million waveform/DC rows, the eight active cases and exploratory status (1 minute).
2. Dataset Explorer: open accepted bit1 mislabeled DATA0 provenance and rejected first-SNM flags. Waveform Viewer: choose an active run, enter23–25 ns, inspect WL/Q/QB crossings and the trace hash (2 minutes).
3. Characterization: show active energy, then hold/read equal-scale butterflies and largest squares. Explain signed two-rail integration and the separate static boundary conditions (2 minutes).
4. Prediction: request write1 at0.95 V/55 C/long; identify Exploratory and the residual envelope. Compare measured active choices at27 C with your own delay limit, then use1 ps to demonstrate no feasible setting. Explain that the demonstration threshold is supplied by the presenter, not a validated design requirement (2 minutes).
5. Evaluation: show constant versus ridge and grouped condition counts, explicitly state zero independent final-test cases. Reports: download evaluation.json and a target table; optionally run retraining to show real stages (1 minute, excluding optional job runtime).

## Remaining scientific work and unsupported claims
The supported local software and measured analysis are implemented. ADDITIONAL_SIMULATIONS_REQUIRED.md specifies a separate, unexecuted nominal-condition campaign and reserved final conditions. Supply original ADE states/netlists/logs for independent provenance and convergence verification. No Cadence installation/run, new simulations, post-layout data, process yield, failure classifier, minimum retention voltage or calibrated prediction uncertainty is claimed. Browser visual smoke testing depends on available automation; actual check outcomes are maintained in progress.md.
