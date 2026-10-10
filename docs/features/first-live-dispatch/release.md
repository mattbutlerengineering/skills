---
stage: ship
run: feature:first-live-dispatch
date: 2026-10-10
assumptions:
  - "Production for this change is main: assembler.yml goes live on this repo the moment it is merged (the next wo:ready-for-agent label runs it), and stamped repos receive the template mirror on their next factory-init stamp or update. Release authorization is prepare-and-stop (autorun-brief.md), so this stage pushes the branch and opens one PR for the operator, as every earlier resume did, and stops there: no merge, tag, deploy, gate label or workflow dispatch."
  - "This run has no tracker seeding. Detector B needs a Closes #N line, so this stage follows PR #606's precedent (this run's previous resume): one plain anchor issue, created with the same type:chore work-type label #605 carried at creation. It is not a wo: lifecycle label and not #178 or #181."
  - "The PR body names none of rows 0128 to 0132 by their work-order tokens. Those rows have no tracker mirror, and the validator's needs-review-label job fails a PR that cites an unmirrored order (pipeline-board release.md, step 4). The body carries a No work order: line instead."
---

# Release: first live dispatch, ADR-0077 job split (prepare-and-stop)

## Readiness

**Ready to hand to the owner's merge gate. Not merged.** No Critical is
open. Review's 2026-10-02 Critical (the allowlist was not a push
boundary) is fixed by WO-0128 and WO-0129 (PRD-0003 §Success criteria).
The re-review's new Critical R1 (a bundle tag reaching `main`) is fixed
by WO-0130 (PRD-0003 §Success criteria) and replay-tested. The Majors
are either fixed (R2, WO-0131, PRD-0003 §Success criteria) or routed
by the owner's decision, recorded below. Four minors (R5, R6, R7 and
2026-10-02 finding 5) are deferred, with review.md's reasons. Finding 6
is deferred and re-judged there.

Verification stands as review left it. Five criteria PASS on evidence
this change does not touch. Criterion 2 is FAIL, routed below.
Criteria 3, 4, 6 and 10, and the inert-label half of 7, are **not
re-proven** for the shipped workflow until a live dispatch runs. The
new workflow is unproven on a runner. It has static, local and
replayed evidence only.

## Owner decisions (2026-10-10)

These are decisions the owner (Matt) took on 2026-10-10 by answering
direct questions in this session. They are not assumptions.

1. **Finding 4 / R3, the validator's `review` job running the agent's
   `Makefile` beside `pull-requests: write` and the reviewer PAT.**
   Routed to a **separate follow-up run** that splits `validator.yml`'s
   `review` job the way ADR-0077 split the assembler. A read-only job
   runs the PR's code and produces a result. A separate job holds the
   PAT, consumes only that result, and runs no PR code. This branch
   ships with R3 **recorded open and routed**, not fixed.
2. **Major 2, ADR-0074's re-emitted gate rows (gate wait counted
   twice).** Routed to a **separate maintenance run** that adds a
   stay-identity key (wo, gate, stay START) to `cost_ledger.row_key`.
   The duplicates already in `docs/factory/costs.jsonl` stay, because
   the ledger is append-only. Readers dedupe by the new key.
3. **Major 3, criterion 2 unmet (gate labels not applied by the
   owner's own hand).** Closed by **one combined post-merge live
   dispatch**. In it the owner applies the three gate labels by hand
   (`wo:prd-approved`, `wo:blueprint-approved`, then
   `wo:ready-for-agent`, each replacing its queue label). The same
   dispatch is the live proof for ADR-0077's unverified runner
   behaviours, listed under Post-release checks. The owner triggers it,
   and it costs money. This run does not trigger it.

## Pre-flight

- [x] Verification green (no unresolved failures). verification.md's
  2026-10-10 re-verification and its addendum (`c38d4a1`) have one FAIL
  (criterion 2) and four not-re-proven criteria. All are routed to the
  combined live dispatch by owner decision 3. Nothing is red that a
  merge would hide.
- [x] No secrets in diff; target config present. A secret-pattern scan
  over `origin/main...HEAD` matched only the test fixtures'
  `sk-ant-oat01-FAKETOKEN` / `sk-ant-oat01-LEAKED` strings. `gh secret
  list` shows `CLAUDE_CODE_OAUTH_TOKEN`, `FACTORY_PAUSE_TOKEN` and
  `FACTORY_REVIEW_TOKEN` (verification.md, criterion 1).
- [x] Migrations/data changes have a tested forward path. There is no
  migration. The only data change is five `$0` `owner-session:unmetered`
  rows appended to `docs/factory/costs.jsonl`, one per row of
  Milestone E, matching earlier owner-session rows.
- [x] Rollback plan concrete (below).
- [x] Up to date with main. After `git fetch origin`, `origin/main`
  (`ca57e5c`) is an ancestor of `HEAD`. `git merge-tree` against it is
  clean, so no merge or manifest regeneration was needed.
- [x] Pairwise merge-tree against the open PRs:
  - **#621** (`docs/docs-audit`): conflicts in `docs/factory/costs.jsonl`
    (both append rows at the tail, so keep both sides) and
    `docs/adr/README.md`. The index conflict comes from the stale merge
    base (`736f54b`): both sides picked up `main`'s 0076 row through
    different merges, and this branch adds 0077 after it. #621 does not
    edit the index itself. The resolution is this branch's side (0076,
    then 0077). #621's third
    conflict, `CONTEXT.md`, is #621's own conflict with `main`.
    `merge-tree origin/main pr/621` shows it without this branch.
  - **#623** (`feat/launch-demo`): conflicts only in
    `docs/factory/costs.jsonl`, with both appending rows. Keep both
    sides.
  - Whichever PR merges second resolves an append-only union. Nothing
    semantic collides.
- [x] Battery on `c38d4a1`:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 1971 tests in 26.660s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  $ actionlint .github/workflows/assembler.yml factory/templates/.github/workflows/assembler.yml
  actionlint exit=0
  ```

## Rollback plan

Door: two-way for the code. `assembler.yml`, `assembler.py`, their
template mirrors and the tests revert cleanly. But a merged workflow is
live: the next `wo:ready-for-agent` label runs it, with real spend and
real writes. The ledger rows and the ADR are effectively one-way.
`costs.jsonl` is append-only, so a revert keeps the five `$0` rows.
ADR-0077 is superseded by a new ADR, never deleted or rewritten.

Blast radius: this repo's dispatch plane, on the first dispatch after
merge. If the three-job graph misbehaves on a runner (the unverified
behaviours below), that dispatch fails to `wo:failed` and loses one
paid run. If the credential split is weaker than claimed, the agent's
code reaches a write credential. R3 is already known to reach the
reviewer PAT one hop later, through the validator. Every stamped repo
gets the same assembler on its next factory-init stamp or update. No
end user of the plugin skills is affected: `skills/` is untouched.

```
# Before merge (current state): withdraw the PR
gh pr close <PR> --delete-branch
gh issue reopen <anchor>        # only if the close comment closed it

# After merge, before any dispatch: do not apply wo:ready-for-agent.
# With no label, the new workflow never runs.

# After merge: revert, keeping the ledger rows (append-only)
git fetch origin && git switch -c revert/adr-0077 origin/main
git revert -m 1 <merge-sha>      # or: git revert <squash-sha>
git checkout origin/main -- docs/factory/costs.jsonl   # keep the rows
find factory/templates -name __pycache__ -type d | xargs rm -rf
python3 factory_init.py update-manifest
python3 -m unittest discover tests && python3 gates.py && python3 lint.py
git add <the reverted paths> factory/manifest.json
git commit && git push -u origin revert/adr-0077   # PR; touches docs/adr/** so it needs the human merge
# then a new ADR superseding ADR-0077, not an edit of it

# Mid-dispatch emergency stop: cancel the assembler run
gh run list --workflow assembler.yml --limit 3
gh run cancel <run-id>
```

## Release log

Each outward action is logged with its result as it happens.

1. Pre-flight above → green; origin/main is an ancestor; the pairwise
   conflicts are append-only unions (#621, #623).

## Post-release checks

The merge is the owner's (gate 3). This PR touches `docs/adr/**`, so
ADR-0036 also requires a human code-owner merge. Nothing can be checked
where it runs until the owner merges. After merge, the **combined live
dispatch** (owner decision 3) is the post-release check. The owner
applies the three gate labels by hand on a fresh mirrored order, and it
must show:

- criterion 2: each of `wo:prd-approved`, `wo:blueprint-approved` and
  `wo:ready-for-agent` applied by the owner's own hand, after reading
  what the gate approves, each replacing its queue label;
- ADR-0077 / verification.md "What only a live dispatch can prove":
  1. claude-code-action's write-permission check on the owner passes
     with the `agent` job's read-only token;
  2. `deliver`'s default-condition steps run after a failed `agent` job
     under `if: always()`, and the failed job's outputs
     (`execution_file`, `outcome`) reach `deliver`;
  3. the bundle cut in the agent's shallow checkout fetches into
     `deliver`'s full clone on a runner;
  4. the subprocess scrub reaches the agent's Bash from the job env, so
     a Bash `env` shows no Anthropic credential;
  5. the pushed branch, the opened PR, find-pr, the validator hand-off
     and the spend row all land as they did for #545.
- This re-proves criteria 3, 4, 6 and 10 and the inert-label half of 7,
  or routes back on the evidence it gives.

## Outcome

Prepared, not shipped. See the release log for the PR and CI.
