---
stage: verify
run: feature:seed-backlog
date: 2026-07-06
---

# Verification: seed backlog

## Summary

4/4 PRD success criteria pass; full test suite (146) and lint green on
`feat/seed-backlog`. Verdict: the convention, the grammar tooling, and the
skill wiring all demonstrably exist and conform.

## Criteria & evidence

### docs/backlog.md exists and every entry matches the grammar (lint-checkable)

- Check: `python3 lint.py` on the branch, plus parsing the real file through
  the public functions.
- Evidence:
  ```
  lint: 0 problem(s) across 15 skills
  entries: 7 problems: 0
  claimed: ['A durable home for idea seeds between ru']
  ```
- Result: PASS

### operate instructs appending retro seeds at run close

- Check: read `skills/operate/SKILL.md` step 6.
- Evidence:
  ```
  skills/operate/SKILL.md:41: `docs/backlog.md` as a well-formed entry per
  the protocol's seed-backlog
  ```
  (create-if-absent and never-rewrite phrasing present in the full step.)
- Result: PASS

### next lists unclaimed seeds when proposing what to start

- Check: read `skills/next/SKILL.md` steps 2 and 6 plus Rules.
- Evidence:
  ```
  :18 and if `docs/backlog.md` exists, list its unclaimed seeds and offer to
  :19 start from one (the protocol's seed-backlog section).
  :49 natural input to a fresh `idea` invocation, and if `docs/backlog.md`
  :59 - The backlog is advisory and read only in the two moments above
  ```
- Result: PASS

### Claiming records (claimed: <run>) in place; no skill treats backlog.md as orientation state

- Check: read `skills/idea/SKILL.md` claim instruction; grep every skill's
  backlog references; parse the real file's claimed entry.
- Evidence:
  ```
  skills/idea/SKILL.md:19-21: starting from a backlog seed, claim it in
  place — append `(claimed: <run-ref>)` to the seed's line
  next Rules :59: "The backlog is advisory and read only in the two moments
  above" — the only orientation-adjacent consumer states the boundary
  parse: claimed entry present (this run's own seed, feature:seed-backlog)
  ```
- Result: PASS

### Full suite and gates (breakdown acceptance criteria roll-up)

- Check: `perl -e 'alarm 240; exec @ARGV' python3 -m unittest discover
  tests` (alarm-guarded; see breakdown Notes on headless hangs).
- Evidence:
  ```
  Ran 146 tests in 4.064s

  OK
  ```
- Result: PASS

## Failures

None.

## Not verified

- Live routing behavior (does the *model* actually list seeds when invoking
  `next`?) — trigger/routing evals pin descriptions, which were deliberately
  untouched; behavioral prose is exercised by following the skill, first
  done in this very run. A routing-eval case for the backlog moments would
  be a future seed, not this run's criterion.
- omp-harness behavior of the new prose — out of scope for this feature run
  (the omp `skill://` protocol-doc gap is already a recorded backlog seed).
