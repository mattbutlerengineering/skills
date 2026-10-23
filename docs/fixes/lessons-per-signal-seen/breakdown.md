---
stage: decompose
run: maintenance:lessons-per-signal-seen
date: 2026-10-23
assumptions:
  - "No live review of the cut. Milestones and size bands are the skill's own defaults, following docs/features/decompose-lessons/breakdown.md as the model of form: short labels (S1, S2, ...), one item per sitting, each milestone demonstrable."
  - "Test-first ordering: each implementation item is blocked by a tests item whose Accept says its cases fail against the tree before the implementation lands. The lost-signal reproduction (defect.md, repro 1) becomes the regression test in S1."
  - "No work-order ids and no tracker markers: detectors C and I scan every markdown file. The issue closes from the PR body, not from this file."
  - "All tests go in tests/test_decompose_lessons.py through the public interface with the module's existing record and replan helpers; the existing per-run seen fixtures are rewritten in the item that changes the shape, not left red."
  - "No permanent test asserts any path is unchanged against main (autorun-brief.md constraint). Scope checks (no skill edit, no plugin.json edit, pin still 55) are one-off commands in the final item."
  - "Architecture.md's decisions are specific enough to write acceptance lines from; no design gap was found, so nothing is routed back to Architect."
---

# Breakdown: lessons-per-signal-seen

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it. All tests go in `tests/test_decompose_lessons.py`
unless an item says otherwise.

## Milestone 1: a signal that matures later is kept

When this milestone is done, `update` run between Implement and Review, then
again after Review, derives and votes the review lesson, and `seen` holds
one `<signal>:<run ref>` entry per measured (signal, run).

- [ ] **S1 Per-signal seen tests** — rewrite the seen fixtures to the new entry form and add the lost-signal regression — size:M
  - Accept: the module holds these cases, each asserting exact values. The defect's reproduction 1 as a test: records H (re-plan hit, gap hit), C (clean), R (clean re-plan, review unmeasurable) then R with a review finding naming an item; `update` after the first measure and again after the second yields the review lesson, equal to the single `update` after Review (control B). A run unmeasurable for a signal is not in `seen` for it and a measured clean run is. `pairs` skips a hit run only when its key for the pair's signal is in `skip`. `votes` refuses a ballot only when the key for the lesson's signal is in `seen`, so a run seen for re-plan can still vote on a review lesson; a run seen for every signal its kind's lessons use costs no git call, asserted by a recording fake runner. `fold` returns the sorted keys of every measured (signal, run) and a second fold over the same records changes nothing; a lesson dropped at 0 is not re-added. `serialize` writes sorted, de-duplicated keys; the header stays line 1 `{"seen": [...]}` and lesson lines are byte-identical to today's. The existing header literals, the `jsonl` helper, the cast helper and the every-complete-run test move to the new form. Run against the tree before S2, the new cases fail.
  - Blocked by: —
- [ ] **S2 Per-signal seen** — `seen_key`, the skip in `pairs`, the ballot in `votes`, the measured rule in `fold`, `serialize` — size:M
  - Accept: the S1 tests pass and every earlier test still passes. One `seen_key(signal, ref)` builds every key and the signal names come from `decompose_signals.SIGNALS`, not a retyped list. `fold`'s seen is the input plus every (signal, run) with `_hit_label` not None, replacing the complete, hit-run and voter unions. The module imports nothing new.
  - Blocked by: S1 Per-signal seen tests

## Milestone 2: an old or oversize file is refused, a zero-item pool says so

When this milestone is done, `load` refuses the old per-run header and a file above the bound with labelled problems, and the comparison line no longer calls an undefined rate "not higher".

- [ ] **S3 Header and bound tests** — cases for header validation, the old-shape refusal and the size bound — size:M
  - Accept: the module holds these cases. A header of new keys loads and round-trips byte-identically. A header entry of the old per-run shape (`feature:c`, `product`) gives exactly `decompose-lessons: <shown> line 1: seen entry '<entry>' is the old per-run shape (ADR-0116); delete the file and run update to rebuild it` and nothing else is returned. A string entry that is neither shape gives `decompose-lessons: <shown> line 1: seen entry '<first 60 characters>' is not <signal>:<run ref>`. A non-list or non-string header still gives `expected the seen header`. `update` and the read-only report over an old-shape file return that problem, exit 1 through `main`, and write nothing. A file one byte above `MAX_LESSONS_BYTES` gives exactly `decompose-lessons: <shown> is <size> bytes, above the 1048576-byte bound; not read`, a file at the bound loads, a missing file still loads as empty, and the read is never attempted above the bound (asserted by patching `cli.read_file` to raise). Before S4 the cases fail.
  - Blocked by: S2 Per-signal seen
- [ ] **S4 Header and bound** — `_parse` entry validation and `MAX_LESSONS_BYTES` in `load` — size:S
  - Accept: the S3 tests pass and every earlier test still passes. `MAX_LESSONS_BYTES = 1024 * 1024` sits beside `LESSONS_PATH` with a comment carrying the measured sizes (architecture.md); the stat guard follows `eval_trends._refusal`'s shape and leaves a missing file or a stat error to `cli.read_file`. The old-shape test reuses the module's run-ref pattern, not a second copy.
  - Blocked by: S3 Header and bound tests
- [ ] **S5 Zero-item pool tests** — cases for both zero-item pools in `compare` — size:S
  - Accept: the module holds these cases through `compare` and `main`. A treated pool of 5 runs and 0 items against an untreated 1/20 gives the line ending `descriptive, no comparison: rate undefined for the treated pool (0 items)`. A treated 5/40 against an untreated 0/0 over 1 run ends `... for the untreated pool (0 items)`. Both zero ends `... for both pools (0 items)`. A pool with items still ends `treated higher` or `treated not higher` exactly as before, and the below-floor line is unchanged. Exit stays 0. Before S6 the cases fail.
  - Blocked by: S2 Per-signal seen
- [ ] **S6 Zero-item pool** — the no-comparison tails in `compare` — size:S
  - Accept: the S5 tests pass and every earlier test still passes. The stale `lean:` comment at the old guard is gone with the guard.
  - Blocked by: S5 Zero-item pool tests

## Milestone 3: the decision and the docs agree with the code

When this milestone is done, no live document describes the per-run header as current, and the ADR trail is consistent.

- [ ] **S7 Doc lines that quote the old shape** — note ADR-0116 in the shipped feature architecture and confirm the live docs — size:S
  - Accept: `docs/features/decompose-lessons/architecture.md` gains a dated one-line note at its Data model sketch and its ADRs entry saying the line-1 entries are `<signal>:<run ref>` from ADR-0116; its other lines are not rewritten. `review.md`, `release.md`, `verification.md` and that run's `breakdown.md` are untouched. `CLAUDE.md` and `CONTEXT.md` are checked: neither names the header shape, so neither is edited, and the result is logged in Notes. `skills/decompose/SKILL.md` is not edited and the phrase pin near the end of the skill tests still passes. `python3 gates.py`, `python3 lint.py` and `python3 kb.py drift` stay at 0 problems.
  - Blocked by: S4 Header and bound, S6 Zero-item pool
- [ ] **S8 ADR trail check** — ADR-0116's status, ADR-0113's status line and the index rows agree — size:S
  - Accept: ADR-0116 is `provisional`, ADR-0113's status line reads `superseded in part by ADR-0116 (...)` and both index rows match their files' status lines. ADR-0116 states the code's final strings and constant; where Implement changed one, the ADR and architecture.md are corrected in the same commit and the change is logged in Notes. `python3 kb.py drift` stays at 0 problems.
  - Blocked by: S4 Header and bound, S6 Zero-item pool

## Milestone 4: the whole repo agrees

- [ ] **S9 Whole-repo verify** — full suite and one-off scope checks — size:S
  - Accept: `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift` and `python3 gates.py && python3 gates.py --selftest` all pass. One-off checks, run and reported but not kept as tests: `git diff main...HEAD --name-only` lists no file under `skills/` and not `.claude-plugin/plugin.json`; `tests/test_dual_membership.py` still pins 55 pairs; no `docs/factory/decompose-lessons.jsonl` exists in the tree; `grep -n "MAX_LESSONS_BYTES" decompose_lessons.py` shows one definition. `git status --porcelain` prints nothing after the commit.
  - Blocked by: S7 Doc lines that quote the old shape, S8 ADR trail check

## Design gaps found

none.

## Notes

Release: no skill text changes, so no wave release PR is owed by this run;
if Implement finds the skill must change, that is a skill change, recorded
here as an Owner follow-up (ADR-0095), never a `plugin.json` edit on this
branch.
