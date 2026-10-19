# SAMS decisions

- 2026-10-19: Preserve all existing files. Write parsed data and reports separately; hash originals before and after implementation.
- 2026-10-19: SAMS is the sole title, without expansion or personal identifiers. Original historical evidence remains untouched and is never served by the application.
- 2026-10-19: Separate target tables; waveform samples are not ML cases. Freeze regression evaluation before model fitting. No artificial final-test claims from tiny datasets.
- 2026-10-19: Use a local three-service stack with disk artifacts and SQLite; avoid cloud, paid services and unnecessary infrastructure.
- 2026-10-19: Final acceptance is30/47 exports, based on recorded revision decisions plus trace checks. Keep14 superseded,1 ambiguous and2 rejected originals. The actual read-SNM exports supersede the older guide's pending status.
- 2026-10-19: Accept RETENTION_DATA0_DC as bit1, never bit0. Validate exported DATA and post-write Q/QB. Use corrected long-mode0.9 V exports and complete active-hold currents only.
- 2026-10-19: Preserve signed ideal-source current accounting and both DC rails. Distinguish20–60 ns active workload energy,25–65 ns quiet power and19–75 ns sequence energy. Exclude unmeasured ideal-control energy explicitly.
- 2026-10-19: Largest-square SNM uses transformed piecewise-linear VTCs with both lobes. Test analytic0.3 V square, invalid VTC rejection and historical rounding. Plot butterflies on equal voltage scales, including square vertices.
- 2026-10-19: Corrected event-window comparison for machine-precision endpoint rounding; it still refuses genuinely incomplete windows. Never extrapolate missing waveform endpoints.
- 2026-10-19: Group active mode pairs by main voltage/temperature and retention state pairs by retention voltage/temperature. The four active-hold references remain separate from quiet-retention training.
- 2026-10-19: Fixed ridge alpha0.1 is deployed only as Exploratory. Report all fixed candidates; do not select a validation-score winner. Bounded interpolation refuses outside-hull folds and reports partial coverage separately. Descriptive residual envelopes are not calibrated confidence intervals.
- 2026-10-19: Use measured candidates for constraint-based setting selection because no independent final-test validation exists. Link requested SNM from separate static experiments with its source/boundary; reject unsupported constraints and invent no electrical acceptance limits.
- 2026-10-19: Pin the verified Python3.10 transitive environment and commit npm's resolved lockfile. Version artifacts with scientific source and target fingerprints; preserve evidence/source snapshots alongside models. Original exports and the private historical guide remain outside version control and are not served by the application.
- 2026-10-19: Browser-control inventory was empty and the in-app browser reported unavailable. Do not claim visual browser tests. Verify the live frontend HTTP proxy, Node/Python inference, measurements and report equality through integration assertions; provide a manual demonstration procedure.
- 2026-10-19: Normalize scientific source line endings and canonicalize target JSON only for model/extractor version fingerprints, so Git/OS text line endings do not create false version changes. Original-export SHA-256 always remains byte-exact.
