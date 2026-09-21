---
stage: review
run: maintenance:a-parse-that-finds-nothing-passes
date: 2026-08-30
assumptions:
  - "No live operator input; severity is ranked here and nothing found is blocking."
  - "Open-PR recon was run before the fix was written, not after: `gh pr list --state open` intersected against every branch's diff for files matching `sweeps`. Two PRs touch tests/test_sweeps.py (#393, #339) and neither touches TestSweepsWorkflow. That check was added to this run's protocol because it was skipped on PR #410 earlier the same day and cost a disclosure comment."
---

# Review: a parse that finds nothing turns its test green

## Findings

### 1. The removed sibling assertion — minor, resolved

`test_the_triage_labels_are_ensured_before_any_sweep_runs` carried its
own `self.assertTrue(jobs)`. With the guard inside `commands()` that line
became a second statement of one claim, and this repo treats a second
owner as a defect to be either removed or explicitly excused
(ADR-0061, `one_owner.py`). Removed. The cost is honest and worth naming:
that test's guard was *visible at its call site*, and a reader of the
test alone can no longer see it. The docstring on `commands()` now says
where it went.

### 2. Guarding the helper rather than the call sites — accepted

The alternative was `jobs = self.commands(); self.assertTrue(jobs)` in
each of the two loops. Rejected: it leaves the third caller unprotected,
and the third caller is always the one that gets written later. The cost
is that `commands()` is now a helper that can fail a test, which is
slightly unusual — mitigated by saying so in the first line of its
docstring.

### 3. `curl_argv()` has the same shape — deferred, deliberately

`curl_argv()` is the other hand-rolled parse in the class, and its
consumer guards at the call site (`argv = self.curl_argv();
self.assertTrue(argv)`) rather than in the helper. That is now
inconsistent with `commands()`. It is left alone: it is guarded, so
nothing is unpinned, and moving it would be tidying adjacent code inside
a fix — which this repo's implementation discipline forbids. Worth a
follow-up issue only if a second caller of `curl_argv()` ever appears.

### 4. The demonstration edit is not a prediction — noted

The comment cites `jobs:` gaining a trailing comment. Nobody is likely to
write that. Its role is to show the parse is empty-able by an edit that
changes nothing semantically, which is what makes the failure mode silent
rather than loud. Stated this way in defect.md so a later reader does not
mistake it for a risk assessment.

## Not found

- No behaviour change to `sweeps.py`, `sweeps.yml`, or any shipped tool.
  The diff is one file under `tests/`.
- No new mirrored file, so no `factory_init.py update-manifest` and no
  detector E interaction.
- No conflict surface with #393 or #339 — their hunks sit at lines
  15–270 and 459–530; this one is at ~930–1010.

## Verdict

Ship. One file, two new tests, both mutation-killed.
