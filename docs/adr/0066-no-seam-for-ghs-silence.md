# No seam for gh's silence; the rule is shared, the meaning is local

- Status: provisional
- Date: 2026-09-21

## Context

`docs/fixes/deepening-cli-seams/architecture.md` (2026-08-13) named a
design gap the deepening review raised: five call sites turn one
windowed `gh` listing into either data a caller may trust or a problem
string saying why not — `label_sync.live_labels`, `gate_digest.run_daily`,
`sweeps.live_issues`, `sweeps.known_keys` and
`work_queue.ready_issue_numbers` — and the review found the failure
handling copy-pasted at two of them verbatim. The open question was
whether that copy-paste was a shared rule wanting one seam, or five
callers that only look alike.

`cli.gh_read` already answers the mechanical half: it runs `gh`, catches
the binary's failure vocabulary, parses and shape-checks the JSON, and —
when a `window` is given — flags a full window as `truncated` without
discarding the value. What it deliberately does not do is decide what a
full window MEANS. That answer is genuinely per-caller:

- **Refuse** when absence would be read as a finding.
  `sweeps.live_issues` and `work_queue.ready_issue_numbers` both abort on
  `truncated` — past the window an issue is simply absent, and a drift
  or readiness check that treats "unseen" as "gone" invents a finding a
  windowed listing cannot support.
- **Report and continue** when absence only under-reports.
  `label_sync.live_labels` and `gate_digest.run_daily` both keep the
  value and surface the fact, because a comparison or a digest that
  under-covers is still useful, and refusing it entirely would throw
  away real data over a note.
- **Report and continue, with a caller-specific consequence.**
  `sweeps.known_keys` keeps the value too, but re-doing a duplicate
  intake is cheaper than silently under-deduping, so its `full_note`
  says what a full window costs THERE, not `gh_read`'s generic sentence.

Three answers, five callers, two callers per non-trivial answer — the
shape the deepening review's own arithmetic later corrected once
`work_queue.eligible`'s truncation policy was fixed to match
`sweeps.live_issues` (see that run's breakdown, Milestone C). That is not
the shape that argues for extracting a seam: a policy-table module would
carry a per-caller message and a per-caller policy both, which is a
configuration table wearing a seam's clothes, not a reduction.

Each site now states its own answer in its own docstring or a comment at
the call site — `label_sync.live_labels`: *"A full window is a suffix
too, but the labels stay usable."*; `sweeps.live_issues`: *"A truncated
window ABORTS here rather than warning, unlike the dedupe listing in
known_keys"*; `sweeps.known_keys`: *"The listing is windowed and gh
truncates it silently, so a full window is reported"*;
`gate_digest.run_daily` via the module-level `TRUNCATED_NOTE`; and
`work_queue.ready_issue_numbers`: *"A truncated window REFUSES here
rather than warning, the same rule as sweeps.live_issues."* Each is
pinned by its own test (`tests/test_label_sync.py`,
`tests/test_sweeps.py` ×2, `tests/test_gate_digest.py` ×3,
`tests/test_work_queue.py`) asserting refuse-vs-continue against a full
window, independent of `cli.py`'s own generic-message test. So a
disagreement between two sites is now a recorded decision, not an
accident — which is the actual defect the deepening review's Card 2
raised (issue #456's sibling class, a copy-paste gap, not this seam).

**A sixth question, adjacent but distinct (issue #449).**
`work_queue.ready_issue_numbers`' refusal used `gh_read`'s default
message — *"raise the window or narrow the query"* — which reads like a
runtime option. Neither is: `LIST_WINDOW` is a module constant, and in a
stamped repo `work_queue.py` is a mirrored payload copy, so the person
seeing this message cannot reach either remedy from where they are
standing. That is not an argument for a runtime-configurable window (the
`implementation-discipline.md` bar — no speculative flexibility nobody
asked for — and `LIST_WINDOW`'s comment already records that it is
deliberately the tightest of the three windows because it is the only
one on a hard-stop path, i.e. tight-and-wrong-fails-loud is the intended
shape). It is an argument for an honest message.

## Decision

**No seam.** `cli.gh_read` keeps owning the mechanical truncation check
and the `truncated` flag; each caller keeps owning what absence means to
it and keeps its own pinned message, via the existing `full_note`
parameter where the shared sentence would mislead. No new module, no
window-policy table, no per-site abstraction.

**`work_queue.ready_issue_numbers` now passes a `full_note`** naming the
real remedy: raise `LIST_WINDOW` in `work_queue.py` (or narrow
`LIST_ARGS`) and redeploy — a code edit, stated as one, not phrased as a
runtime flag. This is the same mechanism `sweeps.known_keys` already
uses for the identical reason (a caller-specific consequence the shared
sentence cannot say), so it adds no new machinery.

## Consequences

- The five sites' policies are now the source a future review reads
  instead of re-deriving by grep — this ADR is that index, not a new
  runtime concept.
- `work_queue.py`'s full-window message no longer implies an option the
  reader cannot reach; `tests/test_work_queue.py` pins both the new
  wording and the absence of the old, misleading sentence. Payload twin
  and `factory/manifest.json` regenerated in the same commit
  (`work_queue.py` is a `factory_init.MIRRORS` identity entry).
- `cli.gh_read`'s docstring already states this design in miniature
  ("the seam states the fact and the CALLER decides what it means"); this
  ADR is the decision record that prose was implementing, made
  explicit and citable.
- If a sixth `gh`-listing site is ever added with a genuinely novel
  policy, the question this ADR answers is still "declare it here," not
  "build the seam now" — three real policies across five callers is not
  evidence for a sixth caller changing that arithmetic on its own.
