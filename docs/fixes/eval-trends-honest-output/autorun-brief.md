# Autorun brief: eval-trends-honest-output

Not an artifact. Written 2026-10-22 by the orchestrator. The Owner answered
in session, taking the recommended option each time:

1. What to drive: #1062 ("eval_trends: empty-root wording, hull labelled
   95%, and other deferred review findings"), chosen from the five follow-up
   issues filed that day. It is a maintenance run (a refinement of a shipped
   tool, #1056), entered at Capture; no PRD or Architect stage.
2. Release (carried over from earlier runs, an orchestrator reading):
   prepare-and-stop. Ship pushes the branch and opens one PR and does not
   merge; a merge needs the Owner's own answer.

The rest is the orchestrator's reading of #1062 and the eval-trends review
(`docs/features/eval-trends/review.md`, section "Deferred"). When a stage
needs an answer this brief does not hold, take the skill-supplied default and
log it under `assumptions:`, or else stop and surface it.

## Scope (what this run changes)

1. **Empty or wrong root.** `python3 eval_trends.py` on a root with no
   records prints `0 record(s)` and only REFUSED lines. Add one clear line
   (`eval-trends: no records found under <root>`) so an empty or mistyped
   root cannot be mistaken for a quiet result. It changes pinned output, so
   the tests that pin the exact lines are amended in the same change, with
   the reason recorded.
2. **Honest hull label.** The day-hull (min lower, max upper of a day's
   reruns' Wilson intervals) is printed as `95% lo-hi`, but it is only the
   span the reruns' own intervals cover, not a 95% interval. Relabel the
   printed text so it no longer claims a confidence level (for example
   `range lo-hi`; Capture/Implement choose the exact word, pin it with a
   test, and update the research note and architecture text that quote the
   old label only if they name it as the tool's output).
3. **Symlinks and file size.** The records readers follow symlinks and have
   no size bound. Refuse a symlinked record and any file above a size bound
   as a labelled problem (exit 1 like other malformed records), never as a
   skip. Measure the largest real record under evals/results and
   plugin-evals/records and set the bound as a named constant a clear
   multiple above it; record the measurement.

## Explicitly not changed (stay documented, no code)

- Future-dated records are accepted if their file name agrees: rejecting
  them would make output depend on the clock.
- First-day-against-last-day with no multiple-comparison correction: the
  header and the verdict suffix already state it.

## Constraints

- Read-only tool: it must still never write under evals/results or
  plugin-evals/records, make no network or model call, stay stdlib only. No
  paid run; LEDGER.md unchanged.
- Root-only (ADR-0115): no new import pair; the dual-membership pin stays 55.
- No permanent test may assert a path is "unchanged against main" (they rot);
  scope checks are one-off commands quoted in the stage notes.
- Branches never touch `.claude-plugin/plugin.json`'s version (ADR-0095); no
  skill is changed, so no release PR.
- The PR closes #1062 (`Closes #1062`) and its body says plainly which items
  were fixed and that future-dated and multiple-comparison stay as
  documented decisions. No work order; the PR body carries a
  `No work order:` line.

stop-after: ship
