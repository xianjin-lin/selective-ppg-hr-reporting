# Release provenance and verification

## Included numerical implementation

`analysis_core.py` is the pure numerical portion of the study's
`fv_analysis_lib.py`, the frozen additional-VitalDB analysis library. Only the
module-level description was adapted for public release. Function bodies,
historical operating-fraction constants and original bootstrap default seed
were preserved. No private path module is imported.

`run_analysis.py` is a new local-input adapter for exploring those routines.
It is explicitly not the historical full execution entry point. The synthetic
case, input guards and open-annotation downloader were prepared for this
release. They neither add experimental findings nor replace frozen results.

## Aggregate result snapshots

`results/published/vitaldb_primary_contrasts.csv` is the frozen
additional-cohort primary comparison output (`fresh_contrasts.csv`).
`mimic_global_intervals.csv` is the frozen global MIMIC interval output
(`mimic_intervals.csv`). These contain aggregate contrasts, not patient records.
The release preparation verifies their bytes against the local frozen sources.

## Figures

The repository includes rendered PNGs of selected study figures only:

- `study_design.png`: MIMIC partition and window-count figure;
- `external_evaluation.png`: additional VitalDB retention/allocation figure;
- `allocation_tradeoff.png`: allocation-trade-off figure, with editorial
  inset/leader placement improvements and unchanged plotted data coordinates.
- `label_coverage_heatmap.png`: window coverage by chart label on MIMIC TEST
  (manuscript Fig. 5), rasterized from the manuscript PDF without editing;
- `label_failure_heatmap.png`: retained HR failure by chart label on MIMIC TEST
  (manuscript Fig. 6), rasterized from the manuscript PDF without editing.

`logo.svg` is a decorative README icon, not a study figure or data.

No waveform example, plotting source, vector editing script or figure-generation
code is included. The rendering assets are explanatory manuscript material,
not numerical inputs to the demo.

## Verification boundary

The public checks cover rounding/ties, missing predictions and the strict
5-bpm boundary, paired cluster weights, contrast arithmetic, family exclusions,
synthetic workflow directions, alignment guards and aggregate-table integrity.
CI runs on synthetic data and never downloads protected records.

Local release preparation additionally checks numerical-function identity,
parity with the historical pure analysis library on synthetic arrays, exact
aggregate-source copies, selected-file content, and absence of plotting code,
data caches, private paths and credential patterns. Pattern scans cannot
provide an absolute guarantee against every possible secret; release content
is deliberately small and explicitly allowlisted for manual inspection.

Successful demo/tests establish software behavior within this released scope.
They do not certify the full unpublished modeling pipeline or regenerate the
paper's clinical results. The demo dependency pin is for the released software
example, not a claim that it is the original GPU-training environment.
