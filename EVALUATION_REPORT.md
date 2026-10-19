# SAMS evaluation report

Primary: MAE in target units. Also RMSE, pooled OOF R² and fraction within ±10% (absolute floors: delay 0.1 ps, energy 0.1 fJ, power 0.001 uW, SNM 1 mV). Frozen before training. 90% target = at least 90% within tolerance on independent final cases; none exist.

Fixed ridge alpha=0.1 deployed for exploratory use; all candidates reported, no winner chosen on validation results. No final test set or broad generalization claim.

Dataset `56fd2a89b9e4`; model `314a27cadc8c`; seed 42; Python 3.10.9; scikit-learn 1.3.2.

| Target | Cases / groups | Model | MAE | RMSE | R² | Within tolerance |
|---|---|---|---:|---:|---:|---:|
| write0_ps | 8 / 4 | constant | 3.30066 | 3.50761 | -0.7778 | 25.0% |
| write0_ps | 8 / 4 | linear | 0.413284 | 0.413284 | 0.9753 | 100.0% |
| write0_ps | 8 / 4 | ridge | 0.404396 | 0.419904 | 0.9745 | 100.0% |
| write0_ps | 8 / 4 | local_neighbor | 2.4755 | 2.63679 | -0.0046 | 25.0% |
| write0_ps | 8 / 4 | gaussian_process | 3.10839 | 3.30431 | -0.5777 | 25.0% |
| write0_ps | 8 / 4 | random_forest | 2.64755 | 2.86379 | -0.1851 | 50.0% |
| write1_ps | 8 / 4 | constant | 5.23594 | 5.75499 | -0.7778 | 25.0% |
| write1_ps | 8 / 4 | linear | 0.784958 | 0.784959 | 0.9669 | 100.0% |
| write1_ps | 8 / 4 | ridge | 0.768078 | 0.790149 | 0.9665 | 100.0% |
| write1_ps | 8 / 4 | local_neighbor | 3.92695 | 4.32961 | -0.0062 | 50.0% |
| write1_ps | 8 / 4 | gaussian_process | 4.93092 | 5.42201 | -0.5780 | 50.0% |
| write1_ps | 8 / 4 | random_forest | 4.1497 | 4.73205 | -0.2020 | 50.0% |
| active_energy_fj | 8 / 4 | constant | 29.984 | 30.7103 | -0.7768 | 0.0% |
| active_energy_fj | 8 / 4 | linear | 2.55526 | 2.58768 | 0.9874 | 100.0% |
| active_energy_fj | 8 / 4 | ridge | 2.50031 | 2.71974 | 0.9861 | 100.0% |
| active_energy_fj | 8 / 4 | local_neighbor | 22.488 | 23.0529 | -0.0012 | 25.0% |
| active_energy_fj | 8 / 4 | gaussian_process | 28.2373 | 28.9234 | -0.5760 | 0.0% |
| active_energy_fj | 8 / 4 | random_forest | 23.7875 | 24.6519 | -0.1449 | 25.0% |
| quiet_power_uw | 8 / 4 | constant | 0.146637 | 0.146806 | -0.7778 | 0.0% |
| quiet_power_uw | 8 / 4 | linear | 0.00591837 | 0.00591837 | 0.9971 | 100.0% |
| quiet_power_uw | 8 / 4 | ridge | 0.00579109 | 0.00748059 | 0.9954 | 100.0% |
| quiet_power_uw | 8 / 4 | local_neighbor | 0.109978 | 0.110134 | -0.0005 | 0.0% |
| quiet_power_uw | 8 / 4 | gaussian_process | 0.138095 | 0.138259 | -0.5768 | 0.0% |
| quiet_power_uw | 8 / 4 | random_forest | 0.118358 | 0.118587 | -0.1600 | 0.0% |
| hold_snm_mv | 6 / 6 | constant | 13.5976 | 15.9543 | -0.4400 | 100.0% |
| hold_snm_mv | 6 / 6 | linear | 1.09029 | 1.33397 | 0.9899 | 100.0% |
| hold_snm_mv | 6 / 6 | ridge | 1.19506 | 1.38802 | 0.9891 | 100.0% |
| hold_snm_mv | 6 / 6 | local_neighbor | 6.88609 | 8.10021 | 0.6288 | 100.0% |
| hold_snm_mv | 6 / 6 | gaussian_process | 9.47039 | 11.2938 | 0.2784 | 100.0% |
| hold_snm_mv | 6 / 6 | random_forest | 12.3962 | 14.3394 | -0.1632 | 100.0% |
| read_snm_mv | 4 / 4 | constant | 1.99634 | 2.15708 | -0.7778 | 100.0% |
| read_snm_mv | 4 / 4 | linear | 0.248498 | 0.248498 | 0.9764 | 100.0% |
| read_snm_mv | 4 / 4 | ridge | 0.238144 | 0.273609 | 0.9714 | 100.0% |
| read_snm_mv | 4 / 4 | local_neighbor | 1.49726 | 1.62139 | -0.0044 | 100.0% |
| read_snm_mv | 4 / 4 | gaussian_process | 1.88005 | 2.03203 | -0.5776 | 100.0% |
| read_snm_mv | 4 / 4 | random_forest | 2.01338 | 2.15399 | -0.7727 | 100.0% |

≥90% meaningful independent predictive performance is NOT established. All numbers above are exploratory grouped cross-validation. Final independent test cases: 0. Individual errors and exact split membership are downloadable in evaluation.json. Waveform samples, synthetic fixtures, older revisions and related exports are never ML observations.

Local-neighbor is a sparse interpolation baseline; it does not establish a densely validated surface. Some folds require extrapolation because the existing voltage/temperature matrix contains only boundary levels. Full-data fitted models are provided only for exploratory scenario investigation; setting selection uses measured candidates.

## Bounded interpolation baseline

Piecewise-linear interpolation refuses points outside each training fold's convex hull; categorical mode/state are handled separately. Subset MAE is not compared to full-coverage regressors.
- write0_ps: 0/8 validation cases inside the training hull; subset MAE None. Full predictions and refusal reasons are in evaluation.json.
- write1_ps: 0/8 validation cases inside the training hull; subset MAE None. Full predictions and refusal reasons are in evaluation.json.
- active_energy_fj: 0/8 validation cases inside the training hull; subset MAE None. Full predictions and refusal reasons are in evaluation.json.
- quiet_power_uw: 0/8 validation cases inside the training hull; subset MAE None. Full predictions and refusal reasons are in evaluation.json.
- hold_snm_mv: 2/6 validation cases inside the training hull; subset MAE 1.173231272748012. Full predictions and refusal reasons are in evaluation.json.
- read_snm_mv: 0/4 validation cases inside the training hull; subset MAE None. Full predictions and refusal reasons are in evaluation.json.