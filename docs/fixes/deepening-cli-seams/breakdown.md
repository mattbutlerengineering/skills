---
stage: decompose
run: maintenance:deepening-cli-seams
date: 2026-08-12
assumptions:
  - "defect.md absent (capture not run) — the condition brief is the deepening review of commit 57635f6, 2026-08-11; re-entry depth would be architect. Until capture seeds defect.md the router orients this run to capture, not implement"
  - "architecture.md absent — design source is the review's confirmed evidence (call sites walked, not inferred) plus ADR-0051, ADR-0046 and ADR-0037/ADR-0039; only Card 1 was designed, so Cards 2 and 4 are recorded as design gaps rather than decomposed"
  - "no PRD — this is maintenance work with no PRD section to cite, so rows carry no WO id and no PRD citation (detector A only holds WO rows to that rule)"
---

# Breakdown: deepening — the cli seams and the front door

Progress lives in the checkboxes below. Source: the deepening review of
`skills` at commit 57635f6 (2026-08-11), which walked four candidates and
graded them Strong / Worth exploring / Worth exploring / Speculative. Rows
carry an item id, a size class (ADR-0034 vocabulary) and blocking edges;
they carry no WO id because no work order exists for them — if they are
mirrored to a tracker later, these checkboxes stay the state (ADR-0026).

## Milestone A: the report seam is finished (no tool retypes the summary line; both mirrored tools gain their first CLI contract coverage)

Card 1, graded Strong — four call sites walked. `cli.report` (cli.py:67–82)
has ten adopters; `work_queue.py` and `budget_guard.py` retype the epilogue
in four places. Both files landed hours *before* the ADR-0051 fold shipped
(#221 and #245 on 2026-08-10, fold in #247), so this finishes that decision
rather than reopening it. Both are `factory_init.MIRRORS` entries
(factory_init.py:136,141), so every edit here regenerates the payload
checksum manifest in the same commit.

- [x] **A1** pin `work_queue.main`'s summary line before touching it — size:M, blocked by: —
  - Accept: a `ReportContract` `clean_cli` case exercises `work_queue.main` and asserts its `wq: N problem(s)` line on both the config-failure leg (work_queue.py:209–213) and the tail (work_queue.py:226–229); the suite is green against unmodified `work_queue.py`. Today `tests/` calls `work_queue.main` zero times, so this item is the whole net of the refactor.
- [x] **A2** pin `budget_guard`'s record legs — size:S, blocked by: —
  - Accept: `ReportContract` covers the `record` and `record-run` summary lines (budget_guard.py:248–251, 259–262) alongside the `check` leg already pinned at tests/test_budget_guard.py:609–610; green against unmodified `budget_guard.py`.
- [x] **A3** free the seam's name in `work_queue` — size:S, blocked by: A1
  - Accept: `work_queue.py:191`'s `def report(batch, deferred, spent, wip)` is renamed to what it is (a batch renderer); `report` joins the five cli names imported at work_queue.py:34–35; A1's contract passes unchanged.
- [x] **A4** fold `work_queue`'s two epilogues onto `cli.report` — size:S, blocked by: A3
  - Accept: both non-JSON legs return `cli.report("wq", problems)`; no count is hand-typed; A1's contract passes unchanged; `python3 factory_init.py update-manifest` leaves no diff and detector E is green in the same commit.
- [x] **A5** settle the `--json` leg — size:S, blocked by: A4
  - Accept: the JSON leg (problems ride inside the payload, so the summary must print without the problem block) either keeps its own print with a comment naming ADR-0051's carve-out, or the seam grows a parameter — and the choice is recorded, not just coded. If the answer is the parameter, that amends ADR-0051 and belongs to Architect first (see Design gaps).
- [x] **A6** fold `budget_guard`'s two epilogues onto `cli.report` — size:S, blocked by: A2
  - Accept: `main()`'s record legs return `cli.report(...)`; A2's contract passes unchanged; manifest regenerated in the same commit and detector E green.

## Milestone B: the front door routes something, or stops pretending to (factory.py has one shape, and its verb table is derived or gone)

Card 3, graded Worth exploring — zero non-test callers walked. `factory.py`
(91 lines, landed 2026-08-10 in #246) keeps a 14-row `VERBS` table by hand
that tests/test_factory_cli.py:27–36 derives mechanically from the root's
`__main__` guards, while the Makefile's 13 targets, the five workflows and
the docs all still invoke tools by filename. The review's finding is that
the middle state — a table nobody uses, maintained by hand — is the shallow
one; both exits are deepenings. `factory.py` is not a MIRRORS entry, so
neither route churns the manifest.

- [x] **B1** decide what `factory.py` is for — size:S, blocked by: —
  - Accept: an ADR records the choice and its consequences — Route A (route the real traffic through it and derive the table: 13 Makefile recipes plus `product_makefile`'s respelling transform at factory_init.py:89, and 14 module imports per invocation on a tool CI runs every push) or Route B (keep `index()`, delete the dispatcher and its 5 `TestDispatch` tests, forfeiting the one-front-door idea from issue #237). Nothing recorded covers this today, and nothing depends on either answer yet.
- [x] **B2** land the decided route — size:L, blocked by: B1
  - Accept: the module and tests/test_factory_cli.py agree with the ADR — Route A: a test asserts every Makefile recipe reaches the verb it names, the convention column is derived rather than declared, and the dead `"argv0"` branch at test_factory_cli.py:53 is either used or gone; Route B: `VERBS` and `main` are gone, `index()` remains, `TestDispatch` is deleted. Re-cut this row into sittings once B1 names the route.

## Milestone C: the two gh callers with the same hazard stop disagreeing about it

Card 2's seam is a design gap (below), but the divergence that made it worth
raising is a defect that stands on its own. `sweeps.live_issues`
(sweeps.py:328–348) refuses to report on a truncated listing because absence
reads as a finding. `work_queue.eligible` (work_queue.py:162–179, window
100) carries the identical hazard — a ready order past the window becomes
"no open issue #N carries `wo:ready-for-agent`" (work_queue.py:101–105) —
and warns instead.

- [x] **C1** resolve the truncation policy in `work_queue.eligible` — size:S, blocked by: —
  - Accept: a test drives `eligible` with a full window and asserts the chosen behavior; either it matches sweeps' refusal, or a comment at the site states why absence is safe to report here when it is not there. No seam is built to get this.

## Design gaps found

Routed back to Architect — decompose does not design around them.

1. **One reader for gh's silence (Card 2, Worth exploring — 5 call sites walked).** Five callers each reassemble three failure modes (missing/unauth/rate-limited, unreadable answer, windowed listing) to make one listing trustworthy; the copy-paste is visible verbatim at label_sync.py:92 and gate_digest.py:167. The blocker is not effort, it is a design question the review named: three window policies with one caller each is the shape that argues *against* a seam, so someone must answer whether only two policies are real (trust / refuse) before anything is built. Cost note for whoever designs it: every problem string it touches is caller-labelled and pinned by exact-string tests, so keeping the strings byte-identical is the whole difficulty. ADR-0037 (amended by ADR-0039) deliberately left these operations with each caller; the vocabulary would stay, only the repeated sequence would move.
2. **Splitting `protocol.py`'s two families (Card 4, Speculative — unpriced by design).** The payload uses 1 of 15 names (`read_frontmatter`, at tools/factory/gates.py:73 and tools/factory/assembler.py:43) and every stamped repo carries ~250 lines of pipeline taxonomy no tool there can call. ADR-0046 (accepted) deferred exactly this and asked that any split clear the shared-module bar. What would settle it is a decision, not a refactor: may a MIRRORS entry pin a root↔root pair as well as a root↔payload pair? ADR-0050 already turned hand-maintained twins into generated ones with detector E as the pin; if that machinery may pin a root pair, the duplicated frontmatter parser stops being an unpinned copy and ADR-0046's blocker dissolves. Until that is answered this is not work.
3. **A5's second answer is an ADR amendment.** If `--json` is served by growing `cli.report` a fourth parameter rather than by an honest carve-out, that changes the seam ADR-0051 fixed and is Architect's call before it is code.
4. **ADR-0046 carries a stale citation.** It names `orientation.py` as one of three pipeline importers; no such file exists — the third importer is `trigger_eval.py`. The reasoning holds and the decision stands, so this is a correction to an accepted ADR, which belongs to whoever owns ADR edits, not to an implementation item.

## Notes

### Deviations logged at implement time (2026-08-12, Milestone A)

- **A4 and A5 could not be sequenced apart, and landed together.** The row
  assumed the `--json` leg was untouched by the fold. It is not: `main`'s
  summary `print` sat *outside* the `if "--json" / else`, so both legs
  shared one statement and folding the report leg necessarily restructured
  the JSON leg's path. A5's decision therefore had to be made to land A4.
- **A1's pin covers three legs, not the two the row named** — the
  config-failure leg, the report tail, *and* `--json` — for the same
  reason. Two of the four new cases carry problems, because a pin taken
  only on a clean run cannot tell a computed count from a hand-typed one.
- **A5's answer: the honest carve-out, held by a lockstep test.** The
  `--json` leg keeps its own summary print (the seam did not grow a
  "summary only" parameter for one caller). That re-types the grammar
  ADR-0051 says must not fork per tool, so a new test asserts the leg's
  last line equals `cli.report`'s own output for the same input — the
  split-contract idiom this repo already uses for workflow outputs. A
  third option was considered and NOT taken: extracting a `summary()`
  helper out of `cli.report` so the grammar keeps one owner. It is the
  better shape, but it changes a seam mirrored into every stamped repo
  and belongs to Architect, not to an implement item.
- **A3 named the renamed function `compose_plan`**, after the sibling
  precedent `cost_report.compose_report`.
- **Adjacent, logged not fixed:** `work_queue.main`'s usage leg
  (`print(__doc__)`, return 2) is still unpinned — `CliContract` is the
  mixin for it and every other tool's `TestMain` pairs the two. Outside
  A1's acceptance criterion, so it was not added.
- **Verification at the milestone boundary:** 1103 tests OK (was 1093),
  `lint: 0 problem(s)`, `gates: 0 problem(s)`, `selftest: ok`. Both folded
  files are MIRRORS entries, so `factory_init.py update-manifest` ran and
  the regenerated payload plus manifest are part of the same change. Each
  pin was mutation-checked before its refactor: four deliberate breakages
  of `work_queue`'s epilogue and four of `budget_guard`'s each failed the
  intended test.

### Deviations logged at implement time (2026-08-12, Milestone C)

- **C1 grew from the window leg to the whole untrusted-listing contract.**
  The row scoped the fix to the full window, but `ready_issue_numbers`
  already returned an empty set on its other two untrustworthy legs (gh
  failed, gh answered unreadably), and an empty set is exactly as
  indistinguishable from "nothing is ready" as a truncated one. Refusing
  only on the window would have left one function with two sentinels for
  one condition. All three legs now return `None`, which is the shape
  `sweeps.live_issues` already has — so "matches sweeps' refusal" is
  satisfied more literally than the row asked for.
- **The refusal is in `ready_issue_numbers` and `main`, not `eligible`.**
  `eligible` is pure and never sees the listing's provenance; the row
  named it as the site of the hazard, which is where the misleading line
  is *printed*, not where the policy is decided. `main` now plans nothing
  and defers nothing when the listing is untrusted; the problems already
  say why.
- **This changes Design gap 1's arithmetic.** The review counted three
  window policies with one caller each — the shape that argues against a
  seam. After C1 the refusal policy has two callers (sweeps.live_issues,
  work_queue.ready_issue_numbers) against three continue-and-warn sites
  (label_sync, gate_digest, sweeps' second listing). Whoever designs that
  seam should re-read the gap with those numbers, not the review's.
- **Verification:** the three C1 tests failed first for the right reason —
  the end-to-end case printed a deferral reading `no open issue #999
  carries wo:ready-for-agent` for a fixture row *and* the full-window
  problem in the same output, which is the invented drift itself. (The
  fixture row's own work-order id is deliberately not quoted here:
  detector A holds every `WO-` token in a breakdown file to a PRD
  citation, prose included.) After the fix: 1104 tests
  OK, `lint: 0`, `gates: 0`, `selftest: ok`, payload and manifest
  regenerated.

### Deviations logged at implement time (2026-08-13, Milestone B)

- **B2's acceptance criterion named Routes A and B; the architecture chose
  a third.** ADR-0054 (provisional) decides that the front door's callers
  are humans — zero file callers is the decided state, not pending
  adoption — because routing the Makefile through `factory.py` would
  either force it into the template payload as a fifteenth mirrored tool
  or make `product_form` translate verbs into payload paths, growing the
  adapter ADR-0046 exists to delete. B2 was therefore re-derived from the
  ADR: derive the convention column in the test, delete the dead branch.
- **The review's "hand-kept table" was two-thirds wrong.** The verb set
  and the verb spelling were already derived and pinned; only the
  calling-convention column was hand-declared. That column is now derived
  from each `main`'s signature — in the test, not in the router, so
  dispatch still imports one module per invocation rather than fourteen.
- **The ADR is `provisional`, not `accepted`.** It was decided inside an
  autonomous loop without the user weighing in on the recommendation,
  which is exactly what that status is for — pivot freely.
- **A trap worth recording:** the mutation check for this item briefly
  reported two false failures. Swapping `"bare"` for `"argv"` is a
  same-length edit, and restoring the file within the same second left
  `factory.py`'s mtime and size unchanged from the mutated compile — so
  Python served stale bytecode from `__pycache__`. The code was correct
  the whole time. Clearing `__pycache__` resolved it.
- **Verification:** 1105 tests OK, `lint: 0`, `gates: 0`, `selftest: ok`.
  Mislabelling `lint` as an `argv` verb fails the new pin at that row.
  `factory.py` is not a MIRRORS entry, so no manifest churn.

### Run notes

- **Provenance.** The deepening review that produced these cards was run
  read-only against commit 57635f6 on 2026-08-11 and wrote its report to the
  OS temp directory, not into the repo. Its own coverage note lists what it
  did not examine (gates.py's ten detectors internally, `selftest()`'s
  275-line body, the test suite as code, the 24 SKILL.md bodies as prose,
  the workflows, and the charter tree) and what it considered and dropped
  against a recorded decision (the harness registry's home per ADR-0053,
  the three design-system.md copies per ADR-0008 — measured, only 9–28
  identical lines — the four diagram skills' descriptions, cli.py's five
  vocabularies, the `--selftest`/unittest duplication, and the
  assembler/cost_report/gate_digest main() triple, which does not clear this
  repo's shared-module bar).
- **Ordering.** The review's own recommendation is Milestone A first — it is
  the only fully confirmed candidate, it is cheap, and the gap it closes
  lives in tools that ship into every stamped repo with zero tests over
  their CLI. Then Milestone B, because it is a decision rather than a
  refactor and it is cheapest to make while `factory.py` is days old and
  nothing depends on either answer.
- **Soft gates.** Two predecessors are missing and both are recorded in the
  frontmatter. To close them: run capture to seed `defect.md` with
  `re-entry: architect` (which also makes the router orient this run to
  implement instead of capture), and run architect for the two design gaps
  above before their work is decomposed.
- **Tracker.** No mirror has been created. Export is opt-in; the prior two
  deepening rounds in this repo were mirrored to beads as an epic with one
  child per item (`wo-cxu`). If these are mirrored, the mapping is recorded
  on each row in the `(tracker: ...)` form and these checkboxes remain the
  state (ADR-0026).
