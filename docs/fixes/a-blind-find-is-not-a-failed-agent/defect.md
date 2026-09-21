---
stage: capture
run: maintenance:a-blind-find-is-not-a-failed-agent
date: 2026-08-25
re-entry: architect
intake: #348
assumptions:
  - "Captured as a DEFECT brief. The pipeline reaches a wrong terminal state on the dispatch plane and skips a required validation, rather than merely reading poorly. Re-entry is architect because the fix is a decision about what a work order's state should be when the factory cannot observe the agent's delivery — and the alternative to a false terminal verdict is an order that stays in-progress, which the workflow's own comment names as the rot wo:failed exists to prevent."
  - "Severity is argued from the rate-limit path, not the truncation path. A truncated listing needs 1000 open PRs and is not reachable in this repo; an unreadable gh call is ordinary and needs nothing. Both share one root and both are fixed here, but the brief does not lean on the rarer half to justify the run."
  - "The in-flight check ran (protocol, Work already in flight): none of the fourteen open PRs touches assembler.py or assembler.yml. #343 and #347 fix the same defect CLASS in rejection_mining.py and gate_digest.py — both are reporting artifacts, and neither shares this one's consequence, which is a state flip rather than a sentence."
---

# Defect: a blind `find-pr` is recorded as a failed agent

## Defect

**Observed.** `assembler.pr_for_issue` (`assembler.py:248`) answers
`(number, problems)`. It returns `number=None` in two unrelated
situations and gives the workflow no way to tell them apart:

- the `gh pr list` read was unusable — a missing, unauthenticated, or
  rate-limited gh (`cli.CLI_FAILURES`);
- the read succeeded and no open PR closes the issue.

`assembler.yml` branches on exactly the two channels this produces — the
step's exit code and its `pr` output — and applies the same treatment to
both:

- **the delivered PR is never validated.** `Trigger the validator on the
  agent's PR` is gated on `steps.find.outputs.pr != ''`. This step exists
  because GitHub suppresses `pull_request` events for PRs the
  `GITHUB_TOKEN` opens, so without it the agent's PR reaches gate 3 with
  no check, no reviewer and no queue entry (WO-0030). A blind find
  re-opens exactly that hole.
- **the work order is flipped to `wo:failed`.** `Mark the work order
  failed` is gated on `failure() && steps.claim.outputs.transitioned ==
  'true'`. `wo:failed` is ADR-0032's terminal state; the gate digest and
  the improvement routine both read it as work that is dead.

So the factory records a verdict about the agent's performance that it
reached from its own blindness.

**Expected.** A verdict about the agent should require having observed
the agent's output. When the factory cannot look, the honest state is
"not known", and the signal belongs to the operator — a red run — not to
the work order's lifecycle label.

**Not a request to make the run green.** A find that cannot look is a
real failure and should redden the run. The defect is the *attribution*,
not the loudness.

## Reproduction / Evidence

Driving the public CLI with the repo's injected gh fake and a real
`$GITHUB_OUTPUT` file — the two channels `assembler.yml` reads:

```
--- agent DELIVERED, gh readable
    exit=0  outputs='pr=6'
--- agent DELIVERED, gh rate-limited
    exit=1  outputs='pr='
--- agent delivered NOTHING, gh readable
    exit=1  outputs='pr='
```

Rows two and three are identical in both channels. The only thing that
differs is the problem string printed to the log:

```
asm: gh pr list failed: boom
asm: no open PR closes issue #110 — the dispatched agent delivered no traceable PR
```

That line is honest, and nothing branches on it.

## Reachability

`cli.gh_runner`'s docstring states the failure vocabulary: *"A missing
(OSError), unauthenticated, or rate-limited (CalledProcessError) gh
raises CLI_FAILURES."* One rate-limited `gh pr list` during a dispatched
run is enough. This needs no unusual scale and no unusual repo.

## The second, rarer half

`pr_for_issue` passes `window=LIST_WINDOW` and never consults
`read.truncated`. On a full window the agent's PR may sit beyond it, and
the function appends a **positive false claim** — *"the dispatched agent
delivered no traceable PR"* — about work it never saw. Same root, worse
sentence, but it needs 1000 open PRs. Recorded and fixed here; not the
reason for the run.

## Impact

The dispatch plane's terminal state is the factory's memory of what
happened. A `wo:failed` reached by blindness is wrong in a way that does
not heal: the order leaves the in-flight queues the digest and the
routine read, and the PR the agent actually delivered sits unvalidated
with no event to wake the validator. The two mechanisms that would
otherwise catch it are the same two the flip removes it from.

## Scope

`assembler.py`, `tests/test_assembler.py`, and
`.github/workflows/assembler.yml`. Both `assembler.py` and the workflow
are in `factory_init.MIRRORS`, so the payload copies and
`factory/manifest.json` move with them.

This changes when a work order may be given ADR-0032's terminal state,
which is a recorded-decision-shaped change; Architect should expect to
offer an ADR.
