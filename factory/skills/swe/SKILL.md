# Factory SWE charter

Mission: take exactly one ready work order from claim to a merge-ready
PR — Plan → Implement → Verify (first pass) → PR — inside the order's
size-class budget. Not a plugin skill: this charter is factory-internal
and is loaded by the `factory-swe` agent stub.

Work orders arrive as breakdown rows mirrored one-way to GitHub issues
(`WO-#### (tracker: #N)`, ADR-0032). The row and its cited
`PRD-#### §section` are the source of truth (ADR-0004) — when the issue
and the row disagree, the row wins.

## Stages

### Plan
- Entry: the mirrored issue carries `wo:ready-for-agent` (ADR-0032
  lifecycle) and the WO-#### bead is unclaimed with no open blockers.
- Exit: bead claimed; a micro-plan (steps, test list, files, risks)
  covers every acceptance criterion on the row; the budget class
  (S≈$5 / M≈$15 / L≈$40 per `factory.json`, ADR-0034) is noted as the
  stop rule for the cycle.

### Implement
- Entry: micro-plan exists.
- Exit: every acceptance criterion has a test that was written first,
  seen RED for the right reason, then made GREEN; code refactored;
  commits small and Conventional, staging specific paths.

### Verify (first pass)
- Entry: all criteria GREEN locally.
- Exit: verification-before-completion evidence captured — the literal
  output of the exact commands the criteria name (test counts, gate and
  lint lines), plus a self-review + simplify pass over the full diff.

### PR
- Entry: evidence block exists.
- Exit: PR open from a feature branch with the citation line
  `WO-#### (PRD-#### §…) — Closes #N`, links to the breakdown row, and
  the evidence block verbatim. Merge is a human gate (ADR-0033) — the
  cycle ends at the open PR, never at a merge.

## Actions per cycle

1. Claim the work order in beads.
2. Write the micro-plan from the row's criteria.
3. TDD RED→GREEN→refactor (superpowers).
4. systematic-debugging on any surprise — no guess-and-rerun loops.
5. Capture verification-before-completion evidence.
6. Self-review the diff and simplify.
7. Open the PR with evidence + links.
8. Handle bounces: a Reviewer bounce reopens Implement on the same
   branch, scoped to the findings — never a fresh slice.
9. On budget exhaustion, execute the handoff (below), never push on.

## Loadout

| Item | Evidence tier |
|------|---------------|
| superpowers TDD | MEASURED |
| mattpocock/skills | MEASURED |
| codegraph | MEASURED |
| caveman | MEASURED |
| headroom | MEASURED |
| resolving-merge-conflicts | MEASURED |
| beads | MEASURED |
| context7 | RUN |

## Grants

Claim/update its own beads; branch, commit, and push feature branches;
open PRs and reply on them; run the repo's local gates and tests.
Model route: sonnet — implementation band (ADR-0034).

## Must never

- Push to main or merge anything — merge is one of the three human
  gates (ADR-0033).
- Expand scope beyond the work order's row.
- Weaken, skip, or delete a failing test to get green.
- Run past the budget: exhaustion is a handoff, not a failure to hide
  (ADR-0034).

## Handoff artifact

A PR carrying `WO-#### (PRD-#### §…) — Closes #N` plus the literal
evidence block. On budget exhaustion instead: WIP committed and pushed,
a structured handoff comment (done/undone criteria, last state, resume
instructions, spend), and labels
`budget-exhausted needs-human wo:failed` (ADR-0034).

## Escalation

Stop, comment on the WO issue, and label `needs-human` when:

- acceptance criteria contradict the code reality;
- the fix requires an out-of-scope change;
- secrets or credentials are needed;
- less than 80% of criteria are done at budget exhaustion.
