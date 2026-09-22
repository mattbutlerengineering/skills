---
stage: decompose
run: feature:codex-style-standards-enforcement
date: 2026-09-20
assumptions:
  - "No tracker mirror issues created for any row below (ADR-0032's one-way rule and the planner charter both presume the blueprint already passed the human blueprint gate; this design hasn't). See Notes."
  - "WO ids continue the repo-global sequence. Originally numbered starting at order 45 on the assumption that feat/first-live-dispatch's breakdown (last recorded order 44) was the highest claim in flight; that assumption was stale — docs/features/pipeline-board/breakdown.md had already claimed (and completed, 2026-08-25) orders 45 through 50 in an unmerged PR this run couldn't see. Renumbered to start at order 51 once the collision surfaced during that PR's merge. See Notes."
---

# Breakdown: Codex-style standards enforcement

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Row grammar per this repo's existing
convention: one line per work order carrying id, size class, blocking
edges, and the PRD citation detector A checks.

## Milestone A: Blueprint formalized (the design decisions this run recorded inline in architecture.md become real, human-approved ADR(s))

- [x] **WO-0051** author the real `docs/adr/**` file(s) for this run's hard-to-reverse decisions — size:M, blocked by: — (PRD-0004 §Out of scope)
  - Accept: at least one new `docs/adr/NNNN-*.md` exists, recording (a) `standards_index.py` as a new seam module (the cost_ledger.py-shaped "two real callers" justification), (b) the `K`/`M` detector-letter assignment and why `J` was skipped, (c) enforcement status living in the index field rather than in ADR prose. `docs/adr/README.md`'s index gains the matching row(s) with status `accepted`. This is a standard `docs/adr/**` PR — human code-owner merge per the existing ADR-0033/ADR-0036 gate, not a new gate. The battery stays green.

## Milestone B: Index mechanism (no statement content yet — the machinery only)

- [x] **WO-0052** `standards_index.py` — statement shape, `## Normative statements` bullet parser, regen algorithm, `update` CLI verb — size:M, blocked by: WO-0051 (PRD-0004 §Success criteria)
  - Accept: the module owns the `{slug, statement, level, source, status, domain}` shape and the `MUST/SHOULD` + `advisory/enforced` + `factory/pipeline/eval/docs` enums; `python3 standards_index.py update` regenerates the ADR-derived subset of `docs/standards.json` deterministically and leaves any `CLAUDE.md#`-sourced entry untouched; a malformed `## Normative statements` bullet (missing slug, missing or doubled RFC-2119 keyword) is a returned problem string, never a silent skip; unit tests cover the parser and the regen/preserve behavior.
- [x] **WO-0053** wire `standards_index.py` into `factory.py`'s `VERBS` and `factory_init.MIRRORS` — size:S, blocked by: WO-0052 (PRD-0004 §Success criteria)
  - Accept: `python3 factory.py standards-index update` works (verb name mechanically derived, pinned by `tests/test_factory_cli.py`'s scan); `factory_init.MIRRORS` gains `("standards_index.py", "tools/factory/standards_index.py", identity)`; `python3 factory_init.py update-manifest` has been re-run and `factory/manifest.json` committed in the same change (detector E stays green).
- [x] **WO-0054** `gates.py` detector `K` (`STANDARDS-DRIFT`) + selftest fixtures — size:M, blocked by: WO-0052 (PRD-0004 §Success criteria)
  - Accept: `K` fails when committed `docs/standards.json`'s ADR-derived entries disagree with a fresh `standards_index.build_index(root)` regen; `K` separately fails when an `enforced` statement's source ADR's `_adr_status` is not `accepted` (reusing the existing helper, not a second status parser); an absent `docs/standards.json` is not a `K` problem (mirrors detector G's "no runs recorded yet" precedent); `python3 gates.py --selftest` exercises both failure shapes with planted fixtures; the `DETECTORS` table and roster docstring agree `K` is claimed (a docstring/table disagreement of the same shape is separately being fixed for letter `J` by unrelated in-flight work on another branch — not this row's concern).
- [x] **WO-0055** `gates.py` detector `M` (`CAPTURE-COMPLETENESS`) + selftest fixtures — size:M, blocked by: — (PRD-0004 §Success criteria)
  - Accept: `M` returns one problem string per `docs/fixes/<slug>/defect.md` missing (or placeholder-only) required section — `Defect`/`Condition`, `Reproduction / Evidence`, `Root-cause hypothesis`, `Blast radius`, `Ruled out`, per `skills/capture/TEMPLATE.md`'s own headings — generalizing detector H's existing `HEADING_LINE`/setext-title section-splitting rather than duplicating it; a run with no `defect.md` yet is out of `M`'s scope entirely; `python3 gates.py --selftest` covers a fixture missing each section; `DETECTORS["M"]` and the roster docstring agree. Independent of the index-mechanism rows above — implementable in parallel.

## Milestone C: Index bootstrapped with real content (still all `status: advisory` — nothing enforced yet)

- [x] **WO-0056** back-fill `## Normative statements` sections into a first small set of existing ADRs — size:M, blocked by: WO-0052 (PRD-0004 §Solution)
  - Accept: a human-reviewed, non-exhaustive first set of statements worth enforcing (candidates: the one-way dispatch-mirror rule, ADR-0004's "typed IDs live only in run-artifact frontmatter," the stdlib-only rule) is added under a `## Normative statements` heading in their source ADRs, each with a stable slug and exactly one RFC-2119 keyword, every one at `status: advisory` (nothing is created pre-enforced — mirrors this repo's own LEDGER discipline of graduating only on evidence). Standard `docs/adr/**` human-merge gate applies; no special flag needed beyond that existing policy.
- [x] **WO-0057** hand-curate a first small set of `CLAUDE.md`-sourced entries directly in `docs/standards.json` — size:S, blocked by: WO-0052 (PRD-0004 §Solution)
  - Accept: a small number of CLAUDE.md "Hard conventions" bullets judged worth enforcing (candidates: "Stdlib only," "Never fabricate... eval honesty") get hand-authored entries with `source: CLAUDE.md#<anchor>`, `status: advisory`; the anchor form is resolvable by a human/reviewer reading CLAUDE.md even though CLAUDE.md has no heading-anchor convention of its own (Implement's call on the exact `source` string shape, per architecture.md's Open-question resolution — not hard-to-reverse, no ADR needed for this row itself).
- [x] **WO-0058** regenerate and commit the bootstrapped `docs/standards.json`; confirm detector `K` green — size:S, blocked by: WO-0053, WO-0054, WO-0056, WO-0057 (PRD-0004 §Success criteria)
  - Accept: `python3 factory.py standards-index update` produces a `docs/standards.json` that includes both the ADR back-fill and the CLAUDE.md back-fill entries from the two rows above; `python3 gates.py` (including `K`) is green; `python3 gates.py --selftest` stays green.

## Milestone D: Standards-aware review and blueprint gate

- [x] **WO-0059** `skills/review/SKILL.md` + `skills/review/TEMPLATE.md` — load, filter, cite, block — size:M, blocked by: WO-0058 (PRD-0004 §Success criteria)
  - Accept: a new process step loads `docs/standards.json`, filters to statements whose `domain` matches the diff's touched paths, and requires findings to cite a matching slug where one applies; `TEMPLATE.md` gains a slug-citation line per finding; an unresolved `enforced`-statement finding is treated by the existing fix-loop rule the same way a critical finding already is (fixed before Ship), without redefining "critical" for anything else; advisory findings stay non-blocking, recorded like any other minor.
- [x] **WO-0060** `factory/charters/reviewer/CHARTER.md` — same load/cite step + `Must never` clause — size:S, blocked by: WO-0058 (PRD-0004 §Success criteria)
  - Accept: "Actions per cycle" gains the load/filter/cite step; "Must never" gains a sibling clause to the existing open-security-finding rule: an unresolved `enforced`-statement finding blocks the pass verdict; ADR-0036's merge-decision conditions are otherwise unchanged.
- [x] **WO-0061** `skills/architect/SKILL.md` + `skills/architect/TEMPLATE.md` — design-relevant load/cite step — size:S, blocked by: WO-0058 (PRD-0004 §Success criteria)
  - Accept: a step before drafting loads statements filtered to `domain ∈ {factory, pipeline}`; `TEMPLATE.md`'s "Decisions & alternatives" guidance notes citing a matching slug where a design decision bears on one, alongside the existing ADR-citation convention.
- [x] **WO-0062** `factory/charters/architect/CHARTER.md` — same design-relevant load/cite step — size:S, blocked by: WO-0058 (PRD-0004 §Success criteria)
  - Accept: "Actions per cycle" gains the same filtered-load-and-cite step as the architect skill's own item above, for the chartered-agent path.

## Milestone E: Close-out

- [x] **WO-0063** full battery green across every item above, traceability re-check — size:S, blocked by: WO-0059, WO-0060, WO-0061, WO-0062 (PRD-0004 §Success criteria)
  - Accept: `python3 -m unittest discover tests`, `python3 lint.py`, and `python3 gates.py && python3 gates.py --selftest` are all green with every prior row's changes present; PRD-0004's success criteria are re-walked one by one against what actually landed (Verify's job, scaled to this feature — the run's own `verification.md`, when this feature run continues past this breakdown).
- [ ] **WO-0064** ⚠️ **NEEDS HUMAN JUDGMENT — not implementable unilaterally.** Resolve PRD-0004's deferred "3 real advisory→enforced promotions with prior evidence" acceptance bar — size:S, blocked by: WO-0058 (PRD-0004 §Out of scope, §Open questions)
  - Accept: a human names either (a) three specific statements from the back-fill milestone above that already have real, pre-existing advisory-flagged evidence to point to honestly (a past PR review comment, an audit finding, a `one_owner.py` finding) — no evidence is fabricated to hit the count — or (b) an explicit decision to defer this criterion to a later run, once a real observation period under `status: advisory` has produced real findings to promote from. Either resolution gets recorded here and, if (a), the promoted entries' `status` flips to `enforced` with the cited evidence named inline in `docs/standards.json` or a linked note.
  - **Why this can't be picked unilaterally:** the acceptance bar as issue #448 literally states it requires evidence that cannot exist before the index does — satisfying it without a human either supplying real prior evidence or explicitly accepting deferral would mean fabricating "previously flagged" history, which `CLAUDE.md`'s eval-honesty rule forbids outright. This is the one row in this breakdown that mirrors this repo's own `wo-cxu.1`-style "needs /grilling"/`ready-for-human` convention (issues #440/#444/#434/#435): a genuine design-policy fork, not a missing detail Implement can default its way through.

## Design gaps found

None — every one of architecture.md's four numbered components maps to
at least one milestone above (Component 1+2 → Milestones B/C;
Component 3 → Milestone B's `K`/`M` rows; Component 4 → Milestone D).
The one remaining open implementation detail — the exact `CLAUDE.md#`
anchor-resolution string for hand-curated entries — was left to
Implement with a working default (the CLAUDE.md back-fill item's own
Accept line above) rather than routed back here, because architecture.md's own bar for what routes
back is "hard-to-reverse," and an anchor-string convention is neither:
it costs one `standards_index.py update` re-run to change.

## Notes

- 2026-09-21: **Milestone D is implemented, verified, and checked off**
  (orders 59 through 62) — all prose, no new Python. `skills/review/
  SKILL.md` gained a "Load applicable standards" step between the
  three-pass review and ranking (before findings are ranked, per this
  row's own Accept line), filtering `docs/standards.json` by domain
  against the diff's touched paths; its fix-loop step now treats an
  unresolved finding against an `enforced` statement as a second,
  independent trigger of the existing before-Ship rule, explicitly
  without redefining "critical" for anything else. `skills/review/
  TEMPLATE.md` gained a `- Standard: <slug or "none">` line per
  finding. `factory/charters/reviewer/CHARTER.md`'s "Actions per
  cycle" gained the mirrored load/filter/cite step (placed right
  before "filter findings by confidence," the charter's analogue of
  ranking), and "Must never" gained a sibling bullet to the existing
  open-security-finding rule, same shape, same consequence, for an
  open `enforced`-statement finding — ADR-0036's merge-decision
  conditions were not touched. `skills/architect/SKILL.md` gained the
  same shape of step before "Draft," filtered to `factory`/`pipeline`
  domains (no diff exists yet at design time, so there is no path-based
  filter to state, unlike review's). `skills/architect/TEMPLATE.md`'s
  "Decisions & alternatives" placeholder bullet gained a citation
  clause. `factory/charters/architect/CHARTER.md`'s "Actions per
  cycle" gained the mirrored step right after the initial
  read-the-codebase step and before designing starts — no `Must never`
  change, since the architect skill's own row (which this row mirrors)
  didn't add a blocking rule either. Full verification battery
  (`python3 -m unittest discover tests`, `python3 lint.py`,
  `python3 gates.py && python3 gates.py --selftest`) is green, on the
  first run after all six file edits landed — none of the new numbered
  steps disturbed `lint.py`'s soft-gate or hand-off recital checks,
  which key off phrase content, not step numbers. Four more lines were
  appended to
  `docs/factory/costs.jsonl` under the same owner-session ledger
  policy, one each for orders 59 through 62.
  - Judgment call: no real run in this repo's history has ever cited an
    ADR number inline inside an architecture.md's own "Decisions &
    alternatives" bullets (checked mechanically — grepped every
    `architecture.md` under `docs/features/**` and `docs/**` for
    `ADR-\d{4}` inside that section; zero hits, including this run's
    own). So there is no literal existing "cite `(ADR-####)` in a
    Decisions bullet" convention to extend. What this run's own
    `architecture.md` does use, elsewhere in its prose (e.g. its Data
    model section), is a general pattern — state the clause, cite the
    ADR number in parens right after it. `skills/architect/TEMPLATE.md`'s
    new clause follows that same shape (cite the standards `slug`
    alongside any ADR number, in the same spot a decision already names
    one), rather than inventing a different citation syntax.
- 2026-09-21: **Milestone C is implemented, verified, and checked off**
  (orders 56 through 58). `docs/adr/0032-factory-dispatch-plane.md` and
  `docs/adr/0004-artifacts-are-the-state.md` each gained one
  `## Normative statements` bullet — `adr0032-one-way-mirror` (factory,
  the module docstring's own worked example verbatim) and
  `adr0004-typed-ids-in-frontmatter` (pipeline) — both `status:
  advisory`. `docs/standards.json` was hand-authored with two
  `CLAUDE.md#`-sourced entries (`eval-honesty`, domain eval; and
  `stdlib-only`, domain factory — see judgment call below), then
  regenerated via `python3 factory.py standards-index update`, which
  combined both back-fills: the file now carries all four entries,
  sorted by slug, and detector `K` is green. Full verification battery
  (`python3 -m unittest discover tests`, `python3 lint.py`,
  `python3 gates.py && python3 gates.py --selftest`) is green. Three
  more lines were appended to `docs/factory/costs.jsonl` under the same
  owner-session ledger policy the prior note below already establishes
  (`run_id: session-2026-09-21-wo-00NN`, `model: claude-sonnet-5`,
  `tokens: 0`, `cost: 0.0`, `outcome: owner-session:unmetered`), one
  each for orders 56 through 58 — detector G would otherwise have
  flagged all three as checked off with no ledger line.
  - Judgment call: the breakdown's third ADR candidate — "the
    stdlib-only rule" — was left out of the ADR back-fill. No
    `docs/adr/*.md` file's own `## Decision` section actually ratifies
    "stdlib only" as a decision; every ADR mentioning "stdlib" (0021,
    0027, 0046, 0062, 0065) treats it as a pre-existing convention it
    relies on or is blocked by, never as something it decides. Its real
    ratified home is `CLAUDE.md`'s own "Hard conventions" bullet
    ("Stdlib only. Every script is standalone Python 3 standard
    library."), so it was hand-curated into the CLAUDE.md-sourced row
    instead (slug `stdlib-only`), per the breakdown's own contingency
    for exactly this case.
  - Judgment call: the breakdown attributes "typed IDs live only in
    run-artifact frontmatter" to ADR-0004, matching `CLAUDE.md`'s own
    citation for that rule. Read literally, ADR-0004's text ("No
    manifest or state file...") never says "typed ID" or "frontmatter"
    for an identifier specifically — the concrete `id: PRD-####`
    frontmatter grammar is actually spelled out in ADR-0032's Decision,
    not ADR-0004's. Followed the breakdown's (and `CLAUDE.md`'s)
    citation rather than override it, but worded the back-filled
    statement to match what ADR-0004 itself actually decided — an
    artifact's identity lives in the artifact, never a parallel
    manifest or tracking tree — instead of restating ADR-0032's
    PRD-#### grammar detail under the wrong ADR's heading.
  - Judgment call: `standards_index.update`'s preserve-hand-curated-
    entries path (`foreign_entries`) was already covered by real unit
    tests before this row — `tests/test_standards_index.py`'s
    `test_preserves_hand_curated_entries_untouched` and
    `test_only_claude_md_sourced_entries_are_returned`, plus
    `gates.py`'s `test_a_hand_curated_entry_never_drifts` — all
    exercised against synthetic tempdir fixtures and genuinely passing,
    not aspirational. What had never happened before this row was
    running `update` against this repo's own real `docs/standards.json`
    for the first time; that has now happened and was confirmed correct
    by inspection (both hand-curated entries survived verbatim, both
    ADR-derived entries appeared, the whole file sorted by slug). No new
    unit test was added — the logic path was already real-tested, not
    merely promised, so a duplicate fixture test would not have closed
    an actual gap.
- 2026-09-21: **Milestones A and B are implemented, verified, and
  checked off** — the code, tests, and the real ADR (ADR-0073) all
  exist and the battery is green. ADR-0073 records the real
  ADR the first row above calls for; the letter-assignment reasoning
  was verified against current `gates.py` (`LABEL-WIRING` merged via PR
  #516 since this breakdown's authoring) rather than trusted from
  `architecture.md`'s day-old snapshot — the conclusion (`K`/`M` are the
  free letters) held, only the "why `J` is skipped" reasoning needed
  updating to match reality. Implementing the `CAPTURE-COMPLETENESS`
  detector surfaced a real conflict `architecture.md` did not
  anticipate: this repo's own `docs/fixes/*/defect.md` corpus (57
  files) almost entirely predates `skills/capture/TEMPLATE.md`'s
  current heading set, so wiring it unconditionally would have turned
  `gates.py` permanently red against this repo's own history. Resolved
  with a `CAPTURE_ADOPTED` cutoff (`gates.py`) grandfathering any
  `defect.md` whose own frontmatter `date:` predates it — deterministic
  and hermetic (a file's own static field, never wall-clock "now"), the
  same "a new rule does not retroactively apply to what predates it"
  principle ADR-0043 already established for the cost-ledger
  detector's `(pre-ledger)` annotation, generalized to every repo this
  detector ships to rather than a 57-file hand-annotation pass scoped
  to this one. Recorded in ADR-0073's own Consequences, not just here.
- 2026-09-21: **the five rows above are checked using this repo's
  existing owner-session ledger policy**, not a new decision — the
  implementing agent that finished the code flagged detector G's
  "merged work order has no line in costs.jsonl" as an open gap and
  reasoned from first principles that any ledger line here would be
  fabrication, without having found the precedent already set for
  exactly this situation: `docs/features/process-dashboard/
  breakdown.md`'s 2026-08-13 note ("owner-session ledger policy"),
  independently reaffirmed by ADR-0069's Context ("every non-gate row
  so far carries outcome `owner-session:unmetered`"). That policy is
  specifically for work implemented interactively (no dispatched
  agent, no assembler/budget_guard run) rather than through the paid
  dispatch pipeline — exactly this session's shape. Five lines were
  appended to `docs/factory/costs.jsonl`, one per each of orders 51
  through 55 above: `run_id: session-2026-09-21-wo-00NN`, `model: claude-sonnet-5`,
  `tokens: 0`, `cost: 0.0`, `outcome: owner-session:unmetered`,
  `at: 2026-09-21`. This is not the ADR-0043 `(pre-ledger)` annotation
  (correctly rejected by the implementing agent as inapplicable — this
  ledger predates none of this work) and it is not a guessed spend
  figure: `$0`/`tokens: 0` is the accurate figure for what this ledger
  measures (the factory's *metered* monthly dispatch budget), which an
  interactive owner/agent session run under a Claude subscription
  genuinely does not draw against — the `unmetered` outcome string is
  what discloses that tokens were real but untracked against this
  specific cap, the same honest framing `process-dashboard/retro.md`
  and `verification.md` both record for their own owner-session rows.
  Full verification battery (`python3 -m unittest discover tests`,
  `python3 lint.py`, `python3 gates.py && python3 gates.py --selftest`)
  is green with the rows checked and the ledger lines present.
- 2026-09-21: **renumbered every row's id, shifting orders 45 through 58 up
  by six to 51 through 64.** Surfaced while resolving PR #484's
  (pipeline-board) merge conflict: that run's own breakdown had already
  claimed and completed orders 45 through 50 on 2026-08-25, invisible to
  this run at authoring time since PR #484 was still open and unmerged.
  No dispatch-plane impact — none of this breakdown's rows have been
  mirrored to tracker issues yet (see the note below), so the renumber
  only touched this file's own text.
- 2026-09-20: **no tracker mirror issues were created for any row
  above.** ADR-0032's one-way rule and the planner charter both
  presume a blueprint has already cleared the human blueprint gate
  (ADR-0033) before its rows become dispatch-ready; `architecture.md`
  has not been through that gate in this run. Mirroring now would let
  the dispatch plane run ahead of an unapproved blueprint — exactly
  the ordering ADR-0032 exists to prevent. Export happens at a real
  Decompose pass, after a human has approved PRD-0004 and
  architecture.md, not as part of this unattended planning pass.
- 2026-09-20: **the ADR-authoring row above is sequenced first**,
  ahead of the code it justifies, so later rows' module docstrings can
  cite a real ADR number the way `cost_ledger.py` cites ADR-0037 today,
  instead of citing architecture.md informally or citing nothing.
- 2026-09-20: **every back-filled statement in Milestone C starts
  `status: advisory`, none `enforced`.** This is deliberate, not an
  oversight: this repo's own LEDGER.md maturity discipline (draft →
  used-once → battle-tested, graduated only on real-run evidence) is
  the direct model PRD-0004 cites for why promotion must be
  evidence-backed and human-decided, never a batch default at
  authoring time.
- 2026-09-20: **the human-judgment row above (the acceptance-criterion-4
  promotion decision) is the one row flagged as needing a human
  design call before it's implementable**, in the same spirit as this
  repo's existing `ready-for-human`-labeled issues (#440/#444/#434/#435)
  and `bd`'s `wo-cxu.1` ("Needs /grilling before implementation...
  not safe to pick unilaterally in the autonomous loop"). No `wo:*`
  label and no `ready-for-human` label were applied by this run — this
  run applies no labels at all — but the row is written so a human
  reading it, or a planner charter re-slicing this breakdown later,
  can apply the real label without having to first rediscover why.
- 2026-09-21: **order 63's traceability re-check, PRD-0004's Success
  criteria walked one by one against what actually landed** (Milestones
  A through D, orders 51 through 62):
  - `docs/standards.json` exists, shape matches issue #448's spec
    exactly (`slug`/`statement`/`level`/`source`/`status`/`domain`,
    `level ∈ {MUST, SHOULD}`, `status ∈ {advisory, enforced}`,
    `domain ∈ {factory, pipeline, eval, docs}`) — met, order 52.
  - A stdlib-only regeneration script deterministically rebuilds the
    ADR-derived subset and leaves hand-curated `CLAUDE.md#` entries
    untouched on regeneration — met, order 52 (parser/regen), order 58
    (exercised for real against this repo's own content, both
    back-fills survived).
  - A new `gates.py` detector fails on committed-vs-regenerated drift
    and on an `enforced` statement citing a non-`accepted` ADR, reusing
    `_adr_status`/`ADR_STATUS` rather than a second status vocabulary —
    met, order 54 (`K`).
  - `gates.py --selftest` covers the new detector(s) with planted
    fixtures — met, orders 54 and 55 (`K` and `M` each carry planted
    fixtures for both their failure shapes).
  - `skills/review/SKILL.md` + `factory/charters/reviewer/CHARTER.md`
    load the index filtered by touched-path domain, cite slugs, and
    block on an unresolved `enforced` finding while keeping advisory
    findings non-blocking — met, orders 59 and 60.
  - `skills/architect/SKILL.md` + `factory/charters/architect/
    CHARTER.md` load the design-relevant slice
    (`domain ∈ {factory, pipeline}`) before drafting and cite bearing
    statements — met, orders 61 and 62.
  - A new gate detector validates `defect.md` completeness against the
    protocol's required sections, with exact problem strings and unit
    tests — met, order 55 (`M`), generalizing detector H's
    section-splitting per the PRD's own suggestion rather than a
    lint-style checker (Implement's call, made at order 55: `gates.py`
    over `lint.py` because the check is generic to any factory-stamped
    repo, matching `architecture.md`'s own Component 3 reasoning).
  - The full battery (`python3 -m unittest discover tests`,
    `python3 lint.py`, `python3 gates.py && python3 gates.py
    --selftest`) stayed green through every one of orders 51 through
    62, independently re-confirmed at order 63 with every prior row's
    changes present.
  - No parallel docs tree: `docs/standards.json`'s `source` field
    points at the ADR/CLAUDE.md passage rather than restating it, and
    `K` itself is what verifies this (a `source` pointing at a
    fictional or drifted passage is exactly what `K`'s regen-diff
    catches) — met, orders 52 through 54, and this is checked
    mechanically rather than asserted, per the PRD's own bar.
  - **Not met, by design, not by gap:** the PRD's separately-scoped
    "3 real advisory→enforced promotions with prior evidence"
    acceptance bar (PRD-0004 §Out of scope) is order 64 below, flagged
    since order 51 as needing a human decision this session cannot make
    without fabricating evidence eval honesty forbids. Every other
    Success-criteria line is met.
  - PRD-0004's own checkbox list is left unchecked: this repo's other
    completed feature PRDs (`process-dashboard`, `software-factory`)
    likewise never check their own Success-criteria boxes — that
    marking is not this repo's convention, and this walk-through is
    written here instead, in the breakdown row whose Accept line calls
    for it.
