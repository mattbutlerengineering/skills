---
stage: operate
run: maintenance:one-fence-rule
date: 2026-10-10
assumptions:
  - "Written the same day as the release, against the skill's let-it-breathe step. The condition was latent: an awk scan of every tracked architecture.md found zero occurrences, and no PR body is known to have tripped the validator. So usage will not produce any further outcome signal. The only outcome this run can have is the one measured at release: the condition is gone. Waiting would only have delayed the run's close. The owner's /loop goal was 'complete all of this work'."
  - "Outcomes are measured against defect.md's Success criteria, because a maintenance run has no prd.md or idea.md."
---

# Retro: one fence rule

## Outcomes vs. intent

### Both repros produce no problem

- What happened: D returns `[]` on the four-backtick and nested-`~~~`
  repros, and `_unquoted` drops the quoted `Closes` line. The three
  red-first cases failed on the old code and pass on the new
  (`verification.md`).
- Signal strength: measured.

### One definition of the fence rule

- What happened: on `origin/main` at `94bb43e`, `FENCE_OPEN` and
  `FENCE_CLOSE` are defined only in `knowledge_plane.py` and its payload
  twin. `ARCH_FENCE` and `validator.FENCES` are gone. Re-checked by
  `git grep` while writing this retro.
- Signal strength: measured.

### Existing tests pass unchanged

- What happened: `unittest discover` 2106 OK, with lint, gates and the
  gates selftest all green. No pre-existing test was edited
  (`release.md`, Pre-flight).
- Signal strength: measured.

### Real-world effect

- What happened: none observable, by construction. The defect never
  occurred in this tree, so the payoff is that it now cannot occur, in
  this repo and in every stamped repo on its next `factory_init` update.
- Signal strength: none yet. The first false-red D gate that does not
  happen is not observable.

## Run retrospective

- Keep: **red-first at the new interface.** Each of the three regression
  cases was watched fail on the old code before the change landed
  (`verification.md`). That is what makes "fixed" a measurement rather
  than a claim.
- Keep: **the decompose soft gate as a second check on the review that
  seeded the run.** Backfilling `defect.md` meant checking for in-flight
  and prior work. That check found that the deepen report's top two
  candidates were already recorded decisions in fix-run artifacts, and
  the run switched to the candidate that held up.
- Keep: **detector M on the run's own brief.** It failed the first draft
  of `defect.md` because a repro's outer fence closed early under
  CommonMark. That is the exact rule this run made universal, catching
  the author.
- Change: **the deepen review rated candidates before checking fix-run
  records.** Candidates #1 and #2 were rated on ADRs alone. Each had a
  reviewed decision in `docs/fixes/` or `docs/features/` that a grep
  would have found.
- Change: **architecture's "accepted behaviour change" list was written
  from the repros, not from a diff of the two rules.** It named the
  validator's change and missed two changes to D (`review.md`, third
  minor).
- Stop: nothing. The run was small, and every artifact was read by a
  later stage.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| The deepen report rated two candidates on divergences that fix-run artifacts already recorded as deliberate | `defect.md` §Notes; deepen report revision 2026-10-10 | judgement | `skills/deepen/SKILL.md` step 1, "Read the repo's own language and decisions first": name run artifacts (`release.md` follow-ups, `review.md` decisions) beside ADRs |
| The moved comment kept a clause ("an unclosed fence is reported") that is false in its new home | `review.md` §"the moved comment told a lie in its new home" | judgement | `skills/implement/SKILL.md`: when a move lands code in a seam module, re-read every moved comment against the new module |
| knowledge_plane's docstring ownership list omitted the fence rule after the move | `review.md` §"knowledge_plane's stated ownership list omitted its new fact" | judgement | same `skills/implement/SKILL.md` line. The repo's stated-convention audit technique already finds these lists going stale, but only when someone runs it |
| Architecture listed one behaviour change and missed two in D | `review.md` §"D's fence handling changed beyond the two repros" | judgement | `skills/architect/SKILL.md`: when one rule replaces another, list behaviour changes from a diff of the two rules, not from the repros |
| A repro fence in the first `defect.md` draft closed early | this retro, Run retrospective; caught before commit | mechanical | already caught by gates detector M; no new carrier |

## Idea seeds

Appended to `docs/backlog.md`:

- The deepen skill checks only ADRs for recorded decisions (it rated two candidates on divergences that fix-run artifacts had already settled)
- `dashboard._timeline` turns an unreadable timeline into "no age"
- `docs/factory/corrections.jsonl` has no producer
- Detectors C and I, and D's citation scan, still read fenced text as claims
- `protocol.read_frontmatter` and `gates._skip_frontmatter` disagree on a `--- ` fence with trailing whitespace

## Run complete

Closed 2026-10-10. Released as `55d5eae` (#658), with the release record
in #661. The seeds above are the input to the next runs.
