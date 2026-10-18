# Solution Equivalence

Check whether two finite dependency catalogs admit exactly the same complete,
root-reachable version selections. Use this after pruning or editing metadata:
a textual delta alone cannot show whether compatibility actually changed.

Run from the repository root with Python 3.9+ and the standard library:

```sh
python3 -B line-4/tools/solution-equivalence/equivalence.py demo
```

I ran this command: it exhausted **108 candidate assignments** and reported
`equivalent`. The demo reads the committed historical Requests metadata projection
and constructs a second catalog by removing releases excluded by mandatory root
constraints. It does not refresh metadata or import the pruning implementation.
The original example and its provenance remain unchanged.

For your own workspace-local inputs:

```sh
python3 -B line-4/tools/solution-equivalence/equivalence.py before.json after.json --max-assignments 10000
```

Exit 0 / `equivalent` means complete enumeration found identical selection sets.
Exit 1 / `different` includes one selection accepted by exactly one catalog and
the direction of the difference. Exit 3 / `inconclusive` means the budget ran out;
it makes no equivalence claim. Exit 2 / `invalid` means malformed input or a read
failure. Two unsatisfiable catalogs are equivalent because both selection sets
are empty. Equal solution sets do not imply either catalog has a solution.

The checker enumerates the union of all potentially reachable releases on both
sides, including optional absence. Every candidate must satisfy all root and
selected dependency constraints and contain exactly the reachable closure.
Numeric-equivalent release labels (`1`, `1.0`) compare equal and witnesses use
four components (`1.0.0.0`). Package aliases use the inherited normalization.
Unreachable metadata differences do not change selection equivalence. Different
dependency edges can still be equivalent if they admit the same selections.

Reports bind both normalized inputs with SHA-256 digests. The digests coalesce
numeric release labels and canonical package names, but retain constraint text;
they are input identities, not semantic-equivalence hashes or authentication.
Search order is deterministic. The default budget is 10,000 candidates, at most
1,000,000. Products grow exponentially; a budget is not a wall-clock guarantee.

Runtime reuses Offline Resolver's finite numeric grammar and bounded,
workspace-only JSON loader through Exhaustive Audit's iterative edge checker.
It never calls the resolver search. Those parsers and the edge checker remain
trust dependencies. This checks metadata selection compatibility, not package
artifacts, interpreter/OS constraints, security, registry completeness, current
availability, installation, or preservation of package behavior.
It reads no environment, installed packages, keys or configuration, and performs
no network calls or writes. No dependencies need installing.

Validation:

```sh
python3 -B -m unittest discover -s line-4/tools/solution-equivalence -p 'test_*.py' -v
```

All 11 tests passed, including 400 seeded pairs checked with an independent
raw-edge selection-set enumerator, counterexample directions, root/reachability
changes, missing targets, cycles, numeric labels, input immutability, exact
budget boundaries and CLI status handling. These are local checks.
