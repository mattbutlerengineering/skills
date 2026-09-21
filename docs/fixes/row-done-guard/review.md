---
stage: review
run: maintenance:row-done-guard
date: 2026-08-23
assumptions: ["Severity was not arbitrated live — this run is autorun-driven. All three findings are called minor, which the review skill lets a run defer freely; none is a defect in the change, and calling any of them major would have been inflation."]
---

# Review: the guard goes at the owner

## Scope

Commits `63a1711` and `4520083` on `agent/issue-327-row-done-guard` against
`main`: `knowledge_plane.py` (+10/−0), `tests/test_knowledge_plane.py`,
`tests/test_gates.py`, the mirrored payload copy and `factory/manifest.json`,
the run's artifacts, and one claimed seed line in `docs/backlog.md`.

Read alongside the diff, because the change is about what they see:
`gates.merged_wo_rows` (gates.py:581), `work_queue.rows` (work_queue.py:70),
`plane_drift` (plane_drift.py:90), and `protocol._CHECKBOX` (protocol.py:71).

## Findings

### Minor: the guard widens the gap with `protocol._CHECKBOX`, and nothing says so

- Scenario: the decayed contract, not a defect. ADR-0058 fixed the roster
  at two owners and left a caveat — "change the bullet shape in one and
  the other must move with it". This run does not change a bullet shape,
  but it does change which lines `row_done` accepts, and the two owners
  now disagree on three shapes where they previously agreed:

  ```
    line                                     row_done  _CHECKBOX
    '- [x]'                                  False     True  box='x'
    '- [x]a WO-0002 no space'                False     True  box='x'
    '- [x]**WO-0003** bold'                  False     True  box='x'
  ```

  The divergence is correct — `ROW` has always required trailing
  whitespace and every other accessor has always diverged from
  `_CHECKBOX` on exactly these shapes, so the run makes `row_done` join
  its own module rather than drift from it. But the caveat as written
  reads as "these two must agree", and nothing in the tree records that
  its scope is bullet shape rather than the whole grammar. The next
  reader who runs this comparison will read the difference as drift.
- Decision: **deferred** — the fix is a sentence or a test pinning the
  intended divergence, and both are edits to ADR-0058's territory, which
  belongs to whoever curates the roster rather than to a correctness fix
  passing through. Seeded at Operate.

### Minor: a bare `- [x]` flips from done to not-done, and the scan is why that is safe

- Scenario: `breakdown_files` splits with `splitlines()`, so lines carry
  no trailing newline. A line that is exactly `- [x]` — checked box,
  nothing after it — was `True` to `row_done` before this run and is
  `False` after. No consumer is affected (it carries no work-order token,
  so detector G ignores it either way, and the other three call sites gate
  on accessors that already returned nothing for it), but the flip is real
  and was not stated in `architecture.md`'s contract section, which
  described the narrowing only in terms of `DONE_ROW`-not-`ROW` lines.
- Decision: **no action, recorded**. The pre-fix tree scan in `defect.md`
  covers this shape — it looked for exactly `row_done(line) and not
  ROW.match(line)`, which a bare `- [x]` would have satisfied while the
  accessor was loose, and it found zero over 1460 lines. So the case is
  measured, not merely argued. Written down here so a future reader finds
  it rather than rediscovering it.

### Minor: detector G still reads the raw line where an accessor exists

- Scenario: `merged_wo_rows` keeps `wo = WO_TOKEN.search(line)`, which is
  why it was the one path where the two grammars could disagree in
  production. With `row_done` guarded, the disagreement is gone — but the
  *shape* that produced it remains: G is the only reader of breakdown rows
  that parses one by raw regex instead of through `knowledge_plane`'s
  accessors, and `row_work_order` exists and returns exactly what G wants.
- Decision: **deferred** — `architecture.md` names it as the rejected
  alternative and says it is worth doing separately; folding it in here
  would have made the run's central claim (fixing the owner is enough)
  untestable, because both changes independently close the escape. Seeded
  at Operate.

## Passes with no findings

- **Design.** The change matches `architecture.md` exactly: the guard is
  at the owner, written in the siblings' early-return shape, and
  `gates.py`, `work_queue.py`, `plane_drift.py` and `dashboard.py` are
  byte-identical to `main`. `DONE_ROW` was not retired and ADR-0058's
  roster is untouched, both deliberately. No ADR was written and none is
  owed — ADR-0058 already recorded this gap as open, so the decision is
  expected in context, and the ADR was not edited to point at this run.
- **Security.** No new input surface, no external call, no secret, no
  injection path. The change narrows what a parser accepts, which is the
  safe direction; the module remains pure and filesystem-free at the
  accessor level.
- **Correctness, beyond the findings.** Every checked-row shape the suite
  already knew still passes (tab after the bullet, `+`/`*` bullets,
  indented rows, double-spaced bullets, uppercase `[X]`); the agreement
  property holds across all fourteen shapes tested; the full battery is
  green at 1347 tests with `lint`, `gates` and `selftest` clean.

## Verdict

Ready to ship. Three minor findings, none blocking: one is recorded as
measured-and-safe, two are deferred with reasons and owe backlog seeds at
Operate.
