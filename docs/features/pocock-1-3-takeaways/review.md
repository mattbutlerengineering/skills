---
stage: review
run: feature:pocock-1-3-takeaways
date: 2026-10-06
assumptions:
  - "No live severity arbitration: the skill's draft-then-arbitrate loop (steps 4 to 6) ran without the user, so the severities below are this stage's ranking against the brief's scale (critical means wrong behaviour, a lie in an artifact, or a broken contract), and every finding is left as a proposal for the orchestrator to route; nothing was fixed here."
  - "One check was added beyond Verify's list: every skills/*/SKILL.md frontmatter block was parsed with Ruby's Psych (libyaml), already present on this machine and outside the repo, as the real strict loader Verify listed under Not verified. It is review evidence only, not a repo dependency; the stdlib-only rule is untouched."
  - "docs/standards.json was read (four statements, all advisory); none matches a finding, so each finding cites none."
  - "origin/main is the locally fetched ref 661ffc7, as in Verify; no git fetch was run."
---

# Review: Pocock 1.3 takeaways

## Scope

The whole branch against `origin/main` (`661ffc7`): sixteen commits,
`9129d61..bd2a87d`, 25 files, +1799/-29. Deliverables examined line by
line: `protocol.py` and its payload mirror (the bare-scalar rule),
`tests/test_protocol_frontmatter.py`, the six reworded descriptions,
`docs/pipeline-protocol.md` (the Pull request body section and the
Harness neutrality paragraph), the three PR-body pointers (work-queue
step 4, ship step 3 and its template, the routine's section 5 skeleton),
operate step 6 and its template, automate's table row, the `next`
lead sentence, the glossary alias in audit/deepen/automate, work-queue
items 6 and 7, `plugin.json`, `factory/manifest.json`, and the fourteen
ledger rows. Run artifacts (`idea.md`, `prd.md`, `architecture.md`,
`breakdown.md`, `verification.md`) were read for process honesty.

Checks run from the worktree at `bd2a87d`, outputs in the session
scratchpad:

```
$ python3 -m unittest discover tests     -> Ran 1800 tests ... OK
$ python3 lint.py                        -> lint: 0 problem(s) across 25 skills
$ python3 gates.py && python3 gates.py --selftest
                                         -> gates: 0 problem(s) / selftest: ok
$ cmp protocol.py factory/templates/tools/factory/protocol.py -> identical

$ ruby psych_check.rb      # YAML.safe_load on each frontmatter block
  25/25 skills: psych ok, description is String,
  equal-to-plain-split=true (longest 949 chars)
$ ruby psych_edges.rb      # the shapes the rule does and does not name
  origin/main audit (colon-space)     => ERR mapping values are not allowed
  quoted phrase "audit this: now"     => ERR mapping values are not allowed
  trailing colon                      => ERR mapping values are not allowed
  tab before hash                     => OK  "Use when closing"   (truncated)
  colon then tab                      => ERR mapping values are not allowed
  leading dash then safe char ("-1 …")=> OK  String
  literal block, ": " in body         => OK  String, same value
  bare "true" / "1024"                => OK  TrueClass / Integer
```

Verify's scratch outputs (`red-green-01ca2ff.txt`, `unittest-312.txt`,
`unittest-314.txt`, `lint.txt`, `gates.txt`, `update-manifest.txt`,
`omp-skills.md`) were re-read and match what `verification.md` quotes.

## Findings

### Minor: the two-character tests use a literal space, so a tab after `:` or before `#` passes the rule while a strict loader does not read it as one scalar

- Scenario: `protocol.py:144-147` (and the identical payload mirror at
  the same lines) test `": " in description` and `" #" in description`.
  YAML's rule is colon or hash beside *white space*, which includes a
  tab. Through the public function, `description: Use when
  closing\t#12 today.` returns `[]`, and Psych reads the description as
  `"Use when closing"`, the rest dropped as a comment; `Read-only:\tit
  proposes.` also returns `[]` and Psych raises. Both are the exact
  divergence the rule exists to catch (the docstring's "a strict loader
  reads what the plain split read"). No description carries a tab today
  (`grep -P '^description:.*\t' skills/*/SKILL.md` is empty), and the
  architecture's decision list (`architecture.md:235`) names the trailing
  colon and block scalars as deliberately not special-cased but does not
  mention tabs, so this is an undocumented gap rather than a recorded
  trade-off. Fix shape: `re.search(r":\s", ...)` and `r"\s#"` in place
  of the two substring tests, or a fourth string `contains a tab`, each
  with an exact-string test in `TestSkillFrontmatterProblems`.
- Standard: none
- Decision: deferred — not ship-blocking: no current input reaches it
  and a tab in a one-line description is improbable. Proposed as a
  follow-up row or backlog seed; if Implement is re-entered for the two
  wording findings below, it is a two-line change to take with them.

### Minor: operate step 6 reproduces one of Pocock's sentences nearly verbatim while claiming "the words are this pipeline's"

- Scenario: `skills/operate/SKILL.md:45-47` reads "A repo with no
  guardrail at all (no hook and no CI job running its own check command)
  is itself a finding, not a neutral default." The `retro` source
  (`scratchpad/pocock/skills_engineering_retro_SKILL.md`, Automated
  checks bullet) reads "A repo with no guardrail (no pre-commit hook and
  no CI job running its lint/typecheck/test command) is itself a
  finding: an un-linted repo is a standing missed opportunity, not a
  neutral default." Roughly twenty of the sentence's words are shared in
  sequence. Line 48 then states "the words are this pipeline's". The
  credit (MIT, Matt Pocock) is present and the licence permits the
  reproduction, so this is not a licensing defect; it is a claim in
  shipped skill text that one sentence contradicts. The rest of step 6
  and the whole Pull request body section are genuine restatements
  (checked against both sources).
- Standard: none
- Decision: fix before ship (route to Implement) — one-sentence edit:
  either reword the guardrail sentence (for example "A repo whose check
  command runs nowhere — no hook, no CI job — is a finding in itself")
  or drop "the words are this pipeline's" and leave the credit. Either
  keeps operate's `description:` byte-identical and nothing in lint
  reads the sentence.

### Minor: work-queue item 7 promises a fast-forward the repo's merge path cannot deliver

- Scenario: `skills/work-queue/SKILL.md:93-94` tells each worker to
  merge or rebase the default-branch tip "so the merge fast-forwards".
  The same skill's gate-3 paragraph and the brief say the PR is
  squash-merged by a human, which never fast-forwards, and the Rules
  section says two orders in one batch may touch the same files with
  the conflict landing on the human at merge time; a worker that merged
  the tip when it finished is stale again as soon as a sibling PR lands.
  The rule itself (confirm the base, merge or rebase the tip before
  done) is a faithful restatement of `implement-spec`'s two worker
  rules and is right to add; the trailing clause overstates its effect.
  Item 6's "default-branch tip" also does not say whose tip (local
  `main` or `origin/main`); preflight makes them equal, so this is
  wording, not behaviour.
- Standard: none
- Decision: fix before ship (route to Implement) — drop the clause or
  replace it with "so the PR applies cleanly to the tip as of hand-off";
  optionally "the remote's default-branch tip" in items 6 and 7. The
  grep the row's Accept names (`default-branch tip` twice) still holds.

### Minor: three run artifacts place the merge reviewer at "gate 2 (ADR-0033)"; ADR-0033 numbers the PR merge gate 3

- Scenario: `prd.md:53` and `prd.md:165`, `architecture.md:144`, and
  `breakdown.md:38` and `breakdown.md:104` say gate 2. ADR-0033's
  Decision lists 1 PRD approval, 2 Blueprint/ADR approval, 3 PR merge;
  `skills/work-queue/SKILL.md` and the new protocol section
  (`docs/pipeline-protocol.md:249`) both say gate 3, so the shipped text
  is right and only the run's own artifacts carry the slip. The
  breakdown's final Note (lines 119-124) records the correction and the
  decision to leave the upstream artifacts as written; nothing was
  hidden. Ship's `release.md` and the PR body should cite gate 3.
- Standard: none
- Decision: deferred — already recorded where the protocol says
  corrections live (the breakdown's Notes); the slip sits in context
  prose under coverage waivers, not in a deliverable or a check. Ship
  reads this finding and cites gate 3.

### Minor: `architecture.md` says the `next` sentence names the skill-file path; it does not

- Scenario: `architecture.md:212-213` ("Failure modes: a harness with
  neither mechanism reads `skills/<stage>/SKILL.md` directly, which the
  sentence already names"). The sentence as shipped at
  `skills/next/SKILL.md:36-39` says "otherwise a read of the skill
  file" and names no path; the list beneath names skills, not files.
  On Claude Code (Skill tool) and omp (`read skill://<name>`) the
  sentence is sufficient and neutral, so the effect is confined to a
  hypothetical third harness and to the accuracy of one design claim.
- Standard: none
- Decision: deferred — adding "`../<stage>/SKILL.md`" to the sentence
  would make the claim true and is harmless to `HANDOFF_LINE`, but the
  sentence is pinned verbatim by row 0087's Accept; leave for the next
  edit of the router or correct the architecture line then.

### Nits (no decision owed)

- `skills/pipeline-board/SKILL.md:3`: of the six rewordings this is the
  one where `; ` joins a noun-phrase list to the clause before it
  ("...pipeline stage; swimlane rows per run, stage columns, ..."); the
  other five join independent clauses and read cleanly. An em dash,
  already used in the same line, would carry the appositive. Trigger
  phrases are intact in all six (the word-diff shows one character each).
- `tests/test_protocol_frontmatter.py:139-207`: every branch of the rule
  is asserted through the public function with exact strings, and
  two-at-once ordering is pinned; a three-at-once case (`"a: b #c`) and
  the limit-then-scalar ordering (an over-1024 description holding
  `: `) are not, though both follow from the tuple concatenation.
- `skills/operate/SKILL.md:36-38`: the mistake sources name
  `breakdown.md`'s Notes; a maintenance run re-entered at implement
  keeps its checkboxes in `defect.md` (`protocol._maintenance_breakdown`),
  so "or `defect.md` for a maintenance run" would spare the agent a
  guess.
- `skills/operate/TEMPLATE.md:22-30`: the section ships in the template
  by default while its note contemplates omission ("a retro without this
  section reads as no environment findings"); saying when to omit it (a
  run that recorded no mistakes) would remove the ambiguity. Prose notes
  in templates are an existing pattern (decompose, verify), so the note's
  presence is not itself a deviation.

### Pre-existing, not this run's

- `package.json:3` is `0.1.0` and has been since #89 (`717eb49`);
  `plugin.json` and `factory/manifest.json` agree at `0.3.0`, which is
  all `lint.check_manifest` pins. Flagged as drift for a separate chore.
- `python3 one_owner.py` reports six problems on this tree, every one in
  files this diff does not touch (`assembler.py`/`validator.py`/
  `work_queue.py`, `budget_guard.py`/`cost_report.py`, `dashboard.py`/
  `gate_digest.py`/`rejection_mining.py`, `eval_schema.py`/
  `trigger_eval.py`, `label_sync.py`/`sweeps.py`). It is a pre-pass, not
  a gate; noted so nobody reads them as new.

## Passes with no findings

- **Correctness of the rule on real input.** All twenty-five
  descriptions parse under Psych with the description equal to
  `read_frontmatter`'s plain split, which is the invariant
  `protocol.py:120-124` states; origin/main's `audit` line raises the
  "mapping values are not allowed" error the PRD predicts. A quoted
  trigger phrase carrying `: ` raises too, so rejecting it is right.
  Ordering is fixed by tuple concatenation; the never-raises contract
  holds because `read_frontmatter` yields only `str` or absent, and the
  empty-string guard covers an empty `|` block. The over-strict side is
  by design and safe: `-`, `?` and `:` followed by a safe character are
  valid YAML 1.2 plain scalars the indicator set rejects, and a `|`
  block body holding `: ` is rejected although valid (`architecture.md:
  235` records this and the trailing colon as not special-cased).
  Non-string plain scalars (`true`, `1024`) pass unnoticed; no
  description is one word.
- **Design.** The rule sits in the seam that owns frontmatter facts and
  both callers (`lint.check_skills`, `trigger_eval`'s loader) inherit it
  unchanged; the payload mirror is byte-identical and the manifest
  checksum moved with it. The protocol section is the one owner and the
  three pointers restate nothing; it names no harness; its account of
  detector B (`Closes #N` required; a work-order id or a reasoned `No
  work order:` line) matches `gates.check_pr_traceability` and
  `NO_WO_DECLARATION`, and the "kept first" convention is stricter than
  B, not contrary to it. The routine skeleton's first two lines are
  byte-identical. The Harness neutrality paragraph's omp facts match
  the saved `docs/skills.md` (skills exposed as `read` of `skill://`;
  "Skills vs custom tools" separates content from callable tools; no
  skill tool documented); the `next` sentence names neither harness and
  the eleven list lines are unchanged, so `check_router` reads the same
  list. Operate's recital obligations (soft-gate names `release.md`, body
  names `retro.md`, no "next stage is" claim) survive the renumbering;
  step 6's mechanical/judgement test ("would a deterministic check have
  caught it") is stated so an agent can apply it, and automate's row
  reads the same section by heading. Deepen, audit and automate read
  naturally with both glossary names and this repo's `CONTEXT.md` is
  unrenamed. Items 6 and 7 do not contradict "Never merge" (direction is
  explicit) or the preflight rule on open PRs. The fourteen `$0`
  owner-session rows follow the policy the breakdown cites
  (process-dashboard Note of 2026-08-13; codex-style-standards
  breakdown of 2026-09-21; ADR-0069 Context), field for field.
- **Security.** No new input surface: the rule reads the same file the
  reader already read, renders one character with `!r`, and writes
  nothing; no secrets in the diff; the ledger rows carry no tokens or
  identities beyond the model name.
- **Process honesty.** Every `assumptions:` entry in the five artifacts
  describes what the scratchpad shows happened (reconstructed trees for
  red-then-green, a live `gh api` read of omp with an empty `.err`,
  version bump at Implement). Every PASS in `verification.md` quotes
  literal output that matches its saved file; nothing is claimed that
  was not run, and the Not verified list is honest (the real-loader gap
  it names is closed above).

## Verdict

**Ready to ship: no critical findings, none unfixed.** Five minors and
four nits; two minors (operate's near-verbatim sentence under a "words
are this pipeline's" claim; work-queue's "so the merge fast-forwards")
are recommended as a one-sentence fix each before the PR opens, routed
to Implement — neither touches a `description:` line, a recital, or the
router list, so the battery stays green without a manifest change. The
tab gap in the rule and the two artifact inaccuracies are deferred with
reasons above. For Ship: cite ADR-0033 gate 3 in `release.md` and the PR
body; the version question (0.3.0 here, 0.3.1 if the lean/polish branch
lands first) is still Ship's to record; `package.json` drift is a
separate chore.
