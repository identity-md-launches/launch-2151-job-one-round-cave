import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).absolute().parent
SPEC = importlib.util.spec_from_file_location('search_batch', HERE / 'batch.py')
batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch)
ROOT = HERE.parents[2]
DOCS = ROOT / 'line-3/tools/evidence-search/examples/docs'


class BatchTests(unittest.TestCase):
    def plan(self):
        return {'format': batch.PLAN_FORMAT, 'queries': [
            {'id': 'zto', 'query': 'ZTO token decimals', 'limit': 2, 'require_all': True},
            {'id': 'pool', 'query': 'ZTO pool tick spacing', 'limit': 2, 'require_all': True},
            {'id': 'none', 'query': 'glacial orchid', 'limit': 2, 'require_all': True}]}

    def test_real_corpus_and_coverage(self):
        result = batch.run(DOCS, self.plan())
        self.assertEqual(result['queries'][0]['result']['hits'][0]['citation'], 'zto.md:1-9')
        self.assertEqual(result['queries'][0]['limit'], 2)
        self.assertEqual(result['queries'][1]['result']['hits'][0]['citation'], 'pool.md:1-10')
        self.assertEqual(result['queries'][2]['result']['hits'], [])
        self.assertEqual(result['coverage']['no_hit_query_ids'], ['none'])
        self.assertTrue(all(hit['source_verified'] for row in result['queries']
                            for hit in row['result']['hits']))
        self.assertEqual(result['corpus_sha256'], batch.run(DOCS, self.plan())['corpus_sha256'])

    def test_invalid_plan_types_and_duplicates(self):
        for mutation in ({'limit': True}, {'require_all': 1}, {'query': '!!!'}, {'id': '../x'}):
            plan = self.plan()
            plan['queries'][0].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(batch.engine.SearchError):
                batch.validate_plan(plan)
        plan = self.plan()
        plan['queries'][1]['id'] = 'zto'
        with self.assertRaises(batch.engine.SearchError):
            batch.validate_plan(plan)

    def test_changed_corpus_prevents_report(self):
        original = batch.freshness.audit
        def stale(index, root):
            report = original(index, root)
            report['fresh'] = False
            return report
        with patch.object(batch.freshness, 'audit', side_effect=stale):
            with self.assertRaisesRegex(batch.engine.SearchError, 'corpus changed'):
                batch.run(DOCS, self.plan())

    def test_demo_cli(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'batch.py'), 'demo'],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['coverage']['no_hit_query_ids'], ['absent'])

    def test_plan_file_cli_and_duplicate_key_rejection(self):
        scratch = ROOT / 'test/scratch/search-batch'
        scratch.mkdir(parents=True, exist_ok=True)
        plan_file = scratch / 'plan.json'
        plan_file.write_text(json.dumps(self.plan()), encoding='utf-8')
        command = [sys.executable, '-B', str(HERE / 'batch.py'), 'run',
                   str(DOCS.relative_to(ROOT)), str(plan_file.relative_to(ROOT))]
        good = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)['coverage']['uncited_documents'], ['imd.md'])
        plan_file.write_text('{"format":"evidence-query-batch/v1","format":"evidence-query-batch/v1","queries":[]}',
                             encoding='utf-8')
        bad = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(bad.stdout, '')
        self.assertIn('duplicate JSON key', bad.stderr)


if __name__ == '__main__':
    unittest.main()
