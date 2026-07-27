# The gh port joins the cli seam

- Status: accepted
- Date: 2026-07-27

Amends ADR-0040, continuing the chain from ADR-0037 through ADR-0039: a
carve-out that ADR-0037 justified by "one caller" or "each keeps its own
port" is folded in once the tree stops matching that rationale. ADR-0040
last restated ADR-0037's "what deliberately did NOT move" list; this
amendment revises that list again.

## Context

ADR-0037 made `cli` the shared adapter over an external CLI — the failure
vocabulary, the one-line `detail` formatter, `runner` — but deliberately
left each caller "its own port": `gh_runner` in label_sync.py (returns the
gh call's stdout) and `git_runner` in budget_guard.py (returns the
CompletedProcess). The seam docstring recorded the reasoning: two adapters
make the seam real, and each port had a single owner, so the port itself
stayed with its caller.

That described the tree the day it shipped. `gh_runner` has since grown
four callers: label_sync (`sync`, `live_labels`), sweeps (label-drift
detection and intake filing), gate_digest (the daily gate digest), and
validator (review and lifecycle). Three of them reached the port through a
tool-to-tool import — `from label_sync import gh_runner`, or
`label_sync.gh_runner` as a default argument — a thin caller depending on
another thin caller's private port. That is the same wart ADR-0040 retired
for `write_outputs`: a convention four tools share, homed in one of them.

`git_runner`, by contrast, still has exactly one caller (budget_guard's
`push_wip` / `hard_stop`).

## Decision

`cli` owns `gh_runner`, beside `runner` and the failure vocabulary — the
shared gh port: shell out to gh, unwrap the CompletedProcess to the stdout
string its callers `json.loads`, and let a missing, unauthenticated, or
rate-limited gh raise `CLI_FAILURES` for each caller to label. label_sync,
sweeps, gate_digest, and validator import it the same direction every other
seam is consumed.

`git_runner` stays in budget_guard. One caller is a hypothetical seam, not
a real one — ADR-0037's own "two adapters make the seam real" test — so it
folds into `cli` only when a second caller appears. The pins live at the
seam's own suite (`tests/test_cli.py`): the gh port returns stdout (not the
CompletedProcess `runner` yields) and raises into `CLI_FAILURES`.

Same authorization pattern as ADR-0039 and ADR-0040: no divergence between
copies fired the move — there was only ever one copy — but the carve-out's
stated rationale ("each caller keeps its own port") stopped describing a
port with four callers and three tool-to-tool imports.

## Consequences

- ADR-0037's "what deliberately did NOT move" list is read through
  ADR-0039, ADR-0040, and this amendment: ROW/TRACKER, `write_outputs`,
  and now `gh_runner` have since moved; `gates.pr_event`, the
  problem-string convention, and the checkbox-regex owners still stand.
- The gh-call convention (shell out, unwrap stdout, raise `CLI_FAILURES`)
  can no longer drift across the four tools that default to it; a fifth
  starts as a thin caller.
- `git_runner` stays local by the same rule that moved `gh_runner`: a
  single-caller port is a hypothetical seam. It folds in when — and only
  when — a second caller appears.
