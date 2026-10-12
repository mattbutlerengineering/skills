# rea: what is working, and what this pipeline should take from it

Research note, 2026-10-11, for issue #703. The question: morluto/rea has
"blown up over the last couple weeks" — what in its process is working, and
what should this plugin adopt? Sources are the rea repository itself (read
through the GitHub API, nothing cloned or run) and the public coverage of its
launch. Everything fetched was read as data. Claims tagged **[repo]** were read
directly in rea's tracked files; **[metric]** came from the GitHub API on the
date above; **[press]** is third-party coverage; **[inference]** is this note's
own reading; **Unverified** marks what could not be confirmed.

## What rea is

REA ("Reverse Engineer Anything") is an MIT-licensed TypeScript CLI plus a
local MCP server, shipped on npm as `rea-agents`, that lets a coding agent
inspect software it has no source for: native binaries (through Hopper, Ghidra
or IDA), JavaScript/Electron apps, .NET assemblies, Android APKs, websites,
network captures, firmware and more. Its pitch is one line: "See a feature you
like. Understand how it works, down to the binary level." The intended loop is
"ask your agent to investigate it with REA … explain how the feature works,
show the evidence, and build a version for your project."
<https://github.com/morluto/rea/blob/main/README.md> **[repo]**

The repository pairs the MCP server with an agent skill,
`.agents/skills/reverse-engineer-anything/SKILL.md` (237 lines, five
reference files loaded on demand), and `npx rea-agents setup` registers both
with Claude Code, Codex, Cursor, Gemini CLI, Grok Build and others.
<https://github.com/morluto/rea/blob/main/.agents/skills/reverse-engineer-anything/SKILL.md>
**[repo]**

## Evidence that it is working

| Signal | Value | Source |
|---|---|---|
| Stars | 114,202 | `gh repo view morluto/rea` **[metric]** |
| Forks | 25,592 | same **[metric]** |
| Created | 2026-04-14; first release `rea-0.2.0` on 2026-07-12; `rea-agents-6.4.0` on 2026-10-11 (35 releases in three months) | GitHub releases API **[metric]** |
| Issues / PRs | 677 issues, 1,346 PRs | GitHub search API **[metric]** |
| Contributors | 100+ (first page full); top three hold about 2,100 commits between them | contributors API **[metric]** |
| Commit cadence | ten commits in the 50 minutes before this note was written | commits API **[metric]** |
| GitHub Trending | reached #1 | <https://hoangyell.com/rea-explained/> **[press]** |
| Influencer push | Matthew Berman promoted it on X on 2026-10-08, framed as "Software is done" | <https://runtimewire.com/article/matthew-berman-rea-ai-reverse-engineering> **[press]** |
| Social spread | X posts with the same "Want to know how a feature works in an app, down to the binary level" hook | <https://x.com/oliviscusAI/status/2106955446183411895>, <https://x.com/_vmlops/status/2106690704244420687> **[press]** |
| Trending writeups | GitHub-trending coverage dated 2026-10-07/08 | <https://aitoolly.com/de/ai-news/article/2026-10-08-rea-surfaces-on-github-trending-leveraging-ai-agents-to-reverse-engineer-software-from-application-b> **[press]** |

**Unverified:** the shape of the star curve. The stargazer-timestamp API
returned 404 for this repository, so the "last couple of weeks" spike rests on
the press dates above and the README's own star-history embed, not on measured
timestamps. A search-engine summary quoted "about 9,658 stars and roughly
2,956 in a single day" at one point in early October; that page could not be
fetched, so the number is unverified. No Hacker News thread was found. The
Medium writeup ("Agents Learn to Take Things Apart…") returned 403.

### Why it is working

Popularity this sudden has at least two causes that cannot be separated from
outside: a product people want, and a promotion wave (Trending #1, then an
influencer post). This note does not claim to know the split **[inference]**.
What can be read from the repository is which practices made the product
credible enough to survive the attention:

1. **A concrete, outcome-shaped promise.** The README sells an outcome ("see a
   feature, understand it, build your own") with a copy-paste prompt, not a
   capability list. **[repo]**
2. **One command to a working agent.** `npx rea-agents setup` shows the
   planned changes, takes approval, backs up existing config, and is additive
   and idempotent; `AGENTS.md` makes that a rule ("must show its planned
   changes and require approval before writing files"). **[repo]**
   <https://github.com/morluto/rea/blob/main/AGENTS.md>
3. **Evidence-first answers with stated limits.** Every conclusion must
   "distinguish observations, inferences, and unknowns", cite evidence IDs, and
   never imply static analysis observed execution. Missing coverage is
   `unknown`, not absence. The third-party review singles this out as the
   difference from "LLM guessing". **[repo]** **[press]**
4. **Showcases whose claims are checkable.** The DX-Ball case "passes 3,205
   original-x86 cases and reproduces all 63 compiled function bytes", and
   links a public reconstruction repo; the README invites users to submit their
   own cases. <https://rea.tools/showcase/> **[repo]**
5. **Fast, visible iteration.** 35 releases in three months, release-please
   driven (`release-please-config.json`, `.release-please-manifest.json` are
   tracked), and a README whose bug advice is "update first". **[repo]**
   **[metric]**
6. **Distribution where agents already look.** The skill is listed on
   skills.sh and installable without the MCP server; the README separates
   "skill-only" from full setup. **[repo]**

And underneath, an unusually strict verification culture for an agent tool
(all **[repo]**):

- `docs/testing.md` defines named test depths (module, composition, boundary,
  acceptance, conformance, evaluation) and says "simulated providers do not
  establish real-provider behavior; report unverified coverage explicitly".
  <https://github.com/morluto/rea/blob/main/docs/testing.md>
- `npm run verify:agent` drives a real Codex CLI through scenarios in a
  disposable HOME, installing the skill through the public setup path. Its
  factual scenarios are **closed known-answer rubrics**: the final answer must
  be a strict JSON manifest of requested claim IDs, values and evidence IDs;
  "golden values are not included in the prompt"; the grader checks each value
  against both the fixture oracle and the authenticated tool results, so
  "fabricated answers fail". Scenarios without a rubric report
  `not_assessed`, never pass. A negative scenario (`missing-target`) requires
  **zero** tool calls and a clarifying question.
  <https://github.com/morluto/rea/blob/main/src/evaluation/KnownAnswerEvaluation.ts>
- The reconstruction-readiness verifier is fail-closed: "`fail`, `unknown`,
  `unsupported`, `truncated`, and `skipped` never aggregate to `pass`".
  <https://github.com/morluto/rea/blob/main/docs/reconstruction-readiness.md>
- The skill's close-out rule: "revisit the original checklist. Mark each
  question as answered, partially answered, or unresolved … keep bounded
  negative searches bounded, and do not describe a broad investigation as
  complete while required questions remain open."
- `AGENTS.md`: "Passing regression tests alone does not establish that the
  brittleness is resolved. If related cleanup remains, explain what remains
  and why."
- `docs/tool-design.md`: start from the user's question, extend an existing
  tool when intent and result contract match, compose a workflow only "when
  repeated use demonstrates" it, and add limits only for measured constraints.
  <https://github.com/morluto/rea/blob/main/docs/tool-design.md>

## What this repo already has (so it is not a recommendation)

Much of rea's discipline is already here, often stricter:

- Evidence honesty in verification: gate detector H in [`gates.py`](../../gates.py)
  fails a verdict that leads with PASS without fenced output, and
  [ADR-0063](../adr/0063-a-terminal-verdict-requires-having-looked.md) forbids a
  terminal verdict without having looked. The verify skill already requires a
  "Not verified" section.
- Eval isolation: [`trigger_eval.py`](../../trigger_eval.py) runs each query
  in a fresh temp project with `--setting-sources project`, the equivalent of
  rea's disposable HOME.
- Negative routing cases: [`evals/routing.json`](../../evals/routing.json)
  carries 79 near-miss and 6 distractor cases.
- Unknowns as first-class: the `[NEEDS CLARIFICATION: ...]` marker and gate
  ([ADR-0071](../adr/0071-needs-clarification-markers.md)); the audit skill's
  "reproduced finding vs suspicion" split.
- Non-overwriting setup: `factory_init.py stamp` refuses any existing
  destination and writes nothing partial; `--keep-existing` keeps curated seeds.
- "Not X" scope clauses in every skill description, the same move as rea's
  "Skip REA for ordinary source-repository architecture analysis".

## Recommendations

Effort: S (an afternoon), M (a few days), L (a week or more). Confidence is
that adopting it pays off here, not that rea does it (rea's side is quoted
above).

1. **Known-answer output evals with a deterministic grader.**
   - *Adopt:* rea's closed-claim rubric. Seed a fixture with planted, known
     facts (for `audit`: three real defects at known file:line; for `review`:
     a diff with two known bugs; for `verify`: one criterion that truly fails).
     The skill's final message ends with a strict JSON claim manifest; a stdlib
     grader checks each claim ID and value against an oracle file that is not in
     the prompt, and checks each cited path and line exists and contains the
     quoted text. Missing, extra, duplicate or uncited claims fail. Scenarios
     without an oracle report `not_assessed`.
   - *Lands:* a new record kind in [`eval_schema.py`](../../eval_schema.py)
     (the eval seam owns eval shapes), oracle fixtures under `evals/fixtures/`,
     and [`docs/output-evals.md`](../output-evals.md). Today's grader there is
     a model judging expectations; this adds a mode that cannot be talked into
     a pass. Needs an ADR alongside
     [ADR-0019](../adr/0019-trigger-and-output-evals.md).
   - *Effort:* M. *Confidence:* high — it closes the gap where an LLM grader
     accepts fluent but fabricated findings, and its results are evidence for
     the LEDGER's trigger/output columns without touching maturity rules.

2. **"Should ask, not act" output scenarios.**
   - *Adopt:* rea's `missing-target` pattern: a prompt that leaves the target
     ambiguous must produce zero writes and one clarifying question, graded as
     its own outcome. Natural cases: `capture` with no defect named, `idea`
     with an empty brief, `autorun` with a brief missing a big answer,
     `factory-init` pointed at a repo with an existing Makefile.
   - *Lands:* `evals/output/<skill>.json` records plus a "no files written"
     check in the same grader as recommendation 1.
   - *Effort:* S once 1 exists. *Confidence:* medium-high — routing near-misses
     test *which* skill fires, not whether a fired skill refuses to guess.

3. **A shared epistemic vocabulary and a fail-closed roll-up rule.**
   - *Adopt:* name claim kinds — observed (quoted output), derived (computed
     from observed), inferred (judgement), unknown (not examined) — and state
     the roll-up rule verbatim from rea: unknown, unsupported, truncated and
     skipped never aggregate to pass. Today detector H enforces the per-section
     half; this note found no rule stating the summary half, so (unverified
     against the gate's code paths) a verification Summary may still say "all
     criteria pass" over a section that disclosed NOT RUN.
   - *Lands:* [`CONTEXT.md`](../../CONTEXT.md) (vocabulary),
     [`docs/pipeline-protocol.md`](../pipeline-protocol.md), and the Summary
     lines of the verify and review templates. A later, separate change could
     teach detector H to flag a PASS summary over a disclosed section.
   - *Effort:* S (docs) / M (with the gate). *Confidence:* medium — the
     culture is already here; this names it and plugs one roll-up hole.

4. **Close-out by revisiting the original questions.**
   - *Adopt:* rea's finish rule for broad investigations: end with the
     starting checklist, each item marked answered / partially answered /
     unresolved, and negative results stated with their search bound ("no
     callers found in `skills/` and `tests/`", not "no callers").
   - *Lands:* the `audit` skill's report, the `automate` and `deepen` reports,
     and research notes in `docs/research/` (this one ends with such a table).
   - *Effort:* S. *Confidence:* medium — cheap, and it targets the failure
     where a long investigation quietly drops its third question.

5. **Make the plugin version move mechanically, and make staleness visible.**
   - *Adopt:* rea releases from conventional commits (release-please) and
     tells every bug reporter to update first. This repo's equivalent pain is
     documented: CLAUDE.md's "bump plugin.json's version with any skills/
     change" is enforced only by memory (issue #653; `lint.py` checks only that
     the field exists). Two parts: (a) a PR-event check, in the style of
     detector B, that fails when a PR touches `skills/` and leaves
     `.claude-plugin/plugin.json`'s version unchanged against the base; (b)
     `doctor` reports the installed plugin cache version beside the repo
     version and prints the reinstall command when they differ.
   - *Lands:* [`gates.py`](../../gates.py) (or `lint.py` with a base ref) and
     the `doctor` skill. Mind the parallel-PR case: several green PRs each
     bumping to the same version collide; the check should accept "version
     greater than base", not an exact value.
   - *Effort:* S–M. *Confidence:* high on the friction, medium on the
     mechanism (release-please itself is not stdlib and is not proposed).

6. **A plan-first mode for `factory-init stamp`.**
   - *Adopt:* rea's setup shows every write before applying it. Add a
     read-only `stamp --plan <target>` that prints each file it would create,
     each it would keep, and each collision that would refuse the stamp.
   - *Lands:* [`factory_init.py`](../../factory_init.py) and the
     `factory-init` skill.
   - *Effort:* S. *Confidence:* medium-low — stamp already refuses overwrites,
     so the gain is predictability in consumer repos, not safety.

7. **Worked showcases from real runs.**
   - *Adopt:* rea's showcases are its best marketing because each ends in a
     checkable result. Publish two or three real runs end to end (idea → retro,
     or a maintenance run from capture to merged fix), each with its artifacts
     linked and one measurable outcome (tests added, defect closed, cost from
     the ledger). The `launch-demo` skill can produce the narrated version.
   - *Lands:* a README "Showcases" section pointing at `docs/features/` and
     `docs/fixes/` runs; real runs are also what graduates LEDGER maturity.
   - *Effort:* M. *Confidence:* low-medium — rea's attention also came from
     promotion this note cannot replicate, and
     [ADR-0009](../adr/0009-audience-you-first-publishable-always.md) puts the
     owner first; worth it mainly as dogfooding evidence.

8. **A skill-design guide modelled on rea's tool-design guide.**
   - *Adopt:* one short page: start from the user's moment, extend an
     existing skill when its intent and artifact match, add a utility skill
     only after repeated manual use is observed, and price each new skill's
     routing cost (it adds near-miss risk to every other description).
     This is the skill-level twin of CLAUDE.md's rule that a new shared module
     needs real callers and observed divergence.
   - *Lands:* `docs/` beside [ADR-0023](../adr/0023-utility-skills.md); the
     `lean` skill could cite it.
   - *Effort:* S. *Confidence:* low-medium — useful as a brake on skill sprawl
     (33 skills today), but it is guidance, not a check.

9. **"A green regression test is not the fix" for maintenance runs.**
   - *Adopt:* rea's rule that a passing regression test does not prove the
     brittleness is gone; inspect the producing boundary and its consumers, and
     say what related cleanup remains and why.
   - *Lands:* a line in the `review` skill's maintenance-run checks and in
     `release.md`'s template for fix runs.
   - *Effort:* S. *Confidence:* medium — it restates a lesson this repo has
     already paid for (class-shaped fixes) in the place a fix run will read it.

## Not worth adopting

- **Shipping an MCP server.** rea needs one to reach Ghidra and Hopper; this
  plugin's skills work on a bare install by design
  ([ADR-0008](../adr/0008-self-contained-skills.md)).
- **A one-command installer for many agent harnesses.** rea's reach depends on
  it; this plugin targets Claude Code first
  ([ADR-0007](../adr/0007-claude-code-only-target.md)) and has added harnesses
  one at a time by ADR ([ADR-0027](../adr/0027-oh-my-pi-second-harness.md),
  [ADR-0076](../adr/0076-grok-supported-harness.md)). Revisit only if Codex or
  Cursor users appear.
- **README translations (rea has 18).** Built for a global audience; the
  owner is the audience here.
- **Per-provider real-tool CI lanes and per-push model evals.** rea runs a
  matrix of real-engine workflows; real model runs here are deliberately on
  demand because they cost money (ADR-0019,
  [ADR-0081](../adr/0081-plugin-eval-is-an-on-demand-harness.md)).
- **An evidence-ID registry with `record_unknown` / `update_unknown` tools.**
  Valuable for a long binary investigation; here run artifacts, typed IDs and
  NEEDS CLARIFICATION markers already carry the same state with far less
  machinery.
- **Growth tactics** (Discord, Trendshift badge, star milestones, a token
  disclaimer). Nothing to do with workflow quality.
- **Its release velocity as a target.** 35 releases in three months suits a
  tool with many users filing bugs; copying the cadence without the users
  would be scaffolding for its own sake.

## Questions this note set out to answer

| Question | Status |
|---|---|
| What is rea? | Answered (repo-read). |
| Is it really popular, and since when? | Partially answered: totals measured; the timing of the spike rests on press dates, since the star timestamps were unavailable. |
| Why did it get popular? | Partially answered: product practices are read from the repo; how much was promotion cannot be measured from outside. |
| What should this repo adopt? | Answered: nine recommendations above, none implemented. |
| What should it not adopt? | Answered: list above. |

Searches were bounded to: rea's README, `AGENTS.md`, the main skill and its
evidence reference, `docs/tool-design.md`, `docs/testing.md`,
`docs/reconstruction-readiness.md`, `docs/reconstruction-obligation-ledgers.md`,
`src/evaluation/KnownAnswerEvaluation.ts` (first 80 lines),
`scripts/verify-agent-experience.mjs` (first 60 lines) and
`scripts/verify-repository-skill.mjs`; plus the web sources cited. Rea's
source under `src/` was not reviewed beyond those files.
