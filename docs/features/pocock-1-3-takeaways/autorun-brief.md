# Autorun brief: pocock-1-3-takeaways

Not an artifact. Written 2026-10-06 by the orchestrator. The user's own
words in this run are three messages: "matt pocock 1.3 was released see
what we can take and learn from this", then `/idea-to-prod:decompose`,
then `/idea-to-prod:autorun` in reply to the question "Do you want this
written as drafted?". Everything below that is not quoted from those
messages is the orchestrator's reading of them plus the read-out the user
saw before approving, and is marked so where it matters.

## What and why

Adopt the lessons of mattpocock/skills v1.3.0 and v1.3.1 (both released
2026-10-04) that apply to this repo. Five borrowings, read out to the
user on 2026-10-06 and not objected to:

1. Skill descriptions must survive a strict YAML loader. Pocock's patch
   notes (#911) say six of his skills had an unquoted `description`
   containing a colon-space, invalid YAML, so `skills.sh` skipped them.
   Six of this repo's skills have the same shape today: audit, automate,
   deepen, doctor, pipeline-board, work-queue. Claude Code and omp use
   permissive parsers so they load; a strict loader would drop them.
   `protocol.read_frontmatter` is a plain `key: value` splitter that does
   not strip quotes, so quoting is not the fix; rewording is, plus a lint
   rule in `skill_frontmatter_problems` (protocol.py, ADR-0052) so it
   cannot recur.
2. A pull request body should say what the merge risks. Pocock's new `pr`
   skill: the smallest visual that shows the change, before/after
   evidence, and a merge-danger call (one-way or two-way door, blast
   radius). Credits Dex Horthy's `show-me`. This repo's work-queue workers
   open PRs with no body guidance beyond `Closes #N`; the human at gate 2
   is who a door call serves.
3. A retro should ask what in the agent's environment would have caught
   the session's mistakes. Pocock's `retro`: navigation pointers,
   automated checks, coding standards, steering files, tool economy,
   information access; a mechanical violation gets a deterministic check,
   only judgement calls go in a standards file. This repo's Operate retro
   judges the product and the pipeline stages, never the environment.
   `automate` is the nearest skill and demands friction evidence; a retro
   naming the mistake is that evidence.
4. Operative hand-offs should name the tool. Pocock (#878, #880): a skill
   naming another skill in prose does not reliably load it; this was his
   most-reported problem. His fix: "Call the Skill tool with X", and never
   for a user-invoked skill. This repo's `next` router step 5 names each
   stage skill in prose. Harness neutrality (protocol section, ADR-0027)
   requires checking omp before adopting.
5. Small borrowings: his glossary convention renamed `CONTEXT.md` to
   `GLOSSARY.md`; our deepen, audit and automate read a target repo's
   vocabulary under the old name only. His `implement-spec` workers
   confirm their branch base before writing and merge the integration tip
   before reporting done; this session had a detached-HEAD incident the
   first rule prevents.

Not borrowed (read out as "noted, not recommended now"): deleting skills
the model handles unaided (his `resolving-merge-conflicts`), marking
skills user-invoked with `disable-model-invocation`, the em-dash purge.

## Run scale and slug

Feature run, small. Slug `pocock-1-3-takeaways`. Run directory
`docs/features/pocock-1-3-takeaways/`. Artifacts scale down per the
protocol's Run scale section: a one-page PRD, an architecture note of a
few paragraphs. No new skill, no new seam module, no ADR unless the
Milestone 4 decision amends ADR-0027.

## Idea-stage inputs (orchestrator's reading)

- Problem, from the sufferer's view: a maintainer of this skills repo
  reads a peer skills repo's release and has no cheap way to know which
  of its lessons already apply here; the one that does is a silent
  loader incompatibility nothing here checks.
- Who has it, how they cope today: the repo owner; they cope by reading
  release notes by hand and asking an agent to compare. One such
  comparison produced this run.
- Why now: v1.3.0/v1.3.1 shipped two days ago; the YAML defect it names
  is live in six skills here today.
- Evidence the problem is real: six SKILL.md descriptions with unquoted
  colon-space (counted 2026-10-06 by script; anecdote count: one peer
  repo hit by the same defect in six skills). The other four borrowings
  are judgement, labelled as such.
- Rough solution shape: five small changes to existing skill and protocol
  text plus one lint rule; nothing new is built.
- Success in one sentence: a strict YAML loader sees every skill, and the
  four other lessons are either adopted in the skill text or rejected
  with a recorded reason.
- Biggest unknowns / ways this dies: (a) omp may have no model-callable
  skill tool, killing borrowing 4 (that is why it starts with a check);
  (b) rewording descriptions changes routing-eval trigger text, and the
  routing eval costs money so it will not be re-run in this run; (c) the
  manifest is also touched by three other unmerged branches.

## Scope

In: the five borrowings above, their tests, the payload mirror and
manifest regeneration, a plugin version bump. Out: new skills; running
`trigger_eval.py` or `charter_replay.py`; any change to `evals/`
definitions; LEDGER maturity changes; the lean/polish branch; the
guarded-read branch; GitHub issues or PRs.

## Success criteria

- No SKILL.md description contains an unquoted `: ` or ` #`, and a lint
  rule with tests rejects one.
- `docs/pipeline-protocol.md` has a pull-request-body section; work-queue,
  ship and the improvement routine's PR skeleton point at it.
- Operate has an environment-retrospective step and template section;
  automate lists retro Environment sections as a friction source.
- A recorded adopt-or-reject decision on tool-naming hand-offs, and `next`
  worded accordingly.
- deepen, audit, automate read `GLOSSARY.md` as well as `CONTEXT.md`;
  work-queue's worker brief carries the base-and-tip rules.
- Full battery green on Python 3.12 and 3.14: `python3 -m unittest
  discover tests`, `python3 lint.py` (`lint: 0 problem(s)`),
  `python3 gates.py && python3 gates.py --selftest`.

## Constraints and things already decided

- Repo hard conventions (CLAUDE.md): stdlib only; seam modules own their
  facts (protocol.py owns frontmatter checks); problem-string contracts
  with exact-string tests through public interfaces; after editing
  protocol.py run `python3 factory_init.py update-manifest` and include
  the manifest; skill bodies harness-neutral; eval honesty (never edit an
  eval definition, `evals/results/` append-only, no fabricated evidence).
- Tests first per work item, then the implementation.
- The approved breakdown draft (below) is the cut the user approved via
  `/autorun`. Decompose keeps it unless `architecture.md` contradicts a
  row; any change is logged in the breakdown's frontmatter assumptions.
- Design gap recommendations the user saw: the lint rule also rejects a
  quoted description (so the reader stays a plain splitter); the protocol
  section owns PR-body shape and the other two places point at it.
- Reword descriptions BEFORE the lint rule lands so every commit is green.
- Git: work only on branch `feat/pocock-1-3-takeaways` in this worktree.
  Never move HEAD (no checkout of other commits, no reset, no rebase).
  Local commits per work item, Conventional Commits, trailer
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. This local-
  commit permission is the orchestrator's reading of `/autorun` (the
  Implement skill commits at item boundaries), not the user's words. No
  push, no PR, no issue, no tag, no merge. The branch's upstream is
  `origin/main`; a bare `git push` would push to main. Never run it.
- Zsh traps in the Bash tool: unmatched globs abort the whole command;
  never name a variable `status`; never `echo` a string starting with
  `=`; write test output to a file and grep `Ran N tests` / `OK`.
- Detector C forbids work-order id tokens (the uppercase two-letter prefix, a hyphen, four digits) in `docs/features/**`
  documents; write "work-order id" in prose. Detector I reads markdown
  links inside fenced blocks. Run gates.py after writing run artifacts.
- Never `Closes` issues #178 or #181; they are permanent state.

## Tracker

No tracker seeding and no tracker export: no GitHub issue interaction at
all. The repo's `bd` tracker is not touched by stages either.

## User-facing surface

None. The deliverables are skill text, protocol text, one Python rule and
its tests. `ux: not-applicable`, reason: no UI surface.

## Release authorization

Prepare and stop. Release mechanism: a pull request to `main`, squash-
merged by a human (ADR-0033 gate 2); versioning is semver in
`.claude-plugin/plugin.json` (bump the patch or minor; `feat/lean-and-
polish-skills` already bumps to 0.3.0 uncommitted, so this run bumps to
0.3.1 if that lands first, else 0.3.0; Ship records which). Ship executes
no externally visible action.

## Work already in flight (checked 2026-10-06)

Eleven open PRs (#585, #589, #595, #596, #597, #598, #600, #602, #604,
#606, #608) read by title and branch; none does any of this work. PR #598
touches the decompose skill and #602 touches work_queue.py; neither
overlaps a row below. `docs/backlog.md` line 6 (is Pi's 1024 limit chars
or bytes) is adjacent to Milestone 1 and out of scope.

## Upstream sources

Release notes and the graduated skills were downloaded on 2026-10-06 to
the session scratchpad:
`/private/tmp/claude-501/-Users-mbutler-github-skills/ee622348-c85b-44f3-8ebf-f048e89ab1b3/scratchpad/pocock/`
(`v1.3.0.md`, `v1.3.1.md`, `skills_engineering_pr_SKILL.md`,
`skills_engineering_retro_SKILL.md`, `skills_engineering_implement-spec_SKILL.md`,
`.agents_invocation.md`, and others). Live source:
`gh api repos/mattpocock/skills/contents/<path>?ref=v1.3.1`.
Pocock's repo is MIT-licensed, copyright Matt Pocock; the `pr` skill's
Summary visuals are Dex Horthy's `show-me` (Humanlayer). Credit both when
the PR-body section borrows their structure; restate, do not copy text.

## Approved breakdown draft

# Breakdown: Pocock 1.3 takeaways

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met.

## Milestone 1: Every skill description survives a strict YAML loader

- [ ] **Reword the six colon descriptions** — audit, automate, deepen, doctor,
  pipeline-board, work-queue: remove each `: ` from the unquoted
  description without changing its trigger phrases.
  - Accept: no SKILL.md description contains `: ` or ` #`; each stays
    within the 1024-char limit; lint, gates and tests green.
  - Blocked by: —
- [ ] **Pin the rule with tests** — `tests/test_protocol_frontmatter.py`: a
  fixture skill whose unquoted description holds `: ` (and one holding
  ` #`, one starting with a YAML indicator such as `"`, `[`, `&`, `*`,
  `|`, `>`) yields one exact problem string through
  `skill_frontmatter_problems`; a clean fixture yields none.
  - Accept: the new tests fail before the rule exists and pass after; the
    problem string is asserted exactly through the public interface.
  - Blocked by: —
- [ ] **Add the rule to `skill_frontmatter_problems`** — protocol.py (the
  seam owner, ADR-0052); regenerate the payload mirror with
  `factory_init.py update-manifest`.
  - Accept: `lint: 0 problem(s)` on the repo; `tests.test_factory_init`
    payload-to-root pin and detector E green; full battery green on
    Python 3.12 and 3.14.
  - Blocked by: Reword the six colon descriptions; Pin the rule with tests

## Milestone 2: A pull request body says what the merge risks

- [ ] **Protocol section "Pull request body"** — `docs/pipeline-protocol.md`
  gains a short section: the smallest visual that shows the change
  (pseudocode, call tree, file tree, diagram or diff), before-and-after
  evidence, and a merge-danger call naming one-way or two-way door plus
  blast radius. Credits mattpocock/skills `pr` and Dex Horthy's `show-me`.
  - Accept: section present and harness-neutral; detector I green.
  - Blocked by: —
- [ ] **Work-queue worker brief cites it** — step 4's brief tells each
  worker the PR body follows that section, keeping the `Closes #N` line
  and detector B's work-order citation.
  - Accept: the brief names the section; lint green.
  - Blocked by: Protocol section "Pull request body"
- [ ] **Ship's rollback plan speaks the same words** — ship step 3 and
  `TEMPLATE.md` record the door and blast radius alongside the rollback
  steps, so release.md and the PR body agree.
  - Accept: both files carry the two fields; lint green.
  - Blocked by: Protocol section "Pull request body"
- [ ] **Routine PR skeleton gains a merge-danger section** —
  `docs/factory/improvement-routine.md` §5 skeleton adds `## Merge danger`
  after `## Verification`, below the detector B lines.
  - Accept: skeleton updated; the first two lines are unchanged; gates
    green.
  - Blocked by: Protocol section "Pull request body"

## Milestone 3: The retro asks what in the environment would have caught it

- [ ] **Operate step: environment retrospective** — a new step after "Retrospect
  on the run itself": from verification failures, review findings and
  breakdown Notes, name for each mistake the check, pointer or rule that
  would have caught it, and classify it mechanical (a deterministic
  check: lint rule, hook, CI job, gate detector) or judgement (CLAUDE.md
  or a standards doc).
  - Accept: step present; the skill description is unchanged so routing
    evals are untouched; lint green.
  - Blocked by: —
- [ ] **Retro template section** — `skills/operate/TEMPLATE.md` gains
  `## Environment` as a table: mistake, evidence, mechanical or judgement,
  proposed carrier.
  - Accept: section present; existing retro.md artifacts untouched.
  - Blocked by: Operate step: environment retrospective
- [ ] **Automate reads retros as friction evidence** — automate step 1's
  surface table adds the Environment sections of `docs/**/retro.md`.
  - Accept: table row present; lint green.
  - Blocked by: Retro template section

## Milestone 4: The router's hand-off fires

- [ ] **Check omp's model-side skill invocation** — read omp's `docs/skills.md`
  model-invoked section and Claude Code's Skill tool; decide whether
  "call the Skill tool with X" is neutral across both harnesses, and
  record the decision in the protocol's Harness neutrality section (an
  ADR only if it amends ADR-0027).
  - Accept: a decision is recorded, adopt or reject with reason.
  - Blocked by: —
- [ ] **Reword `next` step 5 per the decision** — each hand-off line becomes
  an explicit tool-call instruction, or the item closes with the recorded
  reason.
  - Accept: wording matches the decision; `evals/routing.json` untouched;
    lint green.
  - Blocked by: Check omp's model-side skill invocation

## Milestone 5: Small borrowings and close-out

- [ ] **Glossary under either name** — deepen, audit and automate name
  `GLOSSARY.md` beside `CONTEXT.md` where they read a target repo's
  vocabulary.
  - Accept: all three SKILL.md files mention both; lint green.
  - Blocked by: —
- [ ] **Worker base-and-tip rules in work-queue** — the step 4 brief tells
  each worker to confirm its branch base is the default-branch tip before
  writing, and to merge or rebase that tip before declaring done.
  - Accept: both rules present in the brief; lint green.
  - Blocked by: —
- [ ] **Version bump and manifest** — bump `.claude-plugin/plugin.json`
  (0.3.1 if feat/lean-and-polish-skills lands first, else 0.3.0); run
  `factory_init.py update-manifest`; full battery on 3.12 and 3.14.
  - Accept: `Ran N tests OK` on both Pythons; `lint: 0 problem(s)`;
    `gates: 0 problem(s)`; `selftest: ok`.
  - Blocked by: every item above

## Design gaps found

- Milestone 1: whether the rule also rejects a *quoted* description, or
  `read_frontmatter` learns to strip quotes. Recommendation: reject quotes
  too, so the reader stays a plain `key: value` splitter and every
  description is a bare scalar. Small enough to settle at Implement.
- Milestone 2: three places now state PR-body shape (protocol, routine
  skeleton, ship template). The protocol section is the owner; the other
  two point at it rather than restate it.

## Notes

- 2026-10-06: `docs/backlog.md` line 6 (is Pi's 1024 limit chars or
  bytes) touches the same check as Milestone 1 but is out of scope here.
- 2026-10-06: `factory/manifest.json` is also touched by
  feat/lean-and-polish-skills, PR #602 and the unpushed guarded-read
  branch; whichever lands later regenerates it.
