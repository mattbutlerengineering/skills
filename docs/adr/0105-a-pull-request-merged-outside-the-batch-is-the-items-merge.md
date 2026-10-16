# A pull request merged outside the batch is the item's merge

- Status: provisional
- Date: 2026-10-16

Amends no record. ADR-0085's rule that a Conductor merge executes an
Owner answer stands: this decides what the ledger does when the repo
merges an item's pull request without any Conductor turn at all, and
#807's reading of the closing PR (merged `by` the repo) extends to item
PRs.

## Context

A consumer runs its own merge train (`/implement-queue` through
routines). It merged four of a batch's item pull requests while the
items were mid-build, and the ledger never knew (issue #938): `next`
kept launching build runs, `deliver` listed only open PRs on the head,
found none, and opened a second PR under the first's title, and a
blocked item whose PR the Owner later merged by hand stayed `blocked`
in the scorecard, so `metered_usd_per_merged` read null for a batch
that shipped.

## Decision

1. **`next` reads each due item's merged PR every tick**, one
   `gh pr list --head <branch> --state merged` per item between `spec`
   and `reviewed` that is neither in flight nor behind an ask (a
   shipped item is the merge turn's, under #807), and per stalled
   item answered `merged`. The read is a fact the pure survey stalls
   on; a failed read fails the tick like any fact's.
2. **A merged PR stalls the item with cause `merge-drift`** — the
   repo's merge drifted from the ledger's — instead of launching its
   next step. The stall row carries the PR number, so one PR raises
   one ask. Its options are `retry`, `merged` and `block`: `retry`
   resumes the step, whose run delivers on a fresh PR; `merged`
   records the PR as the item's merge. `merged` is recommended once
   the build is done (the item is past build, or no breakdown row is
   unchecked), `retry` while rows remain.
3. **A `merged` answer writes `stalled → merged`**, carrying the PR,
   its merge commit as `sha`, and `checks: {}`: the Conductor read no
   checks of its own; the repo merged under its rules. No other answer
   leaves `stalled` for `merged`.
4. **`deliver` names a merged PR on the head** when it finds no open
   one: a refusal's stall reason ends with it, and a fresh PR's body
   starts with it. The title is unchanged; the body says why there is
   a second PR.
5. **`close` reconciles a blocked item whose PR merged after the
   block** as `blocked → merged` with the same fields, before it
   carries spend or labels anything: the merged PR carried the branch's
   spend rows to main, and the item needs no `needs-human` label. This
   is the one way out of `blocked`. The closing PR closes its issue and
   the printed summary names it as merged outside the batch.
6. **The scorecard counts every merged item under `merged`** — the
   per-merged ratios read what shipped — and the merges the Conductor's
   turn did not make (a merged row not from `merging`) under a new key,
   `merged_outside` (#814: a changed meaning is a new key). Older rows
   lack it and read as written.
7. **`open` names the workflows on origin/main that merge pull
   requests themselves**, in an advisory line, never a refusal.

## Consequences

- An item whose PR the repo merges mid-build costs one Owner answer,
  not a second PR and the runs behind it; the ledger holds which PR
  merged what.
- A repo under a merge train will merge the fresh PR too; each merge
  raises its own ask, and the `open` line says to expect it.
- `conductor_landed.py` (mirrored) owns the vocabulary and the pure
  reads; `conductor_next.merged_pr` is the one gh read, shared by the
  tick, the delivery and the close.
- Not decided: an item stalled behind another ask whose PR then merges
  (the block that answers it reconciles at close); a PR merged while
  the item's run is in flight (its run finishes, delivers a fresh PR
  naming the merged one, and the next tick asks); spend rows a
  blocked item's branch gained after its PR merged (none are written
  after a block today).
