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

- [x] **CONTEXT.md: claim kinds and fail-closed roll-up** — two vocabulary entries, the only owner of the words — size:S
  - Accept: `CONTEXT.md` has a **Claim kind** entry defining observed (quoted output), derived (computed from observed), inferred (judgement) and unknown (not examined; what NOT RUN, skipped, deferred and n/a disclose), and a **Fail-closed roll-up** entry stating that unknown, unsupported, truncated and skipped never aggregate to pass, so a Summary or Verdict counts or names them. `grep -c "never aggregate to pass" CONTEXT.md` prints 1. No literal four-digit work-order or PRD id appears in the added text (`docs/kb/gates-scan-every-doc.md`).
  - Blocked by: —
- [x] **Protocol: state the roll-up rule once** — one short section in `docs/pipeline-protocol.md` — size:S
  - Accept: the new section states the rule once, links `CONTEXT.md` for the claim kinds without redefining observed, derived, inferred or unknown, and cites ADR-0107 for the gate half (detector H on `verification.md`, grandfathered by `date:` before `ROLLUP_ADOPTED`). `grep -n "derived (computed" docs/pipeline-protocol.md` prints nothing.
  - Blocked by: CONTEXT.md: claim kinds and fail-closed roll-up
- [x] **Templates and verify SKILL.md carry the rule** — `skills/verify/TEMPLATE.md`'s `## Summary` placeholder, `skills/review/TEMPLATE.md`'s `## Verdict` placeholder and `skills/verify/SKILL.md`'s "summary of it" line — size:S
  - Accept: each of the three places says the line counts or names every NOT RUN / unknown item and never reads as an unqualified pass over them, pointing to `CONTEXT.md` rather than redefining the claim kinds. `skills/review/SKILL.md` is unchanged (it never describes the Verdict line). The verify template's Summary heading is still spelled exactly `## Summary`. `.claude-plugin/plugin.json` is unchanged (ADR-0095).
  - Blocked by: CONTEXT.md: claim kinds and fail-closed roll-up

## Milestone 3: the finished change passes every check

- [x] **Whole-repo verify** — the four CI checks and the one-owner pre-pass over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` each print `gates: 0 problem(s)`. `git diff --stat main -- 'docs/**/verification.md' 'docs/**/review.md'` prints nothing, and `git diff --name-only main -- .claude-plugin/plugin.json` prints nothing. `python3 one_owner.py` reports no `one-owner:` problem naming `ROLLUP_ADOPTED` or `SUMMARY_UNKNOWN_TERM`.
  - Blocked by: Payload mirror and manifest regen; Protocol: state the roll-up rule once; Templates and verify SKILL.md carry the rule

## Milestone 4: Review fix loop (Owner-authorized 2026-10-17)

The Owner decided live on 2026-10-17 to fix both open review majors before
Ship. When this milestone is done, a quoted, empty or non-ISO `date:` no
longer grandfathers a post-cutoff Summary, and the reviewer's honest gap
phrasings that unambiguously mean not-examined satisfy the Summary rule.

- [x] **Date-dodge tests** — new cases in `TestEvidenceRollUp` — size:S
  - Accept: through `gates.evidence_problems`, a full-pass Summary over a NOT RUN criterion gives the roll-up problem when `date:` is `"2026-10-20"`, `'2026-10-20'`, empty, `20/10/2026` or `16 Oct 2026`; gives `[]` when `date:` is `"2026-10-16"` (quoted ISO, pre-cutoff) or `2026-10-16T09:00:00` (datetime, pre-cutoff). Run before the next item, the five dodge cases fail.
  - Blocked by: —
- [x] **Grandfather only an ISO date** — `_rollup_applies` strips surrounding quotes and whitespace, takes a datetime's date part, and grandfathers only a `YYYY-MM-DD` value before `ROLLUP_ADOPTED`; detectors O and M unchanged; one backlog seed for O and M's raw-string compare — size:S
  - Accept: the date-dodge tests pass; every other `tests/test_gates.py` case passes unedited; `docs/backlog.md` gains one seed line ending `(from: session:2026-10-17)`.
  - Blocked by: Date-dodge tests
- [x] **Honest-wording tests** — new cases in `TestEvidenceRollUp` — size:S
  - Accept: each added shape (see Notes) gives `[]` over a NOT RUN criterion dated past the cutoff, and each rejected shape still gives the roll-up problem. Run before the next item, every added shape fails.
  - Blocked by: —
- [x] **Widen `SUMMARY_UNKNOWN_TERM`** — Summary-only extras, the trailing boundary no longer rejects `-` or `/`; the heads shared with `DISCLOSURE_VERDICT` stay identical — size:S
  - Accept: the honest-wording tests pass; every other `tests/test_gates.py` case passes unedited; `python3 gates.py` on the real tree prints `gates: 0 problem(s)`.
  - Blocked by: Honest-wording tests
- [ ] **Docs, payload and manifest** — dated amendment in ADR-0107 and `architecture.md`; the verify SKILL.md overstatement corrected; payload copies and manifest regenerated — size:S
  - Accept: stray `.orig`/`.rej` deleted first, `python3 factory_init.py update-manifest` prints `factory-init: 0 problem(s)`; the four CI checks are clean; `git diff --stat origin/main -- 'docs/**/verification.md' 'docs/**/review.md'` lists only this run's own files; `.claude-plugin/plugin.json` unchanged.
  - Blocked by: Grandfather only an ISO date; Widen `SUMMARY_UNKNOWN_TERM`

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

- 2026-10-17 (Templates and verify SKILL.md, placement): the "summary of
  it" line in `skills/verify/SKILL.md` step 4 is about evidence not being
  a summary, not about the `## Summary` line. The roll-up sentence is
  appended to that step's text right after it, naming `## Summary`
  explicitly, rather than reworded into it. The two templates point to
  "the plugin's CONTEXT.md" in prose, not by a link, because their text
  is copied into a target repo where a relative link would dangle.

- 2026-10-17 (Whole-repo verify): `python3 run_tests.py` printed
  `tests: 3303 tests across 106 modules in 18.9s on 8 workers, 0
  problem(s)`; `python3 lint.py` printed `lint: 0 problem(s) across 34
  skills`; `python3 kb.py drift` printed `drift: 0 problem(s)`;
  `python3 gates.py && python3 gates.py --selftest` printed `gates: 0
  problem(s)` and `selftest: ok`. `python3 one_owner.py` (advisory)
  printed `one-owner: 9 problem(s)`, none naming `ROLLUP_ADOPTED` or
  `SUMMARY_UNKNOWN_TERM`, and none in code this run added. `git diff
  --stat origin/main -- 'docs/**/verification.md' 'docs/**/review.md'`
  and `git diff --name-only origin/main -- .claude-plugin/plugin.json`
  printed nothing (against the stale local `main`, see the deviation
  above, the first lists only the two pr-body-preflight files from
  #991).

- 2026-10-17 (Review fix loop, Date-dodge tests, RED): `python3 -m
  unittest tests.test_gates.TestEvidenceRollUp` printed `FAILED
  (failures=5)`, one per dodge shape (`date='"2026-10-20"'`,
  `date="'2026-10-20'"`, `date=''`, `date='20/10/2026'`,
  `date='16 Oct 2026'`), each `AssertionError: Lists differ: [] !=
  [(8, 'summary "Summary" neither counts nor[118 chars]ss')]`. The
  pre-cutoff quoted and datetime cases pass before the fix as well; they
  pin that the normalization still grandfathers them.
- 2026-10-17 (Review fix loop, Grandfather only an ISO date, GREEN):
  `python3 -m unittest tests.test_gates` printed `OK`; `python3
  gates.py` printed `gates: 0 problem(s)`. A date carrying a trailing
  YAML comment (`date: 2026-10-01 # x`) is now judged, not
  grandfathered: it is not ISO after normalization, and the Owner's rule
  grandfathers only a value that is. No tracked `prd.md`, `defect.md` or
  `verification.md` has a non-ISO `date:`, so O and M (unchanged, seeded
  in `docs/backlog.md`) and H's real-tree output are unaffected.
- 2026-10-17 (Review fix loop, Honest-wording tests, RED): `python3 -m
  unittest tests.test_gates.TestEvidenceRollUp` printed `FAILED
  (failures=12)`, one per added shape, the first `FAIL:
  test_honest_gap_wordings_from_review_pass (...) (summary='7 PASS; the
  live dispatch check could not be run.')`. The three rejected shapes
  already fail the gate before the change; their test pins that they
  still do.
- 2026-10-17 (Review fix loop, wording decisions). Added, each a
  Summary-only alternative, so the heads `SUMMARY_UNKNOWN_TERM` shares
  with `DISCLOSURE_VERDICT` stay spelled identically (the deferred
  shared-heads minor is not made worse):
  - `not applicable`: the spelled-out `n/a`, the same claim kind.
  - `n't (been )?run` (straight or curly apostrophe): "wasn't run",
    "hasn't been run", "couldn't run" can only mean not run.
  - `not be(en)? run`: "could not be run", "has not been run".
  - trailing boundary `(?!\w)` instead of `(?![\w/-])`: a hyphen or
    slash after a head ("skipped-by-design", "deferred/blocked") no
    longer hides it. The leading boundary is unchanged.
  - `unexercised` ("remains unexercised"): only means not examined.
  - `not_?run` ("NOT_RUN", "NOTRUN"): an identifier spelling of the
    NOT RUN head; unambiguous.
  - `unverifiable`: says the check could not be examined; the honest
    "NOT YET VERIFIABLE" already passes through `not yet`.
  Rejected, pinned as still failing:
  - `outstanding` ("is outstanding"): as often praise ("outstanding
    coverage") as a gap, so it would satisfy the rule on incidental prose.
  - `blocked` ("1 BLOCKED"): this repo's artifacts routinely describe a
    gate that "blocked" a bad change as passing behaviour; "deferred/
    blocked" already passes through `deferred`.
  - `skips` ("1 skips"): mostly a verb describing behaviour ("the
    detector skips fenced lines"), and widening the shared `skip(?:ped)?`
    head in one regex only would drift the two copies.
- 2026-10-17 (Review fix loop, Widen `SUMMARY_UNKNOWN_TERM`, GREEN):
  `python3 -m unittest tests.test_gates` printed `OK`; `python3
  gates.py` printed `gates: 0 problem(s)`; no pre-existing case edited.
