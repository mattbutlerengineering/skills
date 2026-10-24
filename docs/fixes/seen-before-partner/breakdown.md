---
stage: decompose
run: maintenance:seen-before-partner
date: 2026-10-24
assumptions:
  - "No live review of the cut. Milestones and size bands are the skill's own defaults, following docs/fixes/lessons-per-signal-seen/breakdown.md as the model of form: short labels (P1, P2, ...), one item per sitting, each milestone demonstrable."
  - "Test-first ordering: the implementation item is blocked by the tests item that pins it, and that item's Accept says its cases fail against the tree before the implementation lands. The defect's reproduction (defect.md, case 1) becomes the regression test."
  - "No work-order ids and no tracker markers: detectors C and I scan every markdown file. No work order issue is created. The issue closes from the PR body, not from this file."
  - "All tests go in tests/test_decompose_lessons.py through the public interface (update, fold, pairs) with the module's existing record and replan helpers. The two new helpers, _partners and _spent, are private and pure; they are covered through fold and pairs, and one direct case each pins the set they return."
  - "No permanent test asserts any path is unchanged against main (autorun-brief.md constraint). Scope checks (no skill edit, no plugin.json edit, pin still 55) are one-off commands in the final item."
  - "ADR-0117, the ADR-0116 status line and the ADR index row were written by Architect and already exist; the ADR item is therefore a check that they agree with the final code, not a write."
  - "architecture.md accepts the deviation from the brief's literal fold-on-use rule (the Owner accepted it in-session); it is built as designed: seen stays measured, only the pairing skip changes. No design gap was found, so nothing is routed back to Architect."
  - "The recorded behaviour changes in architecture.md (the sources difference when an earlier clean run arrives later, the stranded pair of an ADR-0116-era file) are documented decisions and get no test beyond the required ones."
---

# Breakdown: seen-before-partner

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. The implementation item is blocked by the tests
item that pins it. All tests go in `tests/test_decompose_lessons.py` unless
an item says otherwise.

## Milestone 1: a hit run seen before its clean partner still pairs

When this milestone is done, `update` over a hit run alone and then over the
hit run plus its clean partner derives the same lessons as one `update` over
both, and a repeated `update` writes nothing.

- [x] **P1 Seen-before-partner tests** — the defect's reproduction and the architecture's required cases — size:M
  - Accept: the module holds these cases through the public interface, each asserting exact values. (1) The defect's case 1: a ledger-bearing file is written by update 1 over H (`feature:h`, re-plan 2 of 10, observed) plus two maintenance runs, then update 2 over H and C (`feature:c`, 0 of 8, observed) prints the line `decompose-lessons: ADD replan/feature/added`, and the resulting file is byte-identical to the single-update control over the same four runs. (2) A repeat `update` over the same records ends with exactly `decompose-lessons: unchanged` and leaves the file byte-identical, with no second vote on any lesson. (3) Clean-first order: update 1 over C, then update 2 over H and C, still derives `replan/feature/added`. (4) A seen hit run with a seen partner stays skipped: a lesson dropped at 0 is not re-derived by `fold` when both runs are already in `seen`, and a clean run arriving later, even first in record order, does not re-open the pair. (5) An unpaired hit run that votes still pairs later: a treated hit run seen while a lesson exists downvotes it as before, and when its clean partner arrives in a later `update` the pair is derived. (6) `_partners` returns the clean runs (count 0) of one kind and label on a signal in record order, and `_spent` returns only the seen keys of hit runs that are seen and have a seen partner, so a seen hit run with no seen partner is absent from the set. The existing `pairs` tests pass unchanged. No case asserts any path is unchanged against main. Run against the tree before P2, cases 1, 5 and 6 fail.
  - Blocked by: —
- [ ] **P2 Partner lookup and spent hit runs** — `_partners`, `_spent`, and `fold`'s skip in `decompose_lessons.py` — size:M
  - Accept: the P1 tests pass and every earlier test still passes. `_partners(records, field, num, run_kind, label)` is the one place the partner predicate lives and `pairs` takes its first element for the exemplar, as it takes the first clean run today; `_spent(records, seen)` is pure and returns a set of seen keys. `fold` calls `pairs(records, skip=_spent(records, set(seen)))` in place of `pairs(records, skip=set(seen))`; the returned `seen` is still the input plus every measured key (`_measured` unchanged), so the header is byte-identical to what the old rule writes for the same records. `pairs` keeps its signature and `skip` meaning; `votes` and `_ballot` are untouched. No new import, no new constant, no new output line, no new problem string, and `NO_PAIR`, `LABEL` and `MAX_LESSONS_BYTES` are unchanged.
  - Blocked by: P1 Seen-before-partner tests

## Milestone 2: the decision and the whole repo agree

When this milestone is done, the ADR trail matches the code and every check passes.

- [ ] **P3 ADR trail check** — ADR-0117, ADR-0116's status line and the index rows agree with the code — size:S
  - Accept: ADR-0117 is `provisional` and states the final behaviour (the skip is decided from `seen` plus a seen partner; `seen` itself unchanged); ADR-0116's status line reads `superseded in part by ADR-0117 (the pairing skip rule; provisional)`; the docs/adr/README.md rows for 0116 and 0117 match their files' status lines. Where Implement changed a name or rule from architecture.md, the ADR and architecture.md are corrected in the same commit and the change is logged in Notes. `python3 kb.py drift` stays at 0 problems.
  - Blocked by: P2 Partner lookup and spent hit runs
- [ ] **P4 Whole-repo verify** — full suite and one-off scope checks — size:S
  - Accept: `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift` and `python3 gates.py && python3 gates.py --selftest` all pass. One-off checks, run and reported but not kept as tests: `git diff main...HEAD --name-only` lists no file under `skills/` and not `.claude-plugin/plugin.json`; `tests/test_dual_membership.py` still pins 55 pairs; no `docs/factory/decompose-lessons.jsonl` exists in the tree; `decompose_lessons.py` gains no import line. `git status --porcelain` prints nothing after the commit.
  - Blocked by: P3 ADR trail check

## Design gaps found

none.

## Notes

Release: no skill text changes, so no wave release PR is owed by this run;
if Implement finds the skill must change, that is a skill change, recorded
here as an Owner follow-up (ADR-0095), never a `plugin.json` edit on this
branch.
