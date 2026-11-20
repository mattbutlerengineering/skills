# The tracker readers list only work-order issues, and sweeps joins the human_gates.py row

- Status: provisional
- Date: 2026-11-20

Recorded by an unattended fix run (issue #2205), so it is provisional. It follows
ADR-0128 for the dual-membership set ADR-0091 pinned, here the
`human_gates.py` row, which held only `dashboard`.

## Context

Three scheduled jobs read the whole tracker in one `gh issue list
--state all` window: the reconcile sweep (`sweeps.live_issues`), and the
gate digest and the toolsmith mine (`human_gates.read_gate_issues`).
Each refuses or flags a full window, as cli.gh_read's contract asks.
They went red at 500 issues (2026-10-19, 2026-10-26) and again at 1000
(2026-11-16 to 2026-11-18), and #2055 raised the window to 2000. The
tracker holds about 1200 issues and grows by about 42 a day, so the
window fills again in early December and the reconcile sweep files
nothing.

None of the three reads the whole tracker. `plane_drift.reconcile_drift`
compares every issue a breakdown row mirrors, and every issue carrying a
`wo:` label (to report one no row mirrors). The digest and the miner
read only mirrored issues: the timelines `read_gate_issues` fetches and
the queues `open_queues` builds both filter on the mirror map.

## Decision

**The readers list only work-order issues.**
`human_gates.read_work_order_issues` makes three reads. The repo's live
labels come first, so a `wo:` label outside the taxonomy is still
searched for. Then one search over all of them: GitHub reads
comma-separated label values as OR. Last, each mirrored number the
search did not return is read by number through the REST API. A
mirrored issue that lost its last `wo:` label is still one the readers
compare. A number that is no issue, a pull request, or an issue
transferred away is absent, as it was from the whole-tracker listing.
Any other failure of a by-number read makes the listing unusable, since
a missing mirrored issue is a finding to reconcile.

**The search window is 1000.** GitHub search returns at most 1000
results per query whatever `--limit` asks for. At exactly that window a
capped search reads as a full one, so the fail-closed check still fires
instead of passing a short listing silently.

**sweeps imports human_gates.** The reconcile sweep and the two gate
readers share the read, and human_gates is mirrored because the gate
readers ship. sweeps is root-only, so the pin's `human_gates.py` row
gains `sweeps`.

## Consequences

- The listing grows with the work-order issues, not with the tracker:
  49 issues carry a `wo:` label today. It fills only when one search
  returns 1000 of them, and then the check reports it.
- A by-number read runs only for a mirrored issue with no `wo:` label.
  There are none today, and the count is bounded by the breakdown rows.
- GitHub's search index can lag a label change by seconds. An issue
  labelled `wo:` moments before a run can be missed by that run's
  search. The next scheduled run sees it. A mirrored issue is never
  missed, because the by-number read is not indexed.
- `human_gates.py` gains one more root-only importer. A future attempt
  at the tools/factory restructure (ADR-0091) has one more pair to
  account for. human_gates imports only `cli`, so the edge adds no
  cycle.
