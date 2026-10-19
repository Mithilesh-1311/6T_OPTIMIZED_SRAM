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
