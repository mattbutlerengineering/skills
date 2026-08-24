---
stage: capture
run: maintenance:quoted-token-is-not-a-claim
date: 2026-08-23
re-entry: architect
assumptions: ["re-entry is architect, not implement: the change amends ADR-0057, which wrote the gate being changed, so the decision needs recording before code.", "Severity is judged on observed CI failures, not on argument: three PRs failed the same job on one day and each was worked around by degrading its own record. The prose-provenance half of the seed is explicitly NOT claimed as a defect here — it is a convention question."]
---

# Defect: a quoted work-order token makes the PR a work-order PR

Origin: backlog seed `docs/backlog.md:38` (from: session:2026-08-21),
claimed as `(claimed: maintenance:quoted-token-is-not-a-claim)`. Tracking
issue #331.

## Defect

`validator.run_lifecycle` (validator.py:386) gates its uncited skip on the
raw body:

```python
        if uncited == "skip" and not WO_TOKEN.findall(body):
            return []
```

Any work-order token anywhere in the body — prose, fenced code block,
blockquote — makes `WO_TOKEN.findall` truthy, so the skip does not apply
and the unresolved citation is reported as a problem. The PR is judged a
malformed work-order PR.

`cited_work_order` (validator.py:233) already knows better. Its own
docstring names the case:

> NOT "the first WO token in the body": the body is author-controlled
> prose that legitimately NAMES other work orders — a blocking edge, **a
> quoted Accept line** — and taking the first token would flip the WRONG
> issue's lifecycle label on merge.

Its resolution is structural and correct: the work order a PR implements
is the one whose breakdown row is mirrored to an issue the PR closes. The
gap is what happens when *nothing* resolves. That outcome means one of two
very different things — "this PR claims a work order and got it wrong" or
"this PR merely mentions work orders" — and the gate cannot tell them
apart.

Expected: a body whose only tokens are quoted is a body that cites no work
order. Observed: it is a malformed work-order PR and the job fails.

## Reproduction / Evidence

The gate, driven with the body of PR #330 (whose tokens are all inside a
fence or a blockquote):

```
  tokens found by the current gate: ['WO-0018', 'WO-0018']
  so `not WO_TOKEN.findall(body)` is False -> the skip does NOT apply
  every one of those tokens is inside a fence or a blockquote
```

## Blast radius — three failures in one day, all worked around by redaction

- **PR #328** quoted a malformed breakdown row inside a fence, to show the
  defect that run was fixing. `needs-review-label` failed.
- **PR #330** quoted a validator error message inside a fence and a test
  docstring inside a blockquote. `needs-review-label` failed.
- Both were fixed by writing `WO-00xx` so no token matches — a workaround
  that degrades the record. A PR about breakdown rows cannot quote one.

The pattern is not incidental to those two runs: any PR whose subject is
the dispatch plane will quote its identifiers.

## What is NOT claimed

**PR #306 is a different defect and this run does not fix it.** Its token
was in prose — `introduced by 663265c (WO-nnnn)`, a deliberate archaeology
note crediting the commit that caused a regression. Nothing about fences
or quoting separates that from a genuine claim; doing so needs a
convention, and the seed proposes one (`Implements: WO-####` read in
preference to a bare-token scan).

That convention is deliberately out of scope. It obliges every future
work-order PR body, including the ones the assembler and the daily
improvement routine generate, to carry a new trailer — an external
commitment with a migration, which the autorun rules say to surface rather
than assume. So the seed is claimed by this run but only half-closed, and
the closing artifact says so rather than letting the claim imply more.

## Why the current gate exists

ADR-0057 wrote it, deliberately: "the malformed-citation case is unchanged
and stays loud on both legs... `--uncited skip` already preserves it: the
relaxation is gated on `not WO_TOKEN.findall(body)`." That reasoning is
sound and this run does not dispute it — a body that *claims* an
unresolvable work order should still be loud. What it disputes is that a
quoted token is a claim. Closing this therefore amends ADR-0057 rather
than reversing it.
