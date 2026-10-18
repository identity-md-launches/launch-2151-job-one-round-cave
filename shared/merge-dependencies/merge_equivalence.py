#!/usr/bin/env python3
"""Compare each input catalog's solution set with a reviewed text merge."""
import argparse
import json
import sys

import check_merge as first
import equivalence

CODES = {'preserved': 0, 'changed': 1, 'text_conflict': 1, 'inconclusive': 3}


def check(base, ours, theirs, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise ValueError('assignment budget must be an integer from 1 to 1000000')
    packet = first.review.packet(base, ours, theirs)
    result = {'format': 'merge-selection-equivalence/v1', 'status': 'text_conflict',
              'review': packet, 'comparisons': {},
              'limits': [
                  'No inputs are changed; this is a review, not approval or an installation.',
                  'Each comparison has its own assignment budget; elapsed time is not bounded.',
                  'Preserved means identical finite selection sets, including two empty sets.',
                  'A different result supplies one counterexample, not every change.',
                  'All comparisons share numeric parsing and edge checking.',
                  'No publisher, artifact, platform, security or package behavior claim.']}
    if not packet['clean']:
        return result
    merged = first.parse(packet['merged'])
    # Validate every catalog before enumerating, so an invalid later branch
    # cannot be silently hidden behind an earlier counterexample.
    inputs = [first.parse(text) for text in (base, ours, theirs)]
    for data in [merged, *inputs]:
        equivalence.normalize(data)
    for name, data in zip(('base', 'ours', 'theirs'), inputs):
        result['comparisons'][name] = equivalence.equivalent(data, merged, max_assignments)
    statuses = {row['status'] for row in result['comparisons'].values()}
    # Any unfinished comparison keeps the overall report incomplete, even if
    # another comparison has already found a real difference.
    result['status'] = ('inconclusive' if 'inconclusive' in statuses else
                        'changed' if 'different' in statuses else 'preserved')
    return result


def demo(max_assignments=10000):
    folder = first.HERE / 'examples'
    texts = [first.review.engine.read_text(folder / f'plan-{name}.json')
             for name in ('base', 'ours', 'theirs')]
    return check(*texts, max_assignments)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('demo', 'check'):
        item = sub.add_parser(name)
        if name == 'check':
            for branch in ('base', 'ours', 'theirs'):
                item.add_argument(branch)
        item.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo(args.max_assignments)
        else:
            texts = [first.review.engine.read_text(p) for p in (args.base, args.ours, args.theirs)]
            result = check(*texts, args.max_assignments)
        code = CODES[result['status']]
        if args.command == 'demo' and result['status'] == 'changed':
            code = 0  # The demonstration succeeds when it exposes the change.
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return code
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({'status': 'invalid', 'error': 'Invalid workspace catalog inputs or budget.'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
