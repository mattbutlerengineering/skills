# A fast-path classification is the review for auto-merge

- Status: accepted (Owner, 2026-10-12)
- Date: 2026-10-12

Amends ADR-0087, for `implement-queue` PRs that the queue profile's
`fast-path` hook classifies as low-risk. The Owner chose this on
2026-10-12, in session. It resolves issue #729.

Read literally, ADR-0087 and the skill contradict each other. The
skill's gate skips review for a fast-path PR (a low-risk diff that no
specialist matches). ADR-0087's condition 2 then refuses the merge,
because no distinct reviewer passed it. So no fast-path PR could ever
auto-merge. That includes the metrics-only PRs the consumer this skill
came from has auto-merged that way for months. An agent following both
rules would either stall those PRs forever or quietly break one of the
rules.

## Decision

Under `merge: auto`, a PR the `fast-path` hook classifies as low-risk,
and that no specialist reviewer matches, **satisfies ADR-0087's
condition 2 without a reviewer dispatch**. The hook is the Owner's own
written low-risk classification: it is committed in the consumer repo
and changed only by a PR there, just like the profile's `merge: auto`.

This holds only while the hook can prove its own inputs are current.
If it fails closed (a stale build, an unreadable classifier), the PR is
reviewed and condition 2 applies as written. ADR-0087's other three
conditions are unchanged: the required check present and green, no
gate-path file, and no hold label.

## Consequences

- Fast-path PRs can auto-merge, as they did before the skill moved here.
- The trust limit is ADR-0087's: a wrong classification in the hook
  merges a risky diff unreviewed. The commit that wrote the hook is
  the audit record, the same way the profile's commit is.
- A consumer with no `fast-path` hook reviews every PR, so nothing
  changes for it.

## If rejected

Option (b) from #729: the fast path skips only the universal reviewer,
and a cheap distinct check still runs and counts as the pass.
