# Data access, versions and local handling

## Controlled access: MIMIC-III-Ext-PPG

- Official record: https://physionet.org/content/mimic-iii-ext-ppg/1.1.0/
- Version-specific DOI: https://doi.org/10.13026/r6k1-xt76
- Governing access: PhysioNet credentialing, required training and a signed DUA.

Use your own approved account. Follow the current access instructions at the
record; approval cannot be supplied by a GitHub repository. No credential,
download cookie, account-specific link, patient-ID list, signal excerpt or
prediction cache is provided here. The repository does not mirror the data.

## Open access: VitalDB via PhysioNet

- Waveforms: https://physionet.org/content/vitaldb/1.0.0/
- Waveform record DOI: https://doi.org/10.13026/czw8-9p62
- Expert annotations: https://physionet.org/content/vitaldb-arrhythmia/1.0.0/
- Annotation record DOI: https://doi.org/10.13026/axd6-wm13

Both linked PhysioNet versions list CC BY 4.0. Attribute the providers and
comply with the exact source version's terms. The separate VitalDB website
lists different terms; its terms must not be silently replaced with a
PhysioNet license. The bundled download example uses only the versioned
PhysioNet annotation endpoint.

```bash
python examples/download_open_annotations.py --output data/vitaldb-arrhythmia-example
```

The example downloads case 337's expert annotation, LICENSE.txt and the official
checksum list, checks SHA-256 and required columns, and writes a local
`download_check.json`. These are provider data, **not** redistributed repository
fixtures. The file may contain annotation boundary/quality rows as well as
beat annotations, so the report labels its values as row counts, not durations.
No model predictions, HR error estimates or paper-comparison statistics are
computed from this file alone.

To obtain waveforms, use the waveform provider's versioned record and its
documented download routes. The whole database is large: do not download a
full archive just to try the data-free analysis example.

## Keep local material local

`data/` and `outputs/` are ignored by Git. The release additionally excludes
waveform formats, checkpoint formats, array caches and common credential-file
formats. Ignore rules are a guardrail, not a privacy guarantee: inspect the
actual staged files and history before every push.

Never put patient records, account secrets, signed download links or identifying
screenshots in commits, issue descriptions, CI artifacts or notebook output.
No downloader in this repository requests a password or a key. Do not disable
TLS verification to work around network failures.

## Provider citations

- Moulaeifard M, Charlton PH, Strodthoff N. MIMIC-III-Ext-PPG, version 1.1.0.
  PhysioNet, 2026. https://doi.org/10.13026/r6k1-xt76
- Lee H, Jung C. VitalDB, version 1.0.0. PhysioNet, 2022.
  https://doi.org/10.13026/czw8-9p62
- Lee HC et al. VitalDB, a high-fidelity multi-parameter vital signs database
  in surgical patients. Scientific Data 9, 279 (2022).
  https://doi.org/10.1038/s41597-022-01411-5
- Eun D et al. VitalDB Arrhythmia Database, version 1.0.0. PhysioNet, 2026.
  https://doi.org/10.13026/axd6-wm13

Check each provider record for additional required citations and current
access requirements before use.
