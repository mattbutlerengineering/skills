---
stage: verify
run: feature:docs-audit
date: 2026-10-10
assumptions:
  - "No live interview: the soft gate was read from breakdown.md (eleven rows, WO-0114 to WO-0124, all checked) and the criteria list is PRD-0010's eight Success criteria plus the one breakdown acceptance no PRD criterion covers (every row checked, with one honest zero-cost ledger row each). Taken from the skill's default, without asking which subset to verify."
  - "The base is the local ref feat/grok-harness at a0f7553905e93f97db571412ab35f8c88bfe8778, the same commit claims.md's Preamble audited; #618 had not moved it. Whether #618 has merged on GitHub was not checked (no network); PRD-0010 open question 4 leaves a moved base to the owner."
  - "The Check-column re-run was extracted mechanically by a scratch script (quoted verbatim in claims.md's Verify re-run section), each Check run as its own `zsh -c` process from the worktree root. A `corrected` row is re-run with the new Check its Disposition names, not the original (which proved the old text false); `follow-up` rows are excluded under architecture.md's fourth assumption. Taken from the architecture, without user input."
  - "Spot-check sample: ten ids drawn with Python's random.sample under random.seed(20261010) from the 444 re-checked ids, plus seven of the twelve corrected rows chosen by hand (every corrected row outside AGENTS-42 to AGENTS-45, whose resync the CLAUDE.md/AGENTS.md parity diff checks wholesale). A check that passes but is narrower than its claim is recorded as an observation, not a failure; only a check that passes while the claim is false would be vacuous."
  - "PRD-0010's 'In place, in scope' is applied by intent for docs/factory/costs.jsonl, as breakdown.md's third assumption directs Verify to: the literal file list omits it, and it carries only the eleven appended owner-session ledger rows that keep detector G (and so the Battery criterion) green. The literal deviation is recorded in that criterion's evidence, not hidden."
---

# Verification: documentation audit

## Summary

8 PASS, 0 FAIL across PRD-0010's eight success criteria, plus one PASS for
the breakdown's close-out acceptance (eleven rows checked, eleven
zero-cost ledger rows). The mechanical re-run of every Check in
`claims.md` on the tip re-checked **444 claims with 0 failures**, five
follow-up rows excluded by id. Seventeen independent spot-checks found no
vacuous Check (two are narrower than their claim; the claim holds by the
independent read). The battery is green: 1958 tests OK, `lint: 0
problem(s)`, `gates: 0 problem(s)`, `selftest: ok`; the
`tests/test_cli_process_reaping.py` flake Implement saw did not recur
(load average 9.00-11.18 during the run), though a second load-sensitive test failed once at load 54 and passed on re-run (Notes). One caveat for Review, already
logged as a breakdown assumption: the scope diff carries one `M` line,
`docs/factory/costs.jsonl`, outside PRD-0010's literal file list. Next
stage: Review.

Tip `d03a0ba`, sixteen commits ahead of base `feat/grok-harness`
`a0f7553`; interpreter `Python 3.14.6`.

## Criteria & evidence

### 1. Claim inventory covers the set

- Check: one `## <path>` section per in-scope file in `claims.md`; every
  per-doc row parsed for eight cells, a backticked Check, an `exit N`
  Result and a verdict in the vocabulary; a case-insensitive grep for
  "from memory".
- Evidence:
  ```
  README.md:1 CONTEXT.md:1 LEDGER.md:1 AGENTS.md:1 CLAUDE.md:1 docs/setup.md:1 docs/pipeline-protocol.md:1 docs/output-evals.md:1 docs/factory/doc-gardener-routine.md:1 docs/factory/improvement-routine.md:1 docs/factory/queue-groomer-routine.md:1 docs/factory/retro-reflect-routine.md:1 evals/README.md:1
  449 rows; malformed: []
  $ grep -ci "from memory" docs/features/docs-audit/claims.md
  0
  per prefix: {'README': 37, 'CONTEXT': 30, 'LEDGER': 31, 'AGENTS': 45, 'CLAUDE': 58, 'SETUP': 53, 'PROTO': 46, 'OEVAL': 18, 'ROUT-GARD': 26, 'ROUT-IMPR': 35, 'ROUT-GROOM': 24, 'ROUT-RETRO': 23, 'EVALS': 18}
  ```
  (the per-prefix counts exclude the five follow-up rows; with them
  LEDGER has 34 rows and PROTO 48, 449 in all.)
- Result: PASS

### 2. Every false or stale claim is resolved

- Check: listed the 17 `false`/`stale` rows; mapped each `corrected` row
  to a hunk of `git diff -U0 feat/grok-harness...HEAD` on its doc covering
  its base line, and each `follow-up F-n` to a Follow-ups row.
- Evidence (hunk headers, base side first):
  ```
  CONTEXT.md      @@ -43,3 +43,4 @@   <- CONTEXT-8 (43-44)
                  @@ -135,2 +136,3 @@ <- CONTEXT-30 (135-136)
  AGENTS.md       @@ -8 +8 @@         <- AGENTS-4 (8)
                  @@ -24 +24,16 @@    <- AGENTS-42 (21-24), AGENTS-43 (17-24)
                  @@ -36,4 +51,13 @@  <- AGENTS-44 (35-36), AGENTS-45 (30-39)
  CLAUDE.md       @@ -8 +8 @@         <- CLAUDE-4 (8)
  docs/setup.md   @@ -112,6 +112,6 @@ <- SETUP-34 (112), SETUP-36 (114)
                  @@ -145 +145,2 @@   <- SETUP-46 (145-146)
  evals/README.md @@ -22,3 +22,6 @@   <- EVALS-11 (19-23)
  follow-up F-3   <- LEDGER-32, LEDGER-33, LEDGER-34 (LEDGER.md: no hunk)
  follow-up F-4   <- PROTO-34, PROTO-37 (docs/pipeline-protocol.md: no hunk)
  ```
  12 corrected, 0 removed, 5 follow-up; every hunk in the diff maps to a
  row, and every row to a hunk or a register row with a reason and a
  carrier.
- Result: PASS

### 3. The corrected docs pass their own checks

- Check: the mechanical re-run, quoted in full in `claims.md` § Verify
  re-run.
- Evidence:
  ```
  rows parsed: 449
  re-checked: 444 (true: 432 corrected: 12 )
  passed: 444 failed: 0
  excluded: [('LEDGER-32', 'follow-up F-3'), ('LEDGER-33', 'follow-up F-3'), ('LEDGER-34', 'follow-up F-3'), ('PROTO-34', 'follow-up F-4'), ('PROTO-37', 'follow-up F-4')]
  ```
  444 claims re-checked, zero failures. Excluded by id (false claim left
  in place by the follow-up disposition, architecture.md's fourth
  assumption): LEDGER-32, LEDGER-33, LEDGER-34, PROTO-34, PROTO-37.
- Spot-checks (a different method from each row's recorded Check):

  | Row | Recorded Check | Independent check | Finding |
  |---|---|---|---|
  | CLAUDE-37 | `ls plane_drift.py` | read CLAUDE.md 57-62 and grepped importers: `dashboard.py`, `sweeps.py` (plus tests); neither in `factory_init.MIRRORS`, nor `plane_drift.py`; `reconcile_drift(..., absent_is_drift=True)` exists; ADR-0060 `Status: accepted` | holds; Check is narrower than the passage (existence only) |
  | AGENTS-22 | `ALL_SKILLS == next + stages + utilities` | read `protocol.py` lines 15-32; compared `sorted(ALL_SKILLS)` to every `skills/*/SKILL.md` dir: `25 True` | holds |
  | ROUT-GARD-21 | grep of ADR-0034's S row | read the playbook line 106 and ADR-0034's class table (`S ≈ $5, one file cluster`) | holds |
  | ROUT-RETRO-8 | ADR-0036 names the four paths | read ADR-0036 lines 33-34 and `.github/CODEOWNERS` (`docs/adr/`, `docs/features/`, `docs/design/` owned) | holds |
  | README-22 | `ls docs/pipeline-protocol.md` | read the protocol's line 4 ("single source of truth for run discovery, orientation") and its `## Soft gating`, `## Artifact frontmatter` headings | holds; Check is existence only |
  | ROUT-IMPR-32 | grep of the charter bullet | read toolsmith `CHARTER.md` 80-85 under `Must never` | holds |
  | ROUT-RETRO-23 | `ls` of the linked playbook | read the playbook's Trigger section and CLAUDE.md lines 101-103 (deferral by owner decision; only the groomer's trigger exists) | holds (the deferral itself is remote/owner state, outside the tree) |
  | AGENTS-34 | `gates._adr_status` | read each ADR's `- Status:` line and `docs/adr/README.md` rows: 0012 and 0019 `accepted` | holds |
  | CLAUDE-26 | AST scan of root `*.py` | AST scan of all 117 tracked `.py`, tests and fixtures included: only `src` imports in three `factory/evals/fixtures/*` fixture repos, which are those repos' own package | holds |
  | SETUP-5 | `gates._adr_status` | read ADR-0005's `- Status: accepted` and the index row | holds |
  | CONTEXT-8 (corrected) | grep stage/router bodies for "Claude Code" | grepped the twelve stage/router `SKILL.md` for `grok`, `omp`, `oh-my-pi`, `claude code`, `codex`, `cursor` (word, case-insensitive): no hit; only `automate` (utility) names Claude Code | holds; Check is narrower than the claim (one harness name) |
  | CONTEXT-30 (corrected) | roles == stubs | listed `factory/charters/` (9 roles) and `factory/agents/` (9 `factory-<role>.md`), read CONTEXT.md 135-138 | holds |
  | SETUP-34 (corrected) | `len(declared_labels) == 13` | rebuilt the 13 from the parts the new text names: assembler.py reads 6 (`wo:ready-for-agent`, `budget-exhausted`, four `type:`), `human_gates.gate_labels()` 5, the template Makefile flips `wo:in-progress` and `wo:failed` — 6+5+2 = 13 | holds |
  | SETUP-36 (corrected) | `len(gate_labels()) == 5` | printed the set: `wo:draft`, `wo:prd-approved`, `wo:blueprint-approved`, `wo:needs-review`, `wo:merged` | holds |
  | SETUP-46 (corrected) | grep of the `ANTHROPIC_API_KEY ... CLAUDE_CODE_OAUTH_TOKEN` condition | read `assembler.yml`: the condition gates the claim step (99), the agent step "Run the chartered agent" (113) and the find step (207); the recorded Result cites 207 | holds; the grep does not pin the agent step specifically, but the agent step carries the same condition |
  | EVALS-11 (corrected) | regex over `evals/results` | `ls evals/results` by prefix (37 trigger, 1 trigger-omp, 1 output, 2 charter) and `eval_schema.py` lines 58-72 (`charter-<date>[-N].json`) | holds |
  | CLAUDE-4 (corrected) | three tools in `make check` | read CLAUDE.md line 8 and the Makefile `check:` target (lint, gates, gates --selftest, unittest) | holds |

  No vacuous Check found: every sampled claim is true by the independent
  read. A sweep of all 444 Checks found none that cannot fail (243
  `python3`, 125 `grep`, 80 `ls`, 1 `git`; no `python3 -c` without a
  conditional exit, no `|| true`).
- Result: PASS

### 4. One job per doc

- Check: counted the Jobs table and its duplicate job cells; read the
  Duplicates table; diffed CLAUDE.md and AGENTS.md above their Beads
  blocks.
- Evidence:
  ```
  job rows: 13
  duplicate job cells (sort | uniq -d): 0
  $ diff <(awk '/BEGIN BEADS/{exit} {print}' CLAUDE.md) <(awk '/BEGIN BEADS/{exit} {print}' AGENTS.md); echo $?
  0
  ```
  Seven Duplicates rows, each `deliberate → <reader>`, none collapsed, so
  no collapse link is owed; the CLAUDE.md/AGENTS.md pair (decision (e))
  and the routine skeleton (decision (f)) are both present.
- Result: PASS

### 5. Links resolve

- Check: the link-scan command recorded in `claims.md` § Link scan, run
  verbatim on the tip.
- Evidence:
  ```
  links: 59 relative across 13 files, 0 missing
  exit 0
  ```
- Result: PASS

### 6. Protocol stays a contract

- Check: `git diff feat/grok-harness...HEAD -- docs/pipeline-protocol.md`;
  the protocol pins and the conformance test.
- Evidence:
  ```
  $ git diff feat/grok-harness...HEAD -- docs/pipeline-protocol.md | wc -l
         0
  lint.check_protocol + check_protocol_tables: []
  $ python3 -m unittest tests.test_protocol_conformance
  OK
  ```
  No protocol hunk exists, so no hunk lacks a row; the two findings that
  would change what a skill must do (PROTO-34, PROTO-37) appear only as
  follow-up F-4. The criterion holds with nothing edited.
- Result: PASS

### 7. In place, in scope

- Check: the two commands PRD-0010 names, plus the ledger-only check.
- Evidence:
  ```
  $ git diff --name-status feat/grok-harness...HEAD
  M	AGENTS.md
  M	CLAUDE.md
  M	CONTEXT.md
  M	docs/factory/costs.jsonl
  A	docs/features/docs-audit/architecture.md
  A	docs/features/docs-audit/autorun-brief.md
  A	docs/features/docs-audit/breakdown.md
  A	docs/features/docs-audit/claims.md
  A	docs/features/docs-audit/idea.md
  A	docs/features/docs-audit/prd.md
  M	docs/setup.md
  M	evals/README.md
  $ git diff --stat feat/grok-harness...HEAD -- docs/adr docs/fixes docs/backlog.md skills factory/templates 'evals' ':!evals/README.md' 'docs/features' ':!docs/features/docs-audit'
  (no output, exit 0)
  $ git diff feat/grok-harness...HEAD -- docs/factory/costs.jsonl | grep '^[-+][^-+]' | grep -vc '^+{'
  0
  $ git diff feat/grok-harness...HEAD -- docs/factory/costs.jsonl | grep -c '^+{'
  11
  $ python3 -c "import factory_init; print([m[0] for m in factory_init.MIRRORS if m[0].endswith('.md')])"
  []
  ```
  (`verification.md` itself is added by this stage's commit, inside the
  run directory.) Only `M` lines for in-scope docs and `A` lines inside
  the run directory, no manifest change owed, and the out-of-scope stat is
  empty. **Literal deviation:** `M docs/factory/costs.jsonl` is not on
  PRD-0010's list; it carries only the eleven appended owner-session rows
  (`"tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered"`),
  admitted by breakdown.md's third assumption, which Verify applies. PASS
  under that reading; the owner can reverse it at merge.
- Result: PASS (by intent, per breakdown assumption three)

### 8. Battery

- Check: the three commands, outputs captured to scratch files and
  grepped; load average read before and after.
- Evidence:
  ```
  10:20  up 98 days, 12:03, 8 users, load averages: 9.00 17.73 38.68
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 1958 tests in 27.395s
  OK
  10:21  up 98 days, 12:03, 8 users, load averages: 11.18 17.46 37.86
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
  No Python file changed in the diff (`git diff --name-only
  feat/grok-harness...HEAD -- '*.py'` prints nothing), so the stdlib-only
  clause has nothing new to cover. The README, protocol and LEDGER prose
  pins each return `[]`. Re-run after writing this artifact: see Notes.
- Result: PASS

### Breakdown close-out (not covered by a PRD criterion)

- Check: every breakdown row checked, one ledger row each.
- Evidence:
  ```
  $ grep -c '^- \[x\] \*\*WO-' docs/features/docs-audit/breakdown.md
  11
  $ grep -c '^- \[ \]' docs/features/docs-audit/breakdown.md
  0
  $ git diff feat/grok-harness...HEAD -- docs/factory/costs.jsonl | grep -c '^+{'
  11
  ```
  The eleven rows run WO-0114 to WO-0124, each
  `owner-session:unmetered`.
- Result: PASS

## Failures

None.

## Not verified

- Remote state: whether #618 has merged or moved on GitHub, and every
  trigger id or issue state the routine playbooks mention (excluded from
  the inventory by architecture decision (g)).
- Claims the five follow-up rows leave false in the docs (LEDGER-32,
  LEDGER-33, LEDGER-34, PROTO-34, PROTO-37): by design, they still fail
  their Checks; they are carried by F-3 and F-4, not fixed.
- Whether a still-true passage is useful (PRD-0010 Out of scope).
- Completeness of extraction — that the inventory caught every checkable
  claim in the thirteen docs — is checked only by the seventeen
  spot-checks and the per-section counts, not by an independent re-read
  of all 2,164 lines.
- The battery ran on Python 3.14.6 only; CI's interpreter was not run
  locally.

## Notes

- The load-sensitive `tests/test_cli_process_reaping.py` failure
  Implement logged did not recur: one full run, load average 9-11, OK.
- After writing this file and the claims.md re-run section, the battery
  was run again, and it failed. Two of the failures were this artifact's
  own fault: detector H flagged the close-out section, which asserted PASS
  with its evidence inline rather than in a fenced block. That failed
  `python3 gates.py` and its mirror test,
  `test_gates.TestEvidenceHonesty.test_repo_verification_artifacts_are_honest`,
  plus `TestMainSummary.test_a_clean_run_ends_with_the_exact_summary_line`.
  The section now has a fenced block. The third failure was
  `test_trigger_eval_run_eval.FakeClaudeTest.test_counts_every_run_and_scores_per_case`
  (`{'none': 2} != {'idea': 2}`), which ran while the host's load average
  was 54.26, and it is a second load-sensitive test besides the one
  Implement logged. The diff changes no Python, so it is recorded here,
  not fixed. After the fix:
  ```
  10:27  load averages: 33.35 41.59 44.39
  gates: 0 problem(s)
  selftest: ok
  lint: 0 problem(s) across 25 skills
  Ran 1958 tests in 31.804s
  OK
  $ python3 -m unittest tests.test_trigger_eval_run_eval
  OK
  ```
