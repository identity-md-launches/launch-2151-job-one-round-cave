"""Integration checks for reviewed-merge selection equivalence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import merge_equivalence as m


def text(data):
    return json.dumps(data, indent=2, sort_keys=True) + '\n'


def catalog():
    return {'packages': {'a': {'1': {}, '2': {}}}, 'roots': {'a': '*'}}


class MergeEquivalenceTests(unittest.TestCase):
    def test_historical_changed_witnesses_recheck(self):
        result = m.demo()
        self.assertEqual(result['status'], 'changed')
        merged = m.first.parse(result['review']['merged'])
        folder = m.first.HERE / 'examples'
        for name, row in result['comparisons'].items():
            original = m.first.parse((folder / f'plan-{name}.json').read_text())
            before, roots_before = m.equivalence.normalize(original)
            after, roots_after = m.equivalence.normalize(merged)
            witness = row['counterexample']['selected']
            self.assertEqual(m.equivalence.checker.assignment(before, roots_before, witness), witness)
            self.assertNotEqual(m.equivalence.checker.assignment(after, roots_after, witness), witness)
            self.assertEqual(row['after_sha256'], m.equivalence.digest(after, roots_after))
        self.assertEqual(m.first.core.resolver.solve(merged)['status'], 'resolved')

    def test_preserved_including_empty_solution_sets(self):
        for data in (catalog(), {'packages': {'a': {'1': {}}}, 'roots': {'a': '>2'}}):
            s = text(data)
            result = m.check(s, s, s)
            self.assertEqual(result['status'], 'preserved')
            self.assertTrue(all(r['status'] == 'equivalent' for r in result['comparisons'].values()))

    def test_added_solution_direction_and_symmetry(self):
        base = catalog(); base['roots']['a'] = '==1'
        branch = catalog()
        args = (text(base), text(branch), text(base))
        result = m.check(*args)
        self.assertEqual(result['status'], 'changed')
        witness = result['comparisons']['base']['counterexample']
        self.assertFalse(witness['accepted_before'])
        self.assertTrue(witness['accepted_after'])
        swapped = m.check(args[0], args[2], args[1])
        self.assertEqual(result['comparisons']['ours'], swapped['comparisons']['theirs'])
        self.assertEqual(result['comparisons']['base'], swapped['comparisons']['base'])

    def test_budgets_and_incomplete_does_not_claim_preserved(self):
        s = text(catalog())
        result = m.check(s, s, s, 1)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertEqual(m.check(s, s, s, 2)['status'], 'preserved')
        self.assertEqual(m.demo(1)['status'], 'inconclusive')
        for value in (True, 0, 1000001, '2'):
            with self.assertRaises(ValueError):
                m.check(s, s, s, value)

    def test_conflicts_skip_enumeration(self):
        base = text(catalog())
        ours = text(dict(catalog(), roots={'a': '==1'}))
        theirs = text(dict(catalog(), roots={'a': '==2'}))
        with patch.object(m.equivalence, 'equivalent', side_effect=AssertionError('must skip')):
            result = m.check(base, ours, theirs)
        self.assertEqual(result['status'], 'text_conflict')
        self.assertEqual(result['comparisons'], {})

    def test_invalid_and_duplicate_json(self):
        for bad in ('{"packages":{},"roots":{"a":"*"},"roots":{"b":"*"}}',
                    '{"roots":{"a":"^1"},"packages":{"a":{"1":{}}}}', '[]'):
            with self.assertRaises((ValueError, TypeError)):
                m.check(bad, bad, bad)

    def test_partial_status_keeps_known_difference(self):
        real = m.equivalence.equivalent
        counter = 0
        def limited(*args):
            nonlocal counter
            counter += 1
            return real(*args[:2], 1 if counter == 2 else args[2])
        with patch.object(m.equivalence, 'equivalent', side_effect=limited):
            result = m.demo()
        self.assertEqual(result['status'], 'inconclusive')
        self.assertEqual(result['comparisons']['base']['status'], 'different')
        self.assertEqual(result['comparisons']['ours']['status'], 'inconclusive')

    def test_cli_immutable_and_portable(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            folder = Path(tmp)
            portable = folder / 'portable'
            shutil.copytree(m.first.HERE, portable, ignore=shutil.ignore_patterns('__pycache__'))
            files = [p for p in portable.rglob('*') if p.is_file()]
            before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
            script = portable / 'merge_equivalence.py'
            def run(*args):
                return subprocess.run([sys.executable, '-B', str(script), *args], capture_output=True, text=True)
            self.assertEqual(run('demo').returncode, 0)
            paths = [portable / 'examples' / f'plan-{n}.json' for n in ('base', 'ours', 'theirs')]
            changed = run('check', *map(str, paths))
            self.assertEqual(changed.returncode, 1)
            self.assertEqual(json.loads(changed.stdout)['status'], 'changed')
            self.assertEqual(run('check', *map(str, paths), '--max-assignments', '1').returncode, 3)
            good = str(paths[0]); self.assertEqual(run('check', good, good, good).returncode, 0)
            self.assertEqual(run('check', good, good, good, '--max-assignments', '0').returncode, 2)
            self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})


if __name__ == '__main__':
    unittest.main()
