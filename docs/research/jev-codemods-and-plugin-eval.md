# Research: #626 (anti-slop / architecture in the workflow) and #633 (jev | claude codemods)

Researched 2026-10-10. Repo read: README.md, CONTEXT.md, skills/implement, skills/review,
skills/deepen, and the `lean` skill on feat/lean-and-polish-skills (worktree
.claude/worktrees/lean-and-polish-skills, PR #632 for #631). Nothing in the repo was modified.

## Sources

Ponytail
- Repo: https://github.com/DietrichGebert/ponytail (MIT; "Ponytail 5"; ~160k stars per the page snapshot)
- JetBrains independent test: https://blog.jetbrains.com/ai/2026/07/ponytail-skill-claude-tested/
- Coverage: https://pasqualepillitteri.it/en/news/5720/ponytail-ai-skill-less-code , https://www.infoq.com/yagni/news/ , https://www.everydev.ai/tools/ponytail
- Directory entries: https://claudemarketplaces.com/skills/DietrichGebert/ponytail/ponytail-debt

Jev / mods / codemods
- Jev with coding agents (Flavio Copes): https://flaviocopes.com/jev-coding-agents/
- Jev mods roundup (pt-BR): https://horadecodar.com.br/?p=46946
- Jev model routing news: https://techbytes.app/posts/using-jev-for-claude-code-model-routing/ (repo https://github.com/gargpratyush/jev-router)
- Jev Model Router mod: https://github.com/davila7/claude-code-templates/tree/main/cli-tool/components/mods/productivity/jev-model-router
- Mods security study: https://pluto.security/blog/claude-code-function-hooks-security/
- Mods rollout issue: https://github.com/anthropics/claude-code/issues/99130
- Claude Code mods (official): https://code.claude.com/docs/en/plugins/mods/overview , https://claude.com/blog/claude-code-mods , https://code.claude.com/docs/en/plugins/mods/reference
- Mods (fr): https://www.it-connect.fr/claude-code-mods-plugins/
- Codemod.com: https://github.com/codemod-com/codemod , https://www.npmjs.com/package/codemod

Claude Code features
- Changelog: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
- What's new (weekly): https://code.claude.com/docs/en/whats-new
- Plugin evals: https://code.claude.com/docs/en/plugin-evals
- Skills (incl. /skill-doctor): https://code.claude.com/docs/en/skills
- Plugin CLI reference: https://code.claude.com/docs/en/plugins/cli-reference

---

## #626: "Use a skill like ponytail ... generating optimal code and minimizing slop"

### What Ponytail is
An MIT, multi-agent skill/plugin by DietrichGebert that makes agents "think like the laziest
senior dev in the room". Core: a seven-rung ladder (does it need to exist, already in the
codebase, stdlib, platform, installed dependency, one-liner, then the minimum), a floor never
cut (validation, error handling, security, accessibility), and `shortcut:` comments (earlier
versions: `ponytail:`) on deliberate simplifications. Commands: `/ponytail` (lite/full/ultra/off),
`/ponytail-review` (diff), `/ponytail-audit` (repo), `/ponytail-debt` (harvest markers),
`/ponytail-gain`, `/ponytail-help`. It is always on via plugin hooks, not by skill triggering.

Evidence:
- Author's claims: -53% code, -26% cost, -41% time (39 tasks, Opus 5.5, 5 runs). The headline
  was revised down once already (80-94% came from a flawed baseline).
- JetBrains independent test (80 paired SkillsBench tasks, Sonnet 5): median -15.4% code
  (p=0.088), -10.3% cost (p=0.004), no detectable quality difference. Two findings matter here:
  1. **It never self-triggered as a bare skill (0 of 10 sessions).** It only works when
     injected by the plugin's SessionStart hook.
  2. **The shortcut-marker convention was followed once in 80 trials.**

### Key finding: the repo already has this
The `lean` skill on feat/lean-and-polish-skills is an explicit, credited adaptation of Ponytail
(skills/lean/references/ladder.md cites DietrichGebert/ponytail, MIT). It has the same ladder,
floor, marker (`lean:`), review/sweep cut-list and debt harvest, plus this pipeline's evidence
rules: no *delete* until its references are enumerated. The lean-and-polish idea.md names #626
as an issue that "wants a base to build on". So #626 does not need a new skill. The gap is
**wiring**. `lean` is a utility skill (ADR-0023), never routed to, so by JetBrains' finding it
will mostly never fire on its own during Implement.

Installing Ponytail next to `lean` is not recommended. The two rulesets would overlap, and the
marker conventions (`shortcut:` vs `lean:`) would differ.

### Options

**A. Call `lean` explicitly from the two stages that need it (recommended). Effort: S, about 2-3 h
including lint/gates/LEDGER touch-ups.**
- implement/SKILL.md step 4: "Write the minimum implementation that passes" becomes "climb
  `lean`'s ladder (skills/lean steps 1-3) before writing; mark deliberate shortcuts `lean:`".
  The existing "Surgical scope" rule already matches lean's step 6.
- review/SKILL.md step 4: add a fourth pass, **Complexity**, that runs `lean`'s review mode over
  the run's diff and records cut-list entries as findings (minor by default, unless a cut removes
  a decayed contract). It also harvests the `lean:` markers the diff added and flags any with no
  trigger. That is the debt check, and it matters because agents rarely write markers unprompted.
  Questions of shape found here are routed to `deepen` (the "architecture" half of #626's title)
  rather than fixed.
- Pros: deterministic (stage skills always run), no new skill, no hook, works on omp too,
  surgical. Cons: it is still prose. It relies on the stage agent reading the ladder, with no
  always-on pressure during free-form coding outside a run.

**B. Always-on injection through a plugin SessionStart hook (Ponytail's own mechanism). Effort: M.**
- Ship hooks/hooks.json in the plugin that injects a compressed ladder and floor every session.
  JetBrains' only measured benefit (-10% cost, -15% code) came from this mode.
- Cons: every consumer of idea-to-prod gets it in every session, including sessions with no
  pipeline run. It costs context on every turn. It needs a per-harness equivalent (.codex/hooks.json
  exists; omp parity is unclear). It also pulls against the plugin's "skills that work on a bare
  install" posture. Reconsider only if A measures weak.

**C. A deterministic slop gate. Effort: M-L.**
- Add a detector to gates.py or lint.py: diff growth against the breakdown item's scope, new
  dependencies with no ADR, duplicated helpers (extend one_owner.py's same-value scan to the
  diff).
- Cons: gates are about drift, and size heuristics produce false positives. one_owner.py is
  deliberately *not* a gate (it is a "question for a human"). This turns a judgment into a red X.
  Better as a later complement to A than as a replacement.

**Recommendation: A**, then measure it with `claude plugin eval` (see #633 item 1). Write cases that
build a small feature with and without the plugin and grade diff size with a regex or file grader,
plus test pass. Graduate to B only if the delta is weak, following eval-honesty rules, not a feeling.

---

## #633: "jev | claude codemods"

### What "jev" is
**Jev is TypeSafe's decision model** (typesafe.ai). It is not a text generator. You send it text
plus typed questions and get back yes/no probabilities, a choice from options you list, or a
position on a scale. In Claude Code it shows up two ways:
1. A TypeSafe skill/plugin (`claude plugin marketplace add typesafe-ai/skills`;
   `claude plugin install typesafe@typesafe-ai`) that helps Claude write code that *calls* Jev.
2. Community **mods** that use Jev as a cheap classifier inside Claude Code: Jev Model Router
   (davila7/claude-code-templates; picks Haiku/Sonnet/Opus per turn or subagent), Jev Skill
   Suggestion (removes the skill listing from context and lets Jev pick at most one SKILL.md per
   prompt), cc-mod-jev (context pruning), and claude-code-jev (allow/block/ask permission gate,
   experimental).
Caveats: TypeSafe paused new signups (late Sept 2026); it needs another key and bill (OpenRouter
at about $0.04/M input); mods are unsandboxed; there are no independent benchmarks of the savings.

### What "claude codemods" most likely means
Almost certainly **Claude Code mods**. They shipped 2026-10-01 in v2.1.287, are on by default,
and are the vehicle all the Jev integrations above use. A mod is a plugin with a JS/TS
`hooks/hooks.json` + `register.(js|ts|tsx)` module. It runs inside Claude Code and can draw panes
or bands, intercept and rewrite tool calls and prompts (`tool.call`, `tool.check`, `agent.spawn`,
`prompt.autocomplete`, `turn.step`), add instant `/commands`, and call models (`$.model.complete`).
Built-in mods include `/diff`, AGENTS.md loading and **"You should know"**, a side agent that flags
what you or Claude might miss. It is disabled by default; enable it with
`/plugin enable cc-plugin-you-should-know@builtin`. Tooling: `claude plugin validate` lists a
mod's hooks and calls, and `claude plugin test` runs it. Risks: mods run with full user
permissions, outside the sandbox. Deny rules are enforced against mods only where sec-default
loads (not on personal Pro/Max). One rollout issue saw mods remotely disabled on 2.1.288.
Alternative reading: Codemod.com (AI-assisted codemods, `codemod learn`, jssg ast-grep transforms).
These are real but aimed at JS/TS framework migrations. **They are not relevant to this repo**
(stdlib Python plus markdown) unless a large mechanical migration comes up.

### Claude Code features, Aug-Oct 2026, relevant to this repo
- W32 (v2.1.220-224): cross-session messaging; auto mode default.
- W33 (v2.1.225-233): fork mode on by default (subagent inherits full context).
- W35 (v2.1.240-250): `--restricted` sessions for eval harnesses on shared machines.
- W36 (v2.1.251-261): **`/skill-doctor`**, which reports each skill's context cost and usage frequency.
- W37 (v2.1.263-269): **`claude plugin eval`** (+ `init`): cases with graders (regex, tool_used,
  tool_order, file_exists, llm, baseline), WITH vs W/OUT-plugin delta, `--threshold`,
  `--max-cost-usd`, `--json`, HTML report.
- v2.1.283: **`/doctor prompt-audit`**, which checks CLAUDE.md, skills, agents and commands for
  outdated prompting patterns.
- v2.1.285: `claude plugin configure`; v2.1.281/283 stricter `claude plugin validate`.
- v2.1.287 (Oct 1): **Mods**; v2.1.288 `/code-review --max-findings`.
- v2.1.290: `claude plugin validate` lists gating hooks; `tool.check` hook gets agentId.
- v2.1.292: **Agent tool `effort` parameter**; `claude plugin install --marketplace`;
  `agent.spawn` covers workflow agents.
- v2.1.295: command/HTTP hooks `onFailure: "block"`.
- v2.1.296: **`autoCompactWindow` in subagent frontmatter**; `CLAUDE_CODE_WORKFLOW_SUBAGENT_MODEL`.

### Ranked workflow improvements for this repo

1. **Adopt `claude plugin eval` for idea-to-prod. Effort M (1-2 days for a first 8-12 cases).**
   It directly serves LEDGER maturity, which "graduates only via a real run". It gives a
   with/without-plugin delta per skill, which trigger_eval.py and charter_replay.py cannot.
   `tool_used: Skill` graders cover routing; `file_exists` and regex graders cover stage
   artifacts. It is also the way to test whether #626 option A works.
   **Hazard:** by default it writes to `./evals/results/`, which is this repo's append-only tree
   whose naming grammar eval_schema.py owns (ADR-0024). Use `--eval-dir plugin-evals` (or a
   manifest setting). Decide by ADR whether its results.json snapshots join the append-only
   record. Keep it on demand only (paid; repo rule "never CI"); pin `--model` and set
   `--max-cost-usd`.
2. **Run `/skill-doctor` and `/doctor prompt-audit` once. Effort S (about 30-60 min, free).**
   The plugin ships about 26 skills with long descriptions (lean's is about 1,000 characters),
   all listed every turn. Measure the per-turn context cost and file backlog seeds for the worst
   offenders.
3. **Wire `lean` into implement and review (#626 option A). Effort S.** This is the concrete
   anti-slop step; measure it with item 1.
4. **Per-stage effort and compaction in autorun/work-queue. Effort S-M.** Use the Agent `effort`
   parameter (2.1.292): low for mechanical stages such as ship checklists, high for architect and
   review. Use `autoCompactWindow` for long implement subagents. Cost/latency win, but it needs a
   check against factory.json caps and cost_ledger.py.
5. **Turn on the built-in "You should know" mod personally. Effort S (one command).** Zero repo
   change; try it for a week on long autorun sessions.
6. **A first-party pipeline mod. Effort M-L. Defer.** For example, a band above the prompt
   showing the active run and stage from board.py, or an instant `/stage` command. Nice UX, but
   it is JS/TS (breaks the stdlib-Python convention and omp parity) and unsandboxed code shipped
   to every consumer. The rollout is still unsettled.
7. **`onFailure: "block"` on hooks. Effort S, low value.** The repo's only hook is
   `bd prime` at SessionStart; factory/templates stamp no hooks. Revisit if a gating hook appears.
8. **Jev mods (model router, skill suggestion). Not recommended.** They add an external key and
   bill, signups are paused, they are unsandboxed, and there is no benchmark. Skill-suggestion
   duplicates what `next` and description routing already do, and would make trigger_eval
   results non-comparable.
9. **Codemod.com / jssg. Not applicable** until a mechanical JS/TS migration exists in a product repo.

**Recommendation: item 1 (plugin eval).** It is the one feature that turns this repo's
"never fabricate evidence" rule into cheap, repeatable measurement. It also gives #626 and every
future skill change (lean, polish, the routing descriptions) a with/without delta instead of
opinion. Start with `claude plugin eval init` scoped to `lean`, `next` and `implement`, and land
the `--eval-dir`/ADR decision first.
