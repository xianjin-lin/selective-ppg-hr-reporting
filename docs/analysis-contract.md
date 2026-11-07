# Analysis contract

## Scope

The release exposes selected numerical analysis functions from the frozen
additional-VitalDB comparison, together with a new, explicitly illustrative
CSV adapter and data-free tests. It does not expose fitting, inference,
waveform preprocessing, model weights, case-selection IDs or plotting code.

`analysis_core.py` retains the numerical function bodies of the original
additional-cohort analysis library. `run_analysis.py` and the synthetic example
are public-facing adapters, not historical execution scripts. Their demo
operating point and example families are not the full manuscript specification.

## Input format

One CSV row represents one fixed prediction for one configuration, seed and
window. Required columns:

| Field | Meaning |
|---|---|
| `config` | Configuration label; do not treat this as a patient identifier |
| `seed` | Paired repetition label; the same labels must occur in each configuration |
| `unit_id` | Local patient/subject cluster ID, never a window index |
| `window_id` | Stable local window ID shared across fits |
| `rhythm` | `AF`, `AF/AFL`, `SR`, or another explicitly supplied label |
| `reference_hr` | Finite ECG-derived reference, 30--220 bpm inclusive |
| `predicted_hr` | Fixed predicted HR in bpm; blank/NaN/Inf counts as failure |
| `confidence` | Finite ranking score, higher means retain first |
| `quality_score` | Finite comparator score, higher means retain first |

Every configuration and seed must have the **same ordered eligible windows**,
unit assignments, rhythm labels and references. Duplicate fit/window rows are
rejected. Input order within a fit is the flat-index tie break; changing it
can change retained sets for tied scores. The adapter rejects fit-specific
ordering changes instead of silently changing the tie rule.

Only the reference is eligibility-filtered. Do not remove failed predictions
before computing failure rates. Invalid scores require an explicit upstream
policy, not silent imputation by this script. For real data, identifiers stay
local and must not be submitted to this repository.

## Selection and endpoints

Within-rhythm selection ranks separately within AF (including `AF/AFL` when
supplied as that analysis stratum) and exact SR. Global selection ranks over
the complete input pool, including other rhythms. `k = floor(f*n + 0.5)`.

| Endpoint | Statistic, confidence minus quality | Unit | Direction |
|---|---|---|---|
| E1_AF / E1_SR | Difference in retained failure rates after separate within-rhythm selection | percentage points | Negative = fewer retained failures under C |
| E2a | Difference in AF coverage after global selection | percentage points | Negative = less AF coverage under C |
| E2b | Difference in reliable AF output after global selection | count | Negative = fewer reliable AF outputs under C |
| E3 | Difference in reliable output across all rhythms after global selection | count | Positive = more reliable outputs under C |

Exactly 5 bpm absolute error is non-failing; values above 5 bpm or non-finite
predictions fail. A non-failing output is counted as reliable only if retained.
Rhythm labels are supplied annotations, not model-predicted diagnoses.

The CSV adapter applies one user-chosen fraction to illustrate both designs.
It does **not** infer the paper's rhythm-specific SQI-defined counts from that
fraction. The historical count ratios are visible as `FR` in the released core
for inspection, but are not automatically substituted into the example.

## Bootstrap and family intervals

1. Select top-k sets once on the observed aligned windows.
2. Aggregate the necessary counts into patient-level vectors for each seed.
3. Resample patients with multinomial weights, applying the same weights to
   both reporting policies and all contrasts.
4. Compute each seed's statistic, then average seed statistics in each draw.
5. Form centered, standardized maximum-absolute-deviation simultaneous
   intervals over the estimable family members.

The released `family` routine excludes observed-undefined contrasts, contrasts
with more than 1% undefined bootstrap values, and effectively degenerate
contrasts. Common valid draws are used within a family. Exclusions must be
reported; an absent interval is not a zero effect.

The adapter uses F1 for E1/E2a/E2b and F2 for E3 at its one selected operating
point. The manuscript includes additional configurations/operating-point
members and separate analysis families. Do not label this adapter's interval
as a paper interval unless the entire relevant frozen family is reconstructed.

The paper's original inference used 20,000 bootstrap draws with prespecified
stability/escalation checks. A 2,000-draw demo is a software illustration, not
a substitute for that protocol. The `stability` helper is exposed for inspection;
the adapter does not silently escalate or certify inferential convergence.

### What the bootstrap does not estimate

The bootstrap reweights fixed retained sets. It never re-ranks windows in each
draw. It is conditional on the observed sets, not the variability of a policy
that repeats top-k selection after cohort composition changes. Seeds are
paired repetitions, not additional independent participants.

### Budget-standardized sensitivity

For fixed global retained budget k, the sensitivity target is

```text
k * [(sum_u w_u Y_A,u / sum_u w_u K_A,u)
   - (sum_u w_u Y_B,u / sum_u w_u K_B,u)]
```

K includes **all rhythms' retained windows**, not AF-only retained counts.
Y is the specified reliable-output count. This scales within each resample;
it does not reselect windows or assign a separate budget to each patient.
Raw and standardized observed estimates can coincide while their bootstrap
distributions differ. The example CLI reports raw counts, not this sensitivity.

## Limits of interpretation

The compared HR predictions do not change when reporting rules change.
No causal mechanism, universal unavoidable trade-off, clinical deployment
validation, equivalence or superiority across all uncertainty scores follows
from this release. Follow the manuscript for the distinction between previously
examined cohorts, the original additional-cohort comparison and exploratory
score adjustments.
