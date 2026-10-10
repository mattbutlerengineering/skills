---
stage: verify
run: feature:pocock-1-3-takeaways
date: 2026-10-06
assumptions:
  - "No live interview: the soft gate was read from breakdown.md (fourteen rows, all checked) and the criteria list was built from PRD-0007's six Success criteria plus the breakdown Accept checks no PRD criterion already covers, without asking the user which subset to verify."
  - "The PRD's red-then-green check (run the new tests against the pre-rule commit, then the post-rule commit) was done by reconstructing each commit's protocol.py and test file into a scratch directory with git show, because the brief forbids moving HEAD; a checkout of either commit was not taken."
  - "The hand-off decision's facts about omp were re-read live with a read-only gh api fetch of oh-my-pi's docs/skills.md at its default branch (the brief forbids gh writes, not reads); the fetch is this stage's choice, the brief and the PRD ask only that both texts be read."
  - "The Environment-retrospective criterion's byte-identical description is read as Operate's line alone, as the PRD states it; automate's description also differs from origin/main, by the one semicolon the Strict-YAML criterion required, and that is recorded under criterion 1 rather than counted against criterion 3."
  - "origin/main is the locally fetched ref (661ffc7); no git fetch was run, so the version-number question Ship owns (0.3.0 or 0.3.1 by merge order) is read against that snapshot."
---

# Verification: Pocock 1.3 takeaways

## Summary

6 PASS, 0 FAIL across PRD-0007's six success criteria, plus one PASS for
the breakdown's close-out acceptance no PRD criterion covers (all rows
checked, one honest ledger row per row). The battery is green on Python
3.12 and 3.14, the manifest is current (the tree stays clean after
regeneration), nothing under `evals/` or `LEDGER.md` moved, and every
reworded description differs from `origin/main` by exactly one character.
Two things this stage could not check are listed under Not verified: the
routing eval (paid, out of scope) and a real strict YAML loader (none
installed; the rule is a substring test by design). Next stage: Review.

Worktree HEAD `482f1f1`, fifteen commits ahead of `origin/main` `661ffc7`;
interpreters `Python 3.14.6` (default) and `Python 3.12.13` (CI's).

## Criteria & evidence

### Strict-YAML descriptions

- Check: (a) a read-only script in the scratchpad walked every
  `skills/*/SKILL.md` through `protocol.read_frontmatter` and counted
  descriptions containing `: ` or ` #`, starting with a character in
  `protocol._YAML_INDICATORS`, or over `SKILL_DESCRIPTION_LIMIT`;
  (b) `git diff origin/main --word-diff=plain` on the six reworded
  description lines, and a count of which skills' description lines
  changed at all; (c) a throwaway skill seeded under a temp dir (not the
  repo) with each defective shape, passed to the public
  `protocol.skill_frontmatter_problems(tmp_root, slug)`; (d) the test
  module alone; (e) the same test module run against the pre-rule commit
  and the post-rule commit, each reconstructed with `git show` into a
  scratch tree, plus a check that the test file is identical at both.
- Evidence:
  ```
  $ python3 strict_yaml_scan.py .
  files scanned: 25
  descriptions missing: 0
  descriptions containing ': ': 0
  descriptions containing ' #': 0
  descriptions starting with a YAML indicator '-?:,[]{}#&*!|>\'"%@`': 0
  descriptions over 1024 chars: 0
  longest description: 949 chars

  $ for f in skills/*/SKILL.md changed vs origin/main: list those whose description: line is in the -U0 diff
  skills/audit/SKILL.md
  skills/automate/SKILL.md
  skills/deepen/SKILL.md
  skills/doctor/SKILL.md
  skills/pipeline-board/SKILL.md
  skills/work-queue/SKILL.md

  $ git diff origin/main --word-diff=plain -U0 -- skills/<slug>/SKILL.md | grep '^description:'   # changed words only
  == audit
  [-always:-]{+always;+}
  == automate
  [-Read-only:-]{+Read-only;+}
  == deepen
  [-source:-]{+source;+}
  == doctor
  [-honestly:-]{+honestly;+}
  == pipeline-board
  [-stage:-]{+stage;+}
  == work-queue
  [-merges:-]{+merges;+}

  $ python3 rule_fires.py . <scratchpad>      # throwaway skill under a temp dir, four descriptions in turn
  colon-space  -> ["skills/throwaway/SKILL.md description is not a bare YAML scalar: contains ': '"]
  space-hash   -> ["skills/throwaway/SKILL.md description is not a bare YAML scalar: contains ' #'"]
  double-quoted-> ["skills/throwaway/SKILL.md description is not a bare YAML scalar: contains ': '", 'skills/throwaway/SKILL.md description is not a bare YAML scalar: starts with \'"\'']
  clean        -> []

  $ python3 -m unittest tests.test_protocol_frontmatter
  Ran 20 tests in 0.014s
  OK

  $ git show 01ca2ff:protocol.py / 01ca2ff:tests/test_protocol_frontmatter.py -> scratch tree; python3 -m unittest tests.test_protocol_frontmatter
  commit 01ca2ff exit=1
  Ran 20 tests in 0.025s
  FAILED (failures=7)
  FAIL: test_description_containing_colon_space (...)
  FAIL: test_description_containing_space_hash (...)
  FAIL: test_description_starting_with_other_yaml_indicators (...) (indicator='[')
  FAIL: test_description_starting_with_other_yaml_indicators (...) (indicator='|')
  FAIL: test_description_starting_with_other_yaml_indicators (...) (indicator="'")
  FAIL: test_description_with_both_substrings_yields_both_in_order (...)
  FAIL: test_double_quoted_description_is_rejected (...)

  $ git show 436e46a:protocol.py / 436e46a:tests/test_protocol_frontmatter.py -> scratch tree; python3 -m unittest tests.test_protocol_frontmatter
  commit 436e46a exit=0
  Ran 20 tests in 0.045s
  OK

  $ git diff --stat 01ca2ff 436e46a -- tests/test_protocol_frontmatter.py
  (empty: the test file is byte-identical across the rule commit)

  $ grep -n '_YAML_INDICATORS\|SKILL_DESCRIPTION_LIMIT = ' protocol.py
  119:SKILL_DESCRIPTION_LIMIT = 1024
  125:_YAML_INDICATORS = "-?:,[]{}#&*!|>'\"%@`"
  147:           if description[0] in _YAML_INDICATORS else [])
  ```
- Result: PASS. Zero of twenty-five descriptions carry any of the three
  shapes or exceed the limit; exactly the six named skills changed, each by
  one colon becoming a semicolon, so every trigger phrase is intact; the
  rule fires on each shape with the exact strings the breakdown pinned and
  stays silent on a clean scalar; the seven new tests fail on the commit
  before the rule and pass on the commit that adds it, with the test file
  unchanged between them.

### Pull request body

- Check: section headings and positions in `docs/pipeline-protocol.md`;
  grep for the section's required content (visual, before-and-after, the
  fixed heading, `Door:`, `Blast radius:`, the two credits); grep each of
  the three pointer files for the section's name and read the pointer in
  context; compare the routine skeleton's first two lines with
  `origin/main` byte for byte; confirm `gates.py` (detector B) is unchanged
  and the section names no harness.
- Evidence:
  ```
  $ grep -n '^## ' docs/pipeline-protocol.md
  7:## Stage order
  12:## Runs and run directories
  63:## Artifacts are the state
  206:## Soft gating
  221:## Run scale
  229:## Artifact frontmatter
  247:## Pull request body
  288:## Harness neutrality

  $ grep -n -E 'smallest visual|Before-and-after|## Merge danger|Door:|Blast radius:|mattpocock|show-me|Horthy' docs/pipeline-protocol.md
  258:1. **The smallest visual that shows the change** — pseudocode for a
  263:2. **Before-and-after evidence** — the failing output or test before and
  270:   ## Merge danger
  272:   Door: <one-way or two-way> — <why>
  273:   Blast radius: <what breaks if the call is wrong>
  285:no text copied, from mattpocock/skills' `pr` skill (MIT, copyright Matt
  286:Pocock) and the visuals menu of Dex Horthy's `show-me` (Humanlayer).
  304:it. The literal borrowing, "call the Skill tool with X" (mattpocock/skills),

  $ sed -n 247,287p docs/pipeline-protocol.md | grep -n -i -E 'claude code|omp|plugin'
  (empty, grep exit=1: the section names no harness)

  $ grep -n 'Pull request body' skills/work-queue/SKILL.md skills/ship/SKILL.md skills/ship/TEMPLATE.md docs/factory/improvement-routine.md
  skills/work-queue/SKILL.md:88:5. The PR body follows the protocol's Pull request body section
  skills/ship/SKILL.md:32:     words of the protocol's Pull request body section, so `release.md`
  docs/factory/improvement-routine.md:163:<Door: and Blast radius: lines, per the protocol's Pull request body section>
  skills/ship/TEMPLATE.md:22:(the same call the PR body makes under the protocol's Pull request body

  $ sed -n 86,90p skills/work-queue/SKILL.md      # step 4's "Each agent's prompt must carry" list
  2. Its mirrored issue number, for `Closes #N` in the PR body.
  ...
  5. The PR body follows the protocol's Pull request body section
     (`../../docs/pipeline-protocol.md`), with item 2's `Closes #N` line
     and the work-order id citation detector B reads kept first.

  $ sed -n 29,33p skills/ship/SKILL.md            # under "3. **Pre-flight.**" (line 24)
     - The rollback plan exists and is concrete: the actual commands or steps
       to undo this release, not "revert if needed". Beside the steps it
       records the door (one-way or two-way) and the blast radius in the
       words of the protocol's Pull request body section, so `release.md`
       and the PR body make the same call.

  $ sed -n 16,23p skills/ship/TEMPLATE.md
  ## Rollback plan

  Door: <one-way or two-way> — <why>

  Blast radius: <what breaks if the call is wrong>

  (the same call the PR body makes under the protocol's Pull request body
  section)

  $ grep -n '^<!-- improvement-routine -->' docs/factory/improvement-routine.md
  151:<!-- improvement-routine -->
  $ sed -n 151,152p docs/factory/improvement-routine.md
  <!-- improvement-routine -->
  No work order: daily improvement routine — <one-line reason>
  $ git show origin/main:docs/factory/improvement-routine.md | sed -n 151,152p
  <!-- improvement-routine -->
  No work order: daily improvement routine — <one-line reason>
  $ cmp <worktree lines 151-152> <origin/main lines 151-152>
  byte-identical

  $ sed -n 156,166p docs/factory/improvement-routine.md
  ## What / why
  <the signal that selected this work, and the change>

  ## Verification
  <verify-suite result; the test that failed first>

  ## Merge danger
  <Door: and Blast radius: lines, per the protocol's Pull request body section>

  ## Daily report
  <the §7 sections: Health, Queue, Reflect, Proposals>

  $ git diff --stat origin/main -- gates.py
  (empty: detector B is unchanged)
  ```
- Result: PASS. The section sits between Artifact frontmatter and Harness
  neutrality, carries the three parts and the one fixed heading with both
  fields, credits both sources, and names no harness; all three writers
  point at it by name and restate nothing; the skeleton's first two lines
  are byte-identical to `origin/main` and `## Merge danger` sits between
  `## Verification` and `## Daily report`. One wording note for Review,
  already in the breakdown's Notes: the section places the merge reviewer
  at gate 3 (ADR-0033's numbering) where the PRD and architecture say gate
  2; the upstream artifacts were left as written.

### Environment retrospective

- Check: grep Operate's numbered steps and the class words; grep the
  template's headings, table header and absent-section note; grep
  automate's surface table; `git diff origin/main` on every
  `docs/**/retro.md` and on Operate's `description:` line; read Operate's
  exact diff to confirm the insert and renumbering left steps 7 and 8's
  text alone.
- Evidence:
  ```
  $ grep -n '^[0-9]\. \*\*' skills/operate/SKILL.md
  17:2. **Soft gate.** Predecessor artifact: `release.md`. If missing, apply soft
  20:3. **Let it breathe.** If the release just happened, say so and offer to
  24:4. **Capture outcomes.** Against `prd.md`'s success criteria and `idea.md`'s
  30:5. **Retrospect on the run itself.** Walk the stages: where did the pipeline
  35:6. **Retrospect on the environment.** The run's own record of its
  50:7. **Seed the next runs.** Every gap, complaint, and "next time" becomes a
  59:8. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)

  $ grep -n -E 'mechanical|judgement' skills/operate/SKILL.md
  38:   rule that would have caught it, and classify it: **mechanical** (a
  40:   job, a gate detector) or **judgement** (only a reader could — a
  42:   mechanical mistake gets a check, never a prose rule; a prose rule is

  $ git diff origin/main -U0 -- skills/operate/SKILL.md | grep '^[-+]' | grep -v '^[-+][-+]'
  -6. **Seed the next runs.** Every gap, complaint, and "next time" becomes a
  +6. **Retrospect on the environment.** The run's own record of its
  +   mistakes is `verification.md`'s failures, `review.md`'s findings and
  +   `breakdown.md`'s Notes. For each mistake, name the check, pointer or
  +   rule that would have caught it, and classify it: **mechanical** (a
  +   deterministic check would have caught it — a lint rule, a hook, a CI
  +   job, a gate detector) or **judgement** (only a reader could — a
  +   `CLAUDE.md` or `AGENTS.md` line, or a standards statement). A
  +   mechanical mistake gets a check, never a prose rule; a prose rule is
  +   what the mistake already slipped past. Propose the carrier as an
  +   existing thing — the checker, detector, hook, job or file that would
  +   hold it. A repo with no guardrail at all (no hook and no CI job
  +   running its own check command) is itself a finding, not a neutral
  +   default. The structure restates the `retro` skill in mattpocock/skills
  +   (MIT, Matt Pocock); the words are this pipeline's.
  +
  +7. **Seed the next runs.** Every gap, complaint, and "next time" becomes a
  -7. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
  +8. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)

  $ grep -n '^## ' skills/operate/TEMPLATE.md
  9:## Outcomes vs. intent
  16:## Run retrospective
  22:## Environment
  32:## Idea seeds
  36:## Run complete

  $ sed -n 24,28p skills/operate/TEMPLATE.md
  One row per mistake the run recorded, naming what in the environment
  would have caught it; a retro without this section reads as no
  environment findings, not as a defect.

  | Mistake | Evidence | Class | Proposed carrier |

  $ grep -n 'Environment' skills/automate/SKILL.md
  44:| Environment retrospectives | the `## Environment` section of every `docs/**/retro.md` — a mistake the run recorded, its evidence, its class (`mechanical` or `judgement`) and the carrier that would have caught it |

  $ git diff origin/main --stat -- 'docs/**/retro.md'
  (empty)
  $ ls docs/features/*/retro.md docs/fixes/*/retro.md docs/retro.md | wc -l
         8

  $ git diff origin/main -U0 -- skills/operate/SKILL.md | grep '^[-+]description:'
  (empty, grep exit=1: Operate's description line is byte-identical)

  $ per-file count of description: lines in the -U0 diff vs origin/main
  skills/operate/SKILL.md description lines in diff vs origin/main: 0
  skills/automate/SKILL.md description lines in diff vs origin/main: 2
  skills/next/SKILL.md description lines in diff vs origin/main: 0
  skills/ship/SKILL.md description lines in diff vs origin/main: 0
  ```
- Result: PASS. Step 6 follows step 5 and the old 6 and 7 are now 7 and 8
  with their text unchanged (the diff touches only the step numbers); the
  template's `## Environment` sits between `## Run retrospective` and
  `## Idea seeds` with the four-column header and the absent-section
  note; automate's table has the row; the eight existing retros are
  untouched; Operate's description is byte-identical. Automate's
  description does differ from `origin/main`, by the one semicolon
  criterion 1 required (its evidence above); the PRD pins Operate's line
  here, and that is what this verdict rests on.

### Hand-off decision

- Check: read `next` step 5 and the protocol's Harness neutrality
  paragraph; `git diff origin/main` on `skills/next/SKILL.md` restricted to
  the eleven hand-off list lines (expect no change) and in full; grep the
  protocol for what the decision says was checked; re-read omp's
  `docs/skills.md` live (read-only `gh api`) for the two facts the decision
  cites and for any model-callable skill tool.
- Evidence:
  ```
  $ sed -n 36,52p skills/next/SKILL.md
  5. **Hand off.** Load the matching stage skill through the harness's
     skill-loading mechanism (a skill tool where one exists, otherwise a read
     of the skill file) and follow it; naming the skill in prose does not
     load it.
     - capture → the `capture` skill (maintenance runs only)
     - idea → the `idea` skill
     - prd → the `prd` skill
     - ux-design → the `ux-design` skill
     - architect → the `architect` skill
     - decompose → the `decompose` skill
     - implement → the `implement` skill
     - verify → the `verify` skill
     - review → the `review` skill
     - ship → the `ship` skill
     - operate → the `operate` skill

     Also mention the direct-entry alternative ("or jump anywhere: any stage

  $ git diff origin/main -U0 -- skills/next/SKILL.md | grep -c '^[-+]\s*- [a-z-]* → the'
  0
  $ grep -c '^  *- [a-z-]* → the `[a-z-]*` skill' skills/next/SKILL.md
  11

  $ git diff origin/main -U0 -- skills/next/SKILL.md | grep '^[-+]' | grep -v '^[-+][-+]'
  -5. **Hand off.** Invoke the matching stage skill and follow it:
  +5. **Hand off.** Load the matching stage skill through the harness's
  +   skill-loading mechanism (a skill tool where one exists, otherwise a read
  +   of the skill file) and follow it; naming the skill in prose does not
  +   load it.

  $ grep -n -E 'checked against omp|skill://|vs custom tools|no skill tool|adopted with neutral wording|applies ADR-0027' docs/pipeline-protocol.md
  305:was checked against omp on 2026-10-06 and adopted with neutral wording
  307:content read via its `read` tool against `skill://` paths, and its "Skills
  308:vs custom tools" section separates skill content from model-callable tool
  309:APIs, so omp has no skill tool and the literal wording fails one of the two
  311:the neutral sentence. This applies ADR-0027 rather than amending it; no new

  $ gh api repos/can1357/oh-my-pi/contents/docs/skills.md -H 'Accept: application/vnd.github.raw'   # read-only; 250 lines
  $ sed -n 1,8p omp-skills.md
  # Skills

  Skills are file-backed capability packs discovered at startup and exposed to the model as:

  - lightweight metadata in the system prompt (name + description)
  - on-demand content via the `read` tool against `skill://...`
  - optional interactive `/skill:<name>` commands
  $ sed -n 234,237p omp-skills.md
  ### Skills vs custom tools

  - **Skills**: documentation/workflow content loaded through prompt context and `read`
  - **Custom tools**: executable tool APIs callable by the model with schemas and runtime side effects
  $ grep -n -i -E 'skill tool|invoke_skill|use_skill|Skill\(' omp-skills.md
  (empty, grep exit=1: no model-callable skill tool is documented)
  ```
- Result: PASS. The protocol records adopt-with-neutral-wording, its
  reason, and what was checked (omp's `docs/skills.md`: skills are read via
  the `read` tool against `skill://`, and the Skills vs custom tools
  section separates skill content from callable tool APIs); omp's live
  document says exactly that and documents no skill tool; `next` step 5's
  lead sentence is the architecture's neutral wording verbatim and the
  diff touches no other line of the file, so the eleven list lines
  `lint.check_router` reads are unchanged.

### Small borrowings

- Check: grep the three skills for `GLOSSARY.md`; confirm this repo's own
  glossary is still `CONTEXT.md` (not renamed); grep the work-queue worker
  brief for the base-check and tip-merge rules and read step 4's list.
- Evidence:
  ```
  $ grep -n 'GLOSSARY.md' skills/deepen/SKILL.md skills/audit/SKILL.md skills/automate/SKILL.md
  skills/automate/SKILL.md:37:| Agent instructions | `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `CONTEXT.md`, `GLOSSARY.md` |
  skills/deepen/SKILL.md:29:- **The domain glossary** — `CONTEXT.md` or `GLOSSARY.md`, or whatever the
  skills/audit/SKILL.md:30:- `README`, `CLAUDE.md`/`AGENTS.md`, `CONTEXT.md`/`GLOSSARY.md`, contributing

  $ ls CONTEXT.md GLOSSARY.md
  ls: GLOSSARY.md: No such file or directory
  CONTEXT.md

  $ grep -n 'default-branch tip' skills/work-queue/SKILL.md
  91:6. Confirm the branch base is the default-branch tip before writing
  93:7. Merge or rebase the default-branch tip into the branch before declaring

  $ sed -n 79,95p skills/work-queue/SKILL.md
  Each agent's prompt must carry:

  1. The work order id, its breakdown row, and its `Accept:` criteria — the
     row is the scope, and anything outside it belongs to another order.
  2. Its mirrored issue number, for `Closes #N` in the PR body.
  3. The repo's own conventions: write the failing test first, then the
     implementation; `make check` must pass before it declares itself done.
  4. Its dollar budget from the plan, and the ADR-0034 rule that exhausting
     it means stopping and handing off, never quietly continuing.
  5. The PR body follows the protocol's Pull request body section
     (`../../docs/pipeline-protocol.md`), with item 2's `Closes #N` line
     and the work-order id citation detector B reads kept first.
  6. Confirm the branch base is the default-branch tip before writing
     anything, and reset onto that tip if it is not.
  7. Merge or rebase the default-branch tip into the branch before declaring
     done, so the merge fast-forwards.
  8. **Open a PR and stop.** Do not merge. Do not approve. Do not apply
  ```
- Result: PASS. All three skills name `GLOSSARY.md` beside `CONTEXT.md`
  where they read a target repo's vocabulary, this repo's own file is
  unrenamed, and the worker brief carries both rules as items 6 and 7 with
  the earlier items (scope, `Closes #N`, test-first and `make check`,
  budget) and the closing open-a-PR-and-stop item intact.

### Battery and packaging

- Check: the full battery from the worktree root on both interpreters,
  each output written to a scratch file and grepped; `python3
  factory_init.py update-manifest` followed by `git status --short`
  (the manifest must already be current); the plugin and manifest version
  fields against `origin/main`; `git diff --stat origin/main` on `evals/`
  and `LEDGER.md`; the payload mirror against the root seam; the two
  callers of the rule unchanged.
- Evidence:
  ```
  $ python3 --version; python3.12 --version
  Python 3.14.6
  Python 3.12.13

  $ python3 -m unittest discover tests > unittest-314.txt 2>&1; echo "exit=$?"; grep -E '^(Ran |OK|FAILED)' unittest-314.txt
  exit=0
  Ran 1800 tests in 23.821s
  OK

  $ python3.12 -m unittest discover tests > unittest-312.txt 2>&1; echo "exit=$?"; grep -E '^(Ran |OK|FAILED)' unittest-312.txt
  exit=0
  Ran 1800 tests in 19.996s
  OK

  $ python3 lint.py > lint.txt 2>&1; echo "exit=$?"; grep -E '^lint:' lint.txt
  exit=0
  lint: 0 problem(s) across 25 skills

  $ (python3 gates.py && python3 gates.py --selftest) > gates.txt 2>&1; echo "exit=$?"; grep -E '^(gates:|selftest:)' gates.txt
  exit=0
  gates: 0 problem(s)
  selftest: ok

  $ python3 factory_init.py update-manifest; echo "exit=$?"
  factory-init: 0 problem(s)
  exit=0
  $ git status --short
  (empty: the committed manifest was already current)

  $ grep version .claude-plugin/plugin.json
    "version": "0.3.0",
  $ git show origin/main:.claude-plugin/plugin.json | grep version
    "version": "0.2.0",
  $ grep -n '"version"' factory/manifest.json
  3:  "version": "0.3.0",

  $ git diff --stat origin/main -- evals/ LEDGER.md
  (empty)

  $ git diff --stat origin/main -- factory/
   factory/manifest.json                       |  4 ++--
   factory/templates/tools/factory/protocol.py | 36 +++++++++++++++++++++++++----
   2 files changed, 33 insertions(+), 7 deletions(-)
  $ cmp protocol.py factory/templates/tools/factory/protocol.py && echo identical
  identical
  $ git diff --stat origin/main -- lint.py trigger_eval.py
  (empty: both callers of skill_frontmatter_problems are unchanged)
  ```
- Result: PASS. 1800 tests `OK` on both interpreters, `lint: 0
  problem(s)`, `gates: 0 problem(s)`, `selftest: ok`; regenerating the
  manifest changes nothing, so the committed manifest matches the payload
  and detector E's view; the plugin is bumped 0.2.0 to 0.3.0 and the
  manifest carries 0.3.0 (origin/main is still 0.2.0, so the lean/polish
  branch has not landed first; Ship records the number); `evals/` and
  `LEDGER.md` are untouched; the payload mirror is byte-identical to the
  root seam and lint and the trigger-eval loader call it unchanged.

### Breakdown close-out (acceptance no PRD criterion covers)

- Check: every row checked; one honest ledger row per checked row, as the
  breakdown's Notes commit to (detector G reads a checked row as a merged
  work order owed a cost line).
- Evidence:
  ```
  $ grep -c '^- \[x\]' docs/features/pocock-1-3-takeaways/breakdown.md; grep -c '^- \[ \]' docs/features/pocock-1-3-takeaways/breakdown.md
  14
  0

  $ git diff origin/main -- docs/factory/costs.jsonl | grep -c '^+{'
  14
  $ ... | python3 -c 'rows=[json.loads(l[1:]) ...]; print(sorted(run_id)); print({(tokens, cost, outcome)})'
  ['session-2026-10-06-wo-0077', 'session-2026-10-06-wo-0078', 'session-2026-10-06-wo-0079', 'session-2026-10-06-wo-0080', 'session-2026-10-06-wo-0081', 'session-2026-10-06-wo-0082', 'session-2026-10-06-wo-0083', 'session-2026-10-06-wo-0084', 'session-2026-10-06-wo-0085', 'session-2026-10-06-wo-0086', 'session-2026-10-06-wo-0087', 'session-2026-10-06-wo-0088', 'session-2026-10-06-wo-0089', 'session-2026-10-06-wo-0090']
  {(0, 0.0, 'owner-session:unmetered')}
  ```
- Result: PASS. Fourteen of fourteen rows are checked and fourteen `$0`
  owner-session ledger rows were appended, one per row from 0077 to 0090,
  which is why `gates: 0 problem(s)` holds with detector G in the set.

## Failures

None.

## Not verified

- **The routing eval.** `python3 trigger_eval.py` was not run: it drives
  the `claude` CLI and costs money, and the brief and PRD-0007 put paid
  evals out of scope. The six reworded descriptions therefore have no
  fresh trigger evidence; the word-diff above shows each changed by one
  punctuation character, which is the whole basis for "every trigger
  phrase survives". The exposure surfaces at the next on-demand eval run.
- **A real strict YAML loader.** No third-party YAML parser is installed
  (the repo is stdlib-only), so the twenty-five descriptions were not
  checked by an actual strict loader. The rule is the three substring
  tests the architecture chose; this stage verified those tests, not a
  parser's acceptance.
- **Detector B on a live pull request event.** B skips locally without a
  PR event payload; its selftest ran (`selftest: ok`) and `gates.py` is
  unchanged against `origin/main`, which is how "no existing PR goes red"
  was established. A real PR body carrying `## Merge danger` was not
  checked against B because this run opens no PR.
- **`charter_replay.py`** was not run, for the same cost reason as the
  routing eval and because nothing in this run touches a role charter.
- **omp's text at a pinned tag.** The live read of omp's `docs/skills.md`
  was from its default branch on 2026-10-06, the same day Architect read
  it; a tag-pinned read was not attempted.
