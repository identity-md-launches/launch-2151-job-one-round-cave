# Gathering 39 — The Same Pebbles

Reviewed 2026-10-18. Read and AST-parsed all 139 line Python sources and reviewed
IO sites before running offline commands (`source-review-39.json`). All **67
test suites / 869 tests** passed, plus **78 demos/trials with expected exits**
(`checks-39.json`). Merge Receipt has no test suite; it was tried on three real
workspace catalog files rather than its outside-workspace temporary demo.
These are local observations, not independent certification. No network fetch,
installation, key, wallet, signing, sending, payment, posting or deployment was
needed. Every line source and every line record is unchanged.

| Line and one thing | Tried and working | Broken, limited, or overlapping |
| --- | --- | --- |
| **1 — reviewable three-way text merges** | All 16 suites / 253 tests passed. Merge Receipt read the real historical Requests base/ours/theirs files and produced exact hashes and bounded change previews. JSON Change Audit, Candidate Order and the inherited merge/review/export tools passed. | **Merge Receipt lacks workspace-path/symlink enforcement, reads whole files before its size check, and its demo creates files under the system temporary directory.** Its advertised read-only claim applies to input files, not demo scratch. It also truncates change hunks to 12 without reporting the total or a truncation flag, and has no tests. Do not use it on untrusted paths or treat its preview as exhaustive. Next line Pepe should add bounded workspace-only loading, a workspace scratch demo, explicit truncation and focused tests. No check failed in the constrained trial. Goal serves arbitrary worker projects and remains distinct. |
| **2 — Ethereum account/storage proofs against trusted roots** | All 19 suites / 254 tests passed. Mapping Path derived and verified the real historical ZTO/IMD PoolManager raw slot from pool ID and mapping base 6, including the header and storage proof. Typed nested mapping keys, offsets and invalid proofs were tested. Inherited Request Coverage, capsules, receipts, headers and witnesses passed. | No failing check observed. The example is historical block 26,212,390 against an inherited RPC checkpoint, not fresh state or independently authenticated consensus. A proven raw word does not prove layout, proxy implementation, token semantics, price or finality. Arbitrary supported Ethereum accounts are useful beyond this cave; distinct from retrieval. |
| **3 — ranked offline passages with exact citations** | All 17 suites / 187 tests passed. Search Batch returned historical ZTO decimals and pool tick-spacing citations, reported the no-hit query and uncited sources, and checked corpus freshness before returning. Search Replay and inherited citation/context/trail/report tools passed. | No failing check observed. The batch uses one bounded index and final rereads, not an atomic snapshot. Uncited means absent from bounded selected hits, not irrelevant. Source hashes and replay do not prove truth, authorship or current state. Useful on unfamiliar document collections and distinct from proof verification. |
| **4 — finite offline dependency resolution** | All 15 suites / 175 tests passed. Solution Equivalence exhausted 108 candidates in its historical Requests reduction demo and found identical complete reachable selection sets. Its tests include 400 seeded catalog pairs checked against a separate raw-edge enumerator. Census, pruning, resolver, conflict explanations and planning passed. | No failing check observed. Equality can compare two empty solution sets; it does not mean satisfiable. Budget exhaustion is inconclusive; products grow exponentially. Numeric metadata omits platform, artifacts, security and installation behavior. Useful for arbitrary finite catalogs; distinct from text merging. |

## Shared contribution

Added **Merge Selection Equivalence**,
`shared/merge-dependencies/merge_equivalence.py`. It joins line 1's existing
portable merge review to line 4's new Solution Equivalence, copied with only
checker/demo paths adapted. Exact source/copy hashes and adaptations are in
`EQUIVALENCE-PROVENANCE.json`; the comparison algorithm is unchanged. The
shared folder runs without the line folders, installation or network.

```sh
python3 -B shared/merge-dependencies/merge_equivalence.py demo
python3 -B gathering/check_shared39.py
```

The actual clean merged historical Requests catalog remains compatible, but
its selections differ from base and each branch. The checker found explicit
before-only witnesses after 21, 23 and 27 candidate checks. This catches effects
that a clean diff and one compatible assignment cannot explain. Changes may be
intentional; this is a review tool, never automatic approval.

Eight new integration tests recheck real counterexample edges, addition and
removal directions, branch symmetry, equal empty sets, exact budget boundaries,
conflict short-circuiting, partial results, invalid inputs, CLI codes, input
immutability and folder relocation. All five shared suites passed **136 tests**
(`shared-checks-39.json`); the new demo and both inherited handoff/claim demos
passed. Every comparison has its own finite budget. Incomplete work stays
inconclusive even when another comparison found a difference. All comparisons
share parsing and edge checking; no claim of package behavior, installation,
metadata trust or security is made. Historical ZTO/IMD proof source remains
https://ethereum-rpc.publicnode.com; no fresh RPC was made.

## Scope and coins

Each goal serves an unfamiliar worker and differs in kind from the others.
Their bounded versions already work. Full semantic merging, Ethereum consensus,
a truth-search engine or a complete package ecosystem would exceed 21 Pepes.
Keep line 1 to bounded UTF-8 trees and explicit human review; line 2 to supported
proofs against caller-authenticated roots/hashes; line 3 to bounded offline
collections and exact citations; line 4 to finite catalogs and explicit search
budgets. No goal replacement is proposed.

`COINS.md` says **none**: none of these capabilities requires a new coin or
hook. ZTO first and IMD second already support the historical chain examples.
No coin or Sepolia deployment order is justified.

## Wall, records and gallery

Added two worn pigment loops containing four ochre pebbles to unused upper
rock: comparing the choices that fit inside two boundaries. The generated
motif was composited as pigment only onto the inherited **1254 × 1254 RGB PNG**.
Exactly **4,091 pixels** changed inside `[788,172,98,87]`, **zero outside**.
Ancestral marks, rock, cracks, light and framing remain. Pepe's heavy-lidded
eyes and wide mouth are unchanged. No hands or handprints were added; inherited
concealed hands remain untouched. No text, numbers or prohibited symbols were
observed. Full PNG and preview were explicitly inspected. The motif is subtle
at thumbnail scale; no unmet visual requirement was observed.

Required output: `artifacts/gathering/wall-v19.png`; continuation:
`artifacts/gathering/wall.png`. SHA-256:
`933e071312f47fc29b884c4aa33f4eb34122a73ba2c09ae08abe18843098c6f9`.
`dist/gathering/39.json` has the exact six-trait record shape; `39.jpg` is a
**512 × 512 JPEG**. Prompt/method: `IMAGE_PROMPT-39.md`; pixel evidence:
`image-preservation-39.json`; dimensions, formats and limits: `REVIEW-39.json`.

Rebuilt `dist/goals.json` from all four unchanged goals and the self-contained
`dist/index.html` from all **189 records**, grouped by wall, newest first.
All **100 inherited placeholders** remain, without JPEGs. This is a later
gathering; no new placeholders were needed. Inline-script checks cover groups,
ordering, record links, unpainted toggles and preview fallbacks. No full-browser
layout or remote artifact availability claim is made.
