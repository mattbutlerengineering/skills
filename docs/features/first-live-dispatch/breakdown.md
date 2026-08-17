---
stage: decompose
run: feature:first-live-dispatch
date: 2026-08-17
---

# Breakdown: first live dispatch

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Row grammar per v1: one line per work
order carrying id, size class, blocking edges, and the PRD citation
detector A checks; tracker mirror numbers are appended per ADR-0032
after each row exists here first. WO ids continue the repo-global
sequence from v1's last order, 0035 (the prefix is dropped here because
detector A reads any line bearing a work-order token as a row needing a
PRD citation — v1's breakdown records the same dodge).

## Milestone A: Armed (both secrets exist; the factory is dispatch-capable with the breaker live)

- [ ] **WO-0036** mint ANTHROPIC_API_KEY and set it as an Actions secret — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: `gh secret list` shows ANTHROPIC_API_KEY; the value is console-set and never touches the repo, shell history, or chat.
- [ ] **WO-0037** mint FACTORY_PAUSE_TOKEN and set it as an Actions secret — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: `gh secret list` shows FACTORY_PAUSE_TOKEN; the PAT is fine-grained, scoped to this repo alone, Variables read/write only.

## Milestone B: Traversal (one real order through all three gates to a merged PR with real spend recorded)

- [ ] **WO-0038** author the payload's mirror issue at the gate line — size:S, blocked by: WO-0036, WO-0037 (PRD-0003 §Success criteria)
  - Accept: the payload row below is on main BEFORE its mirror issue exists (ADR-0032 one-way); the issue is labeled `type:chore` + `wo:draft` and its number is appended to the payload row as its tracker ref.
- [ ] **WO-0039** gates.py J-roster agreement — the dispatched payload — size:S, blocked by: WO-0038 (PRD-0003 §Success criteria)
  - Accept: gates.py's detector-roster docstring, the DETECTORS `"J"` entry, and the unclaimed-letters comment all agree detector J is claimed and implemented (K stays unclaimed); the battery stays green. Delivered by the dispatched agent as a PR closing the mirror issue — never by hand.
- [ ] **WO-0040** gate walk and supervised dispatch — size:S, blocked by: WO-0038 (PRD-0003 §Success criteria)
  - Accept: Matt applies `wo:prd-approved`, `wo:blueprint-approved`, then `wo:ready-for-agent` on the mirror issue, each after reading what the gate approves; the assembler run concludes `success`; the agent's PR closes the issue via the Closes grammar; the spend row lands on main workflow-committed with real nonzero tokens; the validator hand-off fires and the order flips to `wo:needs-review` untouched by hands.
- [ ] **WO-0041** gate 3: review, merge, close out — size:S, blocked by: WO-0040 (PRD-0003 §Success criteria)
  - Accept: Matt reviews and merges the agent's PR manually; the order reaches `wo:merged`; detector G is green on the close-out; the payload row above is checked as merged.

## Milestone C: Breaker proven (the stop machinery has fired for real and the run's evidence is verification-grade)

- [ ] **WO-0042** fire the breaker on real spend and prove dispatch inert — size:S, blocked by: WO-0041 (PRD-0003 §Success criteria)
  - Accept: a PR lowers `monthly_cap_usd` to 0.01 with `factory_init.py update-manifest` in the same commit; a `workflow_dispatch` cost-report run computes PAUSE from real rows and itself sets `FACTORY_PAUSED=true`; an owner-applied ready label while paused yields an assembler run concluding `skipped`; a second PR reverts the cap (manifest regenerated); Matt clears the flag by hand.
- [ ] **WO-0043** evidence bundle and spend rollup — size:S, blocked by: WO-0042 (PRD-0003 §Success criteria)
  - Accept: every PRD-0003 success criterion has a quotable, fenced check recorded for Verify (run conclusions, label timelines, ledger rows, secret names); the ledger rollup shows total run spend ≤ $10.

## Design gaps found

None — every component in architecture.md's seven phases maps to a row
(phase 1 → Milestone A's two rows; phase 2 → the authoring row and the
payload row; phases 3–4 → the gate-walk row; phase 5 → the gate-3 row;
phase 6 → the breaker row; phase 7 → the evidence row), and every PRD
success criterion is covered by an Accept line above.

## Notes

- 2026-08-17: the payload row (WO-0039, PRD-0003 §Success criteria)
  carries no tracker ref at draft time — ADR-0032's one-way rule means
  the mirror issue is created only after this file lands on main; the
  authoring row (WO-0038, PRD-0003 §Success criteria) appends the ref
  as part of its acceptance.
- 2026-08-17: only the payload row is mirrored to the tracker — the
  owner-work rows (arming, gate walk, breaker, evidence) are
  supervision steps the dispatch plane never reads, and mirroring them
  would put non-dispatchable rows in front of the ready-label flow for
  no consumer.
- 2026-08-17: the retro's prerequisite lesson applied — the secrets are
  explicit Milestone A rows and every dispatch-path row is blocked on
  them, so the run cannot reach a supervision window with its
  prerequisites unowned (the amendment class v1's supervised-exercise
  row hit cannot recur here).
- 2026-08-17: owner-work rows are checked by the operator during
  Implement with evidence quoted at check time; the ledger gets rows
  only for the dispatched run itself — owner supervision is not a paid
  model run and gets no fabricated spend row (eval-honesty).
