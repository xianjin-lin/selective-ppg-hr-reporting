"""Data-free regression checks for the public analysis companion."""
import csv
from pathlib import Path
import tempfile
import unittest

import numpy as np
import analysis_core as A
from examples.run_demo import write_synthetic
from run_analysis import analyze, load_predictions


class AnalysisTests(unittest.TestCase):
    def test_rounding_and_ties(self):
        self.assertEqual(A.k_of(.5,3),2)
        self.assertEqual(A.k_of(.25,2),1)
        score = np.array([.5,.9,.9,.1,.95])
        mask = np.array([True,True,True,True,False])
        self.assertEqual(A.retained(score,mask,.25).tolist(),[False,True,False,False,False])

    def test_failure_boundary_and_missing(self):
        self.assertEqual(A.failure([np.nan,75,75.0001,np.inf],[70]*4).tolist(),[True,False,True,True])

    def test_cluster_weights_are_paired_and_deterministic(self):
        first = A.weights(7,50)
        self.assertTrue(np.array_equal(first,A.weights(7,50)))
        self.assertTrue(np.all(first.sum(1)==7))

    def test_contrast_arithmetic(self):
        values = [(np.array([1.,0.]),np.array([2.,2.]),np.array([2.,1.]),np.array([2.,2.]))]*3
        c = A.Contrast(0,'E1','demo','AF','ratio',values)
        self.assertAlmostEqual(A.evaluate([c],np.ones((1,2)))[0,0],-50.)

    def test_family_exclusions(self):
        draws = np.random.default_rng(0).normal(size=(4000,5))
        draws[:,3] = 1.
        draws[:100,4] = np.nan
        family = A.family(np.array([0.,0.,np.nan,1.,0.]),draws,list(range(5)))
        self.assertEqual(family['members_used'],[0,1])
        self.assertEqual(set(family['exclusions']),{2,3,4})
        self.assertTrue(2. < family['c'] < 2.5)

    def test_synthetic_workflow_and_alignment_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'demo.csv'
            write_synthetic(path)
            rows = load_predictions(path)
            result = analyze(rows,.75,bootstrap=300)
            self.assertEqual(result['units'],12)
            self.assertEqual(len(result['contrasts']),10)
            for row in result['contrasts']:
                if row['endpoint']=='E2b': self.assertLess(row['estimate'],0)
                if row['endpoint']=='E3': self.assertGreater(row['estimate'],0)
            with self.assertRaises(ValueError): analyze(rows,1.01,bootstrap=300)
            # Reverse one fit: the score-tie order must not silently change across fits.
            with open(path,newline='',encoding='utf-8') as stream:
                reader = csv.DictReader(stream)
                fields,raw = reader.fieldnames,list(reader)
            raw[:240] = reversed(raw[:240])
            with open(path,'w',newline='',encoding='utf-8') as stream:
                writer = csv.DictWriter(stream,fieldnames=fields)
                writer.writeheader(); writer.writerows(raw)
            with self.assertRaisesRegex(ValueError,'aligned'): load_predictions(path)

    def test_published_aggregate_tables(self):
        root = Path(__file__).resolve().parents[1]/'results/published'
        with open(root/'vitaldb_primary_contrasts.csv',newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows),40)
        self.assertEqual(len({r['id'] for r in rows}),40)
        self.assertNotIn('subjectid',rows[0])
        for row in rows:
            if row['sim_lo'] and row['sim_hi']:
                self.assertLessEqual(float(row['sim_lo']),float(row['sim_hi']))


if __name__ == '__main__':
    unittest.main()
