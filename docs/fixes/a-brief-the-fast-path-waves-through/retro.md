---
stage: operate
run: maintenance:a-brief-the-fast-path-waves-through
date: 2026-11-04
users-observed: 0
signal-source: "none found. Looked at PR #1147 (one comment, the factory reviewer bot's; no human review, no reaction), issue #1146 (no comments, no reactions), the merge-train journal #930 (no comment since the merge) and PRs merged since 2026-11-04 (one, #1147). The only human on the record, the Owner, merged the PR and set the run's scope; that is authoring, not using the gate"
assumptions:
  - "Written the same day as the merge (2026-11-04, about an hour after it), against the let-it-breathe step. The brief's `operate:` section sets `minimum-signal: Ship written back as released (the PR merged)`, which exists, so the stage runs; the brief never supplies the count. Outcomes below record state and tests, not use."
  - "Outcomes are measured against the brief's Success criteria and `defect.md`'s work-item Accept lines, because a maintenance run has no `prd.md`."
  - "The factory reviewer bot's PR comment is not counted as a person. It is the repo's automated check on every PR."
---

# Retro: a brief edit no longer waves through the fast path

## Outcomes vs. intent

### A diff touching only an `autorun-brief.md` prints `fast-path: review (<path>)`, exit 1

- What happened: merged on main as `11a2bc9` (`release.md`, Write-back). In a fresh temp repo, run from this tree (main plus the write-back commit), a brief-only edit printed `fast-path: review (docs/fixes/y/autorun-brief.md)` with exit 1, and a neighbour `docs/features/x/breakdown.md` printed `fast-path: low-risk` with exit 0. That is the post-release check `release.md` left unrun. `verification.md` records the same, with the pre-fix `low-risk` exit 0 captured from the failing tests.
- Signal strength: unobserved. It is measured at the classifier (tests and a temp-repo run), but no real PR has met the gate since the merge, so nothing has landed in use.

### Other run artifacts stay `low-risk`; the profile's `gate_paths` equals `gate_globs()`

- What happened: the neighbour case above holds on main. The pin test `TestProfilePin` and the full suite were green on the PR head (3978 tests, 0 problems, in the reviewer bot's PR comment on #1147) and in `verification.md`.
- Signal strength: unobserved (tests only).

### Did the exposure ever bite? (the brief's reason for the fix)

- What happened: `defect.md` ("Does it bite today?") found no merged PR with a brief as its only changed file, and none merged through the train. Since the merge: journal #930's last comment (2026-11-04T00:38:59Z) is before it and names #1147 as a human-gate PR; no later comment exists. Of the PRs merged since 2026-11-04, only #1147 lists a brief.
- Signal strength: unobserved. Absence of a brief-only PR since the merge says nothing about the gate working, because no such PR has existed to route.

### The cost: a brief-only PR now needs a human merge

- What happened: not exercised. No resume's brief commit has opened a PR since the merge.
- Signal strength: unobserved.

## Open debt

None filed against this run. #1146 is the run's intake (created 2026-11-03T21:50:43Z, before the merge) and is closed by the PR; it counts toward nothing. The debt that stays visible lives in the backlog and in `review.md`:

- Root-level glob dialect for `**/autorun-brief.md` (`review.md`, first Minor, deferred; inert today).
- Case-sensitive basename match (`review.md`, second Minor, deferred; shared with `prd.md` and `architecture.md`).
- The `chore(release)` version bump per ADR-0095 is outstanding for the Owner (`release.md`, Write-back).

## Run retrospective

- Keep: **a brief that names its own evidence checks.** Capture was told to cite journal #930 or the PRs and to say plainly if none bit; it found 18 PRs listing a brief, one applicable (#1077), and showed that one did not merge through the train. That turned "latent" from a guess into a finding (`defect.md`).
- Keep: **red first against the pre-fix file.** Verify restored `fast_path.py` from `d5adfab^`, saw the new tests fail, then pass (`verification.md`); the pin test failing pre-fix proves it binds the two lists.
- Keep: **Review's probes of the matcher** (a directory named like the brief, near-miss basenames, trailing space) closed the correctness questions before Ship with exact outputs (`review.md`, Passes).
- Change: **the Full gate box was checked before a clean suite run existed.** `defect.md` Notes record three loaded runs that each failed one wall-clock test and a box already ticked; the orchestrator's later run at `a5d776e` (3978 tests, 0 problems) is what the Accept line needed. The tick and the evidence were out of order.
- Change: **Ship ran the launch-demo skill on a fix whose brief says "User-facing surface: None".** It rendered and committed a 300 KB `launch.mp4` (`1013dc4`) and the Owner reverted it before merge (`8808499`, `release.md` Release log 6 and 7).
- Change: **counts drift across artifacts.** `defect.md` says the red run was `failures=8`, `verification.md` observed 9 and explained why. A later reader sees two numbers for one red run.
- Stop: nothing.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| The Full gate work item was checked before a clean `run_tests.py` run was recorded | `defect.md` Work items (Full gate `[x]`) against Notes, where three loaded runs failed and the clean run is a later orchestrator entry | mechanical | the gates detector that reads run artifacts: a checked work item whose Accept line names `python3 run_tests.py` must have a `tests: N tests across M modules ... 0 problem(s)` line in the same artifact. A gap in that detector, not a new prose rule |
| Ship produced a launch video for a fix with no user-facing surface | `release.md` assumptions and Release log 6 and 7; `skills/ship/SKILL.md` step 4 acts on the verdict `SHIP` alone, and `launch_demo.py config` prints `config["when"]` without reading the run | mechanical | `launch_demo.py config` is the tool Ship asks and the skill forbids Ship from reading the config itself, so the carrier is that tool or the Ship step: it must consult the run (the brief's "User-facing surface" line, or `prd.md` `ux: not-applicable`) before answering `SHIP`. This needs an Owner decision on which signal is authoritative |
| Deferred minors left the classifier's three basenames and the profile's glob spelling unproven against a root-level path or a case-insensitive host | `review.md` Minor findings 1 and 2 | mechanical | `tests/test_fast_path.py`: one test that feeds each profile glob to the GitHub-side matcher's dialect once that matcher is settled (it is the open backlog seed on how implement-queue gets its changed-file list), and one test that pins the case decision for all three basenames |
| Two counts of one red run (`failures=8` and `failures=9`) | `defect.md` Notes against `verification.md` §Failing tests first | judgement | none: Verify already explained the difference in-line, and no check can tell a subTest recount from an error. The reader caught it |

## Idea seeds

Proposed only; the skill says to append them to `docs/backlog.md`, and they are appended there in a separate commit, not filed as issues:

- Make `launch_demo.py config`, or Ship step 4, consult the run's "User-facing surface: None" or `ux: not-applicable` before answering `SHIP`, so a fix with no surface does not render a launch video the Owner then reverts (from: maintenance:a-brief-the-fast-path-waves-through)
- A gates detector: a checked work item whose Accept line names `python3 run_tests.py` needs a recorded `tests: ... 0 problem(s)` line in the same artifact (from: maintenance:a-brief-the-fast-path-waves-through)
- Decide the glob dialect for `**/` entries in `gate_paths` against a root-level path, and pin the case-sensitivity of the gate basenames (`autorun-brief.md`, `prd.md`, `architecture.md`) in one test (from: maintenance:a-brief-the-fast-path-waves-through)
- After the next resume that edits a brief, check that its PR was routed `review` and not auto-merged, so the gate has a first real observation (from: maintenance:a-brief-the-fast-path-waves-through)

## Run complete

Closed 2026-11-04. Released as `11a2bc9` (#1147). The seeds above are the input to the next Idea-stage run.
