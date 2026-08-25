---
stage: verify
run: maintenance:the-digest-says-what-it-could-read
date: 2026-08-25
assumptions:
  - "The regression centrepiece is the pair of end-to-end body assertions at the run_daily seam, not the compose_digest unit tests. The defect was measured on the posted body, so that is where it is pinned; the unit tests cover the rendering states more cheaply but would not have caught a run_daily that forgot to pass the fact."
---

# Verification: the digest states its own coverage

Commands run in the run worktree at `b7b625f`. Output quoted, not
summarised.

## C1 — a truncated listing no longer produces an identical digest

`defect.md` measured two bodies as character-for-character equal. Same
probe, same fakes, after the fix — the truncated body now carries a
sentence the complete one does not:

```
===== LISTING TRUNCATED
--- digest BODY (what #178 shows a human):
    ## Blueprint gate (wo:prd-approved)
    - #123 WO-0018 rejection mining — waiting 2d 0h

    Coverage: the issue listing came back at its full window, so issues
    outside it are not represented here — an empty section may mean
    unseen, not none.

    Updated daily by the gate digest (WO-0017); a passage lands a
    gate-latency row in docs/factory/costs.jsonl (ADR-0041).
```

The queue itself still renders and the digest still posts — truncation
reports and continues, as `cli.gh_read`'s contract prescribes.

**PASS.** Pinned by `test_a_full_window_says_so_in_the_posted_body`
(asserts the inequality directly, plus the note's presence and absence)
and `test_a_truncated_listing_is_stated_in_the_footer`.

## C2 — an unreadable timeline no longer renders as a readable one

The defect brief's second measurement, re-run against the fix:

```
timeline read fine, no gate event : '- #123 WO-0018 rejection mining'
timeline could not be read        : '- #123 WO-0018 rejection mining — age unknown (timeline unreadable)'
IDENTICAL LINE: False
```

Both halves matter. The readable-but-eventless line is byte-for-byte what
it was, so a history that simply held no arrival does not acquire a
failure's mark.

**PASS.** Pinned by
`test_an_unreadable_timeline_is_marked_in_the_posted_body`,
`test_an_unaged_item_says_why_when_its_history_was_unreadable`, and — for
the no-over-marking half — `test_an_aged_item_never_wears_the_mark`.

## C3 — the coverage parameter is required

```
    def test_the_coverage_fact_has_no_default(self):
        with self.assertRaises(TypeError):
            gate_digest.compose_digest([], "2026-07-22")
```

Watched fail before the change (the two-argument call succeeded), passes
after. **PASS.**

## C4 — the two tests that pinned the defect still pin their problem strings

`test_a_failing_timeline_still_posts_the_digest` and
`test_an_unparseable_timeline_still_posts_the_digest` had their body
assertions updated (logged as a deviation in `breakdown.md`). Their
`assertEqual(problems, [...])` assertions are unchanged byte-for-byte, so
the workflow-log channel is still pinned exactly where it was.
**PASS.**

## C5 — the payload mirror and manifest are in lockstep

```
$ python3 -B factory_init.py update-manifest
factory-init: 0 problem(s)
$ git status --short
 M factory/manifest.json
 M factory/templates/tools/factory/gate_digest.py
```

Exactly the two expected files. `python3 -B` deliberately: an unmerged
open PR (#320) fixes the manifest walk that would otherwise pin
`__pycache__/*.pyc`, and until it lands the caller has to remember.
**PASS.**

## C6 — the repo's own battery

```
$ python3 -m unittest discover tests
Ran 1350 tests in 13.908s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

**PASS.** Test count 1349 → 1350 net (six added, five of the additions
sharing the file with two rewritten assertions and one removed direct
tuple fixture).

## C7 — no new second owner

`python3 one_owner.py` on this branch and on a detached checkout of
`origin/main` (`622e7c0`), diffed:

```
7c7
< ... gate_digest.py:187 run_daily ...
> ... gate_digest.py:227 run_daily ...
9c9
< ... gate_digest.py:91 LIST_ARGS ...
> ... gate_digest.py:124 LIST_ARGS ...
```

9 problems before, 9 after; the only differences are line numbers on two
pre-existing findings that moved because lines were added above them. No
finding added, none removed. **PASS.**

## Not verified

- **The live daily run.** Nothing here observed the real gate-digest
  workflow posting to #178. The evidence is entirely against injected
  fakes, which is this tool's whole test strategy — but a fake is not a
  scheduled run, and the first real observation will be the next
  `gate-digest.yml` firing after merge.
- **The truncation branch in production.** This repo has ~150 issues
  against a 1000-entry window, so the footer sentence will not render
  here for a long time. It is verified by construction and by test, never
  by observation.
- **A first-run create vs. an edit.** Both probes and the new tests
  exercise the `issue create` path, because the fixtures start with no
  digest issue. The `issue edit` path carries the same `body` from the
  same `compose_digest` call, so the rendering cannot differ — but the
  edit path is not separately asserted for the new text.
- **The four adjacent readers.** `dashboard.py:158`, `dashboard.py:197`,
  `assembler.py:257`, `label_sync.py:111` still ignore `truncated`. Out
  of scope by design (`architecture.md §Out of scope`); nothing here
  measured whether their artifacts suffer the same way.

## Observation, not a finding

Detector A reads breakdown rows line-by-line and is fence-blind: a
deviation note in `breakdown.md` that quoted a literal digest line
starting `- #123 WO-0018 …` was parsed as a work-order row and failed
`gates.py` with *"work-order row WO-0018 cites no PRD id"*, which also
failed `test_a_clean_run_ends_with_the_exact_summary_line`. Worked around
by rewording the quote. Recorded rather than fixed — it is the same
fence-blindness detector C is already known to have, and changing a
detector's parse is not this run's scope.
