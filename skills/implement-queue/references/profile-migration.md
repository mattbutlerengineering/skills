# Profile migration

What a queue profile (`.claude/implement-queue.md`) loses by lacking an
entry the skill's tables now name. The Phase 0 profile check reads this
file: a profile written before a row existed keeps working, but the
default for that row may be the fail-closed one, and nothing else tells
its Owner.

**Keeping this file whole.** Every row of the skill's key table and hook
table has a row here, by name and in the same order. Adding a hook or a
key to the skill means adding its row here in the same change; a test
holds the two lists equal.

Each row's *Consequence when absent* is the skill's own default,
restated. A hook can tighten a default, never loosen a rule in the
skill's Rules section.

## Frontmatter keys

| Key              | Consequence when absent                                                    |
| ---------------- | -------------------------------------------------------------------------- |
| `source`         | Plain `ready` issues. Factory work orders are never claimed.               |
| `merge`          | `off`: the run stops at reviewed, green PRs and merges nothing.            |
| `max_workers`    | 3 workers in flight.                                                       |
| `required_check` | No check is demanded present, so the gate trusts the rollup alone. Name the repo's gate job. |
| `hold_labels`    | `[needs-review]` only.                                                     |
| `priority`       | `[security, ci-fix, feature, audit]`.                                      |
| `gate_paths`     | The four ADR-0036 defaults only. A repo with instruction docs, workflows or release files agents obey must list them, or its PRs are not held for a human. |

## Hooks

| Hook             | Consequence when absent                                                                                  |
| ---------------- | -------------------------------------------------------------------------------------------------------- |
| `preflight`      | The gate's own green on `origin/main`'s head SHA: the required check present and successful, else its push-triggered runs. Needs `gh`; a cloud session names the REST or MCP twin. A hook that reads a run-list window is crowded out by event-driven workflows, and a `failure`-only filter misses a cancelled run whose gate job failed. |
| `transition`     | `gh issue edit`. Fails under a cloud session's GraphQL 403; name the REST or MCP twin.                    |
| `compose`        | Candidates are taken in priority order, skipping only issues that name the same files.                    |
| `base-freshness` | `git fetch origin` and a shared-history check against `origin/main`.                                      |
| `worker`         | A general worker agent given the Worker brief.                                                            |
| `model`          | The worker's default model.                                                                               |
| `ci-status`      | `gh pr checks <N>` plus the presence check. Fails under a cloud session's GraphQL 403.                    |
| `fast-path`      | Every PR is reviewed (with no `verdict` hook, held unreviewed instead). Safe but slower: no docs-only PR skips review. |
| `verdict`        | **Every PR off the fast path is held for a human unreviewed, with a `reviewer-verdict: error (no verdict hook)` comment: no review is dispatched, even under `merge: auto`, so nothing off the fast path merges. Fast-path PRs can still merge, and the final report says so; no warning is printed.** Add the hook. It runs on the reviewer's `score` and exits 0 for `pass`, 1 for `flag`, 2 for `error`, printing the line the verdict comment opens with; the pass threshold lives only in it (ADR-0123). |
| `reviewers`      | One universal reviewer, no specialists.                                                                   |
| `merge-command`  | `gh pr merge <N> --auto --squash --delete-branch --match-head-commit <sha>`, `<sha>` the gated head. Needs `gh` and a session that may merge. |
| `update-branch`  | `gh pr update-branch <N>`.                                                                                |
| `changed-files`  | The REST file list with `filename` and `previous_filename`, its length checked against the PR's `changed_files`. With no `gh` the default cannot run, so every PR needs a human merge unless the profile names another source that lists both paths of a rename. |
| `lock`           | None: one session at a time is the only lock.                                                             |
| `reap`           | None: worker worktrees left behind are reported, not removed.                                             |
| `telemetry`      | None: no usage is recorded.                                                                               |

## What the check reports

- **A missing key or hook:** the row above, in one line per entry.
- **A section or key the skill does not name:** ignored, never run. It
  is a typo, a hook this skill version predates, or one retired since.
- **Neither:** nothing to report. A profile that names every row is
  current as of the skill version being read.
