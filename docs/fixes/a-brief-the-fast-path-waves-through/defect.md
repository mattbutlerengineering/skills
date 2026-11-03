---
stage: capture
run: maintenance:a-brief-the-fast-path-waves-through
date: 2026-11-03
re-entry: implement
intake: #1146
origin: docs/backlog.md line 143 seed (from feature:faster-sdlc), review finding #6 of that run
assumptions: ["re-entry: implement, taken from the brief's reading (the orchestrator's, not an Owner answer) under the skill's rule that a scoped fix with no design decisions re-enters at Implement. Owner decision 1 fixes the shape (every autorun-brief.md at any depth is a gate path) and the change sits inside the existing gate list, so Capture found no design question to send to Architect", "Capture: the in-flight check ran with git only; gh pr list reported no open pull request, so the review surface was reachable and the result is a clean 'nothing matched', not a check that could not run"]
---

# Defect: a brief edit waves through the fast path

Intake: #1146, "fast-path: an autorun-brief.md edit classifies low-risk and
can auto-merge" (`type:defect`, filed 2026-11-03T21:50:43Z).

## Defect (or Condition)

`fast_path.py` (ADR-0096, as amended by ADR-0121) classifies a diff that
touches only `docs/features/<slug>/autorun-brief.md` or
`docs/fixes/<slug>/autorun-brief.md` as `fast-path: low-risk`, exit 0.
Expected: `fast-path: review (<path>)`, exit 1, a human merge.

Why it matters (issue body, quoted): "An autorun resume follows the brief
as its interview answers (`skills/autorun/SKILL.md`, steps 1 and 5). The
brief holds the run's release authorization, its `operate:` section and
its `stop-after:` line. So a docs-only PR could switch a run from
'prepare and stop' to an authorized release without human review." Under
`.claude/implement-queue.md`'s `merge: auto`, a low-risk PR merges on a
green `check` alone.

## Reproduction / Evidence

Reproduced for real in a temp git repo (base `main` holding
`docs/features/x/autorun-brief.md`, `docs/fixes/y/autorun-brief.md` and
`docs/features/x/breakdown.md`; one branch per edit), running the
worktree's classifier, `python3 fast_path.py main <branch>`:

    edit docs/features/x/autorun-brief.md
    fast-path: low-risk
    exit 0
    edit docs/fixes/y/autorun-brief.md
    fast-path: low-risk
    exit 0
    edit docs/features/x/breakdown.md (the neighbour, correctly low-risk)
    fast-path: low-risk
    exit 0

The profile has no matching entry. Rendering `fast_path.gate_globs()` and
filtering for `brief` returns `[]`; testing every glob against
`docs/features/x/autorun-brief.md` with `fnmatch` returns `[]`;
`.claude/implement-queue.md` contains no line with `brief`.

Both brief edits are the failing-first cases for the regression tests.

## Root-cause hypothesis

Hypothesis, not a finding: ADR-0121's instruction-doc survey excluded
`docs/features/**` and `docs/fixes/**` wholesale as "outputs of stages, not
instructions". The survey was right for most files and wrong for the one
file autorun obeys. Review finding #6 of the faster-sdlc run
(`docs/features/faster-sdlc/review.md`, "Minor (new, re-review 2)")
names exactly this, deferred as "narrower exposure, an Owner-authored
file", and says the fix is a `**/autorun-brief.md` entry in the profile
and `GATE_NAMES`, "which the pin test then keeps in step". The code
agrees: `is_gate_path` matches `GATE_FILES`, `GATE_PREFIXES` and the
basenames in `GATE_NAMES` (`prd.md`, `architecture.md`); the brief is in
none.

## Blast radius

- Who: any run whose brief sits on main and is resumed from main. A
  resume obeys the edited brief (release authorization, `operate:`,
  `stop-after:`), so the exposure is one run's authority bounds per
  edited brief, not the whole pipeline. A brief edit is visible in the PR
  diff, but the fast path makes human reading optional.
- Since when: ADR-0096's classifier (merge-train PR #915, 2026-10-15). It
  has been unchanged for briefs through ADR-0121.
- Code touched by the fix: `fast_path.py`, `tests/test_fast_path.py`,
  `.claude/implement-queue.md` (`gate_paths` plus its prose list), and the
  ADR record (ADR-0121 amendment).
- Mirrors re-checked: `factory_init.MIRRORS` has 39 entries and none
  names `fast_path.py` or `implement-queue.md` (a name filter over the
  list returned `[]`; `grep fast_path factory_init.py` is empty). Both are
  root-only, so no `update-manifest` is needed unless a mirrored file
  changes; if one does, run it per the brief's constraints.
- Cost of the fix: a PR that edits only a brief, such as a resume's brief
  commit, loses the fast path and needs a human merge.
- Out of reach of this fix: the `implement-queue` skill's GitHub-side
  `gate_paths` matcher (backlog line 144's seed).

### Does it bite today?

Nothing bites. Checked: `gh pr list --state merged --search
"merged:>=2026-10-16"` returned 106 PRs (earliest `mergedAt`
2026-10-16T00:39:00Z, the merge train's first run being #929 at
00:38 UTC in journal #930). 18 of them list an `autorun-brief.md` among
their files. Re-running `fast_path.classify` over each PR's changed files
(today's classifier): 17 are `review` for other reasons (a gate path or a
non-docs file, for example `CLAUDE.md`, `docs/adr/**`,
`.claude-plugin/plugin.json`, `decompose_lessons.py`). One, #1077
("docs(faster-sdlc): autorun brief; CI record row checked on the Owner's
decision", merged 2026-10-25T05:00:46Z), is two files
(`docs/features/faster-sdlc/autorun-brief.md`, `breakdown.md`) and
classifies `low-risk`: the only PR to which the defect applied. It did
not merge through the train: `mergedBy` is the Owner's login,
`autoMergeRequest` is null, and journal #930 records for it "#1077
failed: the `pull_request`-event `check` ... is red on head 6a76176 ...
No gate path touched (docs only)" with no merge attempted. No merged PR
had a brief as its only changed file, and none merged through the train.
The exposure is latent, as the brief's reading said.

## Ruled out

- Other run artifacts (`defect.md`, `breakdown.md`, `release.md`,
  `retro.md`, and the rest) as gate paths: Owner decision 1 (issue
  #1146) says they are state the stages re-derive. `prd.md` and
  `architecture.md` are already gate paths.
- A train merge of a brief-only PR to date: none (above).
- A `GATE_PREFIXES` entry as the fix: briefs live under per-slug
  directories, so only a basename match reaches them at any depth.
- Whether to gate other `docs/features/**` files: the seed's second half;
  the Owner narrowed it to `autorun-brief.md` only, so no further survey.

## In-flight check

Ran at the start of the run, outcome: **nothing matched**; the check ran.

- `gh pr list --state open` returned `[]`, so no open pull request does
  this (the review surface was reachable).
- `git branch -a --no-merged origin/main` filtered for
  `brief|fast-path|gate|1146`: the only name touching the surface is
  `fix/implement-queue-fast-path-consent`, with a worktree at
  `.claude/worktrees/fix-729`. Its `git ls-tree --name-only` of
  `docs/features/ docs/fixes/` shows only `a-broken-taxonomy-passes-the-gate`,
  `a-config-the-gate-cannot-read`, `a-gate-wait-is-not-spend`,
  `gate-row-the-reader-rejects-becomes-spend` and
  `gate-timeline-timestamp-trust`; head commit is ADR-0088 dated
  2026-10-12, predating the classifier. Not this work. The
  `agent/a-*-gate*` branches checked (`a-broken-taxonomy-passes-the-gate`,
  `a-config-the-gate-cannot-read`) are unrelated fixes dated August 2026.
  The other gate-named worktrees are detectors work, not the fast path.
- `git worktree list` shows this run's own worktree
  (`skills-wt-brief-gate`, branch `fix/a-brief-the-fast-path-waves-through`)
  and no other branch or worktree carrying a `docs/fixes/` directory for
  this slug or a brief gate.

## Work items

Shape per the brief: every `autorun-brief.md` at any depth is a gate path;
a basename match in the classifier, `"**/autorun-brief.md"` in the profile
rendered by `gate_globs()`. Implement picks the exact matcher and logs it.

- [x] **Failing tests first** — in `tests/test_fast_path.py`, through the
  public interface with exact output lines, written and run red before
  the fix.
  - Accept: a diff of only `docs/features/x/autorun-brief.md` and one of
    only `docs/fixes/y/autorun-brief.md` each expect
    `fast-path: review (<path>)`, exit 1 (red before the fix, where the
    output was `fast-path: low-risk`, exit 0); a neighbour such as
    `docs/features/x/breakdown.md` still prints `fast-path: low-risk`; a
    rename of a brief into and out of the run directory (real git,
    `TestRealGit` style) prints `review`; the pin test
    `TestProfilePin` expects the new glob.
- [x] **Classifier entry** — add the basename kind next to
  `GATE_PREFIXES`/`GATE_FILES` in `fast_path.py`, matched by
  `is_gate_path`, and rendered by `gate_globs()` as `**/autorun-brief.md`;
  update the module docstring and USAGE where they enumerate gate paths.
  - Accept: the new tests pass; `gate_globs()` contains
    `**/autorun-brief.md`; no other artifact basename is gated.
- [x] **Profile entry** — add `"**/autorun-brief.md"` to `gate_paths` in
  `.claude/implement-queue.md` and extend its prose list of gate paths.
  - Accept: `TestProfilePin` passes (profile `gate_paths` equals
    `fast_path.gate_globs()`).
- [x] **Amend ADR-0121** — a new provisional ADR (the next free number)
  recording that the brief is an instruction source and amending
  ADR-0121's survey; add its row to `docs/adr/README.md`; add the
  amendment to ADR-0121's status line, as ADR-0096's records ADR-0121's.
  - Accept: `python3 gates.py` and `python3 lint.py` pass; the README row
    and the status line point at each other.
- [x] **Claim the seed** — append
  `(claimed: maintenance:a-brief-the-fast-path-waves-through)` to
  `docs/backlog.md` line 143.
  - Accept: line 143 ends with the claim marker; no other line changes.
- [x] **Full gate** — run the suite and gates.
  - Accept: `python3 run_tests.py`, `python3 lint.py`,
    `python3 kb.py drift`, and `python3 gates.py && python3 gates.py
    --selftest` all pass; if a mirrored file changed, `python3
    factory_init.py update-manifest` was run first (after deleting stray
    `.orig`/`.rej`).

Out: the other faster-sdlc seeds (backlog line 144 onward), the
`implement-queue` skill's GitHub-side matcher, rewriting shipped
artifacts. Constraints: stdlib only; problem-string contracts with exact
string asserts; never edit `.claude-plugin/plugin.json`; write no literal
four-digit work-order or PRD-style id that does not exist.

## Notes

- 2026-11-03: Tracker: the PR closes #1146 with `Closes #1146` and
  carries a `No work order:` line (brief). Release is prepare and stop;
  the PR touches `fast_path.py` and `docs/adr/**`, so the train holds it
  for a human merge.

- 2026-11-03: Implement. Red first: `python3 -m unittest tests.test_fast_path`
  on the old classifier printed `FAILED (failures=8)` (brief edit
  alone: `(0, 'fast-path: low-risk\n') != (1, 'fast-path: review
  (docs/fixes/y/autorun-brief.md)\n')`; also the pin-glob test and the
  two real-git renames). After: `Ran 24 tests ... OK`. Matcher: the
  basename `autorun-brief.md` added to `GATE_NAMES` (exact basename, so
  `my-autorun-brief.md` and `autorun-brief-notes.md` stay low-risk);
  `gate_globs()` renders `**/autorun-brief.md`. Profile `gate_paths`
  and prose updated. ADR-0122 (provisional) amends ADR-0121; README row
  and ADR-0121's status line point at it. Backlog line 143 claimed.
  `fast_path.py` and `implement-queue.md` are not in `factory_init.MIRRORS`
  (`grep -c` of both names in `factory_init.py` is 0), so no
  `update-manifest`. Gate: `lint: 0 problem(s) across 35 skills`,
  `drift: 0 problem(s)`, `gates: 0 problem(s)`, `selftest: ok`.
  `run_tests.py` over three runs under machine load failed only one
  wall-clock test each time, a different one each run
  (`test_voice_grade` 200 KB linear-time, `test_gates` zero-count
  line); those modules pass when run alone.
