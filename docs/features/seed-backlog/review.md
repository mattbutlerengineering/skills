---
stage: review
run: feature:seed-backlog
date: 2026-07-06
---

# Review: seed backlog

## Scope

The 8-commit diff `main...feat/seed-backlog` (1ac1042..df6323e): run
artifacts, `docs/pipeline-protocol.md` seed-backlog section, `protocol.py`
grammar (`_BACKLOG_RUN_REF`, `_BACKLOG_ENTRY`, `parse_backlog`,
`check_backlog`), `lint.py` checker registration, prose wiring in
`skills/operate|next|idea|capture/SKILL.md`, `tests/test_backlog.py`,
`tests/test_lint_checkers.py` additions, and the real `docs/backlog.md`.
Reviewed inline in three passes (correctness, design, security) after a
dispatched reviewer agent stalled twice with no output.

## Findings

### Minor: mis-ordered claim marker silently reads as unclaimed

- Scenario: a hand-written entry with the markers reversed —
  `- fix the thing (claimed: feature:x) (from: session:2026-07-05)` —
  fullmatches the grammar with the `(claimed: …)` text lazily absorbed into
  the seed text. Confirmed live: `parse_backlog` returns
  `claimed: None` and `check_backlog` returns `[]`, so a claimed seed would
  be re-proposed by `next` as available. (Duplicate markers and trailing
  garbage do fail the match and get reported; only this exact reversal
  slips through.)
- Decision: deferred — the documented grammar is explicit about order, the
  file is small and hand-edited under skill instruction (operate/idea write
  the canonical form), and the consequence is a duplicate proposal a human
  would catch at claim time. Tightening the regex to reject `(claimed:`
  inside seed text is cheap if this ever bites; parked as a known edge, not
  worth a grammar complication pre-first-use.

### Minor: lint checker inherits repo-wide decode-error exposure

- Scenario: a `docs/backlog.md` with invalid UTF-8 raises
  `UnicodeDecodeError` out of `read_text` (`lint.py:173` catches `OSError`
  only), crashing lint with a traceback instead of a problem string.
- Decision: deferred — not a deviation: every sibling checker
  (`lint.py:111,159,190`) uses bare `read_text` with no handling at all;
  this checker is already the most defensive of the set. Fixing it here
  alone would be inconsistent; a repo-wide `errors=`/except policy is a
  separate maintenance seed if ever wanted.

## Passes with no findings

- **Correctness** — beyond the minor above: `fullmatch` anchoring is
  correct for all four run-ref alternatives (no prefix leaks like
  `products`); `splitlines` handles CRLF; duplicate/extra claim markers and
  trailing whitespace fail closed (reported by check, skipped by parse);
  parse/check divergence on malformed lines is the documented contract.
  Tests (9 in `test_backlog.py`, 3 exact-string in `test_lint_checkers.py`)
  cover conformant, malformed-bullet, bad-run-ref, claimed, and
  non-bullet inputs through public functions only. Suite 146 OK, lint 0/15.
- **Design** — code matches `architecture.md`'s contracts exactly: grammar
  lives in `protocol.py` (ADR-0021 charter), lint checker is a thin caller
  returning `backlog: line N: …` label-prefixed strings, absent file → `[]`
  (strictly opt-in), `docs/backlog.md` has no frontmatter (the deliberate
  design signal). Skill prose lands at the planned insertion points; no
  `description:` frontmatter line was touched (trigger evals stay pinned —
  verified by grep during Verify).
- **Security** — local file read only, no execution or injection surface;
  the one error message exposes only the OS error text, matching siblings.

## Verdict

Ready to ship. No critical or major findings; both minors deferred with
reasons above. Next stage is Ship.
