# Autorun brief: decompose-eval-suite

Not an artifact. Written 2026-10-20 by the orchestrator under the `/goal`
"complete remaining gh issues". The Owner answered in session, taking the
recommended option each time:

1. What to drive: #989, the last step of the Decompose learning loop
   (steps 1 to 3 merged as #1040, #1047, #1050).
2. Scope: "Suite and graders only, no paid run (Recommended)". Author the
   Decompose eval suite under `plugin-evals/` (manifest
   `experimental.evals`, ADR-0081) with fixture architectures holding
   known-good cuts, and deterministic graders that emit text feedback
   (coverage misses, dangling Blocked by, untestable Accept lines,
   mis-sized items), all tested offline for free. The optional reflective
   prompt optimization (GEPA/TextGrad) is out of scope: the issue says
   "only then", and no scored outcome data exists to optimize against.
   No paid run: nothing here invokes `claude plugin eval`, and LEDGER.md
   maturity does not move (ADR-0012, ADR-0019). A first paid run needs the
   Owner's own say-so and is a follow-up.
3. Release (carried over from #986 to #988, an orchestrator reading):
   prepare-and-stop. Ship pushes the branch and opens one PR and does not
   merge. A merge needs the Owner's own answer.

The rest of this brief is the orchestrator's reading of issue #989 and of
the repo. When a stage needs an answer this brief doesn't hold, it follows
the autorun rule: take the skill-supplied default and log it, or else stop
and surface the question.

## What and why (orchestrator's reading of #989)

GEPA and TextGrad rewrite a prompt from execution traces plus a score and
text feedback; both need a scored eval whose feedback says why a candidate
failed. Today `plugin-evals/` has no Decompose suite and LEDGER.md lists
decompose at `used-once`. This run builds the suite (the issue's step 1),
not the optimizer (step 2).

## Acceptance (from the issue, as scoped by the Owner)

- The suite is wired so it runs with `claude plugin eval . --tag decompose`
  and records results append-only (shape and naming from `eval_schema.py`,
  records under `plugin-evals/records/`). This run does not execute it.
- LEDGER maturity moves only on a real run: this run leaves it unchanged.
- No eval definition is edited to make a failing case pass.
- Graders are deterministic and offline, emit text feedback, and are
  tested through public interfaces with exact strings.

## Idea-stage inputs (orchestrator's reading)

- **Problem, from the sufferer's view.** The Owner changes the Decompose
  skill (#988 just did) with no scored way to tell a better skill from a
  worse one; the only signals are after-the-fact outcome rates.
- **Who has it, and how they cope today.** The Owner and the Decompose
  skill's later editors. They judge breakdowns by reading them.
- **Why now.** The loop's steps 1 to 3 shipped; step 4 needs a scored eval
  before any optimization is possible.
- **Evidence.** Anecdote, labelled: GEPA (arXiv 2507.19457) and TextGrad
  results from the issue; nothing specific to software decomposition.
- **Rough shape.** A plugin-eval suite plus a stdlib grader that reads a
  produced breakdown.md against a fixture architecture and prints
  line-level feedback. A hunch, not a design.
- **Success.** A grader run on a known-good and a known-bad fixture cut
  gives different, explained scores, offline.
- **Ways this dies.** Fixtures that only mirror the skill's own template
  (so everything passes); graders that reward gaming; suite shape that the
  plugin-eval harness rejects.

## Scope, constraints and tracker

- In: suite definition under `plugin-evals/`, fixtures, deterministic
  graders with text feedback, tests, docs.
- Out: any paid eval run, any LEDGER change, prompt optimization, editing
  skills/decompose, a plugin.json version bump (ADR-0095).
- Stdlib only. A new shared module needs multiple real callers AND observed
  divergence (CLAUDE.md seam rule); eval knowledge lives in `eval_schema.py`
  (ADR-0022, ADR-0024), so read it before adding a second owner.
- `plugin-evals/` layout and the manifest `experimental.evals` entry follow
  ADR-0081; read the existing suites first.
- Issue #989 seeds the run and the PR closes it. No work order is mirrored;
  the PR body carries a `No work order:` line.
- No user-facing surface (`ux:` not applicable).

## Operate

operate:
  skip

Operate does not run in this invocation: step 4 is the last of the loop and
no downstream step reads this run's output.

stop-after: ship
