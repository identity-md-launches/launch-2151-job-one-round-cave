#!/usr/bin/env python3
"""Emit a bounded, read-only receipt for three-way text review."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

LIMIT = 1_000_000
PREVIEW = 12


def snapshot(path):
    data = Path(path).read_bytes()
    if len(data) > LIMIT:
        raise ValueError("input exceeds 1 MiB")
    text = data.decode("utf-8")
    lines = text.splitlines()
    return {
        "path": str(path), "bytes": len(data), "lines": len(lines),
        "sha256": hashlib.sha256(data).hexdigest(), "text": text, "lines_data": lines,
    }


def changes(base, branch):
    rows = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, base, branch).get_opcodes():
        if tag != "equal":
            rows.append({"kind": tag, "base": [i1 + 1, i2], "branch": [j1 + 1, j2],
                         "removed": i2 - i1, "added": j2 - j1})
    return rows


def receipt(paths):
    items = [snapshot(p) for p in paths]
    base = items[0]["lines_data"]
    result = {"base": {k: v for k, v in items[0].items() if k not in ("text", "lines_data")},
              "branches": []}
    for item in items[1:]:
        result["branches"].append({
            **{k: v for k, v in item.items() if k not in ("text", "lines_data")},
            "changes": changes(base, item["lines_data"])[:PREVIEW],
        })
    return result


def demo():
    base = "one\ntwo\nthree\n"
    ours = "one\ntwo ours\nthree\n"
    theirs = "one\ntwo\nthree theirs\n"
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for name, text in (("base", base), ("ours", ours), ("theirs", theirs)):
            p = Path(d) / name
            p.write_text(text, encoding="utf-8")
            paths.append(p)
        print(json.dumps(receipt(paths), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="BASE OURS THEIRS")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        demo()
        return 0
    if len(args.paths) != 3:
        parser.error("provide BASE OURS THEIRS, or use --demo")
    print(json.dumps(receipt(args.paths), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
