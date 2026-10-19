# Autorun brief: decompose-outcome-signals

Not an artifact. Written 2026-10-18 by the orchestrator. The Owner invoked
`/idea-to-prod:autorun` with no description and answered five questions one
at a time in session, taking the recommended option each time:

1. What to drive: "#986 Decompose loop 1/4 (Recommended)".
2. Scale and slug: "decompose-outcome-signals (Recommended)". This is a
   feature run.
3. Data source: "Subjects + file-history fallback (Recommended)".
4. Release: "Prepare-and-stop, open PR (Recommended)".
5. Operate: "minimum-signal: #987 uses it (Recommended)".

The rest of this brief is the orchestrator's reading of issue #986 and of
the repo, and is marked that way. When a stage needs an answer this brief
doesn't hold, it follows the autorun rule: take the skill-supplied default
and log it, or else stop and surface the question.

## What and why

This is issue #986, step 1 of 4 in the Decompose learning loop. It came out
of the 2026-10-16 deep-research pass on how the Decompose stage can learn
over time. The tool is a stdlib-only measurement over git history. It
reports three outcome signals per run and in aggregate:

- **Re-plan rate.** How many breakdown items were added, split, merged or
  dropped between a run's decompose boundary and its implement boundary.
  External reference from the issue: about 10% of items are re-estimated
  after planning in open-source agile projects (3–17% by project;
  Empirical Software Engineering, doi 10.1007/s10664-022-10192-9).
- **Design gaps routed back to Architect.** A decompose boundary that a
  later architect commit on the same run follows. The issue's example is
  pr-body-preflight, 772e374 → 766633c on 2026-10-16.
- **Review findings traced to an item.** Findings in review.md that name a
  breakdown item.

Steps 2–4 (#987, #988, #989) calibrate against these numbers. Each later
step's effect can only be measured once this one exists.

## Idea-stage inputs

- **Problem, from the sufferer's view.** The Owner tunes the Decompose
  skill without knowing whether its plans hold up. Nobody can say how
  often a breakdown is re-planned during Implement, how often Decompose
  had to send a design gap back to Architect, or which items review
  findings land on. Changes to the skill are judged by feel.
- **Who has it, and how they cope today.** The Owner, and every later
  step of the series (#987 calibration, #988 lessons file, #989 eval and
  prompt optimization), which needs a baseline. Today nobody copes: the
  signals sit unread in git history and in review.md files.
- **Why now.** The 2026-10-16 research pass ranked an estimate-versus-actual
  feedback loop as the best-evidenced approach. The cost data that loop
  needs is nearly absent: #987 reports 7 of 184 ledger rows with a cost.
  Git signals cost nothing to collect, so they are the first loop the
  repo can actually run.
- **Evidence.**
  - Observed: the pr-body-preflight run routed two design gaps from
    Decompose back to Architect (772e374 decompose, then 766633c
    architect, both on `feat/pr-body-preflight`).
  - Measured by the orchestrator on 2026-10-18: 35 run directories hold a
    `breakdown.md`. Commits with a `docs(<slug>): decompose — …` subject
    exist for only 3 runs across every ref (factory, fail-closed-roll-up,
    pr-body-preflight), counting GitHub PR head refs.
  - The external re-estimation rate is the published study cited in #986.
- **Rough shape of a solution (a hunch).** A root stdlib Python tool that
  shells out to git (`cli.py` conventions). For each run directory it
  locates the decompose and implement boundaries, diffs the breakdown's
  item rows between them, scans later commits for architect boundaries,
  and matches review.md findings against item ids. Output follows the
  repo's problem-string / count contract.
- **Success, in one sentence.** One command prints re-plan, design-gap and
  review-traced counts for every measurable run and in aggregate. The
  first real numbers for this repo are recorded append-only by the tool
  itself, never typed by hand.
- **Biggest unknowns, and how this dies.**
  1. History is squashed. Main is squash-merged, so boundary commits
     survive only on run branches and PR head refs (`refs/pull/*/head`),
     and those can be pruned. A tool that silently measures 3 runs would
     be honest but worthless as a baseline.
  2. Boundary inference. Most runs predate the commit-subject convention,
     so an inferred boundary (see Owner decision 3) can be wrong. If an
     inferred number is presented as observed, the measurement lies.
  3. Breakdown row identity. A "split" or "merge" is only detectable if
     items carry stable ids (WO ids, row numbers, titles), and the shape
     of breakdown rows has drifted across runs.
  4. Review findings rarely name an item id. The third signal may be
     close to zero for honest reasons, and zero must not read as "no
     findings".

## Owner decision 3: data source

Read each run's history across every ref, PR head refs included. When a
run has `docs(<slug>): decompose — …` / `implement — …` / `architect — …`
boundary subjects, use them. When it doesn't, fall back to the commit that
first added the run's `breakdown.md` (inferred decompose boundary) and the
first commit that ticks a breakdown checkbox (inferred implement boundary).
Every per-run row labels each boundary **observed** or **inferred**, and
the aggregate reports the two populations separately as well as combined.
A run with neither form of boundary is reported as unmeasurable, with the
reason, and never counted as zero.

## Scope

In:

- the measurement tool, its tests through the public interface, and a
  `make`/doc mention only if the repo's conventions require one;
- the three signals above, per run and in aggregate, with the
  observed/inferred labelling;
- a run with no re-plans, one with a split, and one routed back to
  Architect, covered by fixture tests (acceptance criteria in #986);
- recording the first real numbers append-only, written by the tool's own
  output. Architect picks the location and naming, following the
  `evals/results/` / `plugin-evals/records/` precedents.

Out:

- cost calibration and metering (#987), the lessons file (#988), and
  prompt optimization (#989);
- changing the Decompose skill or the boundary-commit convention;
- fetching from the network inside the tool. It reads the refs the clone
  has, and says which refs it read. Fetching `refs/pull/*/head` is a
  documented manual step, not something the tool does.

## Success criteria

- One invocation measures every run directory with a breakdown and prints
  per-run rows and an aggregate in the repo's problem-string / count
  contract.
- Boundaries are labelled observed or inferred. Unmeasurable runs are
  named with a reason.
- Tests through the public interface cover at least: no re-plans; a split;
  routed back to Architect; an inferred boundary; an unmeasurable run.
- The first real numbers for this repo are recorded append-only, from the
  tool's actual output.
- `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py` and `python3 gates.py --selftest` all pass.

## Constraints and already decided

- Stdlib only. External CLIs go through `cli.py`.
- Root-only tool unless a payload tool imports it (ADR-0060's rule). The
  expected answer is root-only, so there's no `factory_init.MIRRORS`
  change and no manifest regen.
- One owner per fact: reuse `protocol.py` for the run walk and artifact
  names, and `knowledge_plane.py` for the typed-ID grammar, rather than
  retyping their regexes. `python3 one_owner.py` is the review pre-pass.
- No plugin version bump (ADR-0095). This is not a `skills/` change.
- Eval honesty: no number is ever entered by hand.

## Tracker

Issue #986 seeds the run. Ship's PR body carries `Closes #986` and a
`No work order:` line, unless Decompose mirrors work orders (it should
not: ADR-0032 mirroring is the factory's, not this run's). There is no
other tracker interaction.

## User-facing surface

None in the UX-stage sense. It is a CLI measurement with text output, so
the PRD's `ux:` decision is expected to be not required.

## Release authorization

Prepare and stop (Owner decision 4). Ship pushes
`feat/decompose-outcome-signals`, opens the PR, records `outcome:
prepared` with `pending-merge: <PR url>`, and stops: no merge, no version
bump, no tag.

## Operate

operate:
  minimum-signal: step 2 (#987) reads this tool's output, either using
    the numbers or failing on them

Operate does not run in this invocation.

stop-after: ship
