---
stage: decompose
run: maintenance:quoted-token-is-not-a-claim
date: 2026-08-23
assumptions:
  - "The cut was not reviewed live — this run is autorun-driven, so the two items, their sizes and their order are read out of architecture.md's Components and Interfaces & contracts sections rather than from the operator's judgment. A mis-sized row is a note to log at implement time, not a design change."
  - "Rows carry an item id and a size class (ADR-0034 vocabulary) and no work-order id and no (tracker: #N) reference, matching every maintenance run in docs/fixes/. Minting a WO-#### with no breakdown-row-then-issue behind it would run the dispatch plane ahead of the knowledge plane (ADR-0032). Illustrative work-order tokens below are written WO-00xx on purpose: detector A reads EVERY line of a breakdown file, not only checkbox rows, so a live four-digit token in prose is a false A finding — the same collision this run's own defect describes, one plane over."
  - "The characterization item comes FIRST and lands green. The test-ordering rule says new tests at the intended interface precede the change; here the interface already exists, so the pin is written against today's code, passes today, and must pass unchanged after A2. That is stronger than writing it afterwards, where a pin that only ever saw the new code proves nothing about what was preserved."
---

# Breakdown: pin what must not move, then move one expression

Progress lives in the checkboxes below. Source is `architecture.md` in this
directory, which decided to strip quoted material from the text the skip
gate reads and to leave `cited_work_order` alone.

**The ordering rule, which decides the cut.** A1 pins the passing
direction against today's code — a quoted token that nonetheless resolves
still flips its label — and must pass unchanged after A2. A2 writes the
failing cases, watches them fail for the right reason, then changes the one
expression. No test written in A1 is edited in A2; if one needs editing,
that is the signal to revert A2, not to edit the test.

**The battery is green at every item.** `python3 -m unittest discover
tests`, `python3 lint.py` (`lint: 0 problem(s)`) and `python3 gates.py &&
python3 gates.py --selftest` (`gates: 0 problem(s)`, `selftest: ok`).
`validator.py` is a `factory_init.MIRRORS` entry, so A2 runs `python3
factory_init.py update-manifest` and commits the regenerated payload twin
and manifest in the same commit — otherwise detector E fires on the
manifest and `tests/test_factory_init.py` on the twin, and the item cannot
close. A1 touches tests only, so it has no payload twin and no manifest
churn, and that is asserted by the item leaving `factory/` untouched.

## Milestone A: a fence is evidence, not a claim (one expression changes; every label flip that happens today still happens)

Item 1 and item 2 of the design.

- [x] **A1** pin the passing direction, against today's code — size:S, blocked by: —
  - Accept: a new case in `TestRunLifecycle` (tests/test_validator.py:534) drives `run_lifecycle` with a body whose only work-order token sits inside a fenced block and whose `Closes #109` sits outside it, and asserts the flip still reaches issue 109 — the same `issue edit` argv the neighbouring `test_merged_pr_flips_the_work_order_to_the_target_label` asserts. It passes against today's code, before any change to validator.py, and the commit message says so. `test_a_mentioned_work_order_does_not_get_the_merged_label` (:590) already pins the prose half of the same property and is not touched. No production file changes in this item; `factory/` is untouched, so no manifest regeneration and detector E is green by construction.
- [x] **A2** the gate reads the body with quoted material removed — size:S, blocked by: A1
  - Accept: `validator._unquoted(body)` returns the body with ``` ``` ```/`~~~` fenced regions and lines beginning with optional whitespace then `>` removed, and `run_lifecycle`'s skip gate reads `not WO_TOKEN.findall(_unquoted(body))` instead of `not WO_TOKEN.findall(body)`. New cases in `TestRunLifecycle`, each written and watched to fail for the right reason first: a body whose only token is inside a fence is a silent no-op under `uncited="skip"` (`problems == []`, `run.calls == []`); so is one whose only token is inside a blockquote; a tilde fence behaves as a backtick fence does; an unterminated fence swallows the rest of the body and therefore also skips. And the boundary that must NOT move: a body naming a work order in ordinary prose with inline-code backticks around the id — the WO-00xx form this repo writes identifiers in — still returns the no-Closes problem, so backticks are typography and not quotation. `test_the_merged_leg_keeps_a_malformed_citation_loud` (:710), `test_the_relaxation_must_be_asked_for` (:682) and `test_uncited_skip_still_flips_a_cited_work_order` (:670) pass UNCHANGED, as does A1's pin. `cited_work_order` (validator.py:233) is not edited. `validator.py` is mirrored: payload twin plus manifest regenerated in the same commit; detector E green; full battery green.

## Notes

Deviations, dated, as they happen.

- **2026-08-23, A2 — `architecture.md`'s Stack paragraph was wrong about
  `re`.** It said "stdlib `re`, already imported"; `validator.py` imports
  `os`, `sys`, `tempfile` and `pathlib` and no `re`, taking its two token
  patterns from `knowledge_plane`. Rather than add an import for one
  helper, `_unquoted` is a line walk over `str.lstrip`/`str.startswith`,
  which also expresses fence state across lines more directly than a
  pattern would. The interface, the stripping rule and the decision are
  unchanged, so this is a correction to a factual claim about the file and
  not a design change; the paragraph in `architecture.md` now says what
  landed and points here.
- **2026-08-23, A2 — one pre-existing 80-column line in `validator.py`.**
  `validator.py:178` is 80 characters and was before this run
  (`git show HEAD:validator.py | awk 'length > 79'` names it and nothing
  else). It is outside this run's scope and is left alone; every line this
  run adds is inside 79.
