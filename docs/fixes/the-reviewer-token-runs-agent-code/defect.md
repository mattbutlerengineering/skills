---
stage: capture
run: maintenance:the-reviewer-token-runs-agent-code
date: 2026-10-10
re-entry: architect
assumptions:
  - "No live interview: the interview source is autorun-brief.md (owner answers collected 2026-10-10, one question at a time); every answer below is from it or from reading the files cited."
  - "No intake issue and no backlog seed: the origin is the first-live-dispatch review's finding 4 (2026-10-02), re-scoped as R3 in the 2026-10-10 re-review, per the brief. Nothing to claim in docs/backlog.md."
  - "re-entry architect, not implement: the owner fixed the SHAPE (job split), but the skill's rule is that anything design-touching re-enters at Architect, and this redesign carries open design decisions (job graph, what crosses the boundary and in what form, how the trusted job obtains the PR event and PR number, whether a new ADR is warranted) — see Notes."
  - "Severity is recorded as major-or-critical pending the PAT-scope answer; the brief directs that the fix be safe under the worst case, so the unknown does not block design."
---

# Defect: the reviewer token runs agent code

## Defect (or Condition)

**Observed.** `validator.yml`'s `review` job runs code the pull request
controls and then, in the same job, hands that code the reviewer's
personal access token.

- The job fires on `pull_request` (`opened`/`reopened`/`synchronize`) for
  every same-repo branch, and on `workflow_dispatch` — the assembler's
  hand-off for factory PRs
  (`.github/workflows/validator.yml:98-104`). No owner step stands between
  either trigger and the token.
- It is granted `pull-requests: write` (`validator.yml:106-108`).
- It checks out PR-controlled code: `refs/pull/<N>/head` when dispatched,
  and checkout's default ref (the PR's merge ref) on `pull_request`
  (`validator.yml:110-112`).
- **Collect findings** runs `make check` from that checkout
  (`validator.yml:124-129`) — the PR's own `Makefile` and every tool and
  test it reaches.
- **Post findings as a non-authoring actor** sets
  `GH_TOKEN: ${{ secrets.FACTORY_REVIEW_TOKEN || secrets.GITHUB_TOKEN }}`
  and runs `make review FINDINGS=findings.txt STATUS="$FINDINGS_RC"`
  (`validator.yml:130-135`). `make review` is the PR's own `Makefile`
  (`Makefile:47-48`; payload copy `factory/templates/Makefile:41-42`)
  invoking the PR's own `validator.py review`, whose `post_review`
  (`validator.py:290`) shells out to `gh pr comment`.

So an agent PR that edits `Makefile`, `validator.py`, or anything `make
check` executes runs arbitrary code with the reviewer PAT in its
environment. It can post any comment, or an approving review, as the
reviewer account (role read live 2026-10-02: `write`), or print the PAT
into the findings it posts.

**Expected.** No step that executes code from the PR holds the reviewer
PAT or any write-scoped token. PR code runs only in a job whose token is
read-only; the job that posts as the reviewer checks out the base ref,
runs only that trusted code, and consumes the read-only job's output as
data.

## Reproduction / Evidence

**Reproduced by reading, not by execution.** No exploitation has been
observed. The path predates the factory's first live dispatch (WO-0030);
its first real post was the review comment on #579.

The evidence is the file:line chain in the Defect section. Live facts read
2026-10-10:

- `gh secret list` shows `FACTORY_REVIEW_TOKEN` is set (updated
  2026-09-28). That means the `||` fallback is not the path taken here:
  the PAT itself is what the PR's code receives.
- `gh variable list` shows no `FACTORY_REVIEW_LOGIN`. The optional
  identity cross-check (`validator.yml:80-81`) is therefore off. It is
  irrelevant to this defect anyway, because it is enforced by the same
  PR-controlled `validator.py` it would be checking.

**First work item (owned by the breakdown, not here):** reproduce
mechanically. A test or replay must show that PR-controlled code reaches a
write-scoped token on the current file, and go RED on it before the fix.
Asserting the defect does not count. The precedent for that test is
`TestAgentCredentialBoundary` (`tests/test_assembler.py` on
`fix/fld-allowlist-boundary`, PR #629).

## Root-cause hypothesis

*Hypothesis.* The job holds two trust levels at once. It was built as
"collect findings, then post them", with the identity question solved
(the token is asked who it is, `validator.yml:71-85`) but the provenance
of the code that holds the token never asked. Within a single job, every
step shares one runner. Three consequences follow from that, each to be
confirmed at Architect or Implement rather than taken as given:

1. **The direct path.** The posting step's own command is PR code (`make
   review` → PR's `validator.py`). This is the path the brief names.
2. **Same-job poisoning.** Making only the posting step trusted would not
   be enough. The earlier PR-code step can write `$GITHUB_ENV` /
   `$GITHUB_PATH` (for example `PATH`, `BASH_ENV`) or replace files in
   the workspace, and the later step inherits all of it. This is why the
   owner's fix is a **job** split, not a step reorder.
3. **The persisted checkout credential.** `actions/checkout@v4` persists
   the job's `GITHUB_TOKEN` into `.git/config` by default. In this job
   that token carries `pull-requests: write`, so `make check` may already
   hold a write-scoped token even before the PAT step. This is a reading
   of checkout's documented default and has not been tested here. The
   Expected clause ("any write-scoped token") covers it either way.

The fork guard (`validator.yml:103`) and the comment rejecting
`pull_request_target` (`validator.yml:86-88`) show the untrusted-code
concern was considered for forks. Same-repo branches were treated as
trusted, but in this factory a same-repo branch is the dispatched agent's
branch.

## Blast radius

- **Who/what:** every same-repo PR in this repo, and every factory PR
  dispatched by the assembler. The workflow is mirrored verbatim into
  the template payload (`factory/templates/.github/workflows/validator.yml`,
  byte-identical, confirmed with `cmp`). **Every stamped product repo
  inherits the same path** with its own reviewer PAT.
- **How badly:** the reviewer account is gate 3's agent reviewer
  (ADR-0033). Code that controls the reviewer's voice can forge the
  pre-chewed review the human merge gate relies on, approve as the
  reviewer, or exfiltrate the PAT for use outside CI.
- **Severity:** depends on the PAT's scopes, which are **unknown** (open
  owner question below). It is **major** if the PAT is limited to
  review/comment, and **critical** if it is classic `repo` or
  fine-grained `contents: write`. The fix must be safe under the worst
  case, so the scopes change the severity label, not the design.
- **Since when:** since the `review` job gained the reviewer-PAT arm
  (WO-0004 era). It became reachable by an actual agent's code at the
  first live dispatch (WO-0030).

## Ruled out

- **Dropping the reviewer account to `triage`** was the review's other
  candidate. The owner did not choose it (2026-10-10). It narrows what the
  PAT can do but leaves PR code holding a credential.
- **Adopting `pull_request_target`** is out of scope unless Architect
  shows it is both required and safe. The workflow's own comment
  (`validator.yml:86-88`) already rejects it, because it would run
  untrusted code with a write token.
- **The fork guard.** It already excludes fork PRs. This defect is the
  same-repo case, which the guard deliberately admits.
- **PR #629's assembler ADR (number 0077 on `fix/fld-allowlist-boundary`).** It closed the same class of defect for the
  assembler, and names this path as *not* closed. It is not a fix for
  this path.

## Notes

- **Work already in flight (protocol check, ran 2026-10-10).** Result:
  nothing matches. `gh pr list --state open` returned three PRs:
  - #629 `fix/fld-allowlist-boundary` is related but does not do this
    work. Its changed files are `assembler.yml`, its payload mirror, and
    `tests/test_workflow_permissions.py`; it does not touch
    `validator.yml` or the Makefile. This run must keep the interface
    #629's deliver job uses unchanged: dispatching the validator with a
    `pr` input.
  - #623 (launch demo) and #621 (docs audit) touch no workflow,
    validator, or Makefile.

  `git log --all --not origin/main -- .github/workflows/validator.yml`
  shows only branches whose work already landed on main (for example
  `fix/validator-dispatch-handoff`, merged as #547). No other worktree's
  branch carries an unmerged change to this path.
- **Re-entry: architect, and why.** The owner decided the fix's shape: a
  read-only job runs the PR's code and hands over a result artifact, and
  a separate PAT-holding job on the base ref consumes it as data and runs
  no PR code. That decision leaves real design open:
  - the job graph and its `needs:`/`if:` gating across both triggers;
  - what crosses the boundary (findings text, exit status, PR number),
    in what form, and how the trusted job treats it as untrusted data;
  - how the trusted job gets the PR event without PR code (the dispatch
    arm's `make pr-event` currently runs from the PR checkout);
  - which ref "base" means on each trigger;
  - per-job grants for `tests/test_workflow_permissions.py`'s recorded
    table (`tests/test_workflow_permissions.py:90-91` records `review`
    as `contents: read, pull-requests: write`);
  - `persist-credentials` on every checkout;
  - whether the decision needs its own ADR. #629's ADR (number 0077) is not yet on main,
    so it must not be edited; cite it by number only if a new ADR is
    written.

  Under the skill's rule, design-touching work re-enters at Architect.
- **Scope (from the brief).** IN: `validator.yml` and its payload mirror;
  the Makefile targets and tools the review path uses; tests pinning the
  new boundary; `tests/test_workflow_permissions.py`; the manifest regen.
  OUT: `assembler.yml`; the reviewer account's role and PAT (owner
  actions); `pull_request_target` unless justified; Majors 2 and 3 of the
  first-live-dispatch review; the fork guard's other paths.
- **Live proof.** The new workflow can be proven only on a runner. Its
  live proof folds into the owner's combined post-merge live dispatch,
  recorded in #629's release.md.
- **Open owner question: the reviewer PAT's scopes.** Is
  `FACTORY_REVIEW_TOKEN` a classic PAT, and with which scopes, or a
  fine-grained PAT, and with which repository permissions? The answer
  settles major vs critical. It does not change the design. Not guessed.
