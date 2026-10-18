#!/usr/bin/env python3
"""Compare complete reachable selection sets of two finite offline catalogs."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CHECKER = HERE / 'exhaustive.py'
if not CHECKER.is_relative_to(Path.cwd().resolve()):
    raise RuntimeError('run from the workspace containing the tools')
spec = importlib.util.spec_from_file_location('equivalence_checker', CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
fmt = checker.fmt


def normalize(data):
    packages, roots = fmt.validate(data)
    # Numeric-equivalent labels denote the same release across catalogs.
    packages = {p: {'.'.join(map(str, fmt.version(v))): deps
                    for v, deps in releases.items()}
                for p, releases in packages.items()}
    return packages, roots


def digest(packages, roots):
    return hashlib.sha256(json.dumps({'packages': packages, 'roots': roots},
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def equivalent(before, after, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise fmt.Invalid('max_assignments must be an integer from 1 to 1000000')
    left, left_roots = normalize(before)
    right, right_roots = normalize(after)
    # Union over all release edges on both sides. Any valid selection on either
    # side is in this overapproximation, including missing-target branches.
    possible, todo = set(), list(set(left_roots) | set(right_roots))
    while todo:
        p = todo.pop()
        if p in possible:
            continue
        possible.add(p)
        for packages in (left, right):
            for deps in packages.get(p, {}).values():
                todo.extend(deps)
    names, domains, total = sorted(possible), [], 1
    for p in names:
        versions = sorted(set(left.get(p, {})) | set(right.get(p, {})), key=fmt.version)
        domain = versions if p in left_roots and p in right_roots else [None] + versions
        domains.append(domain)
        total *= len(domain)
    base = {'method': 'finite-selection-equivalence-v1',
            'before_sha256': digest(left, left_roots),
            'after_sha256': digest(right, right_roots),
            'candidate_assignments': total, 'max_assignments': max_assignments,
            'release_labels': 'four numeric components; equivalent numeric labels coalesced'}
    checked = 0
    for values in itertools.product(*domains):
        if checked == max_assignments:
            return dict(base, status='inconclusive', checked_assignments=checked)
        checked += 1
        selected = {p: v for p, v in zip(names, values) if v is not None}
        # Exact closure equality rejects extraneous unreachable assignments;
        # otherwise two catalogs with different reachability could look equal.
        accepts_left = checker.assignment(left, left_roots, selected) == selected
        accepts_right = checker.assignment(right, right_roots, selected) == selected
        if accepts_left != accepts_right:
            return dict(base, status='different', checked_assignments=checked,
                        counterexample={'selected': selected,
                                        'accepted_before': accepts_left,
                                        'accepted_after': accepts_right})
    return dict(base, status='equivalent', checked_assignments=checked)


def demo_catalogs():
    before = fmt.load(HERE / 'examples/base.json')
    # Independent demonstration of a safe reduction: filter only releases of
    # mandatory roots that violate their own root requirement. No pruner import.
    packages, roots = fmt.validate(before)
    after = {'roots': roots, 'packages': {
        p: {v: deps for v, deps in releases.items()
            if p not in roots or checker.matches(v, roots[p])}
        for p, releases in packages.items()}}
    return before, after


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', help='workspace-local JSON, or demo')
    parser.add_argument('after', nargs='?', help='second workspace-local JSON')
    parser.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        if args.before == 'demo' and args.after is None:
            before, after = demo_catalogs()
        elif args.after is not None and args.before != 'demo':
            before, after = fmt.load(args.before), fmt.load(args.after)
        else:
            raise fmt.Invalid('provide two catalogs, or demo alone')
        result = equivalent(before, after, args.max_assignments)
        code = {'equivalent': 0, 'different': 1, 'inconclusive': 3}[result['status']]
    except (fmt.Invalid, OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        result, code = {'status': 'invalid', 'error': str(exc)}, 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
