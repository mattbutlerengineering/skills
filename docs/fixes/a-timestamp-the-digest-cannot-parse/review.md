---
stage: review
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-22
assumptions:
  - "No diff to review, by design: this run's Implement stage added zero lines of source, test, template, manifest, or ADR content (breakdown.md's single checkbox is a re-confirmation, not a code change). Per this dispatch's own instruction, this artifact reviews the closure REASONING instead of a diff — adapted from the review skill's normal diff-scoped process, per its own soft-gating rule for an unusual predecessor shape."
  - "Verification green, not unverified: verification.md exists and all 7 of defect.md's success criteria are marked PASS with quoted command output, so the normal predecessor gate is satisfied. The unusual part is that the underlying fix predates this run's own Implement stage (it shipped via PR #326 and PR #499, both independently seeded), not that Verify was skipped or weak."
  - "Every command in 'Independent re-verification' below was executed fresh by this stage, at this stage's own HEAD (still 47b6937 — no commits landed on main during this review), rather than copied from architecture.md/breakdown.md/verification.md's quoted output. Where this artifact's own output differs cosmetically from a prior stage's (e.g. one_owner.py's trailing newline, buffered-stdout ordering), that is noted rather than silently reconciled."
---

# Review: a timestamp the digest cannot parse — closure claim, adversarially re-checked

## Scope

No code diff exists for this run to review — Implement's own breakdown item
(A1) added no source, test, template, manifest, or ADR file, and `git
status` at HEAD `47b6937` confirms the only changes in the tree are this
run's own artifacts (`architecture.md`, `autorun-brief.md`, `breakdown.md`
modified; `verification.md` new). What this review instead examined:

1. **The two PRs the closure claim rests on**, read in full rather than
   taken from architecture.md's prose: `git show 9324d31` (PR #326) and
   `git show b6b365c` (PR #499), diffed sentence-by-sentence against each of
   `defect.md`'s 7 success criteria.
2. **Caller enumeration**, re-derived by grep rather than trusted from
   `defect.md`'s or `architecture.md`'s own tables: every importer of
   `human_gates.label_events`, `_parse_ts`, `_is_timestamp`, and
   `refused_timestamps` across the repo (excluding stale worktree copies
   under `.claude/worktrees/`).
3. **`dashboard._age_seconds`'s claimed incidental closure**, verified by
   reading `dashboard.py`'s `_queues`/`_timeline`/`waiting_since` call chain
   directly, not by citing the claim.
4. **ADR-0056's status and the no-ADR-0062 reasoning**, checked against the
   actual three-part bar (found in `skills/architect/SKILL.md`, not
   `canon.md` as architecture.md's prose implies — see Findings) and against
   ADR-0056's own text.
5. **The two cited deferrals** (`rejection_mining` forwarding;
   the narrower reporting asymmetry), checked by reading
   `docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md` itself
   rather than trusting the citation.
6. **Independent re-execution** of defect.md's §1/§3 repro histories through
   the real `gate_digest.run_daily`/`main`/`rejection_mining.run_mine`, and
   of the full verification battery, fresh, in this stage's own shell.

## Independent re-verification (this stage, fresh, HEAD `47b6937`)

- **Ancestry**: `git merge-base --is-ancestor b6b365c HEAD` and `... 9324d31
  HEAD` both confirm true; `b6b365c`'s commit timestamp
  (2026-09-21T07:14:02-07:00) predates `HEAD`'s (2026-09-21T20:38:57-07:00).
- **Repro**: re-ran defect.md's §1 (completed/confirmed stay, malformed
  closing timestamp) and §3 (open stay, malformed labeled timestamp)
  histories through `gate_digest.run_daily`/`main` and
  `rejection_mining.run_mine`, built from scratch rather than pasted from
  verification.md. Both: `main -> exit 1`, problem string `"gd: timeline for
  #106 refused 1 malformed timestamp(s)"`, no traceback;
  `rejection_mining.run_mine` clean, `problems: []`, on both. Matches
  `verification.md` exactly.
- **Battery**: `python3 -m unittest discover tests` → `Ran 1700 tests ...
  OK`, exit 0. `python3 -m unittest tests.test_human_gates
  tests.test_gate_digest tests.test_dashboard tests.test_rejection_mining`
  → `Ran 193 tests ... OK`, exit 0. `python3 lint.py` →
  `lint: 0 problem(s) across 25 skills`. `python3 gates.py && python3
  gates.py --selftest` → `gates: 0 problem(s)`, `selftest: ok`. `python3
  one_owner.py` → 7 problems, none touching `human_gates.py`, and the two
  findings naming `gate_digest.py`/`dashboard.py`/`rejection_mining.py` are
  about shared `gh issue list` argument tuples and issue-listing payload
  keys, not timestamp handling.
- **Mirrors**: `human_gates.py`, `gate_digest.py`, `rejection_mining.py` all
  diff clean against their `factory/templates/tools/factory/` twins.
  `dashboard.py` confirmed absent from `factory_init.MIRRORS`.
- **ADR-0056**: `- Status: accepted`, confirmed by reading the file, unchanged.

No discrepancy found against any of architecture.md's, breakdown.md's, or
verification.md's quoted evidence.

## Findings

### Low: `_admit`'s "one pass" framing is aspirational, not literal, at both call sites

- Scenario: `gate_digest._timelines` and `dashboard._timeline` each do:
  `refused = refused_timestamps(raw)` followed by `label_events(raw)`.
  `refused_timestamps` and `label_events` are each one-line wrappers
  (`return _admit(timeline)[1]` / `[0]`) around the same private walk, so
  every call site that wants both the admitted list and the refused count
  runs `_admit` over the same raw timeline **twice**, not once. PR #499's
  own commit message and `_admit`'s docstring both frame this as "one pass
  over the raw timeline, so the two questions cannot drift apart" — true in
  the sense that there is one *spelling* of the walk (a real `one_owner.py`
  win, confirmed above), but the two questions still cost two traversals
  per caller invocation. For a GitHub issue timeline (tens of events,
  fetched and walked once per issue per scheduled daily run) this is
  immaterial in absolute cost; it is a documentation-vs-implementation gap,
  not a performance defect, and it changes no output.
- Decision: **not fixed, not this run's to fix.** This is pre-existing,
  already-reviewed, already-shipped code from PR #499
  (`a-malformed-timestamp-is-silently-dropped/review.md` finding 1 reviewed
  the `_admit` refactor and found it eliminated a real `one_owner.py` risk;
  it did not claim single-traversal performance, only single-spelling
  correctness). Flagged here per this dispatch's explicit instruction to
  report anything worth flagging in the shipped state, fresh — not a defect
  in this run's closure claim, and not something Review can fix (Review
  reports, it doesn't patch, and this run's own scope is verification and
  closure, not code).

No medium, high, or critical findings.

## Passes with no findings

- **Correctness of the closure claim.** Every one of `defect.md`'s 7
  success criteria was checked against the actual shipped diffs (`9324d31`,
  `b6b365c`), not just architecture.md's Traceability table, and each holds
  on inspection of the code, not just on re-running the same commands prior
  stages already ran. In particular: criterion 4's disjunction ("removed or
  recorded as intentional in an ADR") is satisfied on the "removed" branch
  for the *specific* crash-shaped asymmetry §6 evidenced (neither
  `gate_passages` nor `gate_rejections` raises on any refused-timestamp
  history any more, confirmed above) — a narrower, reporting-only asymmetry
  is a different, smaller thing than what §6 measured, correctly
  distinguished rather than conflated in architecture.md's own text.
- **Caller completeness.** Re-derived, not trusted: `gate_digest.py`,
  `dashboard.py` (both call `refused_timestamps` + `label_events`);
  `rejection_mining.py` (imports `label_events` only — confirmed by
  `grep`); `tests/test_human_gates.py` and `tests/test_cost_ledger.py`
  (the latter imports only the `GATES` constant for test fixtures, never
  touches timestamp parsing); `gates.py` detector J (`gate_labels()` only,
  label names, no timestamp field). No caller of `label_events`,
  `_parse_ts`, `_is_timestamp`, or `refused_timestamps` exists outside this
  set. No third exposure found beyond what `defect.md`/`architecture.md`
  already name.
- **`dashboard._age_seconds`'s incidental closure**, verified by reading
  the code rather than the claim: `dashboard._queues` computes `since =
  waiting_since(events, queue_label)` where `events` is
  `label_events(raw)`'s output; `waiting_since` (`human_gates.py:209`)
  only ever returns a `ts` drawn from that already-admitted list. Since
  `label_events` admits no event whose timestamp fails `_is_timestamp`,
  `_age_seconds` can never receive a value that would raise. Confirmed, not
  assumed.
- **ADR-0056 / no-ADR-0062 reasoning.** ADR-0056's decision text names an
  ownership scope, not a closed API surface — adding `_admit` (private) and
  `refused_timestamps` (public pure function) to `human_gates.py` extends
  the module without contradicting the decision. The "no ADR" call is
  checked against the actual three-part bar (`skills/architect/SKILL.md`:
  "hard to reverse, surprising without context, and the result of a real
  trade-off," all three required) rather than taken on faith: deleting
  `refused_timestamps` and its two call sites reverts exactly to #326's
  shipped behavior (one line, confirmed in `release.md`'s own rollback
  section) — genuinely not hard to reverse — so the bar fails on that
  clause alone regardless of the other two. Not a rationalization.
  (Architecture.md attributes the bar to `canon.md`; it actually lives in
  `skills/architect/SKILL.md` — a citation slip, not a substantive error,
  and not worth a Findings entry since the rule itself is quoted and
  applied correctly.)
- **The two cited deferrals, checked against the source, not the
  citation.** `docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md`
  really does contain, verbatim, the "Follow-up recorded, not actioned"
  section architecture.md/breakdown.md/verification.md quote: item 1 on
  `rejection_mining.py` staying silent ("Not costing it anything observable
  today ... one line to add there if a future caller ... starts to need
  it") and item 2 on no live occurrence ever being observed. Both are real,
  both predate this run by one day, neither is fabricated or
  misrepresented.
- **Security.** No new input-handling code exists to review (no diff). The
  shipped admission gate (`_is_timestamp`) validates a decoded API response
  field before use, the `isinstance` check prevents a non-string
  `created_at` from reaching `.replace()`, and no problem string echoes
  timeline payload content beyond an issue number and a count. Nothing
  here changed in this run, and nothing found is new.

## Verdict

**The closure claim holds.** `defect.md`'s problem — a malformed-but-truthy
gate-timeline timestamp producing a traceback instead of a `gd:`-prefixed
problem string — does not reproduce against real `main` at `47b6937`,
independently confirmed by re-running the exact repro this stage built
from scratch (not copied) through the live `gate_digest.run_daily`/`main`.
All 7 of `defect.md`'s success criteria are met by the already-shipped,
already-reviewed code in PR #326 and PR #499; no gap, no missed caller, no
weakened test, and no unjustified ADR-skipping was found on adversarial
re-check. The one finding (low) is a documentation/implementation nuance in
already-shipped code with no bearing on correctness or on any success
criterion, and is not this run's to fix. Ready to proceed to Ship, which
this run's own artifacts already record as prepare-and-stop with no
externally visible release action.

Only file written by this stage: `review.md`.
