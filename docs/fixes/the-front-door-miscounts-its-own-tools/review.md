---
stage: review
run: maintenance:the-front-door-miscounts-its-own-tools
date: 2026-08-28
assumptions: []
---

# Review — the front door miscounts its own tools

Scope: the diff on `agent/the-front-door-miscounts-its-own-tools` against
`origin/main` — `factory.py` (module docstring only) and
`tests/test_factory_cli.py` (one docstring sentence, one import, +5
tests).

## Correctness

**1 (minor, accepted) — the fix is documentary.** No verb, dispatch path
or table entry changed, and `python3 factory.py help` printed all
seventeen before and after. `defect.md` says so rather than dressing a
prose fix as a behavioural one. What justifies the run is that the pin
did not exist: the test file derived the verb *set* mechanically and
never read the sentence beside it, which is why the number could sit
three behind through several tool additions.

**2 (minor, accepted) — the pin is a regex over prose, which is a blunt
instrument.** Two things keep it honest.
`test_the_pin_catches_the_sentence_that_drifted` holds the original
sentence verbatim, so the pin cannot pass by matching nothing — the
failure mode that makes a checker worse than none.
`test_the_pin_leaves_ordinary_prose_alone` asserts three real sentences
from the file do not fire, so the cheapest way to satisfy it is not to
delete the explanation.

**3 (minor, accepted) — the pin covers only the router's docstring.** It
does not scan the test file's own prose, where the stale echo also lived
and was corrected by hand. Scanning the test file's source would match
the pin's own non-vacuity fixture, and scanning its docstrings would
match the class docstring that records what drifted. The narrower pin
guards the artifact readers orient from; the wider one would have to
carve out its own evidence, which is worse than not having it.

**4 (checked, not a finding) — the word survives twice in the test file
on purpose.** Once in the number-word alternation, which needs it, and
once in the class docstring recording that the count said fourteen
against a table of seventeen. Both are statements about the pin's
history, not counts of the table, and `defect.md`'s criterion was
corrected to say so rather than being satisfied by contorting the text.

## Design

**5 — removed rather than corrected.** Writing "Seventeen" would have
been one character of work and would have re-armed the same drift for the
eighteenth tool. The module's whole thesis is that it restates nothing,
and the replacement sentence names the owner (`VERBS`, and `factory.py
help`) instead of the number — so the next reader is pointed at something
that cannot go stale.

**6 — the pin lives in the test, not the router.** `factory.py` states
that any logic landing there is logic that stopped being testable where
it lives, and ADR-0054 already moved the calling-convention derivation
into the test for the same reason. The checker sits beside the existing
mechanical scan.

**7 — the sweep's negative results are in the artifact.** Three other
hand-typed counts in the root modules were checked and are accurate, so
`defect.md` says this is one stale count and not a class of them. A run
that reported the broader claim would have been asserting something its
own evidence contradicts.

## Security

Nothing. Docstring text and a test-local regex over strings. No IO, no
input surface, no dependency.

## Not addressed

**8 — counts outside the root Python modules.** `docs/**`, `skills/**`
and `factory/templates/**` were not enumerated. `verification.md` records
that as NOT RUN rather than letting criterion 5 read as a whole-repo
survey.

## Verdict

No critical or major findings. 1–3 and 5–7 are accepted as designed; 4 is
a recorded observation; 8 is an explicit coverage gap.
