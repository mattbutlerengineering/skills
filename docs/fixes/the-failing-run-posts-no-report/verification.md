---
stage: verify
run: maintenance:the-failing-run-posts-no-report
date: 2026-08-27
assumptions: []
---

# Verification: the failing run posts no report

Eight criteria, each with the command run and its actual output.

## 1. The defect reproduces — PASS

A single malformed ledger line drives `cost_report.main` exactly as
`make cost-report` does. Every output the posting step needs is produced,
and the process still exits 1, which is what the implicit `success()`
gate reads:

```
$ python3 repro.py
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

## 2. The unfixed posting step states no gate — PASS

The new `step_block` helper isolates the step. Against the workflow as it
stands on `origin/main`, three of the four new tests fail:

```
$ git stash push -- .github/workflows/cost-report.yml factory/templates/.github/workflows/cost-report.yml factory/manifest.json
$ python3 -m unittest tests.test_cost_report.TestEveryConsumerOfTheReportStatesItsGate
AssertionError: 'always()' not found in '      - name: Post the weekly cost report issue\n        env:\n          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n          REPORT_TITLE: ${{ steps.report.outputs.title }}\n          REPORT_BODY: ${{ steps.report.outputs.body }}\n        run: gh issue create --title "$REPORT_TITLE" --body "$REPORT_BODY"'

----------------------------------------------------------------------
Ran 4 tests in 0.001s

FAILED (failures=3)
```

The failure message is the whole finding: the step's complete text, with
no `if:` in it.

## 3. The fix makes them green — PASS

```
$ python3 -m unittest tests.test_cost_report
Ran 46 tests in 0.021s

OK
```

## 4. The gated step reads as intended — PASS

The step as it now stands, read back through `step_block`:

```
      - name: Post the weekly cost report issue
        if: >-
          always()
          && steps.report.outputs.title != ''
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPORT_TITLE: ${{ steps.report.outputs.title }}
          REPORT_BODY: ${{ steps.report.outputs.body }}
        run: gh issue create --title "$REPORT_TITLE" --body "$REPORT_BODY"
```

Same folded `>-` form as the pause step below it, so the two gates read
alike.

## 5. The payload mirror is byte-identical — PASS

The workflow is mirrored verbatim, so both copies carry the same edit:

```
$ diff -q .github/workflows/cost-report.yml factory/templates/.github/workflows/cost-report.yml
identical
```

## 6. The manifest moved exactly one checksum — PASS

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ git diff --stat factory/manifest.json
 factory/manifest.json | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git diff factory/manifest.json | grep '^[+-]' | grep -v '^[+-][+-]'
-    "templates/.github/workflows/cost-report.yml": "d956ee88bb68b42e0062996e86f4602d31fc3026ad32513f5cd2340e63c3ddb8",
+    "templates/.github/workflows/cost-report.yml": "234d724ec87f0b879bdeffcf0661f48dcaaf0325c657bbd4c7e6754f0ba23bce",
```

One line, for the one file that changed. No other payload byte moved.

## 7. The full battery is green — PASS

```
$ python3 -m unittest discover tests
Ran 1348 tests in 16.259s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

1348 = the 1344 on `origin/main` plus this run's four. Detector E — the
manifest/payload gate this change is most likely to trip — is inside that
`gates: 0`.

## 8. The one-owner pre-pass is unchanged — PASS

```
$ python3 one_owner.py
one-owner: 9 problem(s)
$ python3 one_owner.py | grep -i 'cost_report\|cost-report'
one-owner: budget_guard.py:55 CONTINUE and cost_report.py:44 CONTINUE state the same value — one fact, one owner
```

Nine, the same count as before this run. One of the nine does name
`cost_report.py`: the `CONTINUE` constant it shares with
`budget_guard.py`. That finding is pre-existing on `origin/main` and
untouched here — `cost_report.py` is not in this run's diff at all — and
the pre-pass is deliberately not a gate.

## Not verified

- **The workflow was not executed.** GitHub Actions evaluates `if:`
  expressions, and nothing offline can prove that
  `always() && steps.report.outputs.title != ''` schedules the step after
  a failed predecessor. What is verified is the file's text and the
  reasoning it mirrors from the pause step three lines below, whose
  identical `always()` construction is already in production. Confirming
  the runtime behaviour needs a real failing `cost-report` run.
- **`gh issue create` was not run.** This module never shells out to gh
  (the compute/mutate boundary); the posting step's own behaviour with a
  populated title and body is unchanged by this run.
- **`FACTORY_PAUSE_TOKEN` is still unset**, so the pause step would still
  exit 1 on a breach. Out of scope and stated in the brief — but it is
  why the missing report mattered so much: with no pause and no issue,
  the failing week left a red run as its only trace.
- **The other five free workflows were not audited** for the same
  implicit-`success()` shape. `cost-report.yml` was examined because its
  compute half advertises a fail-closed path; whether `sweeps.yml`,
  `gate-digest.yml`, `validator.yml`, `design.yml` or `charter-replay.yml`
  have consumers gated by omission is an open question, not a claim.
