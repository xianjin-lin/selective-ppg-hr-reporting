"""Deterministic synthetic demonstration. No real records or model checkpoints."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_analysis import FIELDS, analyze, load_predictions


def write_synthetic(path):
    rows = []
    for cfg in ('demo-A','demo-B'):
        for seed in range(3):
            for unit in range(12):
                for window in range(20):
                    af = window < 6
                    failed = (window+unit+seed) % (4 if af else 13) == 0
                    reference = 80.0+unit+(window%3)
                    error = 8.0 if failed else 1.0+(seed/10)
                    confidence = (0.35 if af else 0.85) - (0.25 if failed else 0.0)
                    confidence += ((unit+window+seed)%7)*0.001
                    quality = 0.5+((window*7+unit*3+seed)%19)*0.02
                    if cfg == 'demo-B': quality += ((window+unit)%3)*0.001
                    rows.append(dict(config=cfg,seed=seed,unit_id=f'synthetic-unit-{unit:02d}',
                                     window_id=f'synthetic-window-{unit:02d}-{window:02d}',
                                     rhythm='AF' if af else 'SR',reference_hr=reference,
                                     predicted_hr=reference+error,confidence=confidence,quality_score=quality))
    path.parent.mkdir(parents=True,exist_ok=True)
    with open(path,'w',newline='',encoding='utf-8') as stream:
        writer = csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('outputs/demo'))
    parser.add_argument('--bootstrap',type=int,default=2000)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    data = args.output/'synthetic_predictions.csv'
    write_synthetic(data)
    result = analyze(load_predictions(data),fraction=0.75,bootstrap=args.bootstrap)
    result['synthetic'] = True
    for contrast in result['contrasts']:
        assert contrast['endpoint'] != 'E3' or contrast['estimate'] > 0
        assert contrast['endpoint'] != 'E2b' or contrast['estimate'] < 0
    # Non-estimable/degenerate intervals become null in the saved demonstration.
    import math
    def safe(value):
        if isinstance(value,dict): return {k:safe(v) for k,v in value.items()}
        if isinstance(value,list): return [safe(v) for v in value]
        if isinstance(value,float) and not math.isfinite(value): return None
        return value
    (args.output/'summary.json').write_text(json.dumps(safe(result),indent=2,allow_nan=False),encoding='utf-8')
    print('SYNTHETIC DEMO: 12 units, 2 configurations, 3 paired seeds, 240 windows per fit.')
    print('At 75% global retention, C has more reliable outputs overall but fewer reliable AF outputs than Q.')
    print('This is a constructed software example, not a reported clinical result.')
    print(f'Outputs: {args.output}')


if __name__ == '__main__':
    main()
