# Selective PPG-based heart-rate reporting

**Separating within-rhythm accuracy from reliable-output yield**

[![Analysis checks](https://github.com/xianjin-lin/selective-ppg-hr-reporting/actions/workflows/checks.yml/badge.svg)](https://github.com/xianjin-lin/selective-ppg-hr-reporting/actions/workflows/checks.yml)

Xianjin Lin, Liyang Yu, Zhonglou Luo, Rui Tian and Wangcai Ding ·
analysis companion to the manuscript of the same title · [How to cite](#citation)

Selecting accurate heart-rate (HR) estimates within a cardiac rhythm is not the
same as allocating a shared reporting budget across rhythms. **A score can
retain fewer failures within atrial fibrillation (AF) yet retain fewer reliable
AF outputs under global ranking.** The study compares confidence- and
quality-based selection of fixed 10-second PPG HR predictions from five
supervised configurations, using MIMIC-III-Ext-PPG and an additional
rhythm-annotated VitalDB cohort. This repository publishes the selection and
statistical routines, a data-free CPU example, aggregate results and three
manuscript figures.

[Research question](#research-question) ·
[Key evidence](#key-evidence) ·
[Study design](#study-design-and-evidence-status) ·
[Quick start](#quick-start) ·
[Release scope](#what-is-and-is-not-released) ·
[Data access](#data-access-and-permissions) ·
[Citation](#citation)

## Research question

Selective reporting is assessed along three distinct quantities:

| Quantity | Question answered |
|---|---|
| **Retained failure** | How often do the reported estimates fail the error tolerance? |
| **Rhythm-specific coverage** | What fraction of a rhythm's eligible windows is reported? |
| **Reliable-output yield** | How many reported estimates are non-failing, within a rhythm or overall? |

A failure is a missing or non-finite estimate, or an absolute error **above
5 bpm** against the ECG-derived reference; exactly 5 bpm is not a failure.
Reference eligibility is applied separately. Matched-count selection within a
rhythm measures accuracy; global ranking against one budget measures
allocation.

## Key evidence

In the additional VitalDB cohort (352 patients), confidence ranking had lower
retained AF/AFL failure than quality-score ranking at matched within-rhythm
counts in all five configurations (the H2-R interval included zero). Under a
shared global budget, it retained fewer reliable AF/AFL outputs and more
reliable outputs overall, for every configuration at both operating points.
Per-contrast values are in [`results/published/`](results/published/README.md).

The figure poses the follow-up question: can an alternative score recover
reliable AF outputs (rightward) without losing reliable outputs overall
(downward)?

<img src="assets/allocation_tradeoff.png" alt="Four scatter panels showing change in reliable AF outputs (horizontal) against change in overall reliable outputs (vertical) relative to confidence ranking, for MIMIC TEST and the additional VitalDB cohort at 92.73% and 87.93% retention, with grey label-informed AF-offset curves." width="100%">

**Allocation trade-offs relative to confidence ranking at matched global
counts.** Top: MIMIC TEST (chart-defined AF); bottom: additional VitalDB cohort
(AF/AFL); left: 92.73% and right: 87.93% retention. Markers are descriptive
configuration-level three-seed means of exploratory alternative scores, not
patients or confidence intervals. Grey label-informed AF-offset curves (−2 to
+2 development SDs) are diagnostics, not deployable rhythm-blind corrections.
Quality-score results lie off-scale.

## Study design and evidence status

The cohorts carry different evidential weight:

| Evidence | Status |
|---|---|
| MIMIC TEST (Folds 8–9) | Examined during development: developmental evidence, not independent confirmation |
| Additional VitalDB cohort: original confidence-versus-quality comparison | Evaluated under analysis rules frozen before waveform retrieval |
| Alternative scores, two-stage policy and label-informed offsets | Exploratory: evaluated on cohorts that had already been examined |

### MIMIC-III-Ext-PPG partitions

<img src="assets/study_design.png" alt="Horizontal bar charts of MIMIC-III-Ext-PPG patient-disjoint partitions (training pool, development and MIMIC TEST) and of candidate versus reference-eligible 10-second windows." width="100%">

(a) Patient-disjoint
record pools for training, development and MIMIC TEST. (b) Candidate and
reference-eligible 10-second windows for HR training and testing.

### Additional VitalDB comparison

<p align="center">
<img src="assets/external_evaluation.png" alt="Interval plots of confidence-minus-quality differences in the additional VitalDB cohort for five configurations: within-rhythm failure differences for AF/AFL and NSR, and global reliable-output differences for AF/AFL and overall at 92.73% and 87.93% retention." width="595">
</p>

Confidence-minus-quality differences. (a) Retained
failure after within-rhythm selection. (b) Reliable-output differences after
global selection; overall counts include AF/AFL. Points are
configuration-level three-seed means; whiskers are approximate simultaneous
95% subject-cluster bootstrap intervals within each contrast family (352
patients; 20,000 resamples).

## Quick start

The data-free example needs Python 3.11 or newer and NumPy only: no PyTorch,
GPU, model checkpoint or data-access approval.

```bash
git clone https://github.com/xianjin-lin/selective-ppg-hr-reporting.git
cd selective-ppg-hr-reporting
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
```

```bash
python -m pip install -r requirements.txt
python examples/run_demo.py
python -m unittest discover -s tests -v
```

The demo writes two local files to `outputs/demo/`:

| File | Contents |
|---|---|
| `synthetic_predictions.csv` | Generated input: 12 synthetic units, two configurations, three paired seeds, 240 windows per fit |
| `summary.json` | Endpoint contrasts, global reporting levels and bootstrap settings |

At 75% retention, the constructed example shows the direction of the
allocation pattern: more reliable outputs overall but fewer reliable AF outputs
under confidence than under quality ranking. It is a software demonstration,
not patient data or a clinical effect size. Its 2,000-draw bootstrap is a short
run, not the manuscript's inferential specification.

### Analyze local predictions

For your own lawfully held, aligned predictions in the
[documented CSV format](docs/analysis-contract.md#input-format):

```bash
python run_analysis.py --input outputs/demo/synthetic_predictions.csv --fraction 0.75 --bootstrap 2000 --output outputs/check
```

Replace the input path and choose the retention fraction **before examining
comparison outcomes**. AF strata are labeled `AF` or `AF/AFL` and exact sinus
rhythm `SR`; other labels stay in the global pool. Outputs are aggregate, with
no window or patient identifiers. The command evaluates one operating point; it
does not recover the manuscript's SQI-defined within-rhythm counts or complete
analysis families.

### Statistical interpretation

- Predictions stay fixed across reporting rules; ties use stable input order
  and retained counts use `floor(fraction * n + 0.5)`.
- Patients, not windows or seeds, are the bootstrap units; seed statistics are
  averaged within each resample under common subject weights.
- Retained sets are selected once and then reweighted, without rerunning top-k
  selection. Intervals are conditional on the observed sets and do not describe
  a policy reselected in a newly composed cohort.
- Raw-count and budget-standardized analyses have different resampling targets.
  An interval spanning zero does not establish equivalence.

The [analysis contract](docs/analysis-contract.md) gives the full definitions.

## What is and is not released

| Included | Not included |
|---|---|
| Matched-count top-k selection with deterministic tie handling | Model training and inference implementations |
| Failure definition and subject-level contrast arithmetic | Model checkpoints, logits or prediction caches |
| Fixed-set paired cluster bootstrap and family intervals | Raw or processed patient-level waveforms |
| A local CSV analysis entry point and synthetic example | Restricted MIMIC files, identifiers or access credentials |
| Two aggregate result tables and three rendered manuscript figures | Figure-generation and plotting scripts |
| An official open-data download and schema-check example | The complete private research workspace or its history |

The companion verifies the released computations; it does not train the five
estimators or regenerate the manuscript's figures, tables or clinical results.
Approved dataset access does not supply the withheld models or predictions, and
no future release of withheld components is promised. See
[provenance](docs/provenance.md) for the origin of each released file.

<details>
<summary><strong>Repository map</strong></summary>

```text
analysis_core.py                       Released pure numerical routines
run_analysis.py                        Local CSV analysis entry point
examples/run_demo.py                   Reproducible synthetic case
examples/download_open_annotations.py  Official open-data access example
tests/test_analysis.py                 CPU-only regression checks
results/published/                     Aggregate manuscript result snapshots
assets/                                Rendered figures only, no plotting sources
docs/                                  Data access, interpretation and provenance
```

</details>

## Data access and permissions

This repository redistributes no original dataset. Each dataset is governed by
its provider's terms for the exact version obtained; repository code
permissions do not extend to third-party data.

| Resource | Official record | Access | Role in the study |
|---|---|---|---|
| MIMIC-III-Ext-PPG 1.1.0 | [PhysioNet](https://physionet.org/content/mimic-iii-ext-ppg/1.1.0/) · [DOI](https://doi.org/10.13026/r6k1-xt76) | **Credentialed: required training and signed DUA** | Fitting, development and MIMIC evaluation |
| VitalDB 1.0.0 | [PhysioNet](https://physionet.org/content/vitaldb/1.0.0/) · [DOI](https://doi.org/10.13026/czw8-9p62) | Open access under that version's CC BY 4.0 license | Waveforms for the additional cohort |
| VitalDB Arrhythmia 1.0.0 | [PhysioNet](https://physionet.org/content/vitaldb-arrhythmia/1.0.0/) · [DOI](https://doi.org/10.13026/axd6-wm13) | Open access under CC BY 4.0 | Expert beat and rhythm annotations for the additional cohort |

**MIMIC access is personal.** Use your own PhysioNet account, complete the
current credentialing and required training, and sign the Data Use Agreement.
Keep records, identifiers, tokens and derived patient-level caches out of Git,
issues and pull requests. This project neither automates approval nor asks for
a password or token.

**VitalDB routes differ.** The VitalDB website and API can display different
terms from the versioned PhysioNet records; a license on one route does not
govern another.

**Open-data example.** This command fetches the provider's example annotation
file (case 337), its license and checksum list from VitalDB Arrhythmia 1.0.0 on
PhysioNet, verifies SHA-256 values and the schema, and writes a row-count
report under `data/`. It needs no key, downloads no MIMIC data and runs no HR
model.

```bash
python examples/download_open_annotations.py
```

[Data-access details](docs/data-access.md) cover versions, local handling and
provider citations.

## Citation

**Manuscript:** *Selective PPG-based heart-rate reporting: Separating
within-rhythm accuracy from reliable-output yield.* No journal acceptance or
publication DOI is claimed.

**Software:** cite this companion using [CITATION.cff](CITATION.cff) (GitHub's
*Cite this repository* button), and cite the
[original dataset providers](docs/data-access.md#provider-citations) when
using their data.

## Rights and responsible use

No LICENSE file is included, so no open-source license is granted for the
published material. [RIGHTS.md](RIGHTS.md) explains how code, figures,
aggregate results and third-party data are separated; sharing this selected
code does not license unreleased components or grant dataset access. This is a
research companion, not a medical device, diagnostic tool or validated
real-time monitoring system.

GitHub issues are welcome for reproducible, non-sensitive software problems.
Never attach patient records, credentials, model caches or identifiable
screenshots.
