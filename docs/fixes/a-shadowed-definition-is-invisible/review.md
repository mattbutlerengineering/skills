---
stage: review
run: maintenance:a-shadowed-definition-is-invisible
date: 2026-08-30
assumptions: []
---

# Review: a shadowed definition is invisible

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. A test, not a gates detector — decided, with the trade stated

`gates.py` was the obvious home: K is unclaimed, and the DETECTORS
table invites a new row. It was rejected:

- **The universe fights the gate.** Every detector must run against
  synthetic fixture trees under `--selftest`, where there is no git
  repo — but `git ls-files` is exactly what this check needs, for the
  250-vs-98 worktree reason in `defect.md`. A detector would have to
  either grow a second, weaker universe or special-case the selftest.
- **Conflict for nothing.** `gates.py` is mirrored, so a detector
  costs a payload copy, a manifest regeneration, and a textual
  conflict with open PR #377, which is claiming detector J and editing
  the same table and docstring.
- **The precedent exists.** `tests/test_factory_init.py` already pins
  a repo-structural invariant (payload↔root) as a test rather than a
  detector.

What is given up is real and worth naming: a stamped downstream repo
inherits `gates.py` but not this file, so downstream repos do not get
the check. Recorded in `verification.md` under what-is-not-verified.

### 2. The pure-function split earns itself — kept

`shadow_problems(rel, source)` is pure over one file's text; the
repo-wide walk is a thin caller. That is the same split as
`gates.evidence_problems` / `check_evidence_honesty`, and it is what
made the seven edge cases testable with synthetic sources instead of by
mutating real files. Only the one mutation that *had* to touch a real
file — reproducing the original bug — did so, and it is reverted.

### 3. The edge cases are the substance, not padding — kept

A naive version of this check is four lines and wrong. Three of the
seven cases are things it must **not** flag: two classes each defining
`setUp`, an `if/else` conditional definition, and the `@property` /
`@setter` pair. Get any of those wrong and the check is noise that
someone disables. The conditional case is handled by construction
rather than by a special case — a nested definition is never a sibling
in `body` — which is worth a test precisely because it is easy to
"fix" into a bug later.

### 4. Constant rebinding deliberately excluded — held

`X = 1 ... X = 2` is not reported. Reassignment is ordinary Python and
flagging it would bury the signal that matters. The consequence that
motivates this whole run — tests silently disappearing — is specific to
`def`/`class`. Stated in what-is-not-verified rather than left as an
apparent gap.

### 5. The check cannot protect itself, and that is acceptable

If someone shadows `TestTheRepoItself`, the last binding still runs, so
a duplicate of the check itself is caught by the check itself. A
duplicate that *deletes* the check would have to be a rebinding, which
is what it reports. No further guard is needed.

### 6. This run exists because of a disclosed mistake — worth stating

The hazard was found by making it. That is recorded in the previous
run's `verification.md` §5 and in `defect.md` here rather than
smoothed over, because "an agent hit this inside a single review" is
the strongest evidence available that the check is worth its lines.
