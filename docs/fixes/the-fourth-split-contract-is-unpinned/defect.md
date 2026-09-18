---
stage: diagnose
run: maintenance:the-fourth-split-contract-is-unpinned
date: 2026-08-30
assumptions: []
---

# Defect: the fourth $GITHUB_OUTPUT split contract has no bridge

## The convention

Three tools write `$GITHUB_OUTPUT` keys that a workflow reads back by
literal name. The repo calls this a **split contract** and pins each one
with a lockstep test that derives both sides:

| Tool | Workflow ref | Pinned by |
|---|---|---|
| `assembler.run_resolve` | `steps.resolve.outputs.*` | `test_assembler.TestWorkflowOutputLockstep` |
| `validator` | `steps.claim.outputs.*` | `test_validator` |
| `cost_report.run_report` | `steps.report.outputs.*` | `test_cost_report.TestWorkflowOutputLockstep` |

The assembler test says why:

> a renamed key breaks here, in CI, instead of silently expanding to an
> empty string in the dispatch step

## The fourth site

`gate_digest.run_daily` writes `changed`, and `gate-digest.yml` reads it:

```yaml
      - name: Post the digest and capture gate latency
        id: digest
        run: make gate-digest
      - name: Commit the new gate-latency rows
        if: steps.digest.outputs.changed == 'true'
        run: |
          git add docs/factory/costs.jsonl
          git commit -m "chore(factory): gate-latency rows (gate-digest)"
          git push
```

Nothing pins it. The only occurrence of `steps.digest.outputs` anywhere
in the repo is that one line of YAML:

```
$ grep -rn "steps.digest.outputs" tests/ .github/
.github/workflows/gate-digest.yml:53:        if: steps.digest.outputs.changed == 'true'
```

## What a rename costs

GitHub Actions substitutes the empty string for an unresolvable
reference — it does not error. So `'' == 'true'` is false, the commit
step is skipped, and:

- `run_daily` still computes gate latency and **appends the rows to
  `docs/factory/costs.jsonl`** in the runner's checkout
- nothing commits them, so they die with the runner
- the digest issue still posts, so the workflow looks like it worked
- the run is **green**

Every day. The cost ledger silently stops receiving gate-latency rows,
and ADR-0034's monthly circuit breaker windows on exactly those rows.

This is the same failure the three pinned sites are protected from. It
is the one that was left out.

## Why it was missed

Nothing derives the list of split contracts either — each of the three
tests was written next to the tool it covers, so "which tools have this
contract" lives only in the reader's head. `gate_digest` grew its
`changed` output later (WO-0017/ADR-0041) and no one went back.

The generalisable version of this — a check that finds every
`steps.<id>.outputs.<key>` in every workflow and demands a bridge — is
noted in `review.md` §4 as a real idea and deliberately not built here.
