# Search Batch

Ask several questions of one offline document collection and see which sources
received exact line citations. The runner builds one bounded Evidence Search
index in memory, verifies cited source bytes, and checks the complete corpus
again before returning. It writes nothing. Python 3.9+ standard library only;
keep the adjacent `evidence-search` and `corpus-freshness` folders.

From the repository root, this one command demonstrates it:

```sh
python3 -B line-3/tools/search-batch/batch.py demo
```

When tried, the bundled historical ZTO and IMD corpus returned `zto.md:1-9`
for token decimals and `pool.md:1-10` for pool tick spacing. A third query had
no hit, and the coverage list identified the source without a selected citation.
The corpus contains recorded observations and assignment supplied pool data;
the demo makes no current chain, price, or factual truth claim.

For your own collection, put a UTF-8 JSON plan inside your workspace:

```json
{
  "format": "evidence-query-batch/v1",
  "queries": [
    {"id": "first", "query": "your search terms", "limit": 3, "require_all": false},
    {"id": "second", "query": "another question", "limit": 2, "require_all": true}
  ]
}
```

Then run `python3 -B line-3/tools/search-batch/batch.py run line-3/my-docs line-3/my-plan.json`.
The output keeps the input query order and limit and includes each engine result, a
SHA-256 identity for the sorted source path/hash pairs, cited and uncited source
paths, and IDs of queries without hits. “Uncited” means absent from these
bounded top results; it says nothing about relevance. Exit 0 means a complete
batch report, even with no-hit queries; exit 2 means invalid input, unreadable
sources, or a detected corpus change, with no partial report on stdout.

Plans accept 1–32 distinct ASCII IDs, 1–50 hits per query, and at most 64 KB of
JSON. Duplicate keys, invalid types, nonfinite JSON values, path traversal and
symlinks fail closed. Source selection and all source, index, passage and query
limits are inherited from Evidence Search. The runner uses only files inside
the current workspace and does not access environment variables, wallets,
secrets or the network. Source documents are inert data.

Keep the collection static while searching. A final full-corpus byte comparison
catches changes observed by that audit, but this is not an atomic filesystem
snapshot; a source could change and change back between reads. SHA-256 binds
bytes, not authority. The tool gives a worker a query portfolio with exact
citations, not proof of source truth or collection completeness.

Checks: `python3 -B line-3/tools/search-batch/test_batch.py -v`.
