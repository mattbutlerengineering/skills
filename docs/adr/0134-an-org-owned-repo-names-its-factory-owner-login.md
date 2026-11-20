# An organization-owned repo names its factory owner login

- Status: provisional
- Date: 2026-11-20

Recorded by an unattended fix run (issue #2105), so it is provisional. It
amends ADR-0032's owner-only rule for `wo:ready-for-agent`.

## Context

ADR-0032 lets only the repo owner apply `wo:ready-for-agent`. The
assembler enforced that as `github.event.sender.login ==
github.repository_owner`, and fed the same owner to
`assembler.actor_is_owner`. For an organization-owned repo,
`repository_owner` is the org's login, and a label's sender is always a
user. The job gate was never true. Every ready label was skipped with no
claim, no comment and no red run, so a stamped org repo looked configured
and never dispatched.

## Decision

**"The repo owner" is `vars.FACTORY_OWNER_LOGIN || github.repository_owner`.**
The assembler's job gate and its `FACTORY_REPO_OWNER` both read that
expression, in the root workflow and the payload a stamped repo runs. A
personal repo leaves the variable unset and behaves as before. An org
repo sets the repository variable to the login of the person who owns
the factory. Only that person's label dispatches; a label from anyone
else is still inert.

**The local planner reads the same variable.** `work_queue.owner_holds`
takes the owner from the `FACTORY_OWNER_LOGIN` repository variable
(`gh variable list`) and falls back to `gh repo view`'s owner, so the
planner and the workflow agree on whose label counts. A failed variable
read fails closed, like a failed owner read. The planner sees repository
variables only, so the variable is set on the repository, not the org.

**Doctor reports the gap.** Its networked tier reports an org-owned repo
with no `FACTORY_OWNER_LOGIN` set, and prints the `gh variable set`
command to fix it.

## Consequences

- One login per repo. An org that wants several people able to dispatch
  needs a later decision, such as a team check. That is not built here.
- The variable is a repository setting, not a file, so the offline gates
  cannot check it. Only doctor's networked tier reports it unset.
- Anyone with permission to edit repository variables can change who the
  owner is. On a personal repo that is the owner. On an org repo it is
  the repo's admins, who could already change the workflow itself.
