---
stage: decompose
run: maintenance:run-discovery-ignores-open-prs
date: 2026-08-25
assumptions:
  - "One milestone, four items, ordered so the pin is written and RED before either skill recites. The repo's TDD convention wants the failing check first, and here the check IS the test: I2 lands with both starting skills still silent, so its two problem strings are observed rather than predicted, and I3/I4 each clear exactly one."
  - "No manifest regeneration item, because this run touches nothing mirrored. Verified against factory_init.MIRRORS rather than remembered: it names root tools, six workflows, CODEOWNERS and the Makefile — `lint.py`, `docs/pipeline-protocol.md` and `skills/**` appear nowhere in it. If that turns out wrong the run gains an item; it does not quietly skip one."
---

# Breakdown: ask before starting

**Files this run touches**, chosen for conflict surface as much as for
design — the check that this run exists to institutionalise, run on
itself:

| file | claimed by an open PR? |
|---|---|
| `docs/pipeline-protocol.md` | no |
| `skills/capture/SKILL.md` | no |
| `skills/idea/SKILL.md` | no |
| `lint.py` | **#324** — hunks at 17, 33–82, 543–586 |
| `tests/test_lint.py` | **#324** — hunks at 70, 531+ |

Nothing mirrored, so no manifest.

## Milestone 1 — the rule has an owner and cannot rot

- [ ] **I1 — the protocol states the rule.**
  A `### Work already in flight` subsection immediately after the **Run
  discovery** paragraph in *Runs and run directories*: run discovery sees
  the working tree; finished work elsewhere sits on a branch behind an
  open change proposal; the moment a run starts is where that is checked;
  a check that could not run is said out loud; a true duplicate stops the
  run. Names its relationship to `work-queue`'s merge-order preflight so
  the two do not read as copies (D5), and states that it is a guard, not a
  second inbound door (the one-way bound is untouched).
  *Acceptance:* the section exists with that heading, `python3 lint.py`
  and `python3 -m unittest discover tests` stay green, and the four
  `tests/test_protocol_*.py` suites pass **unedited** — the fourth success
  criterion, that no existing orientation behaviour changes, has no better
  evidence than the orientation suites not moving.

- [ ] **I2 — the recital pin, written RED.**
  A helper in `lint.py` beside `_capture_problems`, called from
  `check_skill_recitals` for `capture` (maintenance loop) and `idea`
  (spine loop) — not a new top-level checker, which would be a second
  owner of "skills recite protocol facts" and would touch `main()`, the
  region #324 edits.
  *Acceptance:* with neither skill yet reciting, `python3 lint.py` reports
  exactly two problems naming `skills/capture/SKILL.md` and
  `skills/idea/SKILL.md`; new cases in `tests/test_lint.py` assert those
  exact strings through the public checker, and the pre-existing
  `test_lint` cases pass unedited.

- [ ] **I3 — `capture` recites it.**
  At the two moments capture starts a run: seed claim (step 2) and
  tracker-intake seeding (step 3), before `defect.md` is written.
  *Acceptance:* the capture problem string clears, the idea one does not —
  observed as one problem, not zero, which is what proves the pin
  discriminates rather than merely passing.

- [ ] **I4 — `idea` recites it.**
  At its seed-claim moment (step 2).
  *Acceptance:* `python3 lint.py` reports `0 problem(s) across 24 skills`,
  the full battery is green, and `python3 one_owner.py` adds no group.

## Notes

*(deviations logged here, dated, as they happen)*
