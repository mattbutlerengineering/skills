---
stage: decompose
run: feature:fail-closed-roll-up
date: 2026-10-17
assumptions:
  - "No live review of the cut: milestone boundaries and sizing are the skill's own defaults (each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows). Milestone 1 is the gate half, because detector H refusing a full-pass Summary over a disclosed NOT RUN can be shown on its own. Milestone 2 is the docs half, which changes no behaviour and can be shown by reading the files. Milestone 3 is the whole-repo check over both."
  - "Test-first ordering follows the repo's TDD rule: the gate implementation item is blocked by a tests item whose Accept is that its new cases run and fail against the tree before the rule lands. The selftest defect fixture is test code, so it sits in that tests item: its new H expect substring makes `python3 gates.py --selftest` fail until the rule exists."
  - "The docs items (CONTEXT.md, the protocol section, the two templates and verify's SKILL.md) have no tests item ahead of them: the architecture names no test for them and the PRD's criteria for them are textual. Each Accept is a grep-checkable outcome instead, and the whole-repo verify item runs lint.py, kb.py drift and gates.py over them."
  - "No ADR item: ADR-0107 was written and committed by Architect with Status provisional, which already meets the PRD's ADR criterion. Implement edits it only if a Notes entry records a deviation that changes what it says."
  - "No work-order ids and no (tracker: #N) markers: the brief seeds no issues and allows no tracker interaction before Ship, and dispatch mirrors one way (ADR-0032). Rows are plain items."
  - "Existing H fixtures carry no date, so the new rule judges them (architecture). An existing test or selftest fixture whose outcome changes under the rule is not fixed by adding a date or editing its assertion; it is logged in Notes and routed back to Architect as a design gap."
---

# Breakdown: Fail-closed roll-up for verification Summaries

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. The gate implementation is blocked by the
tests item that pins it.

## Milestone 1: detector H refuses a Summary that rolls a disclosed NOT RUN up into a pass

When this milestone is done, `python3 gates.py` reports one `H:` problem
for a `verification.md` dated on or after `ROLLUP_ADOPTED` (or undated)
whose `## Summary` names no unknown-kind word while another section holds a
labelled disclosure, and main's real tree still reports 0 problems.

- [x] **Roll-up rule tests** — new cases in `tests/test_gates.py` beside `TestEvidenceHonesty`, plus one defect artifact in `gates_selftest.evidence_honesty_defect_fixture` — size:M
  - Accept: the cases assert exact output through `gates.evidence_problems(text)` and `gates.check_evidence_honesty(root)`: a fixture dated `2026-10-17` with one criterion verdict `NOT RUN` and a Summary reading as a full pass gives exactly one problem at the first Summary heading's line whose text is `summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "<criterion title>", line <verdict line>); unknown never rolls up to pass`, and through `check_evidence_honesty` that string carries the `H: {rel}:{lineno} ` prefix; the same shape with no `date:` fails identically (fail closed); the same shape dated `2026-10-16` gives `[]`; a Summary counting it (`1 PASS, 1 NOT RUN`) gives `[]`; a Summary naming a different kind (`1 deferred`) gives `[]`; a fixture with no disclosed criterion gives `[]`; a criterion that only mentions "not run" in prose with no labelled disclosure verdict gives `[]`; a fixture with no section titled `Summary` gives `[]`; a Summary that says `not run` only inside a fenced block fails with the problem above; two disclosed criteria give one problem carrying `the 2 criterion section(s)` and the first one's title and line; the three honest Summary shapes from main (`0 of 7 met, 0 failed, 7 unmet`, `7 PASS, 0 FAIL, 2 NOT YET VERIFIABLE`, `16 PASS, 3 FAIL, 1 DEFERRED`), each over a labelled disclosure and dated past the cutoff, give `[]`; `gates.ROLLUP_ADOPTED == "2026-10-17"`; each section dict from `gates.verification_sections` carries `names_unknown`, true for a section with an unfenced `unknown` and false for one whose only such word is fenced. The selftest defect fixture gains one artifact dated `2026-10-17` with a full-pass Summary over one `NOT RUN` criterion, and the H `expect` gains the substring `neither counts nor names`. Run before the next item, the new `tests/test_gates.py` cases fail (no `ROLLUP_ADOPTED`, no `names_unknown`, no roll-up problem) and `python3 gates.py --selftest` fails on the missing H substring.
  - Blocked by: —
- [x] **Roll-up rule in detector H** — in `gates.py`: `ROLLUP_ADOPTED`, `SUMMARY_TITLE` and `SUMMARY_UNKNOWN_TERM` as the architecture's data model gives them; the `names_unknown` flag in `verification_sections`; new private `_rollup_problems(sections)` and `_rollup_applies(text)`; one step in `evidence_problems` after the per-section loop and before the artifact-wide backstop; the import widened to `from protocol import read_frontmatter, parse_frontmatter`; the module docstring's H roster entry gains the Summary half — size:M
  - Accept: the roll-up rule tests pass, and `python3 gates.py --selftest` prints `gates: 0 problem(s)`. Every pre-existing `tests/test_gates.py` case and the selftest clean fixture pass with no assertion or fixture edited (any outcome change is logged in Notes and routed back as a design gap). `check_evidence_honesty` is unchanged in code. `verification_sections` stays the only section parse of the artifact: `_rollup_problems` reads its dicts and calls `_is_disclosure`, and no new regex walks headings. No module import edge is added beyond the widened `protocol` import, so `tests/test_dual_membership.py` passes with its pin unchanged. `python3 gates.py` on the real tree prints `gates: 0 problem(s)`, and `git diff --stat main -- 'docs/**/verification.md' 'docs/**/review.md'` prints nothing.
  - Blocked by: Roll-up rule tests
- [x] **Payload mirror and manifest regen** — refresh the payload copies of `gates.py` and `gates_selftest.py` and the checksum manifest — size:S
  - Accept: stray `.orig`/`.rej` files are deleted first (`docs/kb/manifest-regen.md`), then `python3 factory_init.py update-manifest` runs, and the manifest and payload copies are part of the change. `tools/factory/gates.py` and `tools/factory/gates_selftest.py` under `factory/templates/` are byte-identical to the root files (identity transform). Detector E reports nothing, and `python3 -m unittest tests.test_factory_init` passes. `.claude-plugin/plugin.json` is unchanged (ADR-0095).
  - Blocked by: Roll-up rule in detector H

## Milestone 2: the claim kinds and the roll-up rule are written once and carried by the templates

When this milestone is done, `CONTEXT.md` owns the four claim kinds and the
rule, the protocol states the rule once and points there, and the verify
Summary and review Verdict guidance tell an author to count or name every
NOT RUN / unknown item.

- [ ] **CONTEXT.md: claim kinds and fail-closed roll-up** — two vocabulary entries, the only owner of the words — size:S
  - Accept: `CONTEXT.md` has a **Claim kind** entry defining observed (quoted output), derived (computed from observed), inferred (judgement) and unknown (not examined; what NOT RUN, skipped, deferred and n/a disclose), and a **Fail-closed roll-up** entry stating that unknown, unsupported, truncated and skipped never aggregate to pass, so a Summary or Verdict counts or names them. `grep -c "never aggregate to pass" CONTEXT.md` prints 1. No literal four-digit work-order or PRD id appears in the added text (`docs/kb/gates-scan-every-doc.md`).
  - Blocked by: —
- [ ] **Protocol: state the roll-up rule once** — one short section in `docs/pipeline-protocol.md` — size:S
  - Accept: the new section states the rule once, links `CONTEXT.md` for the claim kinds without redefining observed, derived, inferred or unknown, and cites ADR-0107 for the gate half (detector H on `verification.md`, grandfathered by `date:` before `ROLLUP_ADOPTED`). `grep -n "derived (computed" docs/pipeline-protocol.md` prints nothing.
  - Blocked by: CONTEXT.md: claim kinds and fail-closed roll-up
- [ ] **Templates and verify SKILL.md carry the rule** — `skills/verify/TEMPLATE.md`'s `## Summary` placeholder, `skills/review/TEMPLATE.md`'s `## Verdict` placeholder and `skills/verify/SKILL.md`'s "summary of it" line — size:S
  - Accept: each of the three places says the line counts or names every NOT RUN / unknown item and never reads as an unqualified pass over them, pointing to `CONTEXT.md` rather than redefining the claim kinds. `skills/review/SKILL.md` is unchanged (it never describes the Verdict line). The verify template's Summary heading is still spelled exactly `## Summary`. `.claude-plugin/plugin.json` is unchanged (ADR-0095).
  - Blocked by: CONTEXT.md: claim kinds and fail-closed roll-up

## Milestone 3: the finished change passes every check

- [ ] **Whole-repo verify** — the four CI checks and the one-owner pre-pass over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` each print `gates: 0 problem(s)`. `git diff --stat main -- 'docs/**/verification.md' 'docs/**/review.md'` prints nothing, and `git diff --name-only main -- .claude-plugin/plugin.json` prints nothing. `python3 one_owner.py` reports no `one-owner:` problem naming `ROLLUP_ADOPTED` or `SUMMARY_UNKNOWN_TERM`.
  - Blocked by: Payload mirror and manifest regen; Protocol: state the roll-up rule once; Templates and verify SKILL.md carry the rule

## Design gaps found

None. Every component in architecture.md (the `verification_sections`
flag, `_rollup_problems`, `_rollup_applies` and the `evidence_problems`
step, the selftest fixture, the docs and templates, the payload) has an
item, and every PRD success criterion maps to an Accept line: the
failing, passing, honest-shape, prose-only, pre-cutoff and pinned-constant
criteria to the roll-up rule tests; 0 problems on main with no shipped
artifact edited to the detector H item and Whole-repo verify; the
`CONTEXT.md`, protocol and template criteria to Milestone 2; the ADR
criterion to ADR-0107, already committed; the battery and detector E to
the payload item and Whole-repo verify.

## Notes

Deviations discovered during Implement get logged here, dated.

- 2026-10-17 (Roll-up rule tests, RED): `TestEvidenceRollUp` in
  `tests/test_gates.py` (14 cases) and the selftest `rolledup` defect
  artifact, run against the tree before the rule landed.
  `python3 -m unittest tests.test_gates.TestEvidenceRollUp` printed
  `FAILED (failures=5, errors=2)`, with
  `AttributeError: module 'gates' has no attribute 'ROLLUP_ADOPTED'`,
  `KeyError: 'names_unknown'` and
  `AssertionError: Lists differ: [] != [(8, 'summary "Summary" neither counts nor[118 chars]ss')]`.
  `python3 gates.py --selftest` printed `H: expected a problem containing
  'neither counts nor names', got [...]` and `selftest: FAIL`. The seven
  cases that expect `[]` pass vacuously before the rule; they pin the
  rule's silence once it lands. Until the payload item, the mirrored
  `gates_selftest.py` differs from its payload copy, so
  `tests.test_factory_init` is red between these commits by design.

- 2026-10-17 (Roll-up rule in detector H, GREEN): `python3 -m unittest
  tests.test_gates` printed `OK`; `python3 gates.py --selftest` printed
  `selftest: ok` and `gates: 0 problem(s)`; `python3 gates.py` printed
  `gates: 0 problem(s)`. No pre-existing H test or selftest fixture
  changed outcome, so there is no design gap. `python3 run_tests.py`'s
  only failing module was `tests.test_factory_init` (the two mirror
  copies, fixed by the next item).
- 2026-10-17 (deviation, environment): the local `main` ref is stale at
  `7376d94`; the branch's base is `origin/main` at `1290a4e` (#991),
  which added `docs/features/pr-body-preflight/verification.md` and
  `review.md`. So `git diff --stat main -- 'docs/**/verification.md'
  'docs/**/review.md'` lists those two files although this run edits
  neither. The same command against `origin/main` prints nothing, and
  that is the check this run reports.
