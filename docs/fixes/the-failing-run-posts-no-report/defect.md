---
stage: capture
run: maintenance:the-failing-run-posts-no-report
date: 2026-08-27
re-entry: implement
assumptions: []
---

# Defect: the week the report is needed most is the week it is not filed

## Defect

`.github/workflows/cost-report.yml`'s **Post the weekly cost report
issue** step carried no `if:`, so GitHub Actions gated it on the implicit
`success()` — it runs only when every earlier step in the job succeeded.
The earlier step is `make cost-report`, and that step exits nonzero on
exactly the fail-closed verdicts: an unreadable ledger line, or a monthly
cap that cannot be resolved.

So the weekly report issue is posted on every ordinary week and skipped
on precisely the weeks something is wrong with the money.

The step immediately below it already knows this. It carries an explicit
`always()` and says why:

```
      # always(): the report step exits nonzero on exactly the fail-closed
      # verdicts (malformed ledger line, unresolvable cap — WO-0033), and
      # those verdicts carry pause=true; an implicit success() gate would
      # skip the pause at the moment it matters most.
```

The same sentence is true of the posting step, one step earlier in the
same file, reading the same `steps.report.outputs`.

## Why it matters

`cost_report.guard` composes a report for the failing path **on
purpose**. Its docstring:

> FAILS CLOSED: any read or resolution problem decides PAUSE rather than
> letting unaccountable spend continue [...] Both aggregates are always
> the best-effort rollup of what WAS readable, even on a failing path, so
> a human reading the report still sees something.

There is no human reading it. The module computes the best-effort
rollup, writes it to `$GITHUB_OUTPUT`, and the workflow discards it.

What a maintainer actually sees in that week: a red `cost-report` run and
nothing else. No issue naming the malformed ledger line, no spend figure,
no verdict — and, today, not even a pause, because the pause step exits 1
when `FACTORY_PAUSE_TOKEN` is unset (it is). The one artifact ADR-0034
gives a human to act on is the artifact this run withholds.

The blast radius is bounded but the direction is wrong: the workflow is
mirrored verbatim into the template payload, so every stamped product
repo inherits the same silence.

## Reproduction

A single malformed line in the ledger — detector G's grammar, the same
one `cost_ledger.read` enforces — driving `cost_report.main` exactly as
`make cost-report` does:

```
$ python3 repro.py                    # costs.jsonl = "not json\n"
cr: unreadable ledger — failing closed
ledger: docs/factory/costs.jsonl:1 is not valid JSON: Expecting value: line 1 column 1 (char 0)
cost_report: 1 problem(s)
=== make cost-report exit code: 1
  pause=true
  title=Factory cost report — 2026-08-28
  reason=cr: unreadable ledger — failing closed
=== the report body the workflow would have posted ===
  ## Factory cost report — 2026-08-28

  **Spend this month (2026-08):** $0.00 of unknown monthly cap (lifetime: $0.00)
  **Runs recorded:** 0
  **Total tokens:** 0

  ### By work order (lifetime)
  - (no runs recorded)

  ### Verdict
  cr: unreadable ledger — failing closed
```

Every output the posting step needs is present and correct — title, body,
verdict. The step is skipped anyway, because the process that produced
them exited 1.

The step as it stood, isolated from the file:

```
      - name: Post the weekly cost report issue
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPORT_TITLE: ${{ steps.report.outputs.title }}
          REPORT_BODY: ${{ steps.report.outputs.body }}
        run: gh issue create --title "$REPORT_TITLE" --body "$REPORT_BODY"
```

## Why the tests did not catch it

`tests/test_cost_report.py` has a class for exactly this rule, and its
docstring states it in the general form:

```
class TestFailClosedPause(unittest.TestCase):
    """WO-0033's workflow half: the report step exits nonzero on exactly
    the fail-closed verdicts, so a pause step gated on implicit success()
    is skipped at the moment it matters most."""
```

It holds two tests: the pause step survives a failing report step, and
the resume step deliberately does not. Both are `assertIn` calls over the
whole file's text. Neither can name a step, so neither could notice that
a **third** step reads the same outputs and states no gate at all — the
suite asserted the invariant on the two steps that already had a gate and
skipped the one that had none.

`TestWorkflowOutputLockstep` looks like it would cover it and does not:
it asserts `{"pause", "title", "body"}` are all referenced by the
workflow. `title` and `body` are referenced — by the step that never
runs.

## Fix

Gate the posting step explicitly, in the same folded form the pause step
uses:

```
        if: >-
          always()
          && steps.report.outputs.title != ''
```

`always()` is the correction. The title guard is what `always()` costs:
without it, a report step that died *before* `write_outputs` (an import
error, a crash) would hand `gh issue create` an empty `--title` and turn
a diagnosable Python traceback into a confusing `gh` error. Outputs are
written before the failing exit — `TestMain` already pins that — so a
present title *is* the evidence that a report was composed. It is the
same shape as the pause step's own gate: `always()` plus a data condition
proving the outputs exist.

The test pins the rule over **every** step that reads
`steps.report.outputs.`, not over one more named step, because a gate
stated by omission is the failure mode. A new `step_block` helper makes
that possible — it isolates one named step, using
`workflow_parse.run_steps`' own block-end rule so a comment introducing
the next step ends this one.

## Breakdown

- [x] Add `step_block` to `tests/test_cost_report.py` and a class pinning
      every consumer's gate — RED, three failures, on the unfixed file.
- [x] Gate the posting step in `.github/workflows/cost-report.yml`.
- [x] Apply the identical edit to
      `factory/templates/.github/workflows/cost-report.yml`.
- [x] `python3 factory_init.py update-manifest`; commit the checksum.
- [x] Battery green; payload mirror byte-identical to root.

## Notes

- 2026-08-27: `WO-0033` and `WO-0009` are cited above by name. Both have
  real rows in `docs/features/software-factory/breakdown.md`, so detector
  C is satisfied; this was checked before writing, after the previous
  run's artifact tripped that gate on a fixture id.
- 2026-08-27: the mirror is byte-identical by design, so no
  transform-aware edit was needed — the same text lands in both files and
  `update-manifest` only moved one checksum.
