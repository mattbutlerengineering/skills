---
stage: review
run: feature:docs-audit
date: 2026-10-10
assumptions:
  - "No live severity arbitration: the skill's draft-then-arbitrate loop ran without the user, so the severities below are this stage's ranking. A false checkable claim left in a doc the run declared clean is ranked major, because PRD-0010's whole deliverable is that every checkable claim is true; a passage that is imprecise or ambiguous but not falsified by the tree is ranked minor. Per the orchestrator's instruction and the skill's default, majors were fixed on the branch (each a one-line, in-place doc edit inside PRD-0010's file list, recorded as a claims.md row) and minors deferred with a reason."
  - "docs/standards.json was read (four MUST statements: adr0004, adr0032, eval-honesty, stdlib-only). The diff adds no typed id, creates no tracker issue, changes no Python and edits no maturity cell, so no finding cites a statement."
  - "Coverage sampling was delegated to two read-only subagents (one on README.md and docs/pipeline-protocol.md, one on the four routine playbooks, docs/output-evals.md and LEDGER.md). Every finding they reported was re-read against the tree by this stage before being recorded; one of their incidental notes (a doubled sys.exit in sweeps.py) did not reproduce and is not recorded."
  - "The review corrections were made on the branch rather than routed back to Implement: each is a single in-place sentence in an in-scope doc, with an original Check that fails on the base text and a new Check that passes on the tip, which is the Implement contract applied to four more rows."
---

# Review: documentation audit

## Scope

`git diff feat/grok-harness...HEAD` at `7a80375` (base `a0f7553`, the
seventeen run commits `f2c510b..7a80375`): the in-place edits to
`AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `docs/setup.md` and
`evals/README.md`, the eleven appended rows in `docs/factory/costs.jsonl`,
and the run directory. Each doc edit was re-checked against the code
directly, not through `claims.md`:

- `CLAUDE.md`/`AGENTS.md` "CI runs all three": `validator.yml` runs
  `make check` on push and pull_request; the Makefile `check:` target is
  lint, gates, gates --selftest, unittest.
- `AGENTS.md` resync: the text above the Beads markers is byte-identical
  to `CLAUDE.md`'s; the diff's three hunks (lines 8, 24, 36 on the base)
  all sit above `BEGIN BEADS`, so both Beads blocks are untouched (they
  still differ from each other, as they did on the base). The synced
  claims were re-derived: `cli.read_file` exists (ADR-0075 present);
  `human_gates.py` and `plane_drift.py` exist with ADR-0056/0060;
  an AST import scan over the 18 mirrored `.py` tools confirms "mirrored
  iff a payload tool imports it" for every seam module (`eval_schema`
  and `plane_drift` are imported by no payload tool and are not mirrored;
  the other six are both); `charter_replay.py --control` and the
  `## Must never` deletion exist.
- `CONTEXT.md` Harness: of the twelve stage/router skills none names a
  harness; only `automate` (a utility) names Claude Code. Charter: nine
  roles in `factory/charters/`, nine `factory/agents/factory-<role>.md`
  stubs, `factory/CHARTERS.md` present.
- `docs/setup.md` labels: `gates.declared_labels` returns exactly 13
  (assembler 6, `human_gates.gate_labels()` 5, Makefile adds
  `wo:in-progress` and `wo:failed`), matching the new composition; the
  old "six gate labels" was six slots over five distinct labels. The
  credential line: both the root and the template `assembler.yml` gate
  the agent step on `ANTHROPIC_API_KEY != '' || CLAUDE_CODE_OAUTH_TOKEN
  != ''`. The unchanged stamp table re-derived too: 77 copies,
  38-file manifest, group counts 39/18/8/6/3/2/1, 28 labels.
- `evals/README.md`: `eval_schema.results_path` has a `charter` kind
  named `charter-<date>[-N].json`; two such files exist; the module
  docstring calls them factory evidence.

Coverage sampling (the brief's third focus): README.md,
pipeline-protocol.md, the four routine playbooks, docs/output-evals.md
and LEDGER.md were read claim by claim against the tree (roughly 200
claims beyond the edited hunks).

Battery on the review tip (`6e2a6a3`, after the fixes):

```
$ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
Ran 1958 tests in 25.479s
OK
$ python3 lint.py
lint: 0 problem(s) across 25 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

The Verify re-run script quoted in `claims.md`, run unchanged on the
review tip: 452 rows, 447 re-checked (431 true, 16 corrected), 0
failed, the same five follow-up rows excluded (`claims.md` § Review
additions).

## Findings

### Major: README's omp install command points at a directory that does not exist

- Scenario: README.md line 35 (base) gives `git clone
  https://github.com/mattbutlerengineering/skills` then `omp --skill
  ./skills/next` with no `cd`. The clone lands in `./skills/`, so
  `./skills/next` is `<clone>/next`; the skill is `<clone>/skills/next`.
  Simulated by copying the tree into a scratch `skills/skills/`: `ls -d
  ./skills/next` → `No such file or directory`. Row README-10 had
  recorded it `true` because its Check (`ls -d skills/next`) ran from
  inside the repo, not from where the README leaves the reader.
- Standard: none
- Decision: fixed in `6e2a6a3` — `omp --skill ./skills/skills/next`;
  README-10 re-verdicted `false` → `corrected`, with a Check that
  resolves the path from the clone root.

### Major: improvement-routine.md says the PR skeleton's first two lines satisfy detector B

- Scenario: lines 147-148 (base) say "the first two lines satisfy
  detector B's traceability contract"; those lines are the
  `<!-- improvement-routine -->` marker and the `No work order:` waiver.
  `gates.check_pr_traceability` also requires `Closes #N` "regardless"
  of the waiver, so a routine that trims the skeleton to what the
  sentence says is load-bearing fails B. The sibling playbooks
  (queue-groomer, doc-gardener) state the rule correctly.
- Standard: none
- Decision: fixed in `6e2a6a3` — now names the `No work order:` line and
  the `Closes #` line together; row ROUT-IMPR-36.

### Major: output-evals.md says `results_path` owns the grammar "for both results kinds"

- Scenario: lines 52-53 (base); `eval_schema.results_path` branches on
  three kinds (`trigger`, `charter`, `output`) and two `charter-*`
  results exist. Same class as the EVALS-11 correction this run already
  made in `evals/README.md`, missed in its sibling doc.
- Standard: none
- Decision: fixed in `6e2a6a3` — "for every results kind (trigger,
  output, charter)"; row OEVAL-19.

### Major: README says the unittest suite runs "all against fixture trees"

- Scenario: README.md line 117 (base). `tests/test_lint.py` calls
  `lint.check_router(ROOT)` on the real repo; `tests/test_budget_guard.py`
  checks the real `factory.json`; `tests/test_factory_init.py` compares
  the real root Makefile and CODEOWNERS with the payload. A contributor
  who trusts "all" expects a doc or config edit cannot turn the suite
  red, and it can.
- Standard: none
- Decision: fixed in `6e2a6a3` — "mostly against fixture trees plus pins
  on the real repo"; row README-38.

### Minor: doc-gardener-routine.md's drifted-index examples are partly held already

- Scenario: lines 74-78 name `factory/CHARTERS.md`'s table and the plugin
  description's skill list as unheld hand-kept lists, but
  `tests/test_factory_charters.py` pins CHARTERS.md's role, path and band
  columns and `lint.check_plugin_skills` holds the plugin description's
  utility-skill names. The sentence is qualified ("wherever no detector
  already holds the list to its source"), and the Owns column and the
  stage-name prose are genuinely unheld, so the routine is pointed at
  real residue; nothing is falsified.
- Standard: none
- Decision: deferred — imprecise rather than false; the precise carve-out
  (which columns, which checker) is the doc-gardener playbook's own
  tuning, by PR, outside this audit's falsification bar.

### Minor: LEDGER.md narrative gives operate-situational-1's pre-change score as 0/5

- Scenario: lines 64-65 say "was 0/5"; the only recorded pre-change
  result, `trigger-2026-07-01.json`, has it at 1/3 (`{'none': 2,
  'operate': 1}`). The honesty policy's 5-run rerun may have happened
  without `--record`, so the tree cannot rule out an unrecorded 0/5.
- Standard: eval-honesty (advisory relevance only — no evidence is
  fabricated either way)
- Decision: deferred — not falsifiable from the tree alone, and LEDGER
  eval narrative is evidence prose; it belongs to the same ledger pass
  F-3 already proposes, which can cite or correct it.

### Minor: the protocol's Work-already-in-flight section names capture's check narrower than capture runs it

- Scenario: `docs/pipeline-protocol.md` 36-37 says the check happens at
  "`capture` claiming a seed or seeding from tracker intake";
  `skills/capture/SKILL.md` step 3 runs it before every `defect.md`. The
  enumeration is not stated as exclusive, so the protocol is not
  contradicted, only incomplete.
- Standard: none
- Decision: deferred — not false, and the protocol is normative for the
  skills; widening the sentence is better done in a protocol pass than
  slipped in by a review fix.

### Minor: README's omp fallback "copy `skills/*`" has the same cwd ambiguity

- Scenario: line 38-39 sits under the same clone with no `cd`; read from
  the clone's parent, `skills/*` is the repo root. Read from inside the
  clone (the natural reading of a fallback) it is correct.
- Standard: none
- Decision: deferred — ambiguous rather than false; the corrected command
  two lines above now shows the clone-relative path.

### Minor: `docs/factory/costs.jsonl` is a literal deviation from PRD-0010's file list

- Scenario: "In place, in scope" lists the files the diff may touch and
  omits the ledger, while detector G fails a checked breakdown row with
  no ledger line. Judged: the exception is sound. The diff on the ledger
  is append-only (`grep -c '^+{'` 11, no other changed line), each row is
  an honest `owner-session:unmetered` zero, it matches the precedent of
  readme-skill-map and pocock-1-3-takeaways, and breakdown assumption 3
  recorded it before Implement rather than after. The gap is in PRD-0010's
  drafting, which should have named the ledger.
- Standard: none
- Decision: deferred — no change to the branch; the owner can reverse it
  at merge, as the assumption says.

### Follow-ups F-1..F-4: correctly characterized

Re-checked, no finding. F-1: `gates._scannable_files` yields no path
under `evals/` (re-run: `[]`); a checker edit is outside PRD-0010's diff.
F-2: a parity check is likewise code. F-3: LEDGER defines **draft** as
"never exercised" and the tree shows capture/autorun/ux-design artifacts
in real runs; maturity moves only by recorded graduation, so a follow-up
is right. F-4: whether utility skills may read and append the backlog is
a contract choice, correctly not made by an audit. None of the four is a
safe in-scope doc correction, and none of the four major findings above
should have been a follow-up.

## Passes with no findings

- **Correctness of the run's own edits**: all twelve corrected passages
  hold against the code; no correction introduced a new inaccuracy or
  changed meaning beyond its claim. (The four majors are missed claims in
  untouched passages, a coverage failure, not edit errors.)
- **Design**: the diff follows `architecture.md` — in-place edits only,
  no file moved or deleted, no protocol hunk, no ADR, skill, template or
  backlog edit, no mirrored file touched (no manifest regeneration
  owed), Beads blocks untouched.
- **Security**: documentation only; no secrets, no executable change. The
  one security-adjacent sentence (setup.md's credential gate) was checked
  against both `assembler.yml` copies and is accurate.

## Verdict

Ready to ship. No critical finding; the four majors were fixed on the
branch in `6e2a6a3` with claims.md rows, and the battery and the Verify
re-run are green on the fix. Five minors are deferred with reasons above.
Note for Ship and the owner: the coverage miss rate in the sample
(four false claims across docs recorded as clean) means "every checkable
claim is true" holds for the inventoried claims, not provably for every
sentence; `verification.md` already lists extraction completeness as not
verified.
