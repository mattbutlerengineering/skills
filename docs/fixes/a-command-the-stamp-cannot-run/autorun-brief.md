# Autorun brief — a command the stamp cannot run

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate is a latent trap recorded during an earlier run and re-derived
from scratch here: `factory_init._PRODUCT_TOOLS` is a hand-maintained
second copy of a fact `MIRRORS` already owns, and nothing checks the
copy against the original.

## What and why

`product_form` is the one production statement of the root→product
command respelling. It walks a hand-typed tuple:

```python
_PRODUCT_TOOLS = ("gates.py", "validator.py", "assembler.py",
                  "budget_guard.py", "cost_report.py", "gate_digest.py",
                  "rejection_mining.py")
```

`MIRRORS` — three definitions below it, in the same file — already says
which root files land under `tools/factory/` in a stamped repo. Ten of
the seventeen mirrored Python tools are absent from `_PRODUCT_TOOLS`, so
a Makefile command naming one of them passes straight through into the
payload Makefile unchanged, telling a stamped product repo to run a file
that is not at its root.

`MIRRORS`' own comment states the invariant and names its enforcement:
"It is absent from `_PRODUCT_TOOLS` on purpose — that tuple respells
Makefile commands, and no target invokes it." That is a claim about the
Makefile, and nothing checks it. `TestLockstep` cannot: it asserts the
payload Makefile against `[product_form(c) for c in ...]`, so the
expectation is computed by the function under test and both sides carry
the same mistake.

`work_queue.py` is the live edge: mirrored, shipped, has a `main()`, and
absent from `_PRODUCT_TOOLS`. The obvious next Makefile target breaks
the stamp silently.

## Scale and re-entry

Maintenance run, slug `a-command-the-stamp-cannot-run`. Re-entry is
`implement`: `MIRRORS` already holds the fact; `product_form` needs to
read it instead of a copy, and the Makefile claim needs an assertion.

## Scope

In: `product_form` derives the respelling from `MIRRORS`; a test pins
that derivation; a test pins the claim the comment makes about the root
Makefile.

Out: adding any Makefile target. Out: `gates.py` — contended by an open
PR, and this rule belongs to `factory_init`, which owns the transform.
Out: `TestLockstep`'s own hand-maintained target enumeration, which is a
separate question about a different file.

## Constraints

Stdlib only. `factory_init.py` is NOT in `factory_init.MIRRORS` — it is
the stamping tool, not part of the payload — so no mirror. The
regenerated payload Makefile must come out byte-identical, which is the
proof that this is a structural fix with no behaviour change today; if
it does not, that is itself a finding.

## Release authorization

None. Ship prepares and stops.
