---
stage: operate
run: feature:pr-body-preflight
date: 2026-11-09
users-observed: 1
signal-source: "gh pr list --state all --search created:>=2026-10-17 (the release date): 319 pull requests, every one authored by one account, the Owner's, which also runs its agent sessions and routines. The hook records nothing when it fires, so its refusals are not counted."
---

# Retro: PR-body preflight hook

The population is one account over 23 days. Nobody else uses the hook:
it ships to this repo only (the PRD's Owner decision), so the count is
the Owner and the agents acting under the Owner's account. Everything
below is read against that.

## Outcomes vs. intent

### A `gh pr create` whose body would fail detector B is refused before the PR opens

- What happened: 0 of 319 pull requests opened since release (2026-10-17) lack the work-order line or the closing line. In the 266 opened in the 30 days before, 7 did (2.6%). The hook is registered in `.claude/settings.json` and runs on every Bash call.
- Signal strength: anecdote. The drop from 7 to 0 fits the hook working, but detector B in CI, the pull request template and the `docs/kb/pr-body-contract.md` update (#1023) all landed in the same window, and the hook logs nothing, so no refusal can be tied to it. The review's own replay found the hook judged 9 of 210 historical `gh pr create` commands (about 4%), because most bodies are written by a heredoc in the same Bash call that opens the PR, which the hook cannot read. The fixes after that finding were not re-measured.

### The hook never blocks a body that detector B accepts

- What happened: no false block has been reported since release. No issue or backlog entry names one.
- Signal strength: unobserved. One person who sees no complaint is the absence of a report, not a measurement; a refused command that was then rewritten is invisible.

### Unattended routines stop going red on a bad PR body (the PRD's problem statement)

- What happened: not measurable from here. The release assumed, and never observed, that `CLAUDE_PROJECT_DIR` is set in the cloud routines; if it is unset the guard in `.claude/settings.json` makes the hook a no-op. All 319 pull requests pass the contract, but that is true of the routines' PRs and the Owner's alike.
- Signal strength: unobserved.

## Open debt

None. The run's own issues are closed: #990 (the feature issue) and #992 (the release record). #1023 was filed after the merge for a documentation gap and is closed.

## Run retrospective

- Keep: the independent review earned its cost. It found two Criticals (text the shell never runs was parsed as commands, so a plain heredoc or a comment could cause a false block) and the 4% coverage figure, by replaying 210 real historical commands rather than reading the code.
- Change: Ship records that `verification.md` predates the re-review's three fix commits and was not re-run. A verification that does not cover the shipped head is a weaker claim than its Summary reads. The run's own record is the only thing that says so.
- Stop: nothing identified.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| A body-reading hook parsed heredoc and comment text as commands and refused a body B accepts | `review.md` §Critical: text the shell never runs is parsed as commands | mechanical | The replay test over fixture hook payloads, `tests/test_pr_body_preflight.py`, which holds the `$(cat <<'EOF'` heredoc shapes |
| `verification.md` was not re-run after three fix commits, so it describes an earlier head | `release.md` assumptions, third entry | mechanical | A `gates.py` detector comparing the commit `verification.md` names against the branch's last code change. None exists |
| The hook's coverage stayed at about 4% of real commands and the decision to re-measure was left to the Owner | `review.md` §Major: real coverage is about 4% | judgement | None fits: the gap is a missing measurement, not a rule, so it is carried by the first seed below |
| Launch brief not produced because the stage brief allowed one file | `release.md` assumptions, fifth entry | judgement | `skills/autorun/SKILL.md`, in how it briefs the Ship stage on launch-demo's verdict |

## Idea seeds

- Re-measure `pr_body_preflight.py` coverage over the heredoc-masked parser: replay the historical `gh pr create` commands the review used (210, 9 judged) and record the judged share, so the review's open decision has a number
- Bind a heredoc to the file it writes (`cat > F <<D`) so a later `--body-file F` in the same compound command is judged: the shape behind 74 of the 210 unjudged commands
- Log each refusal the PR-body hook makes (one line to a gitignored file), so a retro can count what the hook actually stopped
- Observe `CLAUDE_PROJECT_DIR` in one cloud routine run, to settle whether the hook is a no-op there

## Run complete

2026-11-09. The seeds above are the input to the next Idea-stage run.
