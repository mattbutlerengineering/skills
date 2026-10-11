---
stage: capture
run: maintenance:dashboard-timeline-unreadable-age
date: 2026-10-11
re-entry: implement
origin:
  - "docs/backlog.md:98 — `dashboard._timeline` returns `[]` on a failed timeline fetch, so the dashboard shows an unreadable age and an unknown age the same way (from: maintenance:one-fence-rule)"
assumptions:
  - "Anchor: tracker issue #665 carries this defect. The Conductor owns the tracker and the backlog, so this run neither edits the issue nor claims the docs/backlog.md seed in place."
  - "Field name: the queue entry gains `aged`, the name gate_digest's Item already uses for the same fact (could the timeline be read). The fetch stays per tool (ADR-0056); only the vocabulary is shared, not code."
---

# Defect: the dashboard cannot tell an unreadable age from an unknown one

## Defect (or Condition)

`dashboard._timeline` (`dashboard.py`, the per-issue timeline fetch)
returns `[]` when `gh api …/timeline` fails or returns JSON it cannot
parse. `dashboard._queues` then walks that empty list, finds no arrival
at the gate, and records `waited_s: None`. A timeline that was read and
holds no arrival at the gate also yields `waited_s: None`.

- **Observed:** the two cases produce identical queue entries, and
  `dashboard.html` renders both as a bare line with no age. Only the
  repo card's problem list mentions the failed fetch, and that list does
  not say which "Needs you" line to distrust.
- **Expected:** the queue entry says whether its timeline could be read,
  and the page marks an unreadable one on that item's own line. This is
  what `gate_digest` already does: `gate_digest._queues` keeps absent
  (unreadable) apart from present-and-empty, and `compose_digest` appends
  ` — age unknown (timeline unreadable)` to that item's line. Its own
  comment records the old `.get(number, [])` default as the collapse it
  fixed.

The `dashboard: gh api timeline for #N failed: …` problem string for a
failed fetch stays exactly as it is.

## Reproduction / Evidence

Run in this worktree at `147da0f` on 2026-10-11. The script drives the
real `dashboard.gather` with the test suite's own fixtures
(`factory_repo`, `queue_gh`, `git_remote`, `clock` from
`tests/test_dashboard.py`). The first case fails every timeline fetch.
The second reads every timeline and finds no labeled events.

```
$ python3 scratchpad/repro.py
failed fetch:
   {'gate': 'prd', 'issue': 7, 'title': 'WO-0101: first', 'waited_s': None, 'url': 'https://github.com/o/r/issues/7'}
   {'gate': 'merge', 'issue': 8, 'title': 'WO-0102: second', 'waited_s': None, 'url': 'https://github.com/o/r/issues/8'}
   problems: ['dashboard: gh api timeline for #7 failed: boom', 'dashboard: gh api timeline for #8 failed: boom']
read, no arrival:
   {'gate': 'prd', 'issue': 7, 'title': 'WO-0101: first', 'waited_s': None, 'url': 'https://github.com/o/r/issues/7'}
   {'gate': 'merge', 'issue': 8, 'title': 'WO-0102: second', 'waited_s': None, 'url': 'https://github.com/o/r/issues/8'}
   problems: []
```

The queue entries are byte-identical. Only the repo-level `problems`
list differs. `dashboard.html`'s `renderNeedsYou` builds each line from
`fmtWait(q.waited_s)` alone, so both cases render with no age suffix.

The existing test `test_a_failing_timeline_lists_the_item_without_an_age`
pins `waited_s` at `[None, None]` for the failed case and asserts
nothing that would tell it apart from the empty case.

## Root-cause hypothesis

Confirmed by reading the code. `_timeline` folds "could not read" into
the same return value as "read, nothing there" (`return []` when
`read.value is None`). Everything downstream sees only the event list,
so it cannot recover the difference. `gate_digest` once had the same
fold (`events_by_issue.get(number, [])`) and fixed it by keeping the
issue absent from its map. `dashboard._timeline` is a separate fetch
(ADR-0056 left the fetches per tool), so that fix never reached it.

## Blast radius

- **Who:** the operator using the localhost console. `dashboard.py` is
  root-only. It is not in `factory_init.MIRRORS` (confirmed: no
  `MIRRORS` entry names it), so no stamped repo ships it and no
  manifest regen applies.
- **What:** a "Needs you" line whose age is missing for a reason the
  page does not give. The operator can read a failed fetch as "this item
  just arrived" or "it has no gate arrival on record." Nothing is lost:
  the item still lists and the problem string is still reported. The
  failure is that the line misleads.
- **Since when:** since the console's queue section first shipped
  (WO-0019). The `[]` default is in its docstring.

## Ruled out

- **Sharing gate_digest's code.** ADR-0056 left the timeline fetches per
  tool. The brief asks for a dashboard-only fix, so `gate_digest.py` and
  `human_gates.py` are untouched.
- **A malformed timestamp.** A refused `created_at` (#491) is a
  successful read with an event dropped. It is reported by its own
  problem string, and the timeline still counts as read. It is not this
  defect, and its test keeps passing unchanged.
- **Changing the problem string.** The failed-fetch string stays
  byte-identical, as the brief requires.

## Work items

- [ ] **Data: the queue entry says whether its timeline was read** — `_timeline` returns `None` on a failed or unparseable fetch, and `_queues` adds `aged` (true when the timeline was read) to each entry.
  - Accept: in `tests/test_dashboard.py`, a failed fetch yields `aged: False` and a read-but-empty timeline yields `aged: True`, both with `waited_s: None`. The failed-fetch problem strings are unchanged.
- [ ] **Render: the page marks an unreadable age on the item's line** — `renderNeedsYou` appends ` — age unknown (timeline unreadable)` when `aged` is false, matching the gate digest's wording.
  - Accept: the node render harness shows the marker for an `aged: false` entry and leaves an `aged: true` entry with no age unmarked.

## Notes

- 2026-10-11: tests went in first and failed for the right reason
  before the fix. The red-run output is in `verification.md`.
