# Recon — name the tree, then check what is in flight

The two recon steps `audit` and `automate` share. `audit` owns this
file; `automate` cites it as `../audit/references/recon.md`. What each
skill maps between the two steps stays in its own `SKILL.md`. Below, a
"finding" is an audit finding or an automate recommendation.

## Name the tree

State, in the report's first two lines, the **absolute repo root** and
`git rev-parse --short HEAD`. Never "this repo": a finding is scoped to a
tree at a commit, and the reader's tree is not yours. Deriving the target
from whatever directory you happen to be standing in is how a report ends
up describing a different repo than the one it names.

## Check what is already in flight

Before judging or recommending anything:

    gh pr list --state open
    gh issue list --state open --limit 50

In a cloud session (Claude Code Remote), where the GraphQL-backed
`gh pr list` and `gh issue list` return HTTP 403 while `gh api` REST
calls succeed: `gh api 'repos/{owner}/{repo}/pulls?state=open'` and
`gh api 'repos/{owner}/{repo}/issues?state=open&per_page=50'`, dropping
every entry that carries a `pull_request` key — the REST issues
endpoint lists pull requests too.

What an unmerged PR already does — a defect it fixes, an automation it
adds — is not a finding: it is a duplicate of work in flight, and a fresh
diagnosis of it is worse than useless because it reads as new. The same
goes for an open issue that already names or proposes it, and for a seed
already sitting in `docs/backlog.md`. Read all three before the sweep,
not after: recon is cheap and re-litigation is not. This is not
hypothetical bookkeeping: a run in this repo rebuilt a one-line fix that
was sitting in an open PR the whole time, because discovery listed open
issues and never open PRs.
