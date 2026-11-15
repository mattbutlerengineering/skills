# Cloud sessions: the REST and MCP twins

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

**Cloud sessions.** Each `gh` command in this file states an intent;
the environment may offer only the GitHub MCP tools or the REST API
through `gh api`, and either carries it out. In Claude Code Remote the
GraphQL-backed `gh issue|pr` subcommands (`list`, `view`, `edit`,
`checks`, `merge`, `update-branch`) return HTTP 403 while `gh api`
REST calls succeed, so a profile written for a cloud session names the
REST twin of each default above (`preflight`'s check-runs read is REST
already). Where `gh` is absent altogether (`spawn gh ENOENT`), the REST
twins have no binary to run through, and the MCP twin is the way:

- `preflight`: REST `gh api repos/{owner}/{repo}/commits/<sha>/check-runs`
  (Phase 0, step 2), with `<sha>` from
  `gh api repos/{owner}/{repo}/branches/main --jq .commit.sha` and the
  push-run read as `gh api 'repos/{owner}/{repo}/actions/runs?head_sha=<sha>&event=push'`.
  MCP: `actions_list` with `method: list_workflow_runs`, filtered to
  `branch: main` and `event: push`, keeping only runs whose `head_sha`
  is the head; with a `required_check`, `method: list_workflow_jobs` on
  each kept run to find the job of that name (missing once every kept
  run has settled is red, as above). The re-run: REST
  `gh api -X POST repos/{owner}/{repo}/actions/runs/<run-id>/rerun-failed-jobs`;
  MCP `actions_run_trigger` with `method: rerun_failed_jobs`.
- Open PRs (Phase 0): MCP `list_pull_requests`, state open.
- Claim (Phase 1): MCP `list_issues` with `labels: ["ready"]`, state
  open; no entry carries a `pull_request` key there, so nothing to drop.
- Phase 0 step 5 ([lifecycle.md](lifecycle.md)): the `has-pr` list is
  `gh api 'repos/{owner}/{repo}/issues?labels=has-pr&state=open&per_page=100' --paginate`
  and the no-state-label count reads
  `gh api 'repos/{owner}/{repo}/issues?state=open&per_page=100' --paginate`,
  each dropping every entry that carries a `pull_request` key; the
  timeline read is REST already. MCP: `list_issues` with
  `labels: ["has-pr"]`, and with state open alone; the timeline has no
  MCP twin, so with no `gh` every `has-pr` issue is reported, never
  changed. The reconcile's count for
  [the closed-unmerged rule](lifecycle.md#a-pr-closed-unmerged) is
  the same timeline read; with no `gh` it cannot be read, so the
  reconcile sets `agent-failed`.
- The already-resolved close ([lifecycle.md](lifecycle.md#already-resolved)):
  `gh api -X PATCH repos/{owner}/{repo}/issues/<N> -f state=closed -f state_reason=completed`.
  MCP: `issue_write` with `method: update`, `state: closed` and
  `state_reason: completed`.
- `transition`: `gh api -X POST repos/{owner}/{repo}/issues/<N>/labels -f 'labels[]=<to>'`
  then `gh api -X DELETE repos/{owner}/{repo}/issues/<N>/labels/<from>`,
  one pair per swap in the Labels table. MCP: `issue_read` with
  `method: get_labels`, then `issue_write` with `method: update` and
  `labels` set to the full resulting set, never only the label added.
- `ci-status`: `gh api repos/{owner}/{repo}/commits/<head-sha>/check-runs`,
  with `<head-sha>` from `gh api repos/{owner}/{repo}/pulls/<N> --jq .head.sha`.
  MCP: `pull_request_read` with `method: get_check_runs`.
- `changed-files`: no MCP twin. `pull_request_read` with
  `method: get_files` is not a source until a run records that it
  reports a rename's `previous_filename`. With no `gh` the default
  cannot run, so every PR needs a human merge, unless the profile's own
  `changed-files` hook names another source that lists both paths of a
  rename.
- `merge-command`: `gh api -X PUT repos/{owner}/{repo}/pulls/<N>/merge -f merge_method=squash -f sha=<sha>`
  once `ci-status` is green (the endpoint answers 409 when the head is
  no longer `<sha>`), then
  `gh api -X DELETE repos/{owner}/{repo}/git/refs/heads/<branch>`.
  REST has no `--auto`: the train merges a green PR itself instead of
  enqueuing it, so the pin at merge time is the whole protection and
  nothing is left to disable. MCP: `merge_pull_request` with
  `merge_method: squash` and `expectedHeadSha` set to the gated head;
  it merges at once too, and has no branch-delete twin, so the branch
  is left to the repo's delete-on-merge setting and reported.
- `update-branch`: `gh api -X PUT repos/{owner}/{repo}/pulls/<N>/update-branch`.
  MCP: `update_pull_request_branch`.
- The verdict comment (gate step 5): MCP `add_issue_comment`, which
  takes a pull request number too.

Tool names are the GitHub MCP server's; a host may prefix them. With
neither `gh` nor an MCP tool for the intent, a stated hook cannot run:
fail closed. Claim nothing you cannot transition, merge nothing you
cannot check, and report the missing capability.
