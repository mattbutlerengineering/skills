---
stage: decompose
run: feature:reviewer-blind-cutoff
date: 2026-11-04
assumptions:
  - "Interview answers came from autorun-brief.md, prd.md and architecture.md, not a live review of the cut; the milestone boundaries below are the recommended ones, accepted as drafted."
  - "No tracker import or export: the brief's Tracker section says no issue seeds the run and no work-order issues are mirrored, so no item carries a `(tracker: #N)` reference and no WO ids are assigned."
  - "No docs/factory/decompose-lessons.jsonl exists in this tree, so step 3 read nothing and drafted as before."
  - "Items are cut test-first: each behaviour change is preceded by the item that writes its failing test, per the brief's 'Test first where behaviour is testable'."
  - "The `verdict` hook is invoked as `python3 reviewer_verdict.py <score>`, as architecture.md specifies, so no factory.py VERBS entry is added; the architecture names none and ADR-0123 does not call for one. Not a design gap."
---

# Breakdown: Withhold the pass cutoff from the implement-queue reviewer

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met.

## Milestone 1: the derivation exists and is tested — `python3 reviewer_verdict.py 7` prints a verdict line

Demonstrable on its own: nothing reads the module yet, but the one
threshold owner is written, pinned and callable.

- [ ] **Write the failing derivation test** — add `tests/test_reviewer_verdict.py` for `reviewer_verdict.derive(score)` and the CLI, before the module exists.
  - Accept: the test file asserts scores 0 through 10 give `flag` for 0 to 6 and `pass` for 7 to 10; 6.5 gives `flag`; a numeric string such as `"8"` derives like the number; missing, non-numeric, NaN, infinite, below 0, above 10 and bool all give an `error` problem string starting `reviewer-verdict:`; the CLI prints `reviewer-verdict: pass (score 8/10)` with exit 0, `reviewer-verdict: flag (score 5/10)` with exit 1, `reviewer-verdict: error (<reason>)` with exit 2, and exit 2 with a usage string on a wrong argument count. Running `python3 -m unittest tests.test_reviewer_verdict` (or the repo's equivalent) before the module is implemented fails on the missing module, and that failure is quoted in the Implement record.
  - Blocked by: —
- [ ] **Implement `reviewer_verdict.py`** — new root-only stdlib module holding `PASS_AT = 7`, `derive(score)` and the `python3 reviewer_verdict.py <score>` main that prints the comment's first line.
  - Accept: every assertion from the previous item passes; the module imports nothing outside the standard library and makes no git, network or model call; `PASS_AT = 7` is the only place the value is written in the module; `python3 one_owner.py` reports no new finding for it; `tests/test_dual_membership.py` still passes with its pinned set unchanged (root-only, not mirrored, ADR-0060).
  - Blocked by: **Write the failing derivation test**

## Milestone 2: the reviewer is blind and the orchestrator derives — the gate reads the score, not a verdict

Demonstrable on its own: the reviewer-facing text names no cutoff, the
queue profile names the hook, and the orchestrator's step 5 acts on the
derived verdict and posts the score.

- [ ] **Write the failing no-cutoff pin test** — extend `tests/test_reviewer_data_rule.py` (the existing reviewer-contract tests) with pins that the reviewer-facing contract states no cutoff and asks for no `verdict`, and that no skill or routine doc keeps the old "7 or more passes" wording.
  - Accept: the pin searches `skills/implement-queue/references/reviewer-contract.md`, `skills/implement-queue/SKILL.md`, `docs/factory/merge-train-routine.md` and `docs/factory/hourly-improvement-routine.md` for "7 or more" and "6 or less" and for the Output table's `verdict` row, and fails today on the contract's lines 30 and 31; the pin does not hold a second copy of the threshold value as an assertion on `reviewer_verdict.PASS_AT`. The failure is quoted in the Implement record.
  - Blocked by: —
- [ ] **Rewrite the reviewer contract** — in `skills/implement-queue/references/reviewer-contract.md`, drop the `verdict` row and the sentence naming where pass becomes flag; ask for `score`, `issues`, `assessment` only; reword line 59's "voids the verdict" to "voids the review"; keep the Scoring bands and the "caps it at 6" example as written.
  - Accept: the contract contains no "7 or more" or "6 or less" and no `verdict` output row for the scored reviewer; the Scoring table's bands and 0 to 10 scale are byte-for-byte unchanged; the specialist `pass`/`block` output line is unchanged; the Scoring band decision (kept, with the residue stated) already sits in `architecture.md` Decisions & alternatives and is not re-decided here; the no-cutoff pin test passes for this file.
  - Blocked by: **Write the failing no-cutoff pin test**
- [ ] **Add the `verdict` hook to the queue profile** — in `.claude/implement-queue.md`, name `python3 reviewer_verdict.py <score>` as the `verdict` hook, in the same form the `fast-path` hook is named.
  - Accept: the profile has a `verdict` hook section giving the command, the three exit codes (0 pass, 1 flag, 2 error) and the fail-closed meaning of exit 2 under `merge: auto`; no pass threshold value appears in the profile.
  - Blocked by: **Implement `reviewer_verdict.py`**
- [ ] **Rewrite the orchestrator's gate wording** — in `skills/implement-queue/SKILL.md`, add a `verdict` row to the hooks table; make step 4's "invalid verdict" and step 5's "Verdict" run the hook on the reviewer's `score` and act on its exit code only; make the verdict comment start with the line the hook printed verbatim; state that a `verdict` the reviewer returned itself is ignored whichever way it points; state that exit 2, a hook that did not run, or a missing hook is `error` (re-dispatch the reviewer once, then hold the PR for a human, no merge under `merge: auto`); update the merge-denial report line near step 5 to the derived verdict.
  - Accept: `SKILL.md` states no threshold value and no "7 or more" or "6 or less"; the hooks table lists `verdict` beside `fast-path`; the retry table in the contract still counts derived flags; the pin test passes for this file; the skill's frontmatter `description` is unchanged (`git diff` of the frontmatter block is empty).
  - Blocked by: **Rewrite the reviewer contract**, **Add the `verdict` hook to the queue profile**

## Milestone 3: the routines and docs agree, and the battery is green

Demonstrable on its own: a person reading the merge-train and hourly
routine protocols sees the derived verdict and the score line, and the
run's own gates pass.

- [ ] **Update the routine protocols** — in `docs/factory/merge-train-routine.md` §3 say a `flag` is the derived one and the gate comment's first line carries the score; in `docs/factory/hourly-improvement-routine.md` step 4 and the journal's `Gate:` line do the same, with the journal line carrying the score.
  - Accept: neither file states the old cutoff wording; both point to the orchestrator wording for the derivation instead of restating a threshold; the no-cutoff pin test passes over both files; `docs/research/desloppify-2026-10-31.md` and `docs/backlog.md` lines that record the old state or seeds are untouched, as architecture.md's reader list says.
  - Blocked by: **Rewrite the orchestrator's gate wording**
- [ ] **Register the new test and tool in the repo's lists** — add `test_reviewer_verdict.py` to `tests/README.md` beside `test_fast_path.py`, and add anything else a repo list requires for a new root module (found by running the battery, not guessed).
  - Accept: `python3 lint.py` and `python3 run_tests.py` report no unlisted-test or unlisted-tool finding for `reviewer_verdict.py` or `tests/test_reviewer_verdict.py`; if a list outside this run's files is required, the item stops and records it under Design gaps found.
  - Blocked by: **Implement `reviewer_verdict.py`**
- [ ] **Run the battery and record the reader-list check** — run the repo's battery from the worktree, and re-run the architecture's reader search to confirm no reader of the reviewer's `verdict` field was missed.
  - Accept: `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest` all exit 0, their summary lines quoted in the Implement record; a search of `skills/`, `docs/` (excluding history named in architecture.md), `factory/`, root tools and tests for `7 or more`, `6 or less` and `verdict` shows each remaining hit is either the derived verdict, Conductor's own `verdict` field (`conductor.py`, `conductor_flow.py`), the specialists' `pass`/`block` output, or history; `python3 factory_init.py update-manifest` is run only if a file under `factory/templates/**` or a mirrored root file was edited, and the Implement record says whether it was owed; no `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p` was run; no artifact states that the reviewer anchors.
  - Blocked by: **Update the routine protocols**, **Register the new test and tool in the repo's lists**

## Coverage

| PRD criterion | Item |
|---|---|
| 1 no threshold in reviewer-facing text | Write the failing no-cutoff pin test; Rewrite the reviewer contract |
| 2 no `verdict` requested | Rewrite the reviewer contract |
| 3 one threshold, unchanged value | Implement `reviewer_verdict.py` |
| 4 testable derivation, test first | Write the failing derivation test; Implement `reviewer_verdict.py` |
| 5 unusable score is `error`, no merge | Write the failing derivation test; Rewrite the orchestrator's gate wording |
| 6 reviewer's own `verdict` ignored | Rewrite the orchestrator's gate wording |
| 7 score and verdict in every comment | Implement `reviewer_verdict.py`; Rewrite the orchestrator's gate wording; Update the routine protocols |
| 8 every reader listed and updated | Run the battery and record the reader-list check |
| 9 no stale "7 or more passes" | Write the failing no-cutoff pin test; Rewrite the orchestrator's gate wording; Update the routine protocols |
| 10 docs and routines updated | Update the routine protocols |
| 11 rubric decision recorded | Rewrite the reviewer contract (decision already in architecture.md) |
| 12 no `description` change | Rewrite the orchestrator's gate wording |
| 13 battery, manifest regen if mirrored | Run the battery and record the reader-list check |
| 14 no paid run | Run the battery and record the reader-list check |
| 15 anchoring not claimed | Run the battery and record the reader-list check |

| Architecture component | Item |
|---|---|
| `reviewer_verdict.py` | Write the failing derivation test; Implement `reviewer_verdict.py` |
| Reviewer contract | Rewrite the reviewer contract |
| Orchestrator wording | Rewrite the orchestrator's gate wording |
| This repo's queue profile | Add the `verdict` hook to the queue profile |
| Routine protocols | Update the routine protocols |
| Tests | Write the failing derivation test; Write the failing no-cutoff pin test |

## Design gaps found

none.

## Notes

The two failing-test items have no blocker and can run in either order; every
behaviour-changing item is preceded by the item that writes its failing
test.
