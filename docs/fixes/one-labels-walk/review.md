---
stage: review
run: maintenance:one-labels-walk
date: 2026-08-24
assumptions:
  - "Severity is arbitrated here rather than by the operator — the run is autorun-driven. F1 is called major because it qualifies the run's own headline claim, not because anything is broken; it is deferred, with the qualification carried into release.md so the claim is never read wider than it is true."
  - "Scope is main..HEAD (five commits, 7 files), read as a diff. The eight remaining one_owner.py groups are outside it by autorun-brief.md and are named, not touched."
---

# Review: the extraction has one owner; the filter has two

Reviewed `main..HEAD` — `486d476`, `48940c8`, `45f4b43`, `f79410e`,
`87b3b9a`. The production change is 24 insertions and 10 deletions in one
root module.

## What was examined

- **`plane_drift.issue_lifecycle` and the new import** — against
  `architecture.md`'s contract and `cli.label_names`' documented
  strictness.
- **Every `wo:` prefix filter in the tree**, by grep, to find out whether
  the fold left a second site of the fact it claims to own. It did.
- **`cli.py`'s import-time behaviour**, because the module docstring now
  makes a claim about it.
- **The import graph**, for cycles.
- **The one-owner pre-pass**, as a design check rather than a gate.

## Findings

### F1 — major, DEFERRED — the `wo:` filter still has two sites

The run folded *extraction*. It did not fold the **filter**, and one other
site applies it to the same payload:

```
$ grep -rn 'startswith("wo:")' --include="*.py" . | grep -v factory/templates | grep -v "^./tests/"
dashboard.py:255:                              if name.startswith("wo:")), None)
plane_drift.py:54:                  if name.startswith("wo:"))
sweeps.py:260:        elif label.startswith("wo:"):
```

`sweeps.py:260` is a different question — is this one intake label a
lifecycle label — and is not a finding. `dashboard.py:252-255` is the same
question this module now owns:

```
$ sed -n '252,255p' dashboard.py
            issue = by_number.get(number, {})
            lifecycle = next((name[len("wo:"):]
                              for name in label_names(issue)
                              if name.startswith("wo:")), None)
```

Failure scenario — and it is a maintenance one, not a wrong output: the
two sites already disagree about what to do when an issue carries **two**
lifecycle labels. `issue_lifecycle` returns both, sorted, which is what
lets `reconcile_drift` report the state-machine violation.
`dashboard.py:254` takes the **first in payload order** and strips the
prefix. So `next(iter(issue_lifecycle(issue)), None)` is not a
behaviour-preserving substitution: it would silently change which of two
labels the dashboard renders. Folding it needs a decision about which
order is right, which is a decision this run's brief scoped out.

**Deferred, and the qualification carried forward.** "One owner for the
labels-array walk" is exactly true — extraction has one owner now — and
would be over-read as "one owner for everything about `wo:` labels".
`release.md` says so in those words.

Worth naming separately: **`one_owner.py` cannot see this one.** It is a
re-implementation over an already-extracted list, not a shared value or a
shared key set, which is the known-miss class `tests/test_one_owner.py`
already pins. The run that just cleared a group the pass *can* see found
an adjacent one it cannot, by grep, in the same file it was editing.

### F2 — minor, no action — the purity claim is now checkable, and checks out

The module docstring asserts that importing `cli` "runs no subprocess".
Verified rather than assumed, since a claim in a docstring is the kind
that rots:

```
$ python3 -c "import ast, collections, pathlib; print(collections.Counter(type(n).__name__ for n in ast.parse(pathlib.Path('cli.py').read_text()).body))"
Counter({'FunctionDef': 13, 'Import': 8, 'Assign': 4, 'ImportFrom': 2, 'Expr': 1, 'ClassDef': 1})
```

No control flow and no bare calls at module level. The one assignment that
*is* a call is `_gh = runner("gh")` (cli.py:306), and `runner` returns a
closure without executing anything:

```
$ sed -n '/^def runner/,/^    return run/p' cli.py
def runner(binary):
    """A run(args) callable shelling out to `binary`, returning the
    CompletedProcess. A failed or missing binary raises CLI_FAILURES —
    the caller's concern, not this adapter's."""
    def run(args):
        return subprocess.run([binary, *args], check=True,
                              capture_output=True, text=True)
    return run
```

No action: the docstring is accurate. Recorded because the next person to
read that sentence should not have to re-derive it.

## Examined and NOT findings

- **Import cycle.** `cli.py` imports stdlib only — eight `Import` and two
  `ImportFrom` nodes, none of them a factory module — so `plane_drift`
  importing it closes no loop. Both of `plane_drift`'s consumers already
  import both modules.
- **Duplicate lifecycle labels.** `sorted()` over a list preserves them,
  and `reconcile_drift`'s multiple-lifecycle-labels line needs them to
  survive. Pinned by `test_a_duplicate_lifecycle_label_survives`, written
  before the fold.
- **The `AttributeError` widening.** A non-dict `issue` returns `[]`
  instead of raising. `reconcile_drift` drops a non-dict entry with a
  `drift:` problem before either walk runs (plane_drift.py:68-72), so it
  is unreachable; it removes a crash and adds no silence, and it is
  pinned.
- **The strictness swap.** The old walk admitted a `None` name and
  filtered it a line later; the seam drops it at extraction. Identical for
  every `wo:`-prefixed name, and measured across every label-entry shape
  in `verification.md` D2 — zero disagreements against the old code.
- **Security.** No new input surface, no new subprocess, no interpolation.
  The payload was already untrusted in shape and is handled more strictly
  now, not less.
- **The pre-pass.** Nine groups to eight, none naming `plane_drift`.

```
$ python3 one_owner.py | tail -1
one-owner: 8 problem(s)
```

- **The eight remaining groups.** Out of scope by `autorun-brief.md`;
  each is its own seed per `docs/backlog.md:53`.

## Verdict

**No critical findings and no unfixed major ones in the code.** F1 is a
deferred design finding whose only obligation on this run is honesty about
the headline claim, discharged in `release.md`. F2 needed no action. Ship
may proceed as prepare-and-stop — the brief authorises no release — and
under ADR-0036 clause 2.
