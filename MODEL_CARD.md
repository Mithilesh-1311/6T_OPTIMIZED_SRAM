# SAMS model card

## Intended use
Local exploratory prediction of schematic SRAM metrics and investigation of measured settings. The model does not control Cadence. Constraint-based recommendations use measured candidates, not model estimates.

## Provenance
Original Cadence numerical exports; GPDK090 v4.6, nmos1v/pmos1v, planar 90 nm CMOS, generally L=100 nm. Historical netlist/setup record describes final-buffer active experiments and separate core-SNM testbenches. Raw exports independently show numerical signal behavior but do not certify temperature, corner, exact topology, solver success or all source settings. No external dataset, synthetic training evidence, layout or silicon evidence is used.

## Inputs and targets

| Target | Inputs available before prediction | Independent cases | Grouped conditions |
|---|---|---:|---:|
| Write-0 delay (ps) | Main supply, temperature, WL mode | 8 | 4 |
| Write-1 delay (ps) | Main supply, temperature, WL mode | 8 | 4 |
| Active workload DC energy (fJ) | Main supply, temperature, WL mode | 8 | 4 |
| Quiet retention power (uW) | Retention voltage, temperature, stored bit | 8 | 4 |
| Hold core SNM (mV) | Cell supply, temperature | 6 | 6 |
| Read core SNM (mV) | Cell supply, temperature | 4 | 4 |

Active-hold's four reference cases are analyzed separately and are not mixed into the quiet-retention regression. Geometry does not vary and is not an input. IDs, filenames, waveform measurements and target-derived quantities are excluded. Each target has its own table; missing labels are never imputed across experiment kinds.

## Models and validation
Fixed candidates: mean constant; standardized ordinary linear regression; standardized ridge with alpha=0.1; fixed RBF Gaussian process with alpha=1e-6 and no kernel optimization; 100-tree forest, minimum leaf size 2; standardized distance-weighted 2-neighbor regression. Bounded piecewise-linear interpolation is checked separately per mode/state inside training convex hulls and refuses unsupported held-out corners. Fixed seed 42. Preprocessing is fitted within each training fold.

Leave one complete voltage/temperature group out. Paired WL modes or stored bits stay together. No waveform samples, related exports or historical revisions cross train/validation boundaries. Exact split memberships and individual errors are stored in versioned evaluation.json. No hyperparameter tuning or model winner selection on these results. Ridge is the predeclared exploratory deployed model, avoiding a post-hoc claim about the best score. A credible final test set is not available.

Primary metric: MAE in physical units. Also RMSE, pooled out-of-fold R², and fraction within ±10% of measured target. Absolute tolerance floors: 0.1 ps for delays, 0.1 fJ for active energy, 0.001 uW for power, 1 mV for SNM. These are evaluation floors, not electrical acceptance constraints. The performance target is at least 90% within tolerance on an independent final set. **Not established.**

## Actual exploratory results
The predeclared ridge grouped-validation results are summarized in EVALUATION_REPORT.md and its machine-readable artifact. The initial verified full dataset gives approximately:

| Target | MAE | RMSE | R² | Within tolerance |
|---|---:|---:|---:|---:|
| Write-0 delay | 0.4044 ps | 0.4199 ps | 0.9745 | 8/8 |
| Write-1 delay | 0.7681 ps | 0.7901 ps | 0.9665 | 8/8 |
| Active energy | 2.5003 fJ | 2.7197 fJ | 0.9861 | 8/8 |
| Quiet retention power | 0.005791 uW | 0.007481 uW | 0.9954 | 8/8 |
| Hold SNM | 1.1951 mV | 1.3880 mV | 0.9891 | 6/6 |
| Read SNM | 0.2381 mV | 0.2736 mV | 0.9714 | 4/4 |

These small exploratory fractions do not establish final-test performance. The constant baseline already falls within 10% for all SNM cases because the target range is narrow; that tolerance score alone cannot demonstrate useful learned prediction. Many nonlinear candidates perform worse than simple linear models. The recorded baseline comparison is necessary context.

## Uncertainty and training domain
The service returns the maximum absolute grouped out-of-fold residual as a descriptive error envelope. It is not a calibrated probability interval and has no guaranteed coverage. Inputs outside measured feature bounds are refused with Unavailable/extrapolation status. Bounds are rectangular in this particular dataset; being inside them does not prove validated interpolation.

Active main supply: 0.9–1.0 V, temperature 27–85 C, mode 0/1. Retention supply: 0.8–0.9 V with main 1.0 V, temperature 27–85 C, bit 0/1. Hold-SNM supply: 0.8–1.0 V. Read-SNM supply: 0.9–1.0 V. Fixed testbench timing, loading, nominal model section and circuit revision apply. No PVT or mismatch generalization follows.

## Unsupported uses
Safety certification, automatic circuit control, minimum retention-voltage claims, failure classification, process yield, silicon or post-layout prediction, sensed read-output delay, earliest wake access, dense validated surfaces, or total-chip energy estimates. There are no valid failure-class labels for training a failure classifier. Successful finite CSV parsing is not proof of Spectre convergence.

## Artifact compatibility
Python 3.10, pinned requirements, schema version 1, exact scikit-learn version checked before inference. Artifacts are trusted locally generated joblib files; user uploads cannot supply models or code. Each current artifact directory stores evaluation, extracted evidence, target tables and numerical source snapshots. Dataset and model versions are returned by the service. Regenerate instead of loading a model produced by a different library/schema version.

## Verified tolerance reporting (release preparation)

Scores below are recalculated from the frozen out-of-fold predictions, not from selected-case fit. Tolerance is max(10% of absolute measurement, the predeclared absolute floor). Zero labels remain eligible; missing/nonfinite labels invalidate the report rather than becoming zero. No thresholds, authoritative models or historical evaluation artifacts changed.

All scores are **exploratory model-selection validation**, not an untouched independent final test. The source records a predeclared ridge model; because results have been available during development, the release reports them conservatively as model-selection validation. Historical timing of the declaration cannot be independently certified.

| Target | Within tolerance | Passing / cases | Groups | MAE | RMSE | Constant baseline | Final test |
|---|---:|---:|---:|---:|---:|---:|---|
| write0_ps | 100% | 8/8 | 4 | 0.404396319 | 0.419904007 | 25% (2/8) | 0; Not evaluated |
| write1_ps | 100% | 8/8 | 4 | 0.768077578 | 0.790149435 | 25% (2/8) | 0; Not evaluated |
| active_energy_fj | 100% | 8/8 | 4 | 2.5003084 | 2.71973992 | 0% (0/8) | 0; Not evaluated |
| quiet_power_uw | 100% | 8/8 | 4 | 0.00579109428 | 0.00748059087 | 0% (0/8) | 0; Not evaluated |
| hold_snm_mv | 100% | 6/6 | 6 | 1.19505881 | 1.38801817 | 100% (6/6) | 0; Not evaluated |
| read_snm_mv | 100% | 4/4 | 4 | 0.23814414 | 0.273608574 | 100% (4/4) | 0; Not evaluated |

Units follow the target suffix: ps, fJ, uW or mV. Constant baselines already meet the SNM tolerance, so the 100% SNM fractions alone do not demonstrate useful predictive skill. No cross-target average is reported. The >=90% threshold is met on these tiny exploratory OOF sets only; independent-final-test performance remains unestablished.

The reviewer independently refitted ridge plus StandardScaler in memory using every saved fold and reproduced all six stored OOF vectors exactly. Related modes/stored bits remain grouped by operating condition. Source hashes are unique within each target. No authoritative artifact was rewritten.

Selected-case example, derived from the current model and recorded target table: active energy, 1 V, 27 C, long wordline (SEL1), `sel1updated.vcsv.txt`, case `14e634dff1ca06fd`: measured 202.83385857169995 fJ, predicted 203.11361956733774 fJ, selected-case relative error 0.13792618136231624%. This case **was included in full-data training**. It is neither an OOF prediction nor independent final validation. Zero measurements have no defined relative percentage; show absolute error instead.

Runtime API `/performance` and download `/reports/performance.json` use `services/ml/performance.py`; `reports/performance.json` is the checked release snapshot. The API verifies frozen artifact equality, group-disjoint splits, source uniqueness and score consistency. Dashboard and all-target cards consume this report. The original `/evaluation` and its download remain unchanged. Observed OOF residual envelopes are not calibrated confidence intervals.
