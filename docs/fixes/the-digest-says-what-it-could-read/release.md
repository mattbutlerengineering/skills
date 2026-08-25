---
stage: ship
run: maintenance:the-digest-says-what-it-could-read
date: 2026-08-25
released: prepared-not-executed
assumptions:
  - "Prepare-and-stop. The autorun brief carries no release authorization, so this stage pushed the branch and opened the PR — the same outward actions the four preceding maintenance runs took — and executed no merge, no tag, no deploy. Merging is a human decision and ADR-0036 clause 2 requires a non-authoring reviewer to re-execute verification and record it on the PR, which this run cannot satisfy for its own work."
---

# Release: prepared, not executed

**PR:** #347 — `fix(gate-digest): the daily digest states what it could read`
**Branch:** `agent/digest-says-what-it-read` (from `origin/main` at `622e7c0`)
**Closes:** #346

## Pre-flight

| Check | Result |
|---|---|
| Verification green | `verification.md`, seven criteria, no unresolved failures |
| No unfixed critical review findings | `review.md` — none critical; two minors fixed in-run |
| No secrets in the diff | scanned for token/key/PEM shapes — no match |
| Configuration in the target environment | none added; `gate-digest.yml` unchanged, same `GITHUB_TOKEN` and same `issues: write` |
| Migrations / data changes | none. The cost-ledger path is untouched and its dedup identity is unchanged |
| Payload and manifest in lockstep | `python3 -B factory_init.py update-manifest`, exactly two files moved, detector E green |

## Rollback

Concrete, in the order they would be run:

```
git revert <merge-sha> -m 1
python3 -B factory_init.py update-manifest   # re-pin the reverted mirror
python3 gates.py                             # detector E must be green
git push
```

The reverted state is the current behaviour of the daily digest, which
has been running since WO-0017. Nothing about the ledger, the workflow,
or the pinned issue's identity changes, so a revert costs one digest
cycle of the old rendering and nothing else. #178 is never deleted or
recreated by this change or its revert.

## CI

Recorded after the push; see the "Post-push" section below.

## Not executed, deliberately

- **The merge.** Autorun stops at Ship absent explicit release
  authorization, and this PR is agent-authored: ADR-0036 clause 2 needs a
  non-authoring reviewer to re-execute verification and record it.
- **Any change to #178 itself.** The digest issue is rewritten only by
  the scheduled workflow. This run read nothing from it and wrote nothing
  to it.
- **Any factory tool in a mutating mode.** No `rejection_mining mine`, no
  sweep filing, no digest posting. Every `gh` call this run made was a
  read, except creating intake #346 and opening PR #347.

## Carry-forward for whoever merges

1. **The first real observation is the next `gate-digest.yml` firing**
   (daily, 05:17 UTC). Everything here is verified against injected
   fakes. Worth opening #178 once after that run and confirming the body
   is unchanged in shape — no coverage sentence should appear, because
   this repo's ~150 issues are nowhere near the 1000-entry window, and no
   item should carry the unreadable mark unless a timeline actually
   failed.
2. **`factory/manifest.json` will conflict** with any of #320, #326,
   #328, #333, #341, #343 that merges first. The resolution is
   regeneration, not a hand-merge: take either side, then run
   `python3 -B factory_init.py update-manifest` and commit.
3. **The `-B` flag is load-bearing until #320 lands.** Without it,
   `update-manifest` can pin `factory/templates/**/__pycache__/*.pyc`
   into the manifest — files `.gitignore` excludes, so detector E then
   passes only in the checkout that generated it.

## Post-push: an intermittent suite failure, recorded rather than swept

One suite invocation during this run reported `FAILED (failures=1)`.
Every subsequent run passed: six consecutive clean runs immediately
after, plus three more with a same-length test-file edit immediately
preceding each, deliberately trying to induce it. The failing test's
identity was **not captured** — the invocation's output was tail-
truncated, and by the time it was re-run the failure was gone.

This is the second occurrence across two consecutive runs (the first is
recorded in `docs/fixes/run-discovery-ignores-open-prs/release.md`). Both
happened on the first suite invocation after a batch of test-file edits.

The leading hypothesis is the repo's documented stale-bytecode trap: a
same-second, same-length edit leaves a `.pyc` that Python still considers
valid, so a test runs against bytecode that no longer matches its source.
That would produce exactly this signature — a failure against a file
whose content is provably correct, gone on the next run. It is a
hypothesis, not a finding: the induction attempt above did not reproduce
it, and without the failing test's name it cannot be confirmed.

Two things follow, neither of which this run performed:

- Suite invocations that immediately follow file edits should use
  `python3 -B` (or clear `__pycache__` first), which makes the
  hypothesised class impossible.
- Suite output should be captured in full rather than tailed, so the next
  occurrence keeps the test's identity.

Seeded at Operate. It is recorded here rather than dismissed because "it
passed on retry" is precisely how a real flake gets lost, and this is now
a pattern rather than an incident.
