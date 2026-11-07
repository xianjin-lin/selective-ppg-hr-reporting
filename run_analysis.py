"""CPU analysis of locally held, aligned predictions. No model or plotting code."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import analysis_core as A

FIELDS = ('config','seed','unit_id','window_id','rhythm','reference_hr',
          'predicted_hr','confidence','quality_score')


def load_predictions(path):
    with open(path, newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError('Input must contain: '+', '.join(FIELDS))
        rows = list(reader)
    if not rows:
        raise ValueError('No prediction rows found.')
    keys = [(r['config'],r['seed'],r['window_id']) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate config/seed/window_id rows.')
    for row in rows:
        if any(not row[k].strip() for k in ('config','seed','unit_id','window_id','rhythm')):
            raise ValueError('Identifiers and rhythm labels must be non-empty.')
        for key in ('reference_hr','predicted_hr','confidence','quality_score'):
            row[key] = float(row[key]) if row[key].strip() else float('nan')
        if not np.isfinite(row['reference_hr']) or not 30 <= row['reference_hr'] <= 220:
            raise ValueError('References must be finite and in [30, 220] bpm; filter eligibility first.')
        if not all(np.isfinite(row[k]) for k in ('confidence','quality_score')):
            raise ValueError('Ranking scores must be finite; never silently impute scores.')
    # One shared reference/label/unit per window across every configuration and seed.
    groups = sorted(set((r['config'],r['seed']) for r in rows))
    canonical = None
    for group in groups:
        signature = [(r['window_id'],r['unit_id'],r['rhythm'],r['reference_hr'])
                     for r in rows if (r['config'],r['seed']) == group]
        if canonical is not None and signature != canonical:
            raise ValueError('All configurations/seeds must share aligned windows, units, labels and references.')
        canonical = signature
    seed_sets = [{r['seed'] for r in rows if r['config']==cfg} for cfg in sorted({r['config'] for r in rows})]
    if any(seeds != seed_sets[0] for seeds in seed_sets):
        raise ValueError('Configurations must have the same paired seed labels.')
    return rows


def analyze(rows, fraction=0.9273, bootstrap=20000, random_seed=20261016, af_labels=('AF','AF/AFL')):
    if not 0 < fraction <= 1 or bootstrap < 100:
        raise ValueError('Require 0 < fraction <= 1 and at least 100 bootstrap draws.')
    unit_ids = sorted({r['unit_id'] for r in rows})
    if len(unit_ids) < 2:
        raise ValueError('At least two independent units are required for the bootstrap.')
    units = {value:i for i,value in enumerate(unit_ids)}
    contrasts, levels = [], []
    for cfg in sorted({r['config'] for r in rows}):
        vectors = {ep:[] for ep in ('E1_AF','E1_SR','E2a','E2b','E3')}
        seeds = sorted({r['seed'] for r in rows if r['config']==cfg})
        for seed in seeds:
            # Stable input order defines the deterministic tie break; sorting IDs is not equivalent.
            group = [r for r in rows if r['config']==cfg and r['seed']==seed]
            u = np.array([units[r['unit_id']] for r in group])
            count = lambda mask: np.bincount(u, weights=np.asarray(mask,float), minlength=len(units))
            hr = np.array([r['predicted_hr'] for r in group])
            ref = np.array([r['reference_hr'] for r in group])
            fail = A.failure(hr,ref)
            masks = {'AF':np.array([r['rhythm'] in af_labels for r in group]),
                     'SR':np.array([r['rhythm']=='SR' for r in group])}
            scores = {name:np.array([r[key] for r in group]) for name,key in [('C','confidence'),('Q','quality_score')]}
            global_sets = {name:A.retained(score,np.ones(len(group),bool),fraction) for name,score in scores.items()}
            for rhythm,mask in masks.items():
                selected = {name:A.retained(score,mask,fraction) for name,score in scores.items()}
                vectors['E1_'+rhythm].append((count(selected['C'] & fail),count(selected['C']),
                                             count(selected['Q'] & fail),count(selected['Q'])))
            ra,rb,af = global_sets['C'],global_sets['Q'],masks['AF']
            vectors['E2a'].append((count(ra & af),count(af),count(rb & af),count(af)))
            vectors['E2b'].append((count(ra & af & ~fail),np.ones(len(units)),count(rb & af & ~fail),np.ones(len(units))))
            vectors['E3'].append((count(ra & ~fail),np.ones(len(units)),count(rb & ~fail),np.ones(len(units))))
            for name,selected in global_sets.items():
                n_af = int(af.sum())
                levels.append(dict(config=cfg,seed=seed,policy=name,total_windows=len(group),
                                   retained=int(selected.sum()),
                                   retained_failure_pct=float(100*fail[selected].mean()) if selected.any() else None,
                                   af_coverage_pct=float(100*(selected & af).sum()/n_af) if n_af else None,
                                   reliable_af=int((selected & af & ~fail).sum()),
                                   reliable_overall=int((selected & ~fail).sum())))
        for endpoint,per_seed in vectors.items():
            kind = 'ratio' if endpoint.startswith('E1') else ('cov' if endpoint=='E2a' else 'count')
            contrasts.append(A.Contrast(len(contrasts),endpoint,cfg,'C-Q',kind,per_seed))
    observed = A.evaluate(contrasts,np.ones((1,len(units))))[0]
    draws = A.evaluate(contrasts,A.weights(len(units),bootstrap,seed=random_seed))
    # A single user-selected operating point; these are not the paper's complete comparison families.
    families = {name:A.family(observed,draws,[i for i,c in enumerate(contrasts) if (c.endpoint=='E3')==is_overall])
                for name,is_overall in [('F1',False),('F2',True)]}
    results = []
    for i,c in enumerate(contrasts):
        family_name = 'F2' if c.endpoint=='E3' else 'F1'
        fam = families[family_name]
        interval = fam['results'].get(i,{})
        results.append(dict(config=c.config,endpoint=c.endpoint,contrast='C-Q',family=family_name,
                            estimate=float(observed[i]),**interval,
                            exclusion=fam['exclusions'].get(i,'')))
    return dict(units=len(units),fraction=fraction,bootstrap_draws=bootstrap,
                bootstrap_seed=random_seed,fixed_retained_sets=True,
                note='Illustrative single-operating-point analysis; not a full-paper reproduction.',
                contrasts=results,global_levels=levels)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('outputs/analysis'))
    parser.add_argument('--fraction',type=float,default=0.9273)
    parser.add_argument('--bootstrap',type=int,default=20000)
    parser.add_argument('--random-seed',type=int,default=20261016)
    args = parser.parse_args()
    result = analyze(load_predictions(args.input),args.fraction,args.bootstrap,args.random_seed)
    args.output.mkdir(parents=True,exist_ok=True)
    # CSV/JSON output is aggregate only; identifiers and individual predictions are not exported.
    def safe(value):
        if isinstance(value,dict): return {k:safe(v) for k,v in value.items()}
        if isinstance(value,list): return [safe(v) for v in value]
        if isinstance(value,float) and not np.isfinite(value): return None
        return value
    (args.output/'summary.json').write_text(json.dumps(safe(result),indent=2,allow_nan=False),encoding='utf-8')
    with open(args.output/'contrasts.csv','w',newline='',encoding='utf-8') as stream:
        fields = sorted(set().union(*(r.keys() for r in result['contrasts'])))
        writer = csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader(); writer.writerows(result['contrasts'])
    print(f'Analyzed {result["units"]} units. Aggregate outputs: {args.output}')
    print('Positive C-Q means more of the named endpoint, not necessarily better performance.')


if __name__ == '__main__':
    main()
