---
stage: diagnose
run: maintenance:a-lazy-import-escapes-the-closure-test
date: 2026-08-30
assumptions: []
---

# Defect: a lazy import escapes the payload closure test

## The invariant, and where it is stated

CLAUDE.md:

> It is mirrored into the payload iff a payload tool imports it:
> `plane_drift.py` is root-only because neither of its callers ships
> (ADR-0060).

`TestPayloadToolsImport` enforces it, and its docstring records the
incident that bought it:

> That is exactly how rejection_mining.py shipped for days importing
> `sweeps`, a module MIRRORS does not carry: the root import resolved,
> the payload import could not, and the failure waited for a scheduled
> run to surface.

The test runs `python3 -B -c "import <tool>"` with the payload directory
as `sys.path[0]`, once per mirrored tool. A missing sibling is an
`ImportError` and the test fails. Good — for **module-scope** imports.

## The hole

`gates.py` reaches two modules through `importlib` inside function
bodies, both deliberately and both documented:

```python
# declared_labels
for name, pull in sorted(LABEL_DECLARERS.items()):   # assembler, human_gates
    try:
        module = importlib.import_module(name)
    except ImportError:
        continue

# check_label_wiring (detector J)
try:
    label_sync = importlib.import_module("label_sync")
except ImportError:
    return []
```

The laziness is correct — the comment explains it: *"label_sync.py is a
stamped sibling, and importing it at module scope would make a partial
stamp crash gates.py before any detector ran."*

But it means `import gates` never executes either import, so the closure
test cannot see them. And `except ImportError` turns the miss into
silence rather than an error.

## What that costs

If any of `assembler`, `human_gates` or `label_sync` stopped shipping:

- **Detector J returns `[]`** in every stamped repo — permanently green,
  checking nothing. Its own docstring says bailing on a bad taxonomy
  "would let one malformed entry switch this detector off silently,
  which is the failure mode it exists to close." The module-missing case
  is that same failure one level up, and it is not closed.
- `declared_labels` silently under-reports, so the labels those modules
  declare look undeclared.

Nothing fails. Not the closure test (the import never runs at module
scope), not detector E (checksums match — the file is simply absent from
the manifest by construction), not `lint.py`.

## Is it live today?

No. All three ship:

```
dynamically imported: ['assembler', 'human_gates', 'label_sync']
NOT shipped         : []
```

This is the same shape as the shadowed-definition run: a latent hazard
whose failure mode is **silence**, in a check that is supposed to be the
thing that speaks up. `rejection_mining`/`sweeps` proves the static half
of this invariant does get violated in practice; there is no reason the
lazy half is immune.

## Why the fix must derive the list

A test that hard-codes `{"assembler", "human_gates", "label_sync"}`
would be wrong the day a fourth lazy import is added, and wrong
silently. This repo has just been bitten by exactly that
(`docs/fixes/a-call-site-list-that-drifted/`), so the set is read out of
`gates.py`'s own source: string literals passed to `import_module`, plus
the keys of a module-level table whose `.items()` binds the loop
variable it is called with.

A third shape — anything the derivation cannot follow — is reported and
**fails the test**, rather than quietly narrowing the set it checks. A
derivation that silently covers nothing would be the same defect as the
one it is closing.
