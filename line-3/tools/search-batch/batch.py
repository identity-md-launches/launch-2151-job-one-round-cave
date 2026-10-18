#!/usr/bin/env python3
"""Run a bounded group of offline searches and summarize citation coverage."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

TOOLS = Path(__file__).absolute().parents[1]


def sibling(name, file):
    spec = importlib.util.spec_from_file_location(name, TOOLS / name.replace('_', '-') / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


engine = sibling('evidence_search', 'search.py')
freshness = sibling('corpus_freshness', 'freshness.py')
FORMAT = 'evidence-search-batch/v1'
PLAN_FORMAT = 'evidence-query-batch/v1'
MAX_PLAN_BYTES = 65536
MAX_QUERIES = 32


def reject_constant(value):
    raise engine.SearchError(f'nonfinite JSON value: {value}')


def load_plan(path):
    raw = engine.read_bytes(engine.workspace_path(path), MAX_PLAN_BYTES)
    try:
        plan = json.loads(raw.decode('utf-8'), object_pairs_hook=engine.reject_duplicates,
                          parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise engine.SearchError('query plan is not valid UTF-8 JSON') from None
    return validate_plan(plan)


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {'format', 'queries'} or plan['format'] != PLAN_FORMAT:
        raise engine.SearchError('invalid query plan envelope')
    queries = plan['queries']
    if not isinstance(queries, list) or not 1 <= len(queries) <= MAX_QUERIES:
        raise engine.SearchError('query plan must contain 1 to 32 queries')
    seen = set()
    for item in queries:
        if not isinstance(item, dict) or set(item) != {'id', 'query', 'limit', 'require_all'}:
            raise engine.SearchError('invalid query entry')
        identifier = item['id']
        if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', identifier) or identifier in seen:
            raise engine.SearchError('invalid or duplicate query id')
        seen.add(identifier)
        query = item['query']
        if not isinstance(query, str) or not 1 <= len(query) <= 4096 or not engine.tokens(query):
            raise engine.SearchError('query must contain a word or address and fit 4096 characters')
        if type(item['limit']) is not int or not 1 <= item['limit'] <= 50:
            raise engine.SearchError('query limit must be an integer from 1 to 50')
        if type(item['require_all']) is not bool:
            raise engine.SearchError('require_all must be boolean')
    return plan


def corpus_id(index):
    pairs = [[item['path'], item['sha256']] for item in sorted(index['documents'], key=lambda d: d['path'])]
    encoded = json.dumps(pairs, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def run(root, plan):
    validate_plan(plan)
    index = engine.build_index(root)
    rows = []
    cited = set()
    no_hits = []
    for item in plan['queries']:
        result = engine.search(index, item['query'], root, item['limit'], item['require_all'])
        cited.update(hit['path'] for hit in result['hits'])
        if not result['hits']:
            no_hits.append(item['id'])
        rows.append({'id': item['id'], 'limit': item['limit'], 'result': result})
    audit = freshness.audit(index, root)
    if not audit['fresh']:
        raise engine.SearchError('corpus changed during batch; retry with static files')
    sources = sorted(item['path'] for item in index['documents'])
    return {'format': FORMAT, 'corpus_sha256': corpus_id(index),
            'indexed_documents': len(sources), 'queries': rows,
            'coverage': {'cited_documents': sorted(cited),
                         'uncited_documents': sorted(set(sources) - cited),
                         'no_hit_query_ids': no_hits}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('run', help='read a JSON query plan and search a corpus')
    command.add_argument('root')
    command.add_argument('plan')
    commands.add_parser('demo', help='search bundled historical ZTO/IMD documents')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            root = TOOLS / 'evidence-search' / 'examples' / 'docs'
            plan = {'format': PLAN_FORMAT, 'queries': [
                {'id': 'zto', 'query': 'ZTO token decimals', 'limit': 2, 'require_all': True},
                {'id': 'pool', 'query': 'ZTO pool tick spacing', 'limit': 2, 'require_all': True},
                {'id': 'absent', 'query': 'glacial orchid', 'limit': 2, 'require_all': True}]}
        else:
            root, plan = args.root, load_plan(args.plan)
        print(json.dumps(run(root, plan), ensure_ascii=False, indent=2))
        return 0
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
