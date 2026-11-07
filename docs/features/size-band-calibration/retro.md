---
stage: operate
run: feature:size-band-calibration
date: 2026-11-07
users-observed: 0
signal-source: "Live `python3 size_band_calibration.py` from /tmp/dc-retro (HEAD = origin/main) on 2026-11-07; `git log --since=2026-10-21 -- size_band_calibration.py tests/test_size_band_calibration.py` (empty); `gh issue list --state all --search 'size band'` and `'size-band-calibration'` (only #987, #1048, #1071 touch it; none is a person using it); `grep -rn size_band_calibration docs/` outside the run dir (citations in docs/features/decompose-lessons, decompose-eval-suite, eval-trends); `wc -l docs/factory/costs.jsonl` (216); plugin-evals/records/2026-10-26-2.json; docs/adr/0112 status."
---

# Retro: Release: Calibrate S/M/L size bands from past error

## Outcomes vs. intent

### The tool prints a band's interval only when n meets the minimum and otherwise says why not, every number computed from ledger rows (idea.md "Success in one sentence")
- What happened: The refusal half works live. 2026-11-07 output, quoted verbatim:
  ```
  size-band-calibration: excluded 177 owner-session:unmetered row(s) — cost never recorded, none estimated
  size-band-calibration: excluded 32 gate-latency row(s) — waits, not spend
  size-band-calibration: band S — refused: n 2 work order(s) is below the minimum of 5, no interval printed; cost $5.908 total; re-plan 4/8 over 1 run(s) (0 unmeasurable)
  size-band-calibration: band M — no metered work order joins this band; re-plan unmeasurable
  size-band-calibration: band L — no metered work order joins this band; re-plan unmeasurable
  size-band-calibration: 2 work order(s), 0 problem(s)
  ```
  No band calibrates. S refuses at n 2 (floor 5), M and L are empty. The interval half has never run on real data: no band has ever met the floor (verification.md "Not verified": "A live interval"; still true today). Not a bug, the designed fail-closed state.
- Signal strength: measured (tool output). That an interval is ever produced is unobserved.

### Metering puts work-item cost in the ledger with a joinable size band, so calibration has rows to read (PRD story 1, success criterion 1; idea.md "Meter first")
- What happened: Join by work-order token is built and tested, but metering volume did not follow. `docs/factory/costs.jsonl` is 216 rows today (`wc -l`); the tool excludes 177 + 32 = 209, leaving 7 rows [INFERENCE: arithmetic on the two printed exclusions, not a separate count]. idea.md measured 7 cost-bearing rows of 184 on 2026-10-16. The metered count is the same 7, while unmetered owner-session rows went 145 -> 177. The run added no metering source: it is a reader, and owner-session work stays invisible by Owner decision.
- Signal strength: measured

### Size inflation is visible: band misses print beside cost and re-plan rate, never 0 for unmeasurable (PRD story 4)
- What happened: S prints `cost $5.908 total; re-plan 4/8 over 1 run(s) (0 unmeasurable)`; M and L print `re-plan unmeasurable`, not 0. Format exists and is exercised live for one band only. Whether it deters inflation is unobserved: no Decompose run since release read it.
- Signal strength: unobserved (that it guards inflation); measured (that it prints)

### Downstream steps #988 and #989 use the output or fail on it (prd.md open question 6, the brief's minimum signal)
- What happened: Neither used a number. #988 shipped (#1050, docs/features/decompose-lessons) and explicitly defers band-miss pairs "until a band clears the n >= 5 floor in `size_band_calibration.py`" (prd.md:48, :130); it cites the tool as a blocker, not as an input. docs/features/decompose-eval-suite and eval-trends mention it in briefs/ideas; the only other consumer text is a verification run of `decompose_grade.py` against this run's breakdown. No breakdown.md or docs/fixes/* dated after 2026-10-20 cites band calibration when sizing (grep over docs/features/*/breakdown.md and docs/fixes/ found none). No Owner or Decompose run is observed reading the tool's output to size work.
- Signal strength: unobserved

### Post-release stability
- What happened: `git log --oneline --since=2026-10-21 -- size_band_calibration.py tests/test_size_band_calibration.py` prints nothing: no change, fix or complaint in 17 days. Silence is consistent with no use, not evidence of correctness.
- Signal strength: unobserved

## Open debt

The run's own items, listed and counted toward nothing:

- ADR-0112 is still `provisional` (docs/adr/0112-*.md `Status: provisional`); release.md Owner step 2 ("Confirm or amend") not done.
- Launch brief not produced (release.md Outcome; `launch_demo.py config` printed SHIP). No `/idea-to-prod:launch-demo` run exists for PR #1047.
- Deferred from Review (review.md), none filed as an issue (`gh issue list --search` finds no chore citing them):
  - Reject non-finite `cost` upstream in `cost_ledger.line_problems`; the tool only guards its own read (fix b4e181b). Touches a mirrored seam, every ledger reader and the manifest.
  - A work-order token under the same size in two runs sums into one sample (review.md minor, architecture.md defines ambiguity as conflicting sizes only).
  - Minors left as is: unreachable `else 0.0` in `cost_mean`; non-finite guard scope (dispatched rows) unpinned.
- release.md is internally inconsistent on main: front matter says `outcome: released` / `released-at: 2026-10-20`, while the body still reads "Prepared and stopped" and "Nothing is released until the Owner merges". #1048 (closed 2026-10-21, "record the #1040 and #1047 releases") patched the front matter only.
- AGENTS.md:103 says `plugin-evals/decompose/` "is authored and has never been run". Stale: `plugin-evals/records/2026-10-26-2.json` is a with-without run, `tagFilters: ["decompose"]`, costUsd 1.433, startedAt 2026-10-26T02:55Z. This is the neighbouring #989 run's claim, not this run's, but the same roster text carries this tool's bullet (AGENTS.md:80).

## Run retrospective
- Keep: the fail-closed contract (refuse with n and minimum, a distinct string for an empty band, `unmeasurable` never 0). It is the reason today's output is honest at n 2. Keep the 35-mutant sweep in Review: it found the one major (NaN/Infinity cost printed as a figure, exit 0) that tests had missed.
- Change: sequencing. The PRD already flagged "will metering ever produce volume" and left it to Operate, and the idea said "meter first", but the run shipped only the reader. Seven metered rows in October and seven in November says the bet's binding constraint was upstream of this tool. A run that ships a calibrator should either carry its feed or record the feed as a named blocker issue at Ship. Also: write the release.md body at the merge write-back, not just the front matter (see #1048).
- Stop: filing nothing for Review's deferred items. They sit in review.md prose and no issue cites them; the cross-run pattern (#1062/#1063) is to file run debt as `type:chore` issues.

## Environment
| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| Non-finite `cost` (NaN/Infinity) printed as a figure with `0 problem(s)`, exit 0 | review.md Major; fixed b4e181b | mechanical | `cost_ledger.line_problems` rejecting non-finite, covered by its existing test module (the deferred upstream fix) |
| Floor-config problem path untested; mutants survived the module's tests | review.md Minor; fixed 9d1cb6d | mechanical | `tests/test_size_band_calibration.py` mutation sweep (already the carrier; pinned) |
| Same-size duplicate work-order token across runs counted as one sample | review.md Minor, deferred | judgement | the review skill's join/ambiguity pass; `knowledge_plane.work_orders` duplicate rule (detector C) already fails repo-wide duplicates |
| `one_owner.py` flagged a second `("S","M","L")` against `factory_config.SIZES` and `_unusable` re-reading ledger keys `cost`/`wo` | breakdown.md Notes (S10), fixed in code | mechanical | `one_owner.py` (caught it; already the carrier) |
| `breakdown_files` raises on an unreadable file, so the tool had to bypass it to keep S8's labelled-problem rule | breakdown.md Notes (S8) | judgement | the Architect/Decompose read of shared helpers; no mechanical carrier named |
| S1 commit red by design (test module fails on import until S2) | breakdown.md Notes (S1) | judgement | none: expected RED-first shape, record only |
| release.md body says "Prepared" while front matter says released | release.md (this run); #1048 patched front matter only | mechanical | `gates.py` detector on release.md front-matter vs. body (not existing for this pair), else `lint.py`; until then a Ship write-back step |
| AGENTS.md "never been run" claim outlived the 2026-10-26 decompose eval record | AGENTS.md:103 vs plugin-evals/records/2026-10-26-2.json | mechanical | `kb.py drift` (checks AGENTS.md against CLAUDE.md; #1071 shows it already drifted once) |

## Idea seeds
- Meter work-item cost at Conductor batch close so M and L ever gain rows; target: 5 joined work orders in one band, measured by this tool's own output.
- A one-line `size_band_calibration.py` count in `eval_trends.py` or the factory dashboard so "n per band vs floor 5" is seen without running the tool.
- File the review.md deferrals (upstream non-finite cost reject; same-size duplicate token) as `type:chore` issues at Ship, with a gate on release.md that lists unfiled deferred items.
- Check release.md write-back mechanically: body and front matter agree on prepared/released after the merge step.
- Re-run this retro when any band reaches n >= 5, or at the first Decompose run that cites an interval when sizing; until then the bet is unmeasured, not failed.

## Run complete
2026-11-07. Verdict: the tool is shipped, quiet and honest (refuses everywhere, no band calibrates, 0 users observed); the bet that metered volume would follow is not met, as the feed was out of this run's scope.
