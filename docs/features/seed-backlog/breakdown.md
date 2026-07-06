---
stage: decompose
run: feature:seed-backlog
date: 2026-07-05
---

# Breakdown: seed backlog

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met. No tracker mirror (opted out).

## Milestone 1: Convention is checkable — lint validates a backlog file

- [x] **Protocol section** — add "Seed backlog (optional)" to
  `docs/pipeline-protocol.md`
  - Accept: section defines location (`docs/backlog.md`), both entry forms,
    all four `run-ref` forms (`product` | `feature:<slug>` |
    `maintenance:<slug>` | `session:<YYYY-MM-DD>`), producers, consumers'
    two read moments, in-place claim rule, and the advisory rule
    ("orientation never reads backlog state"), phrased parallel to the
    tracker-mirror section.
  - Blocked by: —
- [x] **Backlog grammar in protocol.py** — `parse_backlog(text)` and
  `check_backlog(text)`
  - Accept: parse returns entries `{text, origin, claimed}` (claimed may be
    None) and skips malformed lines; check returns `backlog: line N: …`
    problem strings, `[]` when conformant, and never raises — tests cover
    conformant, malformed-bullet, bad-run-ref, claimed, and non-bullet-line
    inputs through the public functions.
  - Blocked by: Protocol section
- [x] **Lint checker** — register `check_backlog` in `lint.py` `CHECKERS`
  - Accept: `docs/backlog.md` validated when present; absent file yields no
    problems; unreadable file yields one problem string; exact-string tests
    in `tests/test_lint_checkers.py`; `python3 lint.py` exits 0 on the repo.
  - Blocked by: Backlog grammar in protocol.py

## Milestone 2: Skills carry the loop

- [x] **operate appends** — extend `skills/operate/SKILL.md` step 6
  - Accept: instructs appending each retro seed to `docs/backlog.md` as a
    well-formed entry at run close (create the file if absent; never rewrite
    existing lines).
  - Blocked by: Protocol section
- [x] **next reads at two moments** — extend `skills/next/SKILL.md`
  - Accept: the no-active-run branch and the completed-run step both list
    unclaimed seeds and offer to start from one; text states the backlog is
    never read during active-run orientation.
  - Blocked by: Protocol section
- [ ] **idea claims (+ capture parks)** — extend `skills/idea/SKILL.md` and
  `skills/capture/SKILL.md`
  - Accept: idea, when starting from a seed, appends `(claimed: <run-ref>)`
    to the seed line in place and records the origin in `idea.md`; capture
    gains one sentence noting a deferred defect may be parked as a seed.
  - Blocked by: Protocol section

## Milestone 3: Seeded for real

- [ ] **Create docs/backlog.md with this session's seeds** — the real
  orphaned follow-ups, plus this run's own seed marked claimed
  - Accept: file exists with ≥5 real seeds carrying
    `(from: session:2026-07-05)` (omp `skill://` protocol-doc gap,
    `next-maintenance-1` under-trigger, omp near-miss under-triggering,
    Pi description-limit unit, ship changelog step, deprecation/sunset
    runs), plus this feature's seed line marked
    `(claimed: feature:seed-backlog)`; `python3 lint.py` exits 0.
  - Blocked by: Lint checker

## Design gaps found

None.

## Notes

(Deviations discovered during Implement get logged here, dated.)
