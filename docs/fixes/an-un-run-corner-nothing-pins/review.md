---
stage: review
run: maintenance:an-un-run-corner-nothing-pins
date: 2026-08-27
assumptions: []
---

# Review: an un-run corner nothing pins

## What was examined

The run's whole diff: a rewritten `tests/test_fixture_recorders.py`
(one test became five, the enumeration derived) and the same
`recording_problems` guard added to both `record.py` scripts. Read
alongside both replay suites and their zero-event guards, the committed
transcripts and their `provenance.json` files, the eval result record's
own shape, and CLAUDE.md's eval-honesty section.

## Findings

### Critical

None.

### Major

**The guard is two copies, deliberately, and the pin is what makes that
defensible.** The recorders are standalone hand-run scripts sharing no
import; there is no module either could reach without inventing one.
`test_the_recorders_refuse_identically` compares the two refusal strings
and fails if they diverge, which is the repo's existing idiom for
justified duplication — the two Makefiles and the payload mirror are
held the same way. Without that test this would be an unowned copy and
the finding would be worse than the defect.

**The guard refuses the empty case only, and that boundary is the
judgment call in this run.** A length threshold would catch partial
crashes too, and would also refuse genuine early decisions — the
recorder stops the moment the detector decides, so a two-line transcript
is a normal outcome. Zero lines is the only stream that cannot be
evidence of anything. The narrower rule is the one that never produces
a false refusal, and a false refusal in a hand-run script that a human
invokes once a quarter is expensive: it teaches the human to work around
the guard.

**Deriving an enumeration introduces its own failure mode, and it is
pinned.** A glob that matched nothing would turn every test in the file
green and vacuous — strictly worse than the hand-typed tuple it
replaced. `test_the_glob_finds_the_recorders_that_exist` asserts the two
known recorders are among what the glob returns, so the enumeration
cannot silently empty out. This is the check that makes the derivation
an improvement rather than a trade.

### Minor

**`SystemExit` from `record()` rather than a return value.**
`record()` returns `fired`, and `None` is a legitimate value of it, so
there is no in-band way to signal refusal without changing the contract
its callers (and the docstring) rely on. A hand-run script aborting is
the right shape and matches the module's own `sys.exit(main())` ending.
The pure half — `recording_problems` — carries the decision and is what
the tests exercise, so nothing important is tested through the exit.
No action.

**The suite now executes both recorders twice per test method.** `load`
re-imports on every call rather than caching, so five tests over two
recorders exec the modules several times. They are inert at import (the
`__main__` guard) and the whole file runs in 0.023s. Caching would be
premature. No action.

**The partial-crash case remains open.** Recorded in "Not verified" with
its reason: the runner's answer to the same question lives in
`trigger_eval.py`, contended by an open branch, and inventing a second
answer here would be the second-source-of-truth mistake this repo exists
to catch. **Deferred**, owner: `trigger_eval.py`'s crash handling.

**`one_owner` is blind to this entire diff.** Its `EXCLUDED` tuple skips
`tests/`, so the steady nine findings are not evidence that the two-copy
guard is acceptable — the suite's own twin-ness test is. Said in the
verification rather than left as an implication.

## Process findings

**ADR-0036 clause 2 is not satisfied.** A non-authoring reviewer must
re-execute the verification and record it on the pull request. This
review is self-authored, so the branch is deliberately **held out of the
merge queue** — no PR is opened, nothing is merged.

**Two candidate findings were checked and dropped before write-up.** The
two replay suites are twins and both already carry the zero-event guard,
so there was no divergence to report; and the claude recorder's
provenance omitting `harness` matches the eval result record, which has
no such field either. Both are recorded in the defect's Notes, because a
run that only reports what it found reads as if everything it looked at
was broken.

**The reproduction created files and removed them.** One fake recorder
directory, injected deliberately, deleted before commit, with `git
status --short` quoted as evidence. The empty-stream reproduction ran
against a *copy* in a temp tree specifically so a mistake could not
overwrite a real committed fixture — the files at risk are pinned eval
evidence.

## Fix / defer decisions

| Finding | Severity | Decision |
| --- | --- | --- |
| The guard is two copies | major | accepted; pinned identical by test |
| Empty-only refusal boundary | major | intended; a threshold would refuse real recordings |
| Derivation's vacuity failure mode | major | pinned by its own test |
| `SystemExit` from `record()` | minor | no action; pure half carries the decision |
| Recorders re-imported per test | minor | no action; inert and fast |
| Partial crash still ambiguous | minor | deferred — owner is `trigger_eval.py` |
| `one_owner` blind to `tests/` | minor | recorded, not claimed as coverage |
| ADR-0036 clause 2 unsatisfied | process | branch held out of the queue |
