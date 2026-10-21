# Autorun brief: idea-ambition-ladder

Not an artifact. Written 2026-10-20 by the orchestrator under the `/goal`
"complete remaining gh issues". The Owner answered in session, taking the
recommended option each time:

1. What to drive: #994, the ambition ladder for `skills/idea`.
2. Demo hand-off, the issue's one open Owner decision: "Via the PRD
   (Recommended)". The PRD copies idea.md's **The demo** into a success
   criterion ("the demo runs as written"); `verify` checks it; `launch-demo`
   stays unchanged and keeps reading only what ship produces. `skills/prd`
   gains one line that carries the demo script forward.
3. Paid eval: "Suite only, no paid run (Recommended)". Author the
   `plugin-evals/idea/` with/without-plugin suite and test it statically
   for free. Nothing here invokes `claude plugin eval`. The issue's
   acceptance box for a cited run under `plugin-evals/records/` stays
   unchecked and is a follow-up that needs the Owner's own authorization.
   LEDGER.md maturity does not move (ADR-0012, ADR-0019).
4. Release (carried over from earlier runs, an orchestrator reading):
   prepare-and-stop. Ship pushes the branch and opens one PR and does not
   merge; a merge needs the Owner's own answer.

The rest of this brief is the orchestrator's reading of issue #994 and of
the repo. When a stage needs an answer this brief doesn't hold, it follows
the autorun rule: take the skill-supplied default and log it, or else stop
and surface the question.

## What and why

Issue #994 is the full spec; read it with `gh issue view 994`. `skills/idea`
only narrows: the rule "don't replace their idea with yours", "no solution
design here", and a single Solution-hunch slot keep every brief at the size
of the opening framing. The proposal is an ambition ladder (Solid /
Showstopper-by-default / Moonshot) after the problem and evidence questions
and before the solution hunch, four showstopper tests (a 30-second demo
exists; removes a step; built on something only this product has;
achievable with a named riskiest piece and a ~2-day spike), three interview
prompts, scaled down for feature runs.

## Changes the issue asks for

- `skills/idea/SKILL.md`: the ladder step, four tests, prompts; feature
  runs get the scaled-down version.
- `skills/idea/TEMPLATE.md`: sections **Ambition rung**, **The demo**,
  **Riskiest piece + spike**, **Cheapest kill test**.
- Unchosen rungs are appended to `docs/backlog.md` as seeds, following the
  protocol's seed-backlog grammar (ADR-0029; the backlog stays an advisory
  seed inbox).
- `skills/prd`: one line carrying the demo script forward (decision 2).
- `plugin-evals/idea/`: a with/without-plugin suite whose cases check the
  brief names a showstopper that passes all four tests, the user's framing
  is kept, and the moonshot is saved as a seed and not chosen. Never run.

## Constraints

- Stdlib only. No new tool is expected; this is skill text, a template, a
  suite and tests. If Architect finds a tool is needed, the seam rule
  applies (CLAUDE.md).
- This branch changes `skills/idea` and `skills/prd`, so by ADR-0095 it
  needs a wave `chore(release)` PR; this branch never touches
  `.claude-plugin/plugin.json`'s version. The Owner's pending wave release
  PR for the earlier Decompose skill change (the lessons run) is the same
  wave; Ship records it as a follow-up and does not open it.
- `lint.py` checks skills (frontmatter, trigger phrasing); re-run it after
  editing any SKILL.md or TEMPLATE.md. TEMPLATE.md edits can affect
  `protocol.py` artifact checks and existing run artifacts: Architect must
  check that old idea.md files still validate.
- Issue #994 seeds the run and the PR closes it. No work order is
  mirrored; the PR body carries a `No work order:` line.
- No user-facing surface beyond skill text (`ux:` not applicable).

## Idea-stage inputs (orchestrator's reading)

- **Problem, from the sufferer's view.** The Owner runs the pipeline and
  every brief comes out achievable but never memorable; no step asks for
  the bigger, presentable version.
- **Who has it, and how they cope today.** The Owner and anyone running
  `idea`. They add ambition by hand, or not at all.
- **Why now.** The launch-demo skill exists and has nothing worth
  recording when briefs have no demo moment.
- **Evidence.** Anecdote, labelled: the issue's own observation across
  runs; none measured.
- **Rough shape.** Skill text, template sections, a PRD hand-off line and
  an eval suite. A hunch, not a design.
- **Success.** A new idea.md names a chosen rung and a 30-second demo
  script that passes the four tests, with unchosen rungs landed as seeds.
- **Ways this dies.** The ladder becomes ceremony and every brief picks
  Showstopper by default; the tests become taste; the user's framing is
  replaced; seed grammar breaks gates.

## Operate

operate:
  skip

Operate does not run in this invocation: the effect shows only over later
runs, and nothing downstream consumes this run's output.

stop-after: ship
