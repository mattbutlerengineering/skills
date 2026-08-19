---
stage: verify
run: maintenance:toolsmith-mine-pr-permissions
date: 2026-08-18
assumptions:
  - "The criteria list was assembled from three sources rather than a prd.md/breakdown.md pair, because this run is re-entry: implement and has neither: the five bullets plus the live check under autorun-brief.md's Success criteria, the three Accept: lines on defect.md's work items, and the standing criterion that the captured defect is actually resolved. Where the brief and defect.md disagree, defect.md is followed and the disagreement is recorded below under 'Where defect.md corrected the brief'."
  - "Two criteria are recorded as NOT YET VERIFIABLE rather than routed back to Implement. The stage skill routes failures to Implement; neither of these is an implementation failure. Both are gated on a post-merge workflow_dispatch that defect.md records as a Ship obligation, and this stage was instructed not to trigger anything. Recording them as passes would be the dishonesty the run's own brief names."
  - "The RED reproduction was run against a full non-invasive copy of the working tree in the session scratchpad, with only .github/workflows/toolsmith-mine.yml replaced by `git show main:` output. No git stash, no worktree add, no mutation of the repository working tree. The five mutants under 'Testing the test' live in that same scratch copy and nowhere else."
  - "`python3 factory_init.py update-manifest` was run in the real working tree, as the Accept criterion and the stage instruction both require. It was a no-op — `git status --porcelain` is empty after it — so the instruction not to modify any source file, test, or workflow holds."
  - "The sibling survey and the tracker read (#294's state) were re-walked read-only to adjudicate the competing predictions. Nothing was triggered, created, edited, pinned, or unpinned."
  - "Recursive greps were avoided: `.claude/worktrees/` holds 20 stale untracked agent checkouts (46M) that pollute recursive search. Every search below is `git grep` or a path-scoped `grep` against a named file, so untracked checkouts cannot contribute a hit."
---

# Verification: toolsmith-mine.yml grants pull-requests: read

## Summary

**7 PASS, 0 FAIL, 2 NOT YET VERIFIABLE.** Every criterion that can be
settled offline is settled and green: the grant is on the surface the tool
reaches, the mirror and manifest are coherent and idempotent, the diff on
the workflow is literally one added line with no deletions, the full
battery is green, and the regression test's RED was independently
re-derived rather than taken from the commit message. What cannot be
settled here is the pair that matters most: **the live check, and with it
the claim that the defect is actually resolved.** Both are gated on a
post-merge `workflow_dispatch` that belongs to Ship. Five findings on the
regression test's reach are recorded — one of them a real false-pass gap —
none of them blocking.

The verdict in one sentence: the fix is correct, coherent, and pinned; it
is not yet *proven*, and the proof is a Ship obligation, not an offline
one.

## Where defect.md corrected the brief

`defect.md` re-verified four of the brief's claims at HEAD and corrected
them. Each is confirmed below rather than accepted:

1. **The payload byte-mirror pin's home.** The brief attributes it to
   `tests/test_factory_init.py`; `defect.md` (*Ruled out*) puts it at
   `tests/test_gates.py:1887`. Confirmed — `tests/test_gates.py:1887-1889`
   is `assertEqual(PAYLOAD_TOOLSMITH_MINE_WORKFLOW.read_bytes(),
   TOOLSMITH_MINE_WORKFLOW.read_bytes())`, a real-repo comparison, while
   `tests/test_factory_init.py`'s only mention of the file is as a member
   of `EXPECTED_RELS` (`:41`), a set of manifest keys asserted against a
   **minimal fixture repo** at `:149`. The brief's attribution is wrong;
   `defect.md` is right, and its instruction not to add a second
   byte-mirror test was followed.
2. **The pin prediction.** Adjudicated in full under *The two competing
   predictions* below. `defect.md` is the one the code supports.
3. **The `_change_requests` call site.** The brief says the listing is
   "reached from `_change_requests` at `:152`"; `defect.md` refines it to
   the function at `:152`, the call at `:156`. Confirmed — `def
   _change_requests` is `rejection_mining.py:152`, the `gh_read(...)` call
   is `:156-157`.
4. **The post-merge dispatch's status.** The brief lists it as in-scope
   item 4, which reads as a fourth work item; `defect.md`'s first
   assumption reclassifies it as a Ship obligation, because a box that can
   only be ticked after merge would stall the run at Implement forever.
   Followed — it is verified below as *not yet verifiable*, not as an open
   work item.

## Criteria & evidence

### Criterion 1 (brief) — the workflow grants `pull-requests: read`, and its payload twin is byte-identical to it

- Check: read the block at HEAD; `diff` and `cmp` root against payload.
- Evidence:
  ```
  === occurrences of 'permissions:' in the target workflow ===
  24:permissions:

  === full permissions block at HEAD ===
  permissions:
    contents: read
    issues: write
    pull-requests: read

  === byte-identity root vs payload ===
  (diff empty: byte-identical)

  === cmp ===
  (cmp: identical)
  ```
  Exactly one `permissions:` line exists at column 0 in the file, which is
  what makes the test's extraction unambiguous (see *Testing the test*).
- Result: **PASS**

### Criterion 2 (brief) — `python3 factory_init.py update-manifest` leaves the tree clean, and detector E is green

- Check: run `update-manifest` in the real tree, then `git status
  --porcelain`; run the detector suite.
- Evidence:
  ```
  === update-manifest ===
  factory-init: 0 problem(s)
  === git status after update-manifest ===
  (end of git status — empty above means clean)
  ```
  ```
  gates: 0 problem(s)
  === gates EXIT 0 ===
  selftest: ok
  === selftest exit: 0 ===
  ```
  Regeneration is idempotent: it reported no problems and produced no
  diff, so the committed `factory/manifest.json` hash
  (`d1629e967ad32f449dbeef3f941b0e0bc70ab57d2667bf0cfb2090d1b50e7590`) is
  the one the current payload actually hashes to.
- Result: **PASS**

### Criterion 3 (brief) — a regression test that fails against the pre-fix file and passes after, watched failing

This is the centerpiece, and the commit message was **not** trusted for
it. `d70216b`'s body quotes a failure; that quote is an assertion until
someone else sees it. The reproduction below is independent.

- Check: rsync the working tree into a scratch copy (excluding `.git`,
  `.claude`, `__pycache__`), overwrite only the workflow with `git show
  main:.github/workflows/toolsmith-mine.yml`, confirm the scratch copy
  still carries the **post-fix test**, then run the new class there. The
  repository working tree was never touched.
- Evidence — the pre-fix state in the scratch copy:
  ```
  --- pre-fix workflow permissions block in scratch ---
  24:permissions:
  25-  contents: read
  26-  issues: write
  27-
  28-concurrency:
  --- confirm scratch test file is the HEAD (post-fix) test ---
  278:class TestWorkflowPermissions(unittest.TestCase):
  304:        self.assertIn("pull-requests: read", self.permissions())
  ```
- Evidence — **the RED, re-derived**:
  ```
  test_the_pr_listing_surface_is_granted (tests.test_rejection_mining.TestWorkflowPermissions.test_the_pr_listing_surface_is_granted) ... FAIL

  ======================================================================
  FAIL: test_the_pr_listing_surface_is_granted (tests.test_rejection_mining.TestWorkflowPermissions.test_the_pr_listing_surface_is_granted)
  ----------------------------------------------------------------------
  Traceback (most recent call last):
    File "/private/tmp/claude-501/-Users-mbutler-github-skills/a9a95e83-c06e-41ff-80f5-637d2df6a7b3/scratchpad/prefix-repro/tests/test_rejection_mining.py", line 304, in test_the_pr_listing_surface_is_granted
      self.assertIn("pull-requests: read", self.permissions())
      ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  AssertionError: 'pull-requests: read' not found in '  contents: read\n  issues: write\n'

  ----------------------------------------------------------------------
  Ran 1 test in 0.002s

  FAILED (failures=1)
  === EXIT: 1 ===
  ```
  This matches `d70216b`'s recorded failure line for line, including the
  assertion message `'pull-requests: read' not found in '  contents:
  read\n  issues: write\n'` — only the file path differs, because the run
  is in the scratch copy. The commit message's claim is now corroborated
  by an independent observation rather than believed.
- Evidence — **the GREEN**, same test, real tree at HEAD:
  ```
  test_the_pr_listing_surface_is_granted (tests.test_rejection_mining.TestWorkflowPermissions.test_the_pr_listing_surface_is_granted) ... ok

  ----------------------------------------------------------------------
  Ran 1 test in 0.001s

  OK
  === EXIT: 0 ===
  ```
- Result: **PASS** — fails before, passes after, both observed here.

### Criterion 4 (brief) — the full battery is green

- Check: all three commands, run in the repository at HEAD.
- Evidence:
  ```
  Ran 1272 tests in 31.844s

  OK
  ```
  ```
  lint: 0 problem(s) across 23 skills
  === EXIT 0 ===
  ```
  ```
  gates: 0 problem(s)
  === gates EXIT 0 ===
  selftest: ok
  === selftest exit: 0 ===
  ```
  All three summary lines match the required shapes: `lint: 0 problem(s)`,
  `gates: 0 problem(s)`, `selftest: ok`.
- Result: **PASS**

### Criterion 5 (brief) — the live check: a post-merge `workflow_dispatch` run whose output has no `rm: gh pr list failed: …` line

- Check: **none performed.** The fix is unmerged (branch
  `toolsmith-mine-pr-permissions`, 2 commits ahead of `main`), and
  triggering the workflow is the Ship obligation `defect.md` records under
  *Release obligation*. This stage was instructed not to trigger anything,
  and did not.
- Evidence: the absence of evidence, stated plainly. Nothing was
  dispatched; no log exists to read.
- What would settle it: merge the run's PR to `main`, then `gh workflow
  run toolsmith-mine.yml`, then read the completed run's log in full. The
  criterion is satisfied **iff** the string `rm: gh pr list failed:` does
  not appear in it. Ship must quote the log and name every problem that
  remains, saying for each whether it is this run's.
- Result: **NOT RUN** — the workflow is unmerged and the dispatch is
  Ship's obligation, so this stage could not execute the check. Recorded
  as a finding, not a pass.

### Criterion 6 (defect.md, work item 1) — the new test fails on the pre-fix workflow, and its failure output is recorded verbatim for Verify to quote

- Check: the re-derivation under Criterion 3, plus reading `d70216b`'s
  message body for the recorded verbatim output.
- Evidence: the same RED reproduced under Criterion 3, re-quoted here so
  this criterion carries its own evidence rather than pointing at a
  neighbour's:
  ```
  FAIL: test_the_pr_listing_surface_is_granted (tests.test_rejection_mining.TestWorkflowPermissions.test_the_pr_listing_surface_is_granted)
  ----------------------------------------------------------------------
  Traceback (most recent call last):
    File ".../scratchpad/prefix-repro/tests/test_rejection_mining.py", line 304, in test_the_pr_listing_surface_is_granted
      self.assertIn("pull-requests: read", self.permissions())
  AssertionError: 'pull-requests: read' not found in '  contents: read\n  issues: write\n'

  Ran 1 test in 0.002s

  FAILED (failures=1)
  ```
  It matches what `d70216b`'s message body records, line for line, with
  only the path differing. The Accept criterion asks for two things — a
  real failure and a preserved record of it — and both hold.
- Result: **PASS**

### Criterion 7 (defect.md, work item 2) — `git diff` on the workflow is exactly one added line, and the test from the previous item passes

- Check: `git diff main..HEAD --numstat` and the diff itself, scoped to
  the workflow.
- Evidence:
  ```
  === NUMSTAT (workflow only) ===
  1	0	.github/workflows/toolsmith-mine.yml
  === DIFF (workflow only) ===
  @@ -24,6 +24,7 @@ on:
   permissions:
     contents: read
     issues: write
  +  pull-requests: read

   concurrency:
     group: toolsmith-mine
  ```
  `1 0` is literally one insertion and zero deletions. No command was
  added to the YAML — the file still names none, so a stamped product repo
  runs the same file, which is the constraint the brief and `defect.md`
  both set. The test passes (Criterion 3's GREEN).
- Result: **PASS**

### Criterion 8 (defect.md, work item 3) — re-running `update-manifest` leaves the tree clean, `TestLockstep`'s byte-mirror pin passes, and the full battery is green

- Check: Criterion 2's idempotence run, plus the named test by itself,
  plus Criterion 4's battery.
- Evidence:
  ```
  === TestLockstep payload mirror pin ===
  test_the_payload_toolsmith_workflow_is_the_mirror_of_this_repo_s (tests.test_gates.TestLockstep.test_the_payload_toolsmith_workflow_is_the_mirror_of_this_repo_s) ... ok

  ----------------------------------------------------------------------
  Ran 1 test in 0.001s

  OK
  ```
  Manifest regeneration left `git status --porcelain` empty; the battery
  is green on all three commands.
- Result: **PASS**

### Criterion 9 (standing) — the defect in defect.md is actually resolved

`defect.md`'s target state has four parts. Three are demonstrated above:
the grant is present, the twin and manifest are regenerated, and a test
pins the grant. The fourth — "a dispatched run's log shows the `gh pr
list` failure gone" — is Criterion 5, and it is not verifiable here.

The honest split:

- **The cause is addressed.** `rejection_mining.py:57` sends `("pr",
  "list", "--state", "all", "--json", "number,state,body,reviews")`
  through `cli.gh_read` from `_change_requests` (`:152`, call at
  `:156-157`). GitHub's refusal named `repository.pullRequests`. The
  workflow now grants `pull-requests: read` on the surface that call
  reaches. Cause, refusal, and grant line up on all three sides.
- **The resolution is not demonstrated.** No offline check can show the
  refusal gone; only the dispatched run can. Sufficiency of `read` is the
  specific unproven step — see *Not verified*.
- Result: **NOT RUN.** The only check that would settle it is the
  dispatched run, which this stage may not trigger. Not a failure —
  nothing found here contradicts the fix — but not a pass either, and it
  must not be reported as one.

## Testing the test

The stage instruction asks whether the assertion actually pins what it
claims. It claims the grant is **in the body of the top-level
`permissions:` block**, not merely somewhere in the file. Five mutants
were built in the scratch copy and run against the unmodified test.

The interface under test is the `permissions()` helper: it takes
`lines.index("permissions:")` — an exact match, so only a column-0
occurrence qualifies — and collects following lines until the first
non-empty line whose first character is not whitespace.

| # | Mutant | Result | Reading |
|---|--------|--------|---------|
| A | grant moved out of the top-level block into a **job-level** `permissions:` under `runs-on` | FAIL | Catches it — this is the claim's substance |
| B | grant spelled `pull-requests: **write**` | FAIL | Catches it, but see the over-pin note |
| C | grant present but **commented out** inside the block (`  # pull-requests: read`) | **passes — false pass** | Real gap |
| D | pre-fix block, with the exact string added as a comment **elsewhere in the file** | FAIL | Catches it — this is what block-scoping buys over a whole-file `assertIn` |
| E | top-level block **removed entirely** | ERROR (`ValueError`) | Still red, but as an error, not a named failure |

Mutant A, verbatim:
```
34-    runs-on: ubuntu-latest
35:    permissions:
36-      pull-requests: read
...
AssertionError: 'pull-requests: read' not found in '  contents: read\n  issues: write\n'
FAILED (failures=1)
```

Mutant C, verbatim:
```
24:permissions:
25-  contents: read
26-  issues: write
27-  # pull-requests: read
--- result ---
.
----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
```

Mutant E, verbatim:
```
ValueError: list.index(x): x not in list
FAILED (errors=1)
```

**What it catches:** the grant being dropped from the block (the actual
regression); the grant being moved to a job-level block; the string
existing anywhere in the file but not in the block. That last one is the
non-trivial property, and it is the reason the helper exists rather than a
bare whole-file `assertIn` — `tests/test_charter_replay.py:640`'s
precedent (`assertIn("permissions:\n  contents: read", text)`) is
whole-file, and this test is strictly stronger than it.

**What it does not catch:** a commented-out grant inside the block (C).
`assertIn` on a substring cannot tell `  pull-requests: read` from `  #
pull-requests: read`. This is a narrow gap — it needs someone to comment
the line out rather than delete it — but it is real, and the test would
stay green through it while the workflow was broken again.

**Two over-pins, both deliberate rather than defective:** the test
rejects `pull-requests: write` (B), which is a strictly stronger and
entirely sufficient grant, and it rejects a job-level grant (A), which
GitHub Actions would honor for that job. Both rejections follow from the
claim `defect.md` states — "the grant has to be *in the block*" — so
neither is a defect in the test. They are worth knowing, because a future
change that legitimately needs `write` will have to touch this assertion,
and the assertion carries no comment saying so.

**Mutant E's shape is a small wart.** Deleting the block entirely raises
`ValueError: list.index(x): x not in list` rather than failing with a
message that names the missing grant. The suite still goes red, which is
what matters; the diagnostic is just poorer than the failure mode it is
most likely to meet.

## The two competing predictions about the dispatched run

The brief predicts the pin error fires again, 2 problems drop to 1, and
the run stays red. `defect.md` predicts no pin line at all, and possibly a
green run at 0 problems. The code was read directly.

**`defect.md`'s prediction is the one the code supports**, conditionally.

`_post_queue` (`rejection_mining.py:164`) has two paths, and only one of
them turns a pin refusal into a problem string:

```
        try:
            run(["issue", "pin", str(existing)])
        except GH_FAILURES:
            pass
        return
```

That is `rejection_mining.py:176-180` — the **edit** path, taken when
`existing is not None`. The refusal is swallowed outright; no problem
string is appended, and `GH_FAILURES` is `cli.CLI_FAILURES` =
`(subprocess.CalledProcessError, OSError)` (`cli.py:50`), which is exactly
what a refusing `gh` raises. Only the **create** path appends `rm: gh
issue pin failed: {gh_detail(err)}` — and the create path is what ran on
2026-08-17, because the queue issue did not exist yet.

`run_mine` picks the path at `:223-226`: it scans the open issues from the
`gh issue list --state all` result for the lowest-numbered one whose body
`startswith(MARKER)`, and passes that number as `existing`.

The condition, checked read-only against the tracker rather than assumed:

```
{"body_head":"<!-- factory-toolsmith-queue -->\nToolsmith queue — mined rejections — 2026-08-17","number":294,"state":"OPEN","title":"Toolsmith queue — mined rejections"}
```

#294 is open and its body starts with the marker, so the lookup finds it
and the next run takes the edit path. Under that state the pin refusal is
silent and `rm: gh issue pin failed: …` does not appear. The brief's
prediction would only hold if #294 were closed, or its body no longer
started with the marker, between now and the dispatch — in which case the
create path fires again and the pin line returns.

**Neither a green nor a red conclusion is self-proving, and Ship must not
treat either as the criterion.** The criterion is the absence of one
specific line, `rm: gh pr list failed:`. A green run at 0 problems does
not prove it — a run that failed earlier for an unrelated reason could
also print no such line. A red run does not disprove it — the swallowed
pin, or something else entirely, can hold the run red while the listing
succeeds. Ship reads the log and names every remaining problem
individually. Reporting the conclusion instead of the log is the failure
mode `defect.md` names and the one this run is most likely to die of.

One consequence worth carrying forward: under `defect.md`'s prediction the
pin attempt keeps failing **silently** every week, so #294 stays unpinned
until a human acts. The pin cap remains the operator's console call — three
issues are pinned (#172 and #178 share the title "Factory gate queue",
#181 is "Factory improvement journal"), which is GitHub's cap. **Nothing
was unpinned, and nothing should be by anyone but the operator.**

## Failures

**None.** No criterion checked here failed, and no evidence gathered here
contradicts the fix. The two unsettled criteria (5 and 9) are gaps in what
can be proven offline, not failures of the implementation, and nothing
routes back to Implement.

## Not verified

Stated explicitly, because a silent gap reads as coverage.

1. **That `pull-requests: read` is *sufficient* for what the listing
   asks.** This is the single most important unproven claim in the run.
   `PR_ARGS` (`rejection_mining.py:57`) is `("pr", "list", "--state",
   "all", "--json", "number,state,body,reviews")`, sent through
   `cli.gh_read` with `window=LIST_WINDOW` (1000), which appends `--limit
   1000`. Every requested field — `number`, `state`, `body`, `reviews` —
   is read-only, and `--state all` widens the listing rather than mutating
   anything, so `read` *should* suffice. But GitHub's scope semantics are
   the other side of a network call this stage did not make, and the
   `reviews` field in particular resolves through a nested lookup whose
   scope requirements are not documented in this repository. **The only
   proof is a dispatched run.** If `read` turns out to be insufficient,
   the symptom is the identical `Resource not accessible by integration
   (repository.pullRequests)` line and the fix is `write`, which
   `assembler.yml:56` and `validator.yml:101` both already use.
2. **The live check itself** (Criterion 5) — nothing dispatched, no log
   read. Settled only by the post-merge `workflow_dispatch`.
3. **That the defect is resolved end to end** (Criterion 9) — follows from
   1 and 2.
4. **CI on the PR.** The battery was run locally on macOS (Darwin 25.5.0)
   at HEAD. No PR exists yet, so no CI run was observed. The brief makes
   green CI on the PR a non-waivable release condition; that is Ship's to
   confirm.
5. **The workflow's YAML validity as GitHub parses it.** The assertion is
   over file text — stdlib-only, no YAML parser in the repository, which
   is a constraint the brief and `defect.md` both record. Nothing here
   proves GitHub accepts the edited file; the one-line insertion into an
   existing block makes that a low risk, not a checked one.
6. **The other three permissions-relevant workflows were not re-surveyed
   from scratch**, only confirmed against `defect.md`'s survey with a
   single scoped `git grep`:
   ```
   .github/workflows/assembler.yml:56:      pull-requests: write
   .github/workflows/toolsmith-mine.yml:27:  pull-requests: read
   .github/workflows/validator.yml:101:      pull-requests: write
   ```
   This confirms the three grants exist; it does not re-derive which tools
   reach which gh surfaces. `defect.md`'s sibling survey was accepted on
   that point.
7. **The deferred permissions drift detector was not built and not
   evaluated.** It is out of scope by decision, and the seed line landed in
   `docs/backlog.md` on this branch (one added line, confirmed in the
   diff), which discharges `defect.md`'s second assumption.
8. **`.claude/worktrees/` was excluded from every search.** It holds 20
   stale untracked agent checkouts (46M) whose copies of these same files
   would produce false hits in any recursive grep. Every search in this
   artifact is `git grep` (tracked files only) or a path-scoped `grep`
   against one named file. No conclusion here rests on a recursive search.

## Handoff

No failures route back to Implement. Next stage is **Review**, which
`defect.md` scales to a small blast radius. Review and Ship both inherit
two obligations from this artifact:

- **Ship must discharge the dispatch and read the log**, not the
  conclusion — Criteria 5 and 9 are open until it does.
- **The operator's pin-cap decision must appear in the final report**, and
  no one unpins anything on this run's behalf.
