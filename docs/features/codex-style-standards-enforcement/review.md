---
stage: review
run: feature:codex-style-standards-enforcement
date: 2026-09-28
assumptions:
  - "No live user arbitrated severity. The skill is draft-first and lets the user arbitrate, but this is an unattended autorun Review, so the reviewer ranked every finding. Rubric used: critical = shipped behavior that corrupts committed state or disables a gate on real content today, or any finding against an `enforced` statement. Major = an unmet PRD-0004 success criterion or architecture contract, or a defect that silently produces a wrong result on a documented path. Minor = an edge case, a loud (not silent) failure, or a documentation inaccuracy."
  - "Every major is recorded `open — needs owner decision`, never deferred. The skill says majors are 'fixed or explicitly deferred by the user', and no user decided anything here (autorun brief standing instruction)."
  - "Minors are deferred by the reviewer, each with its reason logged, under the skill's 'Minors ... may be deferred freely'."
  - "Step 5 loaded the index from the repo-relative `docs/standards.json` in this worktree, not the skill's literal `../../docs/standards.json`. From the installed plugin cache (0.1.0 and 0.2.0) that path resolves to a file that does not exist, and the charters use the repo-relative reading. The divergence is itself a finding (Major 4)."
  - "Verify's candidate on the stale plugin version is ranked minor and routed to Ship, not Implement, following `docs/features/pipeline-board/review.md`'s precedent for plugin-cache propagation. The resume brief forbids a published plugin version bump, so Ship can only record it as a pending owner step."
  - "Commit 40ac3dd (#527, detectors N and O) edits the same `gates.py` CHECKERS tuple as K and M, but it belongs to another run and changes no K or M line. It is outside this review's scope."
---

# Review: Codex-style standards enforcement

## Scope

This run's commits on `main`:

- f3ceb97 (#500): idea, PRD, architecture and breakdown.
- 4d565bb (#506): renumbered the work-order ids.
- **69ecd19 (#517)**, the implementation: 24 files, +2731/−139. It adds `standards_index.py` and its payload copy, detectors K and M in `gates.py` and its payload copy, the `factory.py` verb, the `factory_init.MIRRORS` entry and the manifest, ADR-0073, the ADR-0004 and ADR-0032 back-fills, `docs/standards.json`, the review and architect skill and template edits, both charter edits, `docs/setup.md` counts, and three test modules.
- f9382c4 (#569): the owner's WO-0064 deferral.

I read every code file in #517 line by line, plus the prose diffs of all four skill and charter files. Verify's six candidate findings were each re-checked against the code, and then the three passes ran.

Every failure scenario was reproduced in a `git archive HEAD` copy under the session scratchpad, never in the worktree. After each scenario that copy was restored, and `gates: 0 problem(s)` was confirmed.

**Standards (step 5).** `docs/standards.json` holds 4 statements, all `advisory`. The diff touches root tools and `factory/**` (domain `factory`), and skill bodies and `docs/**` (domains `pipeline` and `docs`). It touches no eval set or harness, so `eval-honesty` is filtered out. The diff was checked against the three statements that remain:

- `stdlib-only`: holds. `standards_index.py` imports only `json`, `re`, `sys`, `pathlib` and the repo's own `cli` and `knowledge_plane` seams, and `tests/test_standards_index.py` imports only stdlib plus the repo's own test helper.
- `adr0032-one-way-mirror`: holds. The WO-0064 row reached `main` in 4d565bb on 2026-09-21. Its mirror issue #518 was created afterwards, at `2026-09-22T04:55:55Z`.
- `adr0004-typed-ids-in-frontmatter`: holds. `docs/standards.json` holds slugs, not run-artifact typed ids, and PRD-0004 lives in its own frontmatter.

No finding below cites a slug, because none is a violation of an indexed statement.

## Findings

### Major 1: detector M passes an unedited capture template on 3 of its 5 required sections (new)

- Scenario: copy `skills/capture/TEMPLATE.md` to `docs/fixes/<slug>/defect.md` and change only the frontmatter (`date: 2026-09-28`). Run M:
  ```
  $ diff skills/capture/TEMPLATE.md docs/fixes/zz-verbatim-template/defect.md
  3,5c3,5
  < run: maintenance:<slug>
  < date: YYYY-MM-DD
  < re-entry: implement | architect
  ---
  > run: maintenance:zz-verbatim-template
  > date: 2026-09-28
  > re-entry: implement
  -- M on the unedited template:
  M: docs/fixes/zz-verbatim-template/defect.md required section 'Root-cause hypothesis' is present but placeholder-only (template text was never filled in)
  M: docs/fixes/zz-verbatim-template/defect.md required section 'Ruled out' is present but placeholder-only (template text was never filled in)
  count 2
  ```
  `Defect (or Condition)`, `Reproduction / Evidence` and `Blast radius` still hold the template's own placeholders, and all three pass.
- Cause: `CAPTURE_PLACEHOLDER` (`^\s*[-*+]?\s*<[^>]*>\s*$`) only recognises a placeholder that opens and closes on one line. The template wraps those three placeholders over 2 or 3 lines (TEMPLATE.md lines 17–18, 22–24 and 32–33). Each wrapped line then reads as real content.
- Why the tests missed it: `test_a_placeholder_only_section_is_flagged` and the selftest fixture both use shortened one-line paraphrases. For example, the test uses `<Who and what is affected, how badly, since when.>`, but the template's text runs over two lines. Verify's criterion-7 plant flagged a placeholder-only `Reproduction / Evidence`, which the real three-line placeholder never triggers, so that plant was a paraphrase too.
- Decayed contract: PRD-0004's success criterion says "each non-placeholder", and the `gates.py` roster says "each with real (non-placeholder) content".
- Standard: none
- Decision: **open — needs owner decision.** Suggested route is Implement:
  1. Match a placeholder that runs from `<` to its closing `>` across lines.
  2. Build the unit-test and selftest fixtures from the real template text.
  3. Re-run `factory_init.py update-manifest`, because `gates.py` is mirrored.

### Major 2: `standards_index.py update`, the fix K's own message prescribes, silently discards committed content (Verify candidate 5, widened and re-ranked)

- Scenario: promote `adr0032-one-way-mirror` to `enforced` and add a hand-curated entry sourced `AGENTS.md#no-push`. K flags the new entry as drift and says to run `update`. `update` exits 0, discards both the promotion and the entry, and K goes green:
  ```
  before: K -> ['K: docs/standards.json has drifted from a fresh ADR regeneration (run `python3 standards_index.py update`)']
  update -> [] (wrote file, exit 0)
  after: {'adr0004-typed-ids-in-frontmatter': 'advisory', 'adr0032-one-way-mirror': 'advisory', 'eval-honesty': 'advisory', 'stdlib-only': 'advisory'}
  after: K -> []
  ```
  A promotion done exactly as the backlog seed for WO-0064's revisit prescribes ("promote those with the flagged evidence cited inline") is green under K. The next `update` then silently reverts it, for example when any ADR gains a bullet:
  ```
  promoted, before update: K -> []
  update -> [] (exit 0)
  after update: {'status': 'advisory', 'evidence': None} | K -> []
  ```
- Cause: `build_index` builds fresh dicts with `status: "advisory"`. `update` keeps only entries whose source starts with `CLAUDE.md#` and silently drops everything else, including extra keys and non-dict entries. A hand-curated `enforced` entry survives (`test_preserves_hand_curated_entries_untouched`). No test covers an ADR-derived one.
- Decayed contract: `gates.py`'s own comment above `_DRIFT_FIELDS` says "a promotion is a docs/standards.json edit that must survive a later regeneration". ADR-0073 records this as an open edge "for whoever exercises WO-0064". That row closed by deferral, and the `docs/backlog.md` seed that replaces it does not carry the edge. The first real promotion will lose it.
- Standard: none
- Decision: **open — needs owner decision.** Latent today, because no statement is `enforced`. Suggested route is Implement: carry the committed `status` (and any extra keys) forward for slugs that still exist, and refuse to drop an entry `update` does not recognise.

### Major 3: the `CLAUDE.md#`-sourced half of the index is asserted, not verified (Verify criterion 9, accepted)

- Scenario: re-read against the code. K's drift comparison skips every entry whose source starts with `standards_index.HAND_CURATED_PREFIX`, and no other check reads those entries. `standards_index.py`'s own comment says the anchor text is "never validated here". Verify pointed `stdlib-only` at `CLAUDE.md#no-such-anchor` and inverted its statement to "Root Python scripts SHOULD pull in any third-party dependency they like". `K`, `gates.py` and `lint.py` all stayed at 0 problems.
- Decayed contract: PRD-0004's success criterion says "verified by the drift detector itself, not asserted". Its open question asked for a `CLAUDE.md` source form "that the drift detector can still verify". `architecture.md` Component 1 promises "see Decisions below for how that resolves", but no Decisions bullet resolves it. The WO-0057 row then relaxed the bar to "resolvable by a human/reviewer". Two of the four entries are hand-maintained paraphrases.
- Standard: none
- Decision: **open — needs owner decision.** There are two routes:
  - (a) Implement: have K resolve each `CLAUDE.md#` anchor and check its statement against CLAUDE.md.
  - (b) Accept the WO-0057 relaxation, and route back to PRD-0004 to reword the criterion.

### Major 4: the review and architect skills read the plugin's index, not the target repo's (Verify candidate 4, accepted)

- Scenario: `skills/review/SKILL.md` step 5 and `skills/architect/SKILL.md` step 4 read `../../docs/standards.json`. Everywhere else in `skills/`, `../../` points at plugin-owned files, such as `../../docs/pipeline-protocol.md` and pipeline-board's `../../board.py`. The installed plugin cache ships the whole `docs/` tree:
  ```
  $ ls ~/.claude/plugins/cache/skills/idea-to-prod/0.2.0/docs | head -5
  adr
  backlog.md
  factory
  features
  fixes
  $ grep -n "docs/standards.json" factory/charters/reviewer/CHARTER.md factory/charters/architect/CHARTER.md
  factory/charters/reviewer/CHARTER.md:47:7. Load `docs/standards.json` if present, filtered to statements whose
  factory/charters/architect/CHARTER.md:31:2. Load `docs/standards.json` if present, filtered to statements whose
  ```
  Once a plugin version that carries `docs/standards.json` is installed, the skill in any product repo reads this repo's four statements. For example, it would apply `stdlib-only` to that product's Python diff and ignore the product's own index. The charters read the target repo's file. ADR-0073 says "each repo using this pipeline generates its own", and PRD-0004's Actors section gives the skill and charter paths the "same index".
- This is a static reading. Exercising it in another repo needs a live model run, which was not authorised.
- Standard: none
- Decision: **open — needs owner decision.** Suggested route is Implement: a prose fix in both SKILL.md files, naming the target repo's `docs/standards.json` the way the charters do.

### Major 5: enforcement status moved to a path an agent can merge without the owner (new, security pass)

- Scenario: PRD-0004 makes the owner "the sole authority for advisory→enforced promotion", and issue #448 says promotion "is an explicit human decision". ADR-0073 decision (c) moved status out of `docs/adr/**` into `docs/standards.json`. That file is not on ADR-0036 condition 3's gate-change list ("any PR touching `docs/adr/**`, a run's `prd.md`, `architecture.md`, or `docs/design/**`"). It is not on the reviewer charter's "Must never … merge" list either, and CODEOWNERS names no explicit path for it. The `docs/backlog.md` merge-queue seed also records that branch protection is unavailable on this plan, so the charter's list is the only guard.
- So an agent PR that promotes or demotes a statement meets ADR-0036's conditions, and the reviewer charter may merge it with no human involved. The charter says "Load `docs/standards.json` if present" without naming a ref, and in the PR's checkout that is the PR's own copy. A PR that demotes an `enforced` statement alongside code that violates it therefore removes its own blocking finding.
- ADR-0073 does not mention this consequence.
- Standard: none
- Decision: **open — needs owner decision.** Latent today, because no statement is `enforced`. The likely remedy is adding `docs/standards.json` (or its `status` field) to the gate-change list. That is itself a governance change, which only the owner merges under ADR-0036.

### Minor 1: nothing checks the committed index's own integrity: duplicate slugs and out-of-enum values pass (new)

- Scenario (scratch copy):
  ```
  == (1) hand-curated entry duplicates ADR-derived slug adr0032-one-way-mirror
     update -> [] (wrote file)
     slugs after update: ['adr0004-typed-ids-in-frontmatter', 'adr0032-one-way-mirror', 'adr0032-one-way-mirror', 'eval-honesty', 'stdlib-only']
     K -> []
  == (2) ADR-derived status set to 'Enforced' (capital E)
     K -> []
  == (3) hand-curated stdlib-only: level MAY, status blocking, domain ui
     K -> []
  ```
  `standards_index.LEVELS` and `STATUSES` are declared, but no module or test reads them. Only `DOMAINS` is checked, and only on ADR bullets. A status typo such as `Enforced` also skips K's supersession check, because that check matches `== "enforced"` exactly.
- Decayed contract: `architecture.md` §Interfaces says `update` gives "a nonzero exit if a regenerated slug collides with a hand-curated one". That is not implemented. PRD-0004 criterion 1's enums are true today by inspection only.
- Standard: none
- Decision: deferred. All four committed entries are in-enum and have unique slugs (Verify criterion 1). The index is 4 hand-reviewed entries. The fix belongs in the same function Majors 2 and 3 would touch, so it should ride along with that Implement pass rather than get its own.

### Minor 2: a missing index is silent even after ADRs declare statements, and stamped repos are never told to create one (new)

- Scenario (scratch copy): delete `docs/standards.json` and append a malformed bullet to ADR-0032's `## Normative statements`:
  ```
  -- index deleted + malformed bullet planted:
  gates: 0 problem(s)
  K -> []
  ```
  Only a manual `standards_index.py update` reports the bad bullet. `docs/setup.md`, `README.md`, `AGENTS.md` and `CONTEXT.md` never mention the index. A stamped repo gets the script and K, but no step that bootstraps an index. There, K stays silent forever and the skills proceed as if the repo were unbootstrapped.
- Standard: none
- Decision: deferred. "An absent index is not a K problem" is `architecture.md`'s explicit contract, following G's precedent. Narrowing it, for example to "absent while any ADR has a `## Normative statements` section", is a design change for the owner, not a defect against the stated design.

### Minor 3: M's grandfather cutoff does not do what ADR-0073 says it does (new)

- Scenario (a): ADR-0073 says "a missing or unparseable date is NOT exempted (fail closed)". But the check is a string comparison, `date < CAPTURE_ADOPTED`. A brief missing four sections gives:
  ```
  '2026-09-28'   -> checked (4 problems)
  '09/28/2026'   -> grandfathered (0 problems)
  '(pending)'    -> grandfathered (0 problems)
  '1 Oct 2026'   -> grandfathered (0 problems)
  'TBD'          -> checked (4 problems)
  '2026-9-28'    -> checked (4 problems)
  None           -> checked (4 problems)
  ```
- Scenario (b): ADR-0073 says the cutoff "generalizes correctly to every other repo", because a brief already on disk "predates M by construction". But `CAPTURE_ADOPTED` is a fixed `2026-09-21`. Take a stamped repo that captured a brief on 2026-10-01 and takes this factory update on 2026-10-20. That brief predates M in that repo, but it is checked in full.
- Scenario (c): ADR-0073 says the corpus "almost entirely predates TEMPLATE.md's current heading set". Git history disagrees: `## Blast radius` and `## Ruled out` arrived in e50f934 on 2026-07-03, and the 57 briefs are dated 2026-08-13 to 2026-09-20. The briefs deviated from the template; they did not predate it (40 of the 57 lack `## Blast radius`).
- Standard: none
- Decision: deferred.
  - (a) needs a date format the protocol's frontmatter does not allow, and it only skips a check.
  - (b) fails loudly, with actionable problem strings, not silently.
  - (c) is a record inaccuracy. ADRs are supersede-only, so correcting it is the owner's call.
  - Out of scope, for the owner: detector O (#527, ADR-0072) copies the same string comparison at `gates.py:1383` (`COVERAGE_ADOPTED`).

### Minor 4: the shipped selftest never fails M on `Reproduction / Evidence` (Verify criterion 14, accepted)

- Scenario: re-read at `gates.py`'s selftest. The M fixture plants two sections missing and two placeholder-only, and asserts `Reproduction / Evidence` clean. Stamped repos run only `gates.py --selftest`, so there nothing would catch that name dropping out of `CAPTURE_REQUIRED_SECTIONS`. In this repo, the unit test `test_a_missing_section_is_flagged` pins all five.
- Standard: none
- Decision: deferred. This folds into Major 1's fix: a selftest fixture built from the real template text exercises every required section, so it is not worth a separate Implement pass.

### Minor 5: the review skill's fix-loop rule is ambiguous for a major that cites an `advisory` statement (new)

- Scenario: `skills/review/SKILL.md` step 8 now reads both "Majors are fixed or explicitly deferred by the user" and "Minors, and findings against `advisory` statements, may be deferred freely". A major-severity defect that also cites an advisory slug matches both rules, and they disagree. Before #517 the major rule was unconditional. Every statement is advisory today, so the first major that cites one will hit this.
- Standard: none
- Decision: deferred. It is a one-clause wording fix. No finding in this review cites a violated statement, so it does not affect this review's own decisions.

### Minor 6: the WO-0063 close-out note overstates the battery record (Verify criterion 8, accepted)

- Scenario: `breakdown.md`'s WO-0063 note says the battery "stayed green through every one of orders 51 through 62". Verify's per-commit replay shows two commits were red: WO-0052's own commit (1 test failure), and WO-0053's (5 test failures plus detector E). #517 squash-merged at a green 69ecd19, so `main`'s history never contains a red state.
- Standard: none. `eval-honesty` is filtered out by domain, and this is an overstatement in a run artifact, not fabricated eval evidence.
- Decision: deferred. There is no code consequence. The correction is a dated line in `breakdown.md`'s Notes, which is outside Review's write scope. The per-commit versus per-merge reading of PRD-0004's criterion stays with the owner, as logged in `verification.md`'s `assumptions:`.

### Minor 7: `.claude-plugin/plugin.json` is still `0.2.0` after `skills/` changed (Verify candidate 6, routed to Ship)

- Scenario: #517 (this run) and #527 (another run) both changed `skills/` after the last bump (04c6efe, #484). The installed `idea-to-prod/0.2.0` cache has no "Load applicable standards" step, so an installed plugin cannot run what this run added.
- Standard: none
- Decision: deferred to Ship. This is a release step, not a code defect, following `pipeline-board/review.md`'s precedent, and it spans two runs. The resume brief forbids a published version bump, so Ship records it as a pending owner step. Fix Major 4 before any bump, so the bump never ships the plugin-relative index path.

## Passes with no findings

No pass was fully clean. These parts of each pass came back clean:

- **Correctness:**
  - `parse_bullet` rejects every malformed shape it claims to: no slug, bad domain, zero or doubled keywords, unreadable line. `update` refuses to write on any problem.
  - Sorting is deterministic, and `MUST NOT` and `SHOULD NOT` bucket correctly.
  - K's supersession check reuses D's `_adr_status_from_lines` and `_status_head` rather than adding a second parser.
  - `repo_root()` resolves correctly from the stamped `tools/factory/` location.
  - Incidental, and out of scope: a non-UTF-8 byte in any ADR crashes `gates.py` with a traceback. The crash is in the pre-existing `knowledge_plane.parse_run` (line 373), with or without the index, so it is not this diff's regression.
- **Design:**
  - K and M are separate letters, as ADR-0073 decided.
  - M builds on H's `_skip_frontmatter` and `_walk_sections` rather than duplicating them.
  - The `MIRRORS` entry, the manifest regen, the `EXPECTED_RELS` pin, the `factory.py` verb and the `docs/setup.md` counts all agree.
  - The reviewer charter's `## Merge decision (ADR-0036)` section is untouched.
  - Deviations from `architecture.md` are recorded as Majors 3 and 4 and Minor 1.
- **Security:**
  - The new code reads local files and writes one JSON file. It makes no network call, runs no shell command and holds no secrets.
  - Input is parsed with `json.loads` and anchored regexes, and problem strings carry only repo-relative paths and line text.
  - The one security-pass finding is governance (Major 5), not code.

## Verdict

**Not ready to ship until the owner rules on five open majors.**

Nothing blocks Ship under the skill's must-fix rule. There is no critical finding, and no finding against an `enforced` statement (all four are `advisory`), so nothing is routed to Implement unconditionally.

Suggested owner routing:

- **Majors 1, 2 and 4 → Implement**, then re-verify. These are bounded code and prose fixes. Minors 1 and 4 ride along with them.
- **Major 3 → the owner chooses** between Implement (an anchor check) and PRD-0004 (reword the criterion).
- **Major 5 → an owner-authored governance change** to ADR-0036's gate-change list, or an explicit acceptance of the risk.

Ship's own item is Minor 7, the plugin version bump. It is recorded, not performed, and should come after Major 4 is fixed.
