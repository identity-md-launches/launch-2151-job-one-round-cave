# Merge Receipt

Create a compact, read-only receipt for a three-way text review. It records the
SHA-256 and line-level additions/removals for each input, so a reviewer can
identify exactly which snapshots were considered before opening the full diff.
It uses only Python's standard library and never writes, merges, executes, or
modifies the supplied files.

Run the offline demonstration from the workspace root:

```sh
python3 -B line-1/tools/merge-receipt/merge_receipt.py --demo
```

For real files:

```sh
python3 -B line-1/tools/merge-receipt/merge_receipt.py BASE OURS THEIRS
```

The JSON output includes byte counts, hashes, changed-line counts, and a small
bounded preview of each branch's line changes. It is evidence for review, not a
semantic merge or approval; it does not resolve conflicts, parse languages, or
prove author intent.
