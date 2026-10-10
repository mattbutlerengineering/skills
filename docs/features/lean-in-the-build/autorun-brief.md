# Autorun brief: lean-in-the-build

Collected 2026-10-10 from the owner, one question at a time. Seeded by
GitHub issue #626 ("Improve architecture as part of our workflow"). This
brief is not an artifact.

## Feature

The owner's issue text, verbatim: "Use a skill like ponytail or something
similar to make sure that as we are building that we are generating
optimal code and minimizing slop." The `lean` utility skill (adapted from
Ponytail, MIT; landing in PR #632) is that skill, but today nothing in the
pipeline invokes it. This run wires it into the build: Implement and
Review.

## Scale

Feature run, slug `lean-in-the-build`, artifacts under
`docs/features/lean-in-the-build/`. Branch `feat/lean-in-the-build`,
worktree `.claude/worktrees/lean-in-build`, built LOCALLY on top of
`feat/lean-and-polish-skills` (PR #632), because it needs `lean` to exist.
No stacked PR is ever opened: Ship waits until #632 is merged to main,
then merges origin/main in and opens a normal PR to main (see Release).

## Idea-stage inputs (owner-confirmed draft)

- **Problem:** agents in Implement write more than the task needs —
  speculative helpers, re-implemented stdlib, second owners of a fact —
  and nothing in the pipeline asks "does this need to exist?" while the
  author is still looking.
- **Who / coping:** the owner reviewing agent PRs at the merge gate;
  today they catch bloat by eye, or a later `deepen` / one-owner pass
  catches it after it has landed.
- **Evidence:** anecdotal (the owner's #626), plus repo history: the
  one-fact-one-owner class recurred at least seven times and two needed
  emergency ADRs, because Review reads only its own run's diff (see the
  docs/backlog.md seed "Nothing in the pipeline asks 'does this fact
  already have an owner?'"). Label both as anecdote / repo history.
- **Why now:** `lean` just landed (PR #632).
- **Solution hunch:** Implement climbs lean's ladder before writing each
  work-order row and records the rung it stopped at; Review runs lean's
  cut-list over the run's diff and files each cut as a finding.
- **Success:** every run's review.md carries a lean cut-list over its
  diff, Implement records which ladder rung each row stopped at, and
  lint and evals pin both.
- **Biggest unknowns / risks:** the cut-list becomes boilerplate nobody
  acts on; ladder-recording bloats breakdown.md; stage skills must stay
  harness-neutral and their evals must not regress; `lean` must stay a
  utility skill (owns no artifact, never routed to) even when stages
  consult it.

## Scope

IN: `skills/implement/SKILL.md` and `skills/review/SKILL.md` (and their
templates/references if any) to consult `lean`; the protocol only where
it describes what those stages must record (normative — a change here is
deliberate and stated); lint checks that pin the new recorded shapes;
output-eval or routing-eval definitions added (never edited to pass);
README/CONTEXT wording if the stages' descriptions change; plugin
version bump per repo convention when skills/ changes.

OUT: changing `lean` itself beyond what wiring strictly needs; CI or
hook-based bloat detection (owner chose stage wiring, not a gate);
`deepen`, `audit`, `polish`; issues #624/#625/#627.

DECIDED (owner, 2026-10-10): wire `lean` into BOTH Implement (ladder per
row) and Review (cut-list over the diff). Not Review-only; no CI/hook.

## Tracker

Seeded by #626 only; the PR says `Closes #626`. No other tracker writes.

## User-facing surface

None. `ux: not-applicable`.

## Release authorization

Ship is HELD until PR #632 is merged to main. Then: merge origin/main
into this branch (verify the merged tree: battery green), push
`feat/lean-in-the-build` by name, open ONE non-draft PR to `main` with
body per the protocol's "Pull request body" section (`Closes #626`, a
`No work order:` line, smallest visual, before/after evidence,
`## Merge danger`), then STOP: no merge, no tag. If #632 is not merged
when Ship is reached, Ship writes release.md as prepare-and-stop and
reports that it is waiting on #632. Never open a PR against
`feat/lean-and-polish-skills`.

## Standing instructions for every stage

Answer interview questions from this brief. Where it is silent and the
stage skill offers a recommended default, take it and log it under the
artifact's `assumptions:` frontmatter; where there is no default —
including every evidentiary question — stop and surface. Never fabricate
verification evidence: run the real commands (`python3 -m unittest
discover tests`, `python3 lint.py`, `python3 gates.py && python3 gates.py
--selftest`). `trigger_eval.py` / `charter_replay.py` cost money: do not
run them; record them as owed. Work only inside
`.claude/worktrees/lean-in-build`. Commit each stage's artifact
(Conventional Commits, ending with `Co-Authored-By: Claude Opus 5.5
<noreply@anthropic.com>`). Typed ids: PRD ids and work-order ids continue
from the highest across ALL local branches and origin (PRD-0011 and row
0148 are used on #632's branch; the reviewer-token branch uses rows to
0145 and may add 0149+ — re-check at the time). Shell is zsh — never
name a variable `status`.

## Amendment 2026-10-10 (owner, relayed by the orchestrating session; issue #626 option A)

The owner chose option A from the #626 research. It narrows the scope
above; where the two disagree, this amendment wins.

- **Implement:** before writing code for each work item, climb lean's
  "does this need to exist" ladder — reference
  `skills/lean/references/ladder.md`, never duplicate it. Keep lean's
  never-cut floor (validation, error handling, security, accessibility).
  Deliberate shortcuts carry a `lean:` marker in the code. Do NOT add a
  per-row "rung reached" record to breakdown.md (the idea's own
  "bloat in the record" risk); the marker is the record.
- **Review:** add a fourth pass, **Complexity**, that applies lean's
  cut-list (`skills/lean/references/cut-list.md`) to the run's diff,
  files cuts as findings, audits the `lean:` markers the diff added
  (each needs its trigger), and routes module-shape concerns to `deepen`
  as a hand-off — never an inline refactor.
- Keep it small and surgical: no new skill, no hook, no CI gate. A
  lint pin is allowed only if a stage-to-utility file reference needs one
  to stay legal; check lint/protocol for the sanctioned cross-skill
  reference pattern (ADR-0023). Write a new ADR if adding a
  stage-to-utility dependency is the kind of decision the repo records.
- Bump `.claude-plugin/plugin.json` (patch).
- Do not run paid evals; never edit an eval definition to make a case
  pass.
- **Base and release:** PR #632 is merged (origin/main 6aacc5c). This run
  now lives on branch `feat/lean-in-the-loop` in worktree
  `.claude/worktrees/agent-a17bfa9ae4fb94037`, cut fresh from origin/main
  with the idea commits cherry-picked; the old `lean-in-build` worktree is
  superseded. Ship IS authorized to push the branch and open ONE ready
  (non-draft) PR to main with `Closes #626` and a `No work order:` waiver
  line, then STOP — no merge, no tag.
