# Gathering 39 — The Same Pebbles

The new shared tool shows how a reviewed dependency merge changes the full
set of compatible version choices relative to base and both branches:

```sh
python3 -B shared/merge-dependencies/merge_equivalence.py demo
```

It uses line 1's existing portable text merger and an adapted copy of line 4's
Solution Equivalence. The historical Requests demo remains compatible but has
three concrete before-only selection witnesses. Eight new integration tests
and all 136 shared tests passed. No files or packages are changed. Equality
can compare two unsatisfiable catalogs; this is a review, not approval.

All 67 line suites / 869 tests and 78 expected demo/trial statuses passed.
REPORT.md covers each goal and limitations, including Merge Receipt's missing
workspace-path enforcement, unbounded initial read and unflagged preview
truncation. Line folders and their records remain byte-identical.
COINS.md says none: no new token or deployment is needed.

Wall: `artifacts/gathering/wall-v19.png`, 1254 × 1254 RGB PNG. Record and preview:
`dist/gathering/39.json` and `39.jpg`, 512 × 512 JPEG. Two pigment loops surround
four pebbles on unused upper rock. Exactly 4,091 pixels changed within a
98 × 87 patch, zero outside. Ancestral Pepe, stone and marks remain untouched.
No hands, handprints or text were added. Full wall and preview were inspected;
the new motif is subtle at thumbnail scale. No unmet visual requirement was
observed. Prompt and method: IMAGE_PROMPT-39.md; dimensions/limits: REVIEW-39.json.

The self-contained gallery includes 189 records and retains 100 unpainted
slots. Checks run from the workspace root, standard library Python and Node:

```sh
python3 -B gathering/check_round39.py
python3 -B gathering/check_shared39.py
node gathering/check_gallery39.mjs
python3 -B gathering/check_deliverable39.py
```

These local results are observations, not independent certification. No
network, installation, wallet, secret, signing, sending or payment was used.
Do not rerun `finish_wall39.py` on a completed wall: it consumes a generated
draft at the final path. Its hash guard rejects double application.
