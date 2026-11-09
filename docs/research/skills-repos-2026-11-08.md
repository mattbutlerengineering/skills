# Popular agent-skills repos: gaps and opportunities for idea-to-prod

Research note for issue #1641, 2026-11-08. Research only; no repo files changed.
Everything fetched was read as data; nothing was installed or run, and no
repo's own agent guidance was followed. Evidence labels: "read" means I opened
the URL and the text is quoted or paraphrased from it; [INFERENCE] means not
read, or derived from a secondary source.

## 0. Scope and what was skipped

Local roster read first: `skills/` (35 skills, every SKILL.md description line),
README.md install and skill sections, `docs/pipeline-protocol.md` headings,
`LEDGER.md` maturity table, `docs/backlog.md`, and the 25 files in
`docs/research/`. Already researched there, so not repeated here: jakubkrehel/skills
(interface skills), anthropics/knowledge-work-plugins engineering plugin,
workflow-summary descriptions (sourced from superpowers `writing-skills`),
autonomous harnesses, knowledge-base, eval metrics, house-voice, desloppify, archify,
xerj. This note covers the cross-repo mechanisms those notes did not.

How the shortlist was chosen: web search surfaced two third-party rankings,
https://skillcritic.com/claude-skills-github (read in full; star counts there are
dated 2026-10-29 by the page itself) and
https://github.com/zhuyansen/awesome-claude-code-skills-collections (read first 283
of 994 lines; its collection audit is dated 2026-10-11 by the page). I took the
repos that are both top-starred there and relevant to a lifecycle pipeline, then
read each repo directly through the GitHub API read.

## 1. Repos surveyed

Stars are from each repo's own header in the GitHub API read of 2026-11-08.
Licences are from the same header unless noted.

| Repo | URL | Stars (2026-11-08) | Ships | Distinctive mechanism | Licence | What I read |
|---|---|---|---|---|---|---|
| anthropics/skills | https://github.com/anthropics/skills | 189,827 | 20 skills per skillcritic [INFERENCE for the count; repo tree read but 442 files elided]: docx, pdf, pptx, xlsx, frontend-design, skill-creator, mcp-builder, canvas-design, brand-guidelines and others; plus `spec/` and `template/` | Reference format. Marketplace with two plugins, `document-skills` and `example-skills`. Progressive disclosure in three levels. skill-creator runs with-skill and baseline subagents side by side, grades, aggregates a benchmark and opens a review viewer | Header shows none. README says many skills Apache 2.0; I read `skills/docx/LICENSE.txt` and it is Apache 2.0 text. skillcritic says docx, pdf, pptx, xlsx are source-available; that conflicts with what I read and is unresolved | README whole; `skills/skill-creator/SKILL.md` first 300 of 492 lines; docx LICENSE.txt |
| mattpocock/skills | https://github.com/mattpocock/skills | 318,710 | 38 skills per zhuyansen audit (https://github.com/zhuyansen/awesome-claude-code-skills-collections); README lists about 30 under `engineering/` and `productivity/`, split user-invoked and model-invoked | Small composable skills, no process owner. Two kinds: user-invoked orchestrators that may call model-invoked disciplines but never another user-invoked skill. `ask-matt` router. `grilling` interview primitive shared by five skills. `GLOSSARY.md` plus ADRs as shared language. `SCOPE.md` and `.out-of-scope/` as a rejection registry. Changesets plus plugin version sync | MIT | README whole; `ask-matt/SKILL.md`; `code-review/SKILL.md`; `retro/SKILL.md`; `SCOPE.md`; `CONTRIBUTING.md` |
| obra/superpowers | https://github.com/obra/superpowers | 314,662 | 15 skills per skillcritic [INFERENCE]; README lists brainstorming, writing-plans, subagent-driven-development, test-driven-development, systematic-debugging, verification-before-completion, writing-skills, using-superpowers, diagnosing-superpowers and others | Mandatory-use bootstrap: a SessionStart hook or extension injects `using-superpowers` at session start and after compaction, per harness. Fresh subagent per task with two-stage review. Skills authored by RED-GREEN-REFACTOR with pressure scenarios. Rationalization and red-flag tables. Ships manifests for 15+ harnesses and a separate live-session eval lab | MIT | README to line 525; `using-superpowers`, `writing-skills` (first 300 of 405 lines), `diagnosing-superpowers`; `docs/testing.md` |
| addyosmani/agent-skills | https://github.com/addyosmani/agent-skills | 114,196 | 25 skills, 9 slash commands (spec, plan, build, test, review, ship and more), 4 subagent personas | Three-tier eval in CI: structural lint, deterministic trigger-and-collision check using stemmed TF-IDF over descriptions with a rank-1 floor, and on-demand behavioural evals. Eval file required per skill. `claude plugin eval` results with dated, model-pinned numbers | MIT | README to line 300; `evals/README.md` whole |
| affaan-m/ECC | https://github.com/affaan-m/ECC | 299,774 | README claims 71 agents, 314 skills, 98 command shims, hooks, rules, memory, continuous learning and the AgentShield scanner | Harness-wide system: hook profiles, instincts and memory, a config scanner, guided installer, adapters with a stated support matrix | MIT | README first 300 of 2,334 lines only. Everything beyond the table and install section is [INFERENCE] |
| vercel-labs/skills | https://github.com/vercel-labs/skills | 38,643 | The `skills` CLI itself, plus one `find-skills` skill | Package manager for skills across 75-plus agents: `add`, `find`, `list`, `check`, `update`, `remove`, `use`, `init`; experimental `skills-lock.json` restore and npm-dependency sync | MIT | README whole; file tree |
| pbakaus/impeccable | https://github.com/pbakaus/impeccable | 106,321 | One `impeccable` skill with 24 commands, plus PRODUCT.md and DESIGN.md context files | 62 deterministic slop rules with no LLM, run three ways: agent edit hook, CLI in CI, browser extension. Per-harness build committed at repo root. `engine-checksums.txt` beside the engine | Apache-2.0 | README to line 300; file tree |

Not surveyed in depth: ComposioHQ/awesome-claude-skills, sickn33/agentic-awesome-skills
and other lists. They are catalogs; the zhuyansen audit (read) says several are
so large that Claude Code lists most skills by name only. Not cited as evidence
for any gap below.

## 2. Gap analysis, ranked by value to this pipeline

Local facts used below were measured from this repo on 2026-11-08: 35 skills;
aggregate name plus description text is 21,770 characters, about 5,400 tokens at
four characters per token; the four longest descriptions are 1,023, 1,018, 995
and 949 characters; 16 of 35 LEDGER rows have no trigger-eval result; 7 skill
directories exist under `plugin-evals/`; no SKILL.md sets
`disable-model-invocation`; no SKILL.md contains the word rationalization; no
`.out-of-scope` registry exists.

### G1. Aggregate description budget (S)

Others hold the always-loaded surface small. The zhuyansen audit counted
mattpocock/skills at 1,468 tokens of names plus descriptions and anthropics/skills
at 2,415, and reports that past a budget Claude Code lists skills by name only,
so installed in bulk some lose their description (https://github.com/zhuyansen/awesome-claude-code-skills-collections,
read; a secondary source, dated 2026-10-11, estimate at four characters per
token). We are at roughly 5,400 by the same estimate, 2 to 3.7 times those, with
four descriptions within 1 to 75 characters of the 1,024 cap. Our lint checks
per-skill description shape; I found no aggregate check in `lint.py` or
`trigger_eval.py` by grep for collision, collide and similar [INFERENCE that no
other checker does it: I did not read every checker].
Action: add an aggregate name-plus-description token total to `lint.py` with a
recorded ceiling, and trim the longest utility descriptions. Their routing detail
belongs in the body. This also follows our own research note
`docs/research/workflow-summary-descriptions.md`.

### G2. Deterministic, free trigger and collision check in CI (M)

addyosmani/agent-skills runs a CI-safe routing tier that ranks each skill's
positive prompts by stemmed TF-IDF over descriptions, enforces a rank-1 floor
of 95, and errors at 75 percent pairwise description similarity, warning at 50
(https://github.com/addyosmani/agent-skills/blob/main/evals/README.md, read in
full). Our routing eval, `trigger_eval.py`, needs the `claude` CLI and costs real
runs (README lines 201 and 206, read). Our own ledger shows the failures this
would catch cheaply: review 2/5, autorun 0/4, mermaid 1/3 (LEDGER.md, read).
Action: add an offline lexical tier over `evals/routing.json` plus a pairwise
description-similarity warning to the lint run, reported separately from the
paid eval. It cannot judge semantics; keep it as a regression tripwire only.

### G3. The "model would just do it itself" clause for under-triggering skills (S)

The same evals README records measured results: for code-review, a clause saying
the skill applies even when the diff is pasted inline took four phrasings from 7
of 27 fires to 21 of 27 with adjacent must-not-fire prompts at 0 of 27; for
test-driven-development the clause took four prompts from 6 of 24 to 19 of 24;
it also records that results moved with Claude Code version, so numbers must be
dated and model-pinned. anthropics skill-creator says the same in general terms:
Claude tends to undertrigger, so descriptions should be a little pushy and name
contexts even when the user does not ask for the skill by name
(https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md,
read to line 300). Our ledger shows review, verify, operate and autorun
under-triggering. Our own note on narrated workflows covers the opposite
failure and does not conflict: the clause names situations, not steps.
Action: for review, verify, operate and autorun, draft one situational clause
each, and rerun `trigger_eval.py --record` with the model pinned, recording the
Claude Code version beside the result.

### G4. Rejection registry and an observed-failure intake bar (S)

mattpocock/skills has `SCOPE.md`, which keeps an idea issue open only if it
describes a failure observed in a real session and does not match a file in
`.out-of-scope/`, one file per rejected concept with the reason; eight such files
were listed (https://github.com/mattpocock/skills/blob/main/SCOPE.md and
CONTRIBUTING.md, read). Reactions do not count; unclear issues get one round of
questions then close after 14 days. This repo's recurring intake shape is "what can we learn
from this link" (the opening of docs/research/jakubkrehel-skills-2026-10-31.md and
anthropic-engineering-plugin-2026-11-08.md, both read). Each such note
re-decides take-or-leave from scratch and nothing records the leave decisions
in a place the next run checks. Our ADRs record accepted decisions (128 files in
`docs/adr/`, counted) but I found no rejected-ideas index.
Action: add `docs/out-of-scope/` with one short file per rejected concept
including those in section 3 below, and make `capture` and `next` check it
before seeding a run.

### G5. Session diagnosis with evidence citations and a scrubbed export (M)

superpowers ships `diagnosing-superpowers`: intake question first, then locate
transcripts, then seven parallel analyst subagents (skill timeline, plan
adherence, repeated work, stumbles, quality evidence, request conflicts, cost
and time), a report where every finding must cite `path:line`, and an optional
bundle with a scrub pass and audit pass repeated until clean
(https://github.com/obra/superpowers/blob/main/skills/diagnosing-superpowers/SKILL.md,
read in full). We already harvest transcripts for knowledge-base candidates
(`skills/knowledge-base/SKILL.md` step 2a, read) and have `trace.py`,
`rejection_mining.py` and `kb_harvest.py` [INFERENCE on how much of the
transcript-reading code is reusable: filenames seen, not read]. We have no user-facing answer to
"why did the skill not fire in that session" or a safe way to hand a failing
session to the maintainer.
Action: a `diagnose` utility skill, or a mode of `doctor`, that reads one session
transcript, reports skill timeline and stage skips with line citations, and
exports a scrubbed bundle only on request. Size M mostly because of the scrub
step; ship the read-only report first.

### G6. Context-boundary guidance at stage boundaries (S)

mattpocock's `ask-matt` and its `PHASE-BOUNDARIES.md` give an ordered decision
for what to do between phases: continue, clear, handoff, subagent, compact,
with the reasoning that continuing costs nothing and should be ruled out first.
It also names a context ceiling of about 150k tokens as a "smart zone" and says
to keep grilling, spec and tickets in one unbroken window then start each
implement fresh
(https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md,
read in full; PHASE-BOUNDARIES.md itself not read). Our protocol commits
artifacts at the stage boundary (docs/pipeline-protocol.md heading "Commit at the
stage boundary", read) and `next` reads artifact state, but a grep of
`docs/pipeline-protocol.md` and `skills/next/SKILL.md` for compact, clear and
context window found nothing, so there is no per-boundary advice on when to clear
context. The artifacts-are-state design makes clearing safe here, which is our
advantage.
Action: add a short "context at the boundary" section to the protocol stating
that any stage boundary is safe to clear because the artifact is the state, with
the one exception of in-flight interview answers, and have `next` print one line
saying so.

### G7. Eval coverage as a gate, plus a no-skill baseline arm (M)

Two repos make eval presence mandatory or make the baseline explicit.
addyosmani requires every skill to ship an eval file with at least 3 positive
triggers, 2 negative triggers and 1 behavioural case, and missing files are CI
errors (evals README, read). anthropics skill-creator spawns a with-skill run
and a baseline run in the same turn, then aggregates pass rate, time and tokens
with mean, stddev and delta, and its analyzer flags assertions that always pass
regardless of the skill (SKILL.md, read to line 300; analyzer file itself not
read). superpowers `writing-skills` states the iron law that a skill without a
failing baseline is untested (read to line 300). Here: 16 of 35 skills have no
trigger result and 7 skill directories have plugin evals. The ledger vocabulary
deliberately keeps eval results from graduating maturity (ADR-0019 as quoted in
LEDGER.md), which stays right; the gap is only coverage and a stated baseline.
Action: lint warns when a skill has neither a routing case nor a plugin-eval
case, and every new plugin eval records its no-plugin arm delta. Start with
capture, doctor, conduct and audit, the highest-stakes rows with no result.

### G8. Review in two axes with fresh sub-agent contexts (M)

mattpocock `code-review` reviews the diff since a fixed point along Standards
(documented repo standards plus a 12-smell Fowler baseline that the repo can
override) and Spec (the originating issue), in two parallel fresh-context
sub-agents, reported side by side and deliberately not merged
(https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md,
read in full). superpowers `subagent-driven-development` does a spec-compliance
pass then a code-quality pass (README, read). Our `review` skill description
covers defects, design decay and security; a grep of its body for fresh,
subagent and spec found no spec-fidelity split [INFERENCE that none exists:
grep only, body not re-read in full]. Our PRD success criteria are a strong
Spec source that mattpocock has to look for.
Action: add a Spec axis to `review` that checks the diff against prd.md
success criteria and breakdown.md acceptance lines, run as a separate fresh
context from the Standards pass, and report them under separate headings.

### G9. A user-invoked versus model-invoked split (S)

mattpocock marks orchestrators such as `ask-matt` and `retro` with
`disable-model-invocation: true` (both SKILL.md files, read) and states the
rule that user-invoked skills may call model-invoked ones, never another
user-invoked one (README, read). addyosmani made its lifecycle commands
user-invoked only and records the routing effect (evals README, read). None
of our 35 skills sets the flag. Several of ours are pure orchestrators that a
model should not start on its own initiative: conduct, autorun, implement-queue,
factory-init. Each already spends money or writes outside the working tree.
Action: set the flag on those four after checking how each harness we support
honours it; this also shortens the always-loaded surface from G1 if the
harness omits such descriptions [INFERENCE: not verified for Claude Code].

### G10. Compaction-surviving bootstrap (M)

superpowers injects its `using-superpowers` skill at session start and again
after compaction, through a SessionStart hook on Claude Code and a Pi extension
on Pi, and its README admits Hermes has no post-compaction hook so a long session
can lose the bootstrap
(https://github.com/obra/superpowers/blob/main/README.md, read to line 525).
Our plugin ships no hooks (no hooks directory at the repo root; `plugin.json`
has no hooks key, both checked) and relies on description routing. Counter-evidence:
the bootstrap text is a "1% chance, you must invoke" shout with a rationalization
table (`using-superpowers/SKILL.md`, read), which conflicts with skill-creator's
guidance to explain why instead of heavy MUSTs (read), and the README also ships a
telemetry ping. Only the mechanism is worth borrowing, not the register.
Action: prototype an opt-in SessionStart hook that injects a two-line router
pointer (state of the run directory plus "run /next") including after compact,
measured against the routing eval before shipping. Gate it behind G2 and G3 so
the cheaper fixes are tried first.

### G11. Official-listing and update-check distribution (S)

mattpocock and superpowers both install from `claude-plugins-official`
(`claude plugin install mattpocock-skills@claude-plugins-official`,
`/plugin install superpowers@claude-plugins-official`, both from their READMEs,
read), and carry skills.sh badges. vercel-labs/skills adds `check` and `update`
and an experimental `skills-lock.json` restore (README, read). We have our own
marketplace, an `npx` branch and `doctor` (README, read) but no lockfile or
update check for adopters. I did not read the submission process for the official
marketplace, so effort is [INFERENCE].
Action: find the official-marketplace submission requirements and decide listing;
independent of that, have `doctor` report installed plugin version against latest.

### G12. A skill-authoring skill (M, lowest)

Three repos ship one: skill-creator (anthropics), `writing-skills` (superpowers),
`writing-for-agents` (mattpocock, listed in README; body not read). We have lint
and AGENTS.md rules [INFERENCE: AGENTS.md and CLAUDE.md contents not read for
authoring guidance] but no skill. Our pipeline's audience is end-user repos,
so a skill-authoring skill is lower value here unless adopters write their own
stages; `automate` already recommends skill versus subagent.
Action: none now. Revisit if adopters report writing stage skills.

### Considered and not ranked

- impeccable's deterministic design-slop detector with a PostToolUse-style hook
  (README read) is the best-built mechanical check I saw, but our `polish` and
  interface research (docs/research/jakubkrehel-skills-2026-10-31.md,
  desloppify-2026-10-31.md) already cover this ground; I did not diff the rule
  sets. Revisit only if `polish` graduates from draft.
- ECC's memory, instincts and continuous learning: README claims only, body
  unread. Our `knowledge-base` and `docs/research/knowledge-system-over-time.md`
  are the comparison; no gap shown.
- Multi-harness manifests: superpowers ships manifests for 15-plus harnesses
  (file tree, read). We already cover Claude Code, Grok, omp and `npx skills`
  (README, read). No gap that is cheap to close.

## 3. What we do that these repos do not (do not copy backwards)

Claims are limited to what I read; absence in a repo is "not seen in the
material read", not proof of absence.

- Artifacts as pipeline state with frontmatter, soft gating and a fail-closed
  roll-up (docs/pipeline-protocol.md headings, read). The repos read keep state in
  tickets, plans or conversation: mattpocock in tracker tickets, superpowers in
  plan files under `docs/`.
- A maturity ledger where a skill graduates only through a real run, never by
  review or by eval (LEDGER.md, read). None of the evals READMEs read does this;
  addyosmani and skill-creator gate on eval scores instead.
- Spend control: cost ledger, budget guard, metered headless Workers in `conduct`,
  conductor spend and a priced batch before any spend (skills/conduct description
  and filenames, read in part). Not seen in the six other repos' READMEs; ECC's
  cost features, if any, are unread.
- Offline gates, validator, factory stamping and drift detectors for instruction
  files (`gates.py`, `kb_drift.py`, `lint.py` in README, read). mattpocock and
  addyosmani have structural checks; none of the repos read has drift detection
  for their own instruction files.
- A 128-record ADR trail and a seed backlog with claimed markers
  (`docs/adr/`, `docs/backlog.md`, read). mattpocock has two ADRs in `.agents/adr/`
  (tree, read).
- The maintenance run entry (`capture`), the Operate retro that feeds back to an
  idea, and run scales. mattpocock's `retro` looks at the agent's environment,
  ours at the shipped product; the two are different and both are worth having.
- Self-contained skills with no third-party tools required, and an explicit
  no-telemetry stance. Contrast superpowers' optional logo ping and impeccable's
  live-mode apply that can launch another agent with approvals off (both READMEs, read).

Do not copy:

- superpowers' all-caps mandatory-invocation preamble. It conflicts with
  skill-creator's explain-the-why guidance (both read) and with our trigger
  results being a routing problem we can measure and fix instead.
- mattpocock's closed-to-new-skills, no-process-owner stance. Its README argues
  against tools that own the process (GSD, BMAD, Spec-Kit; README, read). Owning a
  stage-gated process is exactly what this repo is for.
- Catalog-scale breadth (ECC's 314 skills claim, awesome lists). The zhuyansen audit
  (read, secondary) says oversized collections lose descriptions in Claude Code.
- Writing the skill body before a baseline exists. Fine to adopt as a habit; not
  as a delete-and-restart iron law for every doc edit.

## 4. Recommended follow-ups for docs/backlog.md

Each line is in seed-inbox form, without parentheses or ids.

- Add an aggregate name and description token ceiling to lint.py and trim the four descriptions within 80 characters of the 1,024 cap, since the audit read puts comparable repos at 1,500 to 2,400 tokens against our roughly 5,400
- Add an offline lexical routing tier and a pairwise description similarity warning, reported apart from the paid trigger eval, so collisions and missing vocabulary show up in CI for free
- Draft one situational clause per under-triggering skill saying it applies even when the diff or code is pasted inline, rerun trigger_eval.py with the model pinned and the Claude Code version recorded
- Create docs/out-of-scope with one file per rejected concept and make capture and next check it before seeding a run from a what-can-we-learn link
- Add a Spec axis to review that grades the diff against prd.md success criteria in a fresh context apart from the standards pass, reported under its own heading
- Mark conduct, autorun, implement-queue and factory-init as user-invoked only after verifying how Claude Code, Grok and omp each honour disable-model-invocation
- Prototype a diagnose skill that reads one session transcript and reports skill timeline and stage skips with path and line citations, with a scrubbed export only on request
- Add a context-at-the-boundary section to the protocol saying any stage boundary is safe to clear because the artifact is the state, and have next print one line saying so
