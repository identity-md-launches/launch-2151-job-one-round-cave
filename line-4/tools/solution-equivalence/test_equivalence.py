import copy
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location('equivalence', Path(__file__).with_name('equivalence.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def catalog(versions=None, roots=None):
    return {'roots': roots or {'a': '*'}, 'packages': versions or {'a': {'1': {}, '2': {}}}}


def raw_solutions(data):
    # Independent raw-edge oracle for generated exact-constraint catalogs.
    packages, roots = data['packages'], data['roots']
    names = sorted(packages)
    solutions = set()
    for values in itertools.product(*[[None] + list(packages[p]) for p in names]):
        chosen = {p: v for p, v in zip(names, values) if v is not None}
        todo, reached, valid = list(roots.items()), set(), True
        while todo:
            p, constraint = todo.pop()
            if p not in chosen or (constraint != '*' and constraint != '==' + chosen[p]):
                valid = False
                break
            if p not in reached:
                reached.add(p)
                todo.extend(packages[p][chosen[p]].items())
        if valid and set(chosen) == reached:
            solutions.add(tuple(sorted((p, v + '.0.0.0') for p, v in chosen.items())))
    return solutions


class EquivalenceTests(unittest.TestCase):
    def test_identity_and_immutability(self):
        data = catalog()
        saved = copy.deepcopy(data)
        result = m.equivalent(data, data)
        self.assertEqual(result['status'], 'equivalent')
        self.assertEqual(result['checked_assignments'], 2)
        self.assertEqual(data, saved)

    def test_removed_and_added_release(self):
        one = catalog({'a': {'1': {}}})
        for before, after, accepted in ((catalog(), one, True), (one, catalog(), False)):
            r = m.equivalent(before, after)
            self.assertEqual(r['status'], 'different')
            self.assertEqual(r['counterexample'], {'selected': {'a': '2.0.0.0'},
                'accepted_before': accepted, 'accepted_after': not accepted})

    def test_numeric_equivalence_and_aliases(self):
        before = catalog({'A_B': {'1': {}}}, {'a-b': '>=1,<=1.0'})
        after = catalog({'a.b': {'1.0.0': {}}}, {'A_B': '==1'})
        self.assertEqual(m.equivalent(before, after)['status'], 'equivalent')

    def test_unreachable_metadata_ignored(self):
        after = catalog({'a': {'1': {}, '2': {}}, 'unused': {'1': {'missing': '*'}}})
        r = m.equivalent(catalog(), after)
        self.assertEqual(r['status'], 'equivalent')
        self.assertEqual(r['candidate_assignments'], 2)

    def test_reachability_changes_selection(self):
        left = catalog({'a': {'1': {'b': '*'}}, 'b': {'1': {}}})
        right = catalog({'a': {'1': {}}, 'b': {'1': {}}})
        r = m.equivalent(left, right)
        self.assertEqual(r['status'], 'different')
        self.assertEqual(r['counterexample']['selected'], {'a': '1.0.0.0'})
        self.assertTrue(r['counterexample']['accepted_after'])

    def test_changed_roots(self):
        left = catalog({'a': {'1': {}}, 'b': {'1': {}}})
        right = catalog(left['packages'], {'b': '*'})
        self.assertEqual(m.equivalent(left, right)['status'], 'different')

    def test_missing_roots_and_cycles(self):
        missing = catalog({'a': {}}, {'missing': '*'})
        impossible = catalog({'a': {'1': {'absent': '*'}}})
        self.assertEqual(m.equivalent(missing, impossible)['status'], 'equivalent')
        cyclic = catalog({'a': {'1': {'b': '*'}}, 'b': {'1': {'a': '*'}}})
        self.assertEqual(m.equivalent(cyclic, copy.deepcopy(cyclic))['status'], 'equivalent')
        self.assertEqual(m.equivalent(cyclic, impossible)['status'], 'different')

    def test_budget_boundary_and_no_false_equivalence(self):
        data = catalog()
        self.assertEqual(m.equivalent(data, data, 1)['status'], 'inconclusive')
        self.assertEqual(m.equivalent(data, data, 2)['status'], 'equivalent')
        fewer = catalog({'a': {'1': {}}})
        self.assertEqual(m.equivalent(data, fewer, 1)['status'], 'inconclusive')
        self.assertEqual(m.equivalent(data, fewer, 2)['status'], 'different')

    def test_invalid_and_digest_binding(self):
        for value in (True, 0, -1, 1.5, 1000001):
            with self.assertRaises(m.fmt.Invalid):
                m.equivalent(catalog(), catalog(), value)
        with self.assertRaises(m.fmt.Invalid):
            m.equivalent(catalog({'a': {'1': {}, '1.0': {}}}), catalog())
        r = m.equivalent(catalog(), catalog({'a': {'1': {}}}))
        self.assertNotEqual(r['before_sha256'], r['after_sha256'])

    def test_seeded_independent_selection_sets(self):
        rng = random.Random(3604)
        for _ in range(400):
            pair = []
            for side in range(2):
                packages = {p: {v: {q: rng.choice(('*', '==1', '==2'))
                    for q in ('a', 'b', 'c', 'missing') if rng.random() < .15}
                    for v in ('1', '2') if rng.random() < .8} for p in ('a', 'b', 'c')}
                pair.append(catalog(packages, {rng.choice(('a', 'b')): rng.choice(('*', '==1', '==2'))}))
            sets = [raw_solutions(data) for data in pair]
            r = m.equivalent(*pair)
            self.assertEqual(r['status'], 'equivalent' if sets[0] == sets[1] else 'different')
            if r['status'] == 'different':
                witness = tuple(sorted(r['counterexample']['selected'].items()))
                self.assertEqual(witness in sets[0], r['counterexample']['accepted_before'])
                self.assertEqual(witness in sets[1], r['counterexample']['accepted_after'])

    def test_demo_and_cli(self):
        before, after = m.demo_catalogs()
        self.assertEqual(m.equivalent(before, after)['status'], 'equivalent')
        script = str(Path(__file__).with_name('equivalence.py'))
        for args, code in ((['demo'], 0), (['demo', '--max-assignments', '1'], 3),
                           (['demo', '--max-assignments', '0'], 2), (['demo', 'extra'], 2)):
            p = subprocess.run([sys.executable, '-B', script] + args, capture_output=True, text=True)
            self.assertEqual(p.returncode, code, p.stdout + p.stderr)
            self.assertIn('status', json.loads(p.stdout))


if __name__ == '__main__':
    unittest.main()
