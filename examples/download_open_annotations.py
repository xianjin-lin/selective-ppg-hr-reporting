"""Download and check one open VitalDB Arrhythmia annotation case from PhysioNet.

The files remain local. This is a data-access example, not an HR-model evaluation.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

BASE = 'https://physionet.org/files/vitaldb-arrhythmia/1.0.0/'
CASE = 'Annotation_Files/Annotation_file_337.csv'
LIMIT = 2*1024*1024


def fetch(name):
    request = Request(BASE+name,headers={'User-Agent':'selective-ppg-hr-reporting/0.1'})
    with urlopen(request,timeout=60) as response:
        final = urlsplit(response.geturl())
        if final.scheme != 'https' or final.hostname not in {'physionet.org','physionet-open.s3.amazonaws.com'}:
            raise ValueError('Unexpected download host; refusing to continue.')
        content = response.read(LIMIT+1)
    if len(content)>LIMIT:
        raise ValueError('Example download exceeded its 2 MiB per-file limit.')
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/vitaldb-arrhythmia-example'))
    args = parser.parse_args()
    checksums = fetch('SHA256SUMS.txt')
    expected = {}
    for line in checksums.decode().splitlines():
        digest,name = line.split(maxsplit=1)
        expected[name.lstrip('*').removeprefix('./')] = digest
    names = [CASE,'LICENSE.txt']
    downloaded = {}
    for name in names:
        content = fetch(name)
        if hashlib.sha256(content).hexdigest() != expected.get(name):
            raise ValueError('Upstream SHA-256 validation failed: '+name)
        downloaded[name] = content
    reader = csv.DictReader(io.StringIO(downloaded[CASE].decode('utf-8-sig')))
    required = {'time_second','beat_type','rhythm_label','bad_signal_quality'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('Official annotation schema has changed; inspect the provider record.')
    rows = list(reader)
    if not rows:
        raise ValueError('The annotation example is empty.')
    counts = dict(sorted(Counter(row['rhythm_label'] for row in rows).items()))
    args.output.mkdir(parents=True,exist_ok=True)
    for name,content in downloaded.items():
        # Fixed, provider-verified names only; no archive extraction or caller-supplied URLs.
        (args.output/Path(name).name).write_bytes(content)
    (args.output/'SHA256SUMS.txt').write_bytes(checksums)
    report = dict(dataset='VitalDB Arrhythmia Database',version='1.0.0',
                  doi='10.13026/axd6-wm13',license='CC BY 4.0',
                  source=BASE+CASE,annotation_rows=len(rows),rhythm_row_counts=counts,
                  warning='Annotation-row counts are not rhythm durations, HR errors, or study results.',
                  files={Path(name).name:hashlib.sha256(content).hexdigest() for name,content in downloaded.items()})
    (args.output/'download_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'Official open-data example checked: {len(rows)} annotation rows; SHA-256 PASS.')
    print(f'Local files only: {args.output}')
    print('No HR model was run. Keep downloaded data out of Git commits.')


if __name__ == '__main__':
    main()
